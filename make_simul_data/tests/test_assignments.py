"""Unit tests for assignment definitions and test case specifications.

Tests the ASSIGNMENTS constant, TestCaseSpec dataclass, get_test_cases(),
get_assignment_by_id(), and DIFFICULTY_WEIGHTS from
make_simul_data.seed_data.assignments.

Run with: pytest make_simul_data/tests/test_assignments.py -v
"""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError
from datetime import date

import pytest

from make_simul_data.seed_data.assignments import (
    ASSIGNMENTS,
    DIFFICULTY_WEIGHTS,
    TestCaseSpec,
    get_assignment_by_id,
    get_test_cases,
)
from make_simul_data.seed_data.config import (
    SEMESTER_END,
    SEMESTER_START,
    AssignmentDef,
)

# ── Constants for tests ─────────────────────────────────────────────────

# Regex pattern for test case IDs: "HW{digit}_TC{2 digits}".
TC_ID_PATTERN: re.Pattern[str] = re.compile(r"^HW\d+_TC\d{2}$")

# Expected number of test cases per assignment, in order HW1..HW5.
EXPECTED_TC_COUNTS: list[int] = [5, 6, 7, 8, 8]


# ── ASSIGNMENTS Constant Tests ──────────────────────────────────────────


class TestAssignmentsConstant:
    """Tests for the module-level ASSIGNMENTS tuple."""

    def test_assignments_count(self) -> None:
        """ASSIGNMENTS contains exactly 5 assignment definitions."""
        assert len(ASSIGNMENTS) == 5

    def test_assignment_type(self) -> None:
        """All elements in ASSIGNMENTS are AssignmentDef instances."""
        for assignment in ASSIGNMENTS:
            assert isinstance(
                assignment, AssignmentDef
            ), f"Expected AssignmentDef, got {type(assignment).__name__}"

    def test_assignment_ids_sequential(self) -> None:
        """Assignment IDs are 'HW1' through 'HW5' in order."""
        expected_ids = ["HW1", "HW2", "HW3", "HW4", "HW5"]
        actual_ids = [a.assignment_id for a in ASSIGNMENTS]
        assert actual_ids == expected_ids

    def test_difficulty_increasing(self) -> None:
        """Difficulty values are strictly increasing: [1, 2, 3, 4, 5]."""
        difficulties = [a.difficulty for a in ASSIGNMENTS]
        assert difficulties == [1, 2, 3, 4, 5]

    def test_num_test_cases(self) -> None:
        """Test case counts match expected values: [5, 6, 7, 8, 8]."""
        actual_counts = [a.num_test_cases for a in ASSIGNMENTS]
        assert actual_counts == EXPECTED_TC_COUNTS

    def test_max_score_all_100(self) -> None:
        """All assignments have max_score == 100."""
        for assignment in ASSIGNMENTS:
            assert assignment.max_score == 100, (
                f"{assignment.assignment_id} has max_score="
                f"{assignment.max_score}, expected 100"
            )

    def test_required_files_not_empty(self) -> None:
        """All assignments have at least one required file."""
        for assignment in ASSIGNMENTS:
            assert (
                len(assignment.required_files) >= 1
            ), f"{assignment.assignment_id} has no required files"

    def test_required_files_are_python(self) -> None:
        """All required files end with '.py'."""
        for assignment in ASSIGNMENTS:
            for filename in assignment.required_files:
                assert filename.endswith(".py"), (
                    f"{assignment.assignment_id} has non-Python "
                    f"required file: {filename!r}"
                )


# ── Due Date Tests ──────────────────────────────────────────────────────


class TestDueDates:
    """Tests for assignment due date calculation and ordering."""

    def test_due_dates_within_semester(self) -> None:
        """All due dates fall between SEMESTER_START and SEMESTER_END."""
        start = date.fromisoformat(SEMESTER_START)
        end = date.fromisoformat(SEMESTER_END)
        for assignment in ASSIGNMENTS:
            due = date.fromisoformat(assignment.due_date)
            assert start < due < end, (
                f"{assignment.assignment_id} due date {assignment.due_date} "
                f"is outside semester range [{SEMESTER_START}, {SEMESTER_END}]"
            )

    def test_due_dates_chronological(self) -> None:
        """Due dates are strictly increasing (HW1 before HW2 before ...)."""
        due_dates = [date.fromisoformat(a.due_date) for a in ASSIGNMENTS]
        for i in range(len(due_dates) - 1):
            assert due_dates[i] < due_dates[i + 1], (
                f"Due dates not chronological: "
                f"{ASSIGNMENTS[i].assignment_id} ({due_dates[i]}) >= "
                f"{ASSIGNMENTS[i + 1].assignment_id} ({due_dates[i + 1]})"
            )


# ── DIFFICULTY_WEIGHTS Tests ────────────────────────────────────────────


