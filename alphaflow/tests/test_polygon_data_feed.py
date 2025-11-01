"""Tests for Polygon.io data feed."""

import os
from datetime import datetime
from unittest.mock import patch

import httpx
import pytest
from dotenv import load_dotenv
from pytest_httpx import HTTPXMock

from alphaflow.data_feeds import PolygonDataFeed
from alphaflow.events import MarketDataEvent

# Load .env file for integration tests
# This allows tests to access API keys without manual export
load_dotenv()


# Test Helpers


def build_polygon_url(
    symbol: str,
    start_date: str,
    end_date: str,
    api_key: str = "test_key",
    multiplier: int = 1,
    timeframe: str = "day",
) -> str:
    """Build Polygon API URL matching the actual implementation.

    Args:
        symbol: Stock ticker symbol
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format
        api_key: API key for authentication
        multiplier: Timeframe multiplier
        timeframe: Timeframe (minute, hour, day, week, month)

    Returns:
        Complete URL with query parameters

    """
    base_url = "https://api.polygon.io"
    url = f"{base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timeframe}/{start_date}/{end_date}"
    return f"{url}?apiKey={api_key}&adjusted=true&sort=asc&limit=50000"


# Unit Tests (with mocking)


def test_polygon_data_feed_initialization_with_api_key() -> None:
    """Test PolygonDataFeed initialization with explicit API key."""
    api_key = "test_api_key_123"
    data_feed = PolygonDataFeed(api_key=api_key)

    assert data_feed.timeframe == "day"
    assert data_feed.multiplier == 1


def test_polygon_data_feed_initialization_with_env_var() -> None:
    """Test PolygonDataFeed initialization using environment variable."""
    with patch.dict(os.environ, {"POLYGON_API_KEY": "env_api_key_456"}):
        data_feed = PolygonDataFeed()

        assert data_feed.timeframe == "day"
        assert data_feed.multiplier == 1


def test_polygon_data_feed_initialization_without_api_key() -> None:
    """Test PolygonDataFeed raises ValueError without API key."""
    with patch.dict(os.environ, {}, clear=True), pytest.raises(ValueError, match="Polygon API key required"):
        PolygonDataFeed()


def test_polygon_data_feed_custom_timeframe() -> None:
    """Test PolygonDataFeed with custom timeframe settings."""
    data_feed = PolygonDataFeed(
        api_key="test_key",
        timeframe="minute",
        multiplier=5,
    )

    assert data_feed.timeframe == "minute"
    assert data_feed.multiplier == 5


def test_polygon_data_feed_requires_start_timestamp() -> None:
    """Test that run() requires start_timestamp."""
    data_feed = PolygonDataFeed(api_key="test_key")

    with pytest.raises(ValueError, match="requires start_timestamp and end_timestamp"):
        list(
            data_feed.run(
                symbol="AAPL",
                start_timestamp=None,
                end_timestamp=datetime(2024, 1, 1),
            )
        )


def test_polygon_data_feed_requires_end_timestamp() -> None:
    """Test that run() requires end_timestamp."""
    data_feed = PolygonDataFeed(api_key="test_key")

    with pytest.raises(ValueError, match="requires start_timestamp and end_timestamp"):
        list(
            data_feed.run(
                symbol="AAPL",
                start_timestamp=datetime(2024, 1, 1),
                end_timestamp=None,
            )
        )


def test_polygon_data_feed_successful_response(httpx_mock: HTTPXMock) -> None:
    """Test successful API response yields correct MarketDataEvents."""
    # Mock API response
    httpx_mock.add_response(
        url=build_polygon_url("AAPL", "2024-01-01", "2024-01-03"),
        json={
            "status": "OK",
            "results": [
                {
                    "t": 1704067200000,  # 2024-01-01 00:00:00 UTC in milliseconds
                    "o": 185.0,
                    "h": 188.0,
                    "l": 184.0,
                    "c": 187.0,
                    "v": 50000000,
                },
                {
                    "t": 1704153600000,  # 2024-01-02 00:00:00 UTC
                    "o": 187.0,
                    "h": 189.0,
                    "l": 186.0,
                    "c": 188.5,
                    "v": 45000000,
                },
            ],
        },
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 3),
        )
    )

    assert len(events) == 2
    assert all(isinstance(event, MarketDataEvent) for event in events)

    # Check first event
    assert events[0].symbol == "AAPL"
    assert events[0].open == 185.0
    assert events[0].high == 188.0
    assert events[0].low == 184.0
    assert events[0].close == 187.0
    assert events[0].volume == 50000000
    # Polygon returns UTC timestamps - verify exact UTC datetime
    assert events[0].timestamp == datetime(2024, 1, 1, 0, 0, 0)

    # Check second event
    assert events[1].timestamp == datetime(2024, 1, 2, 0, 0, 0)


