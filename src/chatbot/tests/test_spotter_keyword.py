from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pexpect


def run_sherpa_keyword_spotter(
    encoder_model: str,
    decoder_model: str,
    joiner_model: str,
    tokens_file: str,
    keywords_file: str,
    audio_files: list[str],
    executable: str = "sherpa-onnx-keyword-spotter",
    timeout: int = 300,
):
    # 运行 sherpa-onnx-keyword-spotter 命令行工具进行关键词检测
    # 过滤掉不必要的Log, 提取关键词检测结果
    """
    使用 pexpect 调用 sherpa-onnx-keyword-spotter 命令行工具进行关键词检测。
    参数:
        encoder_model (str): 编码器模型路径
        decoder_model (str): 解码器模型路径
        joiner_model (str): 连接器模型路径
        tokens_file (str): 词典文件路径
        keywords_file (str): 关键词文件路径
        audio_files (list): 要处理的音频文件路径列表
        executable (str): sherpa-onnx-keyword-spotter 可执行文件的路径或名称
        timeout (int): 命令执行的超时时间（秒）
    返回:
        dict: 包含每个音频文件检测结果的字典
    """
    # 构建命令行参数
    cmd = [
        executable,
        f"--encoder={encoder_model}",
        f"--decoder={decoder_model}",
        f"--joiner={joiner_model}",
        f"--tokens={tokens_file}",
        f"--keywords-file={keywords_file}",
    ]
    cmd.extend(audio_files)
    # 检查所有文件是否存在
    for file_path in [encoder_model, decoder_model, joiner_model, tokens_file, keywords_file] + audio_files:
        if not Path(file_path).exists():
            raise FileNotFoundError(f"文件未找到: {file_path}")
    # 检查可执行文件是否存在
    child = pexpect.spawn(f"{executable} --help", timeout=10)  # type: ignore
    child.expect(pexpect.EOF)
    child.close()
    if child.exitstatus != 0:
        raise RuntimeError(f"无法找到或执行 {executable}，请确保它在系统 PATH 中或提供完整路径")
    print(f"执行命令: {' '.join(cmd)}")
    results: dict[str, list[Any]] = {audio_file: [] for audio_file in audio_files}
    current_audio = None
    # 启动进程
    child = pexpect.spawn(" ".join(cmd), timeout=timeout, encoding="utf-8")  # type: ignore
    # 实时读取输出
    while True:
        if child.eof():  # 检查是否已经到达文件末尾（进程结束）
            break
        line = child.readline().strip()  # type: ignore
        if isinstance(line, str):
            print(line)
        else:
            continue
        # 检查是否是音频文件路径行
        found_audio = False
        for audio_file in audio_files:
            if audio_file in line:
                current_audio = audio_file
                found_audio = True
                break
        # 如果不是音频路径行，且当前有音频文件上下文，尝试解析 JSON
        if not found_audio and current_audio and line.startswith("{"):
            result_data = json.loads(line)
            results[current_audio].append(result_data)
    child.close()  # 确保进程关闭
    return results


def main():
    # 配置模型路径和文件
    base_path = "./models/sherpa-onnx-kws-zipformer-wenetspeech-3.3M-2024-01-01"
    encoder_model = f"{base_path}/encoder-epoch-12-avg-2-chunk-16-left-64.onnx"
    decoder_model = f"{base_path}/decoder-epoch-12-avg-2-chunk-16-left-64.onnx"
    joiner_model = f"{base_path}/joiner-epoch-12-avg-2-chunk-16-left-64.onnx"
    tokens_file = f"{base_path}/tokens.txt"
    keywords_file = f"{base_path}/test_wavs/test_keywords.txt"
    audio_files = [
        f"{base_path}/test_wavs/3.wav",
        f"{base_path}/test_wavs/4.wav",
        f"{base_path}/test_wavs/5.wav",
    ]
    # 运行关键词检测
    results = run_sherpa_keyword_spotter(
        encoder_model=encoder_model,
        decoder_model=decoder_model,
        joiner_model=joiner_model,
        tokens_file=tokens_file,
        keywords_file=keywords_file,
        audio_files=audio_files,
    )
    # 打印结构化结果
    print("\n结构化结果:")
    for audio_file, detections in results.items():
        print(f"\n音频文件: {audio_file}")
        if detections:
            for detection in detections:
                print(f"  关键词: {detection.get('keyword', '未知')}")
                print(f"  开始时间: {detection.get('start_time', 0.0)} 秒")
                print(f"  时间戳: {detection.get('timestamps', [])}")
                print(f"  词素: {detection.get('tokens', [])}")
        else:
            print("  未检测到关键词")


if __name__ == "__main__":
    main()
