"""
database.py
-----------
Sets up the SQLAlchemy engine, session factory, and declarative base
used by the rest of the application.

For this prototype we use SQLite (file-based, zero-configuration).
The database URL is read from the .env file via python-dotenv so it
can be swapped later (e.g. to PostgreSQL) without changing code.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Load variables from .env into the process environment
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mctc_feedback.db")

# `check_same_thread` is required for SQLite when used with FastAPI,
# because FastAPI can access the DB from different threads.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    FastAPI dependency that yields a database session and guarantees
    it is closed after the request finishes, even if an error occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
