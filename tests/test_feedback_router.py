"""Integration tests for Feedback Router (Sprint 3, Step 4).

Tests use FastAPI TestClient with dependency overrides and service mocks.

Tests:
    1. test_list_drafts_returns_200
    2. test_get_draft_returns_200_with_evidence
    3. test_get_draft_returns_404_for_missing
    4. test_approve_returns_200_with_new_status
    5. test_approve_returns_409_for_already_approved
    6. test_publish_returns_200
    7. test_generate_feedback_returns_503_on_ollama_error
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.deps import get_db, get_storage
from app.llm import OllamaUnavailableError
from app.main import app

# ---------------------------------------------------------------------------
# Shared constants
# ---------------------------------------------------------------------------

SAMPLE_SUBMISSION_ID = "cbca2439-5fa7-4a69-b4d5-57515f2ca8df"
SAMPLE_DRAFT_ID = str(uuid.uuid4())
SAMPLE_TA_ID = str(uuid.uuid4())
SAMPLE_EVIDENCE_ID = str(uuid.uuid4())
NOW = datetime(2026, 4, 1, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _override_deps():
    """Replace DB and storage dependencies with mocks for all tests."""
    mock_conn = MagicMock()
    mock_storage = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_conn
    app.dependency_overrides[get_storage] = lambda: mock_storage
    yield
    app.dependency_overrides.clear()


@pytest.fixture()
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)


# ---------------------------------------------------------------------------
# Helper: sample draft dict (matches feedback_service output)
# ---------------------------------------------------------------------------


def _sample_draft_row(
    status: str = "pending",
    approved_by: str | None = None,
    approved_at: datetime | None = None,
    published_at: datetime | None = None,
) -> dict:
    return {
        "draft_id": SAMPLE_DRAFT_ID,
        "submission_id": SAMPLE_SUBMISSION_ID,
        "model_name": "llama3.2",
        "prompt_version": "v1.0",
        "generated_at": NOW.isoformat(),
        "draft_text": "Good work on this assignment. " * 20,  # >200 chars
        "confidence": float(Decimal("0.850")),
        "status": status,
        "approved_by": approved_by,
        "approved_at": approved_at.isoformat() if approved_at else None,
        "published_at": published_at.isoformat() if published_at else None,
    }


def _sample_evidence() -> dict:
    return {
        "evidence_id": SAMPLE_EVIDENCE_ID,
        "evidence_type": "test_run",
        "pointer": "test_add::test_basic",
        "snippet": "assert add(1, 2) == 3",
    }


# ---------------------------------------------------------------------------
# 1. GET /api/submissions/{submission_id}/feedback-drafts
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.list_drafts")
def test_list_drafts_returns_200(mock_list, client):
    """List endpoint returns 200 with draft summaries."""
    mock_list.return_value = [_sample_draft_row(), _sample_draft_row()]

    resp = client.get(f"/api/submissions/{SAMPLE_SUBMISSION_ID}/feedback-drafts")

    assert resp.status_code == 200
    body = resp.json()
    assert body["submission_id"] == SAMPLE_SUBMISSION_ID
    assert body["count"] == 2
    assert len(body["drafts"]) == 2
    # draft_text_preview should be at most 200 characters
    for draft in body["drafts"]:
        assert len(draft["draft_text_preview"]) <= 200
        assert "draft_id" in draft
        assert "status" in draft


# ---------------------------------------------------------------------------
# 2. GET /api/feedback-drafts/{draft_id}
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.get_draft_detail")
def test_get_draft_returns_200_with_evidence(mock_detail, client):
    """Detail endpoint returns 200 with evidence list."""
    detail = _sample_draft_row()
    detail["evidence"] = [_sample_evidence()]
    mock_detail.return_value = detail

    resp = client.get(f"/api/feedback-drafts/{SAMPLE_DRAFT_ID}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["draft_id"] == SAMPLE_DRAFT_ID
    assert len(body["evidence"]) == 1
    assert body["evidence"][0]["evidence_type"] == "test_run"


# ---------------------------------------------------------------------------
# 3. GET /api/feedback-drafts/{draft_id} — not found
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.get_draft_detail")
def test_get_draft_returns_404_for_missing(mock_detail, client):
    """Detail endpoint returns 404 when draft does not exist."""
    mock_detail.side_effect = ValueError(f"draft not found: {SAMPLE_DRAFT_ID}")

    resp = client.get(f"/api/feedback-drafts/{SAMPLE_DRAFT_ID}")

    assert resp.status_code == 404
    assert "not found" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 4. POST /api/feedback-drafts/{draft_id}/approve
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.approve_draft")
def test_approve_returns_200_with_new_status(mock_approve, client):
    """Approve endpoint returns 200 with approved status."""
    mock_approve.return_value = _sample_draft_row(
        status="approved",
        approved_by=SAMPLE_TA_ID,
        approved_at=NOW,
    )

    resp = client.post(
        f"/api/feedback-drafts/{SAMPLE_DRAFT_ID}/approve",
        json={"ta_id": SAMPLE_TA_ID},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "approved"
    assert body["approved_by"] == SAMPLE_TA_ID
    assert body["draft_id"] == SAMPLE_DRAFT_ID


# ---------------------------------------------------------------------------
# 5. POST /api/feedback-drafts/{draft_id}/approve — conflict
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.approve_draft")
def test_approve_returns_409_for_already_approved(mock_approve, client):
    """Approve endpoint returns 409 when draft is not in pending status."""
    mock_approve.side_effect = ValueError(
        "cannot approve draft in 'approved' status; expected 'pending'"
    )

    resp = client.post(
        f"/api/feedback-drafts/{SAMPLE_DRAFT_ID}/approve",
        json={"ta_id": SAMPLE_TA_ID},
    )

    assert resp.status_code == 409
    assert "cannot approve" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# 6. POST /api/feedback-drafts/{draft_id}/publish
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.publish_draft")
def test_publish_returns_200(mock_publish, client):
    """Publish endpoint returns 200 with published status."""
    mock_publish.return_value = _sample_draft_row(
        status="published",
        approved_by=SAMPLE_TA_ID,
        approved_at=NOW,
        published_at=NOW,
    )

    resp = client.post(f"/api/feedback-drafts/{SAMPLE_DRAFT_ID}/publish")

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "published"
    assert body["published_at"] is not None
    assert body["draft_id"] == SAMPLE_DRAFT_ID


# ---------------------------------------------------------------------------
# 7. POST /api/submissions/{id}/generate-feedback — Ollama unavailable
# ---------------------------------------------------------------------------


@patch("app.routers.feedback.feedback_service.trigger_feedback_generation")
def test_generate_feedback_returns_503_on_ollama_error(mock_trigger, client):
    """Generate endpoint returns 503 when Ollama is unavailable."""
    mock_trigger.side_effect = OllamaUnavailableError("connection refused")

    resp = client.post(f"/api/submissions/{SAMPLE_SUBMISSION_ID}/generate-feedback")

    assert resp.status_code == 503
    assert "unavailable" in resp.json()["detail"].lower()
