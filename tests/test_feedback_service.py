"""Unit tests for Feedback Service Layer (Sprint 3, Step 3).

Tests use unittest.mock to simulate psycopg2 — no real DB required.

Tests:
    1. test_list_drafts_returns_drafts_for_submission
    2. test_get_draft_detail_includes_evidence
    3. test_get_draft_detail_raises_on_missing_draft
    4. test_approve_draft_transitions_pending_to_approved
    5. test_approve_draft_rejects_non_pending_status
    6. test_publish_draft_transitions_approved_to_published
    7. test_publish_draft_rejects_non_approved_status
    8. test_trigger_feedback_generation_calls_pipeline
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from app.services.feedback_service import (
    approve_draft,
    get_draft_detail,
    list_drafts,
    publish_draft,
    trigger_feedback_generation,
)

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SAMPLE_SUBMISSION_ID = "cbca2439-5fa7-4a69-b4d5-57515f2ca8df"
SAMPLE_DRAFT_ID = str(uuid.uuid4())
SAMPLE_TA_ID = str(uuid.uuid4())
SAMPLE_VERSION_ID = str(uuid.uuid4())
NOW = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)

# Column descriptions matching SELECT queries (cursor.description format)
DRAFT_COLUMNS = [
    ("draft_id",),
    ("submission_id",),
    ("version_id",),
    ("model_name",),
    ("prompt_version",),
    ("generated_at",),
    ("draft_text",),
    ("confidence",),
    ("status",),
    ("approved_by",),
    ("approved_at",),
    ("published_at",),
]

EVIDENCE_COLUMNS = [
    ("evidence_id",),
    ("evidence_type",),
    ("pointer",),
    ("snippet",),
]

# A sample draft row tuple (matches DRAFT_COLUMNS order)
SAMPLE_DRAFT_ROW = (
    uuid.UUID(SAMPLE_DRAFT_ID),
    uuid.UUID(SAMPLE_SUBMISSION_ID),
    uuid.UUID(SAMPLE_VERSION_ID),
    "llama3.2",
    "v1.0",
    NOW,
    "Good work. All tests passed.",
    Decimal("0.850"),
    "pending",
    None,
    None,
    None,
)

SAMPLE_EVIDENCE_ROW = (
    uuid.uuid4(),
    "test_run",
    "test_run:abc123",
    "all 5 tests passed",
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_conn() -> MagicMock:
    """Mock psycopg2 connection with cursor context manager support."""
    conn = MagicMock()
    cursor = MagicMock()

    # Support `with conn.cursor() as cur:` pattern
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)

    conn.cursor.return_value = cursor
    return conn


# ---------------------------------------------------------------------------
# Test 1: list_drafts
# ---------------------------------------------------------------------------


def test_list_drafts_returns_drafts_for_submission(
    mock_conn: MagicMock,
) -> None:
    """Verify list_drafts returns draft dicts for a given submission."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.description = DRAFT_COLUMNS
    cursor.fetchall.return_value = [SAMPLE_DRAFT_ROW, SAMPLE_DRAFT_ROW]

    result = list_drafts(SAMPLE_SUBMISSION_ID, mock_conn)

    # Returns a list of 2 dicts
    assert len(result) == 2
    assert isinstance(result[0], dict)
    assert result[0]["draft_id"] == SAMPLE_DRAFT_ID
    assert result[0]["status"] == "pending"

    # SQL includes WHERE and ORDER BY
    sql = cursor.execute.call_args[0][0]
    assert "WHERE submission_id" in sql
    assert "ORDER BY generated_at DESC" in sql

    # Read-only — no commit
    mock_conn.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Test 2: get_draft_detail with evidence
# ---------------------------------------------------------------------------


