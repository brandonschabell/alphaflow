"""Tests for the DefaultAnalyzer."""

from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory

from alphaflow import AlphaFlow
from alphaflow.analyzers import DefaultAnalyzer
from alphaflow.brokers import SimpleBroker
from alphaflow.data_feeds import PolarsDataFeed
from alphaflow.strategies import BuyAndHoldStrategy


def test_default_analyzer_initialization() -> None:
    """Test analyzer is properly initialized."""
    analyzer = DefaultAnalyzer()
    assert analyzer._values == {}
    assert analyzer._fills == {}
    assert analyzer._plot_path is None


def test_default_analyzer_initialization_with_plot_path() -> None:
    """Test analyzer initialization with custom plot path."""
    plot_path = Path("test_plot.html")
    plot_title = "Test Portfolio"
    analyzer = DefaultAnalyzer(plot_path=plot_path, plot_title=plot_title)

    assert analyzer._plot_path == plot_path
    assert analyzer._plot_title == plot_title


def test_default_analyzer_topic_subscriptions() -> None:
    """Test analyzer subscribes to correct topics."""
    from alphaflow.enums import Topic

    analyzer = DefaultAnalyzer()
    topics = analyzer.topic_subscriptions()

    assert Topic.FILL in topics
    assert Topic.MARKET_DATA in topics
    assert len(topics) == 2


def test_default_analyzer_with_backtest() -> None:
    """Test analyzer collects data during a backtest."""
    af = AlphaFlow()
    af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
    af.add_equity("AAPL")
    af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
    af.set_broker(SimpleBroker())

    analyzer = DefaultAnalyzer()
    af.add_analyzer(analyzer)

    af.set_cash(10000)
    af.set_data_start_timestamp(datetime(1980, 12, 25))
    af.set_backtest_start_timestamp(datetime(1980, 12, 29))
    af.set_backtest_end_timestamp(datetime(1981, 1, 5))
    af.run()

    # Analyzer should have collected values
    assert len(analyzer._values) > 0
    assert len(analyzer._fills) > 0


def test_default_analyzer_generate_plot() -> None:
    """Test analyzer generates a plot file."""
    with TemporaryDirectory() as tmpdir:
        plot_path = Path(tmpdir) / "test_plot.html"

        af = AlphaFlow()
        af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
        af.add_equity("AAPL")
        af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
        af.set_broker(SimpleBroker())
        af.add_analyzer(DefaultAnalyzer(plot_path=plot_path))

        af.set_cash(10000)
        af.set_data_start_timestamp(datetime(1980, 12, 25))
        af.set_backtest_start_timestamp(datetime(1980, 12, 29))
        af.set_backtest_end_timestamp(datetime(1981, 1, 5))
        af.run()

        # Plot should be created
        assert plot_path.exists()


def test_default_analyzer_with_benchmark() -> None:
    """Test analyzer with benchmark comparison."""
    with TemporaryDirectory() as tmpdir:
        plot_path = Path(tmpdir) / "benchmark_plot.html"

        af = AlphaFlow()
        af.set_data_feed(PolarsDataFeed("alphaflow/tests/data/AAPL.csv"))
        af.add_equity("AAPL")
        af.set_benchmark("AAPL")  # Use AAPL as its own benchmark
        af.add_strategy(BuyAndHoldStrategy(symbol="AAPL", target_weight=1.0))
        af.set_broker(SimpleBroker())
        af.add_analyzer(DefaultAnalyzer(plot_path=plot_path, plot_title="With Benchmark"))

        af.set_cash(10000)
        af.set_data_start_timestamp(datetime(1980, 12, 25))
        af.set_backtest_start_timestamp(datetime(1980, 12, 29))
        af.set_backtest_end_timestamp(datetime(1981, 1, 5))
        af.run()

        # Plot should be created with benchmark
        assert plot_path.exists()


def test_analyzer_calculate_max_drawdown() -> None:
    """Test maximum drawdown calculation."""
    analyzer = DefaultAnalyzer()

    portfolio_values = [100.0, 110.0, 105.0, 95.0, 100.0, 120.0]
    max_drawdown = analyzer.calculate_max_drawdown(portfolio_values)

    # Peak at 110, trough at 95 = (110-95)/110 = 13.6%
    assert max_drawdown > 0.13
    assert max_drawdown < 0.14


def test_analyzer_calculate_sharpe_ratio() -> None:
    """Test Sharpe ratio calculation."""
    analyzer = DefaultAnalyzer()

    timestamps = [
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        datetime(2020, 1, 3),
        datetime(2020, 1, 4),
        datetime(2020, 1, 5),
    ]
    portfolio_values = [100.0, 102.0, 104.0, 103.0, 106.0]

    sharpe = analyzer.calculate_sharpe_ratio(timestamps, portfolio_values)

    # Should return a positive number for positive returns
    assert isinstance(sharpe, float)
    assert sharpe > 0


def test_analyzer_calculate_sharpe_ratio_zero_std() -> None:
    """Test Sharpe ratio with zero standard deviation."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)]
    portfolio_values = [100.0, 100.0, 100.0]  # No change

    sharpe = analyzer.calculate_sharpe_ratio(timestamps, portfolio_values)
    assert sharpe == 0.0


def test_analyzer_calculate_sharpe_ratio_single_value() -> None:
    """Test Sharpe ratio with only one value returns 0."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1)]
    portfolio_values = [100.0]

    sharpe = analyzer.calculate_sharpe_ratio(timestamps, portfolio_values)
    assert sharpe == 0.0


