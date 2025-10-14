.PHONY: help test lint check clean install docs sync

help:
	@echo "AlphaFlow Development Commands"
	@echo "=============================="
	@echo "make test          - Run pytest tests"
	@echo "make lint          - Run ruff formatter and linter with auto-fix"
	@echo "make check         - Run both linter and tests"
	@echo "make clean         - Remove Python cache files and build artifacts"
	@echo "make install       - Sync uv environment with lockfile"
	@echo "make sync          - Sync uv environment with lockfile"
	@echo "make docs          - Serve documentation locally with mkdocs"

test:
	uv run pytest alphaflow/tests/

lint:
	uv run ruff format alphaflow/
	uv run ruff check --fix alphaflow/

check: lint test

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf build/ dist/ .pytest_cache/ .ruff_cache/

install:
	uv sync

sync:
	uv sync

docs:
	uv run mkdocs serve
