from __future__ import annotations

from pathlib import Path

import requests

from chatbot._typing import ResponseMethod


def do_request(
    method: str,
    url: str,
    headers: dict = None,
    data=None,
    files=None,
    json_data=None,
    stream: bool = False,
    output_path: str = None,
):
    if json_data is not None:
        response = requests.request(method, url, headers=headers, json=json_data, stream=stream)
    else:
        response = requests.request(method, url, headers=headers, data=data, files=files, stream=stream)

    if output_path and stream:
        with open(output_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return output_path
    else:
        return response.text
