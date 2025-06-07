from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING

import requests
import streamlit as st
from dotenv import load_dotenv

from chatbot._dictionary import session_keys
from chatbot.config_manager.config import ServiceSettings, load_settings_file
from chatbot.console.logger import Logger

if TYPE_CHECKING:
    from chatbot._typing import VadResponse

load_dotenv()

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态

# --- Configuration ---
settings = load_settings_file("config.toml", ServiceSettings)
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
    settings: ServiceSettings = load_settings_file("config.toml", ServiceSettings)
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


def get_tts_response(text: str):
    settings = load_settings_file("config.toml", ServiceSettings)
    SPLIT_TTS_URL = settings.vits_split_url  # 对于长句应该使用切分合成, 避免爆显存而使用内存导致计算缓慢
    # 发送文本进行语音合成，保存输出文件
    headers = {"Content-Type": "application/json"}
    json_data = {"text": text}
    response = requests.post(SPLIT_TTS_URL, headers=headers, json=json_data)
    return response


def write_tts_response(response: requests.Response, output_path: Path):
    with output_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    Logger.debug(f"语音已保存到 {output_path}")


def get_asr_response(audio_path: Path):
    settings = load_settings_file("config.toml", ServiceSettings)
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file {audio_path} does not exist.")
    ASR_URL = settings.asr_url
    audio_file = {"file": audio_path.open("rb")}
    response = requests.request("POST", ASR_URL, files=audio_file)
    return response.json().get("text", "").strip()


def get_vad_response(input_path: Path):
    settings = load_settings_file("config.toml", ServiceSettings)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} does not exist.")
    VAD_URL = settings.vad_url
    audio_file = {"file": input_path.open("rb")}
    res = requests.request("POST", VAD_URL, files=audio_file).json()
    if not isinstance(res, dict):
        raise ValueError(f"Invalid VAD response: {res}")
    response: VadResponse = {
        "audio_length": res["audio_length"],
        "timestamp": res["timestamp"],
        "key": res["key"],
    }
    return response
