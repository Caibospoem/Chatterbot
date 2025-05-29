##  让树莓派聊天的小尝试 =-=.

因为之前我一直在倒腾 Funasr 和 Bert-VITS2.

于是乎这里就把它搞一个简单的聊天机器人. 同时水一下这学期的课设. 采用 ASR -> NLP -> TTS. 分离式的缺点在于我在调用 api 的时候得调用三次, 这样网络延迟就上来了, 目前测试整个流程一般需要 3s.

## 引用的仓库:

[**Bert-VITS-Inference:** 仅保留推理部分的代码, 仅兼容 2.3 的模型, 用 uv 重构的推理模块, 可用 fastapi 调用, 可用 streamlit WebUI](https://github.com/MrXnneHang/Bert-VITS2.3-Inference)

[**XnneHangLab:** 综合性仓库, 支持从 b 站视频下载 -> 字幕识别和编辑(使用funasr), 使用 streamlit WebUI, 可用 fastapi 调用部分功能, 支持 cli](https://github.com/XnneHangLab/XnneHangLab)
