from __future__ import annotations

import asyncio
import os
import subprocess
import time
from pathlib import Path

from chatbot.api.async_api import async_get_asr_response
from chatbot.console.logger import Logger
from chatbot.tools.config import RunnerSettings, load_settings_file
from chatbot.tools.timed_helper import get_time_tag_with_millis

# 音频参数
RATE = 48000  # 采样率
CHANNELS = 1  # 单声道
WINDOW_DURATION = 5.0  # 滑动窗口时长（秒）
SLIDE_INTERVAL = 2.0  # 滑动间隔（秒）
MIN_DATA_SIZE = 1000  # 最小数据量（字节）
OPUS_BITRATE = "16k"  # Opus比特率


# TODO 缺少唤醒条件, 缺少流式处理, 暂时非常费算力
class RealTimeVoiceClientAsync:
    def __init__(self):
        self.settings = load_settings_file("config.toml", RunnerSettings)
        self.cache_dir = Path(self.settings.cache_dir) / "asr"
        self.audio_buffer: asyncio.Queue[bytes] = asyncio.Queue()  # 音频数据缓冲区
        self.recording = True
        self.sending = False
        self.fast_send_mode = False  # 是否处于快速发送模式
        self.last_text_count = 0  # 上次ASR返回的文字数量
        self.text_count_unchanged = 0  # 文字数量不变的次数
        self.ffmpeg_process = None  # FFmpeg进程
        self.pending_response = False  # 是否有待处理的ASR回复
        self.last_send_time = 0  # 上次发送的时间
        self.current_audio_data: list[bytes] = []  # 当前滑动窗口内的音频数据
        self.final_text = ""  # 最终识别的文本
        if not self.cache_dir.exists():
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    async def start_ffmpeg_recording(self):
        """启动FFmpeg录音进程，录制WAV格式（未压缩PCM）"""
        input_device = "pulse" if os.name != "nt" else "dshow"
        if input_device == "pulse":
            ffmpeg_command = [
                "ffmpeg",
                "-f",
                "pulse",
                "-i",
                "default",
                "-ar",
                str(RATE),
                "-ac",
                str(CHANNELS),
                "-f",
                "s16le",
                "pipe:",
            ]
        else:
            ffmpeg_command = [
                "ffmpeg",
                "-f",
                "dshow",
                "-i",
                "audio=Microphone",
                "-ar",
                str(RATE),
                "-ac",
                str(CHANNELS),
                "-f",
                "s16le",
                "pipe:",
            ]
        try:
            self.ffmpeg_process = await asyncio.create_subprocess_exec(
                *ffmpeg_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            Logger.info("FFmpeg录音进程已启动")
            return True
        except Exception as e:
            Logger.error(f"启动FFmpeg录音失败：{e}")
            return False

    async def record_audio(self):
        """持续从FFmpeg进程读取音频数据并放入缓冲区"""
        if not await self.start_ffmpeg_recording():
            return
        chunk_size = 1024
        while self.recording:
            try:
                # TODO FFmpeg 可以通用,但是它似乎存在一些问题, 可以多参考别人
                data = await self.ffmpeg_process.stdout.read(chunk_size) if self.ffmpeg_process else b""  # type: ignore
                if data:
                    await self.audio_buffer.put(data)
                else:
                    Logger.warning("FFmpeg进程结束或无数据")
                    break
            except Exception as e:
                Logger.error(f"读取FFmpeg音频数据错误：{e}")
                await asyncio.sleep(0.1)

    def convert_wav_to_opus(self, wav_data: bytes, output_path: str):
        """将WAV数据转换为Opus格式"""
        try:
            temp_wav_path = self.cache_dir / f"temp_wav_{get_time_tag_with_millis()}.wav"
            with temp_wav_path.open("wb") as f:
                f.write(self.create_wav_header(len(wav_data)))
                f.write(wav_data)
            subprocess.run(
                ["ffmpeg", "-i", str(temp_wav_path), "-c:a", "libopus", "-b:a", OPUS_BITRATE, "-y", output_path],
            )
            temp_wav_path.unlink(missing_ok=True)  # 删除临时WAV文件
            return True
        except Exception as e:
            Logger.error(f"转换WAV到Opus失败：{e}")
            return False

    def create_wav_header(self, data_size: int):
        """创建WAV文件头部"""
        import struct

        sample_rate = RATE
        channels = CHANNELS
        bits_per_sample = 16
        byte_rate = sample_rate * channels * bits_per_sample // 8
        block_align = channels * bits_per_sample // 8
        header = b"RIFF"
        header += struct.pack("<L", 36 + data_size)
        header += b"WAVE"
        header += b"fmt "
        header += struct.pack("<L", 16)
        header += struct.pack("<H", 1)
        header += struct.pack("<H", channels)
        header += struct.pack("<L", sample_rate)
        header += struct.pack("<L", byte_rate)
        header += struct.pack("<H", block_align)
        header += struct.pack("<H", bits_per_sample)
        header += b"data"
        header += struct.pack("<L", data_size)
        return header

    async def receive_asr_response(self, audio_path: str):
        """接收ASR回复"""
        audio_file_path = Path(audio_path)
        if not audio_file_path.exists():
            Logger.error(f"音频文件不存在：{audio_path}")
            return None
        text: str = await async_get_asr_response(audio_file_path)
        return text

    def handle_asr_response(self, response: str):
        """处理ASR回复，调整发送模式"""
        text = response.strip() if response else ""
        self.pending_response = False
        if text:
            text_count = len(text)
            self.final_text = text  # 更新最终识别文本
            Logger.info(f"收到ASR回复：{text}，文字数量：{text_count}")
            if not self.fast_send_mode:
                self.fast_send_mode = True
                Logger.info("检测到文字，进入快速发送模式")
            else:
                if text_count == self.last_text_count:
                    self.text_count_unchanged += 1
                    if self.text_count_unchanged >= 2:
                        Logger.info(f"文字数量连续两次不变，停止录音，最终识别结果：{self.final_text}")
                        self.recording = False
                else:
                    self.text_count_unchanged = 0
            self.last_text_count = text_count
        else:
            self.fast_send_mode = False
            self.text_count_unchanged = 0

    async def send_audio(self):
        """异步处理音频数据并获取ASR结果，使用自适应滑动窗口"""
        bytes_per_second = RATE * CHANNELS * 2  # 每秒字节数 (16位PCM)
        window_size = int(WINDOW_DURATION * bytes_per_second)  # 初始窗口大小（字节）
        slide_size = int(SLIDE_INTERVAL * bytes_per_second)  # 滑动大小（字节）
        self.last_send_time = time.time()
        while self.recording:
            try:
                # 从缓冲区获取音频数据
                while True:
                    try:
                        data = await asyncio.wait_for(self.audio_buffer.get(), timeout=0.01)
                        self.current_audio_data.append(data)
                    except TimeoutError:
                        break
                current_time = time.time()
                # 正常模式下每2秒滑动一次，快速模式下收到回复立即发送
                if (not self.fast_send_mode and current_time - self.last_send_time >= SLIDE_INTERVAL) or (
                    self.fast_send_mode and not self.pending_response
                ):
                    if self.current_audio_data:
                        audio_data = b"".join(self.current_audio_data)
                        if len(audio_data) < MIN_DATA_SIZE:
                            Logger.warning(f"音频数据过小（{len(audio_data)}字节），等待更多数据")
                            await asyncio.sleep(0.5)
                            continue
                        # 快速模式下不丢弃数据，允许窗口自适应扩展
                        if self.fast_send_mode:
                            Logger.info(f"快速模式：窗口自适应扩展，当前数据长度：{len(audio_data)}字节")
                        else:
                            # 正常模式下，如果数据超过窗口大小，丢弃前面的数据
                            if len(audio_data) > window_size:
                                audio_data = audio_data[-window_size:]
                                self.current_audio_data = [audio_data]
                            # 正常模式下滑动窗口：丢弃前2秒的数据
                            if len(audio_data) > slide_size:
                                audio_data = audio_data[slide_size:]
                                self.current_audio_data = [audio_data] if audio_data else []
                        # 保存音频数据并转换为Opus
                        temp_opus_path = self.cache_dir / f"{get_time_tag_with_millis()}.opus"
                        if self.convert_wav_to_opus(audio_data, str(temp_opus_path)):
                            Logger.info(f"保存Opus编码音频数据到文件：{temp_opus_path}，长度：{len(audio_data)}字节")
                        else:
                            Logger.error("转换音频文件失败")
                            continue
                        self.last_send_time = current_time
                        self.pending_response = True
                        response = await self.receive_asr_response(str(temp_opus_path))
                        if response:
                            self.handle_asr_response(response)
                    await asyncio.sleep(0.01)
            except Exception as e:
                Logger.error(f"处理音频错误：{e}")
                await asyncio.sleep(0.5)

    async def start(self):
        """启动录音和发送任务"""
        record_task = asyncio.create_task(self.record_audio())
        send_task = asyncio.create_task(self.send_audio())
        await asyncio.gather(record_task, send_task)

    async def stop(self):
        """停止录音和发送"""
        self.recording = False
        if self.ffmpeg_process:
            self.ffmpeg_process.terminate()
            await self.ffmpeg_process.wait()
        Logger.info("程序已停止")


if __name__ == "__main__":
    client = RealTimeVoiceClientAsync()
    try:
        asyncio.run(client.start())
    except KeyboardInterrupt:
        asyncio.run(client.stop())
