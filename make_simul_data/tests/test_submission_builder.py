"""Unit tests for ZIP bundle generation and submission assembly.

Tests the build_submission() function, SubmissionBundle dataclass, and
helper functions from make_simul_data.seed_data.submission_builder.

Run with: pytest make_simul_data/tests/test_submission_builder.py -v

Test organization:
    TestSubmissionBundleDataclass  -- Frozen dataclass contract tests.
    TestComputeSubmissionDir       -- Directory path computation.
    TestComputeZipFilename         -- ZIP filename convention.
    TestComputeSha256              -- SHA-256 hash computation.
    TestComputeSubmittedAt         -- Timestamp generation.
    TestBuildSubmissionBasic       -- Core build_submission() behavior.
    TestZipContents                -- ZIP archive contents verification.
    TestZipSizeConstraints         -- ZIP size within expected range.
    TestArtifactRecords            -- SubmissionArtifact correctness.
    TestSubmissionRecord           -- Submission model correctness.
    TestReproducibility            -- Same seed produces identical output.
    TestAllAssignments             -- All 5 assignments build successfully.
    TestDirectoryStructure         -- On-disk directory layout.
    TestEdgeCases                  -- Error handling and boundary conditions.
"""

from __future__ import annotations

import dataclasses
import zipfile
from datetime import timezone

import pytest

from make_simul_data.seed_data.assignments import get_assignment_by_id
from make_simul_data.seed_data.code_generator import (
    GeneratedCodeFile,
    generate_code_files,
)
from make_simul_data.seed_data.config import (
    ASSIGNMENTS_DIR,
    FILE_SIZE_ZIP,
    create_rng,
)
from make_simul_data.seed_data.students import StudentProfile
from make_simul_data.seed_data.submission_builder import (
    MIME_PYTHON,
    MIME_ZIP,
    SubmissionBundle,
    _compute_sha256,
    _compute_sha256_bytes,
    _compute_submission_dir,
    _compute_submitted_at,
    _compute_zip_filename,
    build_submission,
)

# ── Test Constants ───────────────────────────────────────────────────

# Seed for reproducible tests. Matches MASTER_SEED from config.py.
TEST_SEED: int = 42


# ── Test Fixtures ────────────────────────────────────────────────────