def test_get_draft_detail_includes_evidence(
    mock_conn: MagicMock,
) -> None:
    """Verify get_draft_detail returns draft dict with evidence list."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    # Track execute calls to set cursor.description per query
    descriptions = [DRAFT_COLUMNS, EVIDENCE_COLUMNS]
    call_count = {"n": 0}

    def _set_description(*args):
        cursor.description = descriptions[call_count["n"]]
        call_count["n"] += 1

    cursor.execute.side_effect = _set_description
    cursor.fetchone.return_value = SAMPLE_DRAFT_ROW
    cursor.fetchall.return_value = [SAMPLE_EVIDENCE_ROW]

    result = get_draft_detail(SAMPLE_DRAFT_ID, mock_conn)

    # Draft fields present
    assert result["draft_id"] == SAMPLE_DRAFT_ID
    assert result["draft_text"] == "Good work. All tests passed."

    # Evidence list included
    assert "evidence" in result
    assert len(result["evidence"]) == 1
    assert result["evidence"][0]["evidence_type"] == "test_run"

    # Two queries executed (draft + evidence)
    assert cursor.execute.call_count == 2

    # Read-only — no commit
    mock_conn.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Test 3: get_draft_detail — missing draft
# ---------------------------------------------------------------------------


def test_get_draft_detail_raises_on_missing_draft(
    mock_conn: MagicMock,
) -> None:
    """Verify ValueError when draft_id does not exist."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.description = DRAFT_COLUMNS
    cursor.fetchone.return_value = None

    with pytest.raises(ValueError, match="draft not found"):
        get_draft_detail(SAMPLE_DRAFT_ID, mock_conn)


# ---------------------------------------------------------------------------
# Test 4: approve_draft — happy path
# ---------------------------------------------------------------------------


def test_approve_draft_transitions_pending_to_approved(
    mock_conn: MagicMock,
) -> None:
    """Verify approve_draft transitions pending -> approved."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    # Build approved row (status changed, approved_by/at set)
    approved_row = list(SAMPLE_DRAFT_ROW)
    approved_row[7] = "approved"  # status
    approved_row[8] = uuid.UUID(SAMPLE_TA_ID)  # approved_by
    approved_row[9] = NOW  # approved_at
    approved_row[8] = "approved"  # status
    approved_row[9] = uuid.UUID(SAMPLE_TA_ID)  # approved_by
    approved_row[10] = NOW  # approved_at
    approved_row = tuple(approved_row)

    # First fetchone: SELECT FOR UPDATE -> current status
    # Second fetchone: RETURNING -> updated row
    descriptions = [
        [("status",)],  # SELECT FOR UPDATE result
        DRAFT_COLUMNS,  # RETURNING result
    ]
    call_count = {"n": 0}

    def _set_description(*args):
        cursor.description = descriptions[call_count["n"]]
        call_count["n"] += 1

    cursor.execute.side_effect = _set_description
    cursor.fetchone.side_effect = [("pending",), approved_row]

    result = approve_draft(SAMPLE_DRAFT_ID, SAMPLE_TA_ID, mock_conn)

    assert result["status"] == "approved"
    assert result["approved_by"] == SAMPLE_TA_ID
    mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Test 5: approve_draft — reject non-pending
# ---------------------------------------------------------------------------


def test_approve_draft_rejects_non_pending_status(
    mock_conn: MagicMock,
) -> None:
    """Verify ValueError when trying to approve a non-pending draft."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.description = [("status",)]
    cursor.fetchone.return_value = ("approved",)

    with pytest.raises(ValueError, match="cannot approve"):
        approve_draft(SAMPLE_DRAFT_ID, SAMPLE_TA_ID, mock_conn)

    mock_conn.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Test 6: publish_draft — happy path
# ---------------------------------------------------------------------------


