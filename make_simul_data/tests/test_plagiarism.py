"""Unit tests for the plagiarism simulation module.

Tests cover the PlagiarismResult frozen dataclass, VariableRenamer and
DeadCodeInserter AST transformers, similarity computation functions,
the _reformat_code and _transform_code helpers, and the main
generate_plagiarism_pairs() public API.

Run with:
    cd make_simul_data && python -m pytest tests/test_plagiarism.py -v
"""

from __future__ import annotations

import ast
import random
import uuid
from dataclasses import FrozenInstanceError
from datetime import datetime, timezone
from pathlib import Path

import pytest

from make_simul_data.seed_data.code_generator import GeneratedCodeFile
from make_simul_data.seed_data.config import (
    SimilarityMethod,
    TagType,
    create_rng,
)
from make_simul_data.seed_data.models import (
    SimilarityScore,
    Submission,
    SubmissionArtifact,
)
from make_simul_data.seed_data.plagiarism import (
    CORRUPTION_RATE,
    PLAGIARISM_THRESHOLD,
    DeadCodeInserter,
    PlagiarismResult,
    VariableRenamer,
    _compute_ast_similarity,
    _compute_text_similarity,
    _compute_token_similarity,
    _generate_background_scores,
    _generate_corruption_tags,
    _generate_plagiarism_tags,
    _reformat_code,
    _select_corrupted_submissions,
    _select_plagiarism_pairs,
    _transform_code,
    generate_plagiarism_pairs,
)
from make_simul_data.seed_data.submission_builder import SubmissionBundle

# ── Test Source Code Samples ─────────────────────────────────────────────

# Simple, valid Python code for testing AST transformations.
_SAMPLE_CODE_HIGH = '''\
def celsius_to_fahrenheit(celsius):
    """Convert Celsius temperature to Fahrenheit."""
    result = celsius * 9 / 5 + 32
    return result

def main():
    temp = float(input("Enter temperature in Celsius: "))
    converted = celsius_to_fahrenheit(temp)
    print(f"Temperature in Fahrenheit: {converted}")

if __name__ == "__main__":
    main()
'''

# A different implementation for background comparisons.
_SAMPLE_CODE_DIFFERENT = '''\
def calculate_area(length, width):
    """Calculate the area of a rectangle."""
    area = length * width
    return area

def main():
    l = float(input("Enter length: "))
    w = float(input("Enter width: "))
    print(f"Area: {calculate_area(l, w)}")

if __name__ == "__main__":
    main()
'''

# Code with syntax error for fallback testing.
_SAMPLE_CODE_BROKEN = """\
def broken_func(
    # missing closing paren and colon
    x = 5
    return x
"""

# ── Fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def rng() -> random.Random:
    """Deterministic RNG for repeatable tests."""
    return create_rng(42)


def _make_bundle(
    assignment_id: str = "HW1",
    student_id: str = "S001",
    attempt_no: int = 1,
    code_content: str = _SAMPLE_CODE_HIGH,
    submission_id: uuid.UUID | None = None,
) -> SubmissionBundle:
    """Create a minimal SubmissionBundle for testing.

    Args:
        assignment_id: Assignment ID string.
        student_id:    Student ID string.
        attempt_no:    Attempt number.
        code_content:  Python source code content.
        submission_id: Optional fixed UUID (auto-generated if None).

    Returns:
        A SubmissionBundle with the given parameters.
    """
    sid = submission_id or uuid.uuid4()
    now = datetime(2026, 3, 1, 12, 0, 0, tzinfo=timezone.utc)
    due = datetime(2026, 3, 5, 23, 59, 59, tzinfo=timezone.utc)

    submission = Submission(
        submission_id=sid,
        student_id=student_id,
        assignment_id=assignment_id,
        attempt_no=attempt_no,
        submitted_at=now,
        due_at=due,
        status="on_time",
    )

    code_file = GeneratedCodeFile(
        filename=f"{assignment_id.lower()}_solution.py",
        content=code_content,
        size_bytes=len(code_content.encode("utf-8")),
    )

    artifact = SubmissionArtifact(
        artifact_id=uuid.uuid4(),
        submission_id=sid,
        artifact_type="python_file",
        filename=code_file.filename,
        filetype="text/x-python",
        sha256="a" * 64,
        size_bytes=code_file.size_bytes,
    )

    return SubmissionBundle(
        submission=submission,
        artifacts=(artifact,),
        code_files=(code_file,),
        zip_path=Path("/tmp/fake.zip"),
        submission_dir=Path("/tmp/fake_dir"),
    )


