.PHONY: help test lint typecheck check clean install docs

help:
	@echo "AlphaFlow Development Commands"
	@echo "=============================="
	@echo "make test          - Run pytest tests"
	@echo "make lint          - Run ruff formatter and linter"
	@echo "make typecheck     - Run mypy type checker"
	@echo "make check         - Run all checks (lint + typecheck + test)"
	@echo "make clean         - Remove cache files and build artifacts"
	@echo "make install       - Install dependencies"
	@echo "make docs          - Serve documentation locally"

test:
	@uv run pytest alphaflow/tests/

lint:
	@uv run ruff format alphaflow/
	@uv run ruff check --fix alphaflow/

typecheck:
	@uv run mypy alphaflow/

check: lint typecheck test

clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete
	@find . -type f -name "*.pyo" -delete
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -rf build/ dist/ .pytest_cache/ .ruff_cache/ .mypy_cache/

install:
	@uv sync

docs:
	@uv run mkdocs serve
