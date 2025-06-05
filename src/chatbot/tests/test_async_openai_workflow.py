from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api.async_api import (
    async_file_to_wav,
    async_get_tts_response,
    async_play_opus_file,
    async_write_tts_response,
    get_openai_response_stream,
)
from chatbot.console.logger import Badge, Logger, set_logger_debug
from chatbot.tools.config import RunnerSettings, load_settings_file
from chatbot.tools.live2d_mouth import cal_mouth_y
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


# TODO: 需要检查 tts 的返回是不是 byte , 有时候返回了 json ,说明出错了, 我没想到这个过程竟然一点错误都没有
async def play_worker(cache_dir: Path):
    while True:
        sentence, audio_path = await st.session_state[session_keys["tts_que"]].get()
        Logger.custom(sentence, badge=Badge("零壹万物", fore="black", back="cyan"))
        # 转换音频格式为 WAV 以供 play_live2d 使用
        wav_path = cache_dir / f"{audio_path.stem}.wav"
        await async_file_to_wav(audio_path, wav_path)
        # 同时播放音频和Live2D动画
        audio_task = asyncio.create_task(async_play_opus_file(audio_path))
        live2d_task = asyncio.create_task(cal_mouth_y(wav_path))
        # 等待两个任务都完成
        await asyncio.gather(audio_task, live2d_task)
        st.session_state[session_keys["tts_que"]].task_done()


async def main():
    settings = load_settings_file("config.toml", RunnerSettings)
    cache_dir = Path(settings.cache_dir) / "tts"
    cache_dir.mkdir(parents=True, exist_ok=True)
    while True:
        prompt = input("请输入:")
        producer = asyncio.create_task(sentence_producer(prompt))
        tts = asyncio.create_task(tts_worker(cache_dir))
        play = asyncio.create_task(play_worker(cache_dir=cache_dir))

        await producer
        await st.session_state[session_keys["sentence_que"]].join()
        await st.session_state[session_keys["tts_que"]].join()
        tts.cancel()
        play.cancel()


if __name__ == "__main__":
    asyncio.run(main())
