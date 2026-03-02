"""Unit tests for the grading engine simulation module.

Tests cover the GradingOutcome dataclass, all private helper functions,
the main simulate_grading() public API, reproducibility with fixed seeds,
score constraints, and attempt-based improvement trends.

Run with:
    cd make_simul_data && python -m pytest tests/test_grading_engine.py -v
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timezone

import pytest

from make_simul_data.seed_data.assignments import ASSIGNMENTS, get_test_cases
from make_simul_data.seed_data.config import (
    RUNTIME_MAX_MS,
    RUNTIME_MIN_MS,
    TIMEOUT_MS,
    AssignmentDef,
    ExecutionStatus,
    TagType,
    create_rng,
)
from make_simul_data.seed_data.grading_engine import (
    ATTEMPT_SKILL_BOOST,
    GradingOutcome,
    _compute_effective_skill,
    _compute_runtime_ms,
    _decide_pass_flags,
    _determine_execution_status,
    _determine_pass_category,
    _generate_stderr,
    _generate_stdout,
    _generate_tags,
    _generate_test_case_results,
    _generate_wrong_output,
    simulate_grading,
)
from make_simul_data.seed_data.models import ExecutionResult
from make_simul_data.seed_data.students import StudentProfile

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def rng() -> random.Random:
    """Deterministic RNG for repeatable tests."""
    return create_rng(42)


@pytest.fixture
def high_skill_student() -> StudentProfile:
    """Student with skill_level = 0.95 (near maximum)."""
    return StudentProfile(
        student_id="S001",
        name="Alice Smith",
        email="alice@example.com",
        skill_level=0.95,
        attempt_counts=(("HW1", 1), ("HW2", 1), ("HW3", 1), ("HW4", 1), ("HW5", 1)),
        is_late_submitter=False,
        generates_pdf=False,
    )


@pytest.fixture
def low_skill_student() -> StudentProfile:
    """Student with skill_level = 0.15 (near minimum)."""
    return StudentProfile(
        student_id="S002",
        name="Bob Jones",
        email="bob@example.com",
        skill_level=0.15,
        attempt_counts=(("HW1", 3), ("HW2", 2), ("HW3", 1), ("HW4", 1), ("HW5", 1)),
        is_late_submitter=True,
        generates_pdf=False,
    )


@pytest.fixture
def mid_skill_student() -> StudentProfile:
    """Student with skill_level = 0.50 (median)."""
    return StudentProfile(
        student_id="S003",
        name="Carol Lee",
        email="carol@example.com",
        skill_level=0.50,
        attempt_counts=(("HW1", 2), ("HW2", 1), ("HW3", 1), ("HW4", 1), ("HW5", 1)),
        is_late_submitter=False,
        generates_pdf=True,
    )


@pytest.fixture
def hw1() -> AssignmentDef:
    """HW1 assignment definition (easiest, difficulty=1)."""
    return ASSIGNMENTS[0]


@pytest.fixture
def hw5() -> AssignmentDef:
    """HW5 assignment definition (hardest, difficulty=5)."""
    return ASSIGNMENTS[4]


# ── TestGradingOutcome ───────────────────────────────────────────────────


class TestGradingOutcome:
    """Verify that GradingOutcome is a frozen dataclass."""

    def test_is_frozen(self, rng: random.Random, high_skill_student, hw1):
        """GradingOutcome should be immutable (frozen)."""
        outcome = simulate_grading(high_skill_student, hw1, uuid.uuid4(), 1, rng)
        with pytest.raises(AttributeError):
            outcome.total_score = 999.0  # type: ignore[misc]

    def test_has_expected_fields(self, rng: random.Random, high_skill_student, hw1):
        """GradingOutcome must contain all four expected fields."""
        outcome = simulate_grading(high_skill_student, hw1, uuid.uuid4(), 1, rng)
        assert isinstance(outcome.execution_result, ExecutionResult)
        assert isinstance(outcome.test_case_results, tuple)
        assert isinstance(outcome.tags, tuple)
        assert isinstance(outcome.total_score, float)


# ── TestComputeEffectiveSkill ────────────────────────────────────────────


class TestComputeEffectiveSkill:
    """Tests for _compute_effective_skill()."""

    def test_attempt_1_no_boost(self):
        """First attempt should not modify skill."""
        assert _compute_effective_skill(0.5, 1) == 0.5

    def test_attempt_2_boost(self):
        """Second attempt adds ATTEMPT_SKILL_BOOST once."""
        result = _compute_effective_skill(0.5, 2)
        assert result == pytest.approx(0.5 + ATTEMPT_SKILL_BOOST)

    def test_attempt_3_boost(self):
        """Third attempt adds ATTEMPT_SKILL_BOOST twice."""
        result = _compute_effective_skill(0.5, 3)
        assert result == pytest.approx(0.5 + 2 * ATTEMPT_SKILL_BOOST)

    def test_capped_at_1(self):
        """Result must never exceed 1.0."""
        result = _compute_effective_skill(0.95, 3)
        assert result == 1.0

    def test_zero_skill_attempt_1(self):
        """Zero-skill student on first attempt stays at 0.0."""
        assert _compute_effective_skill(0.0, 1) == 0.0


# ── TestDeterminePassCategory ────────────────────────────────────────────


class TestDeterminePassCategory:
    """Tests for _determine_pass_category()."""

    def test_returns_valid_category(self, rng):
        """Must return one of the three known categories."""
        valid = {"all_pass", "partial_pass", "all_fail"}
        for _ in range(100):
            cat = _determine_pass_category(0.5, rng)
            assert cat in valid

    def test_high_skill_favors_all_pass(self):
        """High skill should produce mostly all_pass outcomes."""
        rng = create_rng(123)
        categories = [_determine_pass_category(0.95, rng) for _ in range(1000)]
        all_pass_rate = categories.count("all_pass") / len(categories)
        # Expected ~0.93 for skill=0.95; allow wide tolerance.
        assert all_pass_rate > 0.80

    def test_low_skill_has_more_failures(self):
        """Low skill should produce more all_fail outcomes than high skill."""
        rng_low = create_rng(456)
        rng_high = create_rng(456)
        low_fails = sum(
            1
            for _ in range(1000)
            if _determine_pass_category(0.1, rng_low) == "all_fail"
        )
        high_fails = sum(
            1
            for _ in range(1000)
            if _determine_pass_category(0.9, rng_high) == "all_fail"
        )
        assert low_fails > high_fails


# ── TestDetermineExecutionStatus ─────────────────────────────────────────


class TestDetermineExecutionStatus:
    """Tests for _determine_execution_status()."""

    def test_all_pass_returns_success(self, rng):
        """ALL_PASS category always maps to SUCCESS."""
        for _ in range(100):
            status = _determine_execution_status("all_pass", 0.5, rng)
            assert status == ExecutionStatus.SUCCESS

    def test_partial_pass_returns_success(self, rng):
        """PARTIAL_PASS category always maps to SUCCESS."""
        for _ in range(100):
            status = _determine_execution_status("partial_pass", 0.5, rng)
            assert status == ExecutionStatus.SUCCESS

    def test_all_fail_returns_error_status(self, rng):
        """ALL_FAIL should return one of the error statuses."""
        valid_errors = {
            ExecutionStatus.RUNTIME_ERROR,
            ExecutionStatus.TIMEOUT,
            ExecutionStatus.COMPILATION_ERROR,
        }
        for _ in range(100):
            status = _determine_execution_status("all_fail", 0.5, rng)
            assert status in valid_errors


# ── TestComputeRuntimeMs ─────────────────────────────────────────────────


class TestComputeRuntimeMs:
    """Tests for _compute_runtime_ms()."""

    def test_timeout_returns_fixed(self, rng):
        """TIMEOUT always returns TIMEOUT_MS."""
        assert _compute_runtime_ms(ExecutionStatus.TIMEOUT, rng) == TIMEOUT_MS

    def test_compilation_error_short(self, rng):
        """COMPILATION_ERROR runtime should be very short (10-100ms)."""
        for _ in range(50):
            ms = _compute_runtime_ms(ExecutionStatus.COMPILATION_ERROR, rng)
            assert 10 <= ms <= 100

    def test_success_in_range(self, rng):
        """SUCCESS runtime should be within [RUNTIME_MIN_MS, RUNTIME_MAX_MS]."""
        for _ in range(100):
            ms = _compute_runtime_ms(ExecutionStatus.SUCCESS, rng)
            assert RUNTIME_MIN_MS <= ms <= RUNTIME_MAX_MS

    def test_runtime_error_in_range(self, rng):
        """RUNTIME_ERROR runtime should be within [RUNTIME_MIN_MS, RUNTIME_MAX_MS]."""
        for _ in range(100):
            ms = _compute_runtime_ms(ExecutionStatus.RUNTIME_ERROR, rng)
            assert RUNTIME_MIN_MS <= ms <= RUNTIME_MAX_MS


# ── TestDecidePassFlags ──────────────────────────────────────────────────


class TestDecidePassFlags:
    """Tests for _decide_pass_flags()."""

    def test_all_pass_all_true(self, rng, hw1):
        """ALL_PASS category should produce all-True flags."""
        test_cases = get_test_cases("HW1")
        flags = _decide_pass_flags("all_pass", test_cases, 0.8, hw1.difficulty, rng)
        assert all(flags)

    def test_all_fail_all_false(self, rng, hw1):
        """ALL_FAIL category should produce all-False flags."""
        test_cases = get_test_cases("HW1")
        flags = _decide_pass_flags("all_fail", test_cases, 0.3, hw1.difficulty, rng)
        assert not any(flags)

    def test_partial_has_mix(self, rng, hw1):
        """PARTIAL_PASS should have at least one True and one False."""
        test_cases = get_test_cases("HW1")
        flags = _decide_pass_flags("partial_pass", test_cases, 0.5, hw1.difficulty, rng)
        assert any(flags) and not all(flags)

    def test_flags_length_matches_test_cases(self, rng, hw1):
        """Flag count must equal the number of test cases."""
        test_cases = get_test_cases("HW1")
        flags = _decide_pass_flags("all_pass", test_cases, 0.8, hw1.difficulty, rng)
        assert len(flags) == len(test_cases)


# ── TestGenerateTestCaseResults ──────────────────────────────────────────


class TestGenerateTestCaseResults:
    """Tests for _generate_test_case_results()."""

    def test_result_count_matches(self, rng, hw1):
        """Number of TestCaseResult records should match test case count."""
        test_cases = get_test_cases("HW1")
        flags = tuple([True] * len(test_cases))
        exec_id = uuid.uuid4()
        results, _ = _generate_test_case_results(
            exec_id, test_cases, flags, ExecutionStatus.SUCCESS, rng
        )
        assert len(results) == len(test_cases)

    def test_all_pass_score_equals_max(self, rng, hw1):
        """All tests passing should yield score = max_score."""
        test_cases = get_test_cases("HW1")
        flags = tuple([True] * len(test_cases))
        exec_id = uuid.uuid4()
        _, total = _generate_test_case_results(
            exec_id, test_cases, flags, ExecutionStatus.SUCCESS, rng
        )
        assert total == pytest.approx(100.0)

    def test_all_fail_score_zero(self, rng, hw1):
        """All tests failing should yield score = 0."""
        test_cases = get_test_cases("HW1")
        flags = tuple([False] * len(test_cases))
        exec_id = uuid.uuid4()
        _, total = _generate_test_case_results(
            exec_id, test_cases, flags, ExecutionStatus.SUCCESS, rng
        )
        assert total == 0.0

    def test_exec_id_fk_consistency(self, rng, hw1):
        """Every TestCaseResult.exec_id must match the provided exec_id."""
        test_cases = get_test_cases("HW1")
        flags = tuple([True] * len(test_cases))
        exec_id = uuid.uuid4()
        results, _ = _generate_test_case_results(
            exec_id, test_cases, flags, ExecutionStatus.SUCCESS, rng
        )
        for r in results:
            assert r.exec_id == exec_id

    def test_compilation_error_all_zero(self, rng, hw1):
        """COMPILATION_ERROR: all scores = 0, all passed = False."""
        test_cases = get_test_cases("HW1")
        flags = tuple([False] * len(test_cases))
        exec_id = uuid.uuid4()
        results, total = _generate_test_case_results(
            exec_id, test_cases, flags, ExecutionStatus.COMPILATION_ERROR, rng
        )
        assert total == 0.0
        assert all(not r.passed for r in results)
        assert all(r.score_awarded == 0.0 for r in results)


# ── TestGenerateStdout ───────────────────────────────────────────────────


class TestGenerateStdout:
    """Tests for _generate_stdout()."""

    def test_compilation_empty(self, rng, hw1):
        """COMPILATION_ERROR should produce empty stdout."""
        test_cases = get_test_cases("HW1")
        flags = tuple([False] * len(test_cases))
        stdout = _generate_stdout(
            ExecutionStatus.COMPILATION_ERROR, test_cases, flags, rng
        )
        assert stdout == ""

    def test_timeout_empty(self, rng, hw1):
        """TIMEOUT should produce empty stdout."""
        test_cases = get_test_cases("HW1")
        flags = tuple([False] * len(test_cases))
        assert _generate_stdout(ExecutionStatus.TIMEOUT, test_cases, flags, rng) == ""

    def test_success_contains_summary(self, rng, hw1):
        """SUCCESS stdout should contain a summary line."""
        test_cases = get_test_cases("HW1")
        flags = tuple([True] * len(test_cases))
        stdout = _generate_stdout(ExecutionStatus.SUCCESS, test_cases, flags, rng)
        assert "Passed 5/5 test cases." in stdout

    def test_success_partial_has_fail(self, rng, hw1):
        """Partial pass stdout should contain both PASS and FAIL lines."""
        test_cases = get_test_cases("HW1")
        flags = (True, False, True, True, False)
        stdout = _generate_stdout(ExecutionStatus.SUCCESS, test_cases, flags, rng)
        assert "PASS" in stdout
        assert "FAIL" in stdout


# ── TestGenerateStderr ───────────────────────────────────────────────────


class TestGenerateStderr:
    """Tests for _generate_stderr()."""

    def test_success_empty(self, rng, hw1):
        """SUCCESS should produce empty stderr."""
        assert _generate_stderr(ExecutionStatus.SUCCESS, hw1, rng) == ""

    def test_timeout_message(self, rng, hw1):
        """TIMEOUT stderr should mention the timeout limit."""
        stderr = _generate_stderr(ExecutionStatus.TIMEOUT, hw1, rng)
        assert "TimeoutError" in stderr
        assert str(TIMEOUT_MS // 1000) in stderr

    def test_runtime_error_has_traceback(self, rng, hw1):
        """RUNTIME_ERROR stderr should contain a Traceback."""
        stderr = _generate_stderr(ExecutionStatus.RUNTIME_ERROR, hw1, rng)
        assert "Traceback" in stderr

    def test_compilation_error_has_syntax(self, rng, hw1):
        """COMPILATION_ERROR stderr should contain SyntaxError or IndentationError."""
        stderr = _generate_stderr(ExecutionStatus.COMPILATION_ERROR, hw1, rng)
        assert "SyntaxError" in stderr or "IndentationError" in stderr


# ── TestGenerateTags ─────────────────────────────────────────────────────


class TestGenerateTags:
    """Tests for _generate_tags()."""

    def test_late_submission_tag(self, rng):
        """Late submissions should get a LATE_SUBMISSION tag."""
        sid = uuid.uuid4()
        tags = _generate_tags(sid, 50.0, ExecutionStatus.SUCCESS, True, rng)
        tag_types = {t.tag for t in tags}
        assert TagType.LATE_SUBMISSION in tag_types

    def test_excellent_tag_high_score(self, rng):
        """Score >= 90 should produce an EXCELLENT tag."""
        sid = uuid.uuid4()
        tags = _generate_tags(sid, 95.0, ExecutionStatus.SUCCESS, False, rng)
        tag_types = {t.tag for t in tags}
        assert TagType.EXCELLENT in tag_types

    def test_no_excellent_below_threshold(self, rng):
        """Score < 90 should NOT produce an EXCELLENT tag."""
        sid = uuid.uuid4()
        tags = _generate_tags(sid, 85.0, ExecutionStatus.SUCCESS, False, rng)
        tag_types = {t.tag for t in tags}
        assert TagType.EXCELLENT not in tag_types

    def test_clean_tag_on_success(self, rng):
        """Successful execution with no negative tags should get CLEAN."""
        sid = uuid.uuid4()
        tags = _generate_tags(sid, 50.0, ExecutionStatus.SUCCESS, False, rng)
        tag_types = {t.tag for t in tags}
        assert TagType.CLEAN in tag_types

    def test_no_plagiarism_tag(self, rng):
        """Grading engine must never produce PLAGIARISM_SUSPECT tags."""
        sid = uuid.uuid4()
        # Run many times to be sure.
        for seed in range(200):
            r = create_rng(seed)
            for status in (
                ExecutionStatus.SUCCESS,
                ExecutionStatus.RUNTIME_ERROR,
                ExecutionStatus.COMPILATION_ERROR,
            ):
                tags = _generate_tags(sid, 50.0, status, False, r)
                assert all(t.tag != TagType.PLAGIARISM_SUSPECT for t in tags)

    def test_confidence_range(self, rng):
        """All tag confidence values should be in [0.0, 1.0]."""
        sid = uuid.uuid4()
        tags = _generate_tags(sid, 95.0, ExecutionStatus.SUCCESS, True, rng)
        for t in tags:
            assert 0.0 <= t.confidence <= 1.0


# ── TestSimulateGrading ─────────────────────────────────────────────────


class TestSimulateGrading:
    """Integration tests for the simulate_grading() public API."""

    def test_returns_grading_outcome(self, rng, high_skill_student, hw1):
        """simulate_grading() must return a GradingOutcome instance."""
        outcome = simulate_grading(high_skill_student, hw1, uuid.uuid4(), 1, rng)
        assert isinstance(outcome, GradingOutcome)

    def test_test_case_count_matches_assignment(self, rng, high_skill_student, hw1):
        """Number of TestCaseResults must equal assignment's num_test_cases."""
        outcome = simulate_grading(high_skill_student, hw1, uuid.uuid4(), 1, rng)
        assert len(outcome.test_case_results) == hw1.num_test_cases

    def test_exec_id_fk_consistency(self, rng, high_skill_student, hw1):
        """All TestCaseResult.exec_id must match ExecutionResult.exec_id."""
        outcome = simulate_grading(high_skill_student, hw1, uuid.uuid4(), 1, rng)
        exec_id = outcome.execution_result.exec_id
        for tc in outcome.test_case_results:
            assert tc.exec_id == exec_id

    def test_submission_id_consistency(self, rng, high_skill_student, hw1):
        """ExecutionResult.submission_id must match the provided UUID."""
        sid = uuid.uuid4()
        outcome = simulate_grading(high_skill_student, hw1, sid, 1, rng)
        assert outcome.execution_result.submission_id == sid

    def test_all_assignments(self, rng, high_skill_student):
        """simulate_grading() should work for all 5 assignments."""
        for assignment in ASSIGNMENTS:
            outcome = simulate_grading(
                high_skill_student, assignment, uuid.uuid4(), 1, create_rng(99)
            )
            assert len(outcome.test_case_results) == assignment.num_test_cases

    def test_late_flag_propagates(self, rng, high_skill_student, hw1):
        """is_late=True should produce a LATE_SUBMISSION tag."""
        outcome = simulate_grading(
            high_skill_student, hw1, uuid.uuid4(), 1, rng, is_late=True
        )
        tag_types = {t.tag for t in outcome.tags}
        assert TagType.LATE_SUBMISSION in tag_types

    def test_submitted_at_affects_timing(self, rng, high_skill_student, hw1):
        """Providing submitted_at should set execution start after that time."""
        ts = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
        outcome = simulate_grading(
            high_skill_student, hw1, uuid.uuid4(), 1, rng, submitted_at=ts
        )
        assert outcome.execution_result.started_at >= ts


