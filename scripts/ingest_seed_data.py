"""Seed data -> PostgreSQL DB + Object Storage ingestion script.

Usage:
    # Load demo subset (3 submissions from demo_case_01)
    python scripts/ingest_seed_data.py --sample demo_case_01

    # Full ingestion (all 100 students x 5 assignments)
    python scripts/ingest_seed_data.py

    # Parse CSVs only, no DB/storage writes
    python scripts/ingest_seed_data.py --dry-run

Steps performed:
    0. Migration  : add submission_version.attempt_no column (IF NOT EXISTS)
    1. Course     : CS1301 / Introduction to CS
    2. Offering   : Spring 2026
    3. Students   : from students.csv
    4. Assignments: HW1-HW5 metadata
    5. Submissions: 1 canonical row per (student, assignment)
                   + submission_version row per attempt
                   + copy python_file artifact to object storage
    6. Test runs  : execution_results.csv -> test_run table
    7. Similarity : similarity_scores.csv -> similarity_check table
"""

from __future__ import annotations

import argparse
import os
import sys
import uuid
from pathlib import Path
from typing import Optional

import pandas as pd
import psycopg2
from dotenv import load_dotenv

# ------------------------------------------------------------------
# Project root setup (allow running without package install)
# ------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.storage import LocalStorageAdapter  # noqa: E402

# ------------------------------------------------------------------
# Constants
# ------------------------------------------------------------------

# Step 0 agreed demo_case_01: 3 submissions
DEMO_SUBMISSION_IDS: set[str] = {
    "cbca2439-5fa7-4a69-b4d5-57515f2ca8df",  # S001, HW1, attempt1 (on_time)
    "707ca4fc-2544-4810-b5f0-1f6e2bcff216",  # S037, HW1, attempt1 (similarity flag)
    "9d1f65ce-3975-41de-ba09-5b4220598737",  # S001, HW1, attempt2 (late)
}

SEED_META = (
    PROJECT_ROOT
    / "make_simul_data"
    / "make_simul_data"
    / "output"
    / "seed_data"
    / "metadata"
)
SEED_FILES = (
    PROJECT_ROOT
    / "make_simul_data"
    / "make_simul_data"
    / "output"
    / "seed_data"
    / "intro_cs"
    / "Assignments"
)

# HW metadata matching make_simul_data/assignments.py ASSIGNMENTS config
ASSIGNMENT_META: dict[str, dict] = {
    "HW1": {
        "title": "Variables, I/O, and Arithmetic",
        "due_at": "2026-01-30T23:59:00Z",
    },
    "HW2": {
        "title": "Conditionals and Boolean Logic",
        "due_at": "2026-02-13T23:59:00Z",
    },
    "HW3": {
        "title": "Loops and Iteration",
        "due_at": "2026-02-27T23:59:00Z",
    },
    "HW4": {
        "title": "Functions and Modular Design",
        "due_at": "2026-03-13T23:59:00Z",
    },
    "HW5": {
        "title": "Lists and Data Structures",
        "due_at": "2026-03-27T23:59:00Z",
    },
}

# Normalize similarity method names (seed CSV -> DB value)
METHOD_MAP: dict[str, str] = {
    "ast_based": "ast_based",
    "token_based": "token_jaccard",
}

# Auto-flag threshold: submissions above this similarity percentage get flagged
SIMILARITY_FLAG_THRESHOLD = 90.0


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def get_conn(database_url: str) -> psycopg2.extensions.connection:
    """Return a psycopg2 connection with autocommit=False (manual transaction)."""
    conn = psycopg2.connect(database_url)
    conn.autocommit = False
    return conn


