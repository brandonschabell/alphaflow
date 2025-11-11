# AlphaFlow AI Coding Agent Instructions

## Project Overview
AlphaFlow is an event-driven backtesting framework for trading strategies built on a pub-sub architecture. Components communicate exclusively through an `EventBus` that routes typed events (`MarketDataEvent`, `OrderEvent`, `FillEvent`) between loosely-coupled modules.

## Core Architecture Pattern

**Event-Driven Pub-Sub Flow:**
1. `DataFeed` → publishes `MarketDataEvent` (Topic.MARKET_DATA)
2. `Strategy` → subscribes to market data, publishes `OrderEvent` (Topic.ORDER)
3. `Broker` → subscribes to orders, publishes `FillEvent` (Topic.FILL)
4. `Portfolio` → subscribes to fills, updates positions/cash
5. `Analyzer` → subscribes to multiple topics, generates metrics

**Key Implementation Details:**
- All components inherit from `Subscriber` base class and implement `read_event(event)` and `topic_subscriptions()`
- Components are registered with `AlphaFlow` main class which wires them to the `EventBus`
- Events are immutable `@dataclass(frozen=True)` with `timestamp` as required field
- See `alphaflow/__init__.py` for base interfaces (Strategy, Broker, DataFeed, Analyzer, Portfolio)

## Component Implementation Patterns

### Creating a Strategy
```python
from alphaflow import Strategy
from alphaflow.enums import Topic, OrderType, Side
from alphaflow.events import MarketDataEvent, OrderEvent

class MyStrategy(Strategy):
    def topic_subscriptions(self):
        return [Topic.MARKET_DATA]
    
    def read_event(self, event: MarketDataEvent):
        # Access portfolio state via self._alpha_flow.portfolio
        # Publish orders via self._alpha_flow.event_bus.publish(Topic.ORDER, OrderEvent(...))
        pass
```
**Pattern:** Strategies filter events by `symbol` and timestamp bounds (`backtest_start_timestamp`/`backtest_end_timestamp`). See `strategies/buy_and_hold_strategy.py` for reference implementation with rebalancing logic.

### Creating a Broker
```python
from alphaflow import Broker
from alphaflow.events import OrderEvent, FillEvent

class MyBroker(Broker):
    def read_event(self, event: OrderEvent):
        # Validate order against portfolio state
        # Generate FillEvent and publish to Topic.FILL
        pass
```
**Pattern:** Brokers check buying power via `portfolio.get_buying_power(margin, timestamp)` and positions via `portfolio.get_position(symbol)`. See `brokers/simple_broker.py` for margin handling.

### Creating a DataFeed
```python
from alphaflow import DataFeed
from alphaflow.events import MarketDataEvent

class MyDataFeed(DataFeed):
    def run(self, symbol: str, start_timestamp, end_timestamp) -> Generator[MarketDataEvent]:
        # Yield MarketDataEvent objects sorted by timestamp
        yield MarketDataEvent(timestamp=..., symbol=symbol, open=..., high=..., low=..., close=..., volume=...)
```
**Pattern:** DataFeeds must yield events in chronological order. AlphaFlow calls `run()` per symbol in universe. See `data_feeds/csv_data_feed.py` for polars integration.

## Critical Conventions

### Timestamp Handling
- All events use Python `datetime` objects (not strings or timestamps)
- `set_backtest_start_timestamp()` / `set_backtest_end_timestamp()` accept `datetime` or ISO strings
- Price lookups via `get_price(symbol, timestamp)` find first price >= timestamp
- Strategies must manually filter events outside backtest window (see `buy_and_hold_strategy.py:27-35`)

### Portfolio State Access
- **Never directly modify** `Portfolio` state from strategies/brokers
- Read-only access patterns:
  - `portfolio.get_cash()` / `portfolio.get_position(symbol)`
  - `portfolio.get_portfolio_value(timestamp)` / `portfolio.get_buying_power(margin, timestamp)`
- State changes only via `FillEvent` → Portfolio subscription

### Component Registration Order
```python
af = AlphaFlow()
af.set_data_feed(...)     # Sets data source
af.add_equity("SYMBOL")   # Builds universe
af.add_strategy(...)      # Subscribes strategy to EventBus
af.set_broker(...)        # Subscribes broker to EventBus
af.add_analyzer(...)      # Subscribes analyzer to EventBus
af.set_cash(100000)       # Initializes portfolio
af.run()                  # Runs backtest
```

## Development Workflow

### Running Tests
```bash
pytest alphaflow/tests/
```
Tests use absolute paths - see `tests/test_alpha_flow.py` for hardcoded data file paths.

### Dependencies
- Managed via `pyproject.toml` with hatchling build system
- Core: polars, httpx, python-dotenv, seaborn
- Python >=3.10 (uses `from __future__ import annotations` for type hints)
- No lockfile in repo (uses `uv.lock` locally)

### Running Examples
```bash
python -m alphaflow.examples.sample_strategies
```
Examples require Alpha Vantage API key in environment. See `examples/sample_strategies.py`.

## Common Pitfalls

1. **Event Ordering:** DataFeeds must yield events sorted by timestamp or backtest logic breaks
2. **Short Selling:** `SimpleBroker` does NOT support shorts - sell orders validated against position size
3. **Data Loading:** All symbols in universe loaded before backtest starts (stored in `_data` dict)
4. **Price Access:** `get_price()` raises `ValueError` if no data exists after requested timestamp
5. **Margin Math:** Buying power = `portfolio_value * margin - positions_value` (see `brokers/simple_broker.py:50`)

## Project-Specific Idioms

- **Generator-based DataFeeds:** Use `yield` not `return` for memory efficiency with large datasets
- **Enum Topics:** All pub-sub uses `Topic` enum from `enums.py`, not string keys
- **Frozen Events:** Events are immutable - create new instances for modifications
- **Symbol Filtering:** Components filter by `event.symbol` in `read_event()`, not at EventBus level
- **Benchmark Tracking:** Set via `set_benchmark(symbol)` - automatically added to universe and loaded

## File Structure Conventions
- Base interfaces: `alphaflow/__init__.py`
- Implementations: `alphaflow/{strategies,brokers,data_feeds,analyzers}/`
- Events: `alphaflow/events/` (all inherit from `Event` base class)
- Tests use `pytest` with relative paths to test data files
