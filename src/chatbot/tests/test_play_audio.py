from __future__ import annotations

import argparse
from pathlib import Path

from chatbot.console.logger import Logger
from chatbot.tools.audio import play_opus_file


def main():
    parser = argparse.ArgumentParser(description="Play an opus audio file.")
    parser.add_argument("--input_file", "-i", type=str, help="Path to the opus audio file to play.")
    args = parser.parse_args()
    input_file = Path(args.input_file)
    if not input_file.exists():
        Logger.error(f"File {input_file} does not exist.")
        return
    else:
        play_opus_file(input_file)
