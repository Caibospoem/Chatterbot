start:
  uv lock
  uv sync
  uv run get_root
  uv run streamlit run src/lab/ui.py --server.port 8051

test-openai:
  uv run src/chatbot/tests/test_async_openai.py

test-workflow:
  uv run src/chatbot/tests/test_async_openai_workflow.py


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