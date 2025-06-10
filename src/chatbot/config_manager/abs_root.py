from __future__ import annotations

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field

from chatbot.config_manager.config import load_settings_file, write_settings_file


class RootAbsDir(BaseModel):
    root_dir: Annotated[str, Field("", title="项目根目录")]  # 项目根目录, 运行时计算绝对路径.


def main():
    # 把当前的 root_dir 写入到配置文件中
    ROOT_DIR = Path(__file__).parent.parent.parent.parent
    settings = load_settings_file("root.toml", RootAbsDir)
    settings.root_dir = str(ROOT_DIR)
    write_settings_file("root.toml", settings)
    return settings
