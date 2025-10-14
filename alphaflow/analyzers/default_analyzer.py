"""Default analyzer implementation for portfolio performance analysis."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from alphaflow import Analyzer
from alphaflow.enums import Topic
from alphaflow.events import FillEvent
from alphaflow.events.event import Event


class DefaultAnalyzer(Analyzer):
    """Default analyzer for computing performance metrics and visualizations.

    Tracks portfolio value over time and generates comprehensive performance
    metrics including Sharpe ratio, Sortino ratio, maximum drawdown, and returns.
    """

    def __init__(
        self,
        plot_path: Path | None = None,
        plot_title: str = "Portfolio Value Over Time",
    ) -> None:
        """Initialize the default analyzer.

        Args:
            plot_path: Optional path to save the performance plot.
            plot_title: Title for the performance plot.

        """
        self._plot_path = plot_path
        self._values: dict[datetime, float] = {}
        self._plot_title = plot_title
        self._fills: dict[datetime, FillEvent] = {}

    def topic_subscriptions(self) -> list[Topic]:
        """Return the topics this analyzer subscribes to.

        Returns:
            List of topics to monitor (FILL and MARKET_DATA).

        """
        return [Topic.FILL, Topic.MARKET_DATA]

    def read_event(self, event: Event) -> None:
        """Process events and record portfolio values.

        Args:
            event: Either a FillEvent or MarketDataEvent to process.

        """
        self._values[event.timestamp] = self._alpha_flow.portfolio.get_portfolio_value(event.timestamp)
        if isinstance(event, FillEvent):
            self._fills[event.timestamp] = event

    def run(self) -> None:
        """Run the analysis after backtest completion.

        Computes all performance metrics, prints them to console, and generates
        a visualization plot if plot_path was specified.

        """
        timestamps_tuple, portfolio_values_tuple = zip(*self._values.items(), strict=False)
        timestamps = list(timestamps_tuple)
        portfolio_values = list(portfolio_values_tuple)

        for metric, value in self.calculate_all_metrics(timestamps, portfolio_values).items():
            print(f"{metric}: {value}")

        fig, ax = plt.subplots(figsize=(12, 6))
        sns.lineplot(x=timestamps, y=portfolio_values, label="Portfolio Value", ax=ax)
        ax.set_title(self._plot_title)
        ax.set_xlabel("Timestamp")
        ax.set_ylabel("Portfolio Value")

        drawdown_str = f"Max Drawdown: {100 * self.calculate_max_drawdown(portfolio_values):.2f}%"
        sharpe_str = f"Sharpe Ratio: {self.calculate_sharpe_ratio(timestamps, portfolio_values):.4f}"
        sortino_str = f"Sortino Ratio: {self.calculate_sortino_ratio(timestamps, portfolio_values):.4f}"
        annualized_return_str = (
            f"Annualized Return: {100 * self.calculate_annualized_return(timestamps, portfolio_values):.2f}%"
        )

        benchmark_values_dict = self._alpha_flow.portfolio.get_benchmark_values()
        if benchmark_values_dict:
            benchmark_timestamps_tuple, benchmark_values_tuple = zip(*benchmark_values_dict.items(), strict=False)
            benchmark_timestamps = list(benchmark_timestamps_tuple)
            benchmark_values = list(benchmark_values_tuple)
            benchmark_multiple = portfolio_values[0] / benchmark_values[0]
            benchmark_values = [value * benchmark_multiple for value in benchmark_values]
            sns.lineplot(
                x=benchmark_timestamps,
                y=benchmark_values,
                label="Benchmark Value",
                ax=ax,
                color="orange",
            )

            benchmark_drawdown = self.calculate_max_drawdown(benchmark_values)
            benchmark_sharpe = self.calculate_sharpe_ratio(benchmark_timestamps, benchmark_values)
            benchmark_sortino = self.calculate_sortino_ratio(benchmark_timestamps, benchmark_values)
            benchmark_annualized_return = self.calculate_annualized_return(benchmark_timestamps, benchmark_values)
            drawdown_str += f" (Benchmark: {100 * benchmark_drawdown:.2f}%)"
            sharpe_str += f" (Benchmark: {benchmark_sharpe:.4f})"
            sortino_str += f" (Benchmark: {benchmark_sortino:.4f})"
            annualized_return_str += f" (Benchmark: {100 * benchmark_annualized_return:.2f}%)"

        ax.legend()

        metrics_text = "\n".join([drawdown_str, sharpe_str, sortino_str, annualized_return_str])
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
        """Calculate the maximum drawdown from peak to trough.

        Args:
            portfolio_values: List of portfolio values over time.

        Returns:
            Maximum drawdown as a decimal (e.g., 0.15 for 15% drawdown).

        """
        max_drawdown: float = 0.0
        peak: float = portfolio_values[0]
        for value in portfolio_values:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        return max_drawdown

    def calculate_sharpe_ratio(self, timestamps: list[datetime], portfolio_values: list[float]) -> float:
        """Calculate the Sharpe ratio for the portfolio.

        Args:
            timestamps: List of datetime objects for each portfolio value.
            portfolio_values: List of portfolio values over time.

        Returns:
            Annualized Sharpe ratio assuming zero risk-free rate.

        """
        if len(portfolio_values) < 2:
            return 0.0

        returns = [portfolio_values[i] / portfolio_values[i - 1] - 1 for i in range(1, len(portfolio_values))]
        mean_return = sum(returns) / len(returns)
        std_return = (sum((ret - mean_return) ** 2 for ret in returns) / len(returns)) ** 0.5
        values_per_year = len(portfolio_values) / (timestamps[-1] - timestamps[0]).days * 365
        if std_return == 0:
            return 0.0
        return float(mean_return * values_per_year**0.5 / std_return)

    def calculate_sortino_ratio(self, timestamps: list[datetime], portfolio_values: list[float]) -> float:
        """Calculate the Sortino ratio for the portfolio.

        Similar to Sharpe ratio but only penalizes downside volatility.

        Args:
            timestamps: List of datetime objects for each portfolio value.
            portfolio_values: List of portfolio values over time.

        Returns:
            Annualized Sortino ratio assuming zero risk-free rate.

        """
        if len(portfolio_values) < 2:
            return 0.0

        returns = [portfolio_values[i] / portfolio_values[i - 1] - 1 for i in range(1, len(portfolio_values))]
        mean_return = sum(returns) / len(returns)

        if abs(mean_return) < 1e-10:
            return 0.0

        # Downside deviation: only penalize returns below zero (target return = 0)
        # Using semi-deviation approach: square only negative returns, normalize by all returns
        downside_deviation = (sum(min(ret, 0) ** 2 for ret in returns) / len(returns)) ** 0.5

        if downside_deviation == 0:
            return float("inf")  # No downside volatility

        values_per_year = len(portfolio_values) / (timestamps[-1] - timestamps[0]).days * 365
        return float(mean_return * values_per_year**0.5 / downside_deviation)

    def calculate_annualized_return(self, timestamps: list[datetime], portfolio_values: list[float]) -> float:
        """Calculate the annualized return.

        Args:
            timestamps: List of datetime objects for each portfolio value.
            portfolio_values: List of portfolio values over time.

        Returns:
            Annualized return as a decimal (e.g., 0.10 for 10% annual return).

        """
        days = (timestamps[-1] - timestamps[0]).days
        if days == 0:
            return 0.0
        return float((portfolio_values[-1] / portfolio_values[0]) ** (365 / days) - 1)

    def calculate_total_return(self, portfolio_values: list[float]) -> float:
        """Calculate the total return over the entire period.

        Args:
            portfolio_values: List of portfolio values over time.

        Returns:
            Total return as a decimal (e.g., 0.25 for 25% return).

        """
        return portfolio_values[-1] / portfolio_values[0] - 1

    def calculate_all_metrics(self, timestamps: list[datetime], portfolio_values: list[float]) -> dict[str, float]:
        """Calculate all performance metrics.

        Args:
            timestamps: List of datetime objects for each portfolio value.
            portfolio_values: List of portfolio values over time.

        Returns:
            Dictionary mapping metric names to their values.

        """
        return {
            "Max Drawdown": self.calculate_max_drawdown(portfolio_values),
            "Sharpe Ratio": self.calculate_sharpe_ratio(timestamps, portfolio_values),
            "Sortino Ratio": self.calculate_sortino_ratio(timestamps, portfolio_values),
            "Annualized Return": self.calculate_annualized_return(timestamps, portfolio_values),
            "Total Return": self.calculate_total_return(portfolio_values),
        }
