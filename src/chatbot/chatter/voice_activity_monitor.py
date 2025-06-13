# type: ignore
from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import numpy as np
import sounddevice as sd
import soundfile as sf

from chatbot.api.async_api import async_file_to_opus, async_get_vad_response
from chatbot.chatter import CHANNELS, RATE
from chatbot.console.logger import Logger
from chatbot.tools.timed_helper import get_time_tag_with_millis

if TYPE_CHECKING:
    from pathlib import Path

    from numpy.typing import NDArray


class VoiceActivityMonitor:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir / "vad_monitor"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.monitoring = False
        self.audio_frames: list[NDArray[np.float32]] = []
        self.all_collected_frames: list[NDArray[np.float32]] = []  # 保存所有收集的音频
        self.check_interval = 1.0  # 每秒检查一次
        self.min_audio_length = 0.5  # 最小音频长度（秒）

    def audio_callback(
        self, indata: NDArray[np.float32], _frames: int, _time: dict[str, float], status: sd.CallbackFlags
    ) -> None:
        """声音设备的回调函数"""
        if status:
            Logger.warning(f"音频回调状态: {status}")
        if self.monitoring:
            self.audio_frames.append(indata.copy())
            self.all_collected_frames.append(indata.copy())  # 同时保存到总集合中

    async def save_audio_segment(self, audio_data: NDArray[np.float32]) -> Path:
        """保存音频片段为Opus文件"""
        time_label = get_time_tag_with_millis()
        temp_wav_path = self.cache_dir / f"vad_check_{time_label}.wav"
        opus_path = self.cache_dir / f"vad_check_{time_label}.opus"

        # 保存为WAV
        sf.write(temp_wav_path, audio_data, RATE, format="WAV", subtype="PCM_16")

        # 转换为Opus
        await async_file_to_opus(temp_wav_path, opus_path)

        # 删除临时WAV文件
        temp_wav_path.unlink()

        return opus_path

    async def check_voice_activity(self, audio_segment: NDArray[np.float32]) -> bool:
        """检查音频片段是否包含语音活动"""
        if len(audio_segment) == 0:
            return False

        try:
            # 保存音频片段
            audio_path = await self.save_audio_segment(audio_segment)

            # 发送到VAD服务
            vad_result = await async_get_vad_response(audio_path)

            # 清理临时文件
            if audio_path.exists():
                audio_path.unlink()

            if not vad_result:
                return False

            # 检查是否有语音活动
            timestamps = vad_result.get("timestamp", [])
            has_voice = len(timestamps) > 0 and any(len(ts) > 0 for ts in timestamps)

            if has_voice:
                Logger.info(f"检测到语音活动: {timestamps}")

            return has_voice

        except Exception as e:
            Logger.error(f"VAD检查出错: {e}")
            return False

    async def listen_for_voice_activity(self) -> tuple[bool, NDArray[np.float32] | None]:
        """监听语音活动，返回是否检测到语音以及收集的音频数据"""
        self.monitoring = True
        self.audio_frames = []
        self.all_collected_frames = []  # 重置总音频收集

        # 计算每次检查需要的样本数
        samples_per_check = int(RATE * self.check_interval)
        min_samples = int(RATE * self.min_audio_length)

        # 启动录音流
        stream = sd.InputStream(samplerate=RATE, channels=CHANNELS, callback=self.audio_callback)
        stream.start()

        Logger.info("开始监听语音活动...")

        try:
            while self.monitoring:
                # 等待收集足够的音频数据
                await asyncio.sleep(self.check_interval)

                if not self.monitoring:
                    break

                # 检查是否有足够的音频数据
                total_samples = sum(len(frame) for frame in self.audio_frames)

                if total_samples >= min_samples:
                    # 提取音频片段进行检查
                    frames_to_check = []
                    samples_collected = 0

                    for frame in self.audio_frames:
                        frames_to_check.append(frame)
                        samples_collected += len(frame)
                        if samples_collected >= samples_per_check:
                            break

                    if frames_to_check:
                        audio_segment = np.concatenate(frames_to_check, axis=0)

                        # 检查语音活动
                        has_voice = await self.check_voice_activity(audio_segment)

                        if has_voice:
                            Logger.info("检测到语音活动！")
                            # 返回检测到语音活动以及到目前为止收集的所有音频
                            if self.all_collected_frames:
                                collected_audio = np.concatenate(self.all_collected_frames, axis=0)
                                duration = len(collected_audio) / RATE
                                Logger.info(f"返回已收集的音频数据，时长: {duration:.2f} 秒")
                                return True, collected_audio
                            else:
                                return True, None

                        # 清理已检查的帧，保留一些重叠
                        overlap_samples = int(samples_per_check * 0.2)  # 20%重叠
                        remaining_samples = 0
                        remaining_frames = []

                        # 从后往前保留重叠部分
                        for frame in reversed(self.audio_frames):
                            if remaining_samples + len(frame) <= overlap_samples:
                                remaining_frames.insert(0, frame)
                                remaining_samples += len(frame)
                            else:
                                break

                        self.audio_frames = remaining_frames

            return False, None

        finally:
            stream.stop()
            stream.close()
            self.monitoring = False

    async def cleanup_resources(self) -> None:
        """清理资源"""
        self.monitoring = False
        # 清理可能残留的临时文件
        for file_path in self.cache_dir.glob("vad_check_*.opus"):
            try:
                file_path.unlink()
            except Exception as e:
                Logger.warning(f"清理临时文件失败 {file_path}: {e}")
