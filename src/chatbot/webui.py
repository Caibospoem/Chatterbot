from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from chatbot.config_manager import get_root_dir
from chatbot.styles.global_style import style

style(True)


def main():
    os.environ["KMP_DUPLICATE_LIB_OK"] = "True"

    root_dir_settings = get_root_dir()
    ROOT_DIR = Path(root_dir_settings.root_dir)

    # 所有页面路径基于 ROOT_DIR 计算
    PAGE_PATHS = {
        "home": ROOT_DIR / "src" / "chatbot" / "pages" / "home.py",
        "settings": ROOT_DIR / "src" / "chatbot" / "pages" / "setting.py",
    }
    # 检查路径是否存在
    for name, path in PAGE_PATHS.items():
        if not path.exists():
            raise FileNotFoundError(f"Page '{name}' not found at: {path}")

    # 在 st.Page() 中使用字符串路径（确保是绝对路径的字符串形式）
    pages = {
        "Home": [
            st.Page(page=str(PAGE_PATHS["home"]), title="主页", icon=":material/home:"),
            st.Page(
                page=str(PAGE_PATHS["settings"]),
                title="全局设置",
                icon=":material/settings:",
            ),
        ],
    }
    pg = st.navigation(pages, position="sidebar")
    pg.run()


if __name__ == "__main__":
    main()