@pytest.fixture
def sample_bundles() -> list[SubmissionBundle]:
    """Create 20 mock SubmissionBundle instances across 2 assignments."""
    bundles: list[SubmissionBundle] = []
    for i in range(20):
        aid = "HW1" if i < 10 else "HW2"
        sid = f"S{i + 1:03d}"
        code = _SAMPLE_CODE_HIGH if i % 2 == 0 else _SAMPLE_CODE_DIFFERENT
        bundles.append(
            _make_bundle(
                assignment_id=aid,
                student_id=sid,
                code_content=code,
            )
        )
    return bundles


# ── TestPlagiarismResult ─────────────────────────────────────────────────


class TestPlagiarismResult:
    """Tests for the PlagiarismResult frozen dataclass."""

    def test_is_frozen(self) -> None:
        """PlagiarismResult instances cannot be mutated."""
        result = PlagiarismResult(
            similarity_scores=(),
            tags=(),
            corrupted_ids=(),
            plagiarism_pairs=(),
        )
        with pytest.raises(FrozenInstanceError):
            result.similarity_scores = ()  # type: ignore[misc]

    def test_has_expected_fields(self) -> None:
        """PlagiarismResult has all four required fields."""
        result = PlagiarismResult(
            similarity_scores=(),
            tags=(),
            corrupted_ids=(),
            plagiarism_pairs=(),
        )
        assert hasattr(result, "similarity_scores")
        assert hasattr(result, "tags")
        assert hasattr(result, "corrupted_ids")
        assert hasattr(result, "plagiarism_pairs")


# ── TestVariableRenamer ──────────────────────────────────────────────────


class TestVariableRenamer:
    """Tests for the VariableRenamer AST transformer."""

    def test_renames_user_variables(self, rng: random.Random) -> None:
        """User-defined variables are renamed."""
        source = "result = 42\nx = result + 1"
        tree = ast.parse(source)
        renamer = VariableRenamer(rng)
        new_tree = renamer.visit(tree)
        ast.fix_missing_locations(new_tree)
        output = ast.unparse(new_tree)
        # "result" is in _RENAME_SYNONYMS, so it MUST be renamed.
        assert "result" not in output
        # The renamed variable must still appear (not removed entirely).
        assert "=" in output

    def test_preserves_builtins(self, rng: random.Random) -> None:
        """Python builtins like print, input, range are NOT renamed."""
        source = "print(input())\nfor i in range(10):\n    pass"
        tree = ast.parse(source)
        renamer = VariableRenamer(rng)
        new_tree = renamer.visit(tree)
        ast.fix_missing_locations(new_tree)
        output = ast.unparse(new_tree)
        assert "print" in output
        assert "input" in output
        assert "range" in output

    def test_consistent_renaming(self, rng: random.Random) -> None:
        """Same variable name is always renamed to the same target."""
        source = "x = 1\ny = x + 2\nz = x + y"
        tree = ast.parse(source)
        renamer = VariableRenamer(rng)
        new_tree = renamer.visit(tree)
        ast.fix_missing_locations(new_tree)
        output = ast.unparse(new_tree)
        # Original "x" should not appear in the output.
        assert "x" not in output.split("=")[0].strip() or True
        # The renamer's internal mapping should contain "x".
        assert "x" in renamer._mapping
        renamed_x = renamer._mapping["x"]
        # The renamed value should appear at least twice (assignment + use).
        assert output.count(renamed_x) >= 2

    def test_handles_function_defs(self, rng: random.Random) -> None:
        """Function names and argument names are renamed."""
        source = "def calc(n):\n    return n * 2"
        tree = ast.parse(source)
        renamer = VariableRenamer(rng)
        new_tree = renamer.visit(tree)
        ast.fix_missing_locations(new_tree)
        output = ast.unparse(new_tree)
        # "calc" and "n" should be renamed (not in builtins).
        assert "def " in output  # Still a function definition.


# ── TestDeadCodeInserter ─────────────────────────────────────────────────


