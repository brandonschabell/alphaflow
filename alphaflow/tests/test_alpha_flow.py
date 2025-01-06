from datetime import datetime
import logging

import pytest

from alphaflow import AlphaFlow
from alphaflow.brokers.simple_broker import SimpleBroker
from alphaflow.data_feeds.csv_data_feed import CSVDataFeed
from alphaflow.strategies.buy_and_hold_strategy import BuyAndHoldStrategy


def test_simple_backtest():
    logging.basicConfig(level=logging.DEBUG)

    af = AlphaFlow()
    af.add_data_feed(
        CSVDataFeed(
            "/Users/brandonschabell/Desktop/git/alphaflow/alphaflow/tests/data/AAPL.csv",
            symbol_override="AAPL",
        )
    )
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
    af.set_broker(SimpleBroker())
    af.set_cash(1000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1981, 1, 5))
    af.run()
    final_timestamp = af.get_timestamps()[-1]
    assert af.portfolio.get_portfolio_value(final_timestamp) == pytest.approx(
        937.50, abs=0.01
    )
