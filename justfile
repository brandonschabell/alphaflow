# Default recipe - show help
default:
    @echo "AlphaFlow Development Commands"
    @echo "=============================="
    @echo "just test          - Run pytest tests"
    @echo "just coverage      - Run tests with coverage report"
    @echo "just lint          - Run ruff formatter and linter"
    @echo "just typecheck     - Run ty type checker"
    @echo "just check         - Run all checks (lint + typecheck + test)"
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
    @uv run ty check

check: lint typecheck test

install:
    @uv sync

docs:
    @uv run mkdocs serve