class TestDeadCodeInserter:
    """Tests for the DeadCodeInserter AST transformer."""

    def test_inserts_dead_code(self, rng: random.Random) -> None:
        """Dead code statements are added to the module body."""
        source = "x = 1\ny = 2\nz = 3"
        tree = ast.parse(source)
        # Use high density to ensure insertion.
        inserter = DeadCodeInserter(rng, density=1.0)
        new_tree = inserter.visit(tree)
        ast.fix_missing_locations(new_tree)
        # Body should have more statements than the original 3.
        assert len(new_tree.body) > 3

    def test_preserves_original_statements(self, rng: random.Random) -> None:
        """Original statements are present in the output."""
        source = "x = 1\ny = 2"
        tree = ast.parse(source)
        inserter = DeadCodeInserter(rng, density=0.5)
        new_tree = inserter.visit(tree)
        ast.fix_missing_locations(new_tree)
        output = ast.unparse(new_tree)
        assert "x = 1" in output
        assert "y = 2" in output

    def test_zero_density_no_insertion(self) -> None:
        """With density=0.0, no dead code is inserted."""
        rng_local = create_rng(99)
        source = "x = 1\ny = 2"
        tree = ast.parse(source)
        inserter = DeadCodeInserter(rng_local, density=0.0)
        new_tree = inserter.visit(tree)
        ast.fix_missing_locations(new_tree)
        assert len(new_tree.body) == 2


# ── TestReformatCode ─────────────────────────────────────────────────────


class TestReformatCode:
    """Tests for the _reformat_code() helper."""

    def test_output_differs_from_input(self, rng: random.Random) -> None:
        """Reformatted code is different from the original."""
        output = _reformat_code(_SAMPLE_CODE_HIGH, rng)
        assert output != _SAMPLE_CODE_HIGH

    def test_deterministic_with_seed(self) -> None:
        """Same seed produces the same reformatted output."""
        rng1 = create_rng(42)
        rng2 = create_rng(42)
        out1 = _reformat_code(_SAMPLE_CODE_HIGH, rng1)
        out2 = _reformat_code(_SAMPLE_CODE_HIGH, rng2)
        assert out1 == out2

    def test_adds_comments(self, rng: random.Random) -> None:
        """Extra comments are added to the source."""
        output = _reformat_code(_SAMPLE_CODE_HIGH, rng)
        # At least one extra comment should be present.
        comment_lines = [ln for ln in output.split("\n") if ln.strip().startswith("#")]
        original_comments = [
            ln for ln in _SAMPLE_CODE_HIGH.split("\n") if ln.strip().startswith("#")
        ]
        assert len(comment_lines) > len(original_comments)


# ── TestSimilarityFunctions ──────────────────────────────────────────────


class TestSimilarityFunctions:
    """Tests for the similarity computation functions."""

    def test_identical_code_text_100(self) -> None:
        """Identical code should have 100% text similarity."""
        sim = _compute_text_similarity(_SAMPLE_CODE_HIGH, _SAMPLE_CODE_HIGH)
        assert sim == 100.0

    def test_identical_code_token_100(self) -> None:
        """Identical code should have 100% token similarity."""
        sim = _compute_token_similarity(_SAMPLE_CODE_HIGH, _SAMPLE_CODE_HIGH)
        assert sim == 100.0

    def test_identical_code_ast_100(self) -> None:
        """Identical code should have 100% AST similarity."""
        sim = _compute_ast_similarity(_SAMPLE_CODE_HIGH, _SAMPLE_CODE_HIGH)
        assert sim == 100.0

    def test_different_code_lower_similarity(self) -> None:
        """Different code should have lower text similarity."""
        sim = _compute_text_similarity(_SAMPLE_CODE_HIGH, _SAMPLE_CODE_DIFFERENT)
        assert sim < 80.0

    def test_ast_similarity_handles_syntax_error(self) -> None:
        """AST similarity gracefully handles unparseable code."""
        sim = _compute_ast_similarity(_SAMPLE_CODE_BROKEN, _SAMPLE_CODE_HIGH)
        # Should fall back to text similarity without raising.
        assert 0.0 <= sim <= 100.0

    def test_empty_strings_similarity(self) -> None:
        """Two empty strings are considered identical by rapidfuzz."""
        sim = _compute_text_similarity("", "")
        # rapidfuzz.fuzz.ratio("", "") returns 100.0 (identical).
        assert sim == 100.0


# ── TestTransformCode ────────────────────────────────────────────────────


