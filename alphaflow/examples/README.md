# AlphaFlow Examples

This directory contains example scripts demonstrating how to use AlphaFlow for backtesting trading strategies.

## Setup

### 1. Configure API Keys

Copy the `.env.example` file to `.env` in the project root:

```bash
cp .env.example .env
```

Then edit `.env` and add your actual API keys:

```bash
# .env file
ALPHA_VANTAGE_API_KEY=your_actual_key_here
POLYGON_API_KEY=your_actual_key_here
FMP_API_KEY=your_actual_key_here
```

**Note:** The `.env` file is gitignored, so your API keys will never be committed to the repository.

### 2. Get API Keys (Free Tiers Available)

- **Alpha Vantage**: [Get API Key](https://www.alphavantage.co/support/#api-key)
- **Polygon.io**: [Get API Key](https://polygon.io)
- **Financial Modeling Prep**: [Get API Key](https://financialmodelingprep.com/developer/docs/)

## Running Examples

All examples should be run as Python modules from the project root using `uv`:

```bash
# Polygon.io data feed example
uv run python -m alphaflow.examples.polygon_example

# Multiple strategy comparison example (Alpha Vantage)
uv run python -m alphaflow.examples.sample_strategies
```

## Available Examples

### `polygon_example.py`
Demonstrates using the Polygon.io data feed with a simple buy-and-hold strategy on AAPL.

**Requirements:** `POLYGON_API_KEY` in `.env`

### `sample_strategies.py`
Compares multiple portfolio allocation strategies using Alpha Vantage data:
- Equal Weight Portfolio
- 60/40 Portfolio
- All-Weather Portfolio
- Optimized Portfolio

**Requirements:** `ALPHA_VANTAGE_API_KEY` in `.env`

## Troubleshooting

### "API key not found"
Make sure you've:
1. Created a `.env` file in the project root (copy from `.env.example`)
2. Added your actual API key to the `.env` file
3. The example script loads dotenv (`load_dotenv()` is called)
