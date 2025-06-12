from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING

from chatbot.console.logger import Logger

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


def file_to_opus(input_path: Path, output_path: Path):
    """
    使用 ffmpeg 将 * 文件转换为 Opus 文件，并应用指定的参数，使用 run_shell_command 执行命令。
    可以处理 MP4, MP3, AAC, FLAC, etc. 等 FFmpeg 支持的格式。
    """
    # TODO 这一步可能比较久,但是只在结束时输出, 可以考虑用 wepxct 和 pexpect
    if not input_path.exists():
        raise FileNotFoundError(f"输入文件不存在: {input_path}")

    if input_path.suffix.lower() == ".opus":
        Logger.info("文件已经是 Opus 格式，无需转换。")
        return input_path

    command = [
        "ffmpeg",
        "-y",  # 强制覆盖输出文件
        "-i",
        str(input_path.absolute()),
        "-vn",  # 禁用视频流
        "-c:a",
        "libopus",  # 音频编码器，Opus
        str(output_path.absolute()),
    ]
    try:
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.DEVNULL,  # 屏蔽子进程标准输出
            stderr=subprocess.DEVNULL,  # 屏蔽子进程错误输出
        )
    except FileNotFoundError:
        print("Error: ffmpeg not found. Please ensure ffmpeg is installed and added to PATH.")
    except subprocess.CalledProcessError as e:
        print(f"Error converting {input_path} to Opus: {e}")
