"""Quality-assurance validation for the generated seed data.

Runs six categories of checks against the output directory to verify
data integrity, structural correctness, and statistical plausibility:

    1. Schema validation     -- manifest.json conforms to JSON Schema
    2. SHA-256 checksums     -- file hashes match manifest records
    3. File existence        -- every manifest-referenced file is on disk
    4. Submission count      -- total submissions within expected range
    5. Distribution checks   -- attempt counts and late rate match config
    6. File size ranges      -- artifact sizes within configured bounds

Key exports:
    ValidationResult  -- Frozen dataclass for individual check outcomes.
    validate_all      -- Run all checks and return aggregated results.

Module dependency graph:
    config.py     -->  validator.py  (OUTPUT_ROOT, METADATA_DIR, ASSIGNMENTS_DIR,
                                      FILE_SIZE_*, NUM_*, SUBMISSION_DISTRIBUTION,
                                      LATE_RATE, ArtifactType)
    manifest.py   -->  validator.py  (MANIFEST_FILENAME for file discovery)

Consumed by:
    generate_data.py  (Step 10, final QA gate after full pipeline execution)
"""

from __future__ import annotations

import csv
import hashlib
import json
import logging
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import jsonschema

from make_simul_data.seed_data.config import (
    ASSIGNMENTS_DIR,
    FILE_SIZE_PDF,
    FILE_SIZE_PYTHON,
    FILE_SIZE_ZIP,
    LATE_RATE,
    METADATA_DIR,
    NUM_ASSIGNMENTS,
    NUM_STUDENTS,
    OUTPUT_ROOT,
    SUBMISSION_DISTRIBUTION,
    ArtifactType,
)
from make_simul_data.seed_data.manifest import MANIFEST_FILENAME

# ── Module Logger ────────────────────────────────────────────────────────

# Logger for validator diagnostics. Uses the module's dotted name so that
# callers can control verbosity via standard logging configuration.
# Used by: every _validate_* function to log progress and issues.
logger: logging.Logger = logging.getLogger(__name__)

# ── Constants ────────────────────────────────────────────────────────────

# Fractional tolerance for statistical distribution checks.
# When verifying that the generated dataset matches expected distributions
# (attempt-count ratios, late-submission rate), the actual value is
# compared against the expected value +/- (expected * DISTRIBUTION_TOLERANCE).
# A value of 0.15 means 15% relative tolerance, which accommodates
# natural stochastic variation from seeded random generation while
# still catching implementation bugs that produce wildly wrong rates.
# Used by: _validate_distribution() in this module.
DISTRIBUTION_TOLERANCE: float = 0.15

# Minimum total number of submissions expected in the dataset.
# Equals NUM_STUDENTS * NUM_ASSIGNMENTS because every student submits
# at least once for every assignment (attempt count >= 1).
# Used by: _validate_submission_count() in this module.
MIN_EXPECTED_SUBMISSIONS: int = NUM_STUDENTS * NUM_ASSIGNMENTS

# Maximum total number of submissions expected in the dataset.
# Equals NUM_STUDENTS * NUM_ASSIGNMENTS * 3 because the maximum
# configured attempt count is 3 (see SUBMISSION_DISTRIBUTION keys).
# Used by: _validate_submission_count() in this module.
MAX_EXPECTED_SUBMISSIONS: int = NUM_STUDENTS * NUM_ASSIGNMENTS * 3

# Relative subdirectory path from OUTPUT_ROOT to the assignments folder.
# Derived from ASSIGNMENTS_DIR to stay in sync with config.py.
# Used by: validate_all() to locate manifest files under a custom output_dir.
_ASSIGNMENTS_REL: Path = ASSIGNMENTS_DIR.relative_to(OUTPUT_ROOT)

# Relative subdirectory path from OUTPUT_ROOT to the metadata folder.
# Derived from METADATA_DIR to stay in sync with config.py.
# Used by: validate_all() to locate CSV files under a custom output_dir.
_METADATA_REL: Path = METADATA_DIR.relative_to(OUTPUT_ROOT)

