"""Tests for the Portfolio class."""

from datetime import datetime

import pytest

from alphaflow import AlphaFlow
from alphaflow.data_feeds import PolarsDataFeed
from alphaflow.events import FillEvent
from alphaflow.events.market_data_event import MarketDataEvent


def test_portfolio_initialization() -> None:
    """Test portfolio is properly initialized."""
    af = AlphaFlow()
    portfolio = af.portfolio

    assert portfolio.get_cash() == 0.0
    assert portfolio.positions == {}


def test_portfolio_set_and_get_cash() -> None:
    """Test setting and getting cash balance."""
    af = AlphaFlow()
    portfolio = af.portfolio

    portfolio.set_cash(10000.0)
    assert portfolio.get_cash() == 10000.0

    portfolio.set_cash(50000.0)
    assert portfolio.get_cash() == 50000.0


def test_portfolio_update_cash() -> None:
    """Test updating cash balance."""
    af = AlphaFlow()
    portfolio = af.portfolio
    portfolio.set_cash(10000.0)

    portfolio.update_cash(500.0)
    assert portfolio.get_cash() == 10500.0

    portfolio.update_cash(-1500.0)
    assert portfolio.get_cash() == 9000.0


def test_portfolio_update_position() -> None:
    """Test updating position quantities."""
    af = AlphaFlow()
    portfolio = af.portfolio

    # Initial position should be 0
    assert portfolio.get_position("AAPL") == 0.0

    # Add shares
    portfolio.update_position("AAPL", 10.0)
    assert portfolio.get_position("AAPL") == 10.0

    # Add more shares
    portfolio.update_position("AAPL", 5.0)
    assert portfolio.get_position("AAPL") == 15.0

    # Remove shares
    portfolio.update_position("AAPL", -7.0)
    assert portfolio.get_position("AAPL") == 8.0


def test_portfolio_get_position_value() -> None:
    """Test calculating position value at a timestamp."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))

    # Load data
    af.run()

    portfolio = af.portfolio
    portfolio.update_position("AAPL", 100.0)

    timestamp = datetime(1980, 12, 29)
    position_value = portfolio.get_position_value("AAPL", timestamp)

    # Price on 1980-12-29 is $0.160714, so 100 shares = $16.0714
    assert position_value == pytest.approx(16.0714, abs=0.01)


def test_portfolio_get_positions_value() -> None:
    """Test calculating total positions value."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    portfolio = af.portfolio
    portfolio.update_position("AAPL", 50.0)

    timestamp = datetime(1980, 12, 29)
    positions_value = portfolio.get_positions_value(timestamp)

    # 50 shares at $0.160714 = $8.0357
    assert positions_value == pytest.approx(8.0357, abs=0.01)


def test_portfolio_get_portfolio_value() -> None:
    """Test calculating total portfolio value (cash + positions)."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(5000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    portfolio = af.portfolio
    portfolio.set_cash(5000.0)
    portfolio.update_position("AAPL", 50.0)

    timestamp = datetime(1980, 12, 29)
    portfolio_value = portfolio.get_portfolio_value(timestamp)

    # Cash: $5000 + 50 shares at $0.160714 = $5008.0357
    assert portfolio_value == pytest.approx(5008.0357, abs=0.01)


def test_portfolio_get_buying_power() -> None:
    """Test calculating buying power with margin."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.run()

    portfolio = af.portfolio
    portfolio.set_cash(10000.0)
    portfolio.update_position("AAPL", 50.0)

    timestamp = datetime(1980, 12, 29)

    # With 1x margin (no margin)
    buying_power_1x = portfolio.get_buying_power(1.0, timestamp)
    # Portfolio value: $10008.0357, positions: $8.0357
    # Buying power = $10008.0357 * 1.0 - $8.0357 = $10000
    assert buying_power_1x == pytest.approx(10000.0, abs=0.01)

    # With 2x margin
    buying_power_2x = portfolio.get_buying_power(2.0, timestamp)
    # Buying power = $10008.0357 * 2.0 - $8.0357 = $20008.0357
    assert buying_power_2x == pytest.approx(20008.0357, abs=0.01)


def test_portfolio_get_benchmark_values_no_benchmark() -> None:
    """Test getting benchmark values when no benchmark is set."""
    af = AlphaFlow()
    portfolio = af.portfolio

    benchmark_values = portfolio.get_benchmark_values()
    assert benchmark_values == {}


def test_portfolio_get_benchmark_values_with_benchmark() -> None:
    """Test getting benchmark values when benchmark is set."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.set_benchmark("AAPL")
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))
    af.run()

    portfolio = af.portfolio
    benchmark_values = portfolio.get_benchmark_values()

    assert len(benchmark_values) > 0
    assert isinstance(list(benchmark_values.keys())[0], datetime)
    assert isinstance(list(benchmark_values.values())[0], float)


def test_portfolio_read_event_with_fill() -> None:
    """Test portfolio updates on fill events."""
    af = AlphaFlow()
    af.set_cash(10000)
    portfolio = af.portfolio

    # Create a fill event
    fill_event = FillEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        fill_price=150.0,
        fill_qty=10.0,
        commission=5.0,
    )

    # Process the event
    portfolio.read_event(fill_event)

    # Cash should be reduced by (fill_price * fill_qty) + commission
    # Cost: 150.0 * 10.0 = 1500.0
    # Commission: 5.0
    # Total: 1505.0
    # Remaining: 10000 - 1505 = 8495.0
    assert portfolio.get_cash() == pytest.approx(8495.0, abs=0.01)
    assert portfolio.get_position("AAPL") == 10.0


def test_portfolio_read_event_with_sell_and_commission() -> None:
    """Test portfolio correctly handles sell orders with commission."""
    af = AlphaFlow()
    af.set_cash(10000)
    portfolio = af.portfolio
    portfolio.update_position("AAPL", 20.0)  # Start with 20 shares

    # Create a sell fill event
    fill_event = FillEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        fill_price=150.0,
        fill_qty=-10.0,  # Negative for sell
        commission=5.0,
    )

    # Process the event
    portfolio.read_event(fill_event)

    # Cash should increase by (150.0 * 10.0) - commission
    # Revenue: 1500.0
    # Commission: 5.0
    # Net: 1495.0
    # Total: 10000 + 1495 = 11495.0
    assert portfolio.get_cash() == pytest.approx(11495.0, abs=0.01)
    assert portfolio.get_position("AAPL") == 10.0  # 20 - 10


def test_portfolio_read_event_with_non_fill() -> None:
    """Test portfolio ignores non-fill events."""
    af = AlphaFlow()
    af.set_cash(10000)
    portfolio = af.portfolio

    # Create a market data event (not a fill event)
    market_event = MarketDataEvent(
        timestamp=datetime.now(),
        symbol="AAPL",
        open=150.0,
        high=155.0,
        low=149.0,
        close=154.0,
        volume=1000000.0,
    )

    initial_cash = portfolio.get_cash()
    initial_position = portfolio.get_position("AAPL")

    # Process the event - should be ignored
    portfolio.read_event(market_event)

    # Nothing should change
    assert portfolio.get_cash() == initial_cash
    assert portfolio.get_position("AAPL") == initial_position
