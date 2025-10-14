# Contributing to AlphaFlow

We welcome contributions from the community! Whether you're fixing bugs, adding features, improving documentation, or suggesting enhancements, your help is appreciated.

## Getting Started

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:
   ```bash
   git clone https://github.com/YOUR_USERNAME/alphaflow.git
   cd alphaflow
   ```

3. **Install dependencies using uv**:
   ```bash
   uv sync --all-extras
   ```

## Development Workflow

### Running Tests

```bash
make test
```

### Running Quality Checks

```bash
make check  # Runs ruff, mypy, and tests
```

### Code Coverage

```bash
make coverage
```

### Building Documentation

```bash
uv run mkdocs serve  # Preview docs locally at http://127.0.0.1:8000
uv run mkdocs build  # Build static site
```

## Code Style

- We use **ruff** for linting and formatting
- We use **mypy** for type checking
- All code must pass `make check` before being merged
- Maintain 90%+ test coverage for new code

## Pull Request Process

1. **Create a feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes** and commit with clear messages:
   ```bash
   git commit -m "Add feature: description of what you added"
   ```

3. **Push to your fork**:
   ```bash
   git push origin feature/your-feature-name
   ```

4. **Open a Pull Request** on GitHub with:
   - Clear description of changes
   - Any relevant issue numbers
   - Screenshots/examples if applicable

5. **Ensure all checks pass**:
   - CI tests must pass
   - Code coverage should not decrease
   - All quality checks must pass

## Areas for Contribution

### High Priority
- Additional strategy implementations
- More data feed integrations
- Broker improvements (slippage, partial fills)
- Performance optimizations

### Documentation
- API documentation improvements
- More examples and tutorials
- Case studies

### Testing
- Edge case coverage
- Integration tests
- Performance benchmarks

## Questions?

Open an issue on GitHub or start a discussion in the repository.

## Code of Conduct

Be respectful, inclusive, and constructive in all interactions.
