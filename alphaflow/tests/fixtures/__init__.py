"""Pytest fixtures for database testing.

This module provides reusable fixtures for testing database functionality
with proper isolation using transaction rollback.
"""

from __future__ import annotations

from collections.abc import Generator

import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker

from alphaflow.database.base import Base


@pytest.fixture(scope="session")
def test_engine():
    """Create a test database engine for the entire test session.
    
    Uses an in-memory SQLite database for fast, isolated testing.
    
    Returns:
        SQLAlchemy Engine instance.
    
    """
    # Use in-memory SQLite for tests - fast and isolated
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        echo=False,  # Set to True for debugging SQL queries
    )
    
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    # Cleanup: drop all tables after tests
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """Create a database session with automatic transaction rollback.
    
    This fixture ensures test isolation by rolling back all changes after
    each test. No data persists between tests.
    
    Usage:
        def test_example(db_session):
            user = User(name="test")
            db_session.add(user)
            db_session.commit()
            # Changes will be rolled back after test
    
    Args:
        test_engine: Test database engine from session fixture.
    
    Yields:
        SQLAlchemy Session with automatic rollback.
    
    """
    # Start a connection
    connection = test_engine.connect()
    
    # Begin a transaction (this is the outer transaction that will be rolled back)
    transaction = connection.begin()
    
    # Create a session bound to the connection
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestSessionLocal()
    
    # Begin a nested transaction (savepoint) for the session
    nested = connection.begin_nested()
    
    # Each time the SAVEPOINT ends, reopen it
    @event.listens_for(session, "after_transaction_end")
    def restart_savepoint(session, transaction):
        """Restart a savepoint after transaction end."""
        if transaction.nested and not transaction._parent.nested:
            # Make sure we're still in a transaction
            if connection.in_transaction():
                session.begin_nested()
    
    yield session
    
    # Cleanup: rollback everything
    session.close()
    
    # Rollback the outer transaction (this undoes everything)
    if transaction.is_active:
        transaction.rollback()
    
    connection.close()


@pytest.fixture(scope="function")
def db_session_no_rollback(test_engine) -> Generator[Session, None, None]:
    """Create a database session without automatic rollback.
    
    Use this fixture when you need changes to persist within a test
    or when testing transaction behavior itself.
    
    Args:
        test_engine: Test database engine from session fixture.
    
    Yields:
        SQLAlchemy Session without automatic rollback.
    
    """
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()
    
    yield session
    
    # Cleanup: close the session
    session.close()
