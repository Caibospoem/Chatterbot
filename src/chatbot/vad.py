from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from funasr import AutoModel

from chatbot.tools.audio import get_wav_duration
from chatbot.tools.timed_helper import timed_function

if TYPE_CHECKING:
    from chatbot._typing import VadResponse


model = AutoModel(
    model="./models/speech_fsmn_vad_zh-cn-16k-common-pytorch",  # vad 是用于音频分段的
    device="cpu",
    disable_update=True,
)


def main(input_path: Path):
    # TODO 真正调用的时候, 把模型拉到全局初始化
    res = model.generate(input=str(input_path))  # type: ignore
    response: VadResponse = {
        "key": res[0]["key"],
        "time_stamp": res[0]["value"],
        "audio_length": get_wav_duration(input_path),
    }

    return response


timed_main = timed_function(main)

if __name__ == "__main__":
    input_path = Path("./output.wav")
    if not input_path.exists():
        raise FileNotFoundError(f"Input file {input_path} does not exist.")
    resposne = timed_main(input_path=input_path)
    print(resposne)
