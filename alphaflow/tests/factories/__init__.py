"""Test data factories for creating test objects.

This module uses factory_boy to provide factories for generating
test data with sensible defaults and easy customization.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import factory
from factory.alchemy import SQLAlchemyModelFactory

from alphaflow.database.models import MarketDataModel, StrategyRunModel, TradeModel


class BaseFactory(SQLAlchemyModelFactory):
    """Base factory with common configuration."""

    class Meta:
        """Factory configuration."""

        abstract = True
        # Session will be set by the test fixture
        sqlalchemy_session = None
        sqlalchemy_session_persistence = "commit"


class MarketDataFactory(BaseFactory):
    """Factory for creating MarketDataModel instances.
    
    Usage:
        # Create with defaults
        market_data = MarketDataFactory(session=db_session)
        
        # Create with custom values
        market_data = MarketDataFactory(
            session=db_session,
            symbol="AAPL",
            close=150.0
        )
        
        # Create multiple instances
        market_data_list = MarketDataFactory.create_batch(
            10,
            session=db_session,
            symbol="AAPL"
        )
    """

    class Meta:
        """Factory configuration."""

        model = MarketDataModel

    timestamp = factory.LazyFunction(lambda: datetime.now(UTC) - timedelta(days=1))
    symbol = "TEST"
    open = 100.0
    high = 105.0
    low = 95.0
    close = 102.0
    volume = 1000000.0
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class StrategyRunFactory(BaseFactory):
    """Factory for creating StrategyRunModel instances.
    
    Usage:
        # Create a completed strategy run
        run = StrategyRunFactory(
            session=db_session,
            final_value=120000.0,
            sharpe_ratio=1.5
        )
    """

    class Meta:
        """Factory configuration."""

        model = StrategyRunModel

    strategy_name = "TestStrategy"
    start_timestamp = factory.LazyFunction(lambda: datetime.now(UTC) - timedelta(days=365))
    end_timestamp = factory.LazyFunction(lambda: datetime.now(UTC))
    initial_cash = 100000.0
    final_value = None
    sharpe_ratio = None
    max_drawdown = None
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


class TradeFactory(BaseFactory):
    """Factory for creating TradeModel instances.
    
    Usage:
        # Create a buy trade
        trade = TradeFactory(session=db_session, side="BUY")
        
        # Create a sell trade with commission
        trade = TradeFactory(
            session=db_session,
            side="SELL",
            commission=5.0
        )
    """

    class Meta:
        """Factory configuration."""

        model = TradeModel

    strategy_run_id = None
    timestamp = factory.LazyFunction(lambda: datetime.now(UTC))
    symbol = "TEST"
    side = "BUY"
    quantity = 100.0
    price = 100.0
    commission = 1.0
    created_at = factory.LazyFunction(lambda: datetime.now(UTC))


# Helper function to set session for all factories
def set_factory_session(session) -> None:
    """Set the database session for all factories.
    
    This is a convenience function to set the session on all factories at once.
    
    Args:
        session: SQLAlchemy session to use for factory operations.
    
    """
    MarketDataFactory._meta.sqlalchemy_session = session
    StrategyRunFactory._meta.sqlalchemy_session = session
    TradeFactory._meta.sqlalchemy_session = session
