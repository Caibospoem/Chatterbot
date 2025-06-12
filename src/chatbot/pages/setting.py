from __future__ import annotations

from pathlib import Path

import streamlit as st

from chatbot._dictionary import session_keys
from chatbot.config_manager import ServiceSettings, load_settings_file, write_settings_file
from chatbot.styles.global_style import style

style()


@st.dialog("消息")
def message_box(title: str, message: str):
    st.markdown("")
    st.markdown(f"### {title} \n {message}")


settings = load_settings_file("config.toml", setting=ServiceSettings)

# Store initial settings in session state if not already present
if session_keys["initial_settings"] not in st.session_state:
    st.session_state.initial_settings = {
        "url": {
            session_keys["asr_url"]: settings.asr_url,
            session_keys["vad_url"]: settings.vad_url,
            session_keys["vits_split_url"]: settings.vits_split_url,
            session_keys["vits_direct_url"]: settings.vits_direct_url,
            session_keys["sdk_base_url"]: settings.sdk_base_url,
            session_keys["sdk_key"]: settings.sdk_key,
            session_keys["access_key"]: settings.access_key,
        },
        "basic": {
            session_keys["cache_dir"]: settings.cache_dir,
            session_keys["system_platform"]: settings.system_platform,
            session_keys["promopt"]: settings.promopt,
        },
    }

# Initialize current values from settings or session state if available after rerun
asr_url = st.session_state.get(session_keys["asr_url"], settings.asr_url)
vad_url = st.session_state.get(session_keys["vad_url"], settings.vad_url)
vits_split_url = st.session_state.get(session_keys["vits_split_url"], settings.vits_split_url)
vits_direct_url = st.session_state.get(session_keys["vits_direct_url"], settings.vits_direct_url)
sdk_base_url = st.session_state.get(session_keys["sdk_base_url"], settings.sdk_base_url)
sdk_key = st.session_state.get(session_keys["sdk_key"], settings.sdk_key)
access_key = st.session_state.get(session_keys["access_key"], settings.access_key)
cache_dir = st.session_state.get(session_keys["cache_dir"], settings.cache_dir)
system_platform = st.session_state.get(session_keys["system_platform"], settings.system_platform)
promopt = st.session_state.get(session_keys["promopt"], settings.promopt)


BOTSave = st.container()
BOTSetting = st.container(border=True)
with BOTSetting:
    st.markdown("")
    st.markdown("###### 服务配置")
    st.markdown("")
    asr_url = st.text_input(
        "ASR 服务地址",
        value=asr_url,
        placeholder="ASR URL",
        key="asr_url",  # Add key
    )
    vad_url = st.text_input(
        "VAD 服务地址",
        value=vad_url,
        placeholder="VAD URL",
        key="vad_url",  # Add key
    )
    st.caption("vad_url 和 asr_url 均可以部署 XnneHangLab 得到.")
    vits_split_url = st.text_input(
        "VITS 切分生成服务地址",
        value=vits_split_url,
        placeholder="VITS Split URL",
        key="vits_split_url",  # Add key
    )
    vits_direct_url = st.text_input(
        "VITS 直接生成服务地址",
        value=vits_direct_url,
        placeholder="VITS Direct URL",
        key="vits_direct_url",  # Add key
    )
    st.caption("VITS 服务地址可以通过部署 Bert-VITS-Inference 来得到.")
    sdk_base_url = st.text_input(
        "OpenAI SDK Base URL",
        value=sdk_base_url,
        placeholder="SDK Base URL",
        key="sdk_base_url",  # Add key
    )
    sdk_key = st.text_input(
        "OpenAI SDK Key",
        value=sdk_key,
        placeholder="SDK Key",
        key="sdk_key",  # Add key
    )
    st.caption("OpenAI SDK Base URL 和 SDK Key 可以选择支持 OpenAI API 的服务提供商。")
    access_key = st.text_input(
        "Picovoice Porcupine Access Key",
        value=access_key,
        placeholder="Access Key",
        key="access_key",  # Add key
    )
    st.caption("Picovoice Porcupine Access Key 可以通过注册 Picovoice 账号免费获取。")
    st.markdown("")
    st.markdown("###### 基础")
    cache_dir = st.text_input(
        "缓存目录",
        value=cache_dir,
        placeholder="Cache Directory",
        key="cache_dir",  # Add key
    )
    promopt = st.text_input(
        "提示文件路径",
        value=promopt,
        placeholder="Prompt File Path",
        key="promopt",  # Add key
    )
    st.caption("缓存目录用于存储临时文件和缓存数据。")
    system_platform = st.selectbox(
        "系统平台",
        options=["raspberry-pi", "linux", "macos", "windows"],
        index=["raspberry-pi", "linux", "macos", "windows"].index(system_platform),
        key="system_platform",  # Add key
    )
    st.markdown("")

with BOTSave:
    col1, col2 = st.columns([0.75, 0.25])
    with col2:
        st.markdown("")
        st.markdown("")
        if st.button("**保存更改**", type="primary", use_container_width=True):
            current_settings = {
                "service": {
                    "asr_url": asr_url,
                    "vad_url": vad_url,
                    "vits_split_url": vits_split_url,
                    "vits_direct_url": vits_direct_url,
                    "sdk_base_url": sdk_base_url,
                    "sdk_key": sdk_key,
                    "access_key": access_key,
                },
                "basic": {
                    "cache_dir": cache_dir,
                    "promopt": promopt,
                    "system_platform": system_platform,
                },
            }

            initial_settings = st.session_state[session_keys["initial_settings"]]

            if current_settings != initial_settings:  # Compare dictionaries
                # Update session state with new settings
                settings.asr_url = asr_url
                settings.vad_url = vad_url
                settings.vits_split_url = vits_split_url
                settings.vits_direct_url = vits_direct_url
                settings.sdk_base_url = sdk_base_url
                settings.sdk_key = sdk_key
                settings.access_key = access_key
                settings.cache_dir = cache_dir
                settings.system_platform = system_platform  # type: ignore
                settings.promopt = promopt
                write_settings_file(settings_name="config.toml", settings=settings)
                message_box("保存成功！", "你也可以通过手动配置 `config.toml` 来修改配置。")
                st.session_state[session_keys["initial_settings"]] = (
                    current_settings  # Update initial settings after save
                )
            else:
                message_box("未检测到更改", "配置未发生任何变化，无需保存。")

        if st.button("**恢复默认设置**", type="secondary", use_container_width=True):
            settings = Path("config") / "config.toml"
            settings.unlink()
            load_settings_file("config.toml", ServiceSettings)
            message_box("恢复成功！", "配置已恢复为默认设置。刷新页面即可查看更改。")

    with col1:
        st.markdown("")
        st.markdown("")
        st.markdown("### 设置")
        st.caption("Settings")
        st.markdown("")