def _make_student(
    skill_level: float = 0.7,
    student_id: str = "S001",
    is_late_submitter: bool = False,
) -> StudentProfile:
    """Create a minimal StudentProfile for testing.

    Args:
        skill_level: Override skill level (default 0.7 = medium tier).
        student_id: Override student ID.
        is_late_submitter: Whether the student tends to submit late.

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
        is_late_submitter=is_late_submitter,
        generates_pdf=False,
    )


def _make_code_files(
    assignment_id: str = "HW1",
    skill_level: float = 0.7,
) -> list[GeneratedCodeFile]:
    """Create GeneratedCodeFile instances using actual code generation.

    Uses generate_code_files() with a fixed seed for realistic code
    content and valid size constraints.

    Args:
        assignment_id: Assignment to generate code for.
        skill_level: Student skill level.

    Returns:
        A list of GeneratedCodeFile instances.
    """
    student = _make_student(skill_level=skill_level)
    assignment = get_assignment_by_id(assignment_id)
    rng = create_rng(TEST_SEED)
    return generate_code_files(student, assignment, 1, rng)


# ── Test Classes ─────────────────────────────────────────────────────


class TestSubmissionBundleDataclass:
    """Verify SubmissionBundle is a frozen dataclass with correct fields."""

    def test_is_frozen(self, tmp_path: object) -> None:
        """Assigning to a SubmissionBundle field raises FrozenInstanceError."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        with pytest.raises(dataclasses.FrozenInstanceError):
            bundle.zip_path = "other"  # type: ignore[misc]

    def test_has_required_fields(self, tmp_path: object) -> None:
        """SubmissionBundle has all five required fields."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert hasattr(bundle, "submission")
        assert hasattr(bundle, "artifacts")
        assert hasattr(bundle, "code_files")
        assert hasattr(bundle, "zip_path")
        assert hasattr(bundle, "submission_dir")

    def test_artifacts_is_tuple(self, tmp_path: object) -> None:
        """artifacts field is a tuple (immutable)."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert isinstance(bundle.artifacts, tuple)

    def test_code_files_is_tuple(self, tmp_path: object) -> None:
        """code_files field is a tuple (immutable)."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert isinstance(bundle.code_files, tuple)


class TestComputeSubmissionDir:
    """Verify directory path computation."""

    def test_default_path_structure(self) -> None:
        """Returns a path under ASSIGNMENTS_DIR with HW/student/attempt structure."""
        path = _compute_submission_dir("S001", "HW1", 1)
        expected = ASSIGNMENTS_DIR / "HW1" / "S001" / "attempt1"
        assert path == expected

    def test_custom_output_dir(self, tmp_path: object) -> None:
        """Respects custom output_dir parameter."""
        path = _compute_submission_dir("S042", "HW3", 2, output_dir=tmp_path)
        expected = tmp_path / "HW3" / "S042" / "attempt2"
        assert path == expected

    def test_different_attempt_numbers(self) -> None:
        """Different attempt numbers produce different paths."""
        p1 = _compute_submission_dir("S001", "HW1", 1)
        p2 = _compute_submission_dir("S001", "HW1", 2)
        p3 = _compute_submission_dir("S001", "HW1", 3)
        assert p1 != p2 != p3


class TestComputeZipFilename:
    """Verify ZIP filename convention."""

    def test_filename_format(self) -> None:
        """Returns filename in S001_HW1_attempt1.zip format."""
        name = _compute_zip_filename("S001", "HW1", 1)
        assert name == "S001_HW1_attempt1.zip"

    def test_different_combinations(self) -> None:
        """Various combinations produce correct filenames."""
        assert _compute_zip_filename("S042", "HW3", 2) == "S042_HW3_attempt2.zip"
        assert _compute_zip_filename("S100", "HW5", 3) == "S100_HW5_attempt3.zip"


class TestComputeSha256:
    """Verify SHA-256 hash computation."""

    def test_known_hash(self, tmp_path: object) -> None:
        """SHA256 of known content matches expected value."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("hello world", encoding="utf-8")
        result = _compute_sha256(test_file)
        # Known SHA256 of "hello world"
        expected = "b94d27b9934d3e08a52e52d7da7dabfac484efe3" "7a5380ee9088f7ace2efcde9"
        assert result == expected

    def test_different_content_different_hash(self, tmp_path: object) -> None:
        """Two different files give different hashes."""
        file1 = tmp_path / "a.txt"
        file2 = tmp_path / "b.txt"
        file1.write_text("content a", encoding="utf-8")
        file2.write_text("content b", encoding="utf-8")
        assert _compute_sha256(file1) != _compute_sha256(file2)

    def test_sha256_bytes_matches_file(self, tmp_path: object) -> None:
        """_compute_sha256_bytes matches _compute_sha256 for same data."""
        content = "test content for hashing"
        test_file = tmp_path / "test.txt"
        test_file.write_bytes(content.encode("utf-8"))
        file_hash = _compute_sha256(test_file)
        bytes_hash = _compute_sha256_bytes(content.encode("utf-8"))
        assert file_hash == bytes_hash

    def test_hash_is_64_chars(self, tmp_path: object) -> None:
        """SHA256 hex digest is exactly 64 characters."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("data", encoding="utf-8")
        assert len(_compute_sha256(test_file)) == 64


class TestComputeSubmittedAt:
    """Verify submission timestamp generation."""

    def test_on_time_before_due(self) -> None:
        """On-time submissions have submitted_at <= due_at (23:59 UTC)."""
        from datetime import datetime

        rng = create_rng(TEST_SEED)
        submitted = _compute_submitted_at("2026-02-14", is_late=False, rng=rng)
        due = datetime.fromisoformat("2026-02-14").replace(
            hour=23, minute=59, second=0, tzinfo=timezone.utc
        )
        assert submitted <= due

    def test_late_after_due(self) -> None:
        """Late submissions have submitted_at > due_at."""
        from datetime import datetime

        rng = create_rng(TEST_SEED)
        submitted = _compute_submitted_at("2026-02-14", is_late=True, rng=rng)
        due = datetime.fromisoformat("2026-02-14").replace(
            hour=23, minute=59, second=0, tzinfo=timezone.utc
        )
        assert submitted > due

    def test_timezone_aware(self) -> None:
        """Returned datetime has tzinfo set (UTC-aware)."""
        rng = create_rng(TEST_SEED)
        submitted = _compute_submitted_at("2026-02-14", is_late=False, rng=rng)
        assert submitted.tzinfo is not None


class TestBuildSubmissionBasic:
    """Core build_submission() behavior tests using tmp_path."""

    def test_returns_submission_bundle(self, tmp_path: object) -> None:
        """Return type is SubmissionBundle."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert isinstance(bundle, SubmissionBundle)

    def test_zip_file_exists_on_disk(self, tmp_path: object) -> None:
        """bundle.zip_path.exists() is True."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.zip_path.exists()

    def test_py_files_exist_on_disk(self, tmp_path: object) -> None:
        """Each .py file is written to disk in the submission directory."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        for cf in bundle.code_files:
            py_path = bundle.submission_dir / cf.filename
            assert py_path.exists(), f"{cf.filename} not found on disk"

    def test_submission_dir_exists(self, tmp_path: object) -> None:
        """bundle.submission_dir.is_dir() is True."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.submission_dir.is_dir()


class TestZipContents:
    """Verify ZIP archive contents."""

    def test_zip_contains_code_files(self, tmp_path: object) -> None:
        """All .py filenames are present in the ZIP archive."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        with zipfile.ZipFile(bundle.zip_path, "r") as zf:
            zip_names = zf.namelist()
            for cf in code_files:
                assert cf.filename in zip_names, f"{cf.filename} not in ZIP"

    def test_zip_code_file_content_matches(self, tmp_path: object) -> None:
        """Content inside ZIP matches GeneratedCodeFile.content."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        with zipfile.ZipFile(bundle.zip_path, "r") as zf:
            for cf in code_files:
                zip_content = zf.read(cf.filename).decode("utf-8")
                assert zip_content == cf.content

    def test_zip_contains_padding_files(self, tmp_path: object) -> None:
        """ZIP has more entries than just code files (padding exists)."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        with zipfile.ZipFile(bundle.zip_path, "r") as zf:
            assert len(zf.namelist()) > len(code_files)

    def test_zip_is_valid(self, tmp_path: object) -> None:
        """zipfile.is_zipfile() returns True."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert zipfile.is_zipfile(bundle.zip_path)


class TestZipSizeConstraints:
    """Verify ZIP size falls within expected range."""

    def test_zip_size_reasonable(self, tmp_path: object) -> None:
        """ZIP is at least 50 KB (sanity check — padding is working)."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        zip_size = bundle.zip_path.stat().st_size
        assert zip_size >= 50_000, f"ZIP too small: {zip_size} bytes"

    def test_zip_size_within_range_with_tolerance(self, tmp_path: object) -> None:
        """ZIP size is within FILE_SIZE_ZIP range with 20% tolerance.

        Compression may cause the ZIP to be smaller than the uncompressed
        target, so we allow a 20% lower bound tolerance.
        """
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        zip_size = bundle.zip_path.stat().st_size
        min_zip, max_zip = FILE_SIZE_ZIP
        # Allow 20% tolerance on the lower bound due to compression effects
        # on code text. Random padding bytes are incompressible so most of
        # the size is preserved.
        assert zip_size >= min_zip * 0.8, f"ZIP too small: {zip_size} < {min_zip * 0.8}"
        # Upper bound should not be exceeded since we target within range.
        assert zip_size <= max_zip * 1.1, f"ZIP too large: {zip_size} > {max_zip * 1.1}"


