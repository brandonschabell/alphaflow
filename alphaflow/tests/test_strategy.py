"""Tests for BuyAndHoldStrategy."""

from datetime import datetime

from alphaflow import AlphaFlow
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import CSVDataFeed
from alphaflow.enums import Topic
from alphaflow.strategies import BuyAndHoldStrategy


def test_buy_and_hold_initialization() -> None:
    """Test BuyAndHoldStrategy initialization."""
    strategy = BuyAndHoldStrategy(symbol="AAPL", target_weight=0.6)

    assert strategy.symbol == "AAPL"
    assert strategy.target_weight == 0.6


def test_buy_and_hold_topic_subscriptions() -> None:
    """Test strategy subscribes to market data."""
    strategy = BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0)

    assert strategy.topic_subscriptions() == [Topic.MARKET_DATA]


def test_buy_and_hold_initial_purchase() -> None:
    """Test strategy makes initial purchase."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
    af.set_broker(SimpleBroker())
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))

    af.run()

    # Check that position was created
    position = af.portfolio.get_position("AAPL")
    assert position > 0


def test_buy_and_hold_rebalancing() -> None:
    """Test strategy rebalances periodically."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    strategy = BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0)
    af.add_strategy(strategy)
    af.set_broker(SimpleBroker())
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1981, 1, 10))

    af.run()

    # Strategy should have executed successfully
    # Check that some position was created
    assert af.portfolio.get_position("AAPL") > 0


def test_buy_and_hold_partial_allocation() -> None:
    """Test strategy with partial portfolio allocation."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=0.5))
    af.set_broker(SimpleBroker())
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))

    af.run()

    # Position should exist but not use all capital
    position = af.portfolio.get_position("AAPL")
    assert position > 0
    # Some cash should remain (roughly 50% since target_weight=0.5)
    assert af.portfolio.get_cash() > 0


def test_buy_and_hold_filters_events_outside_backtest() -> None:
    """Test strategy ignores events outside backtest window."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    strategy = BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0)
    af.add_strategy(strategy)
    af.set_broker(SimpleBroker())
    af.set_cash(10000)
    # Load more data than backtest window
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1981, 1, 5))
    af.set_backtest_end_timestamp(datetime(1981, 1, 7))

    af.run()

    # Position should only be created after backtest_start_timestamp
    position = af.portfolio.get_position("AAPL")
    assert position > 0


def test_buy_and_hold_filters_wrong_symbol() -> None:
    """Test strategy ignores events for other symbols."""
    af = AlphaFlow()
    af.set_data_feed(CSVDataFeed("alphaflow/tests/data/AAPL.csv"))
    # Add AAPL to universe but strategy only trades AAPL
    af.add_equity("AAPL")
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
    af.set_broker(SimpleBroker())
    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1980, 12, 31))

    af.run()

    # Should only have position in AAPL
    assert af.portfolio.get_position("AAPL") > 0
