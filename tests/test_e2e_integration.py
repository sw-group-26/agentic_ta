"""End-to-end integration tests for the feedback pipeline (Sprint 3, Step 7).

These tests exercise the full lifecycle through the service layer:
  generate -> list -> detail -> approve -> publish

All DB interactions are mocked (MagicMock), consistent with the project's
existing test infrastructure.  The @pytest.mark.integration marker allows
running them separately:

    pytest tests/test_e2e_integration.py -v -m integration

Each test run writes a log file to ``logs/test_integration_{date}.log``.
"""

from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
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
# Constants (reuse same column definitions as test_feedback_service.py)
# ---------------------------------------------------------------------------

SAMPLE_SUBMISSION_ID = "cbca2439-5fa7-4a69-b4d5-57515f2ca8df"
SAMPLE_DRAFT_ID = str(uuid.uuid4())
SAMPLE_TA_ID = str(uuid.uuid4())
SAMPLE_INSTRUCTOR_ID = str(uuid.uuid4())
NOW = datetime(2026, 4, 5, 12, 0, 0, tzinfo=timezone.utc)

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
    ("published_by_instructor_id",),
    ("published_at",),
]

EVIDENCE_COLUMNS = [
    ("evidence_id",),
    ("evidence_type",),
    ("pointer",),
    ("snippet",),
]

# Mock LLM response (same structure as scripts/demo_e2e.py)
MOCK_LLM_RESPONSE = {
    "draft_text": (
        "Overall good work on HW1. Your solution correctly handles the "
        "base cases. Consider adding edge-case checks for empty input."
    ),
    "confidence": 0.82,
    "evidence": [
        {
            "type": "test_run",
            "pointer": "test_run:demo-run-001",
            "snippet": "5/5 tests passed",
        },
        {
            "type": "code_snippet",
            "pointer": "main.py:L12-L18",
            "snippet": "def solve(n): ...",
        },
    ],
    "model_name": "mock-llm",
    "prompt_version": "v1.0-mock",
}

# ---------------------------------------------------------------------------
# Logging setup — dual handler (console INFO + file DEBUG)
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

logger = logging.getLogger("test_integration")
logger.setLevel(logging.DEBUG)

# Prevent duplicate handlers on re-import
if not logger.handlers:
    os.makedirs(LOG_DIR, exist_ok=True)
    _ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    _fh = logging.FileHandler(LOG_DIR / f"test_integration_{_ts}.log")
    _fh.setLevel(logging.DEBUG)
    _fh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    _sh = logging.StreamHandler()
    _sh.setLevel(logging.INFO)
    _sh.setFormatter(logging.Formatter("%(asctime)s | %(message)s"))
    logger.addHandler(_fh)
    logger.addHandler(_sh)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_conn() -> MagicMock:
    """Mock psycopg2 connection with cursor context manager support."""
    conn = MagicMock()
    cursor = MagicMock()
    cursor.__enter__ = MagicMock(return_value=cursor)
    cursor.__exit__ = MagicMock(return_value=False)
    conn.cursor.return_value = cursor
    return conn


@pytest.fixture
def mock_storage() -> MagicMock:
    """Mock LocalStorageAdapter."""
    return MagicMock()


# ---------------------------------------------------------------------------
# Helper — reconfigure cursor mock for each pipeline stage
# ---------------------------------------------------------------------------


def _configure_cursor(mock_conn, description, fetchone=None, fetchall=None):
    """Reset cursor mock for the next service call.

    Args:
        mock_conn: The mocked psycopg2 connection.
        description: Column description tuples for cursor.description.
        fetchone: Return value for cursor.fetchone().
        fetchall: Return value for cursor.fetchall().
    """
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    cursor.execute.reset_mock()
    cursor.execute.side_effect = None
    cursor.description = description
    cursor.fetchone.reset_mock()
    cursor.fetchone.return_value = fetchone
    cursor.fetchone.side_effect = None
    cursor.fetchall.reset_mock()
    cursor.fetchall.return_value = fetchall if fetchall is not None else []
    mock_conn.commit.reset_mock()


