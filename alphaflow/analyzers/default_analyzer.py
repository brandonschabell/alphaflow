"""Default analyzer implementation for portfolio performance analysis."""

from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import seaborn as sns

from alphaflow import Analyzer
from alphaflow.enums import Topic
from alphaflow.events import FillEvent, MarketDataEvent


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

    def topic_subscriptions(self):
        """Return the topics this analyzer subscribes to.

        Returns:
            List of topics to monitor (FILL and MARKET_DATA).

        """
        return [Topic.FILL, Topic.MARKET_DATA]

    def read_event(self, event: FillEvent | MarketDataEvent):
        """Process events and record portfolio values.

        Args:
            event: Either a FillEvent or MarketDataEvent to process.

        """
        self._values[event.timestamp] = self._alpha_flow.portfolio.get_portfolio_value(event.timestamp)
        if isinstance(event, FillEvent):
            self._fills[event.timestamp] = event

    def run(self):
        """Run the analysis after backtest completion.

        Computes all performance metrics, prints them to console, and generates
        a visualization plot if plot_path was specified.

        """
        timestamps, portfolio_values = zip(*self._values.items(), strict=False)

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
        anualized_return_str = (
            f"Anualized Return: {100 * self.calculate_anualized_return(timestamps, portfolio_values):.2f}%"
        )

        benchmark_values = self._alpha_flow.portfolio.get_benchmark_values()
        if benchmark_values:
            benchmark_timestamps, benchmark_values = zip(*benchmark_values.items(), strict=False)
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
            benchmark_anualized_return = self.calculate_anualized_return(benchmark_timestamps, benchmark_values)
            drawdown_str += f" (Benchmark: {100 * benchmark_drawdown:.2f}%)"
            sharpe_str += f" (Benchmark: {benchmark_sharpe:.4f})"
            sortino_str += f" (Benchmark: {benchmark_sortino:.4f})"
            anualized_return_str += f" (Benchmark: {100 * benchmark_anualized_return:.2f}%)"

        ax.legend()

        metrics_text = "\n".join([drawdown_str, sharpe_str, sortino_str, anualized_return_str])
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
        max_drawdown = 0
        peak = portfolio_values[0]
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
        returns = [portfolio_values[i] / portfolio_values[i - 1] - 1 for i in range(1, len(portfolio_values))]
        mean_return = sum(returns) / len(returns)
        std_return = (sum((ret - mean_return) ** 2 for ret in returns) / len(returns)) ** 0.5
        values_per_year = len(portfolio_values) / (timestamps[-1] - timestamps[0]).days * 365
        if std_return == 0:
            return 0
        return mean_return * values_per_year**0.5 / std_return

    def calculate_sortino_ratio(self, timestamps: list[datetime], portfolio_values: list[float]) -> float:
        """Calculate the Sortino ratio for the portfolio.

        Similar to Sharpe ratio but only penalizes downside volatility.

        Args:
            timestamps: List of datetime objects for each portfolio value.
            portfolio_values: List of portfolio values over time.

        Returns:
            Annualized Sortino ratio assuming zero risk-free rate.

        """
        returns = [portfolio_values[i] / portfolio_values[i - 1] - 1 for i in range(1, len(portfolio_values))]
        downside_returns = [min(ret, 0) for ret in returns]
        mean_return = sum(returns) / len(returns)
        downside_deviation = (sum((ret - mean_return) ** 2 for ret in downside_returns) / len(downside_returns)) ** 0.5
        values_per_year = len(portfolio_values) / (timestamps[-1] - timestamps[0]).days * 365
        if downside_deviation == 0:
            return 0
        return mean_return * values_per_year**0.5 / downside_deviation

    def calculate_anualized_return(self, timestamps: list[datetime], portfolio_values: list[float]) -> float:
        """Calculate the annualized return.

        Args:
            timestamps: List of datetime objects for each portfolio value.
            portfolio_values: List of portfolio values over time.

        Returns:
            Annualized return as a decimal (e.g., 0.10 for 10% annual return).

        """
        return (portfolio_values[-1] / portfolio_values[0]) ** (365 / (timestamps[-1] - timestamps[0]).days) - 1

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
            "Anualized Return": self.calculate_anualized_return(timestamps, portfolio_values),
            "Total Return": self.calculate_total_return(portfolio_values),
        }
