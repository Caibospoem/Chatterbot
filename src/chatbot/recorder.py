from __future__ import annotations

import asyncio
import logging
import signal
import time
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
import pvporcupine
import sounddevice as sd
import soundfile as sf
import streamlit as st
from pvrecorder import PvRecorder

from chatbot._dictionary import session_keys
from chatbot.api.async_api import (
    async_file_to_wav,
    async_get_asr_response,
    async_get_tts_response,
    async_get_vad_response,
    async_play_opus_file,
    async_write_tts_response,
    get_openai_response_stream,
)
from chatbot.config_manager import ServiceSettings, load_settings_file
from chatbot.console.logger import Badge, Logger, set_logger_debug
from chatbot.tools.live2d_mouth import cal_mouth_y
from chatbot.tools.timed_helper import get_time_tag_with_millis

if TYPE_CHECKING:
    from numpy.typing import NDArray

# 音频参数
RATE = 16000  # 采样率
CHANNELS = 1  # 单声道
SILENCE_THRESHOLD = 1000  # 静音检测阈值（毫秒）
MAX_RECORDING_TIME = 30  # 最长录音时间（秒）
SEGMENT_DURATION = 1.5  # 每个VAD检测段的持续时间（秒）
INITIAL_WAIT_TIME = 3.0  # 初始等待时间（秒）


