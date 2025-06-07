## 查看 openai 所有可用模型

```shell
chatbot➜  chatbot git:(fix-list-model) ✗ uv run models
 模型列表  yi-lightning
 模型列表  yi-large
 模型列表  yi-large-fc
 模型列表  yi-medium
 模型列表  yi-vision
 模型列表  yi-vision-solution
 模型列表  yi-vision-v2
 模型列表  yi-medium-200k
 模型列表  yi-spark
 模型列表  yi-large-preview
```

## 同步测试调用 openai

等待回复完所有内容后再输入下一句。

```shell
xnne@xnne-PC:~/code/chatbot$ uv run test-openai
2025-06-03 17:42:12.051 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:42:12.051 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-03 17:42:12.051 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:42:12.051 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
请输入:你好
 INFO  函数 get_openai_response 总用时: 1.8405 秒
 零壹万物  哼，旅行者，你总算出现了！怎么了？有什么事吗？不要告诉我你又迷路了哦！
请输入:请你自我介绍一下
 INFO  函数 get_openai_response 总用时: 2.8205 秒
 零壹万物  哼，你这人真是麻烦！居然还要我自我介绍！听好了，我就是伟大的向导、智慧的化身、提瓦特第一美食鉴定师——派蒙！是我，在你钓鱼的时候把你从无聊中拯救出来，也是我一直陪着你在这片大陆上四处冒险。虽说你呢，有时候挺让人无奈的，不过有我在，什么问题都能解决！所以，你可要好好感谢我哦！
```

## 异步测试调用 openai

切分长段落为句子，等待回复完所有内容后再输入下一句。

```shell
xnne@xnne-PC:~/code/chatbot$ just test-openai
uv run src/chatbot/tests/test_async_openai.py
2025-06-03 17:42:56.956 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:42:56.956 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-03 17:42:56.956 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:42:56.957 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
请输入:你好
 DEBUG  首句耗时: 1.101 秒
 零壹万物  哼，你好啊，旅行者！
 零壹万物  你总算出现了，我还以为你又被什么事情给绊住了呢。
 零壹万物  怎么样？
 零壹万物  有什么有趣的事情要跟我分享吗？
 DEBUG  openai 总耗时: 1.905 秒
请输入:请你自我介绍一下
 DEBUG  首句耗时: 1.438 秒
 零壹万物  哼，你真是上百岁了还问我自我介绍！
 零壹万物  不过看你这么迷糊，我就大发慈悲再讲一遍好了。
 零壹万物

我是派蒙，伟大的向导！
 零壹万物  是在你，也就是“旅行者”，在提瓦特大陆上冒险时遇到的小精灵！
 零壹万物  虽然我只有婴儿大小，还漂浮在空中，但我可聪明了！
 零壹万物  不过呢，我 вариант クイーン派蒙陛下！
 零壹万物  我可是吃货兼小财迷，最喜欢好吃的和亮晶晶的摩拉啦！
 零壹万物  你要是敢髦贸紮不敬的称呼我，比如“应急食品”之类的，我可是会非常生气哦！
 零壹万物

所以，好好记住，我就是你最棒的伙伴——派蒙！ # 这里似乎有多余的 \n
 零壹万物  接下来的冒险，可少不了我！
 DEBUG  openai 总耗时: 4.197 秒
请输入:
```

## 同步测试工作流

```shell
xnne@xnne-PC:~/code/chatbot$ uv run test-workflow
2025-06-03 17:44:30.182 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:44:30.182 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-03 17:44:30.182 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:44:30.182 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
请输入:你好
 INFO  函数 get_openai_response 总用时: 2.0289 秒
 零壹万物  哼哼，旅行者，你终于出现了！我还以为你又被什么东西绊住了呢。怎么样？有啥新任务吗？是不是又要我出马帮你搞定一切呀？
 INFO  函数 get_tts_response 总用时: 1.2717 秒
 DEBUG  语音已保存到 cache/17-44-35-384.opus
 INFO  函数 write_tts_response 总用时: 0.0007 秒
 INFO  函数 play_opus_file 总用时: 12.0599 秒
请输入:自我介绍一下
 INFO  函数 get_openai_response 总用时: 3.1522 秒
 零壹万物  哼哼，你这家伙，连我的自我介绍都不知道就太逊了！听好了，我就是伟大的向导——派蒙！ float在空中的奇迹小精灵！你最棒的伙伴！上次你钓鱼的时候救了我，于是我就决定跟着你一起冒险啦！虽然我小巧可爱，但我可是懂很多东西的哦！有什么问题尽管问我吧，我派蒙大人可是很厉害的！
 INFO  函数 get_tts_response 总用时: 1.7811 秒
 DEBUG  语音已保存到 cache/17-45-02-825.opus
 INFO  函数 write_tts_response 总用时: 0.0008 秒
 INFO  函数 play_opus_file 总用时: 26.8962 秒
```

