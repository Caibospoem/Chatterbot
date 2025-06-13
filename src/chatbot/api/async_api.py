# type: ignore

from __future__ import annotations

import asyncio
import json
import re
import time
from pathlib import Path
from typing import TYPE_CHECKING

import aiofiles
import aiohttp
import streamlit as st
from dotenv import load_dotenv

from chatbot._dictionary import session_keys
from chatbot.config_manager import ServiceSettings, load_settings_file
from chatbot.console.logger import Badge, Logger
from chatbot.tools.audio import file_to_opus, file_to_wav, play_opus_file

if TYPE_CHECKING:
    from chatbot._typing import VadResponse


load_dotenv()

if session_keys["text_response"] not in st.session_state:
    st.session_state[session_keys["text_response"]] = ""  # 初始化会话状态

if session_keys["short_term_memory"] not in st.session_state:
    st.session_state[session_keys["short_term_memory"]] = []  # 初始化短期记忆


# --- Configuration ---
settings = load_settings_file("config.toml", ServiceSettings)
OPENAI_API_KEY = settings.sdk_key
OPENAI_ENDPOINT = f"{settings.sdk_base_url}/v1/chat/completions"  # Use Chat Completions endpoint
MODEL = "yi-lightning"
SYSTEMPROMOT = Path("./prompts/paimeng.txt").read_text(encoding="utf-8").strip()  # 派蒙的promot