class TestArtifactRecords:
    """Verify SubmissionArtifact records are correct."""

    def test_artifact_count_hw1(self, tmp_path: object) -> None:
        """HW1 (1 code file) produces 2 artifacts: 1 python + 1 zip."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert len(bundle.artifacts) == len(code_files) + 1

    def test_artifact_count_hw4(self, tmp_path: object) -> None:
        """HW4 (2 code files) produces 3 artifacts: 2 python + 1 zip."""
        student = _make_student()
        assignment = get_assignment_by_id("HW4")
        code_files = _make_code_files("HW4")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert len(bundle.artifacts) == len(code_files) + 1

    def test_python_artifact_type(self, tmp_path: object) -> None:
        """Python artifacts have artifact_type 'python_file'."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        python_artifacts = [
            a for a in bundle.artifacts if a.artifact_type == "python_file"
        ]
        assert len(python_artifacts) == len(code_files)

    def test_zip_artifact_type(self, tmp_path: object) -> None:
        """ZIP artifact has artifact_type 'zip_bundle'."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        zip_artifacts = [a for a in bundle.artifacts if a.artifact_type == "zip_bundle"]
        assert len(zip_artifacts) == 1

    def test_artifact_sha256_length(self, tmp_path: object) -> None:
        """All SHA256 hashes are 64-character hex strings."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        for artifact in bundle.artifacts:
            assert len(artifact.sha256) == 64
            assert all(c in "0123456789abcdef" for c in artifact.sha256)

    def test_artifact_size_bytes_positive(self, tmp_path: object) -> None:
        """All artifacts have size_bytes > 0."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        for artifact in bundle.artifacts:
            assert artifact.size_bytes > 0

    def test_artifact_submission_id_matches(self, tmp_path: object) -> None:
        """All artifacts reference the correct submission_id."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        for artifact in bundle.artifacts:
            assert artifact.submission_id == bundle.submission.submission_id

    def test_python_artifact_filetype(self, tmp_path: object) -> None:
        """Python artifacts have MIME type text/x-python."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        python_artifacts = [
            a for a in bundle.artifacts if a.artifact_type == "python_file"
        ]
        for artifact in python_artifacts:
            assert artifact.filetype == MIME_PYTHON

    def test_zip_artifact_filetype(self, tmp_path: object) -> None:
        """ZIP artifact has MIME type application/zip."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        zip_artifacts = [a for a in bundle.artifacts if a.artifact_type == "zip_bundle"]
        assert zip_artifacts[0].filetype == MIME_ZIP


