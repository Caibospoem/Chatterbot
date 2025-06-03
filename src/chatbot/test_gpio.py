from __future__ import annotations

import time

import RPi.GPIO as GPIO


def monitor_callback(channel: int):
    # 读取引脚状态并打印
    print(f"Pin {channel} state: {GPIO.input(channel)}")


def main():
    # 设置GPIO模式
    GPIO.setmode(GPIO.BCM)

    # 选择要监控的引脚
    pin_to_monitor = 18  # 使用BCM编号

    # 设置引脚为输入模式，并启用内部上拉/下拉电阻
    GPIO.setup(pin_to_monitor, GPIO.IN, pull_up_down=GPIO.PUD_UP)

    # 设置边沿检测，监控引脚状态变化
    GPIO.add_event_detect(pin_to_monitor, GPIO.BOTH, callback=monitor_callback, bouncetime=300)

    try:
        print(f"Monitoring pin {pin_to_monitor}... Press Ctrl+C to exit")
        while True:
            time.sleep(1)  # 主循环中可以添加其他任务

    except KeyboardInterrupt:
        print("Monitoring stopped by user")
    finally:
        GPIO.cleanup()  # 清理所有使用过的GPIO
