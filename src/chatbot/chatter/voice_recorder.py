from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING

import numpy as np
import sounddevice as sd
import soundfile as sf

from chatbot.api.async_api import async_get_asr_response, async_get_vad_response
from chatbot.chatter import CHANNELS, INITIAL_WAIT_TIME, MAX_RECORDING_TIME, RATE, SEGMENT_DURATION, SILENCE_THRESHOLD
from chatbot.console.logger import Logger
from chatbot.tools.timed_helper import get_time_tag_with_millis

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


class VoiceRecorder:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / "asr"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.recording = False
        self.audio_frames: list[NDArray[np.float32]] = []  # 临时缓冲区，用于从回调中收集帧
        self.all_audio_frames: list[NDArray[np.float32]] = []  # 保存所有录制的帧
        self.audio_length = 0  # 录音时长（秒）
        # 分段处理状态
        self.segments_to_process: list[tuple[NDArray[np.float32], int]] = []
        self.processing_segments = False

    def audio_callback(
        self, indata: NDArray[np.float32], _frames: int, _time: dict[str, float], status: sd.CallbackFlags
    ) -> None:  # type: ignore
        """声音设备的回调函数"""
        if status:
            Logger.warning(f"音频回调状态: {status}")
        if self.recording:
            # 将音频帧添加到临时缓冲区
            self.audio_frames.append(indata.copy())

    async def save_wav(self, audio_data: NDArray[np.float32], file_path: Path) -> Path:
        """将音频数据保存为WAV文件"""
        sf.write(file_path, audio_data, RATE, format="WAV", subtype="PCM_16")  # type: ignore[arg-type]
        Logger.info(f"已保存WAV文件: {file_path}")
        return file_path

    async def process_segments(self) -> None:
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

    async def record_and_process(self) -> None | str:
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
