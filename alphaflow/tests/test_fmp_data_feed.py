"""Tests for FMP data feed.

Most tests use mocked responses. One integration test makes a real API call
and requires a valid FMP_API_KEY environment variable to run.
"""

import os
from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

import httpx
import pytest

from alphaflow.data_feeds import FMPDataFeed
from alphaflow.events import MarketDataEvent


@pytest.fixture
def mock_fmp_response() -> list[dict[str, str | float]]:
    """Mock FMP API response data in reverse chronological order (as API returns)."""
    return [
        {
            "date": "2024-01-05",
            "adjOpen": 181.99,
            "adjHigh": 185.59,
            "adjLow": 181.81,
            "adjClose": 185.14,
            "volume": 71946900,
        },
        {
            "date": "2024-01-04",
            "adjOpen": 182.15,
            "adjHigh": 183.08,
            "adjLow": 180.88,
            "adjClose": 181.91,
            "volume": 87667500,
        },
        {
            "date": "2024-01-03",
            "adjOpen": 184.22,
            "adjHigh": 185.88,
            "adjLow": 183.43,
            "adjClose": 184.25,
            "volume": 58414400,
        },
    ]


def test_fmp_data_feed_initialization() -> None:
    """Test FMPDataFeed initialization with API key."""
    data_feed = FMPDataFeed(api_key="test_key")
    assert data_feed is not None


def test_fmp_data_feed_initialization_from_env() -> None:
    """Test FMPDataFeed initialization from environment variable."""
    with patch.dict(os.environ, {"FMP_API_KEY": "env_test_key"}):
        data_feed = FMPDataFeed()
        assert data_feed is not None


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_yields_market_data_events(
    mock_get: Any, mock_fmp_response: list[dict[str, str | float]]
) -> None:
    """Test FMPDataFeed yields MarketDataEvent objects."""
    mock_get.return_value.json.return_value = mock_fmp_response
    mock_get.return_value.raise_for_status.return_value = None

    data_feed = FMPDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 3),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    assert len(events) == 3
    assert all(isinstance(event, MarketDataEvent) for event in events)


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_events_have_correct_symbol(
    mock_get: Any, mock_fmp_response: list[dict[str, str | float]]
) -> None:
    """Test all events have the requested symbol."""
    mock_get.return_value.json.return_value = mock_fmp_response
    mock_get.return_value.raise_for_status.return_value = None

    data_feed = FMPDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="TEST_SYMBOL",
            start_timestamp=datetime(2024, 1, 3),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    assert all(event.symbol == "TEST_SYMBOL" for event in events)


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_events_sorted_by_timestamp(
    mock_get: Any, mock_fmp_response: list[dict[str, str | float]]
) -> None:
    """Test events are yielded in chronological order (oldest first)."""
    mock_get.return_value.json.return_value = mock_fmp_response
    mock_get.return_value.raise_for_status.return_value = None

    data_feed = FMPDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 3),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    timestamps = [event.timestamp for event in events]
    assert timestamps == sorted(timestamps), "Events should be sorted chronologically"


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_event_has_all_ohlcv_fields(
    mock_get: Any, mock_fmp_response: list[dict[str, str | float]]
) -> None:
    """Test MarketDataEvent has all required OHLCV fields."""
    mock_get.return_value.json.return_value = mock_fmp_response
    mock_get.return_value.raise_for_status.return_value = None

    data_feed = FMPDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 3),
            end_timestamp=datetime(2024, 1, 5),
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


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_uses_adjusted_prices(mock_get: Any, mock_fmp_response: list[dict[str, str | float]]) -> None:
    """Test that FMPDataFeed correctly parses adjusted OHLC fields."""
    mock_get.return_value.json.return_value = mock_fmp_response
    mock_get.return_value.raise_for_status.return_value = None

    data_feed = FMPDataFeed(api_key="test_key")
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 3),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    # Check that first event (Jan 3rd after reversing) has expected values
    event = events[0]
    assert event.open == 184.22
    assert event.high == 185.88
    assert event.low == 183.43
    assert event.close == 184.25
    assert event.volume == 58414400


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_constructs_correct_url(mock_get: Any, mock_fmp_response: list[dict[str, str | float]]) -> None:
    """Test that the correct stable endpoint URL is constructed."""
    mock_get.return_value.json.return_value = mock_fmp_response
    mock_get.return_value.raise_for_status.return_value = None

    data_feed = FMPDataFeed(api_key="test_key_123")
    list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 3),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    # Verify the URL uses the new stable endpoint
    call_args = mock_get.call_args[0][0]
    assert "financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted" in call_args
    assert "symbol=AAPL" in call_args
    assert "apikey=test_key_123" in call_args
    assert "from=2024-01-03" in call_args
    assert "to=2024-01-05" in call_args


@patch("alphaflow.data_feeds.fmp_data_feed.httpx.get")
def test_fmp_data_feed_handles_http_error(mock_get: Any) -> None:
    """Test that HTTP errors are properly raised."""
    mock_request = Mock(spec=httpx.Request)
    mock_response = Mock(spec=httpx.Response)

    mock_get.return_value.raise_for_status.side_effect = httpx.HTTPStatusError(
        "404 Not Found",
        request=mock_request,
        response=mock_response,
    )

    data_feed = FMPDataFeed(api_key="test_key")
    with pytest.raises(ValueError, match="Failed to fetch data from FMP"):
        list(
            data_feed.run(
                symbol="INVALID",
                start_timestamp=datetime(2024, 1, 3),
                end_timestamp=datetime(2024, 1, 5),
            )
        )


def test_fmp_data_feed_cache_not_implemented() -> None:
    """Test that cache option raises NotImplementedError."""
    data_feed = FMPDataFeed(api_key="test_key", use_cache=True)

    with pytest.raises(NotImplementedError, match="Cache not implemented yet"):
        list(
            data_feed.run(
                symbol="AAPL",
                start_timestamp=datetime(2024, 1, 3),
                end_timestamp=datetime(2024, 1, 5),
            )
        )


@pytest.mark.skipif(
    not os.getenv("FMP_API_KEY"),
    reason="FMP_API_KEY environment variable not set",
)
def test_fmp_data_feed_integration() -> None:
    """Integration test: Verify endpoint works with real API.

    This test makes a real API call to verify the new stable endpoint works.
    Requires FMP_API_KEY environment variable.
    """
    data_feed = FMPDataFeed(api_key=os.getenv("FMP_API_KEY"))
    events = list(
        data_feed.run(
            symbol="AAPL",
            start_timestamp=datetime(2024, 1, 2),
            end_timestamp=datetime(2024, 1, 5),
        )
    )

    # Basic assertions to verify the endpoint works
    assert len(events) > 0, "Should fetch data from FMP API"
    assert all(isinstance(event, MarketDataEvent) for event in events)
    assert all(event.symbol == "AAPL" for event in events)
    assert all(event.open > 0 for event in events)
    assert all(event.high >= event.low for event in events)

    # Verify events are sorted chronologically
    timestamps = [event.timestamp for event in events]
    assert timestamps == sorted(timestamps)