def load_csvs() -> dict[str, pd.DataFrame]:
    """Load all 6 seed metadata CSV files."""
    return {
        "students": pd.read_csv(SEED_META / "students.csv"),
        "submissions": pd.read_csv(SEED_META / "submissions.csv"),
        "artifacts": pd.read_csv(SEED_META / "submission_artifacts.csv"),
        "executions": pd.read_csv(SEED_META / "execution_results.csv"),
        "test_cases": pd.read_csv(SEED_META / "test_case_results.csv"),
        "similarity": pd.read_csv(SEED_META / "similarity_scores.csv"),
    }


def _expand_to_full_groups(df: pd.DataFrame, filter_ids: set[str]) -> pd.DataFrame:
    """
    Return all rows whose (student_id, assignment_id) group contains at least
    one submission_id from filter_ids.

    This ensures attempt1 is included even if only attempt2 is in filter_ids.
    """
    demo_groups: set[tuple] = set(
        zip(
            df[df["submission_id"].isin(filter_ids)]["student_id"],
            df[df["submission_id"].isin(filter_ids)]["assignment_id"],
        )
    )
    mask = df.apply(
        lambda r: (r["student_id"], r["assignment_id"]) in demo_groups, axis=1
    )
    return df[mask]


# ------------------------------------------------------------------
# Step 0: Migration
# ------------------------------------------------------------------


def migrate(cur: psycopg2.extensions.cursor) -> None:
    """Add attempt_no column to submission_version if it does not already exist."""
    cur.execute(
        "ALTER TABLE submission_version " "ADD COLUMN IF NOT EXISTS attempt_no INTEGER"
    )


# ------------------------------------------------------------------
# Step 1-2: Course + Offering
# ------------------------------------------------------------------


def ingest_course_and_offering(
    cur: psycopg2.extensions.cursor,
) -> tuple[str, str]:
    """
    Upsert CS1301 course and Spring 2026 course_offering.

    Returns:
        (course_id, offering_id) as DB UUID strings
    """
    # Upsert course (unique on course_code)
    cur.execute(
        """
        INSERT INTO course (course_id, course_code, course_name)
        VALUES (gen_random_uuid(), 'CS1301', 'Introduction to CS')
        ON CONFLICT (course_code) DO NOTHING
        """
    )
    cur.execute("SELECT course_id FROM course WHERE course_code = 'CS1301'")
    course_id = str(cur.fetchone()[0])

    # Upsert offering (functional unique index: course_id + semester + year +
    # COALESCE(section,'')). ON CONFLICT DO NOTHING catches the violation;
    # then SELECT to get the actual ID.
    cur.execute(
        """
        INSERT INTO course_offering (offering_id, course_id, semester, year, instructor)
        VALUES (gen_random_uuid(), %s, 'Spring', 2026, 'TBA')
        ON CONFLICT DO NOTHING
        """,
        (course_id,),
    )
    cur.execute(
        """
        SELECT offering_id FROM course_offering
        WHERE course_id = %s AND semester = 'Spring' AND year = 2026
        """,
        (course_id,),
    )
    offering_id = str(cur.fetchone()[0])

    return course_id, offering_id


# ------------------------------------------------------------------
# Step 3: Students
# ------------------------------------------------------------------


def ingest_students(
    cur: psycopg2.extensions.cursor,
    students_df: pd.DataFrame,
    seed_ids: Optional[set[str]] = None,
) -> dict[str, str]:
    """
    Upsert students from students.csv into the student table.

    Args:
        seed_ids: Seed student_id values to include (None = all students)

    Returns:
        Mapping {seed_student_id: db_uuid}
    """
    mapping: dict[str, str] = {}
    for _, row in students_df.iterrows():
        if seed_ids and row["student_id"] not in seed_ids:
            continue
        cur.execute(
            """
            INSERT INTO student (student_id, name, email)
            VALUES (gen_random_uuid(), %s, %s)
            ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name
            RETURNING student_id
            """,
            (row["name"], row["email"]),
        )
        db_uuid = str(cur.fetchone()[0])
        mapping[row["student_id"]] = db_uuid
    return mapping


# ------------------------------------------------------------------
# Step 4: Assignments
# ------------------------------------------------------------------


