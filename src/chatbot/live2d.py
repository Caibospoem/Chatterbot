from __future__ import annotations

import socket
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

live2d_port = 8000  # Live2D服务端口

app = FastAPI()

# 挂载静态文件目录
app.mount("/assets", StaticFiles(directory="./dist/assets"), name="assets")


def get_local_ip():  # 获取本机IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("223.5.5.5", 1))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    return ip


lan_ip = get_local_ip()


@app.get("/")
async def index():  # Live2D页面
    return FileResponse("./dist/live2d_web.html")


@app.get("/api/get_mouth_y")
async def read_txt():  # 读取缓存
    with Path("./cache/mouth.txt").open("r") as f:
        return {"y": f.read()}


def run_live2d():  # 启动Live2D服务
    uvicorn.run(app, host="0.0.0.0", port=live2d_port, log_level="error")


if __name__ == "__main__":
    run_live2d()
