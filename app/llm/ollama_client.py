"""Ollama local LLM client for feedback generation (Step 7).

Sends a feedback packet assembled from the PostgreSQL DB (via build_feedback_packet)
to the local Ollama REST API and returns a structured draft response.

Packet data flow:
    DB tables  →  build_feedback_packet()  →  packet dict
               →  generate_feedback()  →  LLM draft

All connection/model settings are loaded from environment variables (see .env):
    OLLAMA_BASE_URL            e.g. http://localhost:11434
    OLLAMA_MODEL               e.g. llama3.2
    OLLAMA_PROMPT_VERSION      e.g. v1.0
    OLLAMA_REQUEST_TIMEOUT_SEC e.g. 120

Usage:
    from app.llm import generate_feedback, OllamaUnavailableError

    packet = build_feedback_packet(submission_id, conn, storage)
    result = generate_feedback(packet)
    # result: {"draft_text": "...", "confidence": 0.82, "evidence": [...],
    #          "model_name": "llama3.2", "prompt_version": "v1.0"}
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level constants — loaded from .env with sensible fallbacks
# ---------------------------------------------------------------------------

# Ollama server endpoint (local-only; no auth required)
OLLAMA_BASE_URL: str = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

# Model tag confirmed installed via `ollama list` (llama3.2:latest, 2.0 GB)
DEFAULT_MODEL: str = os.getenv("OLLAMA_MODEL", "llama3.2")

# Prompt template version — bump when prompt structure changes
# so DB records remain traceable to the correct template
PROMPT_VERSION: str = os.getenv("OLLAMA_PROMPT_VERSION", "v1.0")

# LLM inference on CPU can take 60-90 s; 120 s gives comfortable headroom
REQUEST_TIMEOUT_SEC: float = float(os.getenv("OLLAMA_REQUEST_TIMEOUT_SEC", "120"))


# ---------------------------------------------------------------------------
# Custom exception
# ---------------------------------------------------------------------------


class OllamaUnavailableError(RuntimeError):
    """Raised when the Ollama server cannot be reached or returns a 5xx error.

    Wraps httpx.ConnectError, httpx.TimeoutException, and HTTP 5xx responses
    into a single exception type so callers can handle all LLM-reachability
    failures uniformly without catching httpx internals.
    """


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------


def _build_prompt(packet: dict[str, Any]) -> str:
    """Convert a feedback packet dict into a structured Ollama prompt string.

    This function translates DB-sourced grading data into natural-language
    sections that the LLM can reason over.  Each section below is annotated
    with the originating DB table and packet key so teammates working on the
    LLM integration can trace every field back to its source.

    Args:
        packet: Output of build_feedback_packet().  Must contain all 7 keys
            listed below.  Missing optional sub-fields are handled gracefully.

    Returns:
        A multi-section prompt string ready to POST to Ollama /api/generate.

    Packet structure reference (for LLM teammates):
        packet["assignment_title"]             str
            Source DB table : assignment.title
            Meaning         : human-readable name of the assignment being graded

        packet["rubric"]                       list[dict]
            Source DB tables: rubric JOIN rubric_item (ordered by order_index)
            Each item keys  : description (str), category (str), max_points (float)
            Meaning         : grading criteria and point allocations

        packet["latest_submission_artifacts"]  dict
            Source DB table : submission_version (attempt_no, created_at)
                              code_snapshot_path → file read by LocalStorageAdapter
            Keys            : attempt_no (int), submitted_at (str|None),
                              code_snapshot_path (str|None), code_content (str|None)
            Meaning         : the student's actual source code from the
                              most recent attempt

        packet["test_summary"]                 dict
            Source DB table : test_run (score, run_at — aggregated across all runs)
            Keys            : total_runs (int), latest_score (float|None),
                              passed_count (int), failed_count (int)
            Meaning         : overall test execution outcome for this submission

        packet["failed_tests"]                 list[dict]
            Source DB table : test_run.results_json_path → parsed JSON file on disk
            Each item keys  : test_case_id (str), score_awarded (float), output (str)
            Meaning         : individual test cases that the student did not pass

        packet["similarity_signals"]           list[dict]
            Source DB table : similarity_check (submission_a, submission_b,
                              similarity_score, method)
            Each item keys  : compared_to (str UUID of the other submission),
                              score (float 0.0-1.0), method (str e.g. "AST")
            Meaning         : plagiarism / code-similarity flags between submissions

        packet["student_history_summary"]      dict
            Source DB table : submission_version (COUNT and score aggregation
                              across all versions for this submission_id)
            Keys            : total_attempts (int), attempt_scores (list[float])
            Meaning         : how many times the student submitted and their score trend
    """
    lines: list[str] = []

    # -----------------------------------------------------------------------
    # System instruction
    # -----------------------------------------------------------------------
    lines.append(
        "You are a teaching assistant grading a Python programming assignment. "
        "Provide constructive, actionable feedback in English for the student."
    )
    lines.append("")

    # -----------------------------------------------------------------------
    # Section 1: Assignment title
    # Source DB table : assignment.title
    # Packet key      : packet["assignment_title"]  (str)
    # -----------------------------------------------------------------------
    lines.append(f"=== Assignment: {packet['assignment_title']} ===")
    lines.append("")

    # -----------------------------------------------------------------------
    # Section 2: Grading rubric
    # Source DB tables: rubric JOIN rubric_item (ordered by rubric_item.order_index)
    # Packet key      : packet["rubric"]  (list[dict])
    # Each dict       : {"description": str, "category": str, "max_points": float}
    # -----------------------------------------------------------------------
    lines.append("=== Grading Rubric ===")
    rubric: list[dict] = packet.get("rubric", [])
    if rubric:
        for i, item in enumerate(rubric, 1):
            lines.append(
                f"{i}. {item['description']} [{item['category']}]"
                f" — {item['max_points']:.0f} pts"
            )
    else:
        lines.append("  (No rubric items found)")
    lines.append("")

    # -----------------------------------------------------------------------
    # Section 3: Late submission notice (conditional)
    # Source DB columns : submission.submitted_at (TIMESTAMPTZ),
    #                     assignment.due_at (TIMESTAMPTZ)
    # Packet key        : packet["latest_submission_artifacts"]["is_late"]  (bool)
    #                     packet["latest_submission_artifacts"]["submitted_at"]
    #                     packet["latest_submission_artifacts"]["due_at"]
    # Included in prompt only when is_late is True
    # -----------------------------------------------------------------------
    artifacts: dict = packet.get("latest_submission_artifacts", {})
    if artifacts.get("is_late"):
        lines.append("=== Late Submission Notice ===")
        lines.append(
            f"This submission was received AFTER the deadline. "
            f"Due: {artifacts.get('due_at', 'N/A')}  |  "
            f"Submitted: {artifacts.get('submitted_at', 'N/A')}"
        )
        lines.append("Please mention in your feedback that this was a late submission.")
        lines.append("")

    # -----------------------------------------------------------------------
    # Section 4: Student's latest submitted code
    # Source DB table : submission_version.attempt_no, submission_version.created_at
    #                   submission_version.code_snapshot_path (stored in submission)
    #                   → file content read by LocalStorageAdapter
    # Packet key      : packet["latest_submission_artifacts"]  (dict)
    # Keys            : attempt_no (int), submitted_at (str|None),
    #                   due_at (str|None), is_late (bool),
    #                   code_snapshot_path (str|None), code_content (str|None)
    # -----------------------------------------------------------------------
    attempt_no = artifacts.get("attempt_no", "?")
    submitted_at = artifacts.get("submitted_at", "N/A")
    code_content: str = artifacts.get("code_content") or "N/A"

    lines.append(
        f"=== Student Code (attempt {attempt_no}, submitted {submitted_at}) ==="
    )
    lines.append("```python")
    lines.append(code_content)
    lines.append("```")
    lines.append("")

    # -----------------------------------------------------------------------
    # Section 5: Test run summary and failed test details
    # Source DB table : test_run.score, test_run.results_json_path, test_run.run_at
    #                   results_json_path → JSON file parsed per test case
    # Packet key (summary) : packet["test_summary"]  (dict)
    #   Keys : total_runs (int), latest_score (float|None),
    #          passed_count (int), failed_count (int)
    # Packet key (details) : packet["failed_tests"]  (list[dict])
    #   Each item : {"test_case_id": str, "score_awarded": float, "output": str}
    # -----------------------------------------------------------------------
    ts: dict = packet.get("test_summary", {})
    lines.append("=== Test Results ===")
    lines.append(f"Total test runs : {ts.get('total_runs', 0)}")
    lines.append(f"Latest score    : {ts.get('latest_score', 'N/A')} pts")
    lines.append(
        f"Passed / Failed : {ts.get('passed_count', 0)} / {ts.get('failed_count', 0)}"
    )

    failed_tests: list[dict] = packet.get("failed_tests", [])
    if failed_tests:
        lines.append("")
        lines.append("Failed test cases:")
        for ft in failed_tests:
            # Truncate long output to keep prompt within token budget
            output_preview = str(ft.get("output", ""))[:300]
            lines.append(
                f"  - [{ft['test_case_id']}] "
                f"score={ft['score_awarded']}: {output_preview}"
            )
    lines.append("")

    # -----------------------------------------------------------------------
    # Section 6: Student submission history
    # Source DB table : submission_version (COUNT(*) per submission_id)
    #                   test_run.score aggregated oldest → newest
    # Packet key      : packet["student_history_summary"]  (dict)
    #   Keys : total_attempts (int), attempt_scores (list[float])
    # -----------------------------------------------------------------------
    hist: dict = packet.get("student_history_summary", {})
    lines.append("=== Student Submission History ===")
    lines.append(f"Total attempts : {hist.get('total_attempts', 0)}")
    score_trend = " → ".join(str(s) for s in hist.get("attempt_scores", []))
    lines.append(f"Score trend    : {score_trend or 'N/A'}")
    lines.append("")

    # -----------------------------------------------------------------------
    # Section 7: Similarity / academic integrity signals  (conditional)
    # Source DB table : similarity_check
    #   Columns used  : submission_a (UUID), submission_b (UUID),
    #                   similarity_score (float), method (str)
    # Packet key      : packet["similarity_signals"]  (list[dict])
    #   Each item     : {"compared_to": str (UUID of the other submission),
    #                    "score": float (0.0-1.0), "method": str (e.g. "AST")}
    # Included in prompt only when at least one signal has score >= 0.8
    # -----------------------------------------------------------------------
    similarity_signals: list[dict] = packet.get("similarity_signals", [])
    high_sim = [s for s in similarity_signals if s.get("score", 0) >= 0.8]
    if high_sim:
        lines.append("=== Academic Integrity Warning ===")
        lines.append(
            f"High code similarity detected with {len(high_sim)} other submission(s)."
        )
        for sig in high_sim:
            lines.append(
                f"  - Method: {sig['method']}, "
                f"Score: {sig['score']:.1%}, "
                f"Compared to submission: {sig['compared_to']}"
            )
        lines.append("Please note this situation in your feedback if appropriate.")
        lines.append("")

    # -----------------------------------------------------------------------
    # Response format instruction
    # The LLM must return a JSON object matching this schema exactly.
    # Ollama's "format": "json" mode enforces JSON output (supported >= 0.1.14).
    # This example also acts as a fallback schema hint if the model ignores it.
    # -----------------------------------------------------------------------
    lines.append("=== Response Format ===")
    lines.append(
        "Respond ONLY with a valid JSON object (no markdown fences, no extra text):"
    )
    schema_example = {
        "draft_text": "Korean feedback here (constructive, specific, actionable)",
        "confidence": 0.85,
        "evidence": [
            {
                "type": "test_run",
                "pointer": "test_case_id value",
                "snippet": "relevant output excerpt",
            }
        ],
    }
    lines.append(json.dumps(schema_example, ensure_ascii=False, indent=2))

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_feedback(
    packet: dict[str, Any],
    model: str = DEFAULT_MODEL,
    base_url: str = OLLAMA_BASE_URL,
    timeout: float = REQUEST_TIMEOUT_SEC,
) -> dict[str, Any]:
    """Send a feedback packet to the local Ollama server and return the LLM draft.

    This is the primary entry point for LLM teammates integrating feedback
    generation.  The ``packet`` argument comes directly from
    ``build_feedback_packet(submission_id, conn, storage)`` and contains
    data assembled from the following DB tables:

        assignment           → packet["assignment_title"]
        rubric + rubric_item → packet["rubric"]
        submission_version + LocalStorageAdapter
                             → packet["latest_submission_artifacts"]
        test_run             → packet["test_summary"], packet["failed_tests"]
        similarity_check     → packet["similarity_signals"]
        submission_version (aggregated)
                             → packet["student_history_summary"]

    This function does NOT write to the database.  The returned dict is
    designed to be passed directly to the Step 8 DB-insert routine:
        result["draft_text"]     → llm_feedback_draft.draft_text
        result["confidence"]     → llm_feedback_draft.confidence
        result["model_name"]     → llm_feedback_draft.model_name
        result["prompt_version"] → llm_feedback_draft.prompt_version
        result["evidence"]       → llm_evidence rows (evidence_type, pointer, snippet)

    Args:
        packet: Dict returned by build_feedback_packet().  Required top-level
            keys: assignment_title, rubric, latest_submission_artifacts,
            test_summary, failed_tests, similarity_signals,
            student_history_summary.
        model: Ollama model tag.  Reads OLLAMA_MODEL from .env (default: "llama3.2").
        base_url: Ollama REST API base URL.  Reads OLLAMA_BASE_URL from .env.
        timeout: HTTP timeout in seconds.  Reads OLLAMA_REQUEST_TIMEOUT_SEC from .env.

    Returns:
        Dict with keys:
            draft_text (str)       : Generated Korean feedback text.
            confidence (float)     : LLM self-reported confidence in [0.0, 1.0].
            evidence (list[dict])  : Grounding evidence items; each has
                                     type (str), pointer (str), snippet (str).
            model_name (str)       : Model tag used — forward to llm_feedback_draft.
            prompt_version (str)   : Prompt template version —
                                     forward to llm_feedback_draft.

    Raises:
        OllamaUnavailableError: When the Ollama server is offline, times out,
            or returns an HTTP 5xx error.
        ValueError: When the LLM response cannot be parsed as JSON or is
            missing required keys (draft_text, confidence, evidence).
        httpx.HTTPStatusError: For HTTP 4xx errors (e.g., model not found) —
            these are caller errors, not server errors, so they propagate as-is.
    """
    prompt = _build_prompt(packet)

    # Payload for Ollama /api/generate endpoint.
    # "stream": False  → receive a single JSON response instead of NDJSON chunks.
    # "format": "json" → Ollama JSON mode; forces the model to output valid JSON.
    #                    Supported since Ollama 0.1.14 (installed: 0.18.1 ✓).
    payload: dict[str, Any] = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    # Send request; wrap connectivity failures into OllamaUnavailableError
    try:
        response = httpx.post(
            f"{base_url}/api/generate",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
    except (httpx.ConnectError, httpx.TimeoutException) as exc:
        raise OllamaUnavailableError(
            f"Ollama server unreachable at {base_url}: {exc}"
        ) from exc
    except httpx.HTTPStatusError as exc:
        # 5xx = server-side problem → wrap; 4xx = caller error → re-raise as-is
        if exc.response.status_code >= 500:
            raise OllamaUnavailableError(
                f"Ollama returned server error HTTP {exc.response.status_code}"
            ) from exc
        raise

    # Ollama wraps the model's text output in {"response": "...", "done": true}
    ollama_envelope: dict = response.json()
    raw_text: str = ollama_envelope.get("response", "")

    # Parse the inner JSON that the LLM was instructed to produce
    try:
        llm_data: dict = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"LLM did not return valid JSON. "
            f"Raw response (first 500 chars): {raw_text[:500]!r}"
        ) from exc

    # Validate that all required keys are present in the LLM output
    required_keys = {"draft_text", "confidence", "evidence"}
    missing = required_keys - set(llm_data.keys())
    if missing:
        raise ValueError(
            f"LLM response is missing required keys: {missing}. "
            f"Got keys: {set(llm_data.keys())}"
        )

    return {
        "draft_text": str(llm_data["draft_text"]),
        "confidence": float(llm_data["confidence"]),
        "evidence": list(llm_data.get("evidence", [])),
        # Forwarded to Step 8 for llm_feedback_draft DB insert
        "model_name": model,
        "prompt_version": PROMPT_VERSION,
    }
