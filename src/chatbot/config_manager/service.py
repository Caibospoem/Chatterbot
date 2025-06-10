from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, Field

from chatbot.config_manager.config import load_settings_file, search_for_settings_file

SystemPlatform = Literal["win", "linux", "mac", "raspberry-pi"]


class ServiceSettings(BaseModel):
    sdk_base_url: Annotated[str, Field("sdk_base_url", title="SDK Base URL")]
    sdk_key: Annotated[str, Field("sdk_key", title="SDK KEY")]
    vits_split_url: Annotated[str, Field("http://localhost:7900/tts/split", title="VITS Split URL")]  # 切分生成
    vits_direct_url: Annotated[str, Field("http://localhost:7900/tts/direct", title="VITS URL")]  # 直接生成
    asr_url: Annotated[str, Field("http://localhost:8000/rec-audio", title="ASR URL")]
    vad_url: Annotated[str, Field("http://localhost:8000/vad-audio", title="ASR URL")]
    cache_dir: Annotated[str, Field("cache", title="Cache Directory")]
    access_key: Annotated[str, Field("access_key", title="Access Key for Picovoice porcupine")]
    system_platform: Annotated[SystemPlatform, Field("raspberry-pi", title="System Platform")]
    promopt: Annotated[str, Field("./prompts/paimeng.txt", title="Prompt File Path")]


def main():
    # 恢复默认设置
    config_path = search_for_settings_file("config.toml")
    if config_path is not None and config_path.exists():
        config_path.unlink()
    load_settings_file("root.toml", ServiceSettings)
