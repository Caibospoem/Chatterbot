from __future__ import annotations

# 音频参数
RATE = 16000  # 采样率
CHANNELS = 1  # 单声道
SILENCE_THRESHOLD = 600  # 静音检测阈值（毫秒）
MAX_RECORDING_TIME = 30  # 最长录音时间（秒）
SEGMENT_DURATION = 0.8  # 每个VAD检测段的持续时间（秒）
INITIAL_WAIT_TIME = 1.5  # 初始等待时间（秒）
