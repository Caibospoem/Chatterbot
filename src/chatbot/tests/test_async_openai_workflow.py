from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api.async_api import (
    async_get_tts_response,
    async_play_opus_file,
    async_write_tts_response,
    get_openai_response_stream,
)
from chatbot.console.logger import Badge, Logger, set_logger_debug
from chatbot.tools.config import RunnerSettings, load_settings_file
from chatbot.tools.timed_helper import get_time_tag_with_millis

streamlit_loggers = [
    logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别

set_logger_debug()  # 设置日志记录器为调试模式

if session_keys["sentence_que"] not in st.session_state:
    st.session_state[session_keys["sentence_que"]] = asyncio.Queue()  # 初始化句子队列
if session_keys["tts_que"] not in st.session_state:
    st.session_state[session_keys["tts_que"]] = asyncio.Queue()  # 初始化音频文件队列


async def sentence_producer(prompt: str):
    async for sentence in get_openai_response_stream(prompt):
        await st.session_state[session_keys["sentence_que"]].put(sentence)
        # Logger.custom(sentence, badge=Badge("零壹万物", fore="black", back="cyan"))


async def tts_worker(cache_dir: Path):
    while True:
        sentence: str = await st.session_state[session_keys["sentence_que"]].get()
        audio_bytes = await async_get_tts_response(sentence)
        time_label = get_time_tag_with_millis()
        output_path = cache_dir / f"{time_label}.opus"
        await async_write_tts_response(audio_bytes, output_path)
        await st.session_state[session_keys["tts_que"]].put((sentence, output_path))
        st.session_state[session_keys["sentence_que"]].task_done()  # 标记句子处理完成


async def play_worker():
    while True:
        sentence, audio_path = await st.session_state[session_keys["tts_que"]].get()
        Logger.custom(sentence, badge=Badge("零壹万物", fore="black", back="cyan"))
        await async_play_opus_file(audio_path)
        st.session_state[session_keys["tts_que"]].task_done()


async def main():
    settings = load_settings_file("config.toml", RunnerSettings)
    cache_dir = Path(settings.cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    while True:
        prompt = input("请输入:")
        producer = asyncio.create_task(sentence_producer(prompt))
        tts = asyncio.create_task(tts_worker(cache_dir))
        play = asyncio.create_task(play_worker())

        await producer
        await st.session_state[session_keys["sentence_que"]].join()
        await st.session_state[session_keys["tts_que"]].join()
        tts.cancel()
        play.cancel()


if __name__ == "__main__":
    asyncio.run(main())
