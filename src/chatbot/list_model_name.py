from __future__ import annotations

import requests


def get_openai_models(api_key: str):
    """
    获取 OpenAI 可用的模型列表

    Args:
        api_key (str): OpenAI API 密钥

    Returns:
        dict: 包含模型信息的响应数据
    """
    url = "https://api.lingyiwanwu.com/v1/models"

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
    api_key = "d3f9935e076142b3afcc47a6a0cab84d"
    models_data = get_openai_models(api_key)

    if models_data:
        print("可用模型:")
        for model in models_data["data"]:
            print(f"- {model['id']}")