class TestSubmissionRecord:
    """Verify Submission model record correctness."""

    def test_submission_has_uuid(self, tmp_path: object) -> None:
        """submission.submission_id is a valid UUID."""
        import uuid

        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert isinstance(bundle.submission.submission_id, uuid.UUID)

    def test_submission_student_id_matches(self, tmp_path: object) -> None:
        """submission.student_id matches input student."""
        student = _make_student(student_id="S042")
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.submission.student_id == "S042"

    def test_submission_assignment_id_matches(self, tmp_path: object) -> None:
        """submission.assignment_id matches input assignment."""
        student = _make_student()
        assignment = get_assignment_by_id("HW3")
        code_files = _make_code_files("HW3")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.submission.assignment_id == "HW3"

    def test_submission_attempt_no_matches(self, tmp_path: object) -> None:
        """submission.attempt_no matches input attempt_no."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.submission.attempt_no == 1

    def test_submission_status_valid(self, tmp_path: object) -> None:
        """Status is one of SubmissionStatus values."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.submission.status in {"on_time", "late"}

    def test_non_late_student_always_on_time(self, tmp_path: object) -> None:
        """Non-late students always get 'on_time' status."""
        student = _make_student(is_late_submitter=False)
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        # Run multiple times with different seeds to verify consistency
        for seed in range(10):
            rng = create_rng(seed)
            bundle = build_submission(
                student, assignment, 1, code_files, rng, output_dir=tmp_path
            )
            assert bundle.submission.status == "on_time"

    def test_submission_timestamps_timezone_aware(self, tmp_path: object) -> None:
        """Both submitted_at and due_at have UTC timezone."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.submission.submitted_at.tzinfo == timezone.utc
        assert bundle.submission.due_at.tzinfo == timezone.utc


class TestReproducibility:
    """Verify that the same seed produces identical output."""

    def test_same_seed_identical_zip_hash(self, tmp_path: object) -> None:
        """Two builds with same RNG seed produce same ZIP SHA256."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")

        rng1 = create_rng(TEST_SEED)
        bundle1 = build_submission(
            student, assignment, 1, code_files, rng1, output_dir=tmp_path / "run1"
        )

        rng2 = create_rng(TEST_SEED)
        bundle2 = build_submission(
            student, assignment, 1, code_files, rng2, output_dir=tmp_path / "run2"
        )

        # Get ZIP artifact hash from each bundle
        zip_arts1 = [a for a in bundle1.artifacts if a.artifact_type == "zip_bundle"]
        zip_arts2 = [a for a in bundle2.artifacts if a.artifact_type == "zip_bundle"]
        zip_hash1 = zip_arts1[0].sha256
        zip_hash2 = zip_arts2[0].sha256
        assert zip_hash1 == zip_hash2

    def test_different_seed_different_zip_hash(self, tmp_path: object) -> None:
        """Different seeds produce different ZIPs."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")

        rng1 = create_rng(1)
        bundle1 = build_submission(
            student, assignment, 1, code_files, rng1, output_dir=tmp_path / "run1"
        )

        rng2 = create_rng(999)
        bundle2 = build_submission(
            student, assignment, 1, code_files, rng2, output_dir=tmp_path / "run2"
        )

        zip_arts1 = [a for a in bundle1.artifacts if a.artifact_type == "zip_bundle"]
        zip_arts2 = [a for a in bundle2.artifacts if a.artifact_type == "zip_bundle"]
        zip_hash1 = zip_arts1[0].sha256
        zip_hash2 = zip_arts2[0].sha256
        assert zip_hash1 != zip_hash2


class TestAllAssignments:
    """Verify that all 5 assignments build successfully."""

    @pytest.mark.parametrize("hw_id", ["HW1", "HW2", "HW3", "HW4", "HW5"])
    def test_builds_without_error(self, hw_id: str, tmp_path: object) -> None:
        """build_submission runs without error for all assignments."""
        student = _make_student()
        assignment = get_assignment_by_id(hw_id)
        code_files = _make_code_files(hw_id)
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert bundle.zip_path.exists()
        assert len(bundle.artifacts) >= 2  # At least 1 python + 1 zip

    @pytest.mark.parametrize("hw_id", ["HW4", "HW5"])
    def test_two_file_assignments(self, hw_id: str, tmp_path: object) -> None:
        """HW4 and HW5 (2 required files) produce 3 artifacts."""
        student = _make_student()
        assignment = get_assignment_by_id(hw_id)
        code_files = _make_code_files(hw_id)
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert len(bundle.artifacts) == 3  # 2 python + 1 zip


class TestDirectoryStructure:
    """Verify on-disk directory layout."""

    def test_nested_directory_created(self, tmp_path: object) -> None:
        """Path includes HW_ID/STUDENT_ID/attemptN structure."""
        student = _make_student(student_id="S007")
        assignment = get_assignment_by_id("HW2")
        code_files = _make_code_files("HW2")
        rng = create_rng(TEST_SEED)
        bundle = build_submission(
            student, assignment, 1, code_files, rng, output_dir=tmp_path
        )
        assert "HW2" in str(bundle.submission_dir)
        assert "S007" in str(bundle.submission_dir)
        assert "attempt1" in str(bundle.submission_dir)

    def test_multiple_attempts_separate_dirs(self, tmp_path: object) -> None:
        """attempt1 and attempt2 are separate directories."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")

        rng1 = create_rng(TEST_SEED)
        bundle1 = build_submission(
            student, assignment, 1, code_files, rng1, output_dir=tmp_path
        )

        rng2 = create_rng(TEST_SEED + 1)
        bundle2 = build_submission(
            student, assignment, 2, code_files, rng2, output_dir=tmp_path
        )

        assert bundle1.submission_dir != bundle2.submission_dir
        assert bundle1.submission_dir.exists()
        assert bundle2.submission_dir.exists()


class TestEdgeCases:
    """Error handling and boundary conditions."""

    def test_empty_code_files_raises_value_error(self, tmp_path: object) -> None:
        """build_submission raises ValueError for empty code_files."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        with pytest.raises(ValueError, match="code_files must not be empty"):
            build_submission(student, assignment, 1, [], rng, output_dir=tmp_path)

    def test_overwrite_existing_directory(self, tmp_path: object) -> None:
        """Building the same submission twice does not raise (exist_ok=True)."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        code_files = _make_code_files("HW1")

        rng1 = create_rng(TEST_SEED)
        build_submission(student, assignment, 1, code_files, rng1, output_dir=tmp_path)

        rng2 = create_rng(TEST_SEED)
        bundle2 = build_submission(
            student, assignment, 1, code_files, rng2, output_dir=tmp_path
        )
        assert bundle2.zip_path.exists()
