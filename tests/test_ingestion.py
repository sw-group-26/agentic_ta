"""Integration tests for seed data ingestion (Step 4).

All tests run inside a transaction that is rolled back on teardown,
so they leave the real DB clean after each run.

Required tests from Sprint2_Wonbum_Plan.md:
    - test_attempt_grouping_creates_one_submission_and_multiple_versions (Test 1)
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import pandas as pd
import psycopg2
import pytest
from dotenv import load_dotenv

# Allow imports from project root without package install
PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from app.storage import LocalStorageAdapter  # noqa: E402
from scripts.ingest_seed_data import (  # noqa: E402
    ingest_course_and_offering,
    ingest_students,
    ingest_submissions,
    migrate,
)

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def db_conn():
    """
    Open a real PostgreSQL connection in a transaction.
    Rolls back automatically after each test to leave the DB clean.
    """
    database_url = os.getenv("DATABASE_URL", "")
    if not database_url:
        pytest.skip("DATABASE_URL not set — skipping DB integration tests")

    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    yield conn
    conn.rollback()
    conn.close()


@pytest.fixture
def storage(tmp_path: Path) -> LocalStorageAdapter:
    """Return a LocalStorageAdapter backed by a temporary directory."""
    return LocalStorageAdapter(tmp_path)


@pytest.fixture
def seeded_offering(db_conn) -> tuple[str, str]:
    """
    Upsert CS1301 course + Spring 2026 offering inside the open transaction.
    Returns (course_id, offering_id).
    """
    with db_conn.cursor() as cur:
        migrate(cur)
        return ingest_course_and_offering(cur)


# ------------------------------------------------------------------
# Helper: insert a minimal assignment directly (no SEED_FILES lookup)
# ------------------------------------------------------------------


def _insert_test_assignment(cur, offering_id: str, title: str = "Test HW") -> str:
    """Insert a throwaway assignment and return its UUID."""
    assignment_uuid = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO assignment (assignment_id, offering_id, title, due_at, language)
        VALUES (%s, %s, %s, '2026-01-30T23:59:00Z', 'python')
        """,
        (assignment_uuid, offering_id, title),
    )
    return assignment_uuid


# ------------------------------------------------------------------
# Test 1 (Sprint2 required)
# ------------------------------------------------------------------


