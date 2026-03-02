"""Unit tests for student profile generation.

Tests the generate_students() function, StudentProfile dataclass, and
get_attempt_count() helper from make_simul_data.seed_data.students.

Run with: pytest make_simul_data/tests/test_students.py -v
"""

from __future__ import annotations

import re
from dataclasses import FrozenInstanceError

import pytest

from make_simul_data.seed_data.students import (
    generate_students,
    get_attempt_count,
)

# ── Constants for tests ─────────────────────────────────────────────────

# Small sample size for fast test execution.
SMALL_SAMPLE: int = 10

# Large sample size for statistical distribution tests.
LARGE_SAMPLE: int = 1000

# Fixed seed for deterministic tests.
TEST_SEED: int = 42

# Regex pattern for student IDs: "S" followed by exactly 3 digits.
STUDENT_ID_PATTERN: re.Pattern[str] = re.compile(r"^S\d{3}$")


# ── Basic Generation Tests ──────────────────────────────────────────────


class TestGenerateStudentsCount:
    """Tests for correct student count generation."""

    def test_default_count(self) -> None:
        """generate_students() with default num returns 100 students."""
        students = generate_students(seed=TEST_SEED)
        assert len(students) == 100

    def test_small_count(self) -> None:
        """generate_students(num=10) returns exactly 10 students."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        assert len(students) == SMALL_SAMPLE

    def test_single_student(self) -> None:
        """generate_students(num=1) returns exactly 1 student."""
        students = generate_students(num=1, seed=TEST_SEED)
        assert len(students) == 1
        assert students[0].student_id == "S001"


# ── Reproducibility Tests ───────────────────────────────────────────────


class TestReproducibility:
    """Tests that the same seed produces identical results."""

    def test_same_seed_identical_output(self) -> None:
        """Two calls with the same seed produce identical student lists."""
        students_a = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        students_b = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        assert students_a == students_b

    def test_different_seed_different_output(self) -> None:
        """Two calls with different seeds produce different student lists."""
        students_a = generate_students(num=SMALL_SAMPLE, seed=42)
        students_b = generate_students(num=SMALL_SAMPLE, seed=99)
        # At minimum, skill_levels should differ.
        skills_a = [s.skill_level for s in students_a]
        skills_b = [s.skill_level for s in students_b]
        assert skills_a != skills_b


# ── Student ID Format Tests ─────────────────────────────────────────────


class TestStudentIdFormat:
    """Tests for student ID formatting and sequencing."""

    def test_id_format_matches_pattern(self) -> None:
        """All student IDs match the 'S{NNN}' pattern."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        for student in students:
            assert STUDENT_ID_PATTERN.match(student.student_id), (
                f"Student ID {student.student_id!r} does not match "
                f"expected pattern 'S{{NNN}}'"
            )

    def test_ids_are_sequential(self) -> None:
        """Student IDs are sequential from S001 to S{num}."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        expected_ids = [f"S{i:03d}" for i in range(1, SMALL_SAMPLE + 1)]
        actual_ids = [s.student_id for s in students]
        assert actual_ids == expected_ids


# ── Skill Level Tests ───────────────────────────────────────────────────


class TestSkillLevel:
    """Tests for skill level values and distribution."""

    def test_skill_level_range(self) -> None:
        """All skill levels are within [0.0, 1.0]."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        for student in students:
            assert 0.0 <= student.skill_level <= 1.0, (
                f"Student {student.student_id} skill_level "
                f"{student.skill_level} is out of range [0, 1]"
            )

    def test_skill_level_distribution_mean(self) -> None:
        """With 1000 students, mean skill_level is roughly 0.714 (Beta(5,2))."""
        students = generate_students(num=LARGE_SAMPLE, seed=TEST_SEED)
        mean_skill = sum(s.skill_level for s in students) / len(students)
        # Beta(5, 2) theoretical mean = 5 / (5 + 2) ≈ 0.714.
        # Allow ±0.05 tolerance for sampling variation.
        assert 0.66 < mean_skill < 0.77, (
            f"Mean skill level {mean_skill:.4f} is outside expected "
            f"range (0.66, 0.77) for Beta(5, 2)"
        )


