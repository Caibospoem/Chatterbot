from __future__ import annotations

from typing import TypedDict


class PorcupineKWSConfig(TypedDict):
    """
    Porcupine KeyWord Spotting 配置类型。
    """

    keyword_paths: list[str]  # 关键词路径列表
    keywords: list[str]  # 关键词列表
