"""Step 7-3 verification script: generate an LLM feedback draft for a single submission.

Connects to PostgreSQL, assembles the feedback packet via build_feedback_packet(),
then sends it to the local Ollama server via generate_feedback().

Usage:
    # Use the hardcoded demo submission (S001 / HW1 / attempt 1)
    python scripts/generate_feedback_draft.py --demo

    # Use a specific submission UUID
    python scripts/generate_feedback_draft.py --submission-id <uuid>

    # Build and print the packet only — skip the Ollama call
    # (useful when Ollama is offline)
    python scripts/generate_feedback_draft.py --demo --dry-run

    # Override model or base URL from the command line
    python scripts/generate_feedback_draft.py --demo --model llama3.2 --base-url http://localhost:11434

Environment variables (loaded from .env):
    DATABASE_URL               PostgreSQL connection string
    LOCAL_STORAGE_ROOT         Root directory for artifact storage
    OLLAMA_BASE_URL            Ollama server base URL
    OLLAMA_MODEL               Ollama model tag
    OLLAMA_REQUEST_TIMEOUT_SEC HTTP timeout in seconds
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow running from the project root without installing the package
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import os  # noqa: E402

import psycopg2  # noqa: E402
from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env")

from app.llm import OllamaUnavailableError, generate_feedback  # noqa: E402
from app.services import build_feedback_packet, save_draft  # noqa: E402
from app.storage import LocalStorageAdapter  # noqa: E402

# ---------------------------------------------------------------------------
# Config (from .env)
# ---------------------------------------------------------------------------

DATABASE_URL: str = os.getenv("DATABASE_URL", "")
STORAGE_ROOT: str = os.getenv("LOCAL_STORAGE_ROOT", str(PROJECT_ROOT / "storage"))

# These values are also read inside generate_feedback() via os.getenv,
# but we read them here as CLI argument defaults for override support.
DEFAULT_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# Demo submission agreed in Step 0: S001 / HW1 / attempt 1 (on_time, 100 pts)
DEMO_SUBMISSION_ID = "cbca2439-5fa7-4a69-b4d5-57515f2ca8df"


# ---------------------------------------------------------------------------
# CLI argument parsing
# ---------------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description=(
            "Generate an LLM feedback draft for a submission (Step 7-3 verification)."
        )
    )

    id_group = parser.add_mutually_exclusive_group(required=True)
    id_group.add_argument(
        "--submission-id",
        metavar="UUID",
        help="UUID of the target submission row.",
    )
    id_group.add_argument(
        "--demo",
        action="store_true",
        help=f"Use the hardcoded demo submission ID ({DEMO_SUBMISSION_ID}).",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build and print the feedback packet, but skip the Ollama call.",
    )
    parser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Ollama model tag to use (default: {DEFAULT_MODEL}).",
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Ollama server base URL (default: {DEFAULT_BASE_URL}).",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    """Entry point: build feedback packet, optionally call Ollama, print results."""
    args = _parse_args()

    submission_id: str = DEMO_SUBMISSION_ID if args.demo else args.submission_id

    # --- Validate environment ---
    if not DATABASE_URL:
        print("[ERROR] DATABASE_URL is not set. Check your .env file.", file=sys.stderr)
        sys.exit(1)

    # --- Connect to PostgreSQL ---
    print(f"[INFO] Connecting to database: {DATABASE_URL}")
    try:
        conn = psycopg2.connect(DATABASE_URL)
        conn.autocommit = False
    except Exception as exc:
        print(f"[ERROR] Cannot connect to database: {exc}", file=sys.stderr)
        sys.exit(1)

    storage = LocalStorageAdapter(STORAGE_ROOT)

    # --- Build feedback packet from DB data ---
    print(f"[INFO] Building feedback packet for submission: {submission_id}")
    try:
        packet = build_feedback_packet(submission_id, conn, storage)
    except ValueError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    # Print the assembled packet so teammates can inspect the DB data structure
    print("\n=== Feedback Packet (assembled from DB) ===")
    print(json.dumps(packet, indent=2, default=str))

    if args.dry_run:
        print("\n[DRY RUN] Skipping Ollama call. Packet printed above.")
        conn.close()
        return

    # --- Call Ollama LLM ---
    print(
        f"\n[INFO] Sending packet to Ollama ({args.base_url}, model={args.model}) ..."
    )
    try:
        result = generate_feedback(packet, model=args.model, base_url=args.base_url)
    except OllamaUnavailableError as exc:
        print(f"\n[FAIL] Ollama is unavailable: {exc}", file=sys.stderr)
        print(
            "[HINT] Run `ollama serve` and ensure the model is pulled: "
            f"`ollama pull {args.model}`",
            file=sys.stderr,
        )
        conn.close()
        sys.exit(1)
    except ValueError as exc:
        print(f"\n[FAIL] LLM response parsing error: {exc}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    # --- Print results ---
    print("\n=== LLM Feedback Draft ===")
    print(result["draft_text"])
    print(f"\nConfidence   : {result['confidence']:.2f}")
    print(f"Model        : {result['model_name']}")
    print(f"Prompt ver.  : {result['prompt_version']}")
    print(f"Evidence     : {len(result['evidence'])} item(s)")
    for i, ev in enumerate(result["evidence"], 1):
        print(f"  [{i}] type={ev.get('type')}  pointer={ev.get('pointer')}")

    # --- Save to DB: llm_feedback_draft + llm_evidence ---
    print("\n[INFO] Saving draft to database ...")
    try:
        draft_id = save_draft(submission_id, result, conn)
        print(f"[SAVED] draft_id: {draft_id}")
    except Exception as exc:
        print(f"[ERROR] Failed to save draft: {exc}", file=sys.stderr)
        conn.close()
        sys.exit(1)

    conn.close()


if __name__ == "__main__":
    main()
