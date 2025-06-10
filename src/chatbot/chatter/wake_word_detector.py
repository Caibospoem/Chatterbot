from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import pvporcupine
from pvrecorder import PvRecorder

from chatbot.chatter.util import handle_porcupine_keyword
from chatbot.console.logger import Logger

if TYPE_CHECKING:
    from chatbot.config_manager._typing import SystemPlatform


class WakeWordDetector:
    def __init__(self, access_key: str, system_platform: SystemPlatform):
        self.access_key = access_key
        self.system_platform: SystemPlatform = system_platform
        self.porcupine = None
        self.wakeup_recorder = None
        self.initialize_keyword_paths()

    def initialize_keyword_paths(self) -> None:
        keyword_config = handle_porcupine_keyword(self.system_platform)
        self.keyword_paths = keyword_config["keyword_paths"]
        self.keywords = keyword_config["keywords"]

    async def cleanup_resources(self) -> None:
        """清理唤醒词检测资源"""
        if self.wakeup_recorder:
            if hasattr(self.wakeup_recorder, "is_recording") and self.wakeup_recorder.is_recording:
                self.wakeup_recorder.stop()
            self.wakeup_recorder.delete()
            self.wakeup_recorder = None
        if self.porcupine:
            self.porcupine.delete()
            self.porcupine = None

    async def initialize(self) -> bool:
        """初始化唤醒词检测"""
        await self.cleanup_resources()
        self.porcupine = pvporcupine.create(  # type: ignore[arg-type]
            access_key=self.access_key,
            keyword_paths=self.keyword_paths,
            model_path="./models/keywords_spotting/porcupine_params_zh.pv",
        )
        self.wakeup_recorder = PvRecorder(device_index=-1, frame_length=self.porcupine.frame_length)
        Logger.info("唤醒词检测初始化成功")
        return True

    async def listen_for_wakeup(self) -> bool:
        """监听唤醒词，直到检测到为止"""
        await self.initialize()
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
