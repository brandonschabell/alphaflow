# Database Testing Infrastructure

This directory contains the database testing infrastructure for AlphaFlow, following best practices for database integration testing.

## Overview

The database infrastructure provides:

- **SQLAlchemy ORM**: Database abstraction layer supporting SQLite, PostgreSQL, MySQL, etc.
- **Pytest Fixtures**: Reusable fixtures for database setup and teardown
- **Transaction Rollback**: Automatic test isolation with transaction rollback
- **Test Data Factories**: Easy generation of test data using factory_boy
- **Example Models**: Demonstration models for market data, trades, and strategy runs

## Quick Start

### 1. Install Dependencies

The database infrastructure requires SQLAlchemy and factory_boy:

```bash
pip install -e ".[dev]"
```

### 2. Using Database Fixtures

Import and use the `db_session` fixture in your tests:

```python
from alphaflow.database.models import MarketDataModel

def test_create_market_data(db_session):
    """Test creating market data."""
    market_data = MarketDataModel(
        timestamp=datetime.utcnow(),
        symbol="AAPL",
        open=150.0,
        high=155.0,
        low=148.0,
        close=153.0,
        volume=50000000.0,
    )
    
    db_session.add(market_data)
    db_session.commit()
    
    assert market_data.id is not None
```

### 3. Using Test Data Factories

Use factories to easily generate test data:

```python
from alphaflow.tests.factories import MarketDataFactory

def test_with_factory(db_session):
    """Test using factory."""
    # Set session for factory
    MarketDataFactory._meta.sqlalchemy_session = db_session
    
    # Create with defaults
    market_data = MarketDataFactory()
    
    # Create with custom values
    market_data = MarketDataFactory(symbol="AAPL", close=150.0)
    
    # Create multiple instances
    market_data_list = MarketDataFactory.create_batch(10, symbol="AAPL")
```

## Architecture

### Database Session Management

The `alphaflow.database.session` module provides:

- **Engine Configuration**: SQLAlchemy engine with proper settings
- **Session Factory**: SessionLocal for creating database sessions
- **init_db()**: Initialize database tables
- **get_session()**: Context manager for database sessions

```python
from alphaflow.database import init_db, get_session

# Initialize database (create tables)
init_db()

# Use session
with get_session() as session:
    # Perform database operations
    session.add(obj)
    session.commit()
```

### Database Models

Example models are provided in `alphaflow.database.models`:

- **MarketDataModel**: Store market data (OHLCV)
- **StrategyRunModel**: Store backtest run metadata and results
- **TradeModel**: Store individual trade records

```python
from alphaflow.database.models import MarketDataModel

market_data = MarketDataModel(
    timestamp=datetime.utcnow(),
    symbol="AAPL",
    open=150.0,
    high=155.0,
    low=148.0,
    close=153.0,
    volume=50000000.0,
)
```

### Pytest Fixtures

Three fixtures are available in `alphaflow.tests.fixtures`:

#### 1. test_engine (session scope)

Creates an in-memory SQLite database for the entire test session:

```python
def test_example(test_engine):
    # test_engine is shared across all tests in the session
    pass
```

#### 2. db_session (function scope)

Provides automatic transaction rollback for test isolation:

```python
def test_with_rollback(db_session):
    # Changes are automatically rolled back after test
    db_session.add(obj)
    db_session.commit()
    # ← Rollback happens here automatically
```

**How it works:**
1. Begins a database transaction
2. Begins a nested transaction (savepoint)
3. All commits only commit the savepoint, not the outer transaction
4. After test completes, the outer transaction is rolled back
5. All changes are discarded, ensuring test isolation

#### 3. db_session_no_rollback (function scope)

Session without automatic rollback for special cases:

```python
def test_without_rollback(db_session_no_rollback):
    # Changes persist in the test database
    # Useful for testing transaction behavior itself
    pass
```

### Test Data Factories

Factories use factory_boy to generate test data with sensible defaults:

```python
from alphaflow.tests.factories import (
    MarketDataFactory,
    StrategyRunFactory,
    TradeFactory,
)

# Set session once for all factories
MarketDataFactory._meta.sqlalchemy_session = db_session

# Create single instance
market_data = MarketDataFactory()

# Create with custom attributes
market_data = MarketDataFactory(symbol="AAPL", close=150.0)

# Create batch
market_data_list = MarketDataFactory.create_batch(100, symbol="AAPL")

# Create related objects
run = StrategyRunFactory()
trades = TradeFactory.create_batch(10, strategy_run_id=run.id)
```

