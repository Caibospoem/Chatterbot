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
}