def test_polygon_data_feed_events_sorted_by_timestamp(httpx_mock: HTTPXMock) -> None:
    """Test events are yielded in chronological order."""
    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [
                {
                    "t": 1704067200000,
                    "o": 185.0,
                    "h": 188.0,
                    "l": 184.0,
                    "c": 187.0,
                    "v": 50000000,
                },  # 2024-01-01 00:00 UTC
                {
                    "t": 1704153600000,
                    "o": 187.0,
                    "h": 189.0,
                    "l": 186.0,
                    "c": 188.5,
                    "v": 45000000,
                },  # 2024-01-02 00:00 UTC
                {
                    "t": 1704240000000,
                    "o": 188.5,
                    "h": 190.0,
                    "l": 188.0,
                    "c": 189.5,
                    "v": 40000000,
                },  # 2024-01-03 00:00 UTC
            ],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    timestamps = [event.timestamp for event in events]
    assert timestamps == sorted(timestamps)


def test_polygon_data_feed_empty_results(httpx_mock: HTTPXMock) -> None:
    """Test data feed handles empty results gracefully."""
    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 3),
        )
    )

    assert len(events) == 0


def test_polygon_data_feed_api_error(httpx_mock: HTTPXMock) -> None:
    """Test data feed handles API errors appropriately."""
    httpx_mock.add_response(
        json={
            "status": "ERROR",
            "error": "Invalid API key",
        }
    )

    data_feed = PolygonDataFeed(api_key="invalid_key")

    with pytest.raises(ValueError, match="Polygon API error: Invalid API key"):
        list(
            data_feed.run(
                symbol="AAPL",
                start_timestamp=datetime(2024, 1, 1),
                end_timestamp=datetime(2024, 1, 3),
            )
        )


def test_polygon_data_feed_http_error(httpx_mock: HTTPXMock) -> None:
    """Test data feed handles HTTP errors."""
    httpx_mock.add_response(status_code=500)

    data_feed = PolygonDataFeed(api_key="test_key")

    with pytest.raises(httpx.HTTPStatusError, match="500 Internal Server Error"):
        list(
            data_feed.run(
                symbol="AAPL",
                start_timestamp=datetime(2024, 1, 1),
                end_timestamp=datetime(2024, 1, 3),
            )
        )


def test_polygon_data_feed_pagination(httpx_mock: HTTPXMock) -> None:
    """Test data feed handles pagination correctly."""
    # First page with next_url
    httpx_mock.add_response(
        url=build_polygon_url("AAPL", "2024-01-01", "2024-01-05"),
        json={
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 185.0, "h": 188.0, "l": 184.0, "c": 187.0, "v": 50000000},
            ],
            "next_url": "https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-05?cursor=next_page",
        },
    )

    # Second page
    httpx_mock.add_response(
        url="https://api.polygon.io/v2/aggs/ticker/AAPL/range/1/day/2024-01-01/2024-01-05?cursor=next_page",
        json={
            "status": "OK",
            "results": [
                {"t": 1704153600000, "o": 187.0, "h": 189.0, "l": 186.0, "c": 188.5, "v": 45000000},
            ],
        },
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    # Should have combined results from both pages
    assert len(events) == 2


def test_polygon_data_feed_event_has_all_ohlcv_fields(httpx_mock: HTTPXMock) -> None:
    """Test MarketDataEvent has all required fields."""
    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 185.0, "h": 188.0, "l": 184.0, "c": 187.0, "v": 50000000},
            ],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 3),
        )
    )

    event = events[0]
    assert hasattr(event, "open")
    assert hasattr(event, "high")
    assert hasattr(event, "low")
    assert hasattr(event, "close")
    assert hasattr(event, "volume")
    assert hasattr(event, "timestamp")
    assert hasattr(event, "symbol")


def test_polygon_data_feed_prices_are_positive(httpx_mock: HTTPXMock) -> None:
    """Test all OHLC prices are positive."""
    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 185.0, "h": 188.0, "l": 184.0, "c": 187.0, "v": 50000000},
            ],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 3),
        )
    )

    for event in events:
        assert event.open > 0
        assert event.high > 0
        assert event.low > 0
        assert event.close > 0


def test_polygon_data_feed_high_low_relationship(httpx_mock: HTTPXMock) -> None:
    """Test high >= low for all events."""
    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 185.0, "h": 188.0, "l": 184.0, "c": 187.0, "v": 50000000},
                {"t": 1704153600000, "o": 187.0, "h": 189.0, "l": 186.0, "c": 188.5, "v": 45000000},
            ],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 3),
        )
    )

    for event in events:
        assert event.high >= event.low


