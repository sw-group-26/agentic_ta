"""
Pydantic v2 schemas for the feedback workflow API.

Defines request/response schemas for the feedback workflow API.

Models align with the API contract: docs/api_contract_sprint3.md
"""

from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Evidence (single evidence item)
# ---------------------------------------------------------------------------


class EvidenceOut(BaseModel):
    """
    Single evidence item linked to a feedback draft.
    """

    model_config = ConfigDict(from_attributes=True)

    evidence_id: UUID
    evidence_type: str  # "test_run" | "code_snippet" | "rubric_item"
    pointer: str
    snippet: str | None = None


# ---------------------------------------------------------------------------
# Draft Summary (list-view summary)
# ---------------------------------------------------------------------------


class DraftSummaryOut(BaseModel):
    """
    Summary representation of a feedback draft for list views.
    """

    model_config = ConfigDict(from_attributes=True)

    draft_id: UUID
    model_name: str
    prompt_version: str | None = None
    generated_at: datetime
    draft_text_preview: str = Field(
        ...,
        description="First 200 characters of draft_text",
    )
    confidence: float | None = None
    status: str  # "pending" | "approved" | "published"


# ---------------------------------------------------------------------------
# Draft Detail (full detail with evidence)
# ---------------------------------------------------------------------------


class DraftDetailOut(BaseModel):
    """
    Full detail of a feedback draft including evidence list.
    """

    model_config = ConfigDict(from_attributes=True)

    draft_id: UUID
    submission_id: UUID
    model_name: str
    prompt_version: str | None = None
    generated_at: datetime
    draft_text: str
    confidence: float | None = None
    status: str  # "pending" | "approved" | "published"
    approved_by: UUID | None = None
    approved_at: datetime | None = None
    published_at: datetime | None = None
    evidence: list[EvidenceOut] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Draft List (list response wrapper)
# ---------------------------------------------------------------------------


class DraftListOut(BaseModel):
    """
    Wrapper for a list of draft summaries scoped to a submission.
    """

    submission_id: UUID
    drafts: list[DraftSummaryOut]
    count: int


# ---------------------------------------------------------------------------
# Approve (approval request & response)
# ---------------------------------------------------------------------------


class ApproveRequest(BaseModel):
    """
    Request body for approving a feedback draft. ta_id is required.
    """

    ta_id: UUID


class ApproveOut(BaseModel):
    """
    Response after successfully approving a draft.
    """

    draft_id: UUID
    status: Literal["approved"] = "approved"
    approved_by: UUID
    approved_at: datetime


# ---------------------------------------------------------------------------
# Publish (publish response)
# ---------------------------------------------------------------------------


class PublishOut(BaseModel):
    """
    Response after successfully publishing a draft.
    """

    draft_id: UUID
    status: Literal["published"] = "published"
    published_at: datetime


# ---------------------------------------------------------------------------
# Generate Feedback (generation response)
# ---------------------------------------------------------------------------


class GenerateFeedbackOut(BaseModel):
    """
    Response after triggering LLM feedback generation.
    """

    draft_id: UUID
    submission_id: UUID
    status: Literal["pending"] = "pending"
    message: str = "Feedback draft generated successfully"
