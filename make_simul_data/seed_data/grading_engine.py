"""Simulated auto-grading engine for the seed data generation pipeline.

This module probabilistically generates grading results (execution outcomes,
per-test-case results, and classification tags) for student submissions
WITHOUT actually executing any student code.  All outcomes are driven by
the student's ``skill_level``, assignment ``difficulty``, and the global
``PASS_RATES`` distribution from ``config.py``.

The single public entry point is :func:`simulate_grading`, which returns a
``GradingOutcome`` frozen dataclass containing everything downstream modules
need: an ``ExecutionResult``, a tuple of ``TestCaseResult`` records, a tuple
of ``SubmissionTag`` records, and the computed ``total_score``.

Module dependency graph (imports from):
    config.py       -> PASS_RATES, RUNTIME_*, TIMEOUT_MS,
                       ExecutionStatus, TagType, TagSource, AssignmentDef
    models.py       -> ExecutionResult, TestCaseResult, SubmissionTag
    students.py     -> StudentProfile
    assignments.py  -> DIFFICULTY_WEIGHTS, TestCaseSpec, get_test_cases

Consumed by:
    generate_data.py  (Step 10 — calls simulate_grading() for every submission)
"""

from __future__ import annotations

import math
import random
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from make_simul_data.seed_data.assignments import (
    DIFFICULTY_WEIGHTS,
    TestCaseSpec,
    get_test_cases,
)
from make_simul_data.seed_data.config import (
    PASS_RATES,
    RUNTIME_MAX_MS,
    RUNTIME_MIN_MS,
    TIMEOUT_MS,
    AssignmentDef,
    ExecutionStatus,
    TagSource,
    TagType,
)
from make_simul_data.seed_data.models import (
    ExecutionResult,
    SubmissionTag,
    TestCaseResult,
)
from make_simul_data.seed_data.students import StudentProfile

# ── Skill / Attempt Constants ────────────────────────────────────────────

# Per-attempt skill boost added to a student's base skill_level.
# Each additional attempt (attempt_no > 1) adds this increment, simulating
# learning from previous feedback.  The same value is used in
# code_generator.py (ATTEMPT_SKILL_BOOST) for consistency across modules.
# Formula: effective_skill = min(1.0, skill_level
#          + ATTEMPT_SKILL_BOOST * (attempt_no - 1))
# Used by: _compute_effective_skill()
ATTEMPT_SKILL_BOOST: float = 0.1

# Range (inclusive) for the flat score bonus applied when attempt_no > 1.
# A random value in [MIN, MAX] is sampled per extra attempt to simulate
# improvement after receiving feedback on earlier submissions.
# Formula: bonus = rng.uniform(MIN, MAX) * (attempt_no - 1)
# Used by: simulate_grading() (after raw score computation)
ATTEMPT_SCORE_BOOST_MIN: float = 5.0
ATTEMPT_SCORE_BOOST_MAX: float = 15.0

# ── Execution Status Probabilities ──────────────────────────────────────

# Probability that a submission in the ALL_FAIL category results in a
# TIMEOUT rather than a RUNTIME_ERROR or COMPILATION_ERROR.
# Roughly 2% of total failures are timeouts (infinite loops, etc.).
# Used by: _determine_execution_status()
TIMEOUT_PROBABILITY: float = 0.02

# Base rate at which ALL_FAIL submissions are classified as
# COMPILATION_ERROR (syntax errors).  The effective rate is scaled by
# ``(1 - effective_skill)``, so low-skill students are more likely to
# produce syntax errors.
# Used by: _determine_execution_status()
COMPILATION_ERROR_BASE_RATE: float = 0.30

# ── Tag Thresholds ───────────────────────────────────────────────────────

# Minimum total_score required to receive the EXCELLENT tag.
# Used by: _generate_tags()
TAG_EXCELLENT_THRESHOLD: float = 90.0

# Probability of assigning a CORRUPTED tag to failed submissions
# (compilation_error or runtime_error).  Simulates damaged/unreadable
# submission files (~2% of error submissions).
# Used by: _generate_tags()
TAG_CORRUPTED_RATE: float = 0.02

# ── Execution Timing ─────────────────────────────────────────────────────

# Maximum random delay (seconds) between submitted_at and execution
# started_at.  Simulates CI/CD queue latency (0 to 5 minutes).
# Used by: simulate_grading()
EXECUTION_START_MAX_OFFSET_SECONDS: int = 300

