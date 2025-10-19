"""Example database models for demonstration purposes.

These models serve as examples of how to use the database infrastructure
and can be used as templates for creating application-specific models.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import DateTime, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from alphaflow.database.base import Base


class MarketDataModel(Base):
    """Example model for storing market data in the database.
    
    This demonstrates how to persist market data events to a database
    instead of only using CSV files.
    """

    __tablename__ = "market_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    open: Mapped[float] = mapped_column(Float, nullable=False)
    high: Mapped[float] = mapped_column(Float, nullable=False)
    low: Mapped[float] = mapped_column(Float, nullable=False)
    close: Mapped[float] = mapped_column(Float, nullable=False)
    volume: Mapped[float] = mapped_column(Float, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<MarketDataModel(symbol={self.symbol}, timestamp={self.timestamp}, close={self.close})>"


class StrategyRunModel(Base):
    """Example model for storing strategy backtest runs.
    
    This demonstrates how to persist backtest results and metadata.
    """

    __tablename__ = "strategy_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_name: Mapped[str] = mapped_column(String(100), nullable=False)
    start_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    end_timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    initial_cash: Mapped[float] = mapped_column(Float, nullable=False)
    final_value: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    sharpe_ratio: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_drawdown: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<StrategyRunModel(strategy={self.strategy_name}, id={self.id})>"


class TradeModel(Base):
    """Example model for storing individual trades.
    
    This demonstrates how to persist trade history for analysis.
    """

    __tablename__ = "trades"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_run_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False, index=True)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    side: Mapped[str] = mapped_column(String(10), nullable=False)  # "BUY" or "SELL"
    quantity: Mapped[float] = mapped_column(Float, nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)
    commission: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    def __repr__(self) -> str:
        """Return string representation of the model."""
        return f"<TradeModel(symbol={self.symbol}, side={self.side}, qty={self.quantity})>"