# ── TestReproducibility ──────────────────────────────────────────────────


class TestReproducibility:
    """Verify deterministic output with the same seed."""

    def test_same_seed_same_result(self, high_skill_student, hw1):
        """Two runs with the same seed must produce identical outcomes."""
        sid = uuid.uuid4()
        ts = datetime(2026, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

        rng1 = create_rng(777)
        o1 = simulate_grading(high_skill_student, hw1, sid, 1, rng1, submitted_at=ts)

        rng2 = create_rng(777)
        o2 = simulate_grading(high_skill_student, hw1, sid, 1, rng2, submitted_at=ts)

        assert o1.total_score == o2.total_score
        assert o1.execution_result.status == o2.execution_result.status
        assert o1.execution_result.runtime_ms == o2.execution_result.runtime_ms
        assert len(o1.test_case_results) == len(o2.test_case_results)
        for r1, r2 in zip(o1.test_case_results, o2.test_case_results):
            assert r1.passed == r2.passed
            assert r1.score_awarded == r2.score_awarded


# ── TestScoreConstraints ─────────────────────────────────────────────────


class TestScoreConstraints:
    """Verify that total_score stays within valid bounds."""

    def test_score_non_negative(self, high_skill_student, hw1):
        """Score must never be negative."""
        for seed in range(100):
            outcome = simulate_grading(
                high_skill_student, hw1, uuid.uuid4(), 1, create_rng(seed)
            )
            assert outcome.total_score >= 0.0

    def test_score_at_most_max(self, high_skill_student, hw1):
        """Score must never exceed max_score (100)."""
        for seed in range(100):
            outcome = simulate_grading(
                high_skill_student, hw1, uuid.uuid4(), 3, create_rng(seed)
            )
            assert outcome.total_score <= hw1.max_score

    def test_low_skill_lower_scores(self, low_skill_student, high_skill_student, hw1):
        """Low-skill students should average lower scores than high-skill."""
        low_scores = [
            simulate_grading(
                low_skill_student, hw1, uuid.uuid4(), 1, create_rng(s)
            ).total_score
            for s in range(200)
        ]
        high_scores = [
            simulate_grading(
                high_skill_student, hw1, uuid.uuid4(), 1, create_rng(s)
            ).total_score
            for s in range(200)
        ]
        assert sum(low_scores) / len(low_scores) < sum(high_scores) / len(high_scores)


# ── TestAttemptImprovement ───────────────────────────────────────────────


class TestAttemptImprovement:
    """Verify that later attempts tend to produce higher scores."""

    def test_attempt_3_higher_than_1(self, mid_skill_student, hw1):
        """Average score for attempt 3 should exceed attempt 1."""
        scores_a1 = [
            simulate_grading(
                mid_skill_student, hw1, uuid.uuid4(), 1, create_rng(s)
            ).total_score
            for s in range(300)
        ]
        scores_a3 = [
            simulate_grading(
                mid_skill_student, hw1, uuid.uuid4(), 3, create_rng(s)
            ).total_score
            for s in range(300)
        ]
        avg_a1 = sum(scores_a1) / len(scores_a1)
        avg_a3 = sum(scores_a3) / len(scores_a3)
        assert avg_a3 > avg_a1


# ── TestGenerateWrongOutput ──────────────────────────────────────────────


class TestGenerateWrongOutput:
    """Tests for _generate_wrong_output()."""

    def test_numeric_mutation(self, rng):
        """Numeric expected output should produce a different number."""
        result = _generate_wrong_output("42\n", rng)
        assert result != "42"

    def test_boolean_flip(self, rng):
        """Boolean expected output should be flipped."""
        assert _generate_wrong_output("True\n", rng) == "False"
        assert _generate_wrong_output("False\n", rng) == "True"

    def test_list_mutation(self, rng):
        """Space-separated list should be mutated but not identical."""
        result = _generate_wrong_output("1 2 3 4 5\n", rng)
        assert result != "1 2 3 4 5"

    def test_empty_string(self, rng):
        """Empty expected output should return 'None'."""
        assert _generate_wrong_output("\n", rng) == "None"
