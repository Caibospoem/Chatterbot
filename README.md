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

## 本地部署

你需要安装 uv .

```shell
scoop install uv # windows 参考 scoop.sh 安装 scoop
curl -LsSf https://astral.sh/uv/install.sh | sh # linux/mac
```

## 用法

前提是你具备所有的远程服务, 参考配置文件:

```shell
sdk_base_url = "https://api.lingyiwanwu.com" # base_url, 可以是其他支持 openai 的服务  
sdk_key = "ccccf9935e0aaaaaaaaaaaaab84ecd" # sdk_key
vits_url = "http://localhost/tts"
asr_url = "http://localhost/rec-audio"
```

```shell
xnne@xnne-PC:~/code/chatbot$ uv run test
请输入:你好呀
 INFO  函数 get_openai_response 总用时: 1.3542 秒
 零壹万物  喵~ 主人，你好呀！有什么想和我一起做的吗？
 INFO  函数 get_tts_response 总用时: 0.7548 秒
语音已保存到 output.opus
 INFO  函数 write_tts_response 总用时: 0.0005 秒
 INFO  函数 get_asr_response 总用时: 0.4490 秒
 FunASR  喵主人，你好呀，有什么想和我一起做的吗？
ffplay version 6.1.1-2deepin0 Copyright (c) 2003-2023 the FFmpeg developers
  built with gcc 12 (Deepin 12.3.0-17deepin6)
  configuration: --prefix=/usr --extra-version=2deepin0 --toolchain=hardened --libdir=/usr/lib/x86_64-linux-gnu --incdir=/usr/include/x86_64-linux-gnu --arch=amd64 --enable-gpl --disable-stripping --enable-gnutls --enable-ladspa --enable-libaom --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libcodec2 --enable-libdav1d --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libharfbuzz --enable-libfribidi --enable-libglslang --enable-libgme --enable-libgsm --enable-libjack --enable-libmp3lame --enable-libmysofa --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librabbitmq --enable-librist --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libsrt --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvidstab --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libx265 --enable-libxml2 --enable-libxvid --enable-libzimg --enable-libzmq --enable-libzvbi --enable-lv2 --enable-omx --enable-openal --enable-opencl --enable-opengl --enable-sdl2 --disable-sndio --enable-libjxl --enable-pocketsphinx --enable-librsvg --enable-libvpl --disable-libmfx --enable-libdc1394 --enable-libdrm --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libsvtav1 --enable-libx264 --enable-libplacebo --enable-librav1e --enable-shared
  libavutil      58. 29.100 / 58. 29.100
  libavcodec     60. 31.102 / 60. 31.102
  libavformat    60. 16.100 / 60. 16.100
  libavdevice    60.  3.100 / 60.  3.100
  libavfilter     9. 12.100 /  9. 12.100
  libswscale      7.  5.100 /  7.  5.100
  libswresample   4. 12.100 /  4. 12.100
  libpostproc    57.  3.100 / 57.  3.100
Input #0, ogg, from 'output.opus': 0KB vq=    0KB sq=    0B f=0/0   
  Duration: 00:00:03.61, start: 0.000000, bitrate: 73 kb/s
  Stream #0:0: Audio: opus, 48000 Hz, mono, fltp
    Metadata:
      encoder         : Lavc60.31.102 libopus
   3.55 M-A: -0.000 fd=   0 aq=    0KB vq=    0KB sq=    0B f=0/0   
音频播放完成。
 INFO  函数 play_opus_file 总用时: 4.1004 秒
请输入:你可以帮我写代码吗
 INFO  函数 get_openai_response 总用时: 1.5477 秒
 零壹万物  我只是一个猫娘，这些事情我不太清楚呢。不过如果你有其他想要我帮忙的事情，我会尽量帮助你的哟！(o´ω`o)
 INFO  函数 get_tts_response 总用时: 0.8661 秒
语音已保存到 output.opus
 INFO  函数 write_tts_response 总用时: 0.0009 秒
 INFO  函数 get_asr_response 总用时: 0.5688 秒
 FunASR  我只是一个猫娘，这些事情我不太清楚呢。不过如果你有其他想要我帮忙的事情，我会尽量帮助你的哟。
