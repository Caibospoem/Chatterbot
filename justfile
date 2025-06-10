start:
  uv run streamlit run src/chatbot/webui.py

test-openai:
  uv run src/chatbot/tests/test_async_openai.py

test-workflow:
  uv run src/chatbot/tests/test_async_openai_workflow.py

test-vad:
  uv run src/chatbot/tests/test_async_vad.py

server:
  uv run uvicorn src.chatbot.live2d:app --reload --host 0.0.0.0 --port 7900

recorder:
  uv run src/chatbot/recorder.py

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

ci-install:
  uv lock
  uv sync


ci-test:
  just test

ci-fmt-check:
  just fmt

ci-lint:
  just lint