## Test Isolation

Test isolation is achieved through transaction rollback:

1. **Each test runs in its own transaction**
2. **Changes are committed to a savepoint**, not the database
3. **After test completion, the transaction is rolled back**
4. **No data persists between tests**

Example:

```python
def test_first(db_session):
    obj = MyModel(name="test")
    db_session.add(obj)
    db_session.commit()
    # Object exists in this test
    assert db_session.query(MyModel).count() == 1
    # ← Automatic rollback happens here

def test_second(db_session):
    # Previous test's data doesn't exist
    assert db_session.query(MyModel).count() == 0
```

## Configuration

### Database URL

Configure database connection via environment variable:

```bash
# SQLite (default)
export DATABASE_URL="sqlite:///./alphaflow.db"

# PostgreSQL
export DATABASE_URL="postgresql://user:pass@localhost/dbname"

# MySQL
export DATABASE_URL="mysql://user:pass@localhost/dbname"
```

For tests, an in-memory SQLite database is used automatically.

### Test Configuration

Tests use in-memory SQLite by default (configured in fixtures).
To use a different database for tests:

```python
@pytest.fixture(scope="session")
def test_engine():
    engine = create_engine("postgresql://test:test@localhost/test_db")
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
```

## Best Practices

### 1. Use Factories for Test Data

```python
# Good: Use factories
market_data = MarketDataFactory(symbol="AAPL")

# Avoid: Manual creation for every test
market_data = MarketDataModel(
    timestamp=datetime.utcnow(),
    symbol="AAPL",
    open=150.0,
    high=155.0,
    low=148.0,
    close=153.0,
    volume=50000000.0,
)
```

### 2. Rely on Transaction Rollback

```python
# Good: Let rollback handle cleanup
def test_example(db_session):
    obj = MyModel(name="test")
    db_session.add(obj)
    db_session.commit()
    # No manual cleanup needed

# Avoid: Manual cleanup
def test_example(db_session):
    obj = MyModel(name="test")
    db_session.add(obj)
    db_session.commit()
    db_session.delete(obj)  # Unnecessary!
    db_session.commit()
```

### 3. Set Factory Session Once

```python
# Good: Set session in fixture or conftest
@pytest.fixture(autouse=True)
def setup_factories(db_session):
    MarketDataFactory._meta.sqlalchemy_session = db_session

# Avoid: Setting in every test
def test_example(db_session):
    MarketDataFactory._meta.sqlalchemy_session = db_session
    market_data = MarketDataFactory()
```

### 4. Use Appropriate Fixture Scope

```python
# Function scope (default): Isolated per test
def test_isolated(db_session):
    # Each test gets fresh session with rollback
    pass

# Session scope: Shared across tests (use sparingly)
@pytest.fixture(scope="session")
def shared_data(test_engine):
    # Data shared across all tests
    pass
```

## Running Tests

Run database tests:

```bash
# Run all database tests
pytest alphaflow/tests/test_database.py -v

# Run specific test class
pytest alphaflow/tests/test_database.py::TestDatabaseFixtures -v

# Run with SQL query output (debugging)
pytest alphaflow/tests/test_database.py -v -s
```

## Examples

See `alphaflow/tests/test_database.py` for comprehensive examples:

- Basic CRUD operations
- Transaction rollback verification
- Factory usage patterns
- Relationship handling
- Query examples

## CI/CD Integration

### Local Development (macOS)

SQLite works out of the box on macOS:

```bash
pytest alphaflow/tests/test_database.py
```

### GitHub Actions

Add to `.github/workflows/ci.yml`:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          pip install -e ".[dev]"
      - name: Run tests
        run: |
          pytest alphaflow/tests/
```

For PostgreSQL in CI:

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test_db
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
    env:
      DATABASE_URL: postgresql://postgres:postgres@localhost:5432/test_db
    steps:
      # ... rest of steps
```

## Troubleshooting

### "No such table" errors

Make sure `init_db()` is called or tables are created in fixtures:

```python
Base.metadata.create_all(bind=engine)
```

### Data persisting between tests

Check that you're using `db_session` fixture (with rollback), not `db_session_no_rollback`.

### Factory not creating objects

Ensure session is set on factory:

```python
MarketDataFactory._meta.sqlalchemy_session = db_session
```

### Import errors

Make sure all packages are installed:

```bash
pip install -e ".[dev]"
```

## Further Reading

- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [factory_boy Documentation](https://factoryboy.readthedocs.io/)
- [pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Database Testing Best Practices](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites)
