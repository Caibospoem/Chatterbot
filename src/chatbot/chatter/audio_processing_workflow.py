from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api.async_api import (
    async_file_to_wav,
    async_get_tts_response,
    async_play_opus_file,
    async_write_tts_response,
    get_openai_response_stream,
)
from chatbot.console.logger import Badge, Logger
from chatbot.tools.live2d_mouth import cal_mouth_y
from chatbot.tools.timed_helper import get_time_tag_with_millis

if TYPE_CHECKING:
    from pathlib import Path


# 初始化Streamlit会话状态
def initialize_session_state() -> None:
    if session_keys["sentence_que"] not in st.session_state:
        st.session_state[session_keys["sentence_que"]] = asyncio.Queue()  # 初始化句子队列
    if session_keys["tts_que"] not in st.session_state:
        st.session_state[session_keys["tts_que"]] = asyncio.Queue()  # 初始化音频文件队列


async def sentence_producer(prompt: str) -> None:
    """从OpenAI获取响应并放入句子队列"""
    async for sentence in get_openai_response_stream(prompt):
        await st.session_state[session_keys["sentence_que"]].put(sentence)
        # Logger.custom(sentence, badge=Badge("零壹万物", fore="black", back="cyan"))


async def tts_worker(cache_dir: Path) -> None:
    """从句子队列获取文本并生成TTS音频"""
    while True:
        sentence: str = await st.session_state[session_keys["sentence_que"]].get()
        audio_bytes = await async_get_tts_response(sentence)
        time_label = get_time_tag_with_millis()
        output_path = cache_dir / f"{time_label}.opus"
        await async_write_tts_response(audio_bytes, output_path)
        await st.session_state[session_keys["tts_que"]].put((sentence, output_path))
        st.session_state[session_keys["sentence_que"]].task_done()  # 标记句子处理完成


async def play_worker(cache_dir: Path) -> None:
    """从音频队列获取文件并播放"""
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


async def process_voice_command(prompt: str, cache_dir: Path) -> None:
    """处理语音命令的完整流程"""
    # 确保缓存目录存在
    (cache_dir / "tts").mkdir(parents=True, exist_ok=True)

    # 创建任务
    producer = asyncio.create_task(sentence_producer(prompt))
    tts = asyncio.create_task(tts_worker(cache_dir / "tts"))
    play = asyncio.create_task(play_worker(cache_dir=cache_dir / "tts"))

    # 等待生产者完成
    await producer

    # 等待所有队列处理完毕
    await st.session_state[session_keys["sentence_que"]].join()
    await st.session_state[session_keys["tts_que"]].join()

    # 取消剩余任务
    tts.cancel()
    play.cancel()