class TestDifficultyWeights:
    """Tests for the DIFFICULTY_WEIGHTS mapping."""

    def test_complete_coverage(self) -> None:
        """DIFFICULTY_WEIGHTS has entries for all difficulty levels 1-5."""
        assert set(DIFFICULTY_WEIGHTS.keys()) == {1, 2, 3, 4, 5}

    def test_values_in_range(self) -> None:
        """All weight values are in the open interval (0.0, 1.0)."""
        for level, weight in DIFFICULTY_WEIGHTS.items():
            assert (
                0.0 < weight < 1.0
            ), f"Difficulty {level} weight {weight} is not in (0, 1)"

    def test_weights_increasing(self) -> None:
        """Weights increase monotonically with difficulty level."""
        weights = [DIFFICULTY_WEIGHTS[i] for i in range(1, 6)]
        for i in range(len(weights) - 1):
            assert weights[i] < weights[i + 1], (
                f"Weight for difficulty {i + 1} ({weights[i]}) >= "
                f"weight for difficulty {i + 2} ({weights[i + 1]})"
            )


# ── get_test_cases() Tests ──────────────────────────────────────────────


class TestGetTestCases:
    """Tests for the get_test_cases() public function."""

    def test_correct_count_per_assignment(self) -> None:
        """get_test_cases() returns the correct number of test cases."""
        for assignment, expected_count in zip(
            ASSIGNMENTS, EXPECTED_TC_COUNTS, strict=True
        ):
            test_cases = get_test_cases(assignment.assignment_id)
            assert len(test_cases) == expected_count, (
                f"{assignment.assignment_id}: expected {expected_count} "
                f"test cases, got {len(test_cases)}"
            )

    def test_returns_tuple_of_test_case_def(self) -> None:
        """get_test_cases() returns a tuple of TestCaseSpec instances."""
        test_cases = get_test_cases("HW1")
        assert isinstance(test_cases, tuple)
        for tc in test_cases:
            assert isinstance(tc, TestCaseSpec)

    def test_points_sum_to_max_score(self) -> None:
        """Sum of test case points equals max_score (100) per assignment."""
        for assignment in ASSIGNMENTS:
            test_cases = get_test_cases(assignment.assignment_id)
            total_points = sum(tc.points for tc in test_cases)
            assert total_points == assignment.max_score, (
                f"{assignment.assignment_id}: points sum to "
                f"{total_points}, expected {assignment.max_score}"
            )

    def test_test_case_id_format(self) -> None:
        """All test case IDs match the 'HW{N}_TC{NN}' pattern."""
        for assignment in ASSIGNMENTS:
            test_cases = get_test_cases(assignment.assignment_id)
            for tc in test_cases:
                assert TC_ID_PATTERN.match(tc.test_case_id), (
                    f"Test case ID {tc.test_case_id!r} does not match "
                    f"expected pattern 'HW{{N}}_TC{{NN}}'"
                )

    def test_test_case_ids_belong_to_assignment(self) -> None:
        """Test case IDs start with their parent assignment ID."""
        for assignment in ASSIGNMENTS:
            test_cases = get_test_cases(assignment.assignment_id)
            for tc in test_cases:
                assert tc.test_case_id.startswith(assignment.assignment_id), (
                    f"Test case {tc.test_case_id} does not belong to "
                    f"assignment {assignment.assignment_id}"
                )

    def test_points_are_positive(self) -> None:
        """All test case points are positive (> 0)."""
        for assignment in ASSIGNMENTS:
            test_cases = get_test_cases(assignment.assignment_id)
            for tc in test_cases:
                assert tc.points > 0, (
                    f"Test case {tc.test_case_id} has non-positive "
                    f"points: {tc.points}"
                )

    def test_invalid_assignment_id_raises_value_error(self) -> None:
        """get_test_cases() raises ValueError for an unknown ID."""
        with pytest.raises(ValueError, match="HW99"):
            get_test_cases("HW99")


# ── get_assignment_by_id() Tests ────────────────────────────────────────


class TestGetAssignmentById:
    """Tests for the get_assignment_by_id() public function."""

    def test_returns_correct_assignment(self) -> None:
        """get_assignment_by_id() returns the correct AssignmentDef."""
        for assignment in ASSIGNMENTS:
            result = get_assignment_by_id(assignment.assignment_id)
            assert result == assignment

    def test_invalid_id_raises_value_error(self) -> None:
        """get_assignment_by_id() raises ValueError for unknown ID."""
        with pytest.raises(ValueError, match="HW99"):
            get_assignment_by_id("HW99")


# ── Frozen Dataclass Tests ──────────────────────────────────────────────


class TestFrozenDataclasses:
    """Tests that TestCaseSpec and AssignmentDef are immutable."""

    def test_test_case_def_is_frozen(self) -> None:
        """Assigning to a TestCaseSpec field raises FrozenInstanceError."""
        test_cases = get_test_cases("HW1")
        with pytest.raises(FrozenInstanceError):
            test_cases[0].points = 50.0  # type: ignore[misc]

    def test_assignment_def_is_frozen(self) -> None:
        """Assigning to an AssignmentDef field raises FrozenInstanceError."""
        with pytest.raises(FrozenInstanceError):
            ASSIGNMENTS[0].max_score = 200  # type: ignore[misc]
