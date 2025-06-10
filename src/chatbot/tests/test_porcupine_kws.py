from __future__ import annotations

import pvporcupine
from pvrecorder import PvRecorder

from chatbot.chatter.util import handle_porcupine_keyword
from chatbot.config_manager import ServiceSettings, load_settings_file


def main():
    settings = load_settings_file("config.toml", ServiceSettings)
    access_key = settings.access_key
    keyword_config = handle_porcupine_keyword(settings.system_platform)
    keyword_paths = keyword_config["keyword_paths"]
    keywords = keyword_config["keywords"]

    porcupine = pvporcupine.create(  # type: ignore
        access_key=access_key,
        keyword_paths=keyword_paths,
        model_path="./models/keywords_spotting/porcupine_params_zh.pv",
    )
    recoder = PvRecorder(device_index=-1, frame_length=porcupine.frame_length)
    try:
        recoder.start()
        print("Listening for wake word...")
        while True:
            keyword_index = porcupine.process(recoder.read())
            if keyword_index >= 0:
                print(f"Detected {keywords[keyword_index]}")

    except KeyboardInterrupt:
        recoder.stop()
    finally:
        porcupine.delete()
        recoder.delete()
