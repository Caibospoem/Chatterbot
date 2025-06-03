from __future__ import annotations

import logging
from collections import deque
from pathlib import Path

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api.sync_api import (
    get_asr_response,
    get_openai_response,
    get_tts_response,
    write_tts_response,
)
from chatbot.console.logger import Badge, Logger, set_logger_debug
from chatbot.tools.config import RunnerSettings, load_settings_file
from chatbot.tools.play_audio import play_opus_file
from chatbot.tools.timed_helper import get_time_tag_with_millis, timed_function

streamlit_loggers = [
    logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别

set_logger_debug()

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态
if session_keys["static_que"] not in st.session_state:
    st.session_state[session_keys["static_que"]] = deque()


time_get_asr_response = timed_function(get_asr_response)
time_get_tts_response = timed_function(get_tts_response)
time_write_tts_response = timed_function(write_tts_response)
time_get_openai_response = timed_function(get_openai_response)
time_play_opus_file = timed_function(play_opus_file)


def main():
    settings = load_settings_file("config.toml", RunnerSettings)
    cache_dir = Path(settings.cache_dir)
    if not cache_dir.exists():
        cache_dir.mkdir(parents=True, exist_ok=True)
    # 防止 cache 过多,同时防止多用户问题, 应该在每次启动程序时清空缓存目录, 平时只写入新的文件

    while True:
        user_prompt = input("请输入:")  # 获取用户输入
        time_get_openai_response(user_prompt)  # 模拟获取ASR响应
        st.session_state[session_keys["static_que"]] = deque()
        Logger.custom(
            st.session_state[session_keys["text_response"]],
            badge=Badge("零壹万物", fore="black", back="cyan"),
        )
        response = time_get_tts_response(st.session_state[session_keys["text_response"]])  # 模拟获取TTS响应
        time_label = get_time_tag_with_millis()
        output_path = cache_dir / f"{time_label}.opus"
        st.session_state[session_keys["static_que"]].append(output_path)
        time_write_tts_response(response, st.session_state[session_keys["static_que"]].popleft())
        time_play_opus_file(output_path)


# 在非异步环境下实际上加上 queue 也没啥用, 但为了保持一致性和相同逻辑, 在这里加上.
