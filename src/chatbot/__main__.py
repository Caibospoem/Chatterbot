# type: ignore
from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path
from typing import TYPE_CHECKING

from chatbot.chatter.audio_processing_workflow import initialize_session_state, process_voice_command
from chatbot.chatter.voice_activity_monitor import VoiceActivityMonitor  # 新增
from chatbot.chatter.voice_recorder import VoiceRecorder
from chatbot.chatter.wake_word_detector import WakeWordDetector
from chatbot.config_manager import ServiceSettings, load_settings_file
from chatbot.console.logger import Logger, set_logger_debug

if TYPE_CHECKING:
    import numpy as np
    from numpy.typing import NDArray


# 配置日志
def configure_logging() -> None:
    streamlit_loggers = [
        logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
    ]
    for logger in streamlit_loggers:
        logger.setLevel(logging.ERROR)
    set_logger_debug()


class VoiceAssistant:
    def __init__(self):
        configure_logging()
        initialize_session_state()
        self.settings = load_settings_file("config.toml", ServiceSettings)
        self.cache_dir = Path(self.settings.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        self.wake_detector = WakeWordDetector(
            access_key=self.settings.access_key, system_platform=self.settings.system_platform
        )
        self.voice_recorder = VoiceRecorder(cache_dir=self.cache_dir)
        self.voice_monitor = VoiceActivityMonitor(cache_dir=self.cache_dir)  # 新增

        self.is_awake = False  # 跟踪唤醒状态
        self.keep_alive_timeout = 10.0  # 保持唤醒的超时时间（秒）

    async def start(self) -> None:
        """启动程序：监听唤醒词并录音"""
        running = True
        while running:
            if not self.is_awake:
                # 未唤醒状态：监听唤醒词
                wakeup_success = await self.wake_detector.listen_for_wakeup()
                if wakeup_success:
                    self.is_awake = True
                    Logger.info("已唤醒，进入对话模式")
                    # 首次唤醒后立即开始录音
                    await self.handle_conversation()
                else:
                    Logger.warning("唤醒词检测失败")
                    running = False
            else:
                # 已唤醒状态：保持活跃并监听语音活动
                await self.keep_alive_and_listen()

        await self.stop()

    async def keep_alive_and_listen(self) -> None:
        """保持唤醒状态并监听语音活动"""
        Logger.info(f"保持唤醒状态，监听语音活动（超时时间：{self.keep_alive_timeout}秒）")

        try:
            # 监听语音活动，带超时，现在返回音频数据
            result = await asyncio.wait_for(
                self.voice_monitor.listen_for_voice_activity(), timeout=self.keep_alive_timeout
            )

            voice_detected, pre_collected_audio = result

            if voice_detected:
                Logger.info("检测到语音活动，开始新的对话")
                # 将预收集的音频传递给录音器
                if pre_collected_audio is not None:
                    await self.handle_conversation_with_pre_audio(pre_collected_audio)
                else:
                    await self.handle_conversation()
            else:
                Logger.info("未检测到语音活动")
                self.is_awake = False

        except TimeoutError:
            Logger.info(f"{self.keep_alive_timeout}秒内未检测到语音活动，进入睡眠状态")
            self.is_awake = False
        except Exception as e:
            Logger.error(f"语音活动监听出错: {e}")
            self.is_awake = False

    async def handle_conversation_with_pre_audio(self, pre_collected_audio: NDArray[np.float32]) -> None:
        """处理带有预收集音频的对话"""
        asr_result = await self.voice_recorder.record_with_pre_collected_audio(pre_collected_audio)
        if asr_result:
            await process_voice_command(asr_result, self.cache_dir)
            Logger.info("对话处理完成")
        else:
            Logger.warning("未获取到有效的语音输入")

    async def handle_conversation(self) -> None:
        """处理一次完整的对话"""
        asr_result = await self.voice_recorder.record_and_process()
        if asr_result:
            await process_voice_command(asr_result, self.cache_dir)
            Logger.info("对话处理完成")
        else:
            Logger.warning("未获取到有效的语音输入")

    async def stop(self) -> None:
        """停止程序"""
        await self.wake_detector.cleanup_resources()
        await self.voice_monitor.cleanup_resources()
        Logger.info("程序已停止")


if __name__ == "__main__":
    assistant = VoiceAssistant()

    def handle_keyboard_interrupt() -> None:
        Logger.info("收到键盘中断，正在停止...")
        asyncio.create_task(assistant.stop())

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 设置信号处理
    loop.add_signal_handler(signal.SIGINT, handle_keyboard_interrupt)

    # 运行主程序
    loop.run_until_complete(assistant.start())
    loop.close()