def test_analyzer_calculate_sharpe_ratio_same_day_span_returns_zero() -> None:
    """Test Sharpe ratio returns 0 when timestamps fall on the same day."""
    analyzer = DefaultAnalyzer()

    timestamps = [
        datetime(2020, 1, 1, 9, 30),
        datetime(2020, 1, 1, 10, 30),
        datetime(2020, 1, 1, 15, 45),
    ]
    portfolio_values = [100.0, 101.0, 102.0]

    sharpe = analyzer.calculate_sharpe_ratio(timestamps, portfolio_values)
    assert sharpe == 0.0


def test_analyzer_calculate_sortino_ratio() -> None:
    """Test Sortino ratio calculation."""
    analyzer = DefaultAnalyzer()

    timestamps = [
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        datetime(2020, 1, 3),
        datetime(2020, 1, 4),
        datetime(2020, 1, 5),
    ]
    portfolio_values = [100.0, 102.0, 101.0, 104.0, 106.0]

    sortino = analyzer.calculate_sortino_ratio(timestamps, portfolio_values)

    # Should return a positive number
    assert isinstance(sortino, float)
    assert sortino > 0


def test_analyzer_calculate_sortino_ratio_with_losses() -> None:
    """Test Sortino ratio correctly handles mixed returns."""
    analyzer = DefaultAnalyzer()

    timestamps = [
        datetime(2020, 1, 1),
        datetime(2020, 1, 2),
        datetime(2020, 1, 3),
        datetime(2020, 1, 4),
    ]
    # Returns: +5%, -2%, +3%
    portfolio_values = [100.0, 105.0, 102.9, 106.0]

    sortino = analyzer.calculate_sortino_ratio(timestamps, portfolio_values)

    # Should return a positive number
    assert isinstance(sortino, float)
    assert sortino > 0

    # Sortino focuses on downside deviation
    sharpe = analyzer.calculate_sharpe_ratio(timestamps, portfolio_values)
    assert isinstance(sharpe, float)
    assert sharpe > 0


def test_analyzer_calculate_sortino_ratio_zero_downside() -> None:
    """Test Sortino ratio with zero returns (constant portfolio values)."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)]
    portfolio_values = [100.0, 100.0, 100.0]

    sortino = analyzer.calculate_sortino_ratio(timestamps, portfolio_values)
    assert sortino == 0


def test_analyzer_calculate_sortino_ratio_only_positive_returns() -> None:
    """Test Sortino ratio with only positive returns returns infinity."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1), datetime(2020, 1, 2), datetime(2020, 1, 3)]
    portfolio_values = [100.0, 105.0, 110.0]  # Only gains

    sortino = analyzer.calculate_sortino_ratio(timestamps, portfolio_values)
    assert sortino == float("inf")  # No downside risk


def test_analyzer_calculate_sortino_ratio_single_value() -> None:
    """Test Sortino ratio with only one value returns 0."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1)]
    portfolio_values = [100.0]

    sortino = analyzer.calculate_sortino_ratio(timestamps, portfolio_values)
    assert sortino == 0.0


def test_analyzer_calculate_sortino_ratio_same_day_span_returns_zero() -> None:
    """Test Sortino ratio returns 0 when timestamps fall on the same day."""
    analyzer = DefaultAnalyzer()

    timestamps = [
        datetime(2020, 1, 1, 9, 30),
        datetime(2020, 1, 1, 11, 0),
        datetime(2020, 1, 1, 15, 45),
    ]
    portfolio_values = [100.0, 99.5, 101.0]

    sortino = analyzer.calculate_sortino_ratio(timestamps, portfolio_values)
    assert sortino == 0.0


def test_analyzer_calculate_annualized_return() -> None:
    """Test annualized return calculation."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1), datetime(2021, 1, 1)]  # 1 year
    portfolio_values = [100.0, 110.0]  # 10% return

    annualized = analyzer.calculate_annualized_return(timestamps, portfolio_values)

    # Should be approximately 10%
    assert annualized > 0.09
    assert annualized < 0.11


def test_analyzer_calculate_annualized_return_same_day() -> None:
    """Test annualized return with same day (zero days) returns 0."""
    analyzer = DefaultAnalyzer()

    timestamps = [datetime(2020, 1, 1), datetime(2020, 1, 1)]  # Same day
    portfolio_values = [100.0, 110.0]

    annualized = analyzer.calculate_annualized_return(timestamps, portfolio_values)
    assert annualized == 0.0


def test_analyzer_calculate_total_return() -> None:
    """Test total return calculation."""
    analyzer = DefaultAnalyzer()

    portfolio_values = [100.0, 150.0]
    total_return = analyzer.calculate_total_return(portfolio_values)

    # 50% return
    assert total_return == 0.5


def test_analyzer_calculate_all_metrics() -> None:
    """Test calculating all metrics at once."""
    analyzer = DefaultAnalyzer()

    timestamps = [
        datetime(2020, 1, 1),
        datetime(2020, 2, 1),
        datetime(2020, 3, 1),
        datetime(2020, 4, 1),
    ]
    portfolio_values = [100.0, 105.0, 103.0, 110.0]

    metrics = analyzer.calculate_all_metrics(timestamps, portfolio_values)

    # Check all expected metrics are present
    assert "Total Return" in metrics
    assert "Max Drawdown" in metrics
    assert "Sharpe Ratio" in metrics
    assert "Sortino Ratio" in metrics
    assert "Annualized Return" in metrics
    assert "Total Slippage Cost" in metrics
    assert "Total Commission Cost" in metrics
    assert "Total Transaction Costs" in metrics
    assert "Average Slippage (bps)" in metrics

    # All values should be strings
    for value in metrics.values():
        assert isinstance(value, str)
