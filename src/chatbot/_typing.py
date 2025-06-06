from __future__ import annotations

from typing import TypedDict


class StSessionSateKeys(TypedDict):
    """
    定义状态会话的键类型。
    """

    text_response: str  # 用于 openai 的文本响应
    sentences: str  # 拆分后的句子列表
    static_que: str  # 静态队列，用于存储音频文件路径, 为了保持逻辑一致性设置
    sentence_que: str  # 动态队列，用于存储句子
    tts_que: str  # 动态队列，用于存储 TTS 音频文件路径


class VadResponse(TypedDict):
    """
    定义 VAD 响应的类型。
    """

    key: str
    time_stamp: list[list[int]]
    audio_length: int
