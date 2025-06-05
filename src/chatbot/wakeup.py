from __future__ import annotations

import pvporcupine
from pvrecorder import PvRecorder

from chatbot.tools.config import RunnerSettings, load_settings_file


def main():
    settings = load_settings_file("config.toml", RunnerSettings)
    access_key = settings.access_key
    keywords = ["jarvis"]

    porcupine = pvporcupine.create(access_key=access_key, keywords=keywords)  # type: ignore[call-arg]
    recoder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    try:
        recoder.start()
        while True:
            keyword_index = porcupine.process(recoder.read())
            if keyword_index >= 0:
                print(f"Detected {keywords[keyword_index]}")

    except KeyboardInterrupt:
        recoder.stop()
    finally:
        porcupine.delete()
        recoder.delete()
