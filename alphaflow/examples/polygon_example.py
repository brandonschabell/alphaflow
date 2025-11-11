"""Example usage of Polygon.io data feed with AlphaFlow."""

import os
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from alphaflow import AlphaFlow
from alphaflow.analyzers import DefaultAnalyzer
from alphaflow.brokers import SimpleBroker
from alphaflow.commission_models import PerShareCommissionModel
from alphaflow.data_feeds import PolygonDataFeed
from alphaflow.slippage_models import FixedSlippageModel
from alphaflow.strategies import BuyAndHoldStrategy

# Make sure you have POLYGON_API_KEY environment variable set
# Get a free API key at https://polygon.io


def main() -> None:
    """Run a simple buy-and-hold backtest using Polygon.io data."""
    # Initialize AlphaFlow
    af = AlphaFlow()

    # Set up Polygon data feed
    # Free tier supports daily bars, paid tiers support intraday
    polygon_feed = PolygonDataFeed(
        timeframe="day",  # 'minute', 'hour', 'day', 'week', 'month'
        multiplier=1,  # e.g., 5 for 5-minute bars
    )
    af.set_data_feed(polygon_feed)

    # Add equities
    af.add_equity("AAPL")
    af.add_equity("MSFT")

    # Set benchmark
    af.set_benchmark("SPY")

    # Add strategy
    af.add_strategy(
        BuyAndHoldStrategy(
            symbol="AAPL",
            target_weight=0.5,
        )
    )
    af.add_strategy(
        BuyAndHoldStrategy(
            symbol="MSFT",
            target_weight=0.5,
        )
    )

    # Add broker
    af.set_broker(
        SimpleBroker(
            slippage_model=FixedSlippageModel(slippage_bps=5),
            commission_model=PerShareCommissionModel(commission_per_share=0.0035, min_commission=1.0),
        )
    )

    # Add analyzer
    af.add_analyzer(DefaultAnalyzer(plot_path=Path("polygon_backtest.png"), plot_title="Polygon.io Backtest"))

    # Set initial capital
    af.set_cash(100000)

    # Set backtest period
    af.set_backtest_start_timestamp(datetime(2023, 1, 1))
    af.set_backtest_end_timestamp(datetime(2024, 6, 1))

    # Run backtest
    print("Running backtest with Polygon.io data...")
    af.run()

    print("\nBacktest complete!")


if __name__ == "__main__":
    # Load environment variables from .env file
    load_dotenv()

    # Check if API key is set
    if not os.getenv("POLYGON_API_KEY"):
        print("ERROR: POLYGON_API_KEY environment variable not set")
        print("Get a free API key at https://polygon.io")
        print("\nSet it with:")
        print("  export POLYGON_API_KEY='your_key_here'")
        print("\nOr add it to a .env file in the project root:")
        print("  POLYGON_API_KEY=your_key_here")
        exit(1)

    main()
