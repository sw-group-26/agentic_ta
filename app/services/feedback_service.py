"""Feedback Service Layer (Sprint 3, Step 3).

Business logic for feedback draft CRUD and approval workflow.
Sits between the router (Step 4) and existing Sprint 2 modules.

State machine: pending -> approved -> published
  - pending  -> approved:  requires ta_id (approve_draft)
  - approved -> published: (publish_draft)
  - All other transitions raise ValueError.

Usage:
    from app.services.feedback_service import list_drafts, approve_draft
"""

from __future__ import annotations

import logging
import time
import uuid
from datetime import datetime
from typing import Any

import psycopg2.extensions

from app.llm import generate_feedback
from app.services.draft_saver import save_draft
from app.services.feedback_packet import build_feedback_packet
from app.storage.local_store import LocalStorageAdapter

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _serialize(val: Any) -> Any:
    """Convert DB-native types to JSON-safe primitives."""
    if isinstance(val, uuid.UUID):
        return str(val)
    if isinstance(val, datetime):
        return val.isoformat()
    return val


def _row_to_dict(
    cursor: Any,
    row: tuple,
) -> dict[str, Any]:
    """Map a single DB row to a dict using cursor.description column names."""
    columns = [desc[0] for desc in cursor.description]
    return {col: _serialize(val) for col, val in zip(columns, row)}


def _rows_to_list(
    cursor: Any,
    rows: list[tuple],
) -> list[dict[str, Any]]:
    """Map multiple DB rows to a list of dicts."""
    columns = [desc[0] for desc in cursor.description]
    return [{col: _serialize(val) for col, val in zip(columns, row)} for row in rows]


