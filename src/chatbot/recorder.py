# from __future__ import annotations

# import asyncio
# import os
# import signal
# import struct
# from pathlib import Path

# import pvporcupine
# from funasr import AutoModel
# from pvrecorder import PvRecorder

# from chatbot.api.async_api import async_get_asr_response
# from chatbot.config_manager.config import ServiceSettings, load_settings_file
# from chatbot.console.logger import Logger
# from chatbot.tools.audio import get_wav_duration
# from chatbot.tools.timed_helper import get_time_tag_with_millis

# # 音频参数
# RATE = 48000  # 采样率
# CHANNELS = 1  # 单声道
# WINDOW_DURATION = 5.0  # 滑动窗口时长（秒）
# SLIDE_INTERVAL = 2.0  # 滑动间隔（秒）
# MIN_DATA_SIZE = 1000  # 最小数据量（字节）
# SILENCE_THRESHOLD = 1500  # 静音检测阈值（毫秒）


# def create_wav_header(sample_rate, channels, bits_per_sample, data_size):
#     """创建WAV文件头"""
#     # WAV文件头格式
#     header = bytearray()

#     # RIFF chunk
#     header.extend(b"RIFF")
#     header.extend(struct.pack("<I", 36 + data_size))  # 文件大小 - 8
#     header.extend(b"WAVE")

#     # fmt chunk
#     header.extend(b"fmt ")
#     header.extend(struct.pack("<I", 16))  # fmt chunk大小
#     header.extend(struct.pack("<H", 1))  # 音频格式 (PCM)
#     header.extend(struct.pack("<H", channels))  # 声道数
#     header.extend(struct.pack("<I", sample_rate))  # 采样率
#     header.extend(struct.pack("<I", sample_rate * channels * bits_per_sample // 8))  # 字节率
#     header.extend(struct.pack("<H", channels * bits_per_sample // 8))  # 块对齐
#     header.extend(struct.pack("<H", bits_per_sample))  # 位深度

#     # data chunk
#     header.extend(b"data")
#     header.extend(struct.pack("<I", data_size))  # 数据大小

#     return header


# def save_wav_file(audio_data: bytes, file_path: Path, sample_rate=RATE, channels=CHANNELS, bits_per_sample=16):
#     """保存音频数据为WAV文件"""
#     try:
#         wav_header = create_wav_header(sample_rate, channels, bits_per_sample, len(audio_data))
#         with file_path.open("wb") as f:
#             f.write(wav_header)
#             f.write(audio_data)
#         Logger.info(f"成功保存WAV文件：{file_path} (大小: {len(audio_data)} 字节)")
#         return True
#     except Exception as e:
#         Logger.error(f"保存WAV文件失败：{e}")
#         return False


# class RealTimeVoiceClientAsync:
#     def __init__(self):
#         self.settings = load_settings_file("config.toml", ServiceSettings)
#         self.cache_dir = Path(self.settings.cache_dir) / "asr"
#         self.recording = False
#         self.sending = False
#         self.ffmpeg_process = None
#         self.final_text = ""
#         # 唤醒词相关配置
#         self.access_key = self.settings.access_key
#         self.keyword_paths = ["./models/keywords_spotting/派蒙派蒙_zh_linux_v3_0_0.ppn"]
#         self.keywords = ["派蒙派蒙"]
#         self.porcupine = None
#         self.wakeup_recorder = None
#         # VAD 模型
#         self.vad_model = AutoModel(
#             model="./models/speech_fsmn_vad_zh-cn-16k-common-pytorch",
#             device="cpu",
#             disable_update=True,
#         )
#         self.last_activity = 0  # 上次语音活动结束时间
#         self.audio_length = 0  # 当前音频总长度
#         self.vad_in_progress = False  # 标记是否正在进行VAD检测
#         self.full_audio_data = bytearray()  # 保存完整的音频数据用于最终ASR

#         if not self.cache_dir.exists():
#             self.cache_dir.mkdir(parents=True, exist_ok=True)

#     def initialize_wakeup(self):
#         """初始化唤醒词检测"""
#         try:
#             # 清理之前的资源
#             if self.porcupine:
#                 self.porcupine.delete()
#                 self.porcupine = None
#             if self.wakeup_recorder:
#                 try:
#                     self.wakeup_recorder.stop()
#                 except:
#                     pass
#                 self.wakeup_recorder.delete()
#                 self.wakeup_recorder = None

#             self.porcupine = pvporcupine.create(
#                 access_key=self.access_key,
#                 keyword_paths=self.keyword_paths,
#                 model_path="./models/keywords_spotting/porcupine_params_zh.pv",
#             )
#             self.wakeup_recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
#             Logger.info("唤醒词检测初始化成功")
#             return True
#         except Exception as e:
#             Logger.error(f"初始化唤醒词检测失败：{e}")
#             return False

#     async def listen_for_wakeup(self):
#         """监听唤醒词，直到检测到为止"""
#         if not self.initialize_wakeup():
#             return False

