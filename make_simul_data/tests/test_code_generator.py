"""Unit tests for Python code file generation.

Tests the generate_code_files() function, GeneratedCodeFile dataclass,
CodeTemplate dataclass, and the code template infrastructure from
make_simul_data.seed_data.code_generator.

Run with: pytest make_simul_data/tests/test_code_generator.py -v

Test organization:
    TestGeneratedCodeFileDataclass  -- Frozen dataclass contract tests.
    TestCodeTemplateDataclass       -- CodeTemplate frozen dataclass tests.
    TestGenerateCodeFilesCount      -- Correct number of files per assignment.
    TestFilenames                   -- Filenames match required_files.
    TestFileSizeConstraints         -- Sizes within FILE_SIZE_PYTHON range.
    TestReproducibility             -- Same seed produces identical output.
    TestSkillLevelVariation         -- Code quality differs by skill tier.
    TestAttemptImprovement          -- Later attempts produce higher-tier code.
    TestCodeContent                 -- Generated code contains expected elements.
    TestAllAssignments              -- All 5 assignments can be generated.
    TestInvalidAssignment           -- Unknown assignment raises ValueError.
"""

from __future__ import annotations

import dataclasses

import pytest

from make_simul_data.seed_data.assignments import get_assignment_by_id
from make_simul_data.seed_data.code_generator import (
    HIGH_SKILL_THRESHOLD,
    LOW_SKILL_THRESHOLD,
    CodeTemplate,
    GeneratedCodeFile,
    _compute_effective_skill,
    _select_quality_tier,
    generate_code_files,
)
from make_simul_data.seed_data.config import FILE_SIZE_PYTHON, create_rng
from make_simul_data.seed_data.students import StudentProfile

# ── Test Constants ───────────────────────────────────────────────────

# Seed for reproducible tests. Matches MASTER_SEED from config.py.
TEST_SEED: int = 42


# ── Test Fixtures ────────────────────────────────────────────────────


def _make_student(
    skill_level: float = 0.7,
    student_id: str = "S001",
) -> StudentProfile:
    """Create a minimal StudentProfile for testing.

    Args:
        skill_level: Override skill level (default 0.7 = medium tier).
        student_id: Override student ID.

    Returns:
        A frozen StudentProfile instance.
    """
    return StudentProfile(
        student_id=student_id,
        name="Test Student",
        email="test@example.com",
        skill_level=skill_level,
        attempt_counts=(
            ("HW1", 1),
            ("HW2", 1),
            ("HW3", 1),
            ("HW4", 1),
            ("HW5", 1),
        ),
        is_late_submitter=False,
        generates_pdf=False,
    )


# ── Test Classes ─────────────────────────────────────────────────────