# JSON Schema definition for manifest.json structural validation.
# Defines required fields, value types, regex patterns, and numeric
# ranges that every valid manifest must satisfy.  Validated using the
# ``jsonschema`` library.
# Used by: _validate_schema() in this module.
MANIFEST_SCHEMA: dict = {
    "type": "object",
    "required": [
        "submission_id",
        "student_id",
        "assignment_id",
        "attempt_no",
        "generated_at",
        "artifacts",
    ],
    "properties": {
        "submission_id": {
            "type": "string",
            "description": "UUID v4 string identifying the submission.",
        },
        "student_id": {
            "type": "string",
            "pattern": r"^S\d{3}$",
            "description": "Student ID in format S001-S999.",
        },
        "assignment_id": {
            "type": "string",
            "pattern": r"^HW\d$",
            "description": "Assignment ID in format HW1-HW9.",
        },
        "attempt_no": {
            "type": "integer",
            "minimum": 1,
            "maximum": 3,
            "description": "Attempt number (1, 2, or 3).",
        },
        "generated_at": {
            "type": "string",
            "description": "ISO 8601 UTC timestamp of manifest generation.",
        },
        "artifacts": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "filename",
                    "artifact_type",
                    "sha256",
                    "size_bytes",
                ],
                "properties": {
                    "filename": {
                        "type": "string",
                        "description": "Artifact filename on disk.",
                    },
                    "artifact_type": {
                        "type": "string",
                        "enum": [e.value for e in ArtifactType],
                        "description": "Type of artifact from ArtifactType enum.",
                    },
                    "sha256": {
                        "type": "string",
                        "pattern": r"^[0-9a-f]{64}$",
                        "description": "SHA-256 hex digest (64 lowercase hex chars).",
                    },
                    "size_bytes": {
                        "type": "integer",
                        "minimum": 0,
                        "description": "File size in bytes.",
                    },
                },
            },
        },
    },
}