def ingest_assignments(
    cur: psycopg2.extensions.cursor,
    offering_id: str,
    hw_ids: Optional[list[str]] = None,
) -> dict[str, str]:
    """
    Upsert assignments from ASSIGNMENT_META into the assignment table.

    Args:
        hw_ids: HW IDs to include (None = HW1-HW5 all)

    Returns:
        Mapping {seed_hw_id: db_uuid}
    """
    mapping: dict[str, str] = {}
    targets = hw_ids or list(ASSIGNMENT_META.keys())
    for hw_id in targets:
        meta = ASSIGNMENT_META[hw_id]
        # No unique constraint on assignment; check by offering_id + title
        cur.execute(
            "SELECT assignment_id FROM assignment"
            " WHERE offering_id = %s AND title = %s",
            (offering_id, meta["title"]),
        )
        row = cur.fetchone()
        if row:
            mapping[hw_id] = str(row[0])
        else:
            assignment_uuid = str(uuid.uuid4())
            cur.execute(
                """
                INSERT INTO assignment
                    (assignment_id, offering_id, title, due_at, language)
                VALUES (%s, %s, %s, %s, 'python')
                """,
                (assignment_uuid, offering_id, meta["title"], meta["due_at"]),
            )
            mapping[hw_id] = assignment_uuid
    return mapping


# ------------------------------------------------------------------
# Step 5: Submissions + Versions + Artifacts
# ------------------------------------------------------------------


def ingest_submissions(
    cur: psycopg2.extensions.cursor,
    submissions_df: pd.DataFrame,
    student_map: dict[str, str],
    assignment_map: dict[str, str],
    offering_id: str,
    storage: LocalStorageAdapter,
    filter_ids: Optional[set[str]] = None,
) -> dict[str, str]:
    """
    Insert one canonical submission per (student, assignment) group and one
    submission_version row per attempt. Copies the python_file artifact of
    each attempt to object storage.

    Canonical submission strategy:
      - submission_id  = attempt1's seed UUID
      - submitted_at   = latest attempt's timestamp
      - code_snapshot_path = latest attempt's stored file path

    Returns:
        Mapping {seed_submission_id: canonical_db_submission_id}
        All attempt seed IDs within a group map to the same canonical DB ID.
    """
    mapping: dict[str, str] = {}

    df = (
        _expand_to_full_groups(submissions_df, filter_ids)
        if filter_ids
        else submissions_df
    )

    for (seed_sid, hw_id), group in df.groupby(["student_id", "assignment_id"]):
        if seed_sid not in student_map or hw_id not in assignment_map:
            continue

        student_uuid = student_map[seed_sid]
        assignment_uuid = assignment_map[hw_id]
        attempts = group.sort_values("attempt_no")
        first_attempt = attempts.iloc[0]
        latest_attempt = attempts.iloc[-1]

        canonical_seed_id = str(first_attempt["submission_id"])
        latest_attempt_no = int(latest_attempt["attempt_no"])
        filename = f"{hw_id.lower()}_solution.py"

        # Copy latest attempt's python file to object storage
        seed_src = (
            SEED_FILES / hw_id / seed_sid / f"attempt{latest_attempt_no}" / filename
        )
        object_key = (
            f"offering/{offering_id}"
            f"/assignment/{assignment_uuid}"
            f"/student/{student_uuid}"
            f"/attempt/{latest_attempt_no}"
            f"/{filename}"
        )
        snapshot_path: Optional[str] = None
        if seed_src.exists():
            snapshot_path = storage.save_file(seed_src, object_key)
        else:
            print(f"  [WARN] Seed file not found: {seed_src}")

        # Upsert canonical submission (UNIQUE: assignment_id + student_id)
        cur.execute(
            """
            INSERT INTO submission (
                submission_id, assignment_id, student_id,
                submitted_at, code_snapshot_path, status
            )
            VALUES (%s, %s, %s, %s, %s, 'submitted')
            ON CONFLICT (assignment_id, student_id) DO UPDATE
                SET submitted_at       = EXCLUDED.submitted_at,
                    code_snapshot_path = EXCLUDED.code_snapshot_path
            RETURNING submission_id
            """,
            (
                canonical_seed_id,
                assignment_uuid,
                student_uuid,
                latest_attempt["submitted_at"],
                snapshot_path,
            ),
        )
        canonical_db_id = str(cur.fetchone()[0])

        # Map all attempt seed IDs to the canonical DB submission ID
        for _, attempt in attempts.iterrows():
            mapping[str(attempt["submission_id"])] = canonical_db_id

        # Insert one submission_version row per attempt
        for _, attempt in attempts.iterrows():
            attempt_no = int(attempt["attempt_no"])

            # Idempotency: skip if this attempt version already exists
            cur.execute(
                "SELECT version_id FROM submission_version "
                "WHERE submission_id = %s AND attempt_no = %s",
                (canonical_db_id, attempt_no),
            )
            if cur.fetchone():
                continue

            # Copy this attempt's file to storage for version history
            attempt_src = (
                SEED_FILES / hw_id / seed_sid / f"attempt{attempt_no}" / filename
            )
            attempt_key = (
                f"offering/{offering_id}"
                f"/assignment/{assignment_uuid}"
                f"/student/{student_uuid}"
                f"/attempt/{attempt_no}"
                f"/{filename}"
            )
            if attempt_src.exists() and not storage.exists(attempt_key):
                storage.save_file(attempt_src, attempt_key)

            cur.execute(
                """
                INSERT INTO submission_version (
                    version_id, submission_id, created_at,
                    attempt_no, diff_summary
                )
                VALUES (gen_random_uuid(), %s, %s, %s, %s)
                """,
                (
                    canonical_db_id,
                    attempt["submitted_at"],
                    attempt_no,
                    f"attempt {attempt_no}: {attempt['status']}",
                ),
            )

    return mapping


