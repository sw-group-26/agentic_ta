"""Unit tests for Ollama LLM client (Step 7).

All tests use unittest.mock to patch httpx.post — no real Ollama server or
DB connection required.

Sprint 2 required test:
    Test 3: test_ollama_client_handles_local_failure_gracefully
"""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import MagicMock, patch

import httpx
import pytest

from app.llm import OllamaUnavailableError, generate_feedback

# ---------------------------------------------------------------------------
# Shared fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_packet() -> dict[str, Any]:
    """Minimal feedback packet matching build_feedback_packet() output shape.

    Reflects the exact 7-key structure returned by app/services/feedback_packet.py.
    Each key maps to a DB source as documented in ollama_client._build_prompt().
    """
    return {
        # Source: assignment.title
        "assignment_title": "HW1 - Variables, I/O, and Arithmetic",
        # Source: rubric JOIN rubric_item
        "rubric": [
            {
                "description": "Correct output for all test cases",
                "category": "Correctness",
                "max_points": 60.0,
            },
            {
                "description": "Code readability and style",
                "category": "Style",
                "max_points": 40.0,
            },
        ],
        # Source: submission_version + LocalStorageAdapter
        "latest_submission_artifacts": {
            "attempt_no": 1,
            "submitted_at": "2026-01-28T10:00:00Z",
            "code_snapshot_path": None,
            "code_content": "x = int(input())\nprint(x * 2)",
        },
        # Source: test_run (aggregated)
        "test_summary": {
            "total_runs": 2,
            "latest_score": 60.0,
            "passed_count": 1,
            "failed_count": 1,
        },
        # Source: test_run.results_json_path -> parsed JSON
        "failed_tests": [
            {
                "test_case_id": "tc_02",
                "score_awarded": 0.0,
                "output": "Expected 42, got 0",
            }
        ],
        # Source: similarity_check
        "similarity_signals": [],
        # Source: submission_version COUNT + score aggregation
        "student_history_summary": {
            "total_attempts": 1,
            "attempt_scores": [60.0],
        },
    }


def _make_mock_response(llm_json: dict[str, Any]) -> MagicMock:
    """Return a mock httpx.Response wrapping LLM output in the Ollama envelope.

    Ollama /api/generate returns:
        {"model": "...", "response": "<json string>", "done": true}
    This helper builds that envelope so tests do not need to repeat the wrapping.
    """
    mock_resp = MagicMock()
    mock_resp.raise_for_status.return_value = None
    mock_resp.json.return_value = {
        "model": "llama3.2",
        "response": json.dumps(llm_json),
        "done": True,
    }
    return mock_resp


# ---------------------------------------------------------------------------
# Sprint 2 Test 3 (required)
# ---------------------------------------------------------------------------


class TestOllamaClientFailure:
    """Sprint 2 Test 3: graceful error handling when Ollama is offline."""

    @patch("app.llm.ollama_client.httpx.post")
    def test_ollama_client_handles_local_failure_gracefully(
        self, mock_post: MagicMock, sample_packet: dict
    ) -> None:
        """generate_feedback raises OllamaUnavailableError on connection failure.

        Simulates Ollama being offline by making httpx.post raise
        httpx.ConnectError.  Verifies that the raw exception is wrapped into
        OllamaUnavailableError so callers never need to import httpx internals.
        """
        mock_post.side_effect = httpx.ConnectError("Connection refused")

        with pytest.raises(OllamaUnavailableError) as exc_info:
            generate_feedback(sample_packet)

        # Error message should hint at the server URL for easy debugging
        assert "unreachable" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Additional unit tests
# ---------------------------------------------------------------------------


class TestGenerateFeedbackSuccess:
    """Unit tests for the happy path of generate_feedback()."""

    @patch("app.llm.ollama_client.httpx.post")
    def test_generate_feedback_returns_required_keys(
        self, mock_post: MagicMock, sample_packet: dict
    ) -> None:
        """generate_feedback returns a dict with all 5 required top-level keys."""
        llm_output = {
            "draft_text": (
                "Good effort overall. Please review tc_02 — output was incorrect."
            ),
            "confidence": 0.82,
            "evidence": [
                {
                    "type": "test_run",
                    "pointer": "tc_02",
                    "snippet": "Expected 42, got 0",
                }
            ],
        }
        mock_post.return_value = _make_mock_response(llm_output)

        result = generate_feedback(sample_packet)

        # All 5 required return keys must be present
        assert "draft_text" in result
        assert "confidence" in result
        assert "evidence" in result
        assert "model_name" in result
        assert "prompt_version" in result

        # Values should match the LLM output
        assert result["draft_text"] == llm_output["draft_text"]
        assert result["confidence"] == pytest.approx(0.82)
        assert isinstance(result["evidence"], list)
        assert len(result["evidence"]) == 1

        # httpx.post must have been called exactly once with the /api/generate path
        mock_post.assert_called_once()
        call_url: str = mock_post.call_args[0][0]
        assert "/api/generate" in call_url


class TestGenerateFeedbackErrors:
    """Unit tests for error cases in generate_feedback()."""

    @patch("app.llm.ollama_client.httpx.post")
    def test_generate_feedback_raises_on_invalid_json(
        self, mock_post: MagicMock, sample_packet: dict
    ) -> None:
        """generate_feedback raises ValueError when LLM returns plain text, not JSON."""
        # Simulate a model that ignores the JSON format instruction
        mock_resp = MagicMock()
        mock_resp.raise_for_status.return_value = None
        mock_resp.json.return_value = {
            "response": "Sorry, I cannot process this request.",  # not JSON
            "done": True,
        }
        mock_post.return_value = mock_resp

        with pytest.raises(ValueError, match="valid JSON"):
            generate_feedback(sample_packet)

    @patch("app.llm.ollama_client.httpx.post")
    def test_generate_feedback_raises_on_server_error(
        self, mock_post: MagicMock, sample_packet: dict
    ) -> None:
        """generate_feedback wraps HTTP 5xx into OllamaUnavailableError."""
        mock_response = MagicMock()
        mock_response.status_code = 503
        mock_post.side_effect = httpx.HTTPStatusError(
            "Service Unavailable",
            request=MagicMock(),
            response=mock_response,
        )

        with pytest.raises(OllamaUnavailableError):
            generate_feedback(sample_packet)

    @patch("app.llm.ollama_client.httpx.post")
    def test_generate_feedback_raises_on_timeout(
        self, mock_post: MagicMock, sample_packet: dict
    ) -> None:
        """generate_feedback wraps TimeoutException into OllamaUnavailableError."""
        mock_post.side_effect = httpx.TimeoutException("Request timed out")

        with pytest.raises(OllamaUnavailableError):
            generate_feedback(sample_packet)