# Mapping from ArtifactType values to their expected file size ranges.
# Each value is a (min_bytes, max_bytes) tuple from config.py.
# Used by: _validate_file_sizes() to check that each artifact's
#          recorded size_bytes falls within the expected range.
_ARTIFACT_SIZE_RANGES: dict[str, tuple[int, int]] = {
    ArtifactType.PYTHON_FILE: FILE_SIZE_PYTHON,
    ArtifactType.ZIP_BUNDLE: FILE_SIZE_ZIP,
    ArtifactType.PDF_REPORT: FILE_SIZE_PDF,
}


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of a single validation check.

    Each validation function (_validate_schema, _validate_checksums, etc.)
    produces one or more ValidationResult instances.  These are collected
    by validate_all() and returned to the caller for reporting and
    pass/fail determination.

    Created by: _validate_* functions in this module.
    Consumed by: validate_all() (aggregation), generate_data.py (Step 10,
                 QA reporting and CI/CD gate).

    Attributes:
        check_name: Short identifier for the validation category that
                    produced this result.  One of: "schema_validation",
                    "sha256_check", "file_existence", "submission_count",
                    "distribution", "file_size".
        passed:     True if this specific check passed, False if it failed.
        message:    Human-readable description of the outcome.  For passes,
                    summarizes what was verified.  For failures, explains
                    what went wrong with relevant values.
        file_path:  Optional absolute path to the file that was validated.
                    None for aggregate checks (submission_count,
                    distribution) that operate on CSV data rather than
                    individual files.
    """

    check_name: str
    passed: bool
    message: str
    file_path: str | None = None


# ── Private Validation Functions ─────────────────────────────────────────


def _validate_schema(assignments_dir: Path) -> list[ValidationResult]:
    """Validate every manifest.json against the MANIFEST_SCHEMA.

    Recursively finds all manifest.json files under the assignments
    directory and validates each one against the JSON Schema defined
    in MANIFEST_SCHEMA.  This ensures that all manifests have the
    correct structure, required fields, and valid value formats.

    Used by: validate_all() as the first validation check.

    Args:
        assignments_dir: Path to the assignments directory
                         (e.g., output/seed_data/intro_cs/Assignments/).

    Returns:
        List of ValidationResult instances, one per manifest file found.
        If no manifests are found, returns a single FAIL result.
    """
    results: list[ValidationResult] = []

    if not assignments_dir.exists():
        return [
            ValidationResult(
                check_name="schema_validation",
                passed=False,
                message=f"Assignments directory not found: {assignments_dir}",
            )
        ]

    manifest_paths: list[Path] = sorted(assignments_dir.rglob(MANIFEST_FILENAME))

    if not manifest_paths:
        return [
            ValidationResult(
                check_name="schema_validation",
                passed=False,
                message="No manifest.json files found under assignments directory.",
            )
        ]

    for manifest_path in manifest_paths:
        try:
            with open(manifest_path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            jsonschema.validate(instance=data, schema=MANIFEST_SCHEMA)
            results.append(
                ValidationResult(
                    check_name="schema_validation",
                    passed=True,
                    message=f"Schema valid: {manifest_path.name}",
                    file_path=str(manifest_path),
                )
            )
        except json.JSONDecodeError as exc:
            results.append(
                ValidationResult(
                    check_name="schema_validation",
                    passed=False,
                    message=f"Invalid JSON: {exc}",
                    file_path=str(manifest_path),
                )
            )
        except jsonschema.ValidationError as exc:
            results.append(
                ValidationResult(
                    check_name="schema_validation",
                    passed=False,
                    message=f"Schema error: {exc.message}",
                    file_path=str(manifest_path),
                )
            )

    logger.info("Schema validation: checked %d manifest(s).", len(manifest_paths))
    return results


def _validate_checksums(assignments_dir: Path) -> list[ValidationResult]:
    """Verify SHA-256 checksums of all artifacts listed in manifests.

    For each artifact entry in every manifest.json, computes the actual
    SHA-256 hash of the file on disk and compares it against the hash
    recorded in the manifest.  This detects file corruption or accidental
    modification after generation.

    Used by: validate_all() as the second validation check.

    Args:
        assignments_dir: Path to the assignments directory.

    Returns:
        List of ValidationResult instances, one per artifact checked.
        Skips artifacts whose files do not exist (file existence is
        checked separately by _validate_file_existence).
    """
    results: list[ValidationResult] = []

    if not assignments_dir.exists():
        return [
            ValidationResult(
                check_name="sha256_check",
                passed=False,
                message=f"Assignments directory not found: {assignments_dir}",
            )
        ]

    for manifest_path in sorted(assignments_dir.rglob(MANIFEST_FILENAME)):
        manifest_dir: Path = manifest_path.parent

        with open(manifest_path, "r", encoding="utf-8") as fh:
            data: dict = json.load(fh)

        for artifact in data.get("artifacts", []):
            filename: str = artifact["filename"]
            expected_sha: str = artifact["sha256"]
            file_path: Path = manifest_dir / filename

            # Skip missing files; existence is checked by _validate_file_existence.
            if not file_path.exists():
                continue

            # Compute actual SHA-256 in 8 KB chunks for memory efficiency.
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as fp:
                while chunk := fp.read(8192):
                    sha256_hash.update(chunk)
            actual_sha: str = sha256_hash.hexdigest()

            if actual_sha == expected_sha:
                results.append(
                    ValidationResult(
                        check_name="sha256_check",
                        passed=True,
                        message=f"SHA-256 match: {filename}",
                        file_path=str(file_path),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="sha256_check",
                        passed=False,
                        message=(
                            f"SHA-256 mismatch for {filename}: "
                            f"expected={expected_sha}, actual={actual_sha}"
                        ),
                        file_path=str(file_path),
                    )
                )

    logger.info("Checksum validation: checked %d artifact(s).", len(results))
    return results


def _validate_file_existence(assignments_dir: Path) -> list[ValidationResult]:
    """Check that every artifact referenced in manifests exists on disk.

    Iterates over all manifest.json files and verifies that each listed
    artifact filename can be found in the same directory as the manifest.

    Used by: validate_all() as the third validation check.

    Args:
        assignments_dir: Path to the assignments directory.

    Returns:
        List of ValidationResult instances, one per artifact checked.
    """
    results: list[ValidationResult] = []

    if not assignments_dir.exists():
        return [
            ValidationResult(
                check_name="file_existence",
                passed=False,
                message=f"Assignments directory not found: {assignments_dir}",
            )
        ]

    for manifest_path in sorted(assignments_dir.rglob(MANIFEST_FILENAME)):
        manifest_dir: Path = manifest_path.parent

        with open(manifest_path, "r", encoding="utf-8") as fh:
            data: dict = json.load(fh)

        for artifact in data.get("artifacts", []):
            filename: str = artifact["filename"]
            file_path: Path = manifest_dir / filename

            if file_path.exists():
                results.append(
                    ValidationResult(
                        check_name="file_existence",
                        passed=True,
                        message=f"File exists: {filename}",
                        file_path=str(file_path),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="file_existence",
                        passed=False,
                        message=f"File missing: {filename}",
                        file_path=str(file_path),
                    )
                )

    logger.info("File existence check: checked %d artifact(s).", len(results))
    return results


def _validate_submission_count(metadata_dir: Path) -> list[ValidationResult]:
    """Verify that the total submission count is within expected range.

    Reads metadata/submissions.csv and checks that the row count falls
    between MIN_EXPECTED_SUBMISSIONS and MAX_EXPECTED_SUBMISSIONS.

    Used by: validate_all() as the fourth validation check.

    Args:
        metadata_dir: Path to the metadata directory containing
                      submissions.csv.

    Returns:
        A single-element list with PASS or FAIL.
    """
    csv_path: Path = metadata_dir / "submissions.csv"

    if not csv_path.exists():
        return [
            ValidationResult(
                check_name="submission_count",
                passed=False,
                message=f"File not found: {csv_path}",
            )
        ]

    with open(csv_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        row_count: int = sum(1 for _ in reader)

    if MIN_EXPECTED_SUBMISSIONS <= row_count <= MAX_EXPECTED_SUBMISSIONS:
        return [
            ValidationResult(
                check_name="submission_count",
                passed=True,
                message=(
                    f"Submission count {row_count} is within expected range "
                    f"[{MIN_EXPECTED_SUBMISSIONS}, {MAX_EXPECTED_SUBMISSIONS}]."
                ),
            )
        ]
    else:
        return [
            ValidationResult(
                check_name="submission_count",
                passed=False,
                message=(
                    f"Submission count {row_count} is outside expected range "
                    f"[{MIN_EXPECTED_SUBMISSIONS}, {MAX_EXPECTED_SUBMISSIONS}]."
                ),
            )
        ]


def _validate_distribution(metadata_dir: Path) -> list[ValidationResult]:
    """Verify that attempt-count and late-rate distributions match config.

    Reads metadata/submissions.csv and checks two distributions:
      1. The fraction of student-assignment pairs with 1, 2, or 3 attempts
         should match SUBMISSION_DISTRIBUTION within +/- DISTRIBUTION_TOLERANCE.
      2. The fraction of "late" submissions should match LATE_RATE within
         +/- DISTRIBUTION_TOLERANCE.

    Used by: validate_all() as the fifth validation check.

    Args:
        metadata_dir: Path to the metadata directory containing
                      submissions.csv.

    Returns:
        List of ValidationResult instances (one per sub-check).
    """
    results: list[ValidationResult] = []
    csv_path: Path = metadata_dir / "submissions.csv"

    if not csv_path.exists():
        return [
            ValidationResult(
                check_name="distribution",
                passed=False,
                message=f"File not found: {csv_path}",
            )
        ]

    # Read all submissions from CSV.
    rows: list[dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if not rows:
        return [
            ValidationResult(
                check_name="distribution",
                passed=False,
                message="submissions.csv is empty.",
            )
        ]

    # --- Check 1: Attempt-count distribution ---
    # Count max attempt per student-assignment pair to determine how many
    # pairs have 1, 2, or 3 total attempts.
    pair_max_attempt: dict[tuple[str, str], int] = {}
    for row in rows:
        key = (row["student_id"], row["assignment_id"])
        attempt = int(row["attempt_no"])
        if key not in pair_max_attempt or attempt > pair_max_attempt[key]:
            pair_max_attempt[key] = attempt

    total_pairs: int = len(pair_max_attempt)
    if total_pairs > 0:
        for num_attempts, expected_rate in SUBMISSION_DISTRIBUTION.items():
            actual_count: int = sum(
                1 for v in pair_max_attempt.values() if v == num_attempts
            )
            actual_rate: float = actual_count / total_pairs
            lower: float = expected_rate * (1 - DISTRIBUTION_TOLERANCE)
            upper: float = expected_rate * (1 + DISTRIBUTION_TOLERANCE)

            if lower <= actual_rate <= upper:
                results.append(
                    ValidationResult(
                        check_name="distribution",
                        passed=True,
                        message=(
                            f"Attempt-count={num_attempts} rate {actual_rate:.3f} "
                            f"is within [{lower:.3f}, {upper:.3f}] "
                            f"(expected {expected_rate:.2f})."
                        ),
                    )
                )
            else:
                results.append(
                    ValidationResult(
                        check_name="distribution",
                        passed=False,
                        message=(
                            f"Attempt-count={num_attempts} rate {actual_rate:.3f} "
                            f"is outside [{lower:.3f}, {upper:.3f}] "
                            f"(expected {expected_rate:.2f})."
                        ),
                    )
                )

    # --- Check 2: Late-submission rate ---
    total_rows: int = len(rows)
    late_count: int = sum(1 for row in rows if row["status"] == "late")
    actual_late_rate: float = late_count / total_rows if total_rows > 0 else 0.0
    late_lower: float = LATE_RATE * (1 - DISTRIBUTION_TOLERANCE)
    late_upper: float = LATE_RATE * (1 + DISTRIBUTION_TOLERANCE)

    if late_lower <= actual_late_rate <= late_upper:
        results.append(
            ValidationResult(
                check_name="distribution",
                passed=True,
                message=(
                    f"Late rate {actual_late_rate:.3f} is within "
                    f"[{late_lower:.3f}, {late_upper:.3f}] "
                    f"(expected {LATE_RATE:.2f})."
                ),
            )
        )
    else:
        results.append(
            ValidationResult(
                check_name="distribution",
                passed=False,
                message=(
                    f"Late rate {actual_late_rate:.3f} is outside "
                    f"[{late_lower:.3f}, {late_upper:.3f}] "
                    f"(expected {LATE_RATE:.2f})."
                ),
            )
        )

    logger.info("Distribution validation: %d sub-checks completed.", len(results))
    return results


def _validate_file_sizes(metadata_dir: Path) -> list[ValidationResult]:
    """Verify that artifact file sizes fall within configured ranges.

    Reads metadata/submission_artifacts.csv and checks that each
    artifact's size_bytes field falls within the expected range for
    its artifact_type (python_file, zip_bundle, pdf_report).
    OCR images are skipped as their sizes are not constrained by config.

    Used by: validate_all() as the sixth validation check.

    Args:
        metadata_dir: Path to the metadata directory containing
                      submission_artifacts.csv.

    Returns:
        List of ValidationResult instances, one per artifact type checked.
        Reports aggregate pass/fail per artifact type rather than per row,
        to keep output concise.
    """
    results: list[ValidationResult] = []
    csv_path: Path = metadata_dir / "submission_artifacts.csv"

    if not csv_path.exists():
        return [
            ValidationResult(
                check_name="file_size",
                passed=False,
                message=f"File not found: {csv_path}",
            )
        ]

    # Read all artifact rows.
    rows: list[dict[str, str]] = []
    with open(csv_path, "r", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)

    if not rows:
        return [
            ValidationResult(
                check_name="file_size",
                passed=False,
                message="submission_artifacts.csv is empty.",
            )
        ]

    # Check each artifact type that has a configured size range.
    for artifact_type, (min_size, max_size) in _ARTIFACT_SIZE_RANGES.items():
        type_rows: list[dict[str, str]] = [
            r for r in rows if r["artifact_type"] == artifact_type
        ]

        if not type_rows:
            # No artifacts of this type; skip (not necessarily an error,
            # e.g., PDF reports may not exist for all submissions).
            continue

        violations: list[str] = []
        for row in type_rows:
            size: int = int(row["size_bytes"])
            if not (min_size <= size <= max_size):
                violations.append(
                    f"{row.get('filename', 'unknown')}: "
                    f"{size} bytes (range: {min_size}-{max_size})"
                )

        if not violations:
            results.append(
                ValidationResult(
                    check_name="file_size",
                    passed=True,
                    message=(
                        f"All {len(type_rows)} '{artifact_type}' artifacts "
                        f"within [{min_size}, {max_size}] bytes."
                    ),
                )
            )
        else:
            results.append(
                ValidationResult(
                    check_name="file_size",
                    passed=False,
                    message=(
                        f"{len(violations)} of {len(type_rows)} "
                        f"'{artifact_type}' artifacts out of range: "
                        + "; ".join(violations[:5])
                        + ("..." if len(violations) > 5 else "")
                    ),
                )
            )

    logger.info("File size validation: checked %d artifact type(s).", len(results))
    return results


# ── Public API ───────────────────────────────────────────────────────────


def validate_all(output_dir: Path | None = None) -> list[ValidationResult]:
    """Run all QA validation checks on the generated seed data.

    This is the main public entry point for Step 9 validation.  It runs
    all six validation categories and returns the combined results.
    Designed to be called after the full generation pipeline has finished
    writing all files to disk.

    Each validation function is wrapped in a try/except to ensure that
    a failure in one check does not prevent the remaining checks from
    executing.  If a check raises an unexpected exception, a FAIL result
    is recorded with the exception message.

    Validation checks performed (in order):
        1. Schema validation      -- manifest.json structure
        2. SHA-256 checksum       -- file integrity
        3. File existence         -- all referenced files present
        4. Submission count       -- total within expected range
        5. Distribution           -- attempt counts, late rate
        6. File size ranges       -- artifact sizes within bounds

    Used by: generate_data.py (Step 10 -- final QA gate after generation)

    Args:
        output_dir: Root directory of the generated dataset.  If None,
                    defaults to OUTPUT_ROOT from config.py.  Must contain
                    "intro_cs/Assignments/" and "metadata/" subdirectories.

    Returns:
        A list of ValidationResult instances, one per individual check.
        Use ``all(r.passed for r in results)`` to determine overall
        pass/fail status.

    Example::

        results = validate_all()
        passed = sum(1 for r in results if r.passed)
        failed = sum(1 for r in results if not r.passed)
        print(f"QA: {passed} passed, {failed} failed")
    """
    if output_dir is None:
        output_dir = OUTPUT_ROOT

    # Resolve the two key subdirectories using relative paths derived
    # from ASSIGNMENTS_DIR and METADATA_DIR in config.py.
    assignments_dir: Path = output_dir / _ASSIGNMENTS_REL
    metadata_dir: Path = output_dir / _METADATA_REL

    all_results: list[ValidationResult] = []

    # Ordered list of (check_name, callable) pairs.
    # Each callable returns a list of ValidationResult instances.
    checks: list[tuple[str, Callable[[], list[ValidationResult]]]] = [
        ("schema_validation", lambda: _validate_schema(assignments_dir)),
        ("sha256_check", lambda: _validate_checksums(assignments_dir)),
        ("file_existence", lambda: _validate_file_existence(assignments_dir)),
        ("submission_count", lambda: _validate_submission_count(metadata_dir)),
        ("distribution", lambda: _validate_distribution(metadata_dir)),
        ("file_size", lambda: _validate_file_sizes(metadata_dir)),
    ]

    for check_name, check_fn in checks:
        try:
            check_results: list[ValidationResult] = check_fn()
            all_results.extend(check_results)
        except Exception as exc:
            # Catch unexpected errors so that one failing check does
            # not prevent the remaining checks from running.
            logger.exception("Unexpected error in %s check.", check_name)
            all_results.append(
                ValidationResult(
                    check_name=check_name,
                    passed=False,
                    message=f"Unexpected error: {exc}",
                )
            )

    # Log summary.
    passed_count: int = sum(1 for r in all_results if r.passed)
    failed_count: int = sum(1 for r in all_results if not r.passed)
    logger.info(
        "Validation complete: %d passed, %d failed out of %d checks.",
        passed_count,
        failed_count,
        len(all_results),
    )

    return all_results