# ------------------------------------------------------------------
# Step 6: Test Runs
# ------------------------------------------------------------------


def ingest_test_runs(
    cur: psycopg2.extensions.cursor,
    submissions_df: pd.DataFrame,
    executions_df: pd.DataFrame,
    test_cases_df: pd.DataFrame,
    submission_map: dict[str, str],
    offering_id: str,
    assignment_map: dict[str, str],
    storage: LocalStorageAdapter,
    filter_sub_ids: Optional[set[str]] = None,
) -> None:
    """
    Insert test_run rows from execution_results.csv.
    Saves test_case_results JSON to object storage and records the path.
    Idempotency: skip if results_json_path already exists in test_run.
    """
    # Build seed_submission_id -> attempt_no from submissions CSV
    sid_to_attempt: dict[str, int] = {
        str(r["submission_id"]): int(r["attempt_no"])
        for _, r in submissions_df.iterrows()
    }

    df = executions_df
    if filter_sub_ids:
        df = df[df["submission_id"].isin(filter_sub_ids)]

    for _, exec_row in df.iterrows():
        seed_sub_id = str(exec_row["submission_id"])
        if seed_sub_id not in submission_map:
            continue

        canonical_db_id = submission_map[seed_sub_id]
        attempt_no = sid_to_attempt.get(seed_sub_id, 1)

        # Fetch assignment_id and student_id from the canonical submission
        cur.execute(
            "SELECT assignment_id, student_id FROM submission WHERE submission_id = %s",
            (canonical_db_id,),
        )
        sub_row = cur.fetchone()
        if not sub_row:
            continue
        assignment_uuid = str(sub_row[0])
        student_uuid = str(sub_row[1])

        # Collect test case results for this execution
        tc = test_cases_df[test_cases_df["exec_id"] == exec_row["exec_id"]]
        total_score = float(tc["score_awarded"].sum()) if not tc.empty else 0.0

        # Determine deterministic object key for results JSON
        results_key = (
            f"offering/{offering_id}"
            f"/assignment/{assignment_uuid}"
            f"/student/{student_uuid}"
            f"/attempt/{attempt_no}"
            f"/results.json"
        )
        expected_path = str(storage.root / results_key.lstrip("/"))

        # Idempotency: skip if already ingested
        cur.execute(
            "SELECT test_run_id FROM test_run WHERE results_json_path = %s",
            (expected_path,),
        )
        if cur.fetchone():
            continue

        # Save results JSON to object storage
        tc_records = (
            tc[["test_case_id", "passed", "score_awarded", "output"]].to_dict("records")
            if not tc.empty
            else []
        )
        results_path = storage.save_json(tc_records, results_key)

        runtime = (
            int(exec_row["runtime_ms"])
            if pd.notna(exec_row.get("runtime_ms"))
            else None
        )
        cur.execute(
            """
            INSERT INTO test_run (
                test_run_id, submission_id, run_at,
                score, runtime_ms, results_json_path
            )
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s)
            """,
            (
                canonical_db_id,
                exec_row["started_at"],
                total_score,
                runtime,
                results_path,
            ),
        )