# ── Exit Code Mapping ────────────────────────────────────────────────────

# Maps each ExecutionStatus to its corresponding process exit code.
# Used by: simulate_grading() (to populate ExecutionResult.exit_code)
_EXIT_CODE_MAP: dict[str, int] = {
    ExecutionStatus.SUCCESS: 0,
    ExecutionStatus.RUNTIME_ERROR: 1,
    ExecutionStatus.TIMEOUT: -1,
    ExecutionStatus.COMPILATION_ERROR: 2,
}

# ── Pass Category Labels ────────────────────────────────────────────────

# String labels for the three pass categories used internally.
# Used by: _determine_pass_category(), _determine_execution_status(),
#          _decide_pass_flags(), _generate_test_case_results()
_CAT_ALL_PASS: str = "all_pass"
_CAT_PARTIAL_PASS: str = "partial_pass"
_CAT_ALL_FAIL: str = "all_fail"

# ── stdout Templates ─────────────────────────────────────────────────────

# Single-line template for a passing test case in stdout.
# Placeholder: {tc_num} — 1-based test case index.
# Used by: _generate_stdout()
_STDOUT_PASS_LINE: str = "Test {tc_num}: PASS"

# Multi-line template for a failing test case in stdout.
# Placeholders: {tc_num}, {expected}, {actual}.
# Used by: _generate_stdout()
_STDOUT_FAIL_LINE: str = (
    "Test {tc_num}: FAIL\n" "  Expected: {expected}\n" "  Got:      {actual}"
)

# Summary line appended at the end of stdout for successful executions.
# Placeholders: {passed}, {total}.
# Used by: _generate_stdout()
_STDOUT_SUMMARY: str = "Passed {passed}/{total} test cases."

# ── stderr Templates — Runtime Errors ────────────────────────────────────

# Realistic Python traceback templates for runtime errors.
# Placeholders: {filename}, {line_no}, {var_name}, {func_name}, {bad_input}.
# Used by: _generate_stderr()
_STDERR_RUNTIME_TEMPLATES: tuple[str, ...] = (
    "Traceback (most recent call last):\n"
    '  File "{filename}", line {line_no}, in <module>\n'
    "NameError: name '{var_name}' is not defined",
    "Traceback (most recent call last):\n"
    '  File "{filename}", line {line_no}, in <module>\n'
    "TypeError: unsupported operand type(s) for +: 'int' and 'str'",
    "Traceback (most recent call last):\n"
    '  File "{filename}", line {line_no}, in <module>\n'
    "IndexError: list index out of range",
    "Traceback (most recent call last):\n"
    '  File "{filename}", line {line_no}, in {func_name}\n'
    "ZeroDivisionError: division by zero",
    "Traceback (most recent call last):\n"
    '  File "{filename}", line {line_no}, in <module>\n'
    "ValueError: invalid literal for int() with base 10: '{bad_input}'",
)

# ── stderr Templates — Compilation Errors ────────────────────────────────

# Realistic Python syntax/indentation error templates.
# Placeholders: {filename}, {line_no}, {bad_line}.
# Used by: _generate_stderr()
_STDERR_COMPILATION_TEMPLATES: tuple[str, ...] = (
    '  File "{filename}", line {line_no}\n'
    "    {bad_line}\n"
    "    ^\n"
    "SyntaxError: invalid syntax",
    '  File "{filename}", line {line_no}\n'
    "    {bad_line}\n"
    "IndentationError: expected an indented block after 'if' statement",
    '  File "{filename}", line {line_no}\n'
    "    {bad_line}\n"
    "    ^\n"
    "SyntaxError: EOL while scanning string literal",
)

# ── stderr Template — Timeout ────────────────────────────────────────────

# Template for timeout stderr message.
# Placeholder: {timeout_sec} — timeout limit in seconds.
# Used by: _generate_stderr()
_STDERR_TIMEOUT: str = (
    "TimeoutError: Execution exceeded {timeout_sec}s limit and was terminated."
)

# ── Template Fill Pools ──────────────────────────────────────────────────

# Pool of variable names used to populate NameError tracebacks.
# Used by: _generate_stderr()
_VARIABLE_NAME_POOL: tuple[str, ...] = (
    "result",
    "total",
    "count",
    "avg",
    "lst",
    "output",
    "temp",
    "val",
    "num",
    "data",
)

