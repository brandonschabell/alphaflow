import logging

from alphaflow import AlphaFlow
from alphaflow.analyzers import DefaultAnalyzer
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import FMPDataFeed
from alphaflow.strategies import BuyAndHoldStrategy


def create_analysis(title: str, file_name: str, weights: dict[str, float]) -> None:
    af = AlphaFlow()
    af.set_data_feed(FMPDataFeed())
    for symbol, weight in weights.items():
        af.add_equity(symbol)
        af.add_strategy(BuyAndHoldStrategy(symbol=symbol, target_weight=weight))
    af.set_benchmark("SPY")
    af.set_broker(SimpleBroker())
    af.add_analyzer(DefaultAnalyzer(plot_path=f"{file_name}.png", plot_title=title))
    af.set_cash(100000)
    af.run()


def main():
    create_analysis("60% SPY / 40% Bonds", "60-40", {"SPY": 0.6, "BND": 0.4})
    create_analysis("BRKB", "BRKB", {"BRK-B": 1})
    create_analysis(
        "65% BRKB / 30% Bonds / 5% Uranium",
        "BRKB-Bonds-URA",
        {"BRK-B": 0.65, "BND": 0.3, "URA": 0.05},
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