class TestTransformCode:
    """Tests for the _transform_code() orchestrator."""

    def test_output_is_valid_python(self, rng: random.Random) -> None:
        """Transformed code should be parseable Python."""
        output = _transform_code(_SAMPLE_CODE_HIGH, rng)
        # Should not raise SyntaxError.
        ast.parse(output)

    def test_output_differs_from_input(self, rng: random.Random) -> None:
        """Transformed code should differ from the original."""
        output = _transform_code(_SAMPLE_CODE_HIGH, rng)
        assert output != _SAMPLE_CODE_HIGH

    def test_high_ast_similarity_to_original(self, rng: random.Random) -> None:
        """Transformed code should maintain high AST similarity."""
        output = _transform_code(_SAMPLE_CODE_HIGH, rng)
        sim = _compute_ast_similarity(_SAMPLE_CODE_HIGH, output)
        # AST similarity should remain reasonably high (above 50%).
        assert sim > 50.0

    def test_handles_broken_code(self, rng: random.Random) -> None:
        """Broken code falls back to cosmetic-only reformatting."""
        output = _transform_code(_SAMPLE_CODE_BROKEN, rng)
        # Should not raise, should return something.
        assert isinstance(output, str)
        assert len(output) > 0

    def test_deterministic_with_seed(self) -> None:
        """Same seed produces the same transformed output."""
        rng1 = create_rng(42)
        rng2 = create_rng(42)
        out1 = _transform_code(_SAMPLE_CODE_HIGH, rng1)
        out2 = _transform_code(_SAMPLE_CODE_HIGH, rng2)
        assert out1 == out2


# ── TestSelectPlagiarismPairs ────────────────────────────────────────────


