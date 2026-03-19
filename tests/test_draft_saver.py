"""Unit tests for Draft Saver (Step 8).

Tests use unittest.mock to simulate a psycopg2 connection — no real DB required.

Tests:
    1. test_save_draft_inserts_feedback_draft_and_evidence
       : Verify INSERT into llm_feedback_draft and llm_evidence when evidence present.
    2. test_save_draft_with_empty_evidence_does_not_raise
       : Verify no error and draft_id returned when evidence list is empty.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import MagicMock

import pytest

from app.services.draft_saver import save_draft

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------

SAMPLE_SUBMISSION_ID = "cbca2439-5fa7-4a69-b4d5-57515f2ca8df"

SAMPLE_DRAFT_ID = str(uuid.uuid4())


@pytest.fixture
def sample_result() -> dict[str, Any]:
    """Minimal result dict matching generate_feedback() output shape."""
    return {
        "draft_text": "All tests passed. Well-structured code.",
        "confidence": 0.85,
        "model_name": "llama3.2",
        "prompt_version": "v1.0",
        "evidence": [
            {
                "type": "test_run",
                "pointer": "test_run:abc123",
                "snippet": "all 5 tests passed",
            },
            {
                "type": "code_snippet",
                "pointer": "file:hw1_solution.py#L1-L10",
                "snippet": "def solve():",
            },
        ],
    }


@pytest.fixture
def mock_conn() -> MagicMock:
    """Mock psycopg2 connection with cursor context manager support."""
    conn = MagicMock()
    cursor = MagicMock()

    # cursor().__enter__ returns cursor itself
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)

    # fetchone() returns draft_id UUID as first call
    cursor.fetchone.return_value = (uuid.UUID(SAMPLE_DRAFT_ID),)

    conn.cursor.return_value = cursor
    return conn


# ---------------------------------------------------------------------------
# Test 1: Verify INSERT calls when evidence is present
# ---------------------------------------------------------------------------


def test_save_draft_inserts_feedback_draft_and_evidence(
    mock_conn: MagicMock,
    sample_result: dict[str, Any],
) -> None:
    """Verify that save_draft inserts to llm_feedback_draft and llm_evidence.

    Verifies:
    - execute() called once for llm_feedback_draft INSERT
    - executemany() called once for llm_evidence INSERT (evidence items > 0)
    - INSERT parameters match the result dict
    - returned draft_id matches the mocked DB response
    """
    draft_id = save_draft(SAMPLE_SUBMISSION_ID, sample_result, mock_conn)

    cursor = mock_conn.cursor.return_value.__enter__.return_value

    # Verify llm_feedback_draft INSERT called exactly once
    assert cursor.execute.call_count == 1
    execute_args = cursor.execute.call_args[0]
    assert "llm_feedback_draft" in execute_args[0]

    # Verify INSERT parameters
    params = execute_args[1]
    assert params[0] == SAMPLE_SUBMISSION_ID
    assert params[1] == sample_result["model_name"]
    assert params[2] == sample_result["prompt_version"]
    assert params[3] == sample_result["draft_text"]
    assert params[4] == sample_result["confidence"]

    # Verify llm_evidence INSERT via executemany
    assert cursor.executemany.call_count == 1
    executemany_args = cursor.executemany.call_args[0]
    assert "llm_evidence" in executemany_args[0]
    rows = executemany_args[1]
    assert len(rows) == len(sample_result["evidence"])

    # Verify commit was called
    mock_conn.commit.assert_called_once()

    # Verify returned draft_id is a UUID string
    assert draft_id == SAMPLE_DRAFT_ID


# ---------------------------------------------------------------------------
# Test 2: Empty evidence list — executemany should not be called
# ---------------------------------------------------------------------------


def test_save_draft_with_empty_evidence_does_not_raise(
    mock_conn: MagicMock,
    sample_result: dict[str, Any],
) -> None:
    """Verify no exception when evidence list is empty, and executemany is skipped.

    Verifies:
    - No exception raised when evidence list is empty
    - execute() called once (llm_feedback_draft INSERT only)
    - executemany() NOT called (no evidence rows to insert)
    - draft_id returned correctly
    """
    sample_result["evidence"] = []

    draft_id = save_draft(SAMPLE_SUBMISSION_ID, sample_result, mock_conn)

    cursor = mock_conn.cursor.return_value.__enter__.return_value

    # Only llm_feedback_draft INSERT should be called
    assert cursor.execute.call_count == 1

    # No evidence rows — executemany must not be called
    cursor.executemany.assert_not_called()

    # Commit still called
    mock_conn.commit.assert_called_once()

    # draft_id returned correctly
    assert draft_id == SAMPLE_DRAFT_ID
