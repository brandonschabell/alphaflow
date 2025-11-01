"""Tests for rate limiting and backoff functionality in datafeeds."""

from datetime import datetime
from unittest.mock import patch

import httpx
import pytest
from pytest_httpx import HTTPXMock

from alphaflow.data_feeds.alpha_vantage_data_feed import AlphaVantageFeed
from alphaflow.data_feeds.fmp_data_feed import FMPDataFeed
from alphaflow.data_feeds.polygon_data_feed import PolygonDataFeed


# Test Helpers
def build_polygon_url(
    symbol: str,
    start_date: str,
    end_date: str,
    api_key: str = "test_key",
    multiplier: int = 1,
    timeframe: str = "day",
) -> str:
    """Build Polygon API URL matching the actual implementation."""
    base_url = "https://api.polygon.io"
    url = f"{base_url}/v2/aggs/ticker/{symbol}/range/{multiplier}/{timeframe}/{start_date}/{end_date}"
    return f"{url}?apiKey={api_key}&adjusted=true&sort=asc&limit=50000"


class TestPolygonDataFeedRateLimiting:
    """Test rate limiting behavior for PolygonDataFeed."""

    def test_rate_limit_with_successful_retry(self, httpx_mock: HTTPXMock) -> None:
        """Test that 429 rate limit triggers backoff and succeeds on retry."""
        symbol = "AAPL"
        start_date = "2024-01-01"
        end_date = "2024-01-05"

        # Build expected URL with query parameters
        url = build_polygon_url(symbol, start_date, end_date)

        # First request returns 429, second succeeds
        httpx_mock.add_response(url=url, status_code=429)
        httpx_mock.add_response(
            url=url,
            json={
                "status": "OK",
                "results": [
                    {
                        "t": 1704067200000,  # 2024-01-01 00:00:00 UTC
                        "o": 100.0,
                        "h": 105.0,
                        "l": 99.0,
                        "c": 103.0,
                        "v": 1000000,
                    }
                ],
            },
        )

        # Initialize datafeed with fast backoff for testing
        data_feed = PolygonDataFeed(
            api_key="test_key",
            rate_limit_retries=2,
            rate_limit_backoff=0.1,  # 0.1 seconds for fast test
            rate_limit_backoff_multiplier=1.0,
        )

        # Run and collect results
        with patch("time.sleep") as mock_sleep:
            events = list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

            # Should have slept once before retry
            mock_sleep.assert_called_once_with(0.1)

        # Should successfully get data after retry
        assert len(events) == 1
        assert events[0].symbol == symbol
        assert events[0].close == 103.0

    def test_rate_limit_exhausts_retries(self, httpx_mock: HTTPXMock) -> None:
        """Test that exhausting retries raises appropriate error."""
        symbol = "AAPL"
        start_date = "2024-01-01"
        end_date = "2024-01-05"

        url = build_polygon_url(symbol, start_date, end_date)

        # Always return 429
        for _ in range(4):  # Initial + 3 retries
            httpx_mock.add_response(url=url, status_code=429)

        data_feed = PolygonDataFeed(
            api_key="test_key",
            rate_limit_retries=3,
            rate_limit_backoff=0.1,
        )

        with patch("time.sleep"), pytest.raises(ValueError, match="Rate limit exceeded after 4 attempts"):
            list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

    def test_exponential_backoff(self, httpx_mock: HTTPXMock) -> None:
        """Test that exponential backoff multiplier works correctly."""
        symbol = "AAPL"
        start_date = "2024-01-01"
        end_date = "2024-01-05"

        url = build_polygon_url(symbol, start_date, end_date)

        # First two requests return 429, third succeeds
        httpx_mock.add_response(url=url, status_code=429)
        httpx_mock.add_response(url=url, status_code=429)
        httpx_mock.add_response(
            url=url,
            json={
                "status": "OK",
                "results": [
                    {
                        "t": 1704067200000,
                        "o": 100.0,
                        "h": 105.0,
                        "l": 99.0,
                        "c": 103.0,
                        "v": 1000000,
                    }
                ],
            },
        )

        data_feed = PolygonDataFeed(
            api_key="test_key",
            rate_limit_retries=3,
            rate_limit_backoff=1.0,
            rate_limit_backoff_multiplier=2.0,  # Double each time
        )

        with patch("time.sleep") as mock_sleep:
            events = list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

            # Should sleep with exponentially increasing delays
            # First retry: 1.0 * (2.0 ** 0) = 1.0
            # Second retry: 1.0 * (2.0 ** 1) = 2.0
            assert mock_sleep.call_count == 2
            mock_sleep.assert_any_call(1.0)
            mock_sleep.assert_any_call(2.0)

        assert len(events) == 1

    def test_non_rate_limit_error_fails_fast(self, httpx_mock: HTTPXMock) -> None:
        """Test that non-429 errors fail immediately without retry."""
        symbol = "AAPL"
        start_date = "2024-01-01"
        end_date = "2024-01-05"

        url = build_polygon_url(symbol, start_date, end_date)

        # Return 500 error (should not retry)
        httpx_mock.add_response(url=url, status_code=500)

        data_feed = PolygonDataFeed(
            api_key="test_key",
            rate_limit_retries=3,
            rate_limit_backoff=0.1,
        )

        with patch("time.sleep") as mock_sleep, pytest.raises(httpx.HTTPStatusError, match="500 Internal Server Error"):
            list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

        # Should not sleep/retry for non-429 errors
        mock_sleep.assert_not_called()

    def test_pagination_with_rate_limiting(self, httpx_mock: HTTPXMock) -> None:
        """Test that rate limiting works during pagination."""
        symbol = "AAPL"
        start_date = "2024-01-01"
        end_date = "2024-01-05"

        initial_url = build_polygon_url(symbol, start_date, end_date)
        # Polygon returns next_url without query params (they're added by the API)
        base_url = "https://api.polygon.io"
        next_url = f"{base_url}/v2/aggs/ticker/{symbol}/range/1/day/{start_date}/{end_date}?cursor=abc123"

        # Initial request succeeds with pagination
        httpx_mock.add_response(
            url=initial_url,
            json={
                "status": "OK",
                "results": [
                    {
                        "t": 1704067200000,
                        "o": 100.0,
                        "h": 105.0,
                        "l": 99.0,
                        "c": 103.0,
                        "v": 1000000,
                    }
                ],
                "next_url": next_url,
            },
        )

        # Next page hits rate limit then succeeds
        httpx_mock.add_response(url=next_url, status_code=429)
        httpx_mock.add_response(
            url=next_url,
            json={
                "status": "OK",
                "results": [
                    {
                        "t": 1704153600000,  # Next day
                        "o": 104.0,
                        "h": 106.0,
                        "l": 103.0,
                        "c": 105.0,
                        "v": 1100000,
                    }
                ],
            },
        )

        data_feed = PolygonDataFeed(
            api_key="test_key",
            rate_limit_retries=2,
            rate_limit_backoff=0.1,
        )

        with patch("time.sleep") as mock_sleep:
            events = list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

            # Should have slept once during pagination
            mock_sleep.assert_called_once_with(0.1)

        # Should get both pages of results
        assert len(events) == 2
        assert events[0].close == 103.0
        assert events[1].close == 105.0


