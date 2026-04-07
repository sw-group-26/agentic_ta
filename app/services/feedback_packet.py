"""Feedback Packet Builder (Step 6).

Assembles submission / rubric / test_run / similarity_check data from the DB
into a single dict to be used as LLM input.

Usage:
    from app.services import build_feedback_packet

    packet = build_feedback_packet(submission_id, conn, storage)
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import psycopg2.extensions

from app.storage import LocalStorageAdapter


def _column_exists(
    cur: psycopg2.extensions.cursor,
    table_name: str,
    column_name: str,
) -> bool:
    """Return True if a given column exists in current schema."""
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = %s
              AND column_name = %s
        )
        """,
        (table_name, column_name),
    )
    return bool(cur.fetchone()[0])


def build_feedback_packet(
    submission_id: str,
    conn: psycopg2.extensions.connection,
    storage: LocalStorageAdapter,
    version_id: str | None = None,
) -> dict[str, Any]:
    """Assemble all grading-related data for a submission into one dict.

    Args:
        submission_id: UUID string of the target submission.
        conn: Active psycopg2 connection (caller manages the transaction).
        storage: LocalStorageAdapter instance used to read artifact files.
        version_id: Optional explicit version context.

    Returns:
        Dict containing:
        - assignment_title (str)
        - rubric (list[dict])  — description, category, max_points
        - latest_submission_artifacts (dict)  — attempt_no, submitted_at,
              code_snapshot_path, code_content
        - test_summary (dict)  — total_runs, latest_score, passed_count, failed_count
        - failed_tests (list[dict])  — test_case_id, score_awarded, output
        - similarity_signals (list[dict])  — compared_to, score, method
        - student_history_summary (dict)  — total_attempts, attempt_scores

    Raises:
        ValueError: When submission_id/version_id does not exist in the DB.
    """
    with conn.cursor() as cur:
        # ------------------------------------------------------------------
        # 1. Fetch submission + assignment info
        # ------------------------------------------------------------------
        cur.execute(
            """
            SELECT a.title, s.code_snapshot_path, s.assignment_id,
                   a.due_at, s.submitted_at
            FROM submission s
            JOIN assignment a ON a.assignment_id = s.assignment_id
            WHERE s.submission_id = %s
            """,
            (submission_id,),
        )
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"submission not found: {submission_id}")
        (
            assignment_title,
            legacy_code_snapshot_path,
            assignment_id,
            due_at,
            submitted_at,
        ) = row

        # Determine whether this submission was late.
        is_late: bool = False
        if submitted_at is not None and due_at is not None:
            is_late = submitted_at > due_at

        # ------------------------------------------------------------------
        # 2. Fetch rubric items
        # ------------------------------------------------------------------
        cur.execute(
            """
            SELECT ri.description, ri.category, ri.max_points
            FROM rubric r
            JOIN rubric_item ri ON ri.rubric_id = r.rubric_id
            WHERE r.assignment_id = %s
            ORDER BY ri.order_index
            """,
            (str(assignment_id),),
        )
        rubric = [
            {"description": desc, "category": cat, "max_points": float(pts)}
            for desc, cat, pts in cur.fetchall()
        ]

        # ------------------------------------------------------------------
        # 3. Resolve target version context
        # ------------------------------------------------------------------
        has_sv_code_snapshot = _column_exists(cur, "submission_version", "code_snapshot_path")
        sv_snapshot_expr = (
            "sv.code_snapshot_path"
            if has_sv_code_snapshot
            else "NULL::text AS code_snapshot_path"
        )

        if version_id is None:
            cur.execute(
                f"""
                SELECT sv.version_id, sv.attempt_no, sv.created_at,
                       sv.commit_hash, {sv_snapshot_expr}
                FROM submission_version sv
                WHERE sv.submission_id = %s
                ORDER BY sv.attempt_no DESC, sv.created_at DESC
                LIMIT 1
                """,
                (submission_id,),
            )
        else:
            cur.execute(
                f"""
                SELECT sv.version_id, sv.attempt_no, sv.created_at,
                       sv.commit_hash, {sv_snapshot_expr}
                FROM submission_version sv
                WHERE sv.submission_id = %s
                  AND sv.version_id = %s
                LIMIT 1
                """,
                (submission_id, version_id),
            )

        version_row = cur.fetchone()
        if version_row is None and version_id is not None:
            raise ValueError(f"version not found for submission: {version_id}")

        target_version_id: str | None = None
        latest_attempt_no = 1
        version_commit_hash: str | None = None
        version_code_snapshot_path: str | None = None
        if version_row is not None:
            target_version_id = str(version_row[0])
            latest_attempt_no = int(version_row[1])
            version_commit_hash = version_row[3]
            version_code_snapshot_path = version_row[4]

        effective_code_snapshot_path = (
            version_code_snapshot_path or legacy_code_snapshot_path
        )

        # Load code content from storage; silently set None on any failure
        code_content: str | None = None
        if effective_code_snapshot_path:
            try:
                abs_path = Path(effective_code_snapshot_path)
                if abs_path.exists():
                    code_content = abs_path.read_text(encoding="utf-8")
                else:
                    # Try treating code_snapshot_path as an object key
                    relative_key = effective_code_snapshot_path.replace(
                        str(storage.root) + "/", "", 1
                    )
                    if storage.exists(relative_key):
                        code_content = storage.load_text(relative_key)
            except Exception:
                code_content = None

        latest_submission_artifacts = {
            "version_id": target_version_id,
            "attempt_no": latest_attempt_no,
            "submitted_at": str(submitted_at) if submitted_at else None,
            "due_at": str(due_at) if due_at else None,
            "is_late": is_late,
            "commit_hash": version_commit_hash,
            "code_snapshot_path": effective_code_snapshot_path,
            "code_content": code_content,
        }

        # ------------------------------------------------------------------
        # 4. test_run summary (latest first, then full history)
        # ------------------------------------------------------------------
        has_test_run_version = _column_exists(cur, "test_run", "version_id")
        if has_test_run_version and target_version_id is not None:
            cur.execute(
                """
                SELECT score, results_json_path, run_at
                FROM test_run
                WHERE submission_id = %s
                  AND version_id = %s
                ORDER BY run_at DESC
                """,
                (submission_id, target_version_id),
            )
        else:
            cur.execute(
                """
                SELECT score, results_json_path, run_at
                FROM test_run
                WHERE submission_id = %s
                ORDER BY run_at DESC
                """,
                (submission_id,),
            )
        test_run_rows = cur.fetchall()

        total_runs = len(test_run_rows)
        latest_score: float | None = None
        latest_results_path: str | None = None

        if test_run_rows:
            latest_score = (
                float(test_run_rows[0][0]) if test_run_rows[0][0] is not None else None
            )
            latest_results_path = test_run_rows[0][1]

        # Collect scores oldest→newest for history
        attempt_scores = [
            float(r[0]) for r in reversed(test_run_rows) if r[0] is not None
        ]

        # ------------------------------------------------------------------
        # 5. Parse failed_tests from results_json_path
        # ------------------------------------------------------------------
        failed_tests: list[dict] = []
        passed_count = 0
        failed_count = 0

        if latest_results_path:
            try:
                results_path = Path(latest_results_path)
                if results_path.exists():
                    raw = results_path.read_text(encoding="utf-8")
                else:
                    # Fallback: treat as object key relative to storage root
                    rel_key = latest_results_path.replace(
                        str(storage.root) + "/", "", 1
                    )
                    raw = storage.load_text(rel_key)

                test_cases: list[dict] = json.loads(raw)
                for tc in test_cases:
                    if tc.get("passed"):
                        passed_count += 1
                    else:
                        failed_count += 1
                        failed_tests.append(
                            {
                                "test_case_id": tc.get("test_case_id", ""),
                                "score_awarded": float(tc.get("score_awarded", 0)),
                                "output": tc.get("output", ""),
                            }
                        )
            except Exception:
                # File missing or JSON parse error — keep empty lists
                pass

        test_summary = {
            "total_runs": total_runs,
            "latest_score": latest_score,
            "passed_count": passed_count,
            "failed_count": failed_count,
        }

        # ------------------------------------------------------------------
        # 6. similarity_signals involving this submission
        # ------------------------------------------------------------------
        cur.execute(
            """
            SELECT
                CASE
                    WHEN submission_a = %s THEN submission_b::text
                    ELSE submission_a::text
                END AS compared_to,
                similarity_score,
                method
            FROM similarity_check
            WHERE submission_a = %s OR submission_b = %s
            ORDER BY similarity_score DESC
            """,
            (submission_id, submission_id, submission_id),
        )
        similarity_signals = [
            {"compared_to": str(r[0]), "score": float(r[1]), "method": r[2]}
            for r in cur.fetchall()
        ]

        # ------------------------------------------------------------------
        # 7. Count total attempts for student_history_summary
        # ------------------------------------------------------------------
        cur.execute(
            "SELECT COUNT(*) FROM submission_version WHERE submission_id = %s",
            (submission_id,),
        )
        total_attempts = cur.fetchone()[0]

    return {
        "assignment_title": assignment_title,
        "rubric": rubric,
        "latest_submission_artifacts": latest_submission_artifacts,
        "test_summary": test_summary,
        "failed_tests": failed_tests,
        "similarity_signals": similarity_signals,
        "student_history_summary": {
            "total_attempts": total_attempts,
            "attempt_scores": attempt_scores,
        },
    }
