"""Draft Saver (Step 8).

Persists LLM-generated feedback to the DB:
  - llm_feedback_draft  — one row per generated draft
  - llm_evidence        — zero or more rows per draft (grounding evidence)

Usage:
    from app.services.draft_saver import save_draft

    draft_id = save_draft(submission_id, result, conn)
"""

from __future__ import annotations

import logging
from typing import Any

import psycopg2.extensions

logger = logging.getLogger(__name__)


def save_draft(
    submission_id: str,
    result: dict[str, Any],
    conn: psycopg2.extensions.connection,
) -> str:
    """Persist an LLM feedback result to the database.

    Args:
        submission_id: UUID string of the target submission.
        result: Dict returned by generate_feedback() — must contain
                draft_text, confidence, model_name, prompt_version, evidence.
        conn: Active psycopg2 connection (caller manages commit/rollback).

    Returns:
        draft_id (str): UUID of the newly inserted llm_feedback_draft row.

    Raises:
        KeyError: If required keys are missing from result.
        psycopg2.Error: On DB insert failure.
    """
    with conn.cursor() as cur:
        # ------------------------------------------------------------------
        # 1. INSERT llm_feedback_draft
        #    DB columns: draft_id, submission_id, model_name, prompt_version,
        #                generated_at (DEFAULT now()), draft_text, confidence,
        #                status
        # ------------------------------------------------------------------
        cur.execute(
            """
            INSERT INTO llm_feedback_draft
                (submission_id, model_name, prompt_version,
                 draft_text, confidence, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING draft_id
            """,
            (
                submission_id,
                result["model_name"],
                result.get("prompt_version"),
                result["draft_text"],
                result.get("confidence"),
                "pending",
            ),
        )
        draft_id: str = str(cur.fetchone()[0])

        logger.info(
            "save_draft submission_id=%s draft_id=%s model_name=%s",
            submission_id[:8],
            draft_id[:8],
            result["model_name"],
        )

        # ------------------------------------------------------------------
        # 2. INSERT llm_evidence (one row per evidence item)
        #    DB columns: evidence_id, draft_id, evidence_type, pointer, snippet
        #    evidence list may be empty — no rows inserted in that case
        # ------------------------------------------------------------------
        evidence_items: list[dict] = result.get("evidence", [])
        if evidence_items:
            cur.executemany(
                """
                INSERT INTO llm_evidence (draft_id, evidence_type, pointer, snippet)
                VALUES (%s, %s, %s, %s)
                """,
                [
                    (
                        draft_id,
                        item.get("type", ""),
                        item.get("pointer", ""),
                        item.get("snippet"),
                    )
                    for item in evidence_items
                ],
            )

        conn.commit()

    return draft_id
