import asyncio
import time
import RPi.GPIO as GPIO
import logging
from rpi_ws281x import PixelStrip, Color

# Reduce logging
logging.basicConfig(level=logging.ERROR)

# LED灯带参数
LED_COUNT = 255       # LED灯带上的LED数量
LED_PIN = 18          # GPIO引脚
pin_to_monitor = 23   # 监控的引脚
LED_FREQ_HZ = 800000  # LED信号频率
LED_DMA = 10          # DMA通道
LED_BRIGHTNESS = 10   # LED亮度（0-255）
LED_INVERT = False    # 是否反转信号
LED_CHANNEL = 0       # 通道

# 设置 GPIO 引脚
GPIO.setmode(GPIO.BCM)
GPIO.setup(pin_to_monitor, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# 初始化LED灯带
strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()
current_brightness = 10

# 全局状态变量（替代 streamlit session_state）
app_state = {
    "starttime": None,
    "PIN": False,
    "light_state": False,  # False表示降低亮度，True表示提高亮度
    "led_on": False
}

async def set_all_pixels(color):
    """设置所有LED为指定颜色"""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
    strip.show()
    await asyncio.sleep(0.1)
    
async def set_brightness(value):
    """设置灯带亮度并应用"""
    global current_brightness
    current_brightness = max(10, min(255, value))  # 确保亮度在10-255之间
    strip.setBrightness(current_brightness)
    strip.show()
    print(f"Brightness set to: {current_brightness}/255")
    await asyncio.sleep(0.1)

async def monitor_io():
    while True:
        try:
            # 当引脚为高电平时时间计数器触发
            if GPIO.input(pin_to_monitor) == GPIO.HIGH:
                if not app_state["PIN"]:
                    app_state["PIN"] = True
                    app_state["starttime"] = time.time()  # 计时器开始计时
                    app_state["light_state"] = not app_state["light_state"]  # 转换长按模式
                    print(f"Button pressed, light_state: {app_state['light_state']}")
            else:
                if app_state["PIN"]:
                    app_state["PIN"] = False
                    print("Button released")
            
            # Add a small sleep to prevent CPU hogging
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in monitor_io: {e}")
            await asyncio.sleep(0.1)

async def light_set():
    while True:
        try:
            # 当检测到持续的高电平时
            if app_state["PIN"] and app_state["starttime"] is not None:
                elapsed_time = time.time() - app_state["starttime"]
                if elapsed_time > 1:
                    if app_state["light_state"]:
                        print("light up")
                        await set_brightness(current_brightness + 10)
                    else:
                        print("light down")
                        await set_brightness(current_brightness - 10)
                    
            else:
                if app_state["starttime"] is not None:
                    elapsed_time = time.time() - app_state["starttime"]
                    if elapsed_time < 1:
                        print("Trigger - Short press detected")
                        app_state["led_on"] = not app_state["led_on"]
                        if app_state["led_on"]:
                            print("light on")
                            await set_all_pixels(Color(255, 255, 255))
                        else:
                            print("light off")
                            await set_all_pixels(Color(0, 0, 0))
                    app_state["starttime"] = None
            
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Error in light_set: {e}")
            await asyncio.sleep(0.1)

async def main():
    print("Starting GPIO monitoring...")
    print(f"Monitoring pin {pin_to_monitor}")
    print("Press Ctrl+C to stop")
    
    try:
        # 创建任务
        task1 = asyncio.create_task(monitor_io())
        task2 = asyncio.create_task(light_set())
        
        # 等待任务完成
        await asyncio.gather(task1, task2)
    except asyncio.CancelledError:
        print("Tasks cancelled")
    except Exception as e:
        print(f"Error in main: {e}")

try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("\nMonitoring stopped by user")
except Exception as e:
    print(f"Unexpected error: {e}")
finally:
    print("Cleaning up GPIO...")
    GPIO.cleanup()  # 清理所有使用过的 GPIO
    print("GPIO cleanup completed")