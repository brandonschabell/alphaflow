"""Tests for Polars data feeds."""

from datetime import datetime
from pathlib import Path

import polars as pl

from alphaflow.data_feeds import PolarsDataFeed
from alphaflow.events import MarketDataEvent


def test_polars_data_feed_initialization() -> None:
    """Test PolarsDataFeed initialization."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    assert isinstance(data_feed.df_or_file_path, str)
    assert data_feed.df_or_file_path == "alphaflow/tests/data/AAPL.csv"


def test_polars_data_feed_run_yields_market_data_events() -> None:
    """Test PolarsDataFeed yields MarketDataEvent objects."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    assert len(events) > 0
    assert all(isinstance(event, MarketDataEvent) for event in events)


def test_polars_data_feed_events_have_correct_symbol() -> None:
    """Test all events have the requested symbol."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    events = list(
        data_feed.run(
            symbol="TEST_SYMBOL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    assert all(event.symbol == "TEST_SYMBOL" for event in events)


def test_polars_data_feed_events_sorted_by_timestamp() -> None:
    """Test events are yielded in chronological order."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1981, 1, 31),
        )
    )

    timestamps = [event.timestamp for event in events]
    assert timestamps == sorted(timestamps)


def test_polars_data_feed_respects_start_timestamp() -> None:
    """Test data feed only yields events after start timestamp."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")
    start_timestamp = datetime(1981, 1, 1)

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=start_timestamp,
            end_timestamp=datetime(1981, 1, 31),
        )
    )

    assert all(event.timestamp >= start_timestamp for event in events)


def test_polars_data_feed_respects_end_timestamp() -> None:
    """Test data feed only yields events before end timestamp."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")
    end_timestamp = datetime(1981, 1, 15)

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=end_timestamp,
        )
    )

    assert all(event.timestamp <= end_timestamp for event in events)


def test_polars_data_feed_event_has_all_ohlcv_fields() -> None:
    """Test MarketDataEvent has open, high, low, close, volume."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    # Check first event has all required fields
    event = events[0]
    assert hasattr(event, "open")
    assert hasattr(event, "high")
    assert hasattr(event, "low")
    assert hasattr(event, "close")
    assert hasattr(event, "volume")
    assert hasattr(event, "timestamp")
    assert hasattr(event, "symbol")


def test_polars_data_feed_prices_are_positive() -> None:
    """Test all OHLC prices are positive."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    for event in events:
        assert event.open > 0
        assert event.high > 0
        assert event.low > 0
        assert event.close > 0


def test_polars_data_feed_high_low_relationship() -> None:
    """Test high >= low for all events."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1981, 1, 31),
        )
    )

    for event in events:
        assert event.high >= event.low


def test_polars_data_feed_empty_range() -> None:
    """Test data feed with date range that has no data."""
    data_feed = PolarsDataFeed("alphaflow/tests/data/AAPL.csv")

    # Use a date range before any data exists
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1970, 1, 1),
            end_timestamp=datetime(1970, 1, 31),
        )
    )

    assert len(events) == 0


def test_polars_data_feed_initialization_with_dataframe() -> None:
    """Test PolarsDataFeed initialization with a Polars DataFrame."""
    df = pl.read_csv("alphaflow/tests/data/AAPL.csv", try_parse_dates=True)
    data_feed = PolarsDataFeed(df)

    assert isinstance(data_feed.df_or_file_path, pl.DataFrame)


def test_polars_data_feed_initialization_with_lazyframe() -> None:
    """Test PolarsDataFeed initialization with a Polars LazyFrame."""
    lf = pl.scan_csv("alphaflow/tests/data/AAPL.csv", try_parse_dates=True)
    data_feed = PolarsDataFeed(lf)

    assert isinstance(data_feed.df_or_file_path, pl.LazyFrame)


def test_polars_data_feed_initialization_with_parquet(tmp_path: Path) -> None:
    """Test PolarsDataFeed initialization with a parquet file path."""
    # Create a temporary parquet file from CSV data
    df = pl.read_csv("alphaflow/tests/data/AAPL.csv", try_parse_dates=True)
    parquet_path = tmp_path / "AAPL.parquet"
    df.write_parquet(parquet_path)

    data_feed = PolarsDataFeed(parquet_path)

    assert isinstance(data_feed.df_or_file_path, Path)
    assert data_feed.df_or_file_path == parquet_path


def test_polars_data_feed_run_with_dataframe() -> None:
    """Test PolarsDataFeed run with a Polars DataFrame yields correct events."""
    df = pl.read_csv("alphaflow/tests/data/AAPL.csv", try_parse_dates=True)
    data_feed = PolarsDataFeed(df)

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    assert len(events) > 0
    assert all(isinstance(event, MarketDataEvent) for event in events)
    assert all(event.symbol == "AAPL" for event in events)


def test_polars_data_feed_run_with_lazyframe() -> None:
    """Test PolarsDataFeed run with a Polars LazyFrame yields correct events."""
    lf = pl.scan_csv("alphaflow/tests/data/AAPL.csv", try_parse_dates=True)
    data_feed = PolarsDataFeed(lf)

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    assert len(events) > 0
    assert all(isinstance(event, MarketDataEvent) for event in events)
    assert all(event.symbol == "AAPL" for event in events)


def test_polars_data_feed_run_with_parquet(tmp_path: Path) -> None:
    """Test PolarsDataFeed run with a parquet file yields correct events."""
    # Create a temporary parquet file from CSV data
    df = pl.read_csv("alphaflow/tests/data/AAPL.csv", try_parse_dates=True)
    parquet_path = tmp_path / "AAPL.parquet"
    df.write_parquet(parquet_path)

    data_feed = PolarsDataFeed(parquet_path)

    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(1980, 12, 25),
            end_timestamp=datetime(1980, 12, 31),
        )
    )

    assert len(events) > 0
    assert all(isinstance(event, MarketDataEvent) for event in events)
    assert all(event.symbol == "AAPL" for event in events)