# Pool of function names used in traceback "in <func>" fields.
# Used by: _generate_stderr()
_FUNCTION_NAME_POOL: tuple[str, ...] = (
    "calculate",
    "process",
    "compute_result",
    "get_value",
    "run",
    "solve",
)

# Pool of invalid string inputs used to populate ValueError tracebacks.
# Used by: _generate_stderr()
_BAD_INPUT_POOL: tuple[str, ...] = (
    "abc",
    "N/A",
    "",
    "null",
    "undefined",
)

# Pool of syntactically invalid Python lines used in SyntaxError tracebacks.
# Used by: _generate_stderr()
_BAD_LINE_POOL: tuple[str, ...] = (
    "if x = 5:",
    "print(hello world)",
    "def foo(x, y",
    "for i in range(10",
    "while True",
    'return "result',
)


# ── Return Type ──────────────────────────────────────────────────────────


@dataclass(frozen=True)
class GradingOutcome:
    """Immutable container for all grading results of a single submission.

    This is the primary return type of simulate_grading().  It bundles the
    ExecutionResult, per-test-case results, classification tags, and the
    final computed total score into a single immutable structure.

    Created by: simulate_grading() in this module.
    Consumed by: generate_data.py (Step 10 — writes fields to CSV metadata).

    Attributes:
        execution_result:  The ExecutionResult Pydantic model instance.
                           Contains execution status, timing, stdout, stderr.
                           Written to: metadata/execution_results.csv.
        test_case_results: Tuple of TestCaseResult Pydantic model instances,
                           one per test case defined for the assignment.
                           Length equals AssignmentDef.num_test_cases.
                           Written to: metadata/test_case_results.csv.
        tags:              Tuple of SubmissionTag Pydantic model instances.
                           May be empty or contain multiple tags (e.g.,
                           LATE_SUBMISSION + EXCELLENT).
                           Written to: metadata/submission_tags.csv.
        total_score:       Final score in [0.0, max_score].  Equals the sum
                           of score_awarded across test_case_results, with an
                           optional attempt bonus, capped at max_score.
    """

    execution_result: ExecutionResult
    test_case_results: tuple[TestCaseResult, ...]
    tags: tuple[SubmissionTag, ...]
    total_score: float


# ── Private Helper Functions ─────────────────────────────────────────────


def _compute_effective_skill(skill_level: float, attempt_no: int) -> float:
    """Compute the effective skill level after applying attempt-based boost.

    Each additional attempt (beyond the first) adds ATTEMPT_SKILL_BOOST to
    the student's base skill_level, simulating learning from feedback.
    The result is clamped to [0.0, 1.0].

    This mirrors the same formula used in code_generator.py to ensure
    consistent skill modeling across the pipeline.

    Used by: simulate_grading() (first step in the grading pipeline)

    Args:
        skill_level: Student's base skill level from StudentProfile,
                     in [0.0, 1.0].
        attempt_no:  Submission attempt number (1, 2, or 3).

    Returns:
        Effective skill level in [0.0, 1.0].
    """
    return min(1.0, skill_level + ATTEMPT_SKILL_BOOST * (attempt_no - 1))


def _determine_pass_category(
    effective_skill: float,
    rng: random.Random,
) -> str:
    """Determine the overall pass/fail category for a submission.

    Uses the global PASS_RATES as base probabilities and adjusts them
    based on the student's effective skill level.  Higher-skill students
    have a greater chance of ALL_PASS and lower chance of ALL_FAIL.

    Adjustment logic:
      - Skill 0.5 (median) => no adjustment, use base PASS_RATES.
      - Skill 1.0 (max)    => all_pass ~0.95, all_fail ~0.01.
      - Skill 0.0 (min)    => all_pass ~0.55, all_fail ~0.09.

    Used by: simulate_grading() (determines the high-level outcome)

    Args:
        effective_skill: Skill level after attempt boost, in [0.0, 1.0].
        rng:             Seeded Random instance for deterministic sampling.

    Returns:
        One of "all_pass", "partial_pass", or "all_fail".
    """
    base_all_pass, _base_partial, base_all_fail = PASS_RATES

    # Shift all_pass probability based on skill deviation from median (0.5).
    adjusted_all_pass = base_all_pass + (effective_skill - 0.5) * 0.4
    adjusted_all_pass = max(0.01, min(0.99, adjusted_all_pass))

    # Shift all_fail probability inversely to skill.
    adjusted_all_fail = base_all_fail - (effective_skill - 0.5) * 0.08
    adjusted_all_fail = max(0.01, min(0.99, adjusted_all_fail))

    # Partial pass fills the remainder (guaranteed >= 0.01 due to clamping).
    adjusted_partial = max(0.01, 1.0 - adjusted_all_pass - adjusted_all_fail)

    # rng.choices() normalizes weights internally; no manual normalization needed.
    weights = [adjusted_all_pass, adjusted_partial, adjusted_all_fail]

    category = rng.choices(
        [_CAT_ALL_PASS, _CAT_PARTIAL_PASS, _CAT_ALL_FAIL],
        weights=weights,
        k=1,
    )[0]

    return category


