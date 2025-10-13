from collections.abc import Generator
from datetime import datetime
import logging
import os

import requests

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class AlphaVantageFeed(DataFeed):
    def __init__(
        self,
        use_cache: bool = False,
        api_key: str | None = None,
    ) -> None:
        self._use_cache = use_cache
        self.__api_key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        if self._use_cache:
            raise NotImplementedError("Cache not implemented yet")
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&apikey={self.__api_key}&outputsize=full"
            logger.debug(f"Fetching data from {url}")
            response = requests.get(url)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch data: {response.text}")
            data = response.json()
            for date, datum in data["Time Series (Daily)"].items():
                event = MarketDataEvent(
                    timestamp=datetime.strptime(date, "%Y-%m-%d"),
                    symbol=symbol,
                    open=float(datum["1. open"]),
                    high=float(datum["2. high"]),
                    low=float(datum["3. low"]),
                    close=float(datum["5. adjusted close"]),
                    volume=float(datum["6. volume"]),
                )
                if start_timestamp is not None and event.timestamp < start_timestamp:
                    continue
                if end_timestamp is not None and event.timestamp > end_timestamp:
                    continue
                yield event
