from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path

from chatbot.chatter.audio_processing_workflow import initialize_session_state, process_voice_command
from chatbot.chatter.voice_recorder import VoiceRecorder
from chatbot.chatter.wake_word_detector import WakeWordDetector
from chatbot.config_manager import ServiceSettings, load_settings_file
from chatbot.console.logger import Logger, set_logger_debug


# 配置日志
def configure_logging() -> None:
    streamlit_loggers = [
        logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
    ]
    for logger in streamlit_loggers:
        logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别
    set_logger_debug()  # 设置日志记录器为调试模式


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

    async def start(self) -> None:
        """启动程序：监听唤醒词并录音"""
        running = True
        while running:
            # 监听唤醒词
            wakeup_success = await self.wake_detector.listen_for_wakeup()
            if wakeup_success:
                # 唤醒后开始录音
                asr_result = await self.voice_recorder.record_and_process()
                if asr_result:
                    # 处理ASR结果
                    await process_voice_command(asr_result, self.cache_dir)
                Logger.info("录音已完成，重新进入唤醒词监听状态")
                await asyncio.sleep(0.5)
            else:
                Logger.warning("唤醒词检测失败")
                running = False
        await self.stop()

    async def stop(self) -> None:
        """停止程序"""
        await self.wake_detector.cleanup_resources()
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