def _determine_execution_status(
    pass_category: str,
    effective_skill: float,
    rng: random.Random,
) -> str:
    """Map a pass category to a concrete ExecutionStatus value.

    - ALL_PASS and PARTIAL_PASS always result in SUCCESS (code ran, some
      or all tests passed).
    - ALL_FAIL may result in TIMEOUT (~2%), COMPILATION_ERROR (scaled by
      inverse skill), or RUNTIME_ERROR (default for remaining failures).

    Used by: simulate_grading() (after pass category is determined)

    Args:
        pass_category:  One of "all_pass", "partial_pass", "all_fail".
        effective_skill: Skill level for compilation-error scaling.
        rng:             Seeded Random instance.

    Returns:
        An ExecutionStatus string value ("success", "runtime_error",
        "timeout", or "compilation_error").
    """
    if pass_category in (_CAT_ALL_PASS, _CAT_PARTIAL_PASS):
        return ExecutionStatus.SUCCESS

    # ALL_FAIL path: decide among TIMEOUT, COMPILATION_ERROR, RUNTIME_ERROR.
    if rng.random() < TIMEOUT_PROBABILITY:
        return ExecutionStatus.TIMEOUT

    # Lower skill => higher compilation error rate.
    compilation_rate = COMPILATION_ERROR_BASE_RATE * (1.0 - effective_skill)
    if rng.random() < compilation_rate:
        return ExecutionStatus.COMPILATION_ERROR

    return ExecutionStatus.RUNTIME_ERROR


def _compute_runtime_ms(status: str, rng: random.Random) -> int:
    """Generate a realistic execution runtime based on the execution status.

    - TIMEOUT:            Fixed at TIMEOUT_MS (30,000 ms).
    - COMPILATION_ERROR:  Very short (10-100 ms) since code never ran.
    - SUCCESS/RUNTIME_ERROR:  Log-normal distribution in
      [RUNTIME_MIN_MS, RUNTIME_MAX_MS] to model real execution time
      variability.

    The log-normal approach uses ``math.exp(rng.gauss(mu, sigma))`` where
    mu and sigma are derived from the log of the min/max bounds.  This
    produces a right-skewed distribution typical of real runtimes.

    Used by: simulate_grading() (to populate ExecutionResult.runtime_ms)

    Args:
        status: ExecutionStatus string value.
        rng:    Seeded Random instance.

    Returns:
        Runtime in milliseconds (int, >= 0).
    """
    if status == ExecutionStatus.TIMEOUT:
        return TIMEOUT_MS

    if status == ExecutionStatus.COMPILATION_ERROR:
        return rng.randint(10, 100)

    # Log-normal distribution for SUCCESS and RUNTIME_ERROR.
    ln_min = math.log(RUNTIME_MIN_MS)
    ln_max = math.log(RUNTIME_MAX_MS)
    mu = (ln_min + ln_max) / 2.0
    sigma = (ln_max - ln_min) / 4.0
    raw = math.exp(rng.gauss(mu, sigma))

    return int(max(RUNTIME_MIN_MS, min(RUNTIME_MAX_MS, raw)))