#         try:
#             self.wakeup_recorder.start()
#             Logger.info("开始监听唤醒词...")
#             while True:
#                 keyword_index = self.porcupine.process(self.wakeup_recorder.read())
#                 if keyword_index >= 0:
#                     Logger.info(f"检测到唤醒词：{self.keywords[keyword_index]}")
#                     return True
#                 await asyncio.sleep(0.01)
#         except Exception as e:
#             Logger.error(f"唤醒词监听过程中发生错误：{e}")
#             return False
#         finally:
#             # 清理唤醒词检测资源
#             try:
#                 if self.wakeup_recorder:
#                     self.wakeup_recorder.stop()
#             except:
#                 pass

#     async def cleanup_wakeup_resources(self):
#         """清理唤醒词检测资源"""
#         try:
#             if self.wakeup_recorder:
#                 try:
#                     self.wakeup_recorder.stop()
#                 except:
#                     pass
#                 self.wakeup_recorder.delete()
#                 self.wakeup_recorder = None
#             if self.porcupine:
#                 self.porcupine.delete()
#                 self.porcupine = None
#         except Exception as e:
#             Logger.error(f"清理唤醒词资源失败：{e}")

#     async def start_ffmpeg_recording(self):
#         """启动FFmpeg录音进程，录制原始PCM格式"""
#         # 确保之前的FFmpeg进程已终止
#         await self.cleanup_ffmpeg_process()

#         input_device = "pulse" if os.name != "nt" else "dshow"
#         if input_device == "pulse":
#             ffmpeg_command = [
#                 "ffmpeg",
#                 "-f",
#                 "pulse",
#                 "-i",
#                 "default",
#                 "-ar",
#                 str(RATE),
#                 "-ac",
#                 str(CHANNELS),
#                 "-f",
#                 "s16le",  # 输出16位PCM格式
#                 "-",  # 输出到stdout
#             ]
#         else:
#             ffmpeg_command = [
#                 "ffmpeg",
#                 "-f",
#                 "dshow",
#                 "-i",
#                 "audio=Microphone",
#                 "-ar",
#                 str(RATE),
#                 "-ac",
#                 str(CHANNELS),
#                 "-f",
#                 "s16le",  # 输出16位PCM格式
#                 "-",  # 输出到stdout
#             ]
#         try:
#             self.ffmpeg_process = await asyncio.create_subprocess_exec(
#                 *ffmpeg_command,
#                 stdout=asyncio.subprocess.PIPE,
#                 stderr=asyncio.subprocess.DEVNULL,  # 忽略stderr避免缓冲区问题
#                 stdin=asyncio.subprocess.DEVNULL,  # 关闭stdin
#             )
#             Logger.info("FFmpeg录音进程已启动")
#             return True
#         except Exception as e:
#             Logger.error(f"启动FFmpeg录音失败：{e}")
#             return False

#     async def cleanup_ffmpeg_process(self):
#         """清理FFmpeg进程"""
#         if self.ffmpeg_process:
#             try:
#                 # 首先尝试优雅地终止进程
#                 if self.ffmpeg_process.returncode is None:
#                     self.ffmpeg_process.terminate()
#                     try:
#                         await asyncio.wait_for(self.ffmpeg_process.wait(), timeout=1.0)
#                         Logger.info("FFmpeg进程已正常终止")
#                     except asyncio.TimeoutError:
#                         Logger.warning("FFmpeg进程未及时终止，强制杀死")
#                         self.ffmpeg_process.kill()
#                         try:
#                             await asyncio.wait_for(self.ffmpeg_process.wait(), timeout=1.0)
#                             Logger.info("FFmpeg进程已被强制终止")
#                         except asyncio.TimeoutError:
#                             Logger.error("无法终止FFmpeg进程")
#             except Exception as e:
#                 Logger.error(f"清理FFmpeg进程时出错：{e}")
#             finally:
#                 self.ffmpeg_process = None

#     async def run_vad(self, audio_path: Path):
#         """运行VAD检测，返回检测结果"""
#         try:
#             res = await asyncio.to_thread(self.vad_model.generate, input=str(audio_path))
#             if res and len(res) > 0 and "value" in res[0] and res[0]["value"]:
#                 last_activity = res[0]["value"][-1][-1] if res[0]["value"][-1] else 0
#                 audio_length = get_wav_duration(audio_path)
#                 return {"last_activity": last_activity, "audio_length": audio_length}
#             return None
#         except Exception as e:
#             Logger.error(f"VAD检测失败：{e}")
#             return None
#         finally:
#             self.vad_in_progress = False

#     async def record_audio(self):
#         """持续从FFmpeg进程读取音频数据并处理"""
#         # 重置状态
#         self.vad_in_progress = False
#         self.last_activity = 0
#         self.audio_length = 0

#         if not await self.start_ffmpeg_recording():
#             Logger.error("无法启动FFmpeg录音进程")
#             return

#         chunk_size = 4096  # 增加chunk大小
#         temp_audio_data = bytearray()
#         self.full_audio_data = bytearray()  # 重置完整音频数据
#         bytes_per_window = int(RATE * CHANNELS * 2 * WINDOW_DURATION)  # 16位=2字节