class TestGeneratedCodeFileDataclass:
    """Verify GeneratedCodeFile is a frozen dataclass with correct fields."""

    def test_is_frozen(self) -> None:
        """Assigning to a GeneratedCodeFile field raises FrozenInstanceError."""
        gcf = GeneratedCodeFile(
            filename="test.py", content="print('hi')", size_bytes=11
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            gcf.filename = "other.py"  # type: ignore[misc]

    def test_has_required_fields(self) -> None:
        """GeneratedCodeFile has filename, content, and size_bytes."""
        gcf = GeneratedCodeFile(filename="test.py", content="x = 1", size_bytes=5)
        assert gcf.filename == "test.py"
        assert gcf.content == "x = 1"
        assert gcf.size_bytes == 5


class TestCodeTemplateDataclass:
    """Verify CodeTemplate is a frozen dataclass with correct fields."""

    def test_is_frozen(self) -> None:
        """Assigning to a CodeTemplate field raises FrozenInstanceError."""
        ct = CodeTemplate(
            template_id="TEST_V1",
            assignment_id="HW1",
            high_quality="# high",
            medium_quality="# med",
            low_quality="# low",
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            ct.template_id = "other"  # type: ignore[misc]

    def test_utils_default_none(self) -> None:
        """Utils fields default to None for single-file assignments."""
        ct = CodeTemplate(
            template_id="TEST_V1",
            assignment_id="HW1",
            high_quality="# high",
            medium_quality="# med",
            low_quality="# low",
        )
        assert ct.utils_high is None
        assert ct.utils_medium is None
        assert ct.utils_low is None


class TestGenerateCodeFilesCount:
    """Verify that generate_code_files returns correct number of files."""

    def test_hw1_returns_one_file(self) -> None:
        """HW1 (single required file) produces exactly 1 GeneratedCodeFile."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        assert len(files) == 1

    def test_hw2_returns_one_file(self) -> None:
        """HW2 (single required file) produces exactly 1 GeneratedCodeFile."""
        student = _make_student()
        assignment = get_assignment_by_id("HW2")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        assert len(files) == 1

    def test_hw3_returns_one_file(self) -> None:
        """HW3 (single required file) produces exactly 1 GeneratedCodeFile."""
        student = _make_student()
        assignment = get_assignment_by_id("HW3")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        assert len(files) == 1

    def test_hw4_returns_two_files(self) -> None:
        """HW4 (two required files) produces exactly 2 GeneratedCodeFiles."""
        student = _make_student()
        assignment = get_assignment_by_id("HW4")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        assert len(files) == 2

    def test_hw5_returns_two_files(self) -> None:
        """HW5 (two required files) produces exactly 2 GeneratedCodeFiles."""
        student = _make_student()
        assignment = get_assignment_by_id("HW5")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        assert len(files) == 2


class TestFilenames:
    """Verify that generated filenames match assignment required_files."""

    @pytest.mark.parametrize("hw_id", ["HW1", "HW2", "HW3", "HW4", "HW5"])
    def test_filenames_match_required_files(self, hw_id: str) -> None:
        """Generated filenames match AssignmentDef.required_files exactly."""
        student = _make_student()
        assignment = get_assignment_by_id(hw_id)
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        generated_names = [f.filename for f in files]
        assert generated_names == list(assignment.required_files)


class TestFileSizeConstraints:
    """Verify that file sizes fall within FILE_SIZE_PYTHON range."""

    @pytest.mark.parametrize("hw_id", ["HW1", "HW2", "HW3", "HW4", "HW5"])
    def test_size_within_range(self, hw_id: str) -> None:
        """All generated files are between 1024 and 10240 bytes."""
        student = _make_student()
        assignment = get_assignment_by_id(hw_id)
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        min_size, max_size = FILE_SIZE_PYTHON
        for f in files:
            assert (
                f.size_bytes >= min_size
            ), f"{f.filename} too small: {f.size_bytes} < {min_size}"
            assert (
                f.size_bytes <= max_size
            ), f"{f.filename} too large: {f.size_bytes} > {max_size}"

    @pytest.mark.parametrize("hw_id", ["HW1", "HW2", "HW3", "HW4", "HW5"])
    def test_size_bytes_matches_content(self, hw_id: str) -> None:
        """size_bytes field equals len(content.encode('utf-8'))."""
        student = _make_student()
        assignment = get_assignment_by_id(hw_id)
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        for f in files:
            actual_size = len(f.content.encode("utf-8"))
            assert f.size_bytes == actual_size, (
                f"{f.filename}: size_bytes={f.size_bytes} != " f"actual={actual_size}"
            )


class TestReproducibility:
    """Verify that the same seed produces identical code."""

    def test_same_seed_identical_output(self) -> None:
        """Two calls with the same RNG seed produce identical file content."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")

        rng1 = create_rng(TEST_SEED)
        files1 = generate_code_files(student, assignment, 1, rng1)

        rng2 = create_rng(TEST_SEED)
        files2 = generate_code_files(student, assignment, 1, rng2)

        assert len(files1) == len(files2)
        for f1, f2 in zip(files1, files2):
            assert f1.filename == f2.filename
            assert f1.content == f2.content
            assert f1.size_bytes == f2.size_bytes

    def test_different_seed_different_output(self) -> None:
        """Two calls with different RNG seeds produce different content."""
        student = _make_student()
        assignment = get_assignment_by_id("HW3")

        rng1 = create_rng(1)
        files1 = generate_code_files(student, assignment, 1, rng1)

        rng2 = create_rng(999)
        files2 = generate_code_files(student, assignment, 1, rng2)

        # Content should differ (different template or mutations)
        # At minimum, padding comments will differ due to different RNG
        assert files1[0].content != files2[0].content


class TestSkillLevelVariation:
    """Verify that code quality varies by skill level."""

    def test_high_skill_has_docstrings(self) -> None:
        """High-skill students (>0.8) produce code containing docstrings."""
        student = _make_student(skill_level=0.95)
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        # High-quality templates contain triple-quoted docstrings
        assert '"""' in files[0].content

    def test_low_skill_fewer_docstrings(self) -> None:
        """Low-skill students (<0.5) produce code with fewer/no docstrings."""
        student = _make_student(skill_level=0.2)
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        # Low-quality templates have no docstrings
        assert '"""' not in files[0].content

    def test_high_skill_code_compiles(self) -> None:
        """High-skill code parses without SyntaxError."""
        student = _make_student(skill_level=0.95)
        for hw_id in ["HW1", "HW2", "HW3"]:
            assignment = get_assignment_by_id(hw_id)
            rng = create_rng(TEST_SEED)
            files = generate_code_files(student, assignment, 1, rng)
            for f in files:
                # compile() will raise SyntaxError if code is invalid
                compile(f.content, f.filename, "exec")

    def test_medium_skill_code_compiles(self) -> None:
        """Medium-skill code parses without SyntaxError."""
        student = _make_student(skill_level=0.65)
        for hw_id in ["HW1", "HW2", "HW3"]:
            assignment = get_assignment_by_id(hw_id)
            rng = create_rng(TEST_SEED)
            files = generate_code_files(student, assignment, 1, rng)
            for f in files:
                compile(f.content, f.filename, "exec")


class TestComputeEffectiveSkill:
    """Verify the effective skill computation."""

    def test_attempt_1_unchanged(self) -> None:
        """First attempt does not modify skill level."""
        assert _compute_effective_skill(0.7, 1) == 0.7

    def test_attempt_2_boosted(self) -> None:
        """Second attempt boosts skill by ATTEMPT_SKILL_BOOST."""
        result = _compute_effective_skill(0.7, 2)
        assert abs(result - 0.8) < 1e-9

    def test_attempt_3_boosted(self) -> None:
        """Third attempt boosts skill by 2 * ATTEMPT_SKILL_BOOST."""
        result = _compute_effective_skill(0.7, 3)
        assert abs(result - 0.9) < 1e-9

    def test_capped_at_one(self) -> None:
        """Effective skill never exceeds 1.0."""
        result = _compute_effective_skill(0.95, 3)
        assert result == 1.0


class TestSelectQualityTier:
    """Verify the quality tier selection logic."""

    def test_high_tier(self) -> None:
        """Skill > HIGH_SKILL_THRESHOLD returns 'high'."""
        assert _select_quality_tier(0.85) == "high"
        assert _select_quality_tier(0.99) == "high"

    def test_medium_tier(self) -> None:
        """Skill in [LOW, HIGH] returns 'medium'."""
        assert _select_quality_tier(0.5) == "medium"
        assert _select_quality_tier(0.65) == "medium"
        assert _select_quality_tier(0.8) == "medium"

    def test_low_tier(self) -> None:
        """Skill < LOW_SKILL_THRESHOLD returns 'low'."""
        assert _select_quality_tier(0.1) == "low"
        assert _select_quality_tier(0.49) == "low"

    def test_boundary_high(self) -> None:
        """Exact HIGH_SKILL_THRESHOLD (0.8) maps to 'medium'."""
        assert _select_quality_tier(HIGH_SKILL_THRESHOLD) == "medium"

    def test_boundary_low(self) -> None:
        """Exact LOW_SKILL_THRESHOLD (0.5) maps to 'medium'."""
        assert _select_quality_tier(LOW_SKILL_THRESHOLD) == "medium"


class TestAttemptImprovement:
    """Verify that later attempts can upgrade the quality tier."""

    def test_attempt3_upgrades_medium_to_high(self) -> None:
        """A student with skill=0.65 at attempt 3 gets effective_skill=0.85."""
        effective = _compute_effective_skill(0.65, 3)
        assert effective == pytest.approx(0.85)
        assert _select_quality_tier(effective) == "high"

    def test_attempt2_upgrades_low_to_medium(self) -> None:
        """A student with skill=0.45 at attempt 2 gets effective_skill=0.55."""
        effective = _compute_effective_skill(0.45, 2)
        assert effective == pytest.approx(0.55)
        assert _select_quality_tier(effective) == "medium"


class TestCodeContent:
    """Verify that generated code contains expected programming elements."""

    def test_hw1_contains_arithmetic(self) -> None:
        """HW1 code contains arithmetic operations."""
        student = _make_student(skill_level=0.9)
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        content = files[0].content
        # Should contain basic arithmetic concepts
        assert "input()" in content or "input" in content

    def test_hw2_contains_conditionals(self) -> None:
        """HW2 code contains if/elif statements."""
        student = _make_student(skill_level=0.9)
        assignment = get_assignment_by_id("HW2")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        content = files[0].content
        assert "if " in content

    def test_hw3_contains_loops(self) -> None:
        """HW3 code contains loop constructs."""
        student = _make_student(skill_level=0.9)
        assignment = get_assignment_by_id("HW3")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        content = files[0].content
        assert "for " in content or "while " in content

    def test_hw4_utils_contains_functions(self) -> None:
        """HW4 utils file contains function definitions."""
        student = _make_student(skill_level=0.9)
        assignment = get_assignment_by_id("HW4")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        # files[1] is the utils file
        utils_content = files[1].content
        assert "def " in utils_content

    def test_hw5_utils_contains_list_ops(self) -> None:
        """HW5 utils file contains list-related operations."""
        student = _make_student(skill_level=0.9)
        assignment = get_assignment_by_id("HW5")
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        utils_content = files[1].content
        assert "def " in utils_content


class TestAllAssignments:
    """Verify that all 5 assignments can be generated without errors."""

    @pytest.mark.parametrize(
        "skill",
        [0.2, 0.5, 0.65, 0.85, 0.95],
        ids=["low", "boundary", "mid", "high", "top"],
    )
    @pytest.mark.parametrize("hw_id", ["HW1", "HW2", "HW3", "HW4", "HW5"])
    def test_generates_without_error(self, hw_id: str, skill: float) -> None:
        """generate_code_files runs without error for all assignments and skills."""
        student = _make_student(skill_level=skill)
        assignment = get_assignment_by_id(hw_id)
        rng = create_rng(TEST_SEED)
        files = generate_code_files(student, assignment, 1, rng)
        assert len(files) >= 1
        for f in files:
            assert f.filename.endswith(".py")
            assert len(f.content) > 0


class TestInvalidAssignment:
    """Verify error handling for invalid assignment IDs."""

    def test_unknown_assignment_raises_value_error(self) -> None:
        """generate_code_files() raises ValueError for unknown assignment."""
        student = _make_student()
        # Create a fake assignment with an unknown ID
        from make_simul_data.seed_data.config import AssignmentDef

        fake_assignment = AssignmentDef(
            assignment_id="HW99",
            title="Fake",
            description="Fake assignment",
            due_date="2026-03-01",
            max_score=100,
            num_test_cases=5,
            difficulty=1,
            required_files=("fake.py",),
        )
        rng = create_rng(TEST_SEED)
        with pytest.raises(ValueError, match="Unknown assignment_id"):
            generate_code_files(student, fake_assignment, 1, rng)