ffplay version 6.1.1-2deepin0 Copyright (c) 2003-2023 the FFmpeg developers
  built with gcc 12 (Deepin 12.3.0-17deepin6)
  configuration: --prefix=/usr --extra-version=2deepin0 --toolchain=hardened --libdir=/usr/lib/x86_64-linux-gnu --incdir=/usr/include/x86_64-linux-gnu --arch=amd64 --enable-gpl --disable-stripping --enable-gnutls --enable-ladspa --enable-libaom --enable-libass --enable-libbluray --enable-libbs2b --enable-libcaca --enable-libcdio --enable-libcodec2 --enable-libdav1d --enable-libflite --enable-libfontconfig --enable-libfreetype --enable-libharfbuzz --enable-libfribidi --enable-libglslang --enable-libgme --enable-libgsm --enable-libjack --enable-libmp3lame --enable-libmysofa --enable-libopenjpeg --enable-libopenmpt --enable-libopus --enable-libpulse --enable-librabbitmq --enable-librist --enable-librubberband --enable-libshine --enable-libsnappy --enable-libsoxr --enable-libspeex --enable-libsrt --enable-libssh --enable-libtheora --enable-libtwolame --enable-libvidstab --enable-libvorbis --enable-libvpx --enable-libwebp --enable-libx265 --enable-libxml2 --enable-libxvid --enable-libzimg --enable-libzmq --enable-libzvbi --enable-lv2 --enable-omx --enable-openal --enable-opencl --enable-opengl --enable-sdl2 --disable-sndio --enable-libjxl --enable-pocketsphinx --enable-librsvg --enable-libvpl --disable-libmfx --enable-libdc1394 --enable-libdrm --enable-libiec61883 --enable-chromaprint --enable-frei0r --enable-libsvtav1 --enable-libx264 --enable-libplacebo --enable-librav1e --enable-shared
  libavutil      58. 29.100 / 58. 29.100
  libavcodec     60. 31.102 / 60. 31.102
  libavformat    60. 16.100 / 60. 16.100
  libavdevice    60.  3.100 / 60.  3.100
  libavfilter     9. 12.100 /  9. 12.100
  libswscale      7.  5.100 /  7.  5.100
  libswresample   4. 12.100 /  4. 12.100
  libpostproc    57.  3.100 / 57.  3.100
Input #0, ogg, from 'output.opus': 0KB vq=    0KB sq=    0B f=0/0   
  Duration: 00:00:08.13, start: 0.000000, bitrate: 74 kb/s
  Stream #0:0: Audio: opus, 48000 Hz, mono, fltp
    Metadata:
      encoder         : Lavc60.31.102 libopus
   8.05 M-A:  0.000 fd=   0 aq=    0KB vq=    0KB sq=    0B f=0/0   
音频播放完成。
 INFO  函数 play_opus_file 总用时: 8.4686 秒
 ```

`vits_url` 可以部署 [Bert-VITS2.3-Inference](https://github.com/MrXnneHang/Bert-VITS2.3-Inference) , 然后运行 `just server`.

`asr_url` 可以部署 [XnneHangLab](https://github.com/XnneHangLab/XnneHangLab) , 然后运行 `just server`,

有问题可以提 issue.

> [!note]
> 你可以利用 frp 和一个远程服务器来实现远程访问, 然后在树莓派部署该服务.(因为虽然树莓派也可以直接运行 FunASR 和 Bert-VITS2 但速度跟乌龟爬一样.)

## 引用的仓库

[**Bert-VITS-Inference:** 仅保留推理部分的代码, 仅兼容 2.3 的模型, 用 uv 重构的推理模块, 可用 fastapi 调用, 可用 streamlit WebUI](https://github.com/MrXnneHang/Bert-VITS2.3-Inference)

[**XnneHangLab:** 综合性仓库, 支持从 b 站视频下载 -> 字幕识别和编辑(使用funasr), 使用 streamlit WebUI, 可用 fastapi 调用部分功能, 支持 cli](https://github.com/XnneHangLab/XnneHangLab)
