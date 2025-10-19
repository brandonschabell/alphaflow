"""Example usage of database testing infrastructure.

This example demonstrates how to use the database testing infrastructure
for testing database-dependent components in AlphaFlow.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from alphaflow.database import get_session, init_db
from alphaflow.database.models import MarketDataModel, StrategyRunModel, TradeModel
from alphaflow.tests.factories import (
    MarketDataFactory,
    StrategyRunFactory,
    TradeFactory,
)


def example_basic_usage():
    """Example 1: Basic database operations."""
    print("\n=== Example 1: Basic Database Operations ===\n")
    
    # Initialize database (creates tables)
    init_db()
    
    # Use context manager for session
    with get_session() as session:
        # Create a market data record
        market_data = MarketDataModel(
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            open=150.0,
            high=155.0,
            low=148.0,
            close=153.0,
            volume=50000000.0,
        )
        session.add(market_data)
        session.commit()
        
        print(f"Created: {market_data}")
        
        # Query the record
        result = session.execute(
            select(MarketDataModel).where(MarketDataModel.symbol == "AAPL")
        ).scalar_one()
        
        print(f"Retrieved: {result}")


def example_using_factories():
    """Example 2: Using factories for test data generation."""
    print("\n=== Example 2: Using Factories ===\n")
    
    init_db()
    
    with get_session() as session:
        # Set session for factories
        MarketDataFactory._meta.sqlalchemy_session = session
        StrategyRunFactory._meta.sqlalchemy_session = session
        TradeFactory._meta.sqlalchemy_session = session
        
        # Create with defaults
        market_data = MarketDataFactory()
        print(f"Created with defaults: {market_data}")
        
        # Create with custom values
        custom_data = MarketDataFactory(symbol="GOOGL", close=2500.0)
        print(f"Created with custom values: {custom_data}")
        
        # Create batch
        batch = MarketDataFactory.create_batch(5, symbol="MSFT")
        print(f"Created batch of {len(batch)} records")
        
        # Create related objects
        run = StrategyRunFactory(strategy_name="BuyAndHold")
        trades = TradeFactory.create_batch(3, strategy_run_id=run.id, symbol="AAPL")
        print(f"Created strategy run with {len(trades)} trades")


def example_complex_queries():
    """Example 3: Complex database queries."""
    print("\n=== Example 3: Complex Queries ===\n")
    
    init_db()
    
    with get_session() as session:
        # Set up factories
        MarketDataFactory._meta.sqlalchemy_session = session
        
        # Create test data
        base_time = datetime.now(UTC)
        for days_ago in range(10):
            MarketDataFactory(
                symbol="AAPL",
                timestamp=base_time - timedelta(days=days_ago),
                close=150.0 + days_ago,
            )
        
        # Query with time range
        cutoff = base_time - timedelta(days=5)
        recent_data = session.execute(
            select(MarketDataModel)
            .where(MarketDataModel.symbol == "AAPL")
            .where(MarketDataModel.timestamp >= cutoff)
            .order_by(MarketDataModel.timestamp.desc())
        ).scalars().all()
        
        print(f"Found {len(recent_data)} records in last 5 days")
        for data in recent_data[:3]:
            print(f"  {data.timestamp.date()}: ${data.close}")


def example_strategy_tracking():
    """Example 4: Tracking strategy runs and trades."""
    print("\n=== Example 4: Strategy Run Tracking ===\n")
    
    init_db()
    
    with get_session() as session:
        # Set up factories
        StrategyRunFactory._meta.sqlalchemy_session = session
        TradeFactory._meta.sqlalchemy_session = session
        
        # Create a strategy run
        run = StrategyRunFactory(
            strategy_name="MomentumStrategy",
            start_timestamp=datetime.now(UTC) - timedelta(days=365),
            end_timestamp=datetime.now(UTC),
            initial_cash=100000.0,
        )
        print(f"Created strategy run: {run.strategy_name}")
        
        # Simulate some trades
        trades_data = [
            ("AAPL", "BUY", 100, 150.0),
            ("GOOGL", "BUY", 50, 2500.0),
            ("AAPL", "SELL", 50, 155.0),
            ("MSFT", "BUY", 75, 300.0),
        ]
        
        for symbol, side, quantity, price in trades_data:
            TradeFactory(
                strategy_run_id=run.id,
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                commission=1.0,
            )
        
        # Query trades for this run
        trades = session.execute(
            select(TradeModel).where(TradeModel.strategy_run_id == run.id)
        ).scalars().all()
        
        print(f"\nTrades for run {run.id}:")
        for trade in trades:
            print(f"  {trade.side} {trade.quantity} {trade.symbol} @ ${trade.price}")
        
        # Calculate total value
        total_bought = sum(t.quantity * t.price for t in trades if t.side == "BUY")
        total_sold = sum(t.quantity * t.price for t in trades if t.side == "SELL")
        print(f"\nTotal bought: ${total_bought:,.2f}")
        print(f"Total sold: ${total_sold:,.2f}")


def example_cleanup_and_testing():
    """Example 5: How transaction rollback works in tests."""
    print("\n=== Example 5: Transaction Rollback (Testing) ===\n")
    
    print("In actual tests, use the db_session fixture:")
    print("""
    def test_example(db_session):
        # This session automatically rolls back after the test
        market_data = MarketDataModel(...)
        db_session.add(market_data)
        db_session.commit()
        
        # Verify data
        assert market_data.id is not None
        
        # ← Automatic rollback happens here
        # No data persists to next test!
    """)
    
    print("\nFor manual cleanup in scripts:")
    init_db()
    
    with get_session() as session:
        # Create some data
        MarketDataFactory._meta.sqlalchemy_session = session
        MarketDataFactory.create_batch(5)
        
        # Explicit rollback
        session.rollback()
        
        # Data is not committed
        count = session.execute(select(MarketDataModel)).scalars().all()
        print(f"Records after rollback: {len(count)}")


def main():
    """Run all examples."""
    print("=" * 60)
    print("Database Testing Infrastructure - Usage Examples")
    print("=" * 60)
    
    try:
        example_basic_usage()
        example_using_factories()
        example_complex_queries()
        example_strategy_tracking()
        example_cleanup_and_testing()
        
        print("\n" + "=" * 60)
        print("All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
