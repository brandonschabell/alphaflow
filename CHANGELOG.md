# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Replaced `Make` with `just` for development commands

## [0.2.0] - 2025-11-11

### Added
- **Polygon.io Data Feed** - New data source supporting daily and intraday market data
- **`.env` File Support** - Store API keys securely without committing them to version control
- **Rate Limit Handling** - Automatic retry with configurable backoff for API rate limits (HTTP 429 errors)
- **Slippage Models** - Pluggable slippage modeling with `FixedSlippageModel` for basis point slippage
- **Commission Models** - Three commission types: fixed per trade, per share, and percentage-based
- **Transaction Cost Analytics** - DefaultAnalyzer now tracks slippage and commission costs
- **Python 3.14** - Adds support for python 3.14

### Changed
- **BREAKING**: Replaced `pandas` with `polars` for improved performance (CSVDataFeed API unchanged)
- **BREAKING**: Replaced `seaborn`/`matplotlib` with `plotly` for interactive visualizations
- Examples now automatically load API keys from `.env` file
- Added `python-dotenv>=1.0.0` dependency
- `SimpleBroker` accepts optional `slippage_model` and `commission_model` parameters

### Fixed
- Timestamp handling now works correctly across all system timezones

[0.2.0]: https://github.com/brandonschabell/alphaflow/releases/tag/v0.2.0

## [0.1.1] - 2025-10-18

### Fixed
- **FMPDataFeed**: Fixed compatibility with Financial Modeling Prep's new API endpoint. Users with free FMP accounts created after August 31, 2025 can now use the data feed.

[0.1.1]: https://github.com/brandonschabell/alphaflow/releases/tag/v0.1.1

## [0.1.0] - 2025-10-14

### Added
- **Event-Driven Architecture**: Complete pub-sub event bus implementation with priority-based event queue
  - `EventBus` with immediate and queued publishing modes
  - `EventQueue` with chronological ordering and priority levels
  - Proper event ordering ensures MarketData → Order → Fill sequence
- **Core Components**:
  - `AlphaFlow` - Main backtest engine
  - `Strategy` - Base class for trading strategies
  - `Broker` - Base class for order execution
  - `DataFeed` - Base class for market data providers
  - `Portfolio` - Position and cash tracking with performance calculations
  - `Analyzer` - Base class for performance analysis
- **Built-in Strategies**:
  - `BuyAndHoldStrategy` - Rebalancing strategy with target weights, quantization, and minimum trade thresholds
- **Built-in Brokers**:
  - `SimpleBroker` - Basic order execution with margin support and commission handling
- **Built-in Data Feeds**:
  - `CSVDataFeed` - Load historical data from CSV files
  - `AlphaVantageFeed` - Integration with Alpha Vantage API
  - `FMPDataFeed` - Integration with Financial Modeling Prep API
- **Built-in Analyzers**:
  - `DefaultAnalyzer` - Comprehensive performance metrics including:
    - Sharpe Ratio
    - Sortino Ratio
    - Maximum Drawdown
    - Annualized Return
    - Total Return
    - Benchmark comparison
    - Portfolio value visualization
- **Event Types**:
  - `MarketDataEvent` - OHLCV price bars
  - `OrderEvent` - Trading orders (market/limit, buy/sell)
  - `FillEvent` - Trade executions with commissions
- **Features**:
  - Benchmark comparison (e.g., SPY for S&P 500)
  - Commission tracking and deduction
  - Margin trading support with buying power calculations
  - Flexible timestamp handling (datetime objects or ISO strings)
  - Position tracking and portfolio valuation
  - Configurable backtest time periods
  - Data caching for performance
- **Testing**:
  - 97 comprehensive unit tests
  - 92% code coverage
  - Full CI/CD pipeline with GitHub Actions
- **Documentation**:
  - Complete Getting Started guide
  - API reference documentation
  - Architecture overview
  - Contributing guidelines
  - ReadTheDocs integration

### Technical Details
- Event comparison protocol for chronological sorting
- Type hints throughout the codebase
- Strict mypy type checking
- Ruff linting and formatting
- Python 3.10+ support (3.10, 3.11, 3.12, 3.13)

### Known Limitations
- Single timeframe support (daily/intraday bars)
- No partial fills (fills are immediate and complete)
- No slippage modeling (planned for v0.2)
- No advanced order types (stop-loss, take-profit, etc.)
- No multi-asset portfolio optimization tools
- Limited to stocks/ETFs (futures, forex, crypto, options coming in future versions)

### Dependencies
- `pandas` - Data handling
- `httpx` - Modern HTTP client for API data feeds
- `seaborn` - Visualization
- `matplotlib` (via seaborn) - Plotting

[0.1.0]: https://github.com/brandonschabell/alphaflow/releases/tag/v0.1.0