def _make_draft_row(
    status="pending", approved_by=None, approved_at=None, published_by_instructor_id=None, published_at=None
):
    """Build a draft row tuple matching DRAFT_COLUMNS order."""
    return (
        uuid.UUID(SAMPLE_DRAFT_ID),
        uuid.UUID(SAMPLE_SUBMISSION_ID),
        uuid.uuid4(),
        "mock-llm",
        "v1.0-mock",
        NOW,
        MOCK_LLM_RESPONSE["draft_text"],
        Decimal("0.820"),
        status,
        uuid.UUID(approved_by) if approved_by else None,
        approved_at,
        uuid.UUID(published_by_instructor_id) if published_by_instructor_id else None,
        published_at,
    )


def _make_evidence_rows():
    """Build evidence row tuples matching EVIDENCE_COLUMNS order."""
    return [
        (uuid.uuid4(), "test_run", "test_run:demo-run-001", "5/5 tests passed"),
        (uuid.uuid4(), "code_snippet", "main.py:L12-L18", "def solve(n): ..."),
    ]


# ---------------------------------------------------------------------------
# Test 1: Full pipeline — submission to published
# ---------------------------------------------------------------------------


@pytest.mark.integration
@patch("app.services.feedback_service.save_draft")
@patch("app.services.feedback_service.generate_feedback")
@patch("app.services.feedback_service.build_feedback_packet")
def test_full_pipeline_submission_to_published(
    mock_build: MagicMock,
    mock_generate: MagicMock,
    mock_save: MagicMock,
    mock_conn: MagicMock,
    mock_storage: MagicMock,
) -> None:
    """Simulate full lifecycle: generate -> list -> detail -> approve -> publish.

    Each stage reconfigures the cursor mock and logs the result.
    """
    logger.info("=" * 60)
    logger.info("TEST: test_full_pipeline_submission_to_published")
    logger.info("=" * 60)

    # --- Stage 1: Generate feedback via LLM pipeline ---
    logger.info("Stage 1: trigger_feedback_generation")
    mock_build.return_value = {"assignment_title": "HW1", "rubric": []}
    mock_generate.return_value = MOCK_LLM_RESPONSE
    mock_save.return_value = SAMPLE_DRAFT_ID

    draft_id = trigger_feedback_generation(
        SAMPLE_SUBMISSION_ID, mock_conn, mock_storage
    )

    assert draft_id == SAMPLE_DRAFT_ID
    mock_build.assert_called_once()
    mock_generate.assert_called_once()
    mock_save.assert_called_once()
    logger.info("  draft_id=%s, status=pending", draft_id[:8])

    # --- Stage 2: List drafts for the submission ---
    logger.info("Stage 2: list_drafts")
    pending_row = _make_draft_row(status="pending")
    _configure_cursor(mock_conn, DRAFT_COLUMNS, fetchall=[pending_row])

    drafts = list_drafts(SAMPLE_SUBMISSION_ID, mock_conn)

    assert len(drafts) == 1
    assert drafts[0]["status"] == "pending"
    logger.info("  found %d draft(s), status=%s", len(drafts), drafts[0]["status"])

    # --- Stage 3: Get draft detail with evidence ---
    logger.info("Stage 3: get_draft_detail")
    cursor = mock_conn.cursor.return_value.__enter__.return_value
    descriptions = [DRAFT_COLUMNS, EVIDENCE_COLUMNS]
    call_count = {"n": 0}

    def _set_desc(*args):
        cursor.description = descriptions[call_count["n"]]
        call_count["n"] += 1

    cursor.execute.reset_mock()
    cursor.execute.side_effect = _set_desc
    cursor.fetchone.reset_mock()
    cursor.fetchone.return_value = pending_row
    cursor.fetchall.reset_mock()
    cursor.fetchall.return_value = _make_evidence_rows()

    detail = get_draft_detail(SAMPLE_DRAFT_ID, mock_conn)

    assert detail["draft_id"] == SAMPLE_DRAFT_ID
    assert len(detail["evidence"]) == 2
    logger.info(
        "  draft_text_preview='%s...', evidence_count=%d",
        detail["draft_text"][:40],
        len(detail["evidence"]),
    )

    # --- Stage 4: Approve draft (pending -> approved) ---
    logger.info("Stage 4: approve_draft (pending -> approved)")
    approved_row = _make_draft_row(
        status="approved", approved_by=SAMPLE_TA_ID, approved_at=NOW
    )
    descriptions_approve = [[("status",)], DRAFT_COLUMNS]
    call_count_approve = {"n": 0}

    def _set_desc_approve(*args):
        cursor.description = descriptions_approve[call_count_approve["n"]]
        call_count_approve["n"] += 1

    cursor.execute.reset_mock()
    cursor.execute.side_effect = _set_desc_approve
    cursor.fetchone.reset_mock()
    cursor.fetchone.side_effect = [("pending",), approved_row]

    result = approve_draft(SAMPLE_DRAFT_ID, SAMPLE_TA_ID, mock_conn)

    assert result["status"] == "approved"
    assert result["approved_by"] == SAMPLE_TA_ID
    mock_conn.commit.assert_called()
    logger.info(
        "  status=%s, approved_by=%s", result["status"], str(result["approved_by"])[:8]
    )

    # --- Stage 5: Publish draft (approved -> published) ---
    logger.info("Stage 5: publish_draft (approved -> published)")
    published_row = _make_draft_row(
        status="published",
        approved_by=SAMPLE_TA_ID,
        approved_at=NOW,
        published_by_instructor_id=SAMPLE_INSTRUCTOR_ID,
        published_at=NOW,
    )
    descriptions_publish = [[("status",)], DRAFT_COLUMNS]
    call_count_publish = {"n": 0}

    def _set_desc_publish(*args):
        cursor.description = descriptions_publish[call_count_publish["n"]]
        call_count_publish["n"] += 1

    cursor.execute.reset_mock()
    cursor.execute.side_effect = _set_desc_publish
    cursor.fetchone.reset_mock()
    cursor.fetchone.side_effect = [("approved",), published_row]
    mock_conn.commit.reset_mock()

    result = publish_draft(SAMPLE_DRAFT_ID, SAMPLE_INSTRUCTOR_ID, mock_conn)

    assert result["status"] == "published"
    assert result["published_by_instructor_id"] == SAMPLE_INSTRUCTOR_ID
    assert result["published_at"] is not None
    mock_conn.commit.assert_called_once()
    logger.info(
        "  status=%s, published_at=%s", result["status"], result["published_at"]
    )

    logger.info("RESULT: PASSED — full pipeline submission to published")
    logger.info("")


