from __future__ import annotations

import json
import re
import time
from pathlib import Path

import aiohttp
import requests
import streamlit as st
from dotenv import load_dotenv

from chatbot._dictionary import session_keys
from chatbot.console.logger import Logger
from chatbot.tools.config import RunnerSettings, load_settings_file

load_dotenv()

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态

# --- Configuration ---
settings = load_settings_file("config.toml", RunnerSettings)
OPENAI_API_KEY = settings.sdk_key
OPENAI_ENDPOINT = f"{settings.sdk_base_url}/v1/chat/completions"  # Use Chat Completions endpoint
MODEL = "yi-lightning"
SYSTEMPROMOT = Path("./promots/paimeng.txt").read_text(encoding="utf-8").strip()  # 派蒙的promot


def get_openai_response(
    prompt: str,
    model: str = MODEL,
    max_tokens: int = 15000,
    temperature: float = 0.9,
    n: int = 1,
    stop: list[str] | None = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0,
):
    """
    获取OpenAI API的响应（同步，非流式）
    """
    settings: RunnerSettings = load_settings_file("config.toml", RunnerSettings)
    OPENAI_API_KEY: str = settings.sdk_key
    OPENAI_ENDPOINT: str = settings.sdk_base_url + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEMPROMOT},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "n": n,
        "stop": stop,
        "presence_penalty": presence_penalty,
        "frequency_penalty": frequency_penalty,
        "stream": False,
    }
    response = requests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    response_json = response.json()
    st.session_state[session_keys["text_response"]] = response_json["choices"][0]["message"]["content"].strip()
    return response_json["choices"][0]["message"]["content"].strip()


async def get_openai_response_stream(
    prompt: str,
    model: str = MODEL,
    max_tokens: int = 15000,
    temperature: float = 0.9,
    n: int = 1,
    stop: list[str] | None = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0,
):
    """
    获取OpenAI API的响应（流式，异步）
    """
    settings: RunnerSettings = load_settings_file("config.toml", RunnerSettings)
    OPENAI_API_KEY: str = settings.sdk_key
    OPENAI_ENDPOINT: str = settings.sdk_base_url + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEMPROMOT},
            {"role": "user", "content": prompt},
        ],
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
                                sentence = buffer[: m.end()]
                                # 第一次分句，记录耗时
                                if first_sentence_time is None:
                                    first_sentence_time = time.monotonic()
                                    Logger.info(f"首句耗时: {first_sentence_time - t_start:.3f} 秒")
                                yield sentence
                                buffer = buffer[m.end() :]
                            else:
                                break
                except Exception as e:
                    Logger.error(f"{e}")

    # 可选，总耗时打印
    t_end = time.monotonic()
    Logger.info(f"总耗时: {t_end - t_start:.3f} 秒")


def get_tts_response(text: str, output_path: Path):
    settings = load_settings_file("config.toml", RunnerSettings)
    VITS_URL = settings.vits_url
    DIRECT_TTS_URL = f"{VITS_URL}/direct"
    # 发送文本进行语音合成，保存输出文件
    headers = {"Content-Type": "application/json"}
    json_data = {"text": text}
    response = requests.post(DIRECT_TTS_URL, headers=headers, json=json_data)
    return response


def write_tts_response(response: requests.Response, output_path: Path):
    with output_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"语音已保存到 {output_path}")


def get_asr_response(audio_path: Path):
    settings = load_settings_file("config.toml", RunnerSettings)
    ASR_URL = settings.asr_url
    audio_file = {"file": audio_path.open("rb")}
    response = requests.request("POST", ASR_URL, files=audio_file)
    return response.json().get("text", "").strip()
