"""
database.py - Database connection and session management.
Sets up SQLAlchemy engine with SQLite, creates all tables on startup,
and provides a FastAPI dependency for getting a database session.
"""

import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

# SQLite database file stored in /data so it persists in Docker via volume mount
DB_PATH = os.environ.get("DB_PATH", "./data/invoice.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

# connect_args required for SQLite to allow usage in multi-threaded FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def get_db():
    """
    FastAPI dependency that yields a database session.
    Ensures the session is always closed after the request.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables defined in the ORM models.
    Called once at application startup.
    """
    # Import models here to ensure they are registered with Base
    from models import User, Customer, Item, Invoice, InvoiceItem, Settings  # noqa
    Base.metadata.create_all(bind=engine)
