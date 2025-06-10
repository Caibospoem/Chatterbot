from __future__ import annotations

import streamlit as st

from chatbot.styles.global_style import style

# 参数配置
style()


st.toast("欢迎使用 ~", icon=":material/verified:")

st.title("Chatterbot v0.0.1")
st.caption(" A Project Powered By [@XnneHangLab](https://github.com/XnneHangLab/)")

st.html(
    """
<a href="https://xnnehang.top/">

<div align="center">
    <img src="https://fastly.jsdelivr.net/gh/MrXnneHang/blog_img/BlogHosting/img/25/02/202503312014744.svg" alt="魔女の实验室" width="270" height="180">
    """
)
