# Database Testing Infrastructure - Quick Start Guide

This guide will help you get started with the database testing infrastructure in AlphaFlow.

## Installation

Install the required dependencies:

```bash
pip install -e ".[dev]"
```

This installs:
- `sqlalchemy` - Database ORM and abstraction layer
- `factory-boy` - Test data factory library

## Your First Database Test

Create a test file `test_my_feature.py`:

```python
from datetime import UTC, datetime
from alphaflow.database.models import MarketDataModel

def test_create_market_data(db_session):
    """Test creating market data."""
    # Create a record
    market_data = MarketDataModel(
        timestamp=datetime.now(UTC),
        symbol="AAPL",
        open=150.0,
        high=155.0,
        low=148.0,
        close=153.0,
        volume=50000000.0,
    )
    
    # Save it
    db_session.add(market_data)
    db_session.commit()
    
    # Verify
    assert market_data.id is not None
    assert market_data.symbol == "AAPL"
    
    # Changes automatically rolled back after test!
```

Run the test:

```bash
pytest alphaflow/tests/test_my_feature.py -v
```

## Using Test Data Factories

Factories make it easy to generate test data:

```python
from alphaflow.tests.factories import MarketDataFactory

def test_with_factory(db_session):
    """Test using factory."""
    # Set session for factory
    MarketDataFactory._meta.sqlalchemy_session = db_session
    
    # Create with defaults
    data1 = MarketDataFactory()
    
    # Create with custom values
    data2 = MarketDataFactory(symbol="AAPL", close=150.0)
    
    # Create multiple at once
    data_list = MarketDataFactory.create_batch(10, symbol="GOOGL")
    
    assert len(data_list) == 10
```

## Key Features

### ✅ Automatic Transaction Rollback

Each test runs in its own transaction that's automatically rolled back:

```python
def test_first(db_session):
    market_data = MarketDataModel(...)
    db_session.add(market_data)
    db_session.commit()
    # ← Rollback happens here

def test_second(db_session):
    # Previous test's data is gone!
    # Fresh, isolated test environment
```

### ✅ In-Memory SQLite for Speed

Tests use an in-memory SQLite database that's super fast and requires no setup.

### ✅ Ready for CI/CD

Works out of the box in GitHub Actions and other CI environments.

## Available Fixtures

### `db_session`

Use this in most tests. Provides automatic transaction rollback:

```python
def test_example(db_session):
    # Your test code
    pass
```

### `test_engine`

Use when you need direct engine access:

```python
def test_engine_example(test_engine):
    connection = test_engine.connect()
    # ...
```

### `db_session_no_rollback`

Use when testing transaction behavior itself:

```python
def test_transaction_behavior(db_session_no_rollback):
    # Test commits/rollbacks explicitly
    pass
```

## Example Models

Three example models are provided:

- `MarketDataModel` - Store OHLCV market data
- `StrategyRunModel` - Track backtest runs and results
- `TradeModel` - Store individual trades

See `alphaflow/database/models.py` for details.

## Running Examples

Run the complete example:

```bash
python -m alphaflow.examples.database_example
```

## Common Patterns

### Pattern 1: Test CRUD Operations

```python
def test_create_and_query(db_session):
    # Create
    obj = MyModel(name="test")
    db_session.add(obj)
    db_session.commit()
    
    # Query
    result = db_session.execute(
        select(MyModel).where(MyModel.name == "test")
    ).scalar_one()
    
    # Update
    result.name = "updated"
    db_session.commit()
    
    # Delete
    db_session.delete(result)
    db_session.commit()
```

### Pattern 2: Test with Related Objects

```python
def test_relationships(db_session):
    StrategyRunFactory._meta.sqlalchemy_session = db_session
    TradeFactory._meta.sqlalchemy_session = db_session
    
    # Create parent
    run = StrategyRunFactory()
    
    # Create children
    trades = TradeFactory.create_batch(3, strategy_run_id=run.id)
    
    # Query relationship
    results = db_session.execute(
        select(TradeModel).where(TradeModel.strategy_run_id == run.id)
    ).scalars().all()
    
    assert len(results) == 3
```

### Pattern 3: Test Time-Based Queries

```python
def test_time_range(db_session):
    base_time = datetime.now(UTC)
    
    # Create historical data
    for days_ago in range(10):
        MarketDataFactory(
            timestamp=base_time - timedelta(days=days_ago),
            symbol="AAPL",
        )
    
    # Query last 5 days
    cutoff = base_time - timedelta(days=5)
    results = db_session.execute(
        select(MarketDataModel)
        .where(MarketDataModel.timestamp >= cutoff)
    ).scalars().all()
    
    assert len(results) <= 6  # Today + 5 days back
```

## Next Steps

- Read the comprehensive documentation: `alphaflow/database/README.md`
- Check out all tests: `alphaflow/tests/test_database.py`
- Review example models: `alphaflow/database/models.py`
- Run the examples: `python -m alphaflow.examples.database_example`

## Getting Help

If you encounter issues:

1. Check the full documentation in `alphaflow/database/README.md`
2. Review the test examples in `alphaflow/tests/test_database.py`
3. Run the example script to verify setup

## Local Development (macOS)

Everything works out of the box on macOS! SQLite is built-in to Python.

```bash
# Install dependencies
pip install -e ".[dev]"

# Run tests
pytest alphaflow/tests/test_database.py -v

# Run examples
python -m alphaflow.examples.database_example
```

## CI/CD (GitHub Actions)

The infrastructure works in CI without additional configuration.

Example workflow snippet:

```yaml
- name: Install dependencies
  run: pip install -e ".[dev]"

- name: Run tests
  run: pytest alphaflow/tests/
```

---

**Happy Testing! 🚀**
