"""CSV file data feed implementation."""

import logging
from pathlib import Path

from typing_extensions import deprecated

from alphaflow.data_feeds.polars_data_feed import PolarsDataFeed

logger = logging.getLogger(__name__)


@deprecated("CSVDataFeed is deprecated and will be removed in a future release. Please use PolarsDataFeed instead.")
class CSVDataFeed(PolarsDataFeed):
    """Data feed that loads market data from CSV files."""

    def __init__(
        self,
        file_path: Path | str,
        *,
        col_timestamp: str = "Date",
        col_symbol: str = "Symbol",
        col_open: str = "Open",
        col_high: str = "High",
        col_low: str = "Low",
        col_close: str = "Close",
        col_volume: str = "Volume",
    ) -> None:
        """Initialize the CSV data feed.

        **Deprecated**: Use PolarsDataFeed instead.

        Args:
            file_path: Path to the CSV file containing market data.
            col_timestamp: Name of the timestamp column.
            col_symbol: Name of the symbol column.
            col_open: Name of the open price column.
            col_high: Name of the high price column.
            col_low: Name of the low price column.
            col_close: Name of the close price column.
            col_volume: Name of the volume column.

        """
        self.file_path = Path(file_path) if isinstance(file_path, str) else file_path
        super().__init__(
            df_or_file_path=file_path,
            col_timestamp=col_timestamp,
            col_symbol=col_symbol,
            col_open=col_open,
            col_high=col_high,
            col_low=col_low,
            col_close=col_close,
            col_volume=col_volume,
        )
