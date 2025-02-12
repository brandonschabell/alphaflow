from collections.abc import Generator
from datetime import datetime
import logging
import os

import requests

from alphaflow import DataFeed
from alphaflow.events.market_data_event import MarketDataEvent

logger = logging.getLogger(__name__)


class FMPDataFeed(DataFeed):
    def __init__(
        self,
        use_cache: bool = False,
        api_key: str | None = None,
    ) -> None:
        self._use_cache = use_cache
        self.__api_key = api_key or os.getenv("FMP_API_KEY")

    def run(
        self,
        symbol: str,
        start_timestamp: datetime | None,
        end_timestamp: datetime | None,
    ) -> Generator[MarketDataEvent, None, None]:
        if self._use_cache:
            raise NotImplementedError("Cache not implemented yet")
        else:
            url = f"https://financialmodelingprep.com/stable/historical-price-eod/dividend-adjusted?symbol={symbol}&apikey={self.__api_key}"
            if start_timestamp:
                url += f"&from={start_timestamp.date()}"
            if end_timestamp:
                url += f"&to={end_timestamp.date()}"
            logger.debug(f"Fetching data from {url}")
            response = requests.get(url)
            if response.status_code != 200:
                raise ValueError(f"Failed to fetch data: {response.text}")
            data = response.json()
            for row in data:
                event = MarketDataEvent(
                    timestamp=datetime.strptime(row["date"], "%Y-%m-%d"),
                    symbol=symbol,
                    open=row["adjOpen"],
                    high=row["adjHigh"],
                    low=row["adjLow"],
                    close=row["adjClose"],
                    volume=row["volume"],
                )
                yield event
