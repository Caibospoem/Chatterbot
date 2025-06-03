from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path


def play_opus_file(file_path: Path):
    try:
        subprocess.run(
            [
                "ffplay",
                "-nodisp",
                "-autoexit",
                "-loglevel",
                "quiet",  # 关闭所有ffplay输出
                str(file_path),
            ],
            check=True,
            stdout=subprocess.DEVNULL,  # 屏蔽子进程标准输出
            stderr=subprocess.DEVNULL,  # 屏蔽子进程错误输出
        )
    except FileNotFoundError:
        print("ffplay 未找到，请确保 FFmpeg 已安装。")
    except subprocess.CalledProcessError as e:
        print(f"播放错误: {e}")
