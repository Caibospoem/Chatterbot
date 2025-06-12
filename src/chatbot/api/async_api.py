from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
import streamlit as st
from dotenv import load_dotenv

from chatbot._dictionary import session_keys
from chatbot.config_manager import ServiceSettings, load_settings_file
from chatbot.console.logger import Logger
from chatbot.tools.audio import file_to_opus, file_to_wav, play_opus_file

if TYPE_CHECKING:
    from chatbot._typing import VadResponse


load_dotenv()

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态

if session_keys["short_term_memory"] not in st.session_state:
    st.session_state[session_keys["short_term_memory"]] = []  # 初始化短期记忆


# --- Configuration ---
settings = load_settings_file("config.toml", ServiceSettings)
OPENAI_API_KEY = settings.sdk_key
OPENAI_ENDPOINT = f"{settings.sdk_base_url}/v1/chat/completions"  # Use Chat Completions endpoint
MODEL = "yi-lightning"
SYSTEMPROMOT = Path("./prompts/paimeng.txt").read_text(encoding="utf-8").strip()  # 派蒙的promot


async def get_openai_response_stream(
    prompt: str,
    model: str = MODEL,
    max_tokens: int = 15000,
    temperature: float = 0.4,
    n: int = 1,
    stop: list[str] | None = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0,
):
    """
    获取OpenAI API的响应（流式，异步）
    """
    settings: ServiceSettings = load_settings_file("config.toml", ServiceSettings)
    OPENAI_API_KEY: str = settings.sdk_key
    OPENAI_ENDPOINT: str = settings.sdk_base_url + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if len(st.session_state[session_keys["short_term_memory"]]) == 0:
        # 如果短期记忆为空，添加系统提示
        st.session_state[session_keys["short_term_memory"]].append({"role": "system", "content": SYSTEMPROMOT})
    st.session_state[session_keys["short_term_memory"]].append({"role": "user", "content": prompt})
    data = {
        "model": model,
        "messages": st.session_state[session_keys["short_term_memory"]],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "n": n,
        "stop": stop,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "stream": True,
    }
    buffer = ""
    t_start = time.monotonic()  # 发起请求前的时间
    first_sentence_time = None

    async with aiohttp.ClientSession() as session:
        async with session.post(OPENAI_ENDPOINT, headers=headers, json=data) as resp:
            async for line in resp.content:
                decoded = line.decode("utf-8").strip()
                if not decoded or not decoded.startswith("data: "):
                    continue
                data_str = decoded[6:]
                if data_str.strip() == "[DONE]":
                    if buffer:
                        yield buffer
                    break
                try:
                    chunk = json.loads(data_str)
                    if "choices" in chunk and chunk["choices"]:
                        content = chunk["choices"][0]["delta"].get("content", "")
                        buffer += content
                        while True:
                            m = re.search(r"[。！？!?\.]", buffer)
                            if m:
                                sentence = buffer[: m.end()].strip().replace("\n", "")
                                # 第一次分句，记录耗时
                                if first_sentence_time is None:
                                    first_sentence_time = time.monotonic()
                                    Logger.debug(f"首句耗时: {first_sentence_time - t_start:.3f} 秒")
                                st.session_state[session_keys["text_response"]] += sentence
                                yield sentence
                                buffer = buffer[m.end() :]
                            else:
                                break
                except Exception as e:
                    Logger.error(f"{e}")

    # 可选，总耗时打印
    t_end = time.monotonic()
    Logger.debug(f"openai 总耗时: {t_end - t_start:.3f} 秒")
    st.session_state[session_keys["short_term_memory"]].append(
        {"role": "assistant", "content": st.session_state[session_keys["text_response"]]}
    )
    Logger.debug(f"短期记忆:{st.session_state[session_keys['short_term_memory']]}")


async def async_get_tts_response(text: str):
    settings = load_settings_file("config.toml", ServiceSettings)
    DIRECT_TTS_URL = settings.vits_direct_url
    headers = {"Content-Type": "application/json"}
    json_data = {"text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(DIRECT_TTS_URL, headers=headers, json=json_data) as resp:
            # 假设接口返回音频二进制流
            content = await resp.read()
            return content


async def async_write_tts_response(content: bytes, output_path: Path):
    async with aiofiles.open(output_path, "wb") as f:  # type: ignore
        await f.write(content)
    Logger.debug(f"语音已保存到 {output_path}")


async def async_play_opus_file(path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, play_opus_file, path)
    await asyncio.sleep(0.3)  # 每个音频播放可以有点间隔
    path.unlink(missing_ok=True)  # 删除文件，避免缓存过多


async def async_get_asr_response(audio_path: Path) -> str:
    """
    异步发送音频文件到ASR服务并获取识别结果。

    参数:
        audio_path (Path): 音频文件路径

    返回:
        str: ASR识别的文本结果，如果出错或无结果则返回空字符串
    """
    settings = load_settings_file("config.toml", ServiceSettings)  # 假设此函数是同步的
    ASR_URL = settings.asr_url
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file {audio_path} does not exist.")

    # 创建异步HTTP会话
    async with aiohttp.ClientSession() as session:
        # 准备文件数据
        with audio_path.open("rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field("file", audio_file, filename=audio_path.name)

            # 发送异步POST请求
            async with session.post(ASR_URL, data=form_data) as response:
                response.raise_for_status()  # 检查HTTP状态码
                result = await response.json()  # 异步读取JSON响应
                await asyncio.sleep(0.1)  # 加点停顿
                return result.get("text", "").strip()


async def async_get_vad_response(audio_path: Path) -> VadResponse:
    """
    异步发送音频文件到VAD服务并获取识别结果。

    参数:
        audio_path (Path): 音频文件路径

    返回:
        VadResponse
    """
    settings = load_settings_file("config.toml", ServiceSettings)  # 假设此函数是同步的
    VAD_URL = settings.vad_url
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file {audio_path} does not exist.")
    # 创建异步HTTP会话
    async with aiohttp.ClientSession() as session:
        # 准备文件数据
        with audio_path.open("rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field("file", audio_file, filename=audio_path.name)

            async with session.post(VAD_URL, data=form_data) as response:
                response.raise_for_status()  # 检查HTTP状态码
                result: VadResponse = await response.json()  # 异步读取JSON响应
                await asyncio.sleep(0.1)  # 加点停顿, 不加似乎会卡 vad. 像是文件损坏了
                return result


async def async_file_to_wav(input_path: Path, output_path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, file_to_wav, input_path, output_path)


async def async_file_to_opus(input_path: Path, output_path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, file_to_opus, input_path, output_path)
