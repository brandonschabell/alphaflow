"""Tests for AlphaFlow core functionality."""

import logging
from datetime import datetime

import pytest

from alphaflow import AlphaFlow
from alphaflow.analyzers import DefaultAnalyzer
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import CSVDataFeed
from alphaflow.strategies import BuyAndHoldStrategy


def test_alphaflow_initialization() -> None:
    """Test AlphaFlow is properly initialized."""
    af = AlphaFlow()

    assert af.event_bus is not None
    assert af.portfolio is not None
    assert af.strategies == []
    assert af.analyzers == []
    assert af.universe == set()
    assert af.data_feed is None
    assert af.broker is None
    assert af.benchmark is None


def test_alphaflow_set_benchmark() -> None:
    """Test setting a benchmark symbol."""
    af = AlphaFlow()
    af.set_benchmark("SPY")

    assert af.benchmark == "SPY"
    assert "SPY" in af.universe


def test_alphaflow_add_equity() -> None:
    """Test adding equity symbols to universe."""
    af = AlphaFlow()

    af.add_equity("AAPL")
    assert "AAPL" in af.universe

    af.add_equity("GOOGL")
    assert "GOOGL" in af.universe
    assert len(af.universe) == 2


def test_alphaflow_set_data_feed() -> None:
    """Test setting the data feed."""
    af = AlphaFlow()
    data_feed = CSVDataFeed("alphaflow/tests/data/AAPL.csv")

    af.set_data_feed(data_feed)

    assert af.data_feed is data_feed
    assert data_feed._alpha_flow is af


def test_alphaflow_add_strategy() -> None:
    """Test adding strategies."""
    af = AlphaFlow()
    strategy = BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0)

    af.add_strategy(strategy)

    assert len(af.strategies) == 1
    assert strategy in af.strategies
    assert strategy._alpha_flow is af


def test_alphaflow_add_multiple_strategies() -> None:
    """Test adding multiple strategies."""
    af = AlphaFlow()
    strategy1 = BuyAndHoldStrategy(symbol="AAPL", target_weight=0.6)
    strategy2 = BuyAndHoldStrategy(symbol="GOOGL", target_weight=0.4)

    af.add_strategy(strategy1)
    af.add_strategy(strategy2)

    assert len(af.strategies) == 2


def test_alphaflow_add_analyzer() -> None:
    """Test adding analyzers."""
    af = AlphaFlow()
    analyzer = DefaultAnalyzer()

    af.add_analyzer(analyzer)

    assert len(af.analyzers) == 1
    assert analyzer in af.analyzers
    assert analyzer._alpha_flow is af


def test_alphaflow_set_broker() -> None:
    """Test setting the broker."""
    af = AlphaFlow()
    broker = SimpleBroker()

    af.set_broker(broker)

    assert af.broker is broker
    assert broker._alpha_flow is af


def test_alphaflow_set_cash() -> None:
    """Test setting initial cash."""
    af = AlphaFlow()

    af.set_cash(50000.0)

    assert af.portfolio.get_cash() == 50000.0


def test_alphaflow_set_data_start_timestamp_datetime() -> None:
    """Test setting data start timestamp with datetime."""
    af = AlphaFlow()
    timestamp = datetime(2020, 1, 1)

    af.set_data_start_timestamp(timestamp)

    assert af.data_start_timestamp == timestamp


def test_alphaflow_set_data_start_timestamp_string() -> None:
    """Test setting data start timestamp with ISO string."""
    af = AlphaFlow()

    af.set_data_start_timestamp("2020-01-01")

    assert af.data_start_timestamp == datetime(2020, 1, 1)


def test_alphaflow_set_backtest_start_timestamp_datetime() -> None:
    """Test setting backtest start timestamp with datetime."""
    af = AlphaFlow()
    timestamp = datetime(2020, 1, 15)

    af.set_backtest_start_timestamp(timestamp)

    assert af.backtest_start_timestamp == timestamp


def test_alphaflow_set_backtest_start_timestamp_string() -> None:
    """Test setting backtest start timestamp with ISO string."""
    af = AlphaFlow()

    af.set_backtest_start_timestamp("2020-01-15")

    assert af.backtest_start_timestamp == datetime(2020, 1, 15)


