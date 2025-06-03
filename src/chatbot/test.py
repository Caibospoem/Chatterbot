from __future__ import annotations

import functools
import logging
import time
from collections.abc import Callable
from typing import Any, TypeVar, cast

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.api import (
    get_asr_response,
    get_openai_response,
    get_tts_response,
    write_tts_response,
)
from chatbot.console.logger import Badge, Logger
from chatbot.tools.play_audio import play_opus_file

streamlit_loggers = [
    logging.getLogger(name) for name in logging.root.manager.loggerDict if name.startswith("streamlit")
]
for logger in streamlit_loggers:
    logger.setLevel(logging.ERROR)  # 裸模式(非 streamlit run 交互式)运行会带来很多警告信息，这里将其设置为ERROR级别

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态

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


time_get_asr_response = timed_function(get_asr_response)
time_get_tts_response = timed_function(get_tts_response)
time_write_tts_response = timed_function(write_tts_response)
time_get_openai_response = timed_function(get_openai_response)
time_play_opus_file = timed_function(play_opus_file)


def main():
    while True:
        user_prompt = input("请输入:")  # 获取用户输入
        time_get_openai_response(user_prompt)  # 模拟获取ASR响应
        Logger.custom(
            st.session_state[session_keys["text_response"]],
            badge=Badge("零壹万物", fore="black", back="cyan"),
        )