# ---------------------------------------------------------------------------
# Test 2: Draft status transitions — valid and invalid
# ---------------------------------------------------------------------------


@pytest.mark.integration
def test_draft_status_transitions_via_service(mock_conn: MagicMock) -> None:
    """Verify all valid and invalid state transitions through the service layer.

    Valid:
        pending  -> approved  (approve_draft)
        approved -> published (publish_draft)

    Invalid (must raise ValueError):
        pending  -> published (publish_draft on pending status)
        approved -> approved  (approve_draft on approved status)
        published -> approved (approve_draft on published status)
        published -> published (publish_draft on published status)
    """
    logger.info("=" * 60)
    logger.info("TEST: test_draft_status_transitions_via_service")
    logger.info("=" * 60)

    cursor = mock_conn.cursor.return_value.__enter__.return_value

    # --- Valid: pending -> approved ---
    logger.info("Transition: pending -> approved (valid)")
    approved_row = _make_draft_row(
        status="approved", approved_by=SAMPLE_TA_ID, approved_at=NOW
    )
    descriptions = [[("status",)], DRAFT_COLUMNS]
    call_count = {"n": 0}

    def _set_desc(*args):
        cursor.description = descriptions[call_count["n"]]
        call_count["n"] += 1

    cursor.execute.reset_mock()
    cursor.execute.side_effect = _set_desc
    cursor.fetchone.reset_mock()
    cursor.fetchone.side_effect = [("pending",), approved_row]

    result = approve_draft(SAMPLE_DRAFT_ID, SAMPLE_TA_ID, mock_conn)
    assert result["status"] == "approved"
    logger.info("  OK: pending -> approved")

    # --- Valid: approved -> published ---
    logger.info("Transition: approved -> published (valid)")
    published_row = _make_draft_row(
        status="published",
        approved_by=SAMPLE_TA_ID,
        approved_at=NOW,
        published_by_instructor_id=SAMPLE_INSTRUCTOR_ID,
        published_at=NOW,
    )
    descriptions_pub = [[("status",)], DRAFT_COLUMNS]
    call_count_pub = {"n": 0}

    def _set_desc_pub(*args):
        cursor.description = descriptions_pub[call_count_pub["n"]]
        call_count_pub["n"] += 1

    cursor.execute.reset_mock()
    cursor.execute.side_effect = _set_desc_pub
    cursor.fetchone.reset_mock()
    cursor.fetchone.side_effect = [("approved",), published_row]
    mock_conn.commit.reset_mock()

    result = publish_draft(SAMPLE_DRAFT_ID, SAMPLE_INSTRUCTOR_ID, mock_conn)
    assert result["status"] == "published"
    assert result["published_by_instructor_id"] == SAMPLE_INSTRUCTOR_ID
    logger.info("  OK: approved -> published")

    # --- Invalid: pending -> published (direct) ---
    logger.info("Transition: pending -> published (invalid, expect ValueError)")
    cursor.execute.reset_mock()
    cursor.execute.side_effect = None
    cursor.description = [("status",)]
    cursor.fetchone.reset_mock()
    cursor.fetchone.return_value = ("pending",)
    cursor.fetchone.side_effect = None
    mock_conn.commit.reset_mock()

    with pytest.raises(ValueError, match="cannot publish"):
        publish_draft(SAMPLE_DRAFT_ID, SAMPLE_INSTRUCTOR_ID, mock_conn)
    mock_conn.commit.assert_not_called()
    logger.info("  OK: ValueError raised (cannot publish pending)")

    # --- Invalid: approved -> approved (re-approve) ---
    logger.info("Transition: approved -> approved (invalid, expect ValueError)")
    cursor.execute.reset_mock()
    cursor.execute.side_effect = None
    cursor.description = [("status",)]
    cursor.fetchone.reset_mock()
    cursor.fetchone.return_value = ("approved",)
    cursor.fetchone.side_effect = None
    mock_conn.commit.reset_mock()

    with pytest.raises(ValueError, match="cannot approve"):
        approve_draft(SAMPLE_DRAFT_ID, SAMPLE_TA_ID, mock_conn)
    mock_conn.commit.assert_not_called()
    logger.info("  OK: ValueError raised (cannot approve already-approved)")

    # --- Invalid: published -> approved ---
    logger.info("Transition: published -> approved (invalid, expect ValueError)")
    cursor.fetchone.return_value = ("published",)

    with pytest.raises(ValueError, match="cannot approve"):
        approve_draft(SAMPLE_DRAFT_ID, SAMPLE_TA_ID, mock_conn)
    logger.info("  OK: ValueError raised (cannot approve published)")

    # --- Invalid: published -> published ---
    logger.info("Transition: published -> published (invalid, expect ValueError)")
    cursor.fetchone.return_value = ("published",)

    with pytest.raises(ValueError, match="cannot publish"):
        publish_draft(SAMPLE_DRAFT_ID, SAMPLE_INSTRUCTOR_ID, mock_conn)
    logger.info("  OK: ValueError raised (cannot publish already-published)")

    logger.info("RESULT: PASSED — all 6 transitions verified (2 valid, 4 invalid)")
    logger.info("")
