"""Step 3-3 verification script: save a seed file and record path in DB.

Usage:
    python scripts/verify_storage.py

What it does:
    1. Saves the demo submission file (S001 / HW1 / attempt 1) via LocalStorageAdapter.
    2. Attempts to update submission.code_snapshot_path in the DB if the row exists.
    3. Prints a summary of each check.

Note:
    The submission row is inserted by Step 4 (ingest_seed_data.py).
    If the row does not exist yet, the DB update step is skipped gracefully.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# Allow running from the project root without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

from app.storage import LocalStorageAdapter  # noqa: E402

# ------------------------------------------------------------------
# Config
# ------------------------------------------------------------------

STORAGE_ROOT = os.getenv("LOCAL_STORAGE_ROOT", str(PROJECT_ROOT / "storage"))
DATABASE_URL = os.getenv("DATABASE_URL", "")

# Demo submission (Step 0 agreed demo case)
DEMO_SUBMISSION_ID = "cbca2439-5fa7-4a69-b4d5-57515f2ca8df"  # S001 / HW1 / attempt 1
DEMO_OFFERING_ID = "intro_cs"  # placeholder until DB offering UUID is known
DEMO_ASSIGNMENT_ID = "HW1"
DEMO_STUDENT_ID = "S001"
DEMO_ATTEMPT_NO = 1

SEED_FILE = (
    PROJECT_ROOT
    / "make_simul_data"
    / "make_simul_data"
    / "output"
    / "seed_data"
    / "intro_cs"
    / "Assignments"
    / "HW1"
    / "S001"
    / "attempt1"
    / "hw1_solution.py"
)

# Object key follows Step 0 convention
OBJECT_KEY = (
    f"offering/{DEMO_OFFERING_ID}"
    f"/assignment/{DEMO_ASSIGNMENT_ID}"
    f"/student/{DEMO_STUDENT_ID}"
    f"/attempt/{DEMO_ATTEMPT_NO}"
    f"/hw1_solution.py"
)


def check_storage() -> str:
    """Save the demo seed file and return the stored path."""
    adapter = LocalStorageAdapter(STORAGE_ROOT)
    stored_path = adapter.save_file(SEED_FILE, OBJECT_KEY)
    loaded = adapter.load_text(OBJECT_KEY)

    print(f"[PASS] File saved  : {stored_path}")
    print(f"[PASS] File loaded : {len(loaded)} chars")
    return stored_path


def check_db(stored_path: str) -> None:
    """Update submission.code_snapshot_path if the submission row exists."""
    if not DATABASE_URL:
        print("[SKIP] DATABASE_URL not set — skipping DB check")
        return

    try:
        import psycopg2
    except ImportError:
        print("[SKIP] psycopg2 not installed — skipping DB check")
        return

    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = True
        with conn.cursor() as cur:
            # Check if submission row exists (inserted by Step 4)
            cur.execute(
                "SELECT submission_id FROM submission WHERE submission_id = %s",
                (DEMO_SUBMISSION_ID,),
            )
            row = cur.fetchone()

            if row is None:
                print(
                    "[SKIP] Submission row not found in DB "
                    f"(id={DEMO_SUBMISSION_ID}). Run Step 4 first."
                )
            else:
                cur.execute(
                    "UPDATE submission SET code_snapshot_path = %s "
                    "WHERE submission_id = %s",
                    (stored_path, DEMO_SUBMISSION_ID),
                )
                cur.execute(
                    "SELECT code_snapshot_path FROM submission"
                    " WHERE submission_id = %s",
                    (DEMO_SUBMISSION_ID,),
                )
                saved = cur.fetchone()[0]
                print(f"[PASS] DB path updated: {saved}")
        conn.close()
    except Exception as exc:
        print(f"[FAIL] DB error: {exc}")


def main() -> None:
    print("=== Step 3-3: Object Storage Verification ===")
    print(f"  storage_root : {STORAGE_ROOT}")
    print(f"  seed_file    : {SEED_FILE}")
    print(f"  object_key   : {OBJECT_KEY}")
    print()

    if not SEED_FILE.exists():
        print(f"[FAIL] Seed file not found: {SEED_FILE}")
        sys.exit(1)

    stored_path = check_storage()
    check_db(stored_path)

    print()
    print("Done.")


if __name__ == "__main__":
    main()
