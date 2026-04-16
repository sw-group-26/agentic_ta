"""Unit tests for Pydantic feedback schemas."""

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
    PublishOut,
    PublishRequest,
)


class TestDraftSummaryOut:
    """DraftSummaryOut required field validation."""

    def test_draft_summary_out_validates_required_fields(self):
        summary = DraftSummaryOut(
            draft_id=uuid.uuid4(),
            model_name="llama3.2",
            generated_at=datetime.now(timezone.utc),
            draft_text_preview="Some preview text...",
            status="pending",
        )
        assert summary.model_name == "llama3.2"
        assert summary.status == "pending"
        assert summary.confidence is None
        assert summary.prompt_version is None

        with pytest.raises(ValidationError):
            DraftSummaryOut(
                model_name="llama3.2",
                generated_at=datetime.now(timezone.utc),
                draft_text_preview="text",
                status="pending",
            )


class TestApproveRequest:
    """ApproveRequest ta_id requirement validation."""

    def test_approve_request_requires_ta_id(self):
        with pytest.raises(ValidationError):
            ApproveRequest()

        with pytest.raises(ValidationError):
            ApproveRequest(ta_id="not-a-uuid")

        ta_uuid = uuid.uuid4()
        req = ApproveRequest(ta_id=ta_uuid)
        assert req.ta_id == ta_uuid


class TestPublishRequest:
    """PublishRequest instructor_id requirement validation."""

    def test_publish_request_requires_instructor_id(self):
        with pytest.raises(ValidationError):
            PublishRequest()

        with pytest.raises(ValidationError):
            PublishRequest(instructor_id="not-a-uuid")

        instructor_uuid = uuid.uuid4()
        req = PublishRequest(instructor_id=instructor_uuid)
        assert req.instructor_id == instructor_uuid


class TestDraftDetailOut:
    """DraftDetailOut evidence list validation."""

    def test_draft_detail_out_includes_evidence_list(self):
        draft_id = uuid.uuid4()
        submission_id = uuid.uuid4()
        evidence_id = uuid.uuid4()
        instructor_id = uuid.uuid4()

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
        assert detail.approved_by is None
        assert detail.approved_at is None
        assert detail.published_by_instructor_id is None
        assert detail.published_at is None

        detail_no_ev = DraftDetailOut(
            draft_id=draft_id,
            submission_id=submission_id,
            model_name="llama3.2",
            generated_at=datetime.now(timezone.utc),
            draft_text="Full text",
            status="published",
            published_by_instructor_id=instructor_id,
            published_at=datetime.now(timezone.utc),
        )
        assert detail_no_ev.evidence == []
        assert detail_no_ev.published_by_instructor_id == instructor_id


class TestPublishOut:
    """PublishOut includes instructor audit field."""

    def test_publish_out_requires_instructor_publish_metadata(self):
        instructor_id = uuid.uuid4()
        out = PublishOut(
            draft_id=uuid.uuid4(),
            published_by_instructor_id=instructor_id,
            published_at=datetime.now(timezone.utc),
        )
        assert out.status == "published"
        assert out.published_by_instructor_id == instructor_id
