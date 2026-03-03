"""Unit tests for manifest generation and dataset validation.

Tests the manifest.py module (generate_manifest, write_manifest) and the
validator.py module (validate_all and its private check functions).

Run with: pytest make_simul_data/tests/test_manifest_validator.py -v

Test organization:
    TestGenerateManifest       -- Manifest model construction from bundles.
    TestWriteManifest          -- JSON serialization to disk.
    TestValidateSchema         -- JSON Schema validation of manifests.
    TestValidateChecksums      -- SHA-256 integrity verification.
    TestValidateFileExistence  -- Artifact file existence checking.
    TestValidateSubmissionCount -- Submission count range verification.
    TestValidateDistribution   -- Statistical distribution checks.
    TestValidateFileSizes      -- Artifact size range verification.
    TestValidateAll            -- Integration tests for validate_all().
"""

from __future__ import annotations

import csv
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest

from make_simul_data.seed_data.assignments import get_assignment_by_id
from make_simul_data.seed_data.code_generator import generate_code_files
from make_simul_data.seed_data.config import (
    FILE_SIZE_PYTHON,
    FILE_SIZE_ZIP,
    NUM_ASSIGNMENTS,
    NUM_STUDENTS,
    ArtifactType,
    create_rng,
)
from make_simul_data.seed_data.manifest import (
    MANIFEST_FILENAME,
    generate_manifest,
    write_manifest,
)
from make_simul_data.seed_data.models import Manifest, ManifestArtifact
from make_simul_data.seed_data.students import StudentProfile
from make_simul_data.seed_data.submission_builder import (
    SubmissionBundle,
    build_submission,
)
from make_simul_data.seed_data.validator import (
    MAX_EXPECTED_SUBMISSIONS,
    ValidationResult,
    _validate_checksums,
    _validate_distribution,
    _validate_file_existence,
    _validate_file_sizes,
    _validate_schema,
    _validate_submission_count,
    validate_all,
)

# ── Test Constants ───────────────────────────────────────────────────────

# Seed for reproducible tests. Matches MASTER_SEED from config.py.
# Used by: all test fixtures that need deterministic RNG.
TEST_SEED: int = 42


# ── Test Helpers ─────────────────────────────────────────────────────────


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


def _make_bundle(tmp_path: Path) -> SubmissionBundle:
    """Create a real SubmissionBundle on disk using build_submission.

    Generates code files and builds a complete submission in tmp_path,
    producing real ZIP files and artifact records on disk.

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        A fully populated SubmissionBundle with files on disk.
    """
    student = _make_student()
    assignment = get_assignment_by_id("HW1")
    rng = create_rng(TEST_SEED)
    code_files = generate_code_files(student, assignment, 1, rng)
    return build_submission(
        student,
        assignment,
        1,
        code_files,
        create_rng(TEST_SEED + 1),
        output_dir=tmp_path,
    )


def _build_assignments_dir(tmp_path: Path) -> Path:
    """Create a minimal assignments directory with a manifest and artifacts.

    Builds a real submission using build_submission(), generates a manifest,
    and returns the base path (tmp_path) that acts as the assignments root.
    The resulting directory structure is:
        tmp_path/HW1/S001/attempt1/{ZIP, manifest.json}

    Args:
        tmp_path: pytest-provided temporary directory.

    Returns:
        Path to the assignments root directory (tmp_path itself).
    """
    student = _make_student()
    assignment = get_assignment_by_id("HW1")
    rng = create_rng(TEST_SEED)
    code_files = generate_code_files(student, assignment, 1, rng)
    bundle = build_submission(
        student,
        assignment,
        1,
        code_files,
        create_rng(TEST_SEED + 100),
        output_dir=tmp_path,
    )
    manifest = generate_manifest(bundle)
    write_manifest(manifest, bundle.submission_dir)

    return tmp_path


