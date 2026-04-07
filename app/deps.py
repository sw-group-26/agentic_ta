"""Dependency Injection Helpers for DB and Storage.

Generator-based DI for use with FastAPI's Depends().
Replace this module when Colleague A provides a shared DI layer.

Usage::

    from app.deps import get_db, get_storage

    @router.get("/example")
    def example(
        conn=Depends(get_db),
        storage=Depends(get_storage),
    ):
        ...
"""

from __future__ import annotations

import os
from collections.abc import Generator

import psycopg2
import psycopg2.extensions
from dotenv import load_dotenv

from app.storage import LocalStorageAdapter

# Load .env file once at module level
load_dotenv()


def get_db() -> Generator[psycopg2.extensions.connection, None, None]:
    """DB connection dependency.

    Yields a psycopg2 connection and closes it on teardown.
    Used with FastAPI's Depends() yield pattern.

    Yields:
        psycopg2 connection object.

    Raises:
        psycopg2.OperationalError: If the DB connection fails.
    """
    conn = psycopg2.connect(os.getenv("DATABASE_URL"))
    try:
        yield conn
    finally:
        conn.close()


def get_storage() -> LocalStorageAdapter:
    """Storage adapter dependency.

    Returns a LocalStorageAdapter instance using LOCAL_STORAGE_ROOT.
    Defaults to ./storage if not set.

    Returns:
        LocalStorageAdapter instance.
    """
    root = os.getenv("LOCAL_STORAGE_ROOT", "./storage")
    return LocalStorageAdapter(root)
