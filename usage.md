## 同步测试调用 openai

等待回复完所有内容后再输入下一句。

```shell
chatbot➜  chatbot git:(global-text-response) ✗ uv run test
2025-06-03 14:22:33.108 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 14:22:33.109 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-03 14:22:33.109 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 14:22:33.109 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
请输入:你好
 INFO  函数 get_openai_response 总用时: 1.7410 秒
 零壹万物  哼，你好啊，旅行者！你是不是又饿了呀？还是有什么事要找我帮忙？快说快说，我忙着呢！
 ```

 ## 异步测试调用 openai

切分长段落为句子，等待回复完所有内容后再输入下一句。

```shell
chatbot➜  chatbot git:(global-text-response) ✗ just test-async
uv run src/chatbot/test_async.py
2025-06-03 14:24:58.294 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 14:24:58.295 WARNING streamlit.runtime.state.session_state_proxy: Session state does not function when running a script without `streamlit run`
2025-06-03 14:24:58.295 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
2025-06-03 14:24:58.295 WARNING streamlit.runtime.scriptrunner_utils.script_run_context: Thread 'MainThread': missing ScriptRunContext! This warning can be ignored when running in bare mode.
请输入:你好呀
 INFO  首句耗时: 1.310 秒
 零壹万物  哼，旅行者，你总算出现了！
 零壹万物  我还以为你又被什么奇怪的玩意儿吸引住了呢。
 零壹万物  这次又有什么事呀？
 零壹万物  不会又是饿了要找吃的吧？
 INFO  总耗时: 2.006 秒
请输入:你是谁
 INFO  首句耗时: 1.322 秒
 零壹万物  哼，你这话问得真奇怪！
 零壹万物  我不是在这儿嘛！
 零壹万物  我是派蒙，你最棒的向导和伙伴！
 零壹万物  不要小看我哦，应急食品什么的绰号我可是会生气的！
 零壹万物  你怎么会不认识我呢，旅行者？
 INFO  总耗时: 2.409 秒
请输入:为什么第一句话你总是不回复我
 INFO  首句耗时: 1.336 秒
 零壹万物  哎呀，这不是明显嘛！
 零壹万物  你怎么这么笨呢，你是想让我把第一句吞下去吗？
 零壹万物  你没事吧？
 零壹万物  是不是肚子饿得厉害，脑袋都不好使了呀！
 INFO  总耗时: 2.523 秒
 ```