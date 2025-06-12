<a href="https://xnnehang.top/">

<div align="center">
    <img src="https://fastly.jsdelivr.net/gh/MrXnneHang/blog_img/BlogHosting/img/25/02/202505300942432.jpg" alt="ChatterBot" width="360" height="300">
</div>
<h1 align="center">ChatterBot</h1>
</a>
<br/>
<div align="center">
<a href="https://github.com/astral-sh/uv"><img alt="uv" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json&style=flat-square"></a>
<a href="https://github.com/astral-sh/ruff"><img alt="ruff" src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json&style=flat-square"></a>
<a href="https://gitmoji.dev"><img alt="Gitmoji" src="https://img.shields.io/badge/gitmoji-%20😜%20😍-FFDD67?style=flat-square"></a>
<img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-%23FF4B4B.svg?style=flat-square&logo=streamlit&logoColor=white"></a>
<br/>
</div>

<p align="center">
<a href='https://xnnehang.top/' style='font-size: 20px;'><strong>文档网站(等等噢)</strong></a> ·
<a href='https://space.bilibili.com/556737824'><strong>bilibili视频教程(再等等噢)</strong></a>
</p>
<p align="center">
  <a href="#介绍"><strong>介绍</strong></a> ·
  <a href="#本地部署"><strong>本地部署</strong></a> ·
  <a href="#用法"><strong>用法</strong></a>
</p>

<br/>

## 介绍

因为之前我一直在倒腾 Funasr 和 Bert-VITS2.

于是乎这里就把它搞一个简单的聊天机器人. 同时水一下这学期的课设. 采用 ASR -> NLP -> TTS. 分离式的缺点在于我在调用 api 的时候得调用三次, 这样网络延迟就上来了, 目前测试整个流程一般需要 3s, 和网速强相关. 但优点也很明显, 我可以自由组合模型, 来接近各个方面的理想最优,

**本项目所有代码均开源，不过有的在不同仓库。**

## 本地部署

你需要安装 uv .

```shell
scoop install uv # windows 参考 scoop.sh 安装 scoop
curl -LsSf https://astral.sh/uv/install.sh | sh # linux/mac
```

克隆仓库：

```shell
https://github.com/MrXnneHang/Chatterbot.git
cd Chatterbot
```

配置文件 `config.toml`:

```shell
sdk_base_url = "sdk_base_url"
sdk_key = "sdk_key"
vits_split_url = "http://localhost:7900/tts/split"
vits_direct_url = "http://localhost:7900/tts/direct"
asr_url = "http://localhost:8000/rec-audio"
vad_url = "http://localhost:8000/vad-audio"
cache_dir = "cache"
access_key = "access_key"
system_platform = "raspberry-pi"
promopt = "./prompts/paimeng.txt"
```

`vits_url` 可以部署 [Bert-VITS2.3-Inference](https://github.com/MrXnneHang/Bert-VITS2.3-Inference) , 然后运行 `just server`.

`asr_url` 和 `vad_url` 可以部署 [XnneHangLab](https://github.com/XnneHangLab/XnneHangLab) , 然后运行 `just server`,

有问题可以提 issue.

> [!note]
> 你可以利用 frp 和一个远程服务器来实现远程访问, 然后在树莓派部署该服务.(因为虽然树莓派也可以直接运行 FunASR 和 Bert-VITS2 但速度跟乌龟爬一样.)
> 这样可以直接用 url 调用， 如果国内服务器甚至可以做到 0.1s 以内的延迟。

`base_url` 和 `sdk-key` 请选择支持 OpenAI 协议的服务商, 我用的是零一万物，尽量选择国内的服务商或者代理中转， 因为即使开了代理， 延迟也会远高于国内的服务商， 同事开了代理还会导致你自己搭建的 frp 服务器访问延迟更高。

## 用法

正在开发中， 参考[用法文档](./usage.md)。

## RoadMap

- [x] 支持对话的上下文
- [x] 支持自动识别录音开始和结束.(参考 Digtal_Life_Server)
- [x] 支持流式切分长段落并且为句子.
- [ ] 回答完成后可以保持激活一段时间
- [ ] 把 vad 片段拉长到 3s，避免空 vad
- [x] 双重唤醒词(support raspberry-pi ` 你好``派蒙 `. 其余都是 `你好`)
- [ ] 可以用唤醒词中断对话但是对话连续且存在记忆。
- [ ] 以段落为单位进行 mcp 情绪识别, 并且播放对应的 live2d 动画.
- [ ] 发送 tts 前检查过短句子, 检查特殊符号 `العبارة`
- [x] 以句子为单位发送 tts 请求, 并且依次播放音频.
- [x] 接入 live2d 模型动画播放
- [ ] 接入 mcp 情绪识别或者 BERT 情绪识别以及情绪动画播放
- [ ] 接入网页端的对话框显示和支持
- [x] 优化 api-key 的调用, 用 streamlit 写一个配置文件的界面.

## 原则

> [!note]
> 尽量选择全平台通用的开发方式.<br>
> coding is for waifus!<br>
> 可爱是第一驱动力!<br>

## 引用和借鉴的仓库

[**Bert-VITS-Inference:** 仅保留推理部分的代码, 仅兼容 2.3 的模型, 用 uv 重构的推理模块, 可用 fastapi 调用, 可用 streamlit WebUI](https://github.com/MrXnneHang/Bert-VITS2.3-Inference)

[**XnneHangLab:** 综合性仓库, 支持从 b 站视频下载 -> 字幕识别和编辑(使用 funasr), 使用 streamlit WebUI, 可用 fastapi 调用部分功能, 支持 cli](https://github.com/XnneHangLab/XnneHangLab)

[**zixiiu/Digital_Life_Server**:Yet another voice assistant, but alive. 打算借鉴如何决定开始录音和结束录音.](https://github.com/zixiiu/Digital_Life_Server)

[**swordswind/ai_virtual_mate_linux** 使用 flask 在网页端显示动态 Live2D 解决显示问题 special-for-linux](https://github.com/swordswind/ai_virtual_mate_linux)

[**swordswind/ai_virtual_mate_web** 在网页端上显示对话框](https://github.com/swordswind)

[**yutto-dev/yutto** 🧊 一个可爱且任性的 B 站视频下载器 打算借鉴 fastmcp 并且以此判别情绪和播放 live2d 动画](https://github.com/yutto-dev/yutto)

[**Arkueid/live2d-py** 直接使用 pygame 播放, 不兼容 linux, 但 live2d 动画播放和情绪识别值得借鉴. ](https://github.com/Arkueid/live2d-py)
