"""End-to-end demo script for the AI TA feedback lifecycle (Sprint 3, Step 6).

Runs the full pipeline in a single script:
  submission -> LLM draft generation -> TA review -> approval -> publish

Usage:
    # Full demo with mock LLM (no Ollama required — recommended for presentations)
    python scripts/demo_e2e.py --mock-llm

    # Full demo with real Ollama LLM
    python scripts/demo_e2e.py

    # API mode (not yet implemented)
    python scripts/demo_e2e.py --api-mode

Environment variables (loaded from .env):
    DATABASE_URL               PostgreSQL connection string
    LOCAL_STORAGE_ROOT         Root directory for artifact storage
    OLLAMA_BASE_URL            Ollama server base URL
    OLLAMA_MODEL               Ollama model tag
    OLLAMA_REQUEST_TIMEOUT_SEC HTTP timeout in seconds
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

# Allow running from the project root without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import psycopg2  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

from app.llm import OllamaUnavailableError  # noqa: E402
from app.services import (  # noqa: E402
    approve_draft,
    build_feedback_packet,
    get_draft_detail,
    list_drafts,
    publish_draft,
    trigger_feedback_generation,
)
from app.storage import LocalStorageAdapter  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
STORAGE_ROOT: str = os.getenv("LOCAL_STORAGE_ROOT", str(PROJECT_ROOT / "storage"))

# Canonical submission IDs from demo_case_01 ingestion.
# S001/HW1 attempt1 seed ID becomes the canonical submission_id.
# S037/HW1 attempt1 seed ID becomes the canonical submission_id.
# S001/HW1 attempt2 maps to the SAME canonical submission as attempt1.
DEMO_CANONICAL_IDS: list[str] = [
    "cbca2439-5fa7-4a69-b4d5-57515f2ca8df",  # S001/HW1 (on_time, 100pts)
    "707ca4fc-2544-4810-b5f0-1f6e2bcff216",  # S037/HW1 (similarity flag)
]

# Human-readable labels for log output
DEMO_LABELS: dict[str, str] = {
    "cbca2439-5fa7-4a69-b4d5-57515f2ca8df": "S001/HW1 (normal, on_time)",
    "707ca4fc-2544-4810-b5f0-1f6e2bcff216": "S037/HW1 (similarity flag)",
}

# Hardcoded mock response matching generate_feedback() return schema
MOCK_LLM_RESPONSE: dict = {
    "draft_text": (
        "Overall good work on this assignment. Your code demonstrates "
        "a solid understanding of variables and basic I/O operations. "
        "Consider adding more descriptive variable names for clarity. "
        "Your arithmetic logic is correct but could benefit from "
        "additional inline comments explaining the computation steps."
    ),
    "confidence": 0.82,
    "evidence": [
        {
            "type": "test_run",
            "pointer": "test_basic_io",
            "snippet": "All basic I/O test cases passed",
        },
        {
            "type": "code_snippet",
            "pointer": "hw1_solution.py#L1-L20",
            "snippet": "Variable naming could be more descriptive",
        },
    ],
    "model_name": "mock-llm",
    "prompt_version": "v1.0-mock",
}


# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------


def setup_logging(timestamp: str) -> logging.Logger:
    """Configure dual-handler logging: console (INFO) + file (DEBUG).

    Creates logs/ directory if needed.
    Log file: logs/demo_e2e_{timestamp}.log

    Args:
        timestamp: Formatted timestamp string for the log filename.

    Returns:
        Configured logger instance.
    """
    log_dir = PROJECT_ROOT / "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_path = log_dir / f"demo_e2e_{timestamp}.log"

    logger = logging.getLogger("demo_e2e")
    logger.setLevel(logging.DEBUG)
    # Prevent duplicate handlers on repeated runs in the same process
    logger.handlers.clear()

    # File handler: detailed format matching Sprint 3 spec
    fh = logging.FileHandler(log_path, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(
        logging.Formatter(
            "%(asctime)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Console handler: concise output
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter("%(message)s"))

    logger.addHandler(fh)
    logger.addHandler(ch)

    logger.info(f"Log file: {log_path}")
    return logger


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=("End-to-end demo: submission -> LLM draft -> TA review -> publish")
    )
    parser.add_argument(
        "--mock-llm",
        action="store_true",
        help="Use hardcoded mock LLM response instead of calling Ollama.",
    )
    parser.add_argument(
        "--api-mode",
        action="store_true",
        help="(Not yet implemented) Launch FastAPI and call via HTTP.",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Phase 0: DB connection + migration check
# ---------------------------------------------------------------------------


def check_db_and_migrations(
    conn: psycopg2.extensions.connection,
    logger: logging.Logger,
) -> None:
    """Verify DB connection and that required tables/columns exist.

    Checks:
        - submission table exists and has rows
        - llm_feedback_draft table has status column (migration applied)

    Raises:
        SystemExit on failure.
    """
    with conn.cursor() as cur:
        # Check submission table has data
        cur.execute("SELECT COUNT(*) FROM submission")
        count = cur.fetchone()[0]
        logger.info(f"  DB check: submission table has {count} row(s)")
        if count == 0:
            logger.error(
                "  No submissions found. "
                "Run: python scripts/ingest_seed_data.py --sample demo_case_01"
            )
            sys.exit(1)

        # Check migration: status column on llm_feedback_draft
        cur.execute(
            "SELECT column_name FROM information_schema.columns "
            "WHERE table_name = 'llm_feedback_draft' AND column_name = 'status'"
        )
        if not cur.fetchone():
            logger.error(
                "  Migration not applied. "
                "Run: psql -f db/migrations/add_draft_status.sql"
            )
            sys.exit(1)
        logger.info("  DB check: llm_feedback_draft.status column exists")


# ---------------------------------------------------------------------------
# Phase 1: Preparation
# ---------------------------------------------------------------------------


def verify_seed_data(
    conn: psycopg2.extensions.connection,
    logger: logging.Logger,
) -> list[str]:
    """Verify demo submissions exist in DB and return validated canonical IDs.

    Queries the submission table for each DEMO_CANONICAL_IDS entry and logs
    student name + assignment title for each found submission.

    Returns:
        List of verified submission_id strings.

    Raises:
        SystemExit if no demo submissions found.
    """
    verified: list[str] = []
    with conn.cursor() as cur:
        for sub_id in DEMO_CANONICAL_IDS:
            cur.execute(
                "SELECT s.submission_id, st.name, a.title, s.status "
                "FROM submission s "
                "JOIN student st ON s.student_id = st.student_id "
                "JOIN assignment a ON a.assignment_id = s.assignment_id "
                "WHERE s.submission_id = %s",
                (sub_id,),
            )
            row = cur.fetchone()
            if row:
                verified.append(sub_id)
                logger.info(
                    f"  Found: {sub_id[:8]}... | {row[1]} | {row[2]} | "
                    f"status={row[3]}"
                )
            else:
                logger.warning(f"  NOT FOUND: {sub_id} — skipping")

    if not verified:
        logger.error(
            "No demo submissions found. "
            "Run: python scripts/ingest_seed_data.py --sample demo_case_01"
        )
        sys.exit(1)

    logger.info(
        f"  Verified {len(verified)} canonical submission(s) "
        "(from 3 seed IDs, 2 canonical)"
    )
    return verified


def ensure_demo_ta(
    conn: psycopg2.extensions.connection,
    logger: logging.Logger,
) -> str:
    """Upsert a demo TA record and return the ta_id.

    Uses ON CONFLICT (email) DO UPDATE to ensure idempotency.

    Returns:
        ta_id as a UUID string.
    """
    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO ta (name, email) "
            "VALUES ('Demo TA', 'demo_ta@gsu.edu') "
            "ON CONFLICT (email) DO UPDATE SET name = EXCLUDED.name "
            "RETURNING ta_id"
        )
        ta_id = str(cur.fetchone()[0])
    conn.commit()
    logger.info(f"  Demo TA: ta_id={ta_id[:8]}...")
    return ta_id


def cleanup_previous_drafts(
    submission_ids: list[str],
    conn: psycopg2.extensions.connection,
    logger: logging.Logger,
) -> None:
    """Delete existing drafts for demo submissions to ensure idempotent reruns.

    llm_evidence rows are removed automatically via ON DELETE CASCADE.
    """
    with conn.cursor() as cur:
        for sub_id in submission_ids:
            cur.execute(
                "DELETE FROM llm_feedback_draft WHERE submission_id = %s",
                (sub_id,),
            )
            deleted = cur.rowcount
            if deleted:
                logger.info(f"  Cleaned up {deleted} old draft(s) for {sub_id[:8]}...")
    conn.commit()


# ---------------------------------------------------------------------------
# Phase 2: LLM feedback generation
# ---------------------------------------------------------------------------


def _mock_generate_feedback(packet: dict, **kwargs: object) -> dict:
    """Return a hardcoded mock response matching generate_feedback() schema."""
    return MOCK_LLM_RESPONSE.copy()


def run_generation_phase(
    submission_ids: list[str],
    conn: psycopg2.extensions.connection,
    storage: LocalStorageAdapter,
    logger: logging.Logger,
    mock_llm: bool,
) -> dict[str, str]:
    """Generate LLM feedback drafts for each demo submission.

    For each submission:
        1. build_feedback_packet() -> log packet summary
        2. trigger_feedback_generation() (patched if mock_llm) -> log result
        3. Log draft_id, confidence, text preview, and timing

    Args:
        submission_ids: List of canonical submission UUIDs.
        conn: Active psycopg2 connection.
        storage: LocalStorageAdapter instance.
        logger: Logger instance.
        mock_llm: Whether to use mock LLM instead of Ollama.

    Returns:
        Mapping {submission_id: draft_id} for successfully generated drafts.
    """
    draft_map: dict[str, str] = {}

    for i, sub_id in enumerate(submission_ids, 1):
        label = DEMO_LABELS.get(sub_id, sub_id[:8])
        logger.info(f"CASE {i}: {label}")

        try:
            # Build packet separately for logging (read-only, minimal overhead)
            t0 = time.time()
            packet = build_feedback_packet(sub_id, conn, storage)
            packet_time = time.time() - t0
            section_count = sum(1 for v in packet.values() if v)
            logger.info(f"  packet_build: {packet_time:.2f}s, sections={section_count}")

            # Generate + save via trigger_feedback_generation
            t1 = time.time()
            if mock_llm:
                with patch(
                    "app.services.feedback_service.generate_feedback",
                    side_effect=_mock_generate_feedback,
                ):
                    draft_id = trigger_feedback_generation(sub_id, conn, storage)
            else:
                draft_id = trigger_feedback_generation(sub_id, conn, storage)
            gen_time = time.time() - t1

            # Log LLM response summary from the saved draft
            drafts = list_drafts(sub_id, conn)
            if drafts:
                latest = drafts[0]
                text_preview = latest["draft_text"][:200]
                logger.info(
                    f"  llm_response: {gen_time:.2f}s, "
                    f"confidence={latest['confidence']}, "
                    f"text={text_preview!r}"
                )

            logger.info(f"  save_draft: draft_id={draft_id[:8]}..., status=pending")
            logger.info(f"CASE {i}: SUCCESS")
            draft_map[sub_id] = draft_id

        except OllamaUnavailableError as exc:
            logger.error(f"  FAIL: Ollama unavailable — {exc}")
            logger.error("  HINT: Use --mock-llm or run `ollama serve`")
            logger.debug(traceback.format_exc())
        except Exception as exc:
            logger.error(f"  FAIL: {exc.__class__.__name__}: {exc}")
            logger.debug(traceback.format_exc())

    return draft_map


# ---------------------------------------------------------------------------
# Phase 3: TA review workflow
# ---------------------------------------------------------------------------


def run_review_phase(
    draft_map: dict[str, str],
    ta_id: str,
    conn: psycopg2.extensions.connection,
    logger: logging.Logger,
) -> None:
    """Demonstrate the TA review workflow for each generated draft.

    For each draft:
        a. list_drafts()      -> show draft list
        b. get_draft_detail() -> show detail + evidence count
        c. approve_draft()    -> pending -> approved
        d. publish_draft()    -> approved -> published
    """
    for sub_id, draft_id in draft_map.items():
        label = DEMO_LABELS.get(sub_id, sub_id[:8])
        logger.info(f"REVIEW: {label}")

        # a. List drafts for the submission
        drafts = list_drafts(sub_id, conn)
        logger.info(f"  list_drafts: {len(drafts)} draft(s) for {sub_id[:8]}...")

        # b. Get draft detail with evidence
        detail = get_draft_detail(draft_id, conn)
        ev_count = len(detail.get("evidence", []))
        logger.info(
            f"  get_draft_detail: draft_id={draft_id[:8]}..., "
            f"confidence={detail['confidence']}, evidence={ev_count}"
        )

        # c. Approve draft (pending -> approved)
        t0 = time.time()
        approved = approve_draft(draft_id, ta_id, conn)
        approve_time = time.time() - t0
        logger.info(
            f"  approve: {approve_time:.2f}s, "
            f"status={approved['status']}, by ta_id={ta_id[:8]}..."
        )

        # d. Publish draft (approved -> published)
        t0 = time.time()
        published = publish_draft(draft_id, conn)
        publish_time = time.time() - t0
        logger.info(f"  publish: {publish_time:.2f}s, status={published['status']}")


# ---------------------------------------------------------------------------
# Phase 4: Final state
# ---------------------------------------------------------------------------


def print_final_state(
    submission_ids: list[str],
    conn: psycopg2.extensions.connection,
    logger: logging.Logger,
) -> None:
    """Query and display the final DB state for all demo drafts."""
    logger.info("=" * 60)
    logger.info("FINAL DB STATE")
    logger.info("=" * 60)

    with conn.cursor() as cur:
        for sub_id in submission_ids:
            cur.execute(
                "SELECT d.draft_id, d.status, d.confidence, "
                "       d.model_name, d.approved_by, "
                "       d.approved_at, d.published_at "
                "FROM llm_feedback_draft d "
                "WHERE d.submission_id = %s "
                "ORDER BY d.generated_at DESC",
                (sub_id,),
            )
            rows = cur.fetchall()
            label = DEMO_LABELS.get(sub_id, sub_id[:8])
            logger.info(f"  {label}:")
            for row in rows:
                logger.info(
                    f"    draft={str(row[0])[:8]}... status={row[1]} "
                    f"confidence={row[2]} model={row[3]} "
                    f"approved_at={row[5]} published_at={row[6]}"
                )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: run the full E2E demo pipeline."""
    args = _parse_args()

    if args.api_mode:
        print("[NOT IMPLEMENTED] --api-mode will be available in a future sprint.")
        sys.exit(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    logger = setup_logging(timestamp)

    logger.info("DEMO START")
    logger.info(f"  mode: {'mock-llm' if args.mock_llm else 'live-llm'}")
    logger.info(f"  timestamp: {timestamp}")
    demo_start = time.time()

    # --- Validate environment ---
    if not DATABASE_URL:
        logger.error("DATABASE_URL is not set. Check your .env file.")
        sys.exit(1)

    # --- Connect to PostgreSQL ---
    logger.info(f"  database: {DATABASE_URL}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
    except Exception as exc:
        logger.error(f"Cannot connect to database: {exc}")
        sys.exit(1)

    storage = LocalStorageAdapter(STORAGE_ROOT)

    try:
        # Phase 0: DB + migration check
        logger.info("=" * 60)
        logger.info("PHASE 0: DB connection + migration check")
        check_db_and_migrations(conn, logger)

        # Phase 1: Verify seed data + prepare TA + cleanup
        logger.info("=" * 60)
        logger.info("PHASE 1: Verify seed data (demo_case_01)")
        submission_ids = verify_seed_data(conn, logger)
        ta_id = ensure_demo_ta(conn, logger)
        cleanup_previous_drafts(submission_ids, conn, logger)

        # Phase 2: Generate LLM feedback drafts
        logger.info("=" * 60)
        logger.info("PHASE 2: Generate LLM feedback drafts")
        draft_map = run_generation_phase(
            submission_ids, conn, storage, logger, args.mock_llm
        )

        if not draft_map:
            logger.error("No drafts generated. Cannot proceed to review phase.")
            sys.exit(1)

        # Phase 3: TA review workflow
        logger.info("=" * 60)
        logger.info(
            "PHASE 3: TA review workflow " "(list -> detail -> approve -> publish)"
        )
        run_review_phase(draft_map, ta_id, conn, logger)

        # Phase 4: Final state
        print_final_state(submission_ids, conn, logger)

        # Summary
        total_time = time.time() - demo_start
        passed = len(draft_map)
        total = len(submission_ids)
        logger.info("=" * 60)
        logger.info(
            f"DEMO COMPLETE: {passed}/{total} cases passed " f"in {total_time:.1f}s"
        )
        logger.info("=" * 60)

    except Exception as exc:
        logger.error(f"Unhandled error: {exc}")
        logger.debug(traceback.format_exc())
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
