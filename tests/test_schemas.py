"""
Unit tests for Pydantic feedback schemas.

Validates request/response schemas defined in app.schemas.feedback.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.feedback import (
    ApproveRequest,
    DraftDetailOut,
    DraftSummaryOut,
    EvidenceOut,
)


class TestDraftSummaryOut:
    """DraftSummaryOut required field validation."""

    def test_draft_summary_out_validates_required_fields(self):
        """
        Verify DraftSummaryOut requires all mandatory fields.
        Check if all required fields are present and optional fields default to None.
        """
        # all required fields provided
        summary = DraftSummaryOut(
            draft_id=uuid.uuid4(),
            model_name="llama3.2",
            generated_at=datetime.now(timezone.utc),
            draft_text_preview="Some preview text...",
            status="pending",
        )
        assert summary.model_name == "llama3.2"
        assert summary.status == "pending"
        # optional fields default to None
        assert summary.confidence is None
        assert summary.prompt_version is None

        # missing required field → ValidationError
        with pytest.raises(ValidationError):
            DraftSummaryOut(
                model_name="llama3.2",
                generated_at=datetime.now(timezone.utc),
                draft_text_preview="text",
                status="pending",
                # draft_id missing
            )


class TestApproveRequest:
    """ApproveRequest ta_id requirement validation."""

    def test_approve_request_requires_ta_id(self):
        """
        Verify ApproveRequest raises ValidationError when ta_id is missing.
        Check if ta_id is required and raises ValidationError when missing.
        """
        # ta_id missing
        with pytest.raises(ValidationError):
            ApproveRequest()

        # invalid UUID string
        with pytest.raises(ValidationError):
            ApproveRequest(ta_id="not-a-uuid")

        # valid UUID
        ta_uuid = uuid.uuid4()
        req = ApproveRequest(ta_id=ta_uuid)
        assert req.ta_id == ta_uuid


class TestDraftDetailOut:
    """DraftDetailOut evidence list validation."""

    def test_draft_detail_out_includes_evidence_list(self):
        """
        Verify DraftDetailOut nests EvidenceOut items correctly.
        Check if evidence list is included and empty list is default.
        """
        draft_id = uuid.uuid4()
        submission_id = uuid.uuid4()
        evidence_id = uuid.uuid4()

        # with evidence
        detail = DraftDetailOut(
            draft_id=draft_id,
            submission_id=submission_id,
            model_name="llama3.2",
            generated_at=datetime.now(timezone.utc),
            draft_text="Full feedback text here...",
            status="pending",
            evidence=[
                EvidenceOut(
                    evidence_id=evidence_id,
                    evidence_type="test_run",
                    pointer="test_case_003",
                    snippet="AssertionError: expected 5 but got 3",
                ),
            ],
        )
        assert len(detail.evidence) == 1
        assert detail.evidence[0].evidence_type == "test_run"
        assert detail.evidence[0].evidence_id == evidence_id
        # nullable fields default to None
        assert detail.approved_by is None
        assert detail.approved_at is None
        assert detail.published_at is None

        # without evidence — defaults to empty list
        detail_no_ev = DraftDetailOut(
            draft_id=draft_id,
            submission_id=submission_id,
            model_name="llama3.2",
            generated_at=datetime.now(timezone.utc),
            draft_text="Full text",
            status="approved",
        )
        assert detail_no_ev.evidence == []