class TestAttemptGrouping:
    """Sprint2 Test 1: attempt grouping into canonical submission + versions."""

    def test_attempt_grouping_creates_one_submission_and_multiple_versions(
        self,
        db_conn,
        storage: LocalStorageAdapter,
        seeded_offering,
        tmp_path: Path,
    ):
        """
        When the same student submits the same assignment twice:
          - submission table must have exactly 1 canonical row
          - submission_version table must have exactly 2 rows (one per attempt)
          - The canonical submission's submitted_at reflects the LATEST attempt
          - submission_map maps both attempt seed IDs to the same canonical DB ID
        """
        _, offering_id = seeded_offering

        # Unique email to avoid conflict with production data in case of leakage
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        students_df = pd.DataFrame(
            [
                {
                    "student_id": "TEST_S_GRPTEST",
                    "name": "Group Test Student",
                    "email": unique_email,
                }
            ]
        )

        with db_conn.cursor() as cur:
            # Upsert student and assignment
            student_map = ingest_students(cur, students_df)
            assert "TEST_S_GRPTEST" in student_map

            assignment_uuid = _insert_test_assignment(cur, offering_id)
            assignment_map = {"HW_GRPTEST": assignment_uuid}

            # Two attempts by the same student on the same assignment
            submissions_df = pd.DataFrame(
                [
                    {
                        "submission_id": "aaaaaaaa-0001-0001-0001-000000000001",
                        "student_id": "TEST_S_GRPTEST",
                        "assignment_id": "HW_GRPTEST",
                        "attempt_no": 1,
                        "submitted_at": "2026-01-28T10:00:00Z",
                        "due_at": "2026-01-30T23:59:00Z",
                        "status": "on_time",
                    },
                    {
                        "submission_id": "aaaaaaaa-0001-0001-0001-000000000002",
                        "student_id": "TEST_S_GRPTEST",
                        "assignment_id": "HW_GRPTEST",
                        "attempt_no": 2,
                        "submitted_at": "2026-01-31T12:00:00Z",
                        "due_at": "2026-01-30T23:59:00Z",
                        "status": "late",
                    },
                ]
            )

            # No actual seed files exist for HW_GRPTEST, so code_snapshot_path = None
            # The test focuses on the grouping logic, not file I/O
            submission_map = ingest_submissions(
                cur,
                submissions_df,
                student_map,
                assignment_map,
                offering_id,
                storage,
            )

            # ---- Assertions ----

            # 1. Exactly 1 canonical submission row
            cur.execute(
                "SELECT COUNT(*) FROM submission WHERE assignment_id = %s",
                (assignment_uuid,),
            )
            assert cur.fetchone()[0] == 1, "Expected exactly 1 canonical submission"

            # 2. submission_map maps both attempt seed IDs to the same canonical DB ID
            attempt1_id = "aaaaaaaa-0001-0001-0001-000000000001"
            attempt2_id = "aaaaaaaa-0001-0001-0001-000000000002"
            assert attempt1_id in submission_map
            assert attempt2_id in submission_map
            assert (
                submission_map[attempt1_id] == submission_map[attempt2_id]
            ), "Both attempts must map to the same canonical submission_id"

            canonical_id = submission_map[attempt1_id]

            # 3. Exactly 2 submission_version rows
            cur.execute(
                "SELECT COUNT(*) FROM submission_version WHERE submission_id = %s",
                (canonical_id,),
            )
            assert (
                cur.fetchone()[0] == 2
            ), "Expected 2 submission_version rows (one per attempt)"

            # 4. Attempt numbers are stored correctly
            cur.execute(
                "SELECT attempt_no FROM submission_version "
                "WHERE submission_id = %s ORDER BY attempt_no",
                (canonical_id,),
            )
            attempt_nos = [r[0] for r in cur.fetchall()]
            assert attempt_nos == [1, 2], "attempt_no values must be [1, 2]"

            # 5. Canonical submission's submitted_at reflects the LATEST attempt
            cur.execute(
                "SELECT submitted_at FROM submission WHERE submission_id = %s",
                (canonical_id,),
            )
            submitted_at = str(cur.fetchone()[0])
            assert (
                "2026-01-31" in submitted_at
            ), "submitted_at should reflect latest attempt (attempt2: 2026-01-31)"

    def test_idempotent_rerun_does_not_duplicate_rows(
        self,
        db_conn,
        storage: LocalStorageAdapter,
        seeded_offering,
    ):
        """
        Running ingest_submissions twice with the same data must not
        create duplicate submission or submission_version rows.
        """
        _, offering_id = seeded_offering
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        students_df = pd.DataFrame(
            [
                {
                    "student_id": "TEST_S_IDEM",
                    "name": "Idempotency Student",
                    "email": unique_email,
                }
            ]
        )

        submissions_df = pd.DataFrame(
            [
                {
                    "submission_id": "bbbbbbbb-0002-0002-0002-000000000001",
                    "student_id": "TEST_S_IDEM",
                    "assignment_id": "HW_IDEM",
                    "attempt_no": 1,
                    "submitted_at": "2026-01-28T10:00:00Z",
                    "due_at": "2026-01-30T23:59:00Z",
                    "status": "on_time",
                }
            ]
        )

        with db_conn.cursor() as cur:
            student_map = ingest_students(cur, students_df)
            assignment_uuid = _insert_test_assignment(
                cur, offering_id, "Idempotency HW"
            )
            assignment_map = {"HW_IDEM": assignment_uuid}

            # First run
            ingest_submissions(
                cur, submissions_df, student_map, assignment_map, offering_id, storage
            )
            # Second run (should be a no-op)
            ingest_submissions(
                cur, submissions_df, student_map, assignment_map, offering_id, storage
            )

            cur.execute(
                "SELECT COUNT(*) FROM submission WHERE assignment_id = %s",
                (assignment_uuid,),
            )
            assert cur.fetchone()[0] == 1, "Re-run must not duplicate submission rows"

            cur.execute(
                "SELECT COUNT(*) FROM submission_version sv "
                "JOIN submission s ON s.submission_id = sv.submission_id "
                "WHERE s.assignment_id = %s",
                (assignment_uuid,),
            )
            assert cur.fetchone()[0] == 1, "Re-run must not duplicate version rows"

    def test_single_attempt_creates_one_version(
        self,
        db_conn,
        storage: LocalStorageAdapter,
        seeded_offering,
    ):
        """A student with one attempt has submission_version count = 1."""
        _, offering_id = seeded_offering
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        students_df = pd.DataFrame(
            [
                {
                    "student_id": "TEST_S_SINGLE",
                    "name": "Single Attempt",
                    "email": unique_email,
                }
            ]
        )
        submissions_df = pd.DataFrame(
            [
                {
                    "submission_id": "cccccccc-0003-0003-0003-000000000001",
                    "student_id": "TEST_S_SINGLE",
                    "assignment_id": "HW_SINGLE",
                    "attempt_no": 1,
                    "submitted_at": "2026-01-28T10:00:00Z",
                    "due_at": "2026-01-30T23:59:00Z",
                    "status": "on_time",
                }
            ]
        )

        with db_conn.cursor() as cur:
            student_map = ingest_students(cur, students_df)
            assignment_uuid = _insert_test_assignment(
                cur, offering_id, "Single Attempt HW"
            )
            assignment_map = {"HW_SINGLE": assignment_uuid}

            submission_map = ingest_submissions(
                cur, submissions_df, student_map, assignment_map, offering_id, storage
            )

            canonical_id = submission_map["cccccccc-0003-0003-0003-000000000001"]

            cur.execute(
                "SELECT COUNT(*) FROM submission_version WHERE submission_id = %s",
                (canonical_id,),
            )
            assert cur.fetchone()[0] == 1
