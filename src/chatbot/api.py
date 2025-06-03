from __future__ import annotations

import json
from pathlib import Path

import requests
from dotenv import load_dotenv

from chatbot.tools.config import RunnerSettings, load_settings_file

load_dotenv()

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
    stream: bool = False,  # 新增参数
):
    """
    获取OpenAI API的响应，可选择流式返回。
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
        "stream": stream,  # 加入stream参数
    }
    response = requests.post(OPENAI_ENDPOINT, headers=headers, data=json.dumps(data), stream=stream)
    response.raise_for_status()
    if not stream:
        response_json = response.json()
        return response_json["choices"][0]["message"]["content"].strip()
    else:
        result = ""
        for line in response.iter_lines():
            if line:
                decoded = line.decode("utf-8")
                print(decoded)
                if decoded.startswith("data: "):
                    data_str = decoded[6:]
                    if data_str.strip() == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        if "choices" in chunk and chunk["choices"]:
                            delta = chunk["choices"][0]["delta"].get("content", "")
                            result += delta
                    except json.JSONDecodeError:
                        continue  # 非法json直接跳过
        return result


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
