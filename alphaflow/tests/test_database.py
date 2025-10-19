"""Tests for database infrastructure.

These tests demonstrate and validate the database testing infrastructure
including fixtures, transaction rollback, and test data factories.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from alphaflow.database.models import MarketDataModel, StrategyRunModel, TradeModel
from alphaflow.tests.factories import (
    MarketDataFactory,
    StrategyRunFactory,
    TradeFactory,
)


class TestDatabaseFixtures:
    """Test database fixtures and session management."""

    def test_db_session_fixture_available(self, db_session) -> None:
        """Test that db_session fixture is available."""
        assert db_session is not None
        assert hasattr(db_session, "add")
        assert hasattr(db_session, "commit")
        assert hasattr(db_session, "rollback")

    def test_transaction_rollback_isolation(self, db_session) -> None:
        """Test that changes are rolled back between tests.
        
        This test creates a record, and subsequent tests should not see it
        due to transaction rollback.
        """
        # Create a record with a unique symbol
        market_data = MarketDataModel(
            timestamp=datetime.now(UTC),
            symbol="ROLLBACK_TEST_1",
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000.0,
        )
        db_session.add(market_data)
        db_session.commit()
        
        # Verify it exists
        result = db_session.execute(
            select(MarketDataModel).where(MarketDataModel.symbol == "ROLLBACK_TEST_1")
        ).scalar_one()
        assert result.symbol == "ROLLBACK_TEST_1"

    def test_transaction_rollback_verification(self, db_session) -> None:
        """Test that previous test's data was rolled back.
        
        This test verifies isolation by checking that data from the
        previous test doesn't exist.
        """
        # Query for data from previous test
        result = db_session.execute(
            select(MarketDataModel).where(MarketDataModel.symbol == "ROLLBACK_TEST_1")
        ).scalar_one_or_none()
        
        # Should be None due to rollback
        assert result is None


class TestMarketDataModel:
    """Test MarketDataModel CRUD operations."""

    def test_create_market_data(self, db_session) -> None:
        """Test creating a market data record."""
        timestamp = datetime.now(UTC)
        market_data = MarketDataModel(
            timestamp=timestamp,
            symbol="AAPL",
            open=150.0,
            high=155.0,
            low=148.0,
            close=153.0,
            volume=50000000.0,
        )
        
        db_session.add(market_data)
        db_session.commit()
        
        assert market_data.id is not None
        assert market_data.symbol == "AAPL"
        assert market_data.close == 153.0

    def test_query_market_data_by_symbol(self, db_session) -> None:
        """Test querying market data by symbol."""
        # Create test data with unique symbols for this test
        for symbol in ["QUERY_TEST_AAPL", "QUERY_TEST_GOOGL", "QUERY_TEST_MSFT"]:
            market_data = MarketDataModel(
                timestamp=datetime.now(UTC),
                symbol=symbol,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000.0,
            )
            db_session.add(market_data)
        db_session.commit()
        
        # Query for QUERY_TEST_AAPL
        results = db_session.execute(
            select(MarketDataModel).where(MarketDataModel.symbol == "QUERY_TEST_AAPL")
        ).scalars().all()
        
        assert len(results) == 1
        assert results[0].symbol == "QUERY_TEST_AAPL"

    def test_query_market_data_by_timestamp_range(self, db_session) -> None:
        """Test querying market data within a timestamp range."""
        base_time = datetime.now(UTC)
        test_symbol = "TIMESTAMP_TEST_AAPL"
        
        # Create data for different days
        for days_ago in range(5):
            market_data = MarketDataModel(
                timestamp=base_time - timedelta(days=days_ago),
                symbol=test_symbol,
                open=100.0,
                high=105.0,
                low=95.0,
                close=102.0,
                volume=1000000.0,
            )
            db_session.add(market_data)
        db_session.commit()
        
        # Query for last 3 days
        cutoff = base_time - timedelta(days=2)
        results = db_session.execute(
            select(MarketDataModel)
            .where(MarketDataModel.timestamp >= cutoff)
            .where(MarketDataModel.symbol == test_symbol)
        ).scalars().all()
        
        assert len(results) == 3


class TestStrategyRunModel:
    """Test StrategyRunModel CRUD operations."""

    def test_create_strategy_run(self, db_session) -> None:
        """Test creating a strategy run record."""
        run = StrategyRunModel(
            strategy_name="BuyAndHold",
            start_timestamp=datetime.now(UTC) - timedelta(days=365),
            end_timestamp=datetime.now(UTC),
            initial_cash=100000.0,
            final_value=120000.0,
            sharpe_ratio=1.5,
            max_drawdown=-0.15,
        )
        
        db_session.add(run)
        db_session.commit()
        
        assert run.id is not None
        assert run.strategy_name == "BuyAndHold"
        assert run.final_value == 120000.0

    def test_update_strategy_run_results(self, db_session) -> None:
        """Test updating strategy run with results."""
        # Create initial run without results
        run = StrategyRunModel(
            strategy_name="TestStrategy",
            start_timestamp=datetime.now(UTC) - timedelta(days=365),
            end_timestamp=datetime.now(UTC),
            initial_cash=100000.0,
        )
        db_session.add(run)
        db_session.commit()
        
        run_id = run.id
        
        # Update with results
        run.final_value = 115000.0
        run.sharpe_ratio = 1.2
        run.max_drawdown = -0.10
        db_session.commit()
        
        # Verify update
        updated_run = db_session.get(StrategyRunModel, run_id)
        assert updated_run.final_value == 115000.0
        assert updated_run.sharpe_ratio == 1.2


class TestTradeModel:
    """Test TradeModel CRUD operations."""

    def test_create_trade(self, db_session) -> None:
        """Test creating a trade record."""
        trade = TradeModel(
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            side="BUY",
            quantity=100.0,
            price=150.0,
            commission=1.0,
        )
        
        db_session.add(trade)
        db_session.commit()
        
        assert trade.id is not None
        assert trade.symbol == "AAPL"
        assert trade.side == "BUY"

    def test_query_trades_by_strategy_run(self, db_session) -> None:
        """Test querying trades associated with a strategy run."""
        # Create a strategy run
        run = StrategyRunModel(
            strategy_name="TestStrategy",
            start_timestamp=datetime.now(UTC) - timedelta(days=365),
            end_timestamp=datetime.now(UTC),
            initial_cash=100000.0,
        )
        db_session.add(run)
        db_session.commit()
        
        # Create trades for this run
        for i in range(3):
            trade = TradeModel(
                strategy_run_id=run.id,
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                side="BUY" if i % 2 == 0 else "SELL",
                quantity=100.0,
                price=150.0 + i,
                commission=1.0,
            )
            db_session.add(trade)
        db_session.commit()
        
        # Query trades for this run
        results = db_session.execute(
            select(TradeModel).where(TradeModel.strategy_run_id == run.id)
        ).scalars().all()
        
        assert len(results) == 3


class TestFactories:
    """Test factory_boy factories for generating test data."""

    def test_market_data_factory_defaults(self, db_session) -> None:
        """Test MarketDataFactory with default values."""
        MarketDataFactory._meta.sqlalchemy_session = db_session
        market_data = MarketDataFactory()
        
        assert market_data.id is not None
        assert market_data.symbol == "TEST"
        assert market_data.open == 100.0
        assert market_data.close == 102.0

    def test_market_data_factory_custom_values(self, db_session) -> None:
        """Test MarketDataFactory with custom values."""
        MarketDataFactory._meta.sqlalchemy_session = db_session
        market_data = MarketDataFactory(
            symbol="AAPL",
            close=150.0,
        )
        
        assert market_data.symbol == "AAPL"
        assert market_data.close == 150.0

    def test_market_data_factory_batch(self, db_session) -> None:
        """Test creating multiple market data records with factory."""
        MarketDataFactory._meta.sqlalchemy_session = db_session
        market_data_list = MarketDataFactory.create_batch(5, symbol="AAPL")
        
        assert len(market_data_list) == 5
        for item in market_data_list:
            assert item.symbol == "AAPL"
            assert item.id is not None

    def test_strategy_run_factory(self, db_session) -> None:
        """Test StrategyRunFactory."""
        StrategyRunFactory._meta.sqlalchemy_session = db_session
        run = StrategyRunFactory(
            strategy_name="TestStrategy",
            final_value=120000.0,
            sharpe_ratio=1.5,
        )
        
        assert run.id is not None
        assert run.strategy_name == "TestStrategy"
        assert run.final_value == 120000.0

    def test_trade_factory(self, db_session) -> None:
        """Test TradeFactory."""
        TradeFactory._meta.sqlalchemy_session = db_session
        trade = TradeFactory(
            symbol="AAPL",
            side="BUY",
            quantity=100.0,
            price=150.0,
        )
        
        assert trade.id is not None
        assert trade.symbol == "AAPL"
        assert trade.side == "BUY"

    def test_factory_with_relationships(self, db_session) -> None:
        """Test factories creating related objects."""
        StrategyRunFactory._meta.sqlalchemy_session = db_session
        TradeFactory._meta.sqlalchemy_session = db_session
        
        # Create a strategy run
        run = StrategyRunFactory(strategy_name="TestStrategy")
        
        # Create trades for this run
        trades = TradeFactory.create_batch(3, strategy_run_id=run.id)
        
        assert len(trades) == 3
        for trade in trades:
            assert trade.strategy_run_id == run.id


class TestDatabaseSessionManagement:
    """Test different aspects of database session management."""

    def test_commit_in_transaction(self, db_session) -> None:
        """Test that commit works within transaction."""
        market_data = MarketDataModel(
            timestamp=datetime.now(UTC),
            symbol="COMMIT_TEST_1",
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000.0,
        )
        db_session.add(market_data)
        db_session.commit()
        
        # Should be able to query it within same test
        result = db_session.execute(
            select(MarketDataModel).where(MarketDataModel.symbol == "COMMIT_TEST_1")
        ).scalar_one()
        assert result is not None

    def test_rollback_in_transaction(self, db_session) -> None:
        """Test explicit rollback within transaction."""
        market_data = MarketDataModel(
            timestamp=datetime.now(UTC),
            symbol="ROLLBACK_TEST_2",
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000.0,
        )
        db_session.add(market_data)
        db_session.rollback()
        
        # Should not exist after rollback
        result = db_session.execute(
            select(MarketDataModel).where(MarketDataModel.symbol == "ROLLBACK_TEST_2")
        ).scalar_one_or_none()
        assert result is None

    def test_multiple_commits(self, db_session) -> None:
        """Test multiple commits in same test."""
        # First commit
        market_data1 = MarketDataModel(
            timestamp=datetime.now(UTC),
            symbol="MULTI_COMMIT_AAPL",
            open=100.0,
            high=105.0,
            low=95.0,
            close=102.0,
            volume=1000000.0,
        )
        db_session.add(market_data1)
        db_session.commit()
        
        # Second commit
        market_data2 = MarketDataModel(
            timestamp=datetime.now(UTC),
            symbol="MULTI_COMMIT_GOOGL",
            open=200.0,
            high=205.0,
            low=195.0,
            close=202.0,
            volume=2000000.0,
        )
        db_session.add(market_data2)
        db_session.commit()
        
        # Both should exist
        results = db_session.execute(
            select(MarketDataModel).where(
                MarketDataModel.symbol.in_(["MULTI_COMMIT_AAPL", "MULTI_COMMIT_GOOGL"])
            )
        ).scalars().all()
        assert len(results) == 2