#         Logger.info("开始录音...")
#         try:
#             while self.recording:
#                 try:
#                     if not self.ffmpeg_process or self.ffmpeg_process.returncode is not None:
#                         Logger.error("FFmpeg进程已终止")
#                         break

#                     # 使用超时读取，避免无限等待
#                     data = await asyncio.wait_for(self.ffmpeg_process.stdout.read(chunk_size), timeout=1.0)

#                     if data:
#                         self.full_audio_data.extend(data)  # 保存到完整音频数据中
#                         temp_audio_data.extend(data)
#                         if len(temp_audio_data) >= bytes_per_window:
#                             await self.process_audio(temp_audio_data[:bytes_per_window])
#                             # 滑动窗口：移除已处理的部分
#                             slide_bytes = int(RATE * CHANNELS * 2 * SLIDE_INTERVAL)
#                             temp_audio_data = temp_audio_data[slide_bytes:]
#                     else:
#                         Logger.warning("FFmpeg进程结束或无数据")
#                         break

#                 except asyncio.TimeoutError:
#                     # 读取超时，检查是否应该继续录音
#                     if not self.recording:
#                         break
#                     continue
#                 except Exception as e:
#                     Logger.error(f"读取FFmpeg音频数据错误：{e}")
#                     break

#         except Exception as e:
#             Logger.error(f"录音过程中发生错误：{e}")
#         finally:
#             Logger.info("录音结束")
#             await self.cleanup_ffmpeg_process()

#     async def process_audio(self, audio_data: bytes):
#         """处理音频数据并保存为临时WAV文件，运行VAD检测"""
#         if len(audio_data) < MIN_DATA_SIZE:
#             Logger.warning(f"音频数据过小（{len(audio_data)}字节），跳过处理")
#             return

#         temp_wav_path = self.cache_dir / f"temp_wav_{get_time_tag_with_millis()}.wav"
#         try:
#             # 使用自定义函数保存WAV文件
#             if not save_wav_file(audio_data, temp_wav_path):
#                 return

#             if not self.vad_in_progress:
#                 self.vad_in_progress = True
#                 vad_result = await self.run_vad(temp_wav_path)
#                 if vad_result:
#                     self.last_activity = vad_result["last_activity"]
#                     self.audio_length = vad_result["audio_length"]
#                     Logger.info(f"VAD结果：last_activity={self.last_activity}, audio_length={self.audio_length}")
#                     if self.audio_length - self.last_activity > SILENCE_THRESHOLD:
#                         Logger.info(f"检测到长时间静音（{self.audio_length - self.last_activity}ms），停止录音")
#                         self.recording = False
#                         # 保存完整音频数据用于最终ASR
#                         full_wav_path = self.cache_dir / f"full_wav_{get_time_tag_with_millis()}.wav"
#                         if save_wav_file(self.full_audio_data, full_wav_path):
#                             await self.send_audio_to_asr(full_wav_path)
#                             full_wav_path.unlink(missing_ok=True)
#                 else:
#                     Logger.warning("VAD结果为空，跳过处理")
#             else:
#                 Logger.info("当前有VAD检测正在进行中，跳过本次检测")
#         except Exception as e:
#             Logger.error(f"处理音频数据失败：{e}")
#             self.vad_in_progress = False
#         finally:
#             if temp_wav_path.exists():
#                 temp_wav_path.unlink(missing_ok=True)

#     async def send_audio_to_asr(self, audio_path: Path):
#         """发送音频文件到ASR服务"""
#         if not audio_path.exists():
#             Logger.error(f"音频文件不存在：{audio_path}")
#             return
#         response = await async_get_asr_response(audio_path)
#         if response:
#             self.final_text = response.strip()
#             Logger.info(f"最终ASR识别结果：{self.final_text}")

#     async def start(self):
#         """启动程序：先监听唤醒词，检测到后开始录音"""
#         try:
#             while True:
#                 # 清理之前的唤醒词资源
#                 await self.cleanup_wakeup_resources()

#                 if await self.listen_for_wakeup():
#                     # 清理唤醒词资源，准备录音
#                     await self.cleanup_wakeup_resources()

#                     # 开始录音
#                     self.recording = True
#                     await self.record_audio()
#                 else:
#                     Logger.warning("唤醒词检测失败，程序退出")
#                     break

#                 Logger.info("录音已完成，重新进入唤醒词监听状态")
#                 await asyncio.sleep(0.5)  # 减少等待时间
#         except asyncio.CancelledError:
#             Logger.info("程序被取消，正在停止...")
#             await self.stop()
#         except KeyboardInterrupt:
#             Logger.info("收到键盘中断，正在停止...")
#             await self.stop()

#     async def stop(self):
#         """停止录音和发送"""
#         self.recording = False
#         await self.cleanup_ffmpeg_process()
#         await self.cleanup_wakeup_resources()
#         Logger.info("程序已停止")


# if __name__ == "__main__":
#     client = RealTimeVoiceClientAsync()
#     try:
#         asyncio.run(client.start())
#     except KeyboardInterrupt:
#         asyncio.run(client.stop())
