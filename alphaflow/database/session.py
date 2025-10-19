"""Database session management."""

from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from alphaflow.database.base import Base

# Default to SQLite for local development
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./alphaflow.db")

# Create engine with appropriate settings
engine = create_engine(
    DATABASE_URL,
    # SQLite-specific settings
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
    # Echo SQL queries for debugging (disable in production)
    echo=False,
)

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    """Initialize database by creating all tables.
    
    This should be called once at application startup.
    """
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Get a database session with automatic cleanup.
    
    Usage:
        with get_session() as session:
            # Use session here
            session.add(obj)
            session.commit()
    
    Yields:
        Session: SQLAlchemy session object.
    
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