class TestAlphaVantageFeedRateLimiting:
    """Test rate limiting behavior for AlphaVantageFeed."""

    def test_rate_limit_with_successful_retry(self, httpx_mock: HTTPXMock) -> None:
        """Test that 429 rate limit triggers backoff and succeeds on retry."""
        symbol = "AAPL"
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey=test_key&outputsize=full"

        # First request returns 429, second succeeds
        httpx_mock.add_response(url=url, status_code=429)
        httpx_mock.add_response(
            url=url,
            json={
                "Time Series (Daily)": {
                    "2024-01-01": {
                        "1. open": "100.0",
                        "2. high": "105.0",
                        "3. low": "99.0",
                        "4. close": "104.0",
                        "5. adjusted close": "103.0",
                        "6. volume": "1000000",
                    }
                }
            },
        )

        data_feed = AlphaVantageFeed(
            api_key="test_key",
            rate_limit_retries=2,
            rate_limit_backoff=0.1,
        )

        with patch("time.sleep") as mock_sleep:
            events = list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

            mock_sleep.assert_called_once_with(0.1)

        assert len(events) == 1
        assert events[0].close == 103.0


class TestFMPDataFeedRateLimiting:
    """Test rate limiting behavior for FMPDataFeed."""

    def test_rate_limit_with_successful_retry(self, httpx_mock: HTTPXMock) -> None:
        """Test that 429 rate limit triggers backoff and succeeds on retry."""
        symbol = "AAPL"
        base_url = "https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted"
        url = f"{base_url}?symbol={symbol}&apikey=test_key&from=2024-01-01&to=2024-01-05"

        # First request returns 429, second succeeds
        httpx_mock.add_response(url=url, status_code=429)
        httpx_mock.add_response(
            url=url,
            json=[
                {
                    "date": "2024-01-01",
                    "adjOpen": 100.0,
                    "adjHigh": 105.0,
                    "adjLow": 99.0,
                    "adjClose": 103.0,
                    "volume": 1000000,
                }
            ],
        )

        data_feed = FMPDataFeed(
            api_key="test_key",
            rate_limit_retries=2,
            rate_limit_backoff=0.1,
        )

        with patch("time.sleep") as mock_sleep:
            events = list(
                data_feed.run(
                    symbol=symbol,
                    start_timestamp=datetime(2024, 1, 1),
                    end_timestamp=datetime(2024, 1, 5),
                )
            )

            mock_sleep.assert_called_once_with(0.1)

        assert len(events) == 1
        assert events[0].close == 103.0