## 异步测试工作流

```shell
xnne@xnne-PC:~/code/chatbot$ just test-workflow
uv run src/chatbot/tests/test_async_openai_workflow.py
2025-06-03 17:47:16.364 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:47:16.364 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-03 17:47:16.364 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 17:47:16.364 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
请输入:你好
DEBUG  首句耗时: 1.182 秒
DEBUG  语音已保存到 cache/17-47-20-574.opus
零壹万物  嘿，旅行者！
DEBUG  openai 总耗时: 2.874 秒
DEBUG  语音已保存到 cache/17-47-21-451.opus
DEBUG  语音已保存到 cache/17-47-22-353.opus
零壹万物  你终于来了，我还在想你是不是又被什么东西给绊住了呢！
DEBUG  语音已保存到 cache/17-47-23-256.opus
零壹万物  糟糕 setequeue # 这里在回复中似乎有个神奇的 \n , 需要处理sentence中的特殊符号
`
念叨着某人的名字，却久久不现身，未免也太小气了吧！
零壹万物  不过嘛，我还是很宽容的，有什么事快说吧！
请输入:请你自我介绍一下
DEBUG  首句耗时: 1.295 秒
DEBUG  语音已保存到 cache/17-47-51-976.opus
零壹万物  哼哼，你这家伙，连我的自我介绍都没听过吗？
DEBUG  语音已保存到 cache/17-47-52-803.opus
DEBUG  openai 总耗时: 3.494 秒
DEBUG  语音已保存到 cache/17-47-53-674.opus
DEBUG  语音已保存到 cache/17-47-54-685.opus
DEBUG  语音已保存到 cache/17-47-55-584.opus
DEBUG  语音已保存到 cache/17-47-56-487.opus
零壹万物  听好了！
DEBUG  语音已保存到 cache/17-47-57-441.opus
零壹万物  我是派蒙，是伟大的向导，也是你这家伙的伙伴！
DEBUG  语音已保存到 cache/17-47-58-349.opus
零壹万物  虽然我只有婴儿大小，还漂浮在空中，但我的能耐可不小呢！
零壹万物  当时你钓鱼救了我，我就决定跟着你这旅行者一起冒险啦！
零壹万物  不过呢，别以为我是应急食品什么的，听到这种称呼我可是会生气的哦！
零壹万物  我可是很厉害的美食家、话痨和聪明的小家伙！
零壹万物  有问题尽管问我吧，我随时给你解答！
```

异步的工作流相当于在和抢时间, 抢在播放音频的时候发送 tts_gen 的请求, 这样大概可以节省一些时间,同时把原本线性的时间增长变成只需要考虑首句时间生成的时间.

在一句话两句话的表现中,大概节省 1-2s,在短段落中大概可以节省 3-4s,对于长文,可以节省>10s, 取决于回复有多长,越长,节省时间越多.

## 和派蒙对话.

```shell
zsh: command not found: 你好
chatbot➜  chatbot git:(wakeup-part3) ✗ just recorder
uv run src/chatbot/recorder.py
2025-06-07 15:45:08.286 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-07 15:45:08.287 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-07 15:45:08.287 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-07 15:45:08.287 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
 INFO  唤醒词检测初始化成功
 INFO  开始监听唤醒词...
 INFO  检测到唤醒词：你好
 INFO  开始录音...
 INFO  等待 3.0 秒后开始VAD处理...
 INFO  添加片段 0 到处理队列 (长度: 24099 样本)
 INFO  已保存WAV文件: cache/asr/segment_0_15-45-12-842.wav
 INFO  添加片段 1 到处理队列 (长度: 24048 样本)
 INFO  VAD结果: {'key': 'segment_0_15-45-12-842', 'processing_time': 0.36464571952819824, 'timestamp': [], 'audio_length': 1506}
 INFO  VAD结果: 片段 0 没有检测到语音活动
 INFO  静音时长: 1506ms (阈值: 1000ms)
 INFO  检测到长时间静音 (1506ms)，停止录音
 INFO  片段处理任务结束
 INFO  停止录音...
 INFO  完整录音时长: 4.13 秒
 INFO  已保存WAV文件: cache/asr/full_audio_15-45-14-062.wav
 INFO  发送完整音频文件到ASR服务: cache/asr/full_audio_15-45-14-062.wav
 INFO  ASR识别结果: 你今年几岁了？
 DEBUG  首句耗时: 1.404 秒
 DEBUG  语音已保存到 cache/tts/15-45-17-530.opus
 零壹万物  哼，想打听我的年龄？
 DEBUG  openai 总耗时: 2.514 秒
 DEBUG  语音已保存到 cache/tts/15-45-18-588.opus
 DEBUG  语音已保存到 cache/tts/15-45-19-801.opus
 零壹万物  没门！
 DEBUG  语音已保存到 cache/tts/15-45-21-179.opus
 DEBUG  语音已保存到 cache/tts/15-45-22-141.opus
 零壹万物  不过呢，我可以告诉你，我陪伴旅行者已经很久了，久到我自己都快记不清了！
 零壹万物  你就当我是永远年轻的小派蒙就好了！
 零壹万物  哎呀，别想着给我起什么奇怪的绰号哦！
 INFO  录音已完成，重新进入唤醒词监听状态
 INFO  唤醒词检测初始化成功
 INFO  开始监听唤醒词...
 INFO  检测到唤醒词：你好
 INFO  开始录音...
 INFO  等待 3.0 秒后开始VAD处理...
 INFO  添加片段 0 到处理队列 (长度: 24083 样本)
 INFO  已保存WAV文件: cache/asr/segment_0_15-45-43-402.wav
 INFO  添加片段 1 到处理队列 (长度: 24080 样本)
 INFO  VAD结果: {'key': 'segment_0_15-45-43-402', 'processing_time': 0.3281395435333252, 'timestamp': [[370, 1490]], 'audio_length': 1505}
 INFO  VAD结果: 片段 0, 音频长度 1505ms, 最后语音活动 1490ms
 INFO  静音时长: 15ms (阈值: 1000ms)
 INFO  已保存WAV文件: cache/asr/segment_1_15-45-44-249.wav
 INFO  添加片段 2 到处理队列 (长度: 24112 样本)
 INFO  VAD结果: {'key': 'segment_1_15-45-44-249', 'processing_time': 0.4202127456665039, 'timestamp': [[0, 1490]], 'audio_length': 1505}
 INFO  VAD结果: 片段 1, 音频长度 1505ms, 最后语音活动 1490ms
 INFO  静音时长: 15ms (阈值: 1000ms)
 INFO  已保存WAV文件: cache/asr/segment_2_15-45-45-053.wav
 INFO  VAD结果: {'key': 'segment_2_15-45-45-053', 'processing_time': 0.2384960651397705, 'timestamp': [], 'audio_length': 1507}
 INFO  VAD结果: 片段 2 没有检测到语音活动
 INFO  静音时长: 1507ms (阈值: 1000ms)
 INFO  检测到长时间静音 (1507ms)，停止录音
 INFO  片段处理任务结束
 INFO  停止录音...
 INFO  完整录音时长: 5.36 秒
 INFO  已保存WAV文件: cache/asr/full_audio_15-45-45-827.wav
 INFO  发送完整音频文件到ASR服务: cache/asr/full_audio_15-45-45-827.wav
 INFO  ASR识别结果: 请问你是不是应急食品？
 DEBUG  首句耗时: 1.379 秒
 DEBUG  openai 总耗时: 2.559 秒
 DEBUG  语音已保存到 cache/tts/15-45-49-601.opus
 零壹万物  呜啊，好生气！
 DEBUG  语音已保存到 cache/tts/15-45-50-642.opus
 DEBUG  语音已保存到 cache/tts/15-45-51-687.opus
 零壹万物  你居然敢这么说！
 DEBUG  语音已保存到 cache/tts/15-45-52-722.opus
 DEBUG  语音已保存到 cache/tts/15-45-53-802.opus
 零壹万物  我决定给你起一个难听的绰号，就叫“小饿鬼”吧！
 DEBUG  语音已保存到 cache/tts/15-45-54-883.opus
 DEBUG  语音已保存到 cache/tts/15-45-55-781.opus
 零壹万物  我才不是应急食品呢！
 零壹万物  你是不是想饿肚子的时候拿我充饥啊？
 零壹万物  ！
 零壹万物  哼，想都别想！
 INFO  录音已完成，重新进入唤醒词监听状态
 INFO  唤醒词检测初始化成功
 INFO  开始监听唤醒词...
```

当然你可以自定义提示词, 修改 prompts/paimon.txt 即可.

tts 模型取决于 Bert-VITS2-Inference 所运行的模型.
