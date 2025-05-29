from __future__ import annotations

import json
from time import time

import requests
from dotenv import load_dotenv

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


# --- Example Usage ---
def main():
    user_prompt = "请你自我介绍一下"
    start = time()
    response = get_openai_response(user_prompt)
    end = time()
    print(f"Response time: {end - start:.2f} seconds")
    print(response)
