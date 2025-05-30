from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def play_opus_file(file_path: Path):
    try:
        # 使用 ffplay 播放 Opus 文件
        # -nodisp 参数用于隐藏视频窗口（如果文件有视频）
        subprocess.run(["ffplay", "-nodisp", "-autoexit", str(file_path)], check=True)
        print("音频播放完成。")
    except FileNotFoundError:
        print("ffplay 未找到，请确保 FFmpeg 已安装。")
    except subprocess.CalledProcessError as e:
        print(f"播放错误: {e}")
