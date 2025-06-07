start:
  uv lock
  uv sync
  uv run get_root
  uv run streamlit run src/lab/ui.py --server.port 8051

server:
  uv run uvicorn src.chatbot.live2d:app --reload --host localhost --port 7900

test-openai:
  uv run src/chatbot/tests/test_async_openai.py

test-workflow:
  uv run src/chatbot/tests/test_async_openai_workflow.py

test-vad:
  uv run src/chatbot/tests/test_async_vad.py

recorder:
  uv run src/chatbot/recorder.py

asr:
  uv run src/chatbot/realtime_asr.py --host "realasr.xnnehang.top" --port 28080 --audio_in /home/xnne/code/chatbot/cache/asr/temp_wav_11-17-32-471.wav

vad:
  uv run src/chatbot/vad.py

fmt: # 似乎不会检查被 .gitignore 忽略的文件
  uv run ruff check --fix --select I . --exclude packages
  uv run ruff format . --exclude packages

lint:
  uv run pyright src/chatbot
  uv run ruff check . --exclude packages

fmt-docs:
  prettier --ignore-path .prettierignore --write '**/*.md'

test:
  uv run pytest tests -vvv

install-model:
  uv lock
  uv sync

  # ASR with hotwords
  uv run modelscope download --model iic/speech_fsmn_vad_zh-cn-16k-common-pytorch --local_dir ./models/speech_fsmn_vad_zh-cn-16k-common-pytorch
  uv run modelscope download --model iic/speech_charctc_kws_phone-xiaoyun --local_dir ./models/speech_charctc_kws_phone-xiaoyun

ci-install:
  uv lock
  uv sync


ci-test:
  just test

ci-fmt-check:
  just fmt

ci-lint:
  just lint