def _decide_pass_flags(
    pass_category: str,
    test_cases: tuple[TestCaseSpec, ...],
    effective_skill: float,
    difficulty: int,
    rng: random.Random,
) -> tuple[bool, ...]:
    """Decide which individual test cases pass or fail.

    - ALL_PASS:      Every test case passes.
    - ALL_FAIL:      Every test case fails.
    - PARTIAL_PASS:  Each test case passes with probability proportional
                     to effective_skill, adjusted by difficulty.  At least
                     one test must pass and at least one must fail.

    Used by: _generate_test_case_results()

    Args:
        pass_category:  "all_pass", "partial_pass", or "all_fail".
        test_cases:     Tuple of TestCaseSpec for the assignment.
        effective_skill: Boosted skill level in [0.0, 1.0].
        difficulty:     Assignment difficulty level (1-5).
        rng:            Seeded Random instance.

    Returns:
        Tuple of booleans, one per test case (True = passed).
    """
    n = len(test_cases)

    if pass_category == _CAT_ALL_PASS:
        return (True,) * n

    if pass_category == _CAT_ALL_FAIL:
        return (False,) * n

    # PARTIAL_PASS: probabilistic per-test-case pass/fail.
    difficulty_weight = DIFFICULTY_WEIGHTS.get(difficulty, 0.5)
    pass_rate = effective_skill * (1.0 - difficulty_weight * 0.3)
    pass_rate = max(0.1, min(0.9, pass_rate))

    flags = [rng.random() < pass_rate for _ in range(n)]

    # Enforce at least one pass and one fail for PARTIAL_PASS.
    if n >= 2:
        if all(flags):
            flags[rng.randint(0, n - 1)] = False
        elif not any(flags):
            flags[rng.randint(0, n - 1)] = True

    return tuple(flags)


