from __future__ import annotations

import asyncio
import time
from pathlib import Path

import numpy as np
import soundfile as sf


async def cal_mouth_y(path: Path):
    """
    异步播放Live2D对口型动画，根据音频文件动态调整动画参数。
    """
    # 使用 soundfile 加载音频文件，速度比 librosa 快
    x, sr = sf.read(str(path))  # type: ignore[assignment]
    # 将 x 转换为 numpy 数组，并确保数据类型为 float64 以便处理
    x = np.asarray(x, dtype=np.float64)
    # 如果是立体声（多通道），取第一个通道（单声道）
    if x.ndim > 1:
        x = x[:, 0]

    # 如果采样率不是8000Hz，重采样到8000Hz
    if sr != 8000:
        # 简单的重采样（这里可以优化为更快的重采样算法）
        duration = len(x) / sr
        new_length = int(duration * 8000)
        x = np.interp(np.linspace(0, len(x), new_length), np.arange(len(x)), x)
        sr = 8000

    # 对音频数据进行归一化和对数处理
    x_min = np.min(x)
    x = x - x_min
    x_max = np.max(x)
    if x_max > 0:  # 防止除以0
        x = x / x_max
    x = np.log1p(x)  # 使用 np.log1p 替代 np.log(x) + 1，更安全
    x_max = np.max(x)
    if x_max > 0:
        x = x / x_max * 1.2

    s_time = time.time()
    chunk_size = int(len(x) / 800)
    if chunk_size == 0:
        chunk_size = 1  # 防止循环次数为0

    for _ in range(chunk_size):
        current_time = time.time()
        index = int((current_time - s_time) * sr) + 1
        if index >= len(x):
            it = 0.0
        else:
            it = x[index]
        if it < 0:
            it = 0.0
        # 写入缓存文件
        with Path("./cache/mouth.txt").open("w") as cache_file:
            cache_file.write(str(float(it)))
        # 使用 asyncio.sleep 避免阻塞
        await asyncio.sleep(0.1)

    # 确保最后将值重置为0
    await asyncio.sleep(0.1)
    path.unlink(missing_ok=True)  # 删除音频文件
    with Path("./cache/mouth.txt").open("w") as cache_file:
        cache_file.write("0")
