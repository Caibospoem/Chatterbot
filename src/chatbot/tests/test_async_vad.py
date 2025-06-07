from __future__ import annotations

import asyncio
from pathlib import Path

from chatbot.api.async_api import async_get_vad_response
from chatbot.console.logger import Logger


class VadResponse:
    pass


async def timer_task():
    """
    计时器任务，每秒输出一次计数。
    """
    count = 1
    while True:
        Logger.info(f"Timer: {count}")
        count += 1
        await asyncio.sleep(1)


async def main(input_paths: list[Path]):
    """
    异步主函数，处理音频文件并获取VAD响应。
    同时运行一个计时器任务。
    按顺序处理 input_paths，不使用并发。
    """
    # 创建计时器任务
    timer = asyncio.create_task(timer_task())

    # 按顺序处理每个音频文件
    for input_path in input_paths:
        response = await async_get_vad_response(input_path)
        Logger.info(response)

    # 处理完成后取消计时器任务
    timer.cancel()
    try:
        await timer  # 等待计时器任务结束
    except asyncio.CancelledError:
        Logger.info("Timer stopped.")


if __name__ == "__main__":
    input_paths = ["examples/1.opus", "examples/2.opus", "examples/3.opus", "examples/4.opus"]
    input_paths = [Path(path) for path in input_paths]

    # 运行主函数
    responses = asyncio.run(main(input_paths))