class TestDataFeedConfiguration:
    """Test datafeed initialization with rate limit parameters."""

    def test_polygon_custom_rate_limit_params(self) -> None:
        """Test PolygonDataFeed accepts custom rate limit parameters."""
        data_feed = PolygonDataFeed(
            api_key="test_key",
            rate_limit_retries=5,
            rate_limit_backoff=30.0,
            rate_limit_backoff_multiplier=1.5,
        )

        assert data_feed.rate_limit_retries == 5
        assert data_feed.rate_limit_backoff == 30.0
        assert data_feed.rate_limit_backoff_multiplier == 1.5

    def test_polygon_default_rate_limit_params(self) -> None:
        """Test PolygonDataFeed uses default rate limit parameters."""
        data_feed = PolygonDataFeed(api_key="test_key")

        assert data_feed.rate_limit_retries == 3
        assert data_feed.rate_limit_backoff == 60.0
        assert data_feed.rate_limit_backoff_multiplier == 1.0

    def test_alpha_vantage_custom_rate_limit_params(self) -> None:
        """Test AlphaVantageFeed accepts custom rate limit parameters."""
        data_feed = AlphaVantageFeed(
            api_key="test_key",
            rate_limit_retries=10,
            rate_limit_backoff=15.0,
        )

        assert data_feed.rate_limit_retries == 10
        assert data_feed.rate_limit_backoff == 15.0

    def test_fmp_custom_rate_limit_params(self) -> None:
        """Test FMPDataFeed accepts custom rate limit parameters."""
        data_feed = FMPDataFeed(
            api_key="test_key",
            rate_limit_retries=7,
            rate_limit_backoff=45.0,
        )

        assert data_feed.rate_limit_retries == 7
        assert data_feed.rate_limit_backoff == 45.0
