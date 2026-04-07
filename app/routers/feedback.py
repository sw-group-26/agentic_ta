"""FastAPI router for the feedback workflow.

Exposes 5 REST endpoints that delegate to the feedback service layer.
This router is registered in main.py via ``include_router(prefix="/api")``.

Endpoints:
    GET  /submissions/{submission_id}/feedback-drafts
    GET  /feedback-drafts/{draft_id}
    POST /feedback-drafts/{draft_id}/approve
    POST /feedback-drafts/{draft_id}/publish
    POST /submissions/{submission_id}/generate-feedback
"""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException

from app.deps import get_db, get_storage
from app.llm import OllamaUnavailableError
from app.schemas.feedback import (
    ApproveOut,
    ApproveRequest,
    DraftDetailOut,
    DraftListOut,
    DraftSummaryOut,
    GenerateFeedbackOut,
    PublishOut,
)
from app.services import feedback_service

router = APIRouter()
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _handle_value_error(exc: ValueError) -> HTTPException:
    """Map service-layer ValueError to 404 or 409.

    The service layer raises ValueError with predictable messages:
    - "draft not found: ..." / "submission not found: ..." -> 404
    - "cannot approve ..." / "cannot publish ..." -> 409
    """
    msg = str(exc).lower()
    if "not found" in msg:
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=409, detail=str(exc))


# ---------------------------------------------------------------------------
# 1. List feedback drafts for a submission
# ---------------------------------------------------------------------------


@router.get(
    "/submissions/{submission_id}/feedback-drafts",
    response_model=DraftListOut,
)
def list_feedback_drafts(
    submission_id: UUID,
    conn=Depends(get_db),
) -> DraftListOut:
    """Return all feedback drafts for a submission (newest first)."""
    logger.info("list_feedback_drafts submission_id=%s", submission_id)

    rows = feedback_service.list_drafts(str(submission_id), conn)

    summaries = [
        DraftSummaryOut(
            draft_id=r["draft_id"],
            version_id=r.get("version_id"),
            model_name=r["model_name"],
            prompt_version=r.get("prompt_version"),
            generated_at=r["generated_at"],
            draft_text_preview=r["draft_text"][:200],
            confidence=r.get("confidence"),
            status=r["status"],
        )
        for r in rows
    ]

    return DraftListOut(
        submission_id=submission_id,
        drafts=summaries,
        count=len(summaries),
    )


# ---------------------------------------------------------------------------
# 2. Get draft detail (full text + evidence)
# ---------------------------------------------------------------------------


@router.get(
    "/feedback-drafts/{draft_id}",
    response_model=DraftDetailOut,
)
def get_feedback_draft(
    draft_id: UUID,
    conn=Depends(get_db),
) -> DraftDetailOut:
    """Return full draft detail including evidence items."""
    logger.info("get_feedback_draft draft_id=%s", draft_id)

    try:
        result = feedback_service.get_draft_detail(str(draft_id), conn)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc

    return DraftDetailOut(**result)


# ---------------------------------------------------------------------------
# 3. Approve a draft (TA action: pending -> approved)
# ---------------------------------------------------------------------------


@router.post(
    "/feedback-drafts/{draft_id}/approve",
    response_model=ApproveOut,
)
def approve_feedback_draft(
    draft_id: UUID,
    body: ApproveRequest,
    conn=Depends(get_db),
) -> ApproveOut:
    """Approve a pending feedback draft. Only TAs may call this."""
    logger.info("approve_feedback_draft draft_id=%s ta_id=%s", draft_id, body.ta_id)

    try:
        result = feedback_service.approve_draft(str(draft_id), str(body.ta_id), conn)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc

    return ApproveOut(
        draft_id=result["draft_id"],
        approved_by=result["approved_by"],
        approved_at=result["approved_at"],
    )


# ---------------------------------------------------------------------------
# 4. Publish a draft (Instructor action: approved -> published)
# ---------------------------------------------------------------------------


@router.post(
    "/feedback-drafts/{draft_id}/publish",
    response_model=PublishOut,
)
def publish_feedback_draft(
    draft_id: UUID,
    conn=Depends(get_db),
) -> PublishOut:
    """Publish an approved feedback draft. Only instructors may call this."""
    logger.info("publish_feedback_draft draft_id=%s", draft_id)

    try:
        result = feedback_service.publish_draft(str(draft_id), conn)
    except ValueError as exc:
        raise _handle_value_error(exc) from exc

    return PublishOut(
        draft_id=result["draft_id"],
        published_at=result["published_at"],
    )


# ---------------------------------------------------------------------------
# 5. Trigger LLM feedback generation
# ---------------------------------------------------------------------------


@router.post(
    "/submissions/{submission_id}/generate-feedback",
    response_model=GenerateFeedbackOut,
)
def generate_feedback_for_submission(
    submission_id: UUID,
    version_id: UUID | None = None,
    conn=Depends(get_db),
    storage=Depends(get_storage),
) -> GenerateFeedbackOut:
    """Trigger LLM feedback generation for a submission."""
    logger.info(
        "generate_feedback submission_id=%s version_id=%s",
        submission_id,
        version_id,
    )

    try:
        draft_id = feedback_service.trigger_feedback_generation(
            str(submission_id),
            conn,
            storage,
            version_id=(str(version_id) if version_id is not None else None),
        )
    except ValueError as exc:
        raise _handle_value_error(exc) from exc
    except OllamaUnavailableError as exc:
        logger.warning("LLM service unavailable: %s", exc)
        raise HTTPException(status_code=503, detail="LLM service unavailable") from exc

    return GenerateFeedbackOut(
        draft_id=draft_id,
        submission_id=submission_id,
        version_id=version_id,
    )
