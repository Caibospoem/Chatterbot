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
    short_term_memory: str  # 记录单次问答的所有内容， 以 role: user , rool: asistant 进行记录。 list[dict[str,str]]

    # 配置文件
    initial_settings: str  # 初始设置，用于存储全局配置
    sdk_base_url: str  # SDK 基础 URL
    sdk_key: str  # SDK 密钥
    vits_split_url: str  # VITS 切分 URL
    vits_direct_url: str  # VITS 直接生成 URL
    asr_url: str  # ASR URL
    vad_url: str  # VAD URL
    cache_dir: str  # 缓存目录
    access_key: str  # Picovoice porcupine 的访问密钥
    system_platform: str  # 系统平台
    promopt: str  # 提示文件路径


class VadResponse(TypedDict):
    """
    定义 VAD 响应的类型。
    """

    key: str
    timestamp: list[list[int]]
    audio_length: int
