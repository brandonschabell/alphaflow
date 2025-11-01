"""Polygon.io API data feed implementation."""

import logging
import os
from collections.abc import Generator
from datetime import datetime, timezone
from functools import partial
from typing import cast

import httpx

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent
from alphaflow.utils import http_request_with_backoff

logger = logging.getLogger(__name__)


class PolygonDataFeed(DataFeed):
    """Data feed that loads market data from Polygon.io API.

    Supports daily and intraday OHLCV data.
    See https://polygon.io for API documentation and pricing.
    """

    BASE_URL = "https://api.polygon.io"

    def __init__(
        self,
        api_key: str | None = None,
        timeframe: str = "day",
        multiplier: int = 1,
        rate_limit_retries: int = 3,
        rate_limit_backoff: float = 60.0,
        rate_limit_backoff_multiplier: float = 1.0,
    ) -> None:
        """Initialize the Polygon.io data feed.

        Args:
            api_key: Polygon.io API key. Falls back to POLYGON_API_KEY env var.
            timeframe: Timeframe for bars ('minute', 'hour', 'day', 'week', 'month').
            multiplier: Multiplier for the timeframe (e.g., 5 for 5-minute bars).
            rate_limit_retries: Number of retry attempts for 429 rate limit errors (default: 3).
            rate_limit_backoff: Initial backoff delay in seconds for rate limit errors (default: 60).
            rate_limit_backoff_multiplier: Multiplier for exponential backoff (default: 1.0).

        """
        self.__api_key = api_key or os.getenv("POLYGON_API_KEY")
        if not self.__api_key:
            raise ValueError(
                "Polygon API key required. Provide via api_key parameter or POLYGON_API_KEY environment variable."
            )

        self.timeframe = timeframe
        self.multiplier = multiplier
        self.rate_limit_retries = rate_limit_retries
        self.rate_limit_backoff = rate_limit_backoff
        self.rate_limit_backoff_multiplier = rate_limit_backoff_multiplier

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        """Load and yield market data events from Polygon.io API.

        Args:
            symbol: The ticker symbol to load data for.
            start_timestamp: Start time for data range (required).
            end_timestamp: End time for data range (required).

        Yields:
            MarketDataEvent objects containing OHLCV data and optionally bid/ask.

        Raises:
            ValueError: If start_timestamp or end_timestamp is None, or API request fails.

        """
        if start_timestamp is None or end_timestamp is None:
            raise ValueError("Polygon data feed requires start_timestamp and end_timestamp")

        # Format dates for API (YYYY-MM-DD)
        start_date = start_timestamp.strftime("%Y-%m-%d")
        end_date = end_timestamp.strftime("%Y-%m-%d")

        # Build aggregates URL
        url = (
            f"{self.BASE_URL}/v2/aggs/ticker/{symbol}/range/{self.multiplier}/{self.timeframe}/{start_date}/{end_date}"
        )

        params: dict[str, str | int | None] = {
            "apiKey": self.__api_key,
            "adjusted": "true",  # Use adjusted prices (splits, dividends)
            "sort": "asc",  # Chronological order
            "limit": 50000,  # Max results per request
        }

        logger.info(f"Fetching {self.multiplier}{self.timeframe} data for '{symbol}' from {start_date} to {end_date}")

        # Fetch initial page with retry/backoff
        data = http_request_with_backoff(
            request_func=lambda: httpx.get(url, params=params, timeout=httpx.Timeout(30.0)),
            retries=self.rate_limit_retries,
            backoff=self.rate_limit_backoff,
            backoff_multiplier=self.rate_limit_backoff_multiplier,
            error_message="Failed to fetch data from Polygon",
        )

        # Check response status
        if data.get("status") != "OK":
            error_msg = data.get("error", "Unknown error")
            raise ValueError(f"Polygon API error: {error_msg}")

        # Check if we have results
        results = data.get("results", [])
        if not results:
            logger.warning(f"No data returned for {symbol} in date range {start_date} to {end_date}")
            return

        # Process and yield results from first page
        total_bars = len(results)
        for bar in results:
            # Polygon returns UTC timestamps in milliseconds
            # Convert to naive UTC datetime (timezone.utc then strip tzinfo for consistency)
            timestamp = datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc).replace(tzinfo=None)

            # Create market data event
            event = MarketDataEvent(
                timestamp=timestamp,
                symbol=symbol,
                open=float(bar["o"]),
                high=float(bar["h"]),
                low=float(bar["l"]),
                close=float(bar["c"]),
                volume=int(bar["v"]),
                # Bid/ask will be None for now - requires separate API call
                # This could be extended in future to fetch NBBO data
            )

            yield event

        # Handle pagination - detect infinite loops by tracking seen URLs
        seen_urls = {url}  # Track visited URLs to prevent circular pagination
        page_count = 1

        while data.get("next_url"):
            next_url = cast(str, data["next_url"])

            # Detect circular pagination (same URL appearing again)
            if next_url in seen_urls:
                logger.warning(f"Detected circular pagination for {symbol} - same URL appeared twice")
                break

            seen_urls.add(next_url)

            try:
                data = http_request_with_backoff(
                    request_func=partial(httpx.get, next_url, timeout=httpx.Timeout(30.0)),
                    retries=self.rate_limit_retries,
                    backoff=self.rate_limit_backoff,
                    backoff_multiplier=self.rate_limit_backoff_multiplier,
                    error_message="Failed to fetch data from Polygon",
                )

                # Check status on paginated response
                if data.get("status") != "OK":
                    logger.warning(f"Pagination request failed for {symbol}: {data.get('error', 'Unknown error')}")
                    break

                page_results = data.get("results", [])
                if not page_results:
                    break

                total_bars += len(page_results)

                # Process and yield results from this page
                for bar in page_results:
                    timestamp = datetime.fromtimestamp(bar["t"] / 1000, tz=timezone.utc).replace(tzinfo=None)
                    event = MarketDataEvent(
                        timestamp=timestamp,
                        symbol=symbol,
                        open=float(bar["o"]),
                        high=float(bar["h"]),
                        low=float(bar["l"]),
                        close=float(bar["c"]),
                        volume=int(bar["v"]),
                    )
                    yield event

                page_count += 1

            except ValueError as e:
                logger.warning(f"Failed to fetch page {page_count + 1} for {symbol}: {e}")
                break

        # Log summary
        logger.info(f"Loaded {total_bars} bars across {page_count} page(s) for {symbol}")