def _resolve_target_version_id(
    submission_id: str,
    conn: psycopg2.extensions.connection,
    requested_version_id: str | None,
) -> str:
    """Resolve and validate the version to use for generation.

    If requested_version_id is provided, it must belong to submission_id.
    Otherwise, latest attempt version is returned.
    """
    with conn.cursor() as cur:
        if requested_version_id is not None:
            cur.execute(
                """
                SELECT version_id
                FROM submission_version
                WHERE version_id = %s
                  AND submission_id = %s
                """,
                (requested_version_id, submission_id),
            )
            row = cur.fetchone()
            if row is None:
                raise ValueError(
                    f"version not found for submission: {requested_version_id}"
                )
            return str(row[0])

        cur.execute(
            """
            SELECT version_id
            FROM submission_version
            WHERE submission_id = %s
            ORDER BY attempt_no DESC, created_at DESC
            LIMIT 1
            """,
            (submission_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"submission version not found: {submission_id}")
        return str(row[0])


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

_DRAFT_COLS = (
    "draft_id, submission_id, model_name, prompt_version, "
    "generated_at, draft_text, confidence, status, "
    "approved_by, approved_at, published_at"
)


def list_drafts(
    submission_id: str,
    conn: psycopg2.extensions.connection,
) -> list[dict[str, Any]]:
    """Return all feedback drafts for a submission, newest first.

    Args:
        submission_id: UUID string of the target submission.
        conn: Active psycopg2 connection.

    Returns:
        List of dicts with draft columns (draft_id, submission_id,
        model_name, prompt_version, generated_at, draft_text,
        confidence, status, approved_by, approved_at, published_at).
    """
    with conn.cursor() as cur:
        cur.execute(
            f"SELECT {_DRAFT_COLS} "
            "FROM llm_feedback_draft "
            "WHERE submission_id = %s "
            "ORDER BY generated_at DESC",
            (submission_id,),
        )
        rows = cur.fetchall()

    result = _rows_to_list(cur, rows)
    logger.info(
        "list_drafts submission_id=%s count=%d",
        submission_id[:8],
        len(result),
    )
    return result


def get_draft_detail(
    draft_id: str,
    conn: psycopg2.extensions.connection,
) -> dict[str, Any]:
    """Return a single draft with its evidence items.

    Args:
        draft_id: UUID string of the draft.
        conn: Active psycopg2 connection.

    Returns:
        Dict with all draft columns plus an ``evidence`` key containing
        a list of evidence dicts (evidence_id, evidence_type, pointer,
        snippet).

    Raises:
        ValueError: If draft_id does not exist.
    """
    with conn.cursor() as cur:
        # Fetch draft row
        cur.execute(
            f"SELECT {_DRAFT_COLS} " "FROM llm_feedback_draft " "WHERE draft_id = %s",
            (draft_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"draft not found: {draft_id}")
        draft = _row_to_dict(cur, row)

        # Fetch evidence rows
        cur.execute(
            "SELECT evidence_id, evidence_type, pointer, snippet "
            "FROM llm_evidence "
            "WHERE draft_id = %s",
            (draft_id,),
        )
        evidence_rows = cur.fetchall()
        draft["evidence"] = _rows_to_list(cur, evidence_rows)

    logger.info(
        "get_draft_detail draft_id=%s evidence_count=%d",
        draft_id[:8],
        len(draft["evidence"]),
    )
    return draft


def approve_draft(
    draft_id: str,
    ta_id: str,
    conn: psycopg2.extensions.connection,
) -> dict[str, Any]:
    """Transition a draft from pending to approved.

    Args:
        draft_id: UUID string of the draft to approve.
        ta_id: UUID string of the TA performing the approval.
        conn: Active psycopg2 connection.

    Returns:
        Dict with updated draft columns (status='approved').

    Raises:
        ValueError: If draft not found or current status is not 'pending'.
    """
    with conn.cursor() as cur:
        # Lock row and read current status
        cur.execute(
            "SELECT status FROM llm_feedback_draft " "WHERE draft_id = %s FOR UPDATE",
            (draft_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"draft not found: {draft_id}")

        status = row[0]
        if status != "pending":
            raise ValueError(
                f"cannot approve draft in '{status}' status; expected 'pending'"
            )

        # Transition: pending -> approved
        cur.execute(
            "UPDATE llm_feedback_draft "
            "SET status = 'approved', approved_by = %s, approved_at = now() "
            "WHERE draft_id = %s "
            f"RETURNING {_DRAFT_COLS}",
            (ta_id, draft_id),
        )
        updated = _row_to_dict(cur, cur.fetchone())

    conn.commit()

    logger.info(
        "approve_draft draft_id=%s pending->approved by ta_id=%s",
        draft_id[:8],
        ta_id[:8],
    )
    return updated


def publish_draft(
    draft_id: str,
    conn: psycopg2.extensions.connection,
) -> dict[str, Any]:
    """Transition a draft from approved to published.

    Args:
        draft_id: UUID string of the draft to publish.
        conn: Active psycopg2 connection.

    Returns:
        Dict with updated draft columns (status='published').

    Raises:
        ValueError: If draft not found or current status is not 'approved'.
    """
    with conn.cursor() as cur:
        # Lock row and read current status
        cur.execute(
            "SELECT status FROM llm_feedback_draft " "WHERE draft_id = %s FOR UPDATE",
            (draft_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"draft not found: {draft_id}")

        status = row[0]
        if status != "approved":
            raise ValueError(
                f"cannot publish draft in '{status}' status; expected 'approved'"
            )

        # Transition: approved -> published
        cur.execute(
            "UPDATE llm_feedback_draft "
            "SET status = 'published', published_at = now() "
            "WHERE draft_id = %s "
            f"RETURNING {_DRAFT_COLS}",
            (draft_id,),
        )
        updated = _row_to_dict(cur, cur.fetchone())

    conn.commit()

    logger.info(
        "publish_draft draft_id=%s approved->published",
        draft_id[:8],
    )
    return updated


def trigger_feedback_generation(
    submission_id: str,
    conn: psycopg2.extensions.connection,
    storage: LocalStorageAdapter,
    version_id: str | None = None,
) -> str:
    """Orchestrate the full feedback generation pipeline.

    Calls three existing Sprint 2 functions in sequence:
      1. build_feedback_packet() — assemble grading context from DB/storage
      2. generate_feedback()     — call local Ollama LLM
      3. save_draft()            — persist draft to DB (commits internally)

    Args:
        submission_id: UUID string of the target submission.
        conn: Active psycopg2 connection.
        storage: LocalStorageAdapter for reading artifact files.
        version_id: Optional explicit target version_id.

    Returns:
        draft_id (str): UUID of the newly created draft.

    Raises:
        ValueError: If submission/version not found.
        OllamaUnavailableError: If Ollama server is unreachable.
    """
    start = time.time()
    try:
        target_version_id = _resolve_target_version_id(submission_id, conn, version_id)

        # Step 1: Assemble grading context
        packet = build_feedback_packet(
            submission_id,
            conn,
            storage,
            version_id=target_version_id,
        )

        # Step 2: Call LLM
        llm_start = time.time()
        result = generate_feedback(packet)
        llm_elapsed = time.time() - llm_start

        # Step 3: Persist draft (save_draft commits internally)
        draft_id = save_draft(
            submission_id,
            result,
            conn,
            version_id=target_version_id,
        )

        total_elapsed = time.time() - start
        logger.info(
            "trigger_generation submission_id=%s version_id=%s draft_id=%s "
            "llm_time=%.1fs confidence=%.2f total_time=%.1fs",
            submission_id[:8],
            target_version_id[:8],
            draft_id[:8],
            llm_elapsed,
            result.get("confidence", 0),
            total_elapsed,
        )
        return draft_id

    except Exception as exc:
        logger.error(
            "trigger_generation failed submission_id=%s error=%s",
            submission_id[:8],
            exc.__class__.__name__,
            exc_info=True,
        )
        raise