def test_publish_draft_transitions_approved_to_published(
    mock_conn: MagicMock,
) -> None:
    """Verify publish_draft transitions approved -> published."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value

    # Build published row
    published_row = list(SAMPLE_DRAFT_ROW)
    published_row[7] = "published"  # status
    published_row[8] = uuid.UUID(SAMPLE_TA_ID)  # approved_by
    published_row[9] = NOW  # approved_at
    published_row[10] = NOW  # published_at
    published_row[8] = "published"  # status
    published_row[9] = uuid.UUID(SAMPLE_TA_ID)  # approved_by
    published_row[10] = NOW  # approved_at
    published_row[11] = NOW  # published_at
    published_row = tuple(published_row)

    descriptions = [
        [("status",)],
        DRAFT_COLUMNS,
    ]
    call_count = {"n": 0}

    def _set_description(*args):
        cursor.description = descriptions[call_count["n"]]
        call_count["n"] += 1

    cursor.execute.side_effect = _set_description
    cursor.fetchone.side_effect = [("approved",), published_row]

    result = publish_draft(SAMPLE_DRAFT_ID, mock_conn)

    assert result["status"] == "published"
    assert result["published_at"] is not None
    mock_conn.commit.assert_called_once()


# ---------------------------------------------------------------------------
# Test 7: publish_draft — reject non-approved
# ---------------------------------------------------------------------------


def test_publish_draft_rejects_non_approved_status(
    mock_conn: MagicMock,
) -> None:
    """Verify ValueError when trying to publish a non-approved draft."""
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.description = [("status",)]
    cursor.fetchone.return_value = ("pending",)

    with pytest.raises(ValueError, match="cannot publish"):
        publish_draft(SAMPLE_DRAFT_ID, mock_conn)

    mock_conn.commit.assert_not_called()


# ---------------------------------------------------------------------------
# Test 8: trigger_feedback_generation — pipeline orchestration
# ---------------------------------------------------------------------------


@patch("app.services.feedback_service._resolve_target_version_id")
@patch("app.services.feedback_service.save_draft")
@patch("app.services.feedback_service.generate_feedback")
@patch("app.services.feedback_service.build_feedback_packet")
def test_trigger_feedback_generation_calls_pipeline(
    mock_build: MagicMock,
    mock_generate: MagicMock,
    mock_save: MagicMock,
    mock_resolve: MagicMock,
    mock_conn: MagicMock,
) -> None:
    """Verify trigger calls build -> generate -> save in order."""
    mock_storage = MagicMock()
    mock_build.return_value = {"assignment_title": "HW1", "rubric": []}
    mock_generate.return_value = {
        "draft_text": "Good work.",
        "confidence": 0.85,
        "model_name": "llama3.2",
        "prompt_version": "v1.0",
        "evidence": [],
    }
    mock_save.return_value = SAMPLE_DRAFT_ID

    draft_id = trigger_feedback_generation(
        SAMPLE_SUBMISSION_ID, mock_conn, mock_storage
    )

    # Pipeline functions called in correct order with correct args
    mock_build.assert_called_once_with(SAMPLE_SUBMISSION_ID, mock_conn, mock_storage)
    mock_generate.assert_called_once_with(mock_build.return_value)
    mock_save.assert_called_once_with(
        SAMPLE_SUBMISSION_ID, mock_generate.return_value, mock_conn
    )

    # Returns draft_id from save_draft
    mock_resolve.return_value = SAMPLE_VERSION_ID

    draft_id = trigger_feedback_generation(
        SAMPLE_SUBMISSION_ID,
        mock_conn,
        mock_storage,
        version_id=SAMPLE_VERSION_ID,
    )

    mock_resolve.assert_called_once_with(
        SAMPLE_SUBMISSION_ID,
        mock_conn,
        SAMPLE_VERSION_ID,
    )
    mock_build.assert_called_once_with(
        SAMPLE_SUBMISSION_ID,
        mock_conn,
        mock_storage,
        version_id=SAMPLE_VERSION_ID,
    )
    mock_generate.assert_called_once_with(mock_build.return_value)
    mock_save.assert_called_once_with(
        SAMPLE_SUBMISSION_ID,
        mock_generate.return_value,
        mock_conn,
        version_id=SAMPLE_VERSION_ID,
    )
    assert draft_id == SAMPLE_DRAFT_ID
