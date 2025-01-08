from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from alphaflow import Analyzer
from alphaflow.enums import Topic
from alphaflow.events import FillEvent, MarketDataEvent


class DefaultAnalyzer(Analyzer):
    def __init__(
        self,
        plot_path: Path | None = None,
        plot_title: str = "Portfolio Value Over Time",
    ) -> None:
        self._plot_path = plot_path
        self._values: dict[datetime, float] = {}
        self._plot_title = plot_title

    def topic_subscriptions(self):
        return [Topic.FILL, Topic.MARKET_DATA]

    def read_event(self, event: FillEvent | MarketDataEvent):
        self._values[event.timestamp] = self._alpha_flow.portfolio.get_portfolio_value(
            event.timestamp
        )

    def run(self):
        timestamps, portfolio_values = zip(*self._values.items())

        for metric, value in self.calculate_all_metrics(
            timestamps, portfolio_values
        ).items():
            print(f"{metric}: {value}")

        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x=timestamps, y=portfolio_values, label="Portfolio Value", ax=ax)
        ax.set_title(self._plot_title)
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Portfolio Value")

        drawdown_str = (
            f"Max Drawdown: {100 * self.calculate_max_drawdown(portfolio_values):.2f}%"
        )
        sharpe_str = f"Sharpe Ratio: {self.calculate_sharpe_ratio(timestamps, portfolio_values):.4f}"
        sortino_str = f"Sortino Ratio: {self.calculate_sortino_ratio(timestamps, portfolio_values):.4f}"
        anualized_return_str = f"Anualized Return: {100 * self.calculate_anualized_return(timestamps, portfolio_values):.2f}%"

        benchmark_values = self._alpha_flow.portfolio.get_benchmark_values()
        if benchmark_values:
            benchmark_timestamps, benchmark_values = zip(*benchmark_values.items())
            benchmark_multiple = portfolio_values[0] / benchmark_values[0]
            benchmark_values = [
                value * benchmark_multiple for value in benchmark_values
            ]
            sns.lineplot(
                x=benchmark_timestamps,
                y=benchmark_values,
                label="Benchmark Value",
                ax=ax,
                color="orange",
            )

            benchmark_drawdown = self.calculate_max_drawdown(benchmark_values)
            benchmark_sharpe = self.calculate_sharpe_ratio(
                benchmark_timestamps, benchmark_values
            )
            benchmark_sortino = self.calculate_sortino_ratio(
                benchmark_timestamps, benchmark_values
            )
            benchmark_anualized_return = self.calculate_anualized_return(
                benchmark_timestamps, benchmark_values
            )
            drawdown_str += f" (Benchmark: {100 * benchmark_drawdown:.2f}%)"
            sharpe_str += f" (Benchmark: {benchmark_sharpe:.4f})"
            sortino_str += f" (Benchmark: {benchmark_sortino:.4f})"
            anualized_return_str += (
                f" (Benchmark: {100 * benchmark_anualized_return:.2f}%)"
            )

        ax.legend()

        metrics_text = "\n".join(
            [drawdown_str, sharpe_str, sortino_str, anualized_return_str]
        )
        plt.text(
            0.05,
            0.95,
            metrics_text,
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment="top",
        )

        fig.tight_layout()
        if self._plot_path:
            fig.savefig(self._plot_path)

    def calculate_max_drawdown(self, portfolio_values: list[float]) -> float:
        max_drawdown = 0
        peak = portfolio_values[0]
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown

    def calculate_sharpe_ratio(
        self, timestamps: list[datetime], portfolio_values: list[float]
    ) -> float:
        returns = [
            portfolio_values[i] / portfolio_values[i - 1] - 1
            for i in range(1, len(portfolio_values))
        ]
        mean_return = sum(returns) / len(returns)
        std_return = (
            sum((ret - mean_return) ** 2 for ret in returns) / len(returns)
        ) ** 0.5
        values_per_year = (
            len(portfolio_values) / (timestamps[-1] - timestamps[0]).days * 365
        )
        if std_return == 0:
            return 0
        return mean_return * values_per_year**0.5 / std_return

    def calculate_sortino_ratio(
        self, timestamps: list[datetime], portfolio_values: list[float]
    ) -> float:
        returns = [
            portfolio_values[i] / portfolio_values[i - 1] - 1
            for i in range(1, len(portfolio_values))
        ]
        downside_returns = [min(ret, 0) for ret in returns]
        mean_return = sum(returns) / len(returns)
        downside_deviation = (
            sum((ret - mean_return) ** 2 for ret in downside_returns)
            / len(downside_returns)
        ) ** 0.5
        values_per_year = (
            len(portfolio_values) / (timestamps[-1] - timestamps[0]).days * 365
        )
        if downside_deviation == 0:
            return 0
        return mean_return * values_per_year**0.5 / downside_deviation

    def calculate_anualized_return(
        self, timestamps: list[datetime], portfolio_values: list[float]
    ) -> float:
        return (portfolio_values[-1] / portfolio_values[0]) ** (
            365 / (timestamps[-1] - timestamps[0]).days
        ) - 1

    def calculate_total_return(self, portfolio_values: list[float]) -> float:
        return portfolio_values[-1] / portfolio_values[0] - 1

    def calculate_all_metrics(
        self, timestamps: list[datetime], portfolio_values: list[float]
    ) -> dict[str, float]:
        return {
            "Max Drawdown": self.calculate_max_drawdown(portfolio_values),
            "Sharpe Ratio": self.calculate_sharpe_ratio(timestamps, portfolio_values),
            "Sortino Ratio": self.calculate_sortino_ratio(timestamps, portfolio_values),
            "Anualized Return": self.calculate_anualized_return(
                timestamps, portfolio_values
            ),
            "Total Return": self.calculate_total_return(portfolio_values),
        }