def _generate_wrong_output(expected: str, rng: random.Random) -> str:
    """Generate a plausible but incorrect output for a failed test case.

    Applies one of several mutation strategies to the expected output:
      - Numeric outputs: offset by a small random amount.
      - Boolean outputs: flip True/False.
      - String outputs:  case change, truncation, or generic replacement.

    Used by: _generate_stdout(), _generate_test_case_results()

    Args:
        expected: The correct expected output string (may include newlines).
        rng:      Seeded Random instance.

    Returns:
        A plausible wrong output string.
    """
    stripped = expected.strip()

    # Try numeric mutation.
    try:
        num = float(stripped)
        offset = rng.choice([-2, -1, 1, 2])
        if num == int(num) and "." not in stripped:
            return str(int(num) + offset)
        return str(round(num + offset, 2))
    except ValueError:
        pass

    # Boolean flip.
    if stripped in ("True", "False"):
        return "False" if stripped == "True" else "True"

    # Space-separated list: shuffle or remove an element.
    parts = stripped.split()
    if len(parts) > 1:
        mutated = list(parts)
        strategy = rng.choice(["swap", "drop", "add"])
        if strategy == "swap" and len(mutated) >= 2:
            i, j = rng.sample(range(len(mutated)), 2)
            mutated[i], mutated[j] = mutated[j], mutated[i]
        elif strategy == "drop" and len(mutated) > 1:
            mutated.pop(rng.randint(0, len(mutated) - 1))
        else:
            mutated.append(rng.choice(mutated))
        return " ".join(mutated)

    # Generic string mutation.
    if stripped:
        mutations = [
            stripped.lower(),
            stripped.upper(),
            stripped[: max(1, len(stripped) // 2)],
            "error",
        ]
        return rng.choice(mutations)

    return "None"


def _generate_stdout(
    status: str,
    test_cases: tuple[TestCaseSpec, ...],
    passed_flags: tuple[bool, ...],
    rng: random.Random,
) -> str:
    """Generate realistic stdout output for the execution.

    - SUCCESS:            Full test results with PASS/FAIL per test case
                          and a summary line.
    - RUNTIME_ERROR:      Partial output (1-3 test lines) before crash.
    - TIMEOUT:            Empty (process killed before output).
    - COMPILATION_ERROR:  Empty (code never ran).

    Used by: simulate_grading() (populates ExecutionResult.stdout)

    Args:
        status:       ExecutionStatus string value.
        test_cases:   Tuple of TestCaseSpec for the assignment.
        passed_flags: Per-test-case pass/fail booleans (same length as
                      test_cases).
        rng:          Seeded Random instance.

    Returns:
        The complete stdout string (may be empty).
    """
    if status in (ExecutionStatus.COMPILATION_ERROR, ExecutionStatus.TIMEOUT):
        return ""

    if status == ExecutionStatus.RUNTIME_ERROR:
        # Partial output: show a few test results before the crash.
        # Lines are shown as PASS because the crash occurs *after* those
        # test cases completed successfully.  The passed_flags argument is
        # intentionally not consulted here — the runtime error interrupts
        # execution mid-run, so only the pre-crash output is captured.
        partial_count = rng.randint(0, min(3, len(test_cases) - 1))
        lines: list[str] = []
        for i in range(partial_count):
            lines.append(_STDOUT_PASS_LINE.format(tc_num=i + 1))
        return "\n".join(lines)

    # SUCCESS: full test output with PASS/FAIL and summary.
    lines = []
    for i, (tc, passed) in enumerate(zip(test_cases, passed_flags)):
        tc_num = i + 1
        if passed:
            lines.append(_STDOUT_PASS_LINE.format(tc_num=tc_num))
        else:
            actual = _generate_wrong_output(tc.expected_output, rng)
            lines.append(
                _STDOUT_FAIL_LINE.format(
                    tc_num=tc_num,
                    expected=tc.expected_output.strip(),
                    actual=actual,
                )
            )

    passed_count = sum(passed_flags)
    lines.append(_STDOUT_SUMMARY.format(passed=passed_count, total=len(test_cases)))

    return "\n".join(lines)


def _generate_stderr(
    status: str,
    assignment: AssignmentDef,
    rng: random.Random,
) -> str:
    """Generate realistic stderr output based on the execution status.

    - SUCCESS:            Empty (no errors).
    - TIMEOUT:            TimeoutError message with the limit in seconds.
    - RUNTIME_ERROR:      Random Python traceback (NameError, TypeError, etc.).
    - COMPILATION_ERROR:  Random SyntaxError or IndentationError.

    Placeholders in templates are filled with realistic values derived from
    the assignment's required files and random line numbers.

    Used by: simulate_grading() (populates ExecutionResult.stderr)

    Args:
        status:     ExecutionStatus string value.
        assignment: The assignment being graded (for filenames).
        rng:        Seeded Random instance.

    Returns:
        The complete stderr string (may be empty).
    """
    if status == ExecutionStatus.SUCCESS:
        return ""

    if status == ExecutionStatus.TIMEOUT:
        return _STDERR_TIMEOUT.format(timeout_sec=TIMEOUT_MS // 1000)

    filename = assignment.required_files[0]
    line_no = rng.randint(1, 50)

    if status == ExecutionStatus.RUNTIME_ERROR:
        template = rng.choice(_STDERR_RUNTIME_TEMPLATES)
        return template.format(
            filename=filename,
            line_no=line_no,
            var_name=rng.choice(_VARIABLE_NAME_POOL),
            func_name=rng.choice(_FUNCTION_NAME_POOL),
            bad_input=rng.choice(_BAD_INPUT_POOL),
        )

    # COMPILATION_ERROR
    template = rng.choice(_STDERR_COMPILATION_TEMPLATES)
    return template.format(
        filename=filename,
        line_no=line_no,
        bad_line=rng.choice(_BAD_LINE_POOL),
    )


def _generate_test_case_results(
    exec_id: uuid.UUID,
    test_cases: tuple[TestCaseSpec, ...],
    passed_flags: tuple[bool, ...],
    status: str,
    rng: random.Random,
) -> tuple[tuple[TestCaseResult, ...], float]:
    """Create TestCaseResult records and compute the raw total score.

    For non-executable statuses (COMPILATION_ERROR, TIMEOUT), all test cases
    are marked as failed with score 0.  For SUCCESS, each test case's score
    is its ``points`` value if passed, 0 otherwise.

    Used by: simulate_grading() (creates per-test-case records)

    Args:
        exec_id:      UUID of the parent ExecutionResult (FK).
        test_cases:   Tuple of TestCaseSpec for the assignment.
        passed_flags: Per-test-case pass/fail booleans.
        status:       ExecutionStatus string value.
        rng:          Seeded Random instance (for wrong output generation).

    Returns:
        A 2-tuple of:
          - Tuple of TestCaseResult Pydantic model instances.
          - Raw total score (float, sum of score_awarded values).
    """
    results: list[TestCaseResult] = []
    total_score = 0.0

    for tc, passed in zip(test_cases, passed_flags):
        score = tc.points if passed else 0.0
        total_score += score

        # Build a short output string for each test case.
        if status in (
            ExecutionStatus.COMPILATION_ERROR,
            ExecutionStatus.TIMEOUT,
        ):
            output = f"Not executed: {status}"
        elif passed:
            output = "PASS"
        else:
            wrong = _generate_wrong_output(tc.expected_output, rng)
            output = f"Expected: {tc.expected_output.strip()}\n" f"Got:      {wrong}"

        results.append(
            TestCaseResult(
                exec_id=exec_id,
                test_case_id=tc.test_case_id,
                passed=passed,
                score_awarded=score,
                output=output,
            )
        )

    return tuple(results), total_score


def _generate_tags(
    submission_id: uuid.UUID,
    total_score: float,
    status: str,
    is_late: bool,
    rng: random.Random,
) -> tuple[SubmissionTag, ...]:
    """Generate classification tags for a submission based on its outcomes.

    Tag rules:
      - LATE_SUBMISSION:    Always if ``is_late`` is True (confidence=1.0).
      - EXCELLENT:          If total_score >= TAG_EXCELLENT_THRESHOLD.
      - CORRUPTED:          With TAG_CORRUPTED_RATE probability, only for
                            COMPILATION_ERROR or RUNTIME_ERROR submissions.
      - CLEAN:              If no negative tags and status is SUCCESS.
      - PLAGIARISM_SUSPECT: NOT generated here — handled by plagiarism.py
                            (Step 8).

    Used by: simulate_grading() (final step before returning GradingOutcome)

    Args:
        submission_id: UUID of the parent Submission (FK).
        total_score:   Final computed score for the submission.
        status:        ExecutionStatus string value.
        is_late:       Whether the submission was late.
        rng:           Seeded Random instance.

    Returns:
        Tuple of SubmissionTag Pydantic model instances (may be empty).
    """
    tags: list[SubmissionTag] = []

    # 1. LATE_SUBMISSION: deterministic based on submission timing.
    if is_late:
        tags.append(
            SubmissionTag(
                submission_id=submission_id,
                tag=TagType.LATE_SUBMISSION,
                source=TagSource.AUTOMATED,
                confidence=1.0,
            )
        )

    # 2. EXCELLENT: high-scoring submissions.
    if total_score >= TAG_EXCELLENT_THRESHOLD:
        confidence = 0.95 + rng.uniform(0.0, 0.05)
        tags.append(
            SubmissionTag(
                submission_id=submission_id,
                tag=TagType.EXCELLENT,
                source=TagSource.AUTOMATED,
                confidence=round(confidence, 4),
            )
        )

    # 3. CORRUPTED: rare tag for error submissions.
    if status in (ExecutionStatus.COMPILATION_ERROR, ExecutionStatus.RUNTIME_ERROR):
        if rng.random() < TAG_CORRUPTED_RATE:
            confidence = rng.uniform(0.6, 0.9)
            tags.append(
                SubmissionTag(
                    submission_id=submission_id,
                    tag=TagType.CORRUPTED,
                    source=TagSource.AUTOMATED,
                    confidence=round(confidence, 4),
                )
            )

    # 4. CLEAN: assigned when no negative tags exist and execution succeeded.
    # LATE_SUBMISSION is deliberately excluded: a late submission can still
    # be CLEAN.  EXCELLENT is also not a negative tag.
    negative_tag_types = {TagType.CORRUPTED, TagType.PLAGIARISM_SUSPECT}
    has_negative = any(t.tag in negative_tag_types for t in tags)
    if not has_negative and status == ExecutionStatus.SUCCESS:
        confidence = 0.85 + rng.uniform(0.0, 0.15)
        tags.append(
            SubmissionTag(
                submission_id=submission_id,
                tag=TagType.CLEAN,
                source=TagSource.AUTOMATED,
                confidence=round(confidence, 4),
            )
        )

    return tuple(tags)


# ── Public API ───────────────────────────────────────────────────────────


def simulate_grading(
    student: StudentProfile,
    assignment: AssignmentDef,
    submission_id: uuid.UUID,
    attempt_no: int,
    rng: random.Random,
    is_late: bool = False,
    submitted_at: datetime | None = None,
) -> GradingOutcome:
    """Simulate auto-grading for a single student submission.

    This is the main public entry point for the grading engine.  It
    probabilistically generates an ExecutionResult, TestCaseResult records,
    SubmissionTag records, and a total score — all without executing any
    student code.

    The grading pipeline proceeds in these steps:
      1. Compute effective skill (base + attempt boost).
      2. Determine pass category (ALL_PASS / PARTIAL / ALL_FAIL).
      3. Map category to ExecutionStatus + exit_code.
      4. Generate execution runtime_ms.
      5. Compute execution timestamps (started_at, finished_at).
      6. Generate exec_id UUID (before test cases for FK).
      7. Retrieve test cases, decide per-test pass/fail flags.
      8. Create TestCaseResult records + raw total score.
      9. Apply attempt-based score bonus.
      10. Generate stdout/stderr.
      11. Build ExecutionResult.
      12. Generate classification tags and return GradingOutcome.

    Used by: generate_data.py (Step 10 — called once per submission in
             the main student x assignment x attempt loop)

    Args:
        student:       StudentProfile of the submitting student.
                       Uses student.skill_level for outcome probabilities.
        assignment:    AssignmentDef of the assignment being graded.
                       Uses difficulty, num_test_cases, max_score,
                       required_files.
        submission_id: UUID of the Submission being graded (FK for all
                       generated records).
        attempt_no:    Which attempt this is (1, 2, or 3).
                       Higher attempts receive skill and score boosts.
        rng:           Seeded Random instance for deterministic generation.
                       Caller should derive this from MASTER_SEED for
                       reproducibility.
        is_late:       Whether the submission was late.  Passed through
                       to _generate_tags() for LATE_SUBMISSION tagging.
                       Default: False.
        submitted_at:  UTC timestamp of submission.  Used as the base time
                       for computing started_at / finished_at.  If None,
                       defaults to datetime.now(timezone.utc).

    Returns:
        A GradingOutcome frozen dataclass containing:
          - execution_result: ExecutionResult (1 per submission)
          - test_case_results: tuple of TestCaseResult (N per submission)
          - tags: tuple of SubmissionTag (0..N per submission)
          - total_score: float in [0.0, max_score]
    """
    # Step 1: Effective skill with attempt boost.
    effective_skill = _compute_effective_skill(student.skill_level, attempt_no)

    # Step 2: High-level pass category.
    pass_category = _determine_pass_category(effective_skill, rng)

    # Step 3: Concrete execution status.
    status = _determine_execution_status(pass_category, effective_skill, rng)
    exit_code = _EXIT_CODE_MAP[status]

    # Step 4: Execution runtime.
    runtime_ms = _compute_runtime_ms(status, rng)

    # Step 5: Execution timestamps.
    base_time = submitted_at if submitted_at is not None else datetime.now(timezone.utc)
    start_offset = rng.randint(0, EXECUTION_START_MAX_OFFSET_SECONDS)
    started_at = base_time + timedelta(seconds=start_offset)
    finished_at = started_at + timedelta(milliseconds=runtime_ms)

    # Step 6: Generate exec_id BEFORE test case results (FK dependency).
    exec_id = uuid.uuid4()

    # Step 7: Retrieve test cases and decide pass/fail flags.
    test_cases = get_test_cases(assignment.assignment_id)

    # For non-executable statuses, all tests fail regardless.
    if status in (ExecutionStatus.COMPILATION_ERROR, ExecutionStatus.TIMEOUT):
        passed_flags: tuple[bool, ...] = (False,) * len(test_cases)
    else:
        passed_flags = _decide_pass_flags(
            pass_category, test_cases, effective_skill, assignment.difficulty, rng
        )

    # Step 8: Create TestCaseResult records and compute raw score.
    test_case_results, raw_total = _generate_test_case_results(
        exec_id, test_cases, passed_flags, status, rng
    )

    # Step 9: Apply attempt-based score bonus.
    total_score = raw_total
    if attempt_no > 1 and total_score > 0:
        boost = rng.uniform(ATTEMPT_SCORE_BOOST_MIN, ATTEMPT_SCORE_BOOST_MAX)
        boost *= attempt_no - 1
        total_score = min(float(assignment.max_score), total_score + boost)
    total_score = round(max(0.0, total_score), 2)

    # Step 10: Generate stdout/stderr.
    stdout = _generate_stdout(status, test_cases, passed_flags, rng)
    stderr = _generate_stderr(status, assignment, rng)

    # Step 11: Build ExecutionResult.
    execution_result = ExecutionResult(
        exec_id=exec_id,
        submission_id=submission_id,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        exit_code=exit_code,
        stdout=stdout,
        stderr=stderr,
        runtime_ms=runtime_ms,
    )

    # Step 12: Generate classification tags.
    tags = _generate_tags(submission_id, total_score, status, is_late, rng)

    return GradingOutcome(
        execution_result=execution_result,
        test_case_results=test_case_results,
        tags=tags,
        total_score=total_score,
    )
