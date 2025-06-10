from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatbot.chatter._typing import PorcupineKWSConfig
    from chatbot.config_manager._typing import SystemPlatform


def handle_porcupine_keyword(system_platform: SystemPlatform):
    key_words = ["你好"]
    """获取 Porcupine 关键词和关键词特征文件路径"""
    if system_platform == "linux":
        keyword_paths = ["./models/keywords_spotting/你好_linux.ppn"]
    elif system_platform == "mac":
        keyword_paths = ["./models/keywords_spotting/你好_mac.ppn"]
    elif system_platform == "raspberry-pi":
        keyword_paths = [
            "./models/keywords_spotting/你好_raspberry-pi.ppn",
            "./models/keywords_spotting/派蒙_zh_raspberry-pi_v3_0_0.ppn",
        ]
        key_words.extend(["派蒙"])
    elif system_platform == "win":
        keyword_paths = ["./models/keywords_spotting/你好_windows.ppn"]

    keyword_config: PorcupineKWSConfig = {
        "keyword_paths": keyword_paths,
        "keywords": key_words,
    }

    return keyword_config
