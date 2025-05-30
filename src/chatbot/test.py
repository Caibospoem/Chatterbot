from __future__ import annotations

import functools
import json
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar, cast

import requests
from dotenv import load_dotenv

from chatbot.console.logger import Badge, Logger
from chatbot.tools.config import RunnerSettings, load_settings_file
from chatbot.tools.play_audio import play_opus_file

load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = "d3f9935e076142b3afcc47a6a0cab84d"
OPENAI_ENDPOINT = "https://api.lingyiwanwu.com/v1/chat/completions"  # Use Chat Completions endpoint
MODEL = "yi-lightning"
SYSTEMPROMOT = "你是一个可可爱爱的猫娘, 你有白色的尾巴和黑色的耳朵.你喜欢简短地回答问题,而且总喜欢在句尾加喵~ 你不喜欢讲英文,你只用中文作答."


# 定义 TypeVar 以处理泛型 Callable
T = TypeVar("T", bound=Callable[..., Any])  # 指定 bound 为 Callable，并使用 ... 表示任意参数


def timed_function(func: T) -> T:
    """
    装饰器函数：接受一个函数作为输入，统计并打印该函数的总执行时间。

    参数:
    func (T): 需要计时的函数或可调用对象。

    返回:
    T: 一个包装后的函数，与原始函数具有相同的签名。
    """

    @functools.wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:  # 显式使用 Any 处理参数和返回类型
        start_time: float = time.perf_counter()  # 添加类型注解 float
        result: Any = func(*args, **kwargs)  # 显式类型注解
        end_time: float = time.perf_counter()  # 添加类型注解 float
        total_time: float = end_time - start_time  # 计算总用时
        Logger.info(f"函数 {func.__name__} 总用时: {total_time:.4f} 秒")  # 打印用时
        return result  # 返回结果

    return cast("T", wrapper)  # 使用 cast 确保类型兼容


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
    Gets a response from the OpenAI API using a direct HTTP request.

    Args:
        prompt: The prompt to send to the API.
        model: The OpenAI model to use.
        max_tokens: The maximum number of tokens to generate.
        temperature: Controls randomness.
        n: Number of completions to generate.
        stop: Stop sequences.
        presence_penalty: Presence penalty.
        frequency_penalty: Frequency penalty.

    Returns:
        The generated text (string), or None if an error occurred.
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
    }

    response = requests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data))
    response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
    response_json = response.json()
    return response_json["choices"][0]["message"]["content"].strip()


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


time_get_asr_response = timed_function(get_asr_response)
time_get_tts_response = timed_function(get_tts_response)
time_write_tts_response = timed_function(write_tts_response)
time_get_openai_response = timed_function(get_openai_response)
time_play_opus_file = timed_function(play_opus_file)


# --- Example Usage ---
def main():
    while True:
        user_prompt = input("请输入:")
        response = time_get_openai_response(user_prompt)
        Logger.custom(response, badge=Badge("零壹万物", fore="black", back="cyan"))
        output_path = Path("output.opus")
        time_get_tts_response(response, output_path)
        tts_response = time_get_asr_response(output_path)
        Logger.custom(tts_response, badge=Badge("tts", fore="black", back="cyan"))
        time_play_opus_file(output_path)
