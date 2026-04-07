"""Integration tests for Feedback Packet Builder (Step 6).

Sprint2 Test 2 (required):
    test_feedback_packet_builder_includes_required_sections

All tests run inside a transaction that is rolled back on teardown,
so they leave the real DB clean after each run.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path

import psycopg2
import pytest
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(PROJECT_ROOT / ".env")

from app.services import build_feedback_packet  # noqa: E402
from app.storage import LocalStorageAdapter  # noqa: E402

# ------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------


@pytest.fixture
def db_conn():
    """Open a real PostgreSQL connection in a transaction.
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


# ------------------------------------------------------------------
# Helper: insert minimum required rows for feedback packet tests
# ------------------------------------------------------------------


def _seed_packet_data(cur, storage: LocalStorageAdapter) -> str:
    """Insert the minimum set of DB rows needed to call build_feedback_packet.

    Returns the canonical submission_id (UUID string).
    """
    # course
    course_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO course (course_id, course_code, course_name) VALUES (%s, %s, %s)",
        (course_id, f"CS_TEST_{uuid.uuid4().hex[:6]}", "Test Course"),
    )

    # course_offering
    offering_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO course_offering (offering_id, course_id, semester, year)
        VALUES (%s, %s, 'Spring', 2026)
        """,
        (offering_id, course_id),
    )

    # student
    student_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO student (student_id, name, email) VALUES (%s, %s, %s)",
        (student_id, "Packet Test Student", f"pkt_{uuid.uuid4().hex[:8]}@test.com"),
    )

    # assignment
    assignment_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO assignment (assignment_id, offering_id, title, due_at, language)
        VALUES (%s, %s, %s, '2026-01-30T23:59:00Z', 'python')
        """,
        (assignment_id, offering_id, "Variables, I/O, and Arithmetic"),
    )

    # rubric + rubric_item
    rubric_id = str(uuid.uuid4())
    cur.execute(
        "INSERT INTO rubric (rubric_id, assignment_id, total_points)"
        " VALUES (%s, %s, 100)",
        (rubric_id, assignment_id),
    )
    cur.execute(
        """
        INSERT INTO rubric_item
            (rubric_item_id, rubric_id, description, category, max_points, order_index)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (str(uuid.uuid4()), rubric_id, "Correct output", "Correctness", 60, 0),
    )
    cur.execute(
        """
        INSERT INTO rubric_item
            (rubric_item_id, rubric_id, description, category, max_points, order_index)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (str(uuid.uuid4()), rubric_id, "Code style", "Style", 40, 1),
    )

    # Save a dummy results.json to storage
    results_data = [
        {
            "test_case_id": "tc_01",
            "passed": True,
            "score_awarded": 30.0,
            "output": "OK",
        },
        {
            "test_case_id": "tc_02",
            "passed": False,
            "score_awarded": 0.0,
            "output": "Wrong answer",
        },
    ]
    results_key = (
        f"offering/{offering_id}/assignment/{assignment_id}"
        f"/student/{student_id}/attempt/1/results.json"
    )
    results_path = storage.save_json(results_data, results_key)

    # submission
    submission_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO submission
            (submission_id, assignment_id, student_id, submitted_at, status)
        VALUES (%s, %s, %s, '2026-01-28T10:00:00Z', 'submitted')
        """,
        (submission_id, assignment_id, student_id),
    )

    # submission_version
    version_id = str(uuid.uuid4())
    cur.execute(
        """
        INSERT INTO submission_version (version_id, submission_id, attempt_no)
        VALUES (%s, %s, 1)
        """,
        (version_id, submission_id),
    )

    # test_run (schema-compatible insert: with or without version_id)
    cur.execute(
        """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.columns
            WHERE table_schema = current_schema()
              AND table_name = 'test_run'
              AND column_name = 'version_id'
        )
        """
    )
    has_test_run_version = bool(cur.fetchone()[0])

    if has_test_run_version:
        cur.execute(
            """
            INSERT INTO test_run
                (test_run_id, submission_id, version_id, score, results_json_path)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), submission_id, version_id, 75.0, results_path),
        )
    else:
        cur.execute(
            """
            INSERT INTO test_run
                (test_run_id, submission_id, score, results_json_path)
            VALUES (%s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), submission_id, 75.0, results_path),
        )

    return submission_id


# ------------------------------------------------------------------
# Test 2 (Sprint2 required)
# ------------------------------------------------------------------


REQUIRED_KEYS = {
    "assignment_title",
    "rubric",
    "latest_submission_artifacts",
    "test_summary",
    "failed_tests",
    "similarity_signals",
    "student_history_summary",
}


class TestFeedbackPacketBuilder:
    """Sprint2 Test 2: build_feedback_packet returns all required sections."""

    def test_feedback_packet_builder_includes_required_sections(
        self,
        db_conn,
        storage: LocalStorageAdapter,
    ):
        """build_feedback_packet must return a dict with all required keys.

        Verifies:
        - All REQUIRED_KEYS are present in the returned dict
        - List-type fields are safe even when some optional data is absent
        - Core field values reflect the seeded data correctly
        """
        with db_conn.cursor() as cur:
            submission_id = _seed_packet_data(cur, storage)

        packet = build_feedback_packet(submission_id, db_conn, storage)

        # 1. All required keys must be present
        assert REQUIRED_KEYS.issubset(
            packet.keys()
        ), f"Missing keys: {REQUIRED_KEYS - packet.keys()}"

        # 2. List fields must be lists (safe even when empty)
        assert isinstance(packet["rubric"], list)
        assert isinstance(packet["failed_tests"], list)
        assert isinstance(packet["similarity_signals"], list)
        assert isinstance(packet["student_history_summary"]["attempt_scores"], list)

        # 3. Values reflect seeded data
        assert packet["assignment_title"] == "Variables, I/O, and Arithmetic"
        assert len(packet["rubric"]) == 2
        assert packet["rubric"][0]["description"] == "Correct output"
        assert packet["rubric"][0]["max_points"] == 60.0

        # 4. test_summary is populated
        assert packet["test_summary"]["total_runs"] == 1
        assert packet["test_summary"]["latest_score"] == 75.0

        # 5. failed_tests extracted from results.json
        assert len(packet["failed_tests"]) == 1
        assert packet["failed_tests"][0]["test_case_id"] == "tc_02"

        # 6. student_history_summary
        assert packet["student_history_summary"]["total_attempts"] == 1
        assert packet["student_history_summary"]["attempt_scores"] == [75.0]

        # 7. similarity_signals is a list (no data seeded, so empty is correct)
        assert packet["similarity_signals"] == []

    def test_feedback_packet_missing_submission_raises(
        self,
        db_conn,
        storage: LocalStorageAdapter,
    ):
        """build_feedback_packet raises ValueError for an unknown submission_id."""
        nonexistent_id = str(uuid.uuid4())
        with pytest.raises(ValueError, match="submission not found"):
            build_feedback_packet(nonexistent_id, db_conn, storage)