def test_polygon_data_feed_correct_symbol(httpx_mock: HTTPXMock) -> None:
    """Test all events have the requested symbol."""
    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [
                {"t": 1704067200000, "o": 185.0, "h": 188.0, "l": 184.0, "c": 187.0, "v": 50000000},
            ],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="TEST_SYMBOL",
            start_timestamp=datetime(2024, 1, 1),
            end_timestamp=datetime(2024, 1, 3),
        )
    )

    assert all(event.symbol == "TEST_SYMBOL" for event in events)


def test_polygon_data_feed_utc_timestamp_handling(httpx_mock: HTTPXMock) -> None:
    """Test that UTC timestamps from Polygon are correctly converted to naive UTC datetimes.

    Polygon returns timestamps in UTC milliseconds. We use fromtimestamp(ts, tz=timezone.utc)
    rather than fromtimestamp() to avoid local timezone conversion issues.
    This test validates that timestamps are correctly interpreted as UTC.
    """
    # Test with a specific UTC timestamp that has a different local time in various timezones
    # 2024-01-15 14:30:00 UTC = 1705329000000 milliseconds
    # In PST (UTC-8): 2024-01-15 06:30:00
    # In EST (UTC-5): 2024-01-15 09:30:00
    # In JST (UTC+9): 2024-01-15 23:30:00

    httpx_mock.add_response(
        json={
            "status": "OK",
            "results": [
                {
                    "t": 1705329000000,  # 2024-01-15 14:30:00 UTC
                    "o": 150.0,
                    "h": 152.0,
                    "l": 149.0,
                    "c": 151.0,
                    "v": 1000000,
                },
                {
                    "t": 1705332600000,  # 2024-01-15 15:30:00 UTC (1 hour later)
                    "o": 151.0,
                    "h": 153.0,
                    "l": 150.5,
                    "c": 152.5,
                    "v": 1100000,
                },
            ],
        }
    )

    data_feed = PolygonDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="TEST",
            start_timestamp=datetime(2024, 1, 15),
            end_timestamp=datetime(2024, 1, 16),
        )
    )

    # Verify timestamps are exactly as expected in UTC, not converted to local time
    assert events[0].timestamp == datetime(2024, 1, 15, 14, 30, 0)
    assert events[1].timestamp == datetime(2024, 1, 15, 15, 30, 0)

    # Verify the timestamps are naive (no timezone info)
    assert events[0].timestamp.tzinfo is None
    assert events[1].timestamp.tzinfo is None

    # Verify correct time delta (should be exactly 1 hour)
    time_delta = events[1].timestamp - events[0].timestamp
    assert time_delta.total_seconds() == 3600  # 1 hour = 3600 seconds


# Integration Tests (requires real API key)


@pytest.mark.skipif(
    not os.getenv("POLYGON_API_KEY"),
    reason="POLYGON_API_KEY not found. Add it to .env file to run integration tests.",
)
def test_polygon_data_feed_integration_real_api() -> None:
    """Integration test with real Polygon.io API.

    Requires POLYGON_API_KEY in .env file or environment.
    Tests daily data retrieval for a well-known stock.
    """
    data_feed = PolygonDataFeed()  # Uses POLYGON_API_KEY from env

    # Test with a well-known stock and recent date range
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 2),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    # Should have at least one trading day
    assert len(events) > 0
    assert all(isinstance(event, MarketDataEvent) for event in events)
    assert all(event.symbol == "AAPL" for event in events)
    assert all(event.open > 0 for event in events)
    assert all(event.high >= event.low for event in events)

    # Events should be sorted chronologically
    timestamps = [event.timestamp for event in events]
    assert timestamps == sorted(timestamps)


@pytest.mark.skipif(
    not os.getenv("POLYGON_API_KEY"),
    reason="POLYGON_API_KEY not found. Add it to .env file to run integration tests.",
)
def test_polygon_data_feed_integration_intraday() -> None:
    """Integration test for intraday data.

    Requires POLYGON_API_KEY in .env file or environment.
    Requires premium Polygon.io tier for intraday data access.
    Will skip if only free tier is available.
    """
    data_feed = PolygonDataFeed(timeframe="minute", multiplier=5)

    try:
        events = list(
            data_feed.run(
                symbol="AAPL",
                start_timestamp=datetime(2024, 1, 2, 9, 30),  # Market open
                end_timestamp=datetime(2024, 1, 2, 10, 30),  # One hour of data
            )
        )

        # If we get here, user has premium access
        assert len(events) > 0
        assert all(isinstance(event, MarketDataEvent) for event in events)

    except ValueError as e:
        # Free tier doesn't support intraday - this is expected
        if "premium" in str(e).lower() or "unauthorized" in str(e).lower():
            pytest.skip("Intraday data requires premium Polygon.io tier")
        raise