streamlit_loggers = [
    logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别

set_logger_debug()  # 设置日志记录器为调试模式

if session_keys["sentence_que"] not in st.session_state:
    st.session_state[session_keys["sentence_que"]] = asyncio.Queue()  # 初始化句子队列
if session_keys["tts_que"] not in st.session_state:
    st.session_state[session_keys["tts_que"]] = asyncio.Queue()  # 初始化音频文件队列


async def sentence_producer(prompt: str):
    async for sentence in get_openai_response_stream(prompt):
        await st.session_state[session_keys["sentence_que"]].put(sentence)
        # Logger.custom(sentence, badge=Badge("零壹万物", fore="black", back="cyan"))


async def tts_worker(cache_dir: Path):
    while True:
        sentence: str = await st.session_state[session_keys["sentence_que"]].get()
        audio_bytes = await async_get_tts_response(sentence)
        time_label = get_time_tag_with_millis()
        output_path = cache_dir / f"{time_label}.opus"
        await async_write_tts_response(audio_bytes, output_path)
        await st.session_state[session_keys["tts_que"]].put((sentence, output_path))
        st.session_state[session_keys["sentence_que"]].task_done()  # 标记句子处理完成


# TODO: 需要检查 tts 的返回是不是 byte , 有时候返回了 json ,说明出错了, 我没想到这个过程竟然一点错误都没有
async def play_worker(cache_dir: Path):
    while True:
        sentence, audio_path = await st.session_state[session_keys["tts_que"]].get()
        Logger.custom(sentence, badge=Badge("零壹万物", fore="black", back="cyan"))
        # 转换音频格式为 WAV 以供 play_live2d 使用
        wav_path = cache_dir / f"{audio_path.stem}.wav"
        await async_file_to_wav(audio_path, wav_path)
        # 同时播放音频和Live2D动画
        audio_task = asyncio.create_task(async_play_opus_file(audio_path))
        live2d_task = asyncio.create_task(cal_mouth_y(wav_path))
        # 等待两个任务都完成
        await asyncio.gather(audio_task, live2d_task)
        st.session_state[session_keys["tts_que"]].task_done()


class VoiceRecorder:
    def __init__(self):
        self.settings = load_settings_file("config.toml", ServiceSettings)
        self.cache_dir = Path(self.settings.cache_dir) / "asr"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.recording = False
        self.audio_frames: list[NDArray[np.float32]] = []  # 临时缓冲区，用于从回调中收集帧
        self.all_audio_frames: list[NDArray[np.float32]] = []  # 保存所有录制的帧
        self.audio_length = 0  # 录音时长（秒）

        # 分段处理状态
        self.segments_to_process: list[tuple[NDArray[np.float32], int]] = []
        self.processing_segments = False

        # PicoVoice唤醒词检测
        self.porcupine = None
        self.wakeup_recorder = None
        self.access_key = self.settings.access_key

        # TODO , 封装， 更加通用， 包括唤醒词文件自动查找和验证文件路径
        self.system_platform = self.settings.system_platform
        if self.system_platform == "win":
            self.keyword_paths = [
                "./models/keywords_spotting/你好_windows.ppn",
            ]
        elif self.system_platform == "mac":
            self.keyword_paths = [
                "./models/keywords_spotting/你好_mac.ppn",
            ]
        elif self.system_platform == "raspberry-pi":
            self.keyword_paths = [
                "./models/keywords_spotting/你好_raspberry-pi.ppn",
            ]
        else:
            Logger.error(f"Unsupported system platform: {self.system_platform}")
            raise ValueError(f"Unsupported system platform: {self.system_platform}")
        self.keywords = ["你好"]

    async def cleanup_wakeup_resources(self):
        """清理唤醒词检测资源"""
        if self.wakeup_recorder:
            if hasattr(self.wakeup_recorder, "is_recording") and self.wakeup_recorder.is_recording:
                self.wakeup_recorder.stop()
            self.wakeup_recorder.delete()
            self.wakeup_recorder = None

        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

    async def initialize_wakeup(self):
        """初始化唤醒词检测"""
        await self.cleanup_wakeup_resources()

        self.porcupine = pvporcupine.create(  # type: ignore[arg-type]
            access_key=self.access_key,
            keyword_paths=self.keyword_paths,
            model_path="./models/keywords_spotting/porcupine_params_zh.pv",
        )
        self.wakeup_recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        Logger.info("唤醒词检测初始化成功")
        return True

    async def listen_for_wakeup(self):
        """监听唤醒词，直到检测到为止"""
        await self.initialize_wakeup()
        if self.wakeup_recorder is None or self.porcupine is None:
            raise RuntimeError("porcupine 或者 PvRecorder 未正确初始化")
        self.wakeup_recorder.start()
        Logger.info("开始监听唤醒词...")

        detected = False
        while not detected:
            pcm_frame = self.wakeup_recorder.read()
            keyword_index = self.porcupine.process(pcm_frame)

            if keyword_index >= 0:
                Logger.info(f"检测到唤醒词：{self.keywords[keyword_index]}")
                detected = True

            await asyncio.sleep(0.01)

        self.wakeup_recorder.stop()
        return True

    def audio_callback(self, indata: NDArray[np.float32], status: sd.CallbackFlags):
        """声音设备的回调函数

        Args:
            indata: 输入音频数据数组
            status: 回调状态标志
        """
        if status:
            Logger.warning(f"音频回调状态: {status}")
        if self.recording:
            # 将音频帧添加到临时缓冲区
            self.audio_frames.append(indata.copy())

    async def save_wav(self, audio_data: NDArray[np.float32], file_path: Path) -> Path:
        """将音频数据保存为WAV文件

        Args:
            audio_data: 包含音频样本的NumPy数组，数据类型为float32
            file_path: WAV文件的保存路径

        Returns:
            Path: 保存的WAV文件路径
        """
        sf.write(file_path, audio_data, RATE, format="WAV", subtype="PCM_16")  # type: ignore[arg-type]
        Logger.info(f"已保存WAV文件: {file_path}")
        return file_path

    async def process_segments(self):
        """按顺序处理音频片段进行VAD检测"""
        self.processing_segments = True
        last_voice_activity_ms = 0
        audio_length_ms = 0

        while self.processing_segments and self.recording:
            if not self.segments_to_process:
                # 如果没有待处理的片段，等待一段时间
                await asyncio.sleep(0.1)
                continue

            # 获取最早的片段进行处理
            segment_data, segment_index = self.segments_to_process.pop(0)
            segment_path = self.cache_dir / f"segment_{segment_index}_{get_time_tag_with_millis()}.wav"

            # 保存片段为WAV文件
            await self.save_wav(segment_data, segment_path)

            # 发送到VAD服务
            vad_result = await async_get_vad_response(segment_path)

            # 清理临时文件
            if segment_path.exists():
                segment_path.unlink()

            if not vad_result:
                Logger.warning(f"VAD处理片段 {segment_index} 失败")
                continue

            Logger.info(f"VAD结果: {vad_result}")

            # 更新音频总长度和最后的语音活动时间
            audio_length_ms = vad_result["audio_length"]

            # 获取时间戳数组
            timestamps = vad_result.get("timestamp", [])
            if timestamps and len(timestamps) > 0:
                # 找到最后一个语音段的结束时间
                last_voice_activity_ms = timestamps[-1][-1] if timestamps[-1] else 0
                Logger.info(
                    f"VAD结果: 片段 {segment_index}, 音频长度 {audio_length_ms}ms, 最后语音活动 {last_voice_activity_ms}ms"
                )
            else:
                Logger.info(f"VAD结果: 片段 {segment_index} 没有检测到语音活动")
                last_voice_activity_ms = 0

            # 检测是否应该停止录音
            silence_duration_ms = audio_length_ms - last_voice_activity_ms
            Logger.info(f"静音时长: {silence_duration_ms}ms (阈值: {SILENCE_THRESHOLD}ms)")

            if silence_duration_ms > SILENCE_THRESHOLD:
                Logger.info(f"检测到长时间静音 ({silence_duration_ms}ms)，停止录音")
                self.recording = False
                break

        self.processing_segments = False
        Logger.info("片段处理任务结束")

    async def record_and_process(self):
        """录音并处理"""
        # 重置录音状态
        self.recording = True
        self.audio_frames = []
        self.all_audio_frames = []  # 存储所有录制的音频帧
        self.segments_to_process = []
        self.audio_length = 0

        # 计算每个片段的样本数
        samples_per_segment = int(RATE * SEGMENT_DURATION)

        # 启动录音流
        stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, callback=self.audio_callback)

        Logger.info("开始录音...")
        start_time = time.time()
        stream.start()

        # 等待初始时间后开始处理
        Logger.info(f"等待 {INITIAL_WAIT_TIME} 秒后开始VAD处理...")
        initial_wait_end = start_time + INITIAL_WAIT_TIME

        # 开始分段处理任务
        segment_processor = asyncio.create_task(self.process_segments())

        segment_index = 0
        segment_buffer: list[NDArray[np.float32]] = []  # 用于构建分段的缓冲区

        # 录音主循环
        while self.recording:
            # 更新录音时长
            current_time = time.time()
            self.audio_length = current_time - start_time

            # 检查最大录音时间
            if self.audio_length > MAX_RECORDING_TIME:
                Logger.info(f"达到最大录音时间 ({MAX_RECORDING_TIME}s)，停止录音")
                self.recording = False
                break

            # 收集当前帧
            current_frames = []
            if self.audio_frames:
                current_frames = self.audio_frames.copy()
                self.audio_frames = []

                # 添加到全局帧列表（用于保存完整录音）
                self.all_audio_frames.extend(current_frames)

                # 添加到分段缓冲区（用于VAD处理）
                segment_buffer.extend(current_frames)

            # 初始等待时间过后，开始处理音频片段
            if current_time >= initial_wait_end and self.recording:
                # 如果缓冲区积累了足够的样本，创建新的片段
                total_samples = sum(len(frame) for frame in segment_buffer)

                if total_samples >= samples_per_segment:
                    frames_for_segment: list[NDArray[np.float32]] = []
                    segment_samples = 0

                    # 提取足够的帧来构成一个片段
                    for i, frame in enumerate(segment_buffer):
                        frames_for_segment.append(frame)
                        segment_samples += len(frame)

                        if segment_samples >= samples_per_segment:
                            # 更新缓冲区，移除已处理的帧
                            segment_buffer = segment_buffer[i + 1 :]
                            break

                    # 如果有足够的帧，创建片段并添加到处理队列
                    if frames_for_segment:
                        segment_data = np.concatenate(frames_for_segment, axis=0)

                        # 将片段添加到处理队列
                        self.segments_to_process.append((segment_data, segment_index))
                        Logger.info(f"添加片段 {segment_index} 到处理队列 (长度: {len(segment_data)} 样本)")

                        segment_index += 1

            # 短暂休眠以减少CPU使用率
            await asyncio.sleep(0.1)

        # 停止录音
        Logger.info("停止录音...")
        stream.stop()
        stream.close()

        # 等待片段处理完成
        self.processing_segments = False
        await segment_processor

        # 合并所有音频帧 - 现在使用all_audio_frames而不是collected_frames
        if self.all_audio_frames and len(self.all_audio_frames) > 0:
            # 添加剩余的帧
            if self.audio_frames:
                self.all_audio_frames.extend(self.audio_frames)

            # 合并所有帧为完整音频
            full_audio = np.concatenate(self.all_audio_frames, axis=0)

            # 记录完整录音时长
            full_duration = len(full_audio) / RATE
            Logger.info(f"完整录音时长: {full_duration:.2f} 秒")

            return await self.save_and_process_full_audio(full_audio)

        Logger.warning("没有收集到音频数据")
        return None

    async def save_and_process_full_audio(self, full_audio: NDArray[np.float32]) -> None | str:
        """保存并处理完整的音频文件"""
        if full_audio.size == 0:
            Logger.warning("没有录制到音频数据")
            return None

        # 保存完整的WAV文件
        time_tag = get_time_tag_with_millis()
        full_wav_path = self.cache_dir / f"full_audio_{time_tag}.wav"
        await self.save_wav(full_audio, full_wav_path)

        # 发送到ASR服务
        Logger.info(f"发送完整音频文件到ASR服务: {full_wav_path}")
        response = await async_get_asr_response(full_wav_path)

        # 清理临时文件
        if full_wav_path.exists():
            full_wav_path.unlink()

        # 处理ASR结果
        if response:
            Logger.info(f"ASR识别结果: {response.strip()}")
            return response.strip()

        Logger.warning("ASR识别返回空结果")
        return None

    async def start(self):
        """启动程序：监听唤醒词并录音"""
        running = True

        while running:
            # 监听唤醒词
            wakeup_success = await self.listen_for_wakeup()

            if wakeup_success:
                # 唤醒后开始录音
                asr_result = await self.record_and_process()

                if asr_result:
                    # 这里可以添加处理ASR结果的代码
                    settings = load_settings_file("config.toml", ServiceSettings)
                    cache_dir = Path(settings.cache_dir) / "tts"
                    cache_dir.mkdir(parents=True, exist_ok=True)
                    prompt = asr_result.strip()
                    producer = asyncio.create_task(sentence_producer(prompt))
                    tts = asyncio.create_task(tts_worker(cache_dir))
                    play = asyncio.create_task(play_worker(cache_dir=cache_dir))

                    await producer
                    await st.session_state[session_keys["sentence_que"]].join()
                    await st.session_state[session_keys["tts_que"]].join()
                    tts.cancel()
                    play.cancel()
                Logger.info("录音已完成，重新进入唤醒词监听状态")
                await asyncio.sleep(0.5)
            else:
                Logger.warning("唤醒词检测失败")
                running = False

        await self.stop()

    async def stop(self):
        """停止程序"""
        self.recording = False
        self.processing_segments = False
        await self.cleanup_wakeup_resources()
        Logger.info("程序已停止")


if __name__ == "__main__":
    recorder = VoiceRecorder()

    def handle_keyboard_interrupt():
        Logger.info("收到键盘中断，正在停止...")
        asyncio.create_task(recorder.stop())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 设置信号处理
    loop.add_signal_handler(signal.SIGINT, handle_keyboard_interrupt)

    # 运行主程序
    loop.run_until_complete(recorder.start())
    loop.close()
