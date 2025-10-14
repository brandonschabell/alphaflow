"""Example backtests demonstrating various portfolio allocations."""

import logging
from pathlib import Path

from alphaflow import AlphaFlow
from alphaflow.analyzers import DefaultAnalyzer
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import AlphaVantageFeed
from alphaflow.strategies import BuyAndHoldStrategy


def create_analysis(title: str, file_name: str, weights: dict[str, float]) -> None:
    """Run a backtest with the given portfolio weights and generate analysis.

    Args:
        title: Title for the analysis plot.
        file_name: Base filename for saving the plot.
        weights: Dictionary mapping symbols to their target portfolio weights.

    """
    af = AlphaFlow()
    af.set_data_feed(AlphaVantageFeed())
    af.set_backtest_start_timestamp("2007-06-01")
    for symbol, weight in weights.items():
        af.add_equity(symbol)
        af.add_strategy(BuyAndHoldStrategy(symbol=symbol, target_weight=weight, share_quantization=1))
    af.set_benchmark("SPY")
    af.set_broker(SimpleBroker())
    af.add_analyzer(DefaultAnalyzer(plot_path=Path(f"{file_name}_av.png"), plot_title=title))
    af.set_cash(100000)
    af.run()


def main() -> None:
    """Run multiple backtests with different portfolio allocations."""
    create_analysis("60% SPY / 40% Bonds", "60-40", {"SPY": 0.6, "BND": 0.4})
    create_analysis("75/25", "75-25 Split", {"SPY": 0.75, "BND": 0.25})
    create_analysis("BRKB", "BRKB", {"BRK-B": 1})
    create_analysis(
        "65% BRKB / 30% Bonds / 5% Uranium",
        "BRKB-Bonds-URA",
        {"BRK-B": 0.65, "BND": 0.3, "URA": 0.05},
    )
    create_analysis(
        "Optimized",
        "Optimized",
        {"BRK-B": 0.31995, "QYLD": 0.19173, "GLD": 0.38832, "URA": 0.05, "SHLD": 0.05},
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