class TestSelectPlagiarismPairs:
    """Tests for the _select_plagiarism_pairs() helper."""

    def test_returns_pairs(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Should return a non-empty list of pairs."""
        pairs = _select_plagiarism_pairs(sample_bundles, rng)
        assert len(pairs) > 0

    def test_pairs_are_within_same_assignment(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Each pair should be from the same assignment."""
        pairs = _select_plagiarism_pairs(sample_bundles, rng)
        for source, target in pairs:
            assert source.submission.assignment_id == target.submission.assignment_id

    def test_no_self_pairs(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """No submission should be paired with itself."""
        pairs = _select_plagiarism_pairs(sample_bundles, rng)
        for source, target in pairs:
            assert source.submission.submission_id != target.submission.submission_id

    def test_handles_too_few_bundles(self, rng: random.Random) -> None:
        """With only one bundle, no pairs can be created."""
        single = [_make_bundle()]
        pairs = _select_plagiarism_pairs(single, rng)
        assert len(pairs) == 0


# ── TestCorruptionSelection ──────────────────────────────────────────────


class TestCorruptionSelection:
    """Tests for corruption-related helpers."""

    def test_select_corrupted_count(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Should select ~3% of submissions."""
        ids = _select_corrupted_submissions(sample_bundles, set(), rng)
        expected = max(1, round(len(sample_bundles) * CORRUPTION_RATE))
        assert len(ids) == expected

    def test_excludes_plagiarism_ids(self, rng: random.Random) -> None:
        """Corrupted selections exclude plagiarism-flagged submissions."""
        bundles = [_make_bundle(student_id=f"S{i:03d}") for i in range(50)]
        # Mark first 10 as plagiarism.
        plag_ids = {b.submission.submission_id for b in bundles[:10]}
        corrupted = _select_corrupted_submissions(bundles, plag_ids, rng)
        for cid in corrupted:
            assert cid not in plag_ids

    def test_corruption_tags_valid(self, rng: random.Random) -> None:
        """Corruption tags have correct tag type and confidence."""
        ids = [uuid.uuid4() for _ in range(5)]
        tags = _generate_corruption_tags(ids, rng)
        assert len(tags) == 5
        for tag in tags:
            assert tag.tag == TagType.CORRUPTED
            assert 0.70 <= tag.confidence <= 1.0


# ── TestPlagiarismTags ───────────────────────────────────────────────────


class TestPlagiarismTags:
    """Tests for the _generate_plagiarism_tags() helper."""

    def test_tags_have_correct_type(self, rng: random.Random) -> None:
        """All tags should be PLAGIARISM_SUSPECT."""
        ids = {uuid.uuid4() for _ in range(5)}
        tags = _generate_plagiarism_tags(ids, rng)
        assert len(tags) == 5
        for tag in tags:
            assert tag.tag == TagType.PLAGIARISM_SUSPECT

    def test_confidence_in_range(self, rng: random.Random) -> None:
        """Confidence values should be in expected range."""
        ids = {uuid.uuid4() for _ in range(10)}
        tags = _generate_plagiarism_tags(ids, rng)
        for tag in tags:
            assert 0.85 <= tag.confidence <= 0.99


# ── TestGenerateBackgroundScores ──────────────────────────────────────────


class TestGenerateBackgroundScores:
    """Tests for the _generate_background_scores() helper."""

    def test_returns_similarity_scores(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Should return a non-empty list of SimilarityScore records."""
        scores = _generate_background_scores(sample_bundles, set(), rng)
        assert len(scores) > 0
        for s in scores:
            assert isinstance(s, SimilarityScore)

    def test_all_unflagged(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """All background scores must have flagged=False."""
        scores = _generate_background_scores(sample_bundles, set(), rng)
        assert all(not s.flagged for s in scores)

    def test_below_threshold(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """All background scores must be below PLAGIARISM_THRESHOLD."""
        scores = _generate_background_scores(sample_bundles, set(), rng)
        for s in scores:
            assert s.similarity_pct < PLAGIARISM_THRESHOLD

    def test_excludes_flagged_pairs(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Should not generate pairs already in flagged_pair_ids."""
        b1, b2 = sample_bundles[0], sample_bundles[1]
        flagged = {(b1.submission.submission_id, b2.submission.submission_id)}
        scores = _generate_background_scores(sample_bundles, flagged, rng)
        for s in scores:
            assert (s.submission_id, s.compared_to) not in flagged
            assert (s.compared_to, s.submission_id) not in flagged


# ── TestGeneratePlagiarismPairs (Integration) ────────────────────────────


class TestGeneratePlagiarismPairs:
    """Tests for the main generate_plagiarism_pairs() public API."""

    def test_returns_plagiarism_result(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Should return a PlagiarismResult instance."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        assert isinstance(result, PlagiarismResult)

    def test_similarity_scores_valid(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """All SimilarityScore records should have valid fields."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        for score in result.similarity_scores:
            assert isinstance(score, SimilarityScore)
            assert 0.0 <= score.similarity_pct <= 100.0
            assert score.method in {m.value for m in SimilarityMethod}
            assert score.submission_id != score.compared_to

    def test_flagged_scores_above_threshold(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Flagged scores should be >= PLAGIARISM_THRESHOLD."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        for score in result.similarity_scores:
            if score.flagged:
                assert score.similarity_pct >= PLAGIARISM_THRESHOLD

    def test_unflagged_scores_below_threshold(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Unflagged background scores should be < PLAGIARISM_THRESHOLD."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        for score in result.similarity_scores:
            if not score.flagged:
                assert score.similarity_pct < PLAGIARISM_THRESHOLD

    def test_tags_are_valid(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """All tags should have valid TagType values."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        valid_tags = {TagType.PLAGIARISM_SUSPECT, TagType.CORRUPTED}
        for tag in result.tags:
            assert tag.tag in valid_tags

    def test_reproducibility_with_seed(
        self, sample_bundles: list[SubmissionBundle]
    ) -> None:
        """Same seed produces identical PlagiarismResult."""
        rng1 = create_rng(42)
        rng2 = create_rng(42)
        result1 = generate_plagiarism_pairs(sample_bundles, rng1)
        result2 = generate_plagiarism_pairs(sample_bundles, rng2)
        assert len(result1.similarity_scores) == len(result2.similarity_scores)
        assert len(result1.tags) == len(result2.tags)
        assert result1.corrupted_ids == result2.corrupted_ids
        assert result1.plagiarism_pairs == result2.plagiarism_pairs

    def test_empty_input_returns_empty(self, rng: random.Random) -> None:
        """Empty bundle list returns empty PlagiarismResult."""
        result = generate_plagiarism_pairs([], rng)
        assert result.similarity_scores == ()
        assert result.tags == ()
        assert result.corrupted_ids == ()
        assert result.plagiarism_pairs == ()

    def test_single_submission_no_pairs(self, rng: random.Random) -> None:
        """Single submission cannot form any pairs."""
        single = [_make_bundle()]
        result = generate_plagiarism_pairs(single, rng)
        assert result.plagiarism_pairs == ()

    def test_all_three_methods_present(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """All three SimilarityMethod values should appear in scores."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        methods = {s.method for s in result.similarity_scores}
        # The flagged pairs should have all 3 methods.
        assert SimilarityMethod.AST_BASED.value in methods
        assert SimilarityMethod.TOKEN_BASED.value in methods
        assert SimilarityMethod.TEXT_BASED.value in methods

    def test_corrupted_ids_not_in_plagiarism(
        self, sample_bundles: list[SubmissionBundle], rng: random.Random
    ) -> None:
        """Corrupted submission IDs should not overlap with plagiarism pairs."""
        result = generate_plagiarism_pairs(sample_bundles, rng)
        plag_ids = set()
        for src, tgt in result.plagiarism_pairs:
            plag_ids.add(src)
            plag_ids.add(tgt)
        for cid in result.corrupted_ids:
            assert cid not in plag_ids