# ── Email Tests ─────────────────────────────────────────────────────────


class TestEmail:
    """Tests for email uniqueness and format."""

    def test_emails_are_unique(self) -> None:
        """All student emails are unique (no duplicates)."""
        students = generate_students(num=100, seed=TEST_SEED)
        emails = [s.email for s in students]
        assert len(emails) == len(set(emails)), "Duplicate emails found"

    def test_emails_contain_at_sign(self) -> None:
        """All emails contain the '@' character."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        for student in students:
            assert "@" in student.email, (
                f"Student {student.student_id} email {student.email!r} "
                f"does not contain '@'"
            )


# ── Attempt Counts Tests ────────────────────────────────────────────────


class TestAttemptCounts:
    """Tests for pre-computed attempt counts per assignment."""

    def test_attempt_counts_for_all_assignments(self) -> None:
        """Each student has attempt_counts for HW1 through HW5."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        expected_hw_ids = {f"HW{i}" for i in range(1, 6)}
        for student in students:
            actual_hw_ids = {aid for aid, _ in student.attempt_counts}
            assert actual_hw_ids == expected_hw_ids, (
                f"Student {student.student_id} missing assignments: "
                f"{expected_hw_ids - actual_hw_ids}"
            )

    def test_attempt_counts_valid_range(self) -> None:
        """All attempt counts are in {1, 2, 3}."""
        students = generate_students(num=SMALL_SAMPLE, seed=TEST_SEED)
        for student in students:
            for aid, count in student.attempt_counts:
                assert count in {1, 2, 3}, (
                    f"Student {student.student_id} has invalid "
                    f"attempt count {count} for {aid}"
                )


# ── Behavioral Flag Tests ───────────────────────────────────────────────


class TestBehavioralFlags:
    """Tests for is_late_submitter and generates_pdf distribution."""

    def test_late_submitter_rate(self) -> None:
        """With 1000 students, ~20% are late submitters (±5%)."""
        students = generate_students(num=LARGE_SAMPLE, seed=TEST_SEED)
        late_count = sum(1 for s in students if s.is_late_submitter)
        late_rate = late_count / len(students)
        assert 0.15 < late_rate < 0.25, (
            f"Late submitter rate {late_rate:.3f} is outside expected "
            f"range (0.15, 0.25)"
        )

    def test_pdf_generation_rate(self) -> None:
        """With 1000 students, ~40% generate PDFs (±5%)."""
        students = generate_students(num=LARGE_SAMPLE, seed=TEST_SEED)
        pdf_count = sum(1 for s in students if s.generates_pdf)
        pdf_rate = pdf_count / len(students)
        assert 0.35 < pdf_rate < 0.45, (
            f"PDF generation rate {pdf_rate:.3f} is outside expected "
            f"range (0.35, 0.45)"
        )


# ── Helper Function Tests ───────────────────────────────────────────────


class TestGetAttemptCount:
    """Tests for the get_attempt_count() helper function."""

    def test_returns_correct_count(self) -> None:
        """get_attempt_count() returns the correct value for a valid ID."""
        students = generate_students(num=1, seed=TEST_SEED)
        student = students[0]
        for aid, expected_count in student.attempt_counts:
            actual_count = get_attempt_count(student, aid)
            assert actual_count == expected_count

    def test_raises_key_error_for_invalid_id(self) -> None:
        """get_attempt_count() raises KeyError for an unknown assignment."""
        students = generate_students(num=1, seed=TEST_SEED)
        with pytest.raises(KeyError, match="HW99"):
            get_attempt_count(students[0], "HW99")


# ── Frozen Dataclass Test ───────────────────────────────────────────────


class TestFrozenDataclass:
    """Tests that StudentProfile is immutable (frozen)."""

    def test_cannot_modify_field(self) -> None:
        """Assigning to a StudentProfile field raises FrozenInstanceError."""
        students = generate_students(num=1, seed=TEST_SEED)
        with pytest.raises(FrozenInstanceError):
            students[0].skill_level = 0.5  # type: ignore[misc]
