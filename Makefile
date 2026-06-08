UV_CACHE_DIR ?= /tmp/uv-cache
APP ?= collector.main:app
HOST ?= 127.0.0.1
PORT ?= 8000

.PHONY: install run test lint check

install:
	env UV_CACHE_DIR=$(UV_CACHE_DIR) uv sync

run:
	env UV_CACHE_DIR=$(UV_CACHE_DIR) uv run uvicorn $(APP) --host $(HOST) --port $(PORT) --reload

test:
	env UV_CACHE_DIR=$(UV_CACHE_DIR) uv run python -m pytest

lint:
	env UV_CACHE_DIR=$(UV_CACHE_DIR) uv run ruff check .

check: lint test
