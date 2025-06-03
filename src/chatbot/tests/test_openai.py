from __future__ import annotations

import logging

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api.sync_api import (
    get_openai_response,
)
from chatbot.console.logger import Badge, Logger, set_logger_debug
from chatbot.tools.timed_helper import timed_function

streamlit_loggers = [
    logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别

set_logger_debug()

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态


time_get_openai_response = timed_function(get_openai_response)


def main():
    while True:
        user_prompt = input("请输入:")  # 获取用户输入
        time_get_openai_response(user_prompt)  # 模拟获取ASR响应
        Logger.custom(
            st.session_state[session_keys["text_response"]],
            badge=Badge("零壹万物", fore="black", back="cyan"),
        )
