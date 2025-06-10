from __future__ import annotations

import requests

from chatbot.config_manager import ServiceSettings, load_settings_file
from chatbot.console.logger import Badge, Logger


def get_openai_models():
    """
    获取 OpenAI 可用的模型列表

    Args:
        api_key (str): OpenAI API 密钥

    Returns:
        dict: 包含模型信息的响应数据
    """
    settings = load_settings_file("config.toml", ServiceSettings)
    api_key = settings.sdk_key
    url = f"{settings.sdk_base_url}/v1/models"

    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # 检查HTTP错误
        return response.json()

    except requests.exceptions.RequestException as e:
        print(f"请求错误: {e}")
        return None


def main():
    # 使用示例
    models_data = get_openai_models()
    if models_data:
        for model in models_data["data"]:
            Logger.custom(f"{model['id']}", badge=Badge("模型列表", fore="black", back="cyan"))