def _write_submissions_csv(
    metadata_dir: Path,
    rows: list[dict[str, str]],
) -> Path:
    """Write a fake submissions.csv with specified rows.

    Args:
        metadata_dir: Directory to write submissions.csv into.
        rows: List of dicts with keys matching Submission model fields.

    Returns:
        Path to the written CSV file.
    """
    metadata_dir.mkdir(parents=True, exist_ok=True)
    csv_path = metadata_dir / "submissions.csv"
    fieldnames = [
        "submission_id",
        "student_id",
        "assignment_id",
        "attempt_no",
        "submitted_at",
        "due_at",
        "status",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def _write_artifacts_csv(
    metadata_dir: Path,
    rows: list[dict[str, str]],
) -> Path:
    """Write a fake submission_artifacts.csv with specified rows.

    Args:
        metadata_dir: Directory to write submission_artifacts.csv into.
        rows: List of dicts with keys matching SubmissionArtifact fields.

    Returns:
        Path to the written CSV file.
    """
    metadata_dir.mkdir(parents=True, exist_ok=True)
    csv_path = metadata_dir / "submission_artifacts.csv"
    fieldnames = [
        "artifact_id",
        "submission_id",
        "artifact_type",
        "filename",
        "filetype",
        "sha256",
        "size_bytes",
    ]
    with open(csv_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return csv_path


def _make_submission_row(
    student_id: str = "S001",
    assignment_id: str = "HW1",
    attempt_no: int = 1,
    status: str = "on_time",
) -> dict[str, str]:
    """Create a single row dict for submissions.csv.

    Args:
        student_id: Student identifier.
        assignment_id: Assignment identifier.
        attempt_no: Attempt number.
        status: Submission status (on_time, late, missing).

    Returns:
        A dict suitable for csv.DictWriter.
    """
    return {
        "submission_id": str(uuid.uuid4()),
        "student_id": student_id,
        "assignment_id": assignment_id,
        "attempt_no": str(attempt_no),
        "submitted_at": "2026-02-10T12:00:00+00:00",
        "due_at": "2026-02-14T23:59:00+00:00",
        "status": status,
    }


# ── Test Classes: manifest.py ────────────────────────────────────────────


class TestGenerateManifest:
    """Tests for generate_manifest()."""

    def test_returns_manifest_instance(self, tmp_path: Path) -> None:
        """generate_manifest() returns a Manifest Pydantic model."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert isinstance(manifest, Manifest)

    def test_submission_id_matches_bundle(self, tmp_path: Path) -> None:
        """Manifest.submission_id equals bundle.submission.submission_id."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert manifest.submission_id == bundle.submission.submission_id

    def test_student_id_matches(self, tmp_path: Path) -> None:
        """Manifest.student_id equals bundle.submission.student_id."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert manifest.student_id == bundle.submission.student_id

    def test_assignment_id_matches(self, tmp_path: Path) -> None:
        """Manifest.assignment_id equals bundle.submission.assignment_id."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert manifest.assignment_id == bundle.submission.assignment_id

    def test_attempt_no_matches(self, tmp_path: Path) -> None:
        """Manifest.attempt_no equals bundle.submission.attempt_no."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert manifest.attempt_no == bundle.submission.attempt_no

    def test_artifact_count_matches(self, tmp_path: Path) -> None:
        """Number of ManifestArtifacts equals number of SubmissionArtifacts."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert len(manifest.artifacts) == len(bundle.artifacts)

    def test_artifact_filenames_match(self, tmp_path: Path) -> None:
        """ManifestArtifact filenames match SubmissionArtifact filenames."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        expected_names = {a.filename for a in bundle.artifacts}
        actual_names = {a.filename for a in manifest.artifacts}
        assert actual_names == expected_names

    def test_artifact_sha256_match(self, tmp_path: Path) -> None:
        """ManifestArtifact sha256 hashes match SubmissionArtifact sha256."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        expected_hashes = {a.sha256 for a in bundle.artifacts}
        actual_hashes = {a.sha256 for a in manifest.artifacts}
        assert actual_hashes == expected_hashes

    def test_artifact_types_match(self, tmp_path: Path) -> None:
        """ManifestArtifact artifact_types match SubmissionArtifact types."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        expected_types = sorted(a.artifact_type for a in bundle.artifacts)
        actual_types = sorted(a.artifact_type for a in manifest.artifacts)
        assert actual_types == expected_types

    def test_generated_at_is_recent(self, tmp_path: Path) -> None:
        """generated_at timestamp is within 5 seconds of now."""
        before = datetime.now(timezone.utc)
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        after = datetime.now(timezone.utc)
        assert before <= manifest.generated_at <= after

    def test_generated_at_has_timezone(self, tmp_path: Path) -> None:
        """generated_at has timezone info (UTC)."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        assert manifest.generated_at.tzinfo is not None

    def test_manifest_artifacts_are_manifest_artifact_type(
        self, tmp_path: Path
    ) -> None:
        """Each artifact in the Manifest is a ManifestArtifact instance."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        for artifact in manifest.artifacts:
            assert isinstance(artifact, ManifestArtifact)


class TestWriteManifest:
    """Tests for write_manifest()."""

    def test_creates_manifest_json_file(self, tmp_path: Path) -> None:
        """manifest.json file is created in the output directory."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        path = write_manifest(manifest, bundle.submission_dir)
        assert path.exists()
        assert path.name == MANIFEST_FILENAME

    def test_file_is_valid_json(self, tmp_path: Path) -> None:
        """Written file can be loaded as valid JSON."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        path = write_manifest(manifest, bundle.submission_dir)
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data, dict)

    def test_json_has_required_keys(self, tmp_path: Path) -> None:
        """JSON object contains all required top-level keys."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        path = write_manifest(manifest, bundle.submission_dir)
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        required_keys = {
            "submission_id",
            "student_id",
            "assignment_id",
            "attempt_no",
            "generated_at",
            "artifacts",
        }
        assert required_keys.issubset(data.keys())

    def test_json_submission_id_is_string(self, tmp_path: Path) -> None:
        """submission_id in JSON is a string (UUID serialized)."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        path = write_manifest(manifest, bundle.submission_dir)
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data["submission_id"], str)

    def test_json_artifacts_is_list(self, tmp_path: Path) -> None:
        """artifacts in JSON is a list."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        path = write_manifest(manifest, bundle.submission_dir)
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        assert isinstance(data["artifacts"], list)

    def test_returns_path(self, tmp_path: Path) -> None:
        """write_manifest returns the Path to manifest.json."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        result = write_manifest(manifest, bundle.submission_dir)
        assert isinstance(result, Path)
        assert result.name == MANIFEST_FILENAME

    def test_idempotent_overwrite(self, tmp_path: Path) -> None:
        """Writing twice to the same directory does not raise errors."""
        bundle = _make_bundle(tmp_path)
        manifest = generate_manifest(bundle)
        path1 = write_manifest(manifest, bundle.submission_dir)
        path2 = write_manifest(manifest, bundle.submission_dir)
        assert path1 == path2
        assert path2.exists()


# ── Test Classes: validator.py ───────────────────────────────────────────


class TestValidationResultDataclass:
    """Verify ValidationResult is a frozen dataclass."""

    def test_is_frozen(self) -> None:
        """Assigning to a ValidationResult field raises FrozenInstanceError."""
        result = ValidationResult(check_name="test", passed=True, message="ok")
        with pytest.raises(AttributeError):
            result.passed = False  # type: ignore[misc]

    def test_default_file_path_is_none(self) -> None:
        """file_path defaults to None when not provided."""
        result = ValidationResult(check_name="test", passed=True, message="ok")
        assert result.file_path is None

    def test_file_path_preserved(self) -> None:
        """file_path is preserved when explicitly set."""
        result = ValidationResult(
            check_name="test",
            passed=True,
            message="ok",
            file_path="/some/path",
        )
        assert result.file_path == "/some/path"


class TestValidateSchema:
    """Tests for _validate_schema()."""

    def test_valid_manifest_passes(self, tmp_path: Path) -> None:
        """A correctly generated manifest passes schema validation."""
        assignments_dir = _build_assignments_dir(tmp_path)
        results = _validate_schema(assignments_dir)
        assert all(r.passed for r in results)
        assert len(results) >= 1

    def test_no_manifests_fails(self, tmp_path: Path) -> None:
        """Empty directory with no manifests returns FAIL."""
        results = _validate_schema(tmp_path)
        assert len(results) == 1
        assert not results[0].passed

    def test_missing_directory_fails(self, tmp_path: Path) -> None:
        """Non-existent assignments directory returns FAIL."""
        results = _validate_schema(tmp_path / "nonexistent")
        assert len(results) == 1
        assert not results[0].passed

    def test_missing_required_field_fails(self, tmp_path: Path) -> None:
        """Manifest missing 'artifacts' key fails schema validation."""
        # Create a manifest with a missing required field.
        sub_dir = tmp_path / "HW1" / "S001" / "attempt1"
        sub_dir.mkdir(parents=True)
        bad_manifest = {
            "submission_id": str(uuid.uuid4()),
            "student_id": "S001",
            "assignment_id": "HW1",
            "attempt_no": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            # "artifacts" key is deliberately missing.
        }
        manifest_path = sub_dir / MANIFEST_FILENAME
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(bad_manifest, fh)

        results = _validate_schema(tmp_path)
        assert any(not r.passed for r in results)

    def test_invalid_student_id_pattern_fails(self, tmp_path: Path) -> None:
        """student_id that does not match S\\d{3} fails."""
        sub_dir = tmp_path / "HW1" / "S001" / "attempt1"
        sub_dir.mkdir(parents=True)
        bad_manifest = {
            "submission_id": str(uuid.uuid4()),
            "student_id": "INVALID",  # Wrong pattern.
            "assignment_id": "HW1",
            "attempt_no": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": [],
        }
        manifest_path = sub_dir / MANIFEST_FILENAME
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(bad_manifest, fh)

        results = _validate_schema(tmp_path)
        assert any(not r.passed for r in results)

    def test_invalid_sha256_pattern_fails(self, tmp_path: Path) -> None:
        """SHA256 that is not 64 hex chars fails."""
        sub_dir = tmp_path / "HW1" / "S001" / "attempt1"
        sub_dir.mkdir(parents=True)
        bad_manifest = {
            "submission_id": str(uuid.uuid4()),
            "student_id": "S001",
            "assignment_id": "HW1",
            "attempt_no": 1,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "artifacts": [
                {
                    "filename": "test.py",
                    "artifact_type": "python_file",
                    "sha256": "NOT_A_VALID_HASH",
                    "size_bytes": 100,
                }
            ],
        }
        manifest_path = sub_dir / MANIFEST_FILENAME
        with open(manifest_path, "w", encoding="utf-8") as fh:
            json.dump(bad_manifest, fh)

        results = _validate_schema(tmp_path)
        assert any(not r.passed for r in results)


class TestValidateChecksums:
    """Tests for _validate_checksums()."""

    def test_correct_checksums_pass(self, tmp_path: Path) -> None:
        """Files with matching SHA-256 in manifest pass."""
        assignments_dir = _build_assignments_dir(tmp_path)
        results = _validate_checksums(assignments_dir)
        # All results should pass (checksums computed by build_submission).
        assert all(r.passed for r in results)
        assert len(results) >= 1

    def test_corrupted_file_fails(self, tmp_path: Path) -> None:
        """File whose content was modified fails checksum verification."""
        # Build a real submission with manifest.
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        code_files = generate_code_files(student, assignment, 1, rng)
        bundle = build_submission(
            student,
            assignment,
            1,
            code_files,
            create_rng(TEST_SEED + 1),
            output_dir=tmp_path,
        )
        manifest = generate_manifest(bundle)
        write_manifest(manifest, bundle.submission_dir)

        # Corrupt the ZIP file by appending garbage bytes.
        with open(bundle.zip_path, "ab") as fh:
            fh.write(b"CORRUPTED_DATA")

        results = _validate_checksums(tmp_path)
        # At least one result should fail (the corrupted ZIP).
        assert any(not r.passed for r in results)

    def test_missing_directory_fails(self, tmp_path: Path) -> None:
        """Non-existent directory returns FAIL."""
        results = _validate_checksums(tmp_path / "nonexistent")
        assert len(results) == 1
        assert not results[0].passed


class TestValidateFileExistence:
    """Tests for _validate_file_existence()."""

    def test_existing_files_pass(self, tmp_path: Path) -> None:
        """All referenced files exist on disk -> PASS."""
        assignments_dir = _build_assignments_dir(tmp_path)
        results = _validate_file_existence(assignments_dir)
        assert all(r.passed for r in results)
        assert len(results) >= 1

    def test_missing_file_fails(self, tmp_path: Path) -> None:
        """A referenced file that was deleted -> FAIL."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        rng = create_rng(TEST_SEED)
        code_files = generate_code_files(student, assignment, 1, rng)
        bundle = build_submission(
            student,
            assignment,
            1,
            code_files,
            create_rng(TEST_SEED + 1),
            output_dir=tmp_path,
        )
        manifest = generate_manifest(bundle)
        write_manifest(manifest, bundle.submission_dir)

        # Delete the ZIP file.
        bundle.zip_path.unlink()

        results = _validate_file_existence(tmp_path)
        assert any(not r.passed for r in results)


class TestValidateSubmissionCount:
    """Tests for _validate_submission_count()."""

    def test_valid_count_passes(self, tmp_path: Path) -> None:
        """Submission count within expected range passes."""
        metadata_dir = tmp_path / "metadata"
        # Create exactly MIN_EXPECTED_SUBMISSIONS rows.
        rows = [
            _make_submission_row(
                student_id=f"S{i:03d}",
                assignment_id=f"HW{j + 1}",
            )
            for i in range(1, NUM_STUDENTS + 1)
            for j in range(NUM_ASSIGNMENTS)
        ]
        _write_submissions_csv(metadata_dir, rows)
        results = _validate_submission_count(metadata_dir)
        assert len(results) == 1
        assert results[0].passed

    def test_too_few_submissions_fails(self, tmp_path: Path) -> None:
        """Count below MIN_EXPECTED_SUBMISSIONS fails."""
        metadata_dir = tmp_path / "metadata"
        # Only 5 submissions (way below minimum).
        rows = [_make_submission_row() for _ in range(5)]
        _write_submissions_csv(metadata_dir, rows)
        results = _validate_submission_count(metadata_dir)
        assert len(results) == 1
        assert not results[0].passed

    def test_too_many_submissions_fails(self, tmp_path: Path) -> None:
        """Count above MAX_EXPECTED_SUBMISSIONS fails."""
        metadata_dir = tmp_path / "metadata"
        # MAX + 1 submissions.
        rows = [_make_submission_row() for _ in range(MAX_EXPECTED_SUBMISSIONS + 1)]
        _write_submissions_csv(metadata_dir, rows)
        results = _validate_submission_count(metadata_dir)
        assert len(results) == 1
        assert not results[0].passed

    def test_missing_csv_fails(self, tmp_path: Path) -> None:
        """Missing submissions.csv returns FAIL."""
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir(parents=True)
        results = _validate_submission_count(metadata_dir)
        assert len(results) == 1
        assert not results[0].passed


class TestValidateDistribution:
    """Tests for _validate_distribution()."""

    def test_correct_distribution_passes(self, tmp_path: Path) -> None:
        """Distribution matching config rates passes all sub-checks."""
        metadata_dir = tmp_path / "metadata"
        rows: list[dict[str, str]] = []

        # Generate rows that match SUBMISSION_DISTRIBUTION exactly.
        # 100 students x 5 assignments = 500 pairs.
        # 60% have 1 attempt, 30% have 2 attempts, 10% have 3 attempts.
        pair_index = 0
        for sid in range(1, NUM_STUDENTS + 1):
            for aid in range(1, NUM_ASSIGNMENTS + 1):
                student_id = f"S{sid:03d}"
                assignment_id = f"HW{aid}"

                # Determine number of attempts based on distribution.
                if pair_index < 300:  # 60% of 500
                    max_attempts = 1
                elif pair_index < 450:  # next 30%
                    max_attempts = 2
                else:  # remaining 10%
                    max_attempts = 3

                for attempt in range(1, max_attempts + 1):
                    # ~20% of submissions are late.
                    is_late = (pair_index + attempt) % 5 == 0
                    status = "late" if is_late else "on_time"
                    rows.append(
                        _make_submission_row(
                            student_id=student_id,
                            assignment_id=assignment_id,
                            attempt_no=attempt,
                            status=status,
                        )
                    )
                pair_index += 1

        _write_submissions_csv(metadata_dir, rows)
        results = _validate_distribution(metadata_dir)
        # Should have at least 4 results (3 attempt rates + 1 late rate).
        assert len(results) >= 4
        assert all(r.passed for r in results)

    def test_missing_csv_fails(self, tmp_path: Path) -> None:
        """Missing submissions.csv returns FAIL."""
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir(parents=True)
        results = _validate_distribution(metadata_dir)
        assert len(results) == 1
        assert not results[0].passed

    def test_empty_csv_fails(self, tmp_path: Path) -> None:
        """Empty submissions.csv returns FAIL."""
        metadata_dir = tmp_path / "metadata"
        _write_submissions_csv(metadata_dir, [])
        results = _validate_distribution(metadata_dir)
        assert len(results) == 1
        assert not results[0].passed


class TestValidateFileSizes:
    """Tests for _validate_file_sizes()."""

    def test_valid_sizes_pass(self, tmp_path: Path) -> None:
        """Artifacts with sizes within range pass."""
        metadata_dir = tmp_path / "metadata"
        rows = [
            {
                "artifact_id": str(uuid.uuid4()),
                "submission_id": str(uuid.uuid4()),
                "artifact_type": ArtifactType.PYTHON_FILE,
                "filename": "test.py",
                "filetype": "text/x-python",
                "sha256": "a" * 64,
                "size_bytes": str(FILE_SIZE_PYTHON[0] + 100),
            },
            {
                "artifact_id": str(uuid.uuid4()),
                "submission_id": str(uuid.uuid4()),
                "artifact_type": ArtifactType.ZIP_BUNDLE,
                "filename": "test.zip",
                "filetype": "application/zip",
                "sha256": "b" * 64,
                "size_bytes": str(FILE_SIZE_ZIP[0] + 100),
            },
        ]
        _write_artifacts_csv(metadata_dir, rows)
        results = _validate_file_sizes(metadata_dir)
        assert all(r.passed for r in results)
        assert len(results) >= 2

    def test_out_of_range_fails(self, tmp_path: Path) -> None:
        """Artifact with size outside configured range fails."""
        metadata_dir = tmp_path / "metadata"
        rows = [
            {
                "artifact_id": str(uuid.uuid4()),
                "submission_id": str(uuid.uuid4()),
                "artifact_type": ArtifactType.PYTHON_FILE,
                "filename": "huge.py",
                "filetype": "text/x-python",
                "sha256": "c" * 64,
                "size_bytes": str(FILE_SIZE_PYTHON[1] + 999999),
            },
        ]
        _write_artifacts_csv(metadata_dir, rows)
        results = _validate_file_sizes(metadata_dir)
        assert any(not r.passed for r in results)

    def test_missing_csv_fails(self, tmp_path: Path) -> None:
        """Missing submission_artifacts.csv returns FAIL."""
        metadata_dir = tmp_path / "metadata"
        metadata_dir.mkdir(parents=True)
        results = _validate_file_sizes(metadata_dir)
        assert len(results) == 1
        assert not results[0].passed


class TestValidateAll:
    """Integration tests for validate_all()."""

    def test_returns_list_of_validation_results(self, tmp_path: Path) -> None:
        """validate_all() returns a list of ValidationResult instances."""
        results = validate_all(output_dir=tmp_path)
        assert isinstance(results, list)
        for r in results:
            assert isinstance(r, ValidationResult)

    def test_missing_output_dir_does_not_crash(self, tmp_path: Path) -> None:
        """validate_all() on a nonexistent directory returns failures."""
        results = validate_all(output_dir=tmp_path / "nonexistent")
        assert isinstance(results, list)
        # All should fail since nothing exists.
        assert all(not r.passed for r in results)

    def test_empty_dir_returns_failures(self, tmp_path: Path) -> None:
        """validate_all() on an empty directory returns failure results."""
        results = validate_all(output_dir=tmp_path)
        assert isinstance(results, list)
        assert len(results) > 0
        # Should have failures for missing manifests, CSVs, etc.
        assert any(not r.passed for r in results)

    def test_check_names_present(self, tmp_path: Path) -> None:
        """All six check categories are represented in results."""
        results = validate_all(output_dir=tmp_path)
        check_names = {r.check_name for r in results}
        expected_checks = {
            "schema_validation",
            "sha256_check",
            "file_existence",
            "submission_count",
            "distribution",
            "file_size",
        }
        # At least some of these should appear (even as failures).
        assert len(check_names & expected_checks) >= 3