def test_alphaflow_set_backtest_end_timestamp_datetime() -> None:
    """Test setting backtest end timestamp with datetime."""
    af = AlphaFlow()
    timestamp = datetime(2021, 1, 1)

    af.set_backtest_end_timestamp(timestamp)

    assert af.backtest_end_timestamp == timestamp


def test_alphaflow_set_backtest_end_timestamp_string() -> None:
    """Test setting backtest end timestamp with ISO string."""
    af = AlphaFlow()

    af.set_backtest_end_timestamp("2021-01-01")

    assert af.backtest_end_timestamp == datetime(2021, 1, 1)


def test_alphaflow_get_timestamps() -> None:
    """Test getting all timestamps from loaded data."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))
    af.run()

    timestamps = af.get_timestamps()

    assert len(timestamps) > 0
    assert all(isinstance(ts, datetime) for ts in timestamps)
    # Timestamps should be sorted
    assert timestamps == sorted(timestamps)


def test_alphaflow_get_price() -> None:
    """Test getting price for a symbol at a timestamp."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    price = af.get_price("AAPL", datetime(1980, 12, 29))

    assert isinstance(price, float)
    assert price > 0


def test_alphaflow_get_price_raises_error_for_missing_data() -> None:
    """Test get_price raises error when no data exists after timestamp."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))
    af.run()

    # Try to get price for a date way in the future
    with pytest.raises(ValueError, match="No price data for symbol"):
        af.get_price("AAPL", datetime(2030, 1, 1))


def test_alphaflow_on_missing_price_warn(caplog: pytest.LogCaptureFixture) -> None:
    """Test that on_missing_price='warn' logs a warning and returns 0.0."""
    af = AlphaFlow(on_missing_price="warn")
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))
    af.run()

    with caplog.at_level(logging.WARNING):
        price = af.get_price("AAPL", datetime(2030, 1, 1))

    assert price == 0.0
    assert "No price data for symbol AAPL" in caplog.text


def test_alphaflow_on_missing_price_ignore() -> None:
    """Test that on_missing_price='ignore' silently returns 0.0."""
    af = AlphaFlow(on_missing_price="ignore")
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))
    af.run()

    price = af.get_price("AAPL", datetime(2030, 1, 1))
    assert price == 0.0


def test_alphaflow_on_missing_price_invalid_value() -> None:
    """Test that invalid on_missing_price value raises ValueError."""
    with pytest.raises(ValueError, match="on_missing_price must be 'raise', 'warn', or 'ignore'"):
        AlphaFlow(on_missing_price="invalid")


def test_alphaflow_run_raises_error_without_data_feed() -> None:
    """Test run raises error when data feed is not set."""
    af = AlphaFlow()
    af.add_equity("AAPL")
    af.set_cash(10000)

    with pytest.raises(ValueError, match="Data feed must be set"):
        af.run()


def test_alphaflow_run_raises_error_for_live_trading() -> None:
    """Test run raises error for live trading (not implemented)."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)

    with pytest.raises(NotImplementedError):
        af.run(is_backtest=False)


def test_alphaflow_complete_backtest_flow() -> None:
    """Test complete backtest flow with all components."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_benchmark("AAPL")
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
    af.set_broker(SimpleBroker())
    af.add_analyzer(DefaultAnalyzer())
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1981, 1, 5))

    # Should run without errors
    af.run()

    # Check that data was loaded
    assert len(af._data) > 0
    assert "AAPL" in af._data

    # Check that portfolio has positions
    final_timestamp = af.get_timestamps()[-1]
    portfolio_value = af.portfolio.get_portfolio_value(final_timestamp)
    assert portfolio_value > 0


def test_simple_backtest() -> None:
    """Test a simple buy-and-hold backtest with AAPL."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
    af.set_broker(SimpleBroker())
    af.set_cash(1000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1981, 1, 5))
    af.run()
    final_timestamp = af.get_timestamps()[-1]
    assert af.portfolio.get_portfolio_value(final_timestamp) == pytest.approx(937.50, abs=0.01)