async def get_openai_response_stream(
    prompt: str,
    model: str = MODEL,
    max_tokens: int = 15000,
    temperature: float = 0.4,
    n: int = 1,
    stop: list[str] | None = None,
    presence_penalty: float = 0,
    frequency_penalty: float = 0,
    max_retries: int = 3,
    first_sentence_timeout: float = 3.5,
    request_timeout: float = 30.0,
):
    """
    获取OpenAI API的响应（流式，异步）
    修复重试时用户消息丢失的问题
    """
    settings: ServiceSettings = load_settings_file("config.toml", ServiceSettings)
    OPENAI_API_KEY: str = settings.sdk_key
    OPENAI_ENDPOINT: str = settings.sdk_base_url + "/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    if len(st.session_state[session_keys["short_term_memory"]]) == 0:
        st.session_state[session_keys["short_term_memory"]].append({"role": "system", "content": SYSTEMPROMOT})

    # 保存原始的用户消息，用于重试
    user_message = {"role": "user", "content": prompt}

    # 重试循环
    for attempt in range(max_retries):
        Logger.custom(
            f"发送OpenAI请求 (第 {attempt + 1}/{max_retries} 次)", badge=Badge("连接", fore="black", back="cyan")
        )
        try:
            # 重置响应文本
            st.session_state[session_keys["text_response"]] = ""
            first_sentence_received = False
            request_completed = False

            # 确保用户消息在短期记忆中（每次重试都重新添加）
            if (
                not st.session_state[session_keys["short_term_memory"]]
                or st.session_state[session_keys["short_term_memory"]][-1] != user_message
            ):
                st.session_state[session_keys["short_term_memory"]].append(user_message)

            # 准备请求数据
            data = {
                "model": model,
                "messages": st.session_state[session_keys["short_term_memory"]],
                "max_tokens": max_tokens,
                "temperature": temperature,
                "n": n,
                "stop": stop,
                "presence_penalty": presence_penalty,
                "frequency_penalty": frequency_penalty,
                "stream": True,
            }

            Logger.info(f"发送的消息: {data['messages']}")

            # 完整的流处理函数
            async def process_complete_stream(data):
                nonlocal first_sentence_received, request_completed
                buffer = ""
                t_start = time.monotonic()
                first_sentence_time = None

                # 设置超时
                timeout = aiohttp.ClientTimeout(
                    total=request_timeout,
                    connect=10.0,  # 连接超时
                    sock_read=request_timeout,  # 读取超时
                )

                try:
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        Logger.debug("正在建立连接...")
                        async with session.post(OPENAI_ENDPOINT, headers=headers, json=data) as resp:
                            Logger.debug(f"连接已建立，状态码: {resp.status}")
                            if resp.status != 200:
                                error_text = await resp.text()
                                raise Exception(f"HTTP {resp.status}: {error_text}")

                            Logger.debug("开始接收响应流...")

                            # 首句超时检查
                            first_sentence_start_time = time.monotonic()

                            async for line in resp.content:
                                decoded = line.decode("utf-8").strip()
                                if not decoded or not decoded.startswith("data: "):
                                    continue

                                data_str = decoded[6:]
                                if data_str.strip() == "[DONE]":
                                    Logger.debug("收到 [DONE] 标记，流结束")
                                    # 处理剩余内容
                                    if buffer.strip():
                                        Logger.debug(f"处理剩余内容: {repr(buffer)}")
                                        st.session_state[session_keys["text_response"]] += buffer.strip()
                                        yield buffer.strip()
                                    request_completed = True
                                    break

                                try:
                                    chunk = json.loads(data_str)
                                    if "choices" in chunk and chunk["choices"]:
                                        content = chunk["choices"][0]["delta"].get("content", "")
                                        if content:
                                            Logger.debug(f"收到内容块: {repr(content)}")
                                            buffer += content

                                            # 检查首句超时
                                            if not first_sentence_received:
                                                current_time = time.monotonic()
                                                if current_time - first_sentence_start_time > first_sentence_timeout:
                                                    Logger.warning(f"首句超时（{first_sentence_timeout}秒）")
                                                    raise TimeoutError("首句获取超时")

                                            # 检查是否形成完整句子
                                            while True:
                                                m = re.search(r"[。！？!?\.]", buffer)
                                                if m:
                                                    sentence = buffer[: m.end()].strip().replace("\n", "")
                                                    if sentence:
                                                        if not first_sentence_received:
                                                            first_sentence_time = time.monotonic()
                                                            first_sentence_received = True
                                                            Logger.debug(
                                                                f"首句耗时: {first_sentence_time - t_start:.3f} 秒"
                                                            )
                                                            Logger.info(f"首句接收成功: {repr(sentence)}")
                                                        else:
                                                            Logger.debug(f"后续句子: {repr(sentence)}")

                                                        st.session_state[session_keys["text_response"]] += sentence
                                                        yield sentence
                                                        buffer = buffer[m.end() :]
                                                else:
                                                    break

                                except json.JSONDecodeError as e:
                                    Logger.warning(f"JSON解析错误: {e}")
                                    continue
                                except Exception as e:
                                    Logger.error(f"解析响应块时出错: {e}")
                                    continue

                            # 如果循环正常结束但没有收到 [DONE]
                            if not request_completed and buffer.strip():
                                Logger.debug(f"流异常结束，处理剩余内容: {repr(buffer)}")
                                st.session_state[session_keys["text_response"]] += buffer.strip()
                                yield buffer.strip()
                                request_completed = True

                except Exception as e:
                    Logger.error(f"流处理过程中出错: {e}")
                    raise

            # 执行流处理
            Logger.debug(f"开始处理完整流（首句超时: {first_sentence_timeout}秒）...")
            t_start = time.monotonic()

            try:
                async for sentence in process_complete_stream(data):
                    yield sentence

                # 检查是否成功完成
                if request_completed and first_sentence_received:
                    t_end = time.monotonic()
                    Logger.debug(f"OpenAI 总耗时: {t_end - t_start:.3f} 秒")
                    st.session_state[session_keys["short_term_memory"]].append(
                        {"role": "assistant", "content": st.session_state[session_keys["text_response"]]}
                    )
                    Logger.debug(f"短期记忆: {st.session_state[session_keys['short_term_memory']]}")
                    Logger.info("OpenAI请求成功完成")
                    return
                elif not first_sentence_received:
                    Logger.warning("未收到首句，需要重试")
                    raise Exception("未收到首句")
                else:
                    Logger.warning("请求未完整完成，需要重试")
                    raise Exception("请求未完整完成")

            except TimeoutError as e:
                Logger.warning(f"请求超时: {e}")
                raise
            except Exception as e:
                Logger.error(f"流处理失败: {e}")
                raise

        except Exception as e:
            Logger.error(f"第 {attempt + 1} 次请求出现异常: {e}")
            import traceback

            Logger.debug(f"异常详情: {traceback.format_exc()}")

        # 重试逻辑
        if attempt < max_retries - 1:
            # 从短期记忆中移除当前的用户消息，下次循环会重新添加
            if (
                st.session_state[session_keys["short_term_memory"]]
                and st.session_state[session_keys["short_term_memory"]][-1]["role"] == "user"
            ):
                st.session_state[session_keys["short_term_memory"]].pop()

            wait_time = 0.5 + attempt * 0.5
            Logger.info(f"等待 {wait_time} 秒后重试...")
            await asyncio.sleep(wait_time)
            continue
        else:
            break

    # 所有重试失败
    Logger.error("所有重试都失败了，返回默认响应")
    st.session_state[session_keys["text_response"]] = "抱歉，我现在无法正常回应，请稍后再试。"
    st.session_state[session_keys["short_term_memory"]].append(
        {"role": "assistant", "content": st.session_state[session_keys["text_response"]]}
    )
    yield "抱歉，我现在无法正常回应，请稍后再试。"


