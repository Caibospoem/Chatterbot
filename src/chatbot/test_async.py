from __future__ import annotations

import asyncio
import logging

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api import get_openai_response_stream
from chatbot.console.logger import Badge, Logger

streamlit_loggers = [
    logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态


async def show_response_stream(prompt: str):
    async for sentence in get_openai_response_stream(prompt):
        Logger.custom(
            sentence,
            badge=Badge("零壹万物", fore="black", back="cyan"),
        )
        await asyncio.sleep(0.1)  # 加点停顿


async def main():
    while True:
        user_prompt = input("请输入:")
        await show_response_stream(user_prompt)


if __name__ == "__main__":
    asyncio.run(main())
