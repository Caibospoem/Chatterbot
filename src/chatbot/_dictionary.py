from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chatbot._typing import StSessionSateKeys

session_keys: StSessionSateKeys = {
    "text_response": "text_response",
    "sentences": "sentences",
    "static_que": "static_que",
    "sentence_que": "sentence_que",
    "tts_que": "tts_que",
    "initial_settings": "initial_settings",
    "sdk_base_url": "sdk_base_url",
    "sdk_key": "sdk_key",
    "vits_split_url": "vits_split_url",
    "vits_direct_url": "vits_direct_url",
    "asr_url": "asr_url",
    "vad_url": "vad_url",
    "cache_dir": "cache_dir",
    "access_key": "access_key",
    "system_platform": "system_platform",
    "promopt": "promopt",
}
