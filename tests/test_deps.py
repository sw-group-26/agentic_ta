"""Tests for dependency injection helpers (app.deps).

DB tests mock psycopg2.connect so no real PostgreSQL is required.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.deps import get_db, get_storage
from app.storage import LocalStorageAdapter


def test_get_db_yields_connection_and_closes():
    """get_db() should yield a connection and call close() on teardown."""
    mock_conn = MagicMock()

    with patch("app.deps.psycopg2.connect", return_value=mock_conn):
        gen = get_db()
        conn = next(gen)

        # Yielded object must be our mock connection
        assert conn is mock_conn
        # close() must not be called yet
        mock_conn.close.assert_not_called()

        # Exhaust the generator (simulates FastAPI teardown)
        try:
            next(gen)
        except StopIteration:
            pass

        # Now close() should have been called exactly once
        mock_conn.close.assert_called_once()


def test_get_storage_returns_adapter(monkeypatch):
    """get_storage() should return a LocalStorageAdapter instance."""
    monkeypatch.setenv("LOCAL_STORAGE_ROOT", "/tmp/test_storage")

    adapter = get_storage()

    assert isinstance(adapter, LocalStorageAdapter)
    assert str(adapter.root).endswith("test_storage")
