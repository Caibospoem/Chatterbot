from __future__ import annotations

import json
from pathlib import Path
from time import time

import requests
from dotenv import load_dotenv

from chatbot.tools.config import RunnerSettings, load_settings_file

load_dotenv()

# --- Configuration ---
OPENAI_API_KEY = "d3f9935e076142b3afcc47a6a0cab84d"
OPENAI_ENDPOINT = "https://api.lingyiwanwu.com/v1/chat/completions"  # Use Chat Completions endpoint
MODEL = "yi-lightning"
SYSTEMPROMOT = "你是一个可可爱爱的猫娘, 你有白色的尾巴和黑色的耳朵.你喜欢简短地回答问题,而且总喜欢在句尾加喵~"


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
    from time import time
    settings = load_settings_file("config.toml", RunnerSettings)
    VITS_URL = settings.vits_url
    DIRECT_TTS_URL = f"{VITS_URL}/direct"
    # 发送文本进行语音合成，保存输出文件
    headers = {"Content-Type": "application/json"}
    json_data = {"text": text}
    response = requests.post(DIRECT_TTS_URL, headers=headers, json=json_data)
    start = time()
    with output_path.open("wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
    print(f"语音已保存到 {output_path}")
    end = time()
    print(f"写入耗时 {end - start:.2f}秒")


def get_asr_response(audio_path: Path):
    settings = load_settings_file("config.toml", RunnerSettings)
    ASR_URL = settings.asr_url
    audio_file = {"file": audio_path.open("rb")}
    response = requests.request("POST", ASR_URL, files=audio_file)
    return response.json().get("text", "").strip()


# --- Example Usage ---
def main():
    while True:
        user_prompt = input("请输入:")
        start = time()
        response = get_openai_response(user_prompt)
        end = time()
        print(f"响应时间: {end - start:.2f}秒")
        print(response)
        output_path = Path("output.opus")
        get_tts_response(response, output_path)
        get_asr_response(output_path)
        end = time()
        print(f"响应时间: {end - start:.2f}秒")
