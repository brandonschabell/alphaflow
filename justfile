# Default recipe - show help
default:
    @echo "AlphaFlow Development Commands"
    @echo "=============================="
    @echo "just test          - Run pytest tests"
    @echo "just coverage      - Run tests with coverage report"
    @echo "just lint          - Run ruff formatter and linter"
    @echo "just typecheck     - Run mypy type checker"
    @echo "just check         - Run all checks (lint + typecheck + test)"
    @echo "just clean         - Remove cache files and build artifacts"
    @echo "just install       - Install dependencies"
    @echo "just docs          - Serve documentation locally"

test:
    @uv run pytest alphaflow/tests/

coverage:
    @uv run pytest alphaflow/tests/ --cov=alphaflow --cov-report=html --cov-report=term
    @echo "Coverage report generated in htmlcov/index.html"

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
    @rm -rf build/ dist/ .pytest_cache/ .ruff_cache/ .mypy_cache/ htmlcov/ .coverage

install:
    @uv sync

docs:
    @uv run mkdocs serve