# ------------------------------------------------------------------
# Step 7: Similarity
# ------------------------------------------------------------------


def ingest_similarity(
    cur: psycopg2.extensions.cursor,
    similarity_df: pd.DataFrame,
    submission_map: dict[str, str],
    offering_id: str,
    assignment_map: dict[str, str],
) -> None:
    """
    Insert similarity_check rows from similarity_scores.csv.
    Skips records where either submission is not in submission_map.
    Updates submission.status = 'flagged' when similarity >= threshold and flagged=True.
    """
    for _, row in similarity_df.iterrows():
        sub_a_seed = str(row["submission_id"])
        sub_b_seed = str(row["compared_to"])

        if sub_a_seed not in submission_map or sub_b_seed not in submission_map:
            continue  # Skip records referencing submissions not yet loaded

        sub_a_db = submission_map[sub_a_seed]
        sub_b_db = submission_map[sub_b_seed]

        cur.execute(
            "SELECT assignment_id FROM submission WHERE submission_id = %s",
            (sub_a_db,),
        )
        sub_row = cur.fetchone()
        if not sub_row:
            continue

        assignment_uuid = str(sub_row[0])
        similarity_score = float(row["similarity_pct"]) / 100.0
        method = METHOD_MAP.get(str(row["method"]), str(row["method"]))

        cur.execute(
            """
            INSERT INTO similarity_check (
                check_id, offering_id, assignment_id,
                submission_a, submission_b,
                similarity_score, method, checked_at
            )
            VALUES (gen_random_uuid(), %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT DO NOTHING
            """,
            (
                offering_id,
                assignment_uuid,
                sub_a_db,
                sub_b_db,
                similarity_score,
                method,
            ),
        )

        # Flag high-similarity submissions
        flagged = str(row.get("flagged", "False")).strip().lower() == "true"
        if float(row["similarity_pct"]) >= SIMILARITY_FLAG_THRESHOLD and flagged:
            cur.execute(
                "UPDATE submission SET status = 'flagged' WHERE submission_id = %s",
                (sub_a_db,),
            )