async def async_get_tts_response(text: str):
    settings = load_settings_file("config.toml", ServiceSettings)
    DIRECT_TTS_URL = settings.vits_direct_url
    headers = {"Content-Type": "application/json"}
    json_data = {"text": text}
    async with aiohttp.ClientSession() as session:
        async with session.post(DIRECT_TTS_URL, headers=headers, json=json_data) as resp:
            # 假设接口返回音频二进制流
            content = await resp.read()
            return content


async def async_write_tts_response(content: bytes, output_path: Path):
    async with aiofiles.open(output_path, "wb") as f:  # type: ignore
        await f.write(content)
    Logger.debug(f"语音已保存到 {output_path}")


async def async_play_opus_file(path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, play_opus_file, path)
    await asyncio.sleep(0.3)  # 每个音频播放可以有点间隔
    path.unlink(missing_ok=True)  # 删除文件，避免缓存过多


async def async_get_asr_response(audio_path: Path) -> str:
    """
    异步发送音频文件到ASR服务并获取识别结果。

    参数:
        audio_path (Path): 音频文件路径

    返回:
        str: ASR识别的文本结果，如果出错或无结果则返回空字符串
    """
    settings = load_settings_file("config.toml", ServiceSettings)  # 假设此函数是同步的
    ASR_URL = settings.asr_url
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file {audio_path} does not exist.")

    # 创建异步HTTP会话
    async with aiohttp.ClientSession() as session:
        # 准备文件数据
        with audio_path.open("rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field("file", audio_file, filename=audio_path.name)

            # 发送异步POST请求
            async with session.post(ASR_URL, data=form_data) as response:
                response.raise_for_status()  # 检查HTTP状态码
                result = await response.json()  # 异步读取JSON响应
                await asyncio.sleep(0.1)  # 加点停顿
                return result.get("text", "").strip()


async def async_get_vad_response(audio_path: Path) -> VadResponse:
    """
    异步发送音频文件到VAD服务并获取识别结果。

    参数:
        audio_path (Path): 音频文件路径

    返回:
        VadResponse
    """
    settings = load_settings_file("config.toml", ServiceSettings)  # 假设此函数是同步的
    VAD_URL = settings.vad_url
    if not audio_path.exists():
        raise FileNotFoundError(f"Audio file {audio_path} does not exist.")
    # 创建异步HTTP会话
    async with aiohttp.ClientSession() as session:
        # 准备文件数据
        with audio_path.open("rb") as audio_file:
            form_data = aiohttp.FormData()
            form_data.add_field("file", audio_file, filename=audio_path.name)

            async with session.post(VAD_URL, data=form_data) as response:
                response.raise_for_status()  # 检查HTTP状态码
                result: VadResponse = await response.json()  # 异步读取JSON响应
                await asyncio.sleep(0.1)  # 加点停顿, 不加似乎会卡 vad. 像是文件损坏了
                return result


async def async_file_to_wav(input_path: Path, output_path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, file_to_wav, input_path, output_path)


async def async_file_to_opus(input_path: Path, output_path: Path):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, file_to_opus, input_path, output_path)
