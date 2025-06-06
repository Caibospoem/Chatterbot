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


def file_to_wav(input_path: Path, output_path: Path) -> None:
    """
    用 ffmpeg 把文件转换为 .wav 文件。
    """
    try:
        # 使用 ffmpeg 命令进行转换
        command = [
            "ffmpeg",
            "-i",
            str(input_path),  # 输入文件
            "-y",  # 覆盖输出文件（如果存在）
            str(output_path),  # 输出文件
        ]
        # 执行命令并等待完成
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,  # 屏蔽子进程标准输出
            stderr=subprocess.DEVNULL,  # 屏蔽子进程错误输出
        )
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please ensure ffmpeg is installed and added to PATH.")
    except Exception as e:
        print(f"Error converting {input_path} to WAV: {e}")


def get_wav_duration(wav_path: Path) -> int:
    """
    使用 FFmpeg 获取 WAV 文件的时长（以毫秒为单位）。

    参数:
        wav_path: WAV 文件路径，可以是字符串或 Path 对象。

    返回:
        时长（毫秒），如果读取失败则返回 0。
    """

    if not wav_path.exists():
        print(f"文件不存在: {wav_path}")
        return 0
    try:
        # 调用 ffprobe 获取时长
        cmd = [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            str(wav_path),
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"ffprobe 命令执行失败: {e.stderr}")
        return 0
    duration_seconds = float(result.stdout.strip())
    duration_ms = int(duration_seconds * 1000)
    return duration_ms