# ------------------------------------------------------------------
# Main
# ------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Ingest seed data into PostgreSQL DB + object storage."
    )
    parser.add_argument(
        "--sample",
        choices=["demo_case_01"],
        help="Load only a named demo subset (demo_case_01: 3 submissions)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse CSVs only; do not write to DB or storage",
    )
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env")
    database_url = os.getenv("DATABASE_URL", "")
    storage_root = os.getenv("LOCAL_STORAGE_ROOT", str(PROJECT_ROOT / "storage"))

    if not database_url:
        print("[ERROR] DATABASE_URL is not set in .env")
        sys.exit(1)

    print("=" * 50)
    print("  Seed Data Ingestion")
    print("=" * 50)
    print(f"  mode         : {args.sample or 'full'}")
    print(f"  database_url : {database_url}")
    print(f"  storage_root : {storage_root}")
    print()

    # Load CSVs
    print("Loading CSVs...")
    data = load_csvs()
    print(f"  students    : {len(data['students'])} rows")
    print(f"  submissions : {len(data['submissions'])} rows")
    print(f"  executions  : {len(data['executions'])} rows")
    print(f"  similarity  : {len(data['similarity'])} rows")
    print()

    if args.dry_run:
        print("[DRY RUN] CSV parsing successful. Exiting without DB writes.")
        return

    # Determine filter sets for demo mode
    filter_sub_ids: Optional[set[str]] = None
    filter_student_ids: Optional[set[str]] = None
    filter_hw_ids: Optional[list[str]] = None

    if args.sample == "demo_case_01":
        filter_sub_ids = DEMO_SUBMISSION_IDS
        demo_df = data["submissions"][
            data["submissions"]["submission_id"].isin(filter_sub_ids)
        ]
        filter_student_ids = set(demo_df["student_id"].unique())
        filter_hw_ids = list(demo_df["assignment_id"].unique())
        print(f"  demo students : {sorted(filter_student_ids)}")
        print(f"  demo HW IDs   : {filter_hw_ids}")
        print()

    storage = LocalStorageAdapter(storage_root)
    conn = get_conn(database_url)

    try:
        with conn.cursor() as cur:
            # Step 0: Migration
            print("[0/6] Schema migration...")
            migrate(cur)
            print("      attempt_no column ensured on submission_version")

            # Step 1: Course + Offering
            print("[1/6] Upserting course + offering...")
            course_id, offering_id = ingest_course_and_offering(cur)
            print(f"      course_id   = {course_id}")
            print(f"      offering_id = {offering_id}")

            # Step 2: Students
            print("[2/6] Upserting students...")
            student_map = ingest_students(cur, data["students"], filter_student_ids)
            print(f"      students loaded: {len(student_map)}")

            # Step 3: Assignments
            print("[3/6] Upserting assignments...")
            assignment_map = ingest_assignments(cur, offering_id, filter_hw_ids)
            for hw_id, hw_uuid in assignment_map.items():
                print(f"      {hw_id} -> {hw_uuid}")

            # Step 4: Submissions + Versions + Artifacts
            print("[4/6] Ingesting submissions + versions + artifacts...")
            submission_map = ingest_submissions(
                cur,
                data["submissions"],
                student_map,
                assignment_map,
                offering_id,
                storage,
                filter_sub_ids,
            )
            canonical_count = len(set(submission_map.values()))
            print(f"      canonical submissions : {canonical_count}")
            print(f"      total attempt mapping : {len(submission_map)}")

            # Step 5: Test Runs
            print("[5/6] Ingesting test_runs...")
            ingest_test_runs(
                cur,
                data["submissions"],
                data["executions"],
                data["test_cases"],
                submission_map,
                offering_id,
                assignment_map,
                storage,
                filter_sub_ids,
            )
            print("      done")

            # Step 6: Similarity
            print("[6/6] Ingesting similarity_checks...")
            ingest_similarity(
                cur,
                data["similarity"],
                submission_map,
                offering_id,
                assignment_map,
            )
            print("      done")

        conn.commit()
        print()
        print("=" * 50)
        print("  Ingestion complete!")
        print("=" * 50)
        print()
        print("Verify with:")
        print(
            '  psql agentic_ta -c "'
            "SELECT s.submission_id, st.name, sv.attempt_no, s.status "
            "FROM submission s "
            "JOIN student st ON s.student_id = st.student_id "
            "JOIN submission_version sv ON sv.submission_id = s.submission_id "
            'ORDER BY st.name, sv.attempt_no;"'
        )

    except Exception as exc:
        conn.rollback()
        print(f"\n[ERROR] Transaction rolled back: {exc}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
