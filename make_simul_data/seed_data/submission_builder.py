"""ZIP bundle generation and submission assembly for the seed data pipeline.

This module packages generated Python code files into ZIP bundles, creates
the on-disk directory structure for each submission attempt, and assembles
Submission and SubmissionArtifact Pydantic model records. Each ZIP contains
the student's .py source files plus deterministic padding data to reach the
target file size range (100-300 KB).

Key exports:
    SubmissionBundle    -- Frozen dataclass holding all outputs of a build.
    build_submission    -- Main entry point: assembles one submission attempt.

Module dependency graph:
    config.py          -->  submission_builder.py  (FILE_SIZE_ZIP, ASSIGNMENTS_DIR,
                                                     ArtifactType, SubmissionStatus)
    models.py          -->  submission_builder.py  (Submission, SubmissionArtifact)
    code_generator.py  -->  submission_builder.py  (GeneratedCodeFile)
    students.py        -->  submission_builder.py  (StudentProfile)

Consumed by:
    generate_data.py   (Step 10, main pipeline loop calls build_submission)
    manifest.py        (Step 9, reads SubmissionBundle.artifacts)
"""

from __future__ import annotations

import hashlib
import random
import uuid
import zipfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path

from make_simul_data.seed_data.code_generator import GeneratedCodeFile
from make_simul_data.seed_data.config import (
    ASSIGNMENTS_DIR,
    FILE_SIZE_ZIP,
    ArtifactType,
    AssignmentDef,
    SubmissionStatus,
)
from make_simul_data.seed_data.models import Submission, SubmissionArtifact
from make_simul_data.seed_data.students import StudentProfile

# ── Constants ────────────────────────────────────────────────────────────

# MIME type for ZIP archive files (RFC 6838).
# Used by: _create_zip_artifact() when constructing SubmissionArtifact records.
MIME_ZIP: str = "application/zip"

# MIME type for Python source code files.
# Used by: _create_python_artifact() when constructing SubmissionArtifact records.
MIME_PYTHON: str = "text/x-python"

# Maximum number of hours before the due date that on-time submissions
# can be submitted. Simulates students submitting throughout the
# assignment window, not just at the deadline.
# Used by: _compute_submitted_at() in this module.
ON_TIME_WINDOW_HOURS: int = 72

# Maximum number of hours after the due date that late submissions
# can arrive. Simulates students who miss the deadline by up to 2 days.
# Used by: _compute_submitted_at() in this module.
LATE_WINDOW_HOURS: int = 48

# Probability that a late-flagged student actually submits late on any
# given assignment. Not every "late submitter" student is late every time.
# Used by: build_submission() when determining submission status.
LATE_PROBABILITY: float = 0.5

# Realistic padding filenames that students commonly include in ZIP
# submissions. These simulate __pycache__ bytecode, IDE configuration,
# test data files, and personal notes that students often forget to
# exclude when zipping their project folders.
# Used by: _generate_padding_data() to name padding entries in the ZIP.
_PADDING_FILENAMES: tuple[str, ...] = (
    "__pycache__/hw_solution.cpython-312.pyc",
    ".vscode/settings.json",
    "test_data/sample_input.txt",
    "test_data/expected_output.txt",
    "notes.txt",
    "README.md",
)


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class SubmissionBundle:
    """Immutable container for all outputs of a single submission build.

    Holds the Submission model record, all SubmissionArtifact records
    (for both the ZIP bundle and individual Python files), the generated
    code files, and file system paths. This bundle is the primary return
    type of build_submission() and is consumed by downstream pipeline
    stages (manifest generation, metadata CSV export).

    Created by: build_submission() in this module.
    Consumed by: generate_data.py (Step 10, collects bundles for metadata),
                 manifest.py (Step 9, reads artifacts list for manifest.json).

    Attributes:
        submission:     The Submission Pydantic model instance with a unique
                        UUID, student/assignment IDs, attempt number, timestamps,
                        and submission status. Serialized to submissions.csv.
        artifacts:      Tuple of SubmissionArtifact records for ALL files in
                        this submission: one for each .py file (artifact_type
                        "python_file") PLUS one for the ZIP bundle itself
                        (artifact_type "zip_bundle"). Each artifact has its
                        own UUID, SHA256 hash, and file size.
        code_files:     Tuple of GeneratedCodeFile instances from Step 4's
                        code_generator. Retained here for downstream use
                        (e.g., plagiarism similarity analysis in Step 8
                        needs the raw source text).
        zip_path:       Absolute Path to the created ZIP file on disk.
                        Example: .../HW1/S001/attempt1/S001_HW1_attempt1.zip
        submission_dir: Absolute Path to the submission's directory on disk.
                        Example: .../HW1/S001/attempt1/
                        The ZIP file and manifest.json both live here.
    """

    submission: Submission
    artifacts: tuple[SubmissionArtifact, ...]
    code_files: tuple[GeneratedCodeFile, ...]
    zip_path: Path
    submission_dir: Path


# ── Helper Functions ─────────────────────────────────────────────────────


def _compute_submission_dir(
    student_id: str,
    assignment_id: str,
    attempt_no: int,
    output_dir: Path | None = None,
) -> Path:
    """Compute the directory path for a single submission attempt.

    Constructs the path following the project's directory convention:
        {output_dir}/{HW_ID}/{STUDENT_ID}/attempt{N}/

    If output_dir is None, uses the default ASSIGNMENTS_DIR from config.py
    which resolves to make_simul_data/output/seed_data/intro_cs/Assignments/.

    Used by: build_submission() in this module.

    Args:
        student_id:    Student identifier (e.g., "S001").
        assignment_id: Assignment identifier (e.g., "HW1").
        attempt_no:    Attempt number (1, 2, or 3).
        output_dir:    Optional base output directory. If None, uses
                       ASSIGNMENTS_DIR from config.py.

    Returns:
        A Path to the submission directory.

    Example::

        path = _compute_submission_dir("S001", "HW1", 1)
        # -> Path(".../intro_cs/Assignments/HW1/S001/attempt1")
    """
    base: Path = output_dir if output_dir is not None else ASSIGNMENTS_DIR
    return base / assignment_id / student_id / f"attempt{attempt_no}"


def _compute_zip_filename(
    student_id: str,
    assignment_id: str,
    attempt_no: int,
) -> str:
    """Compute the ZIP bundle filename for a submission.

    Follows the naming convention: {STUDENT_ID}_{HW_ID}_attempt{N}.zip.
    This convention is defined in the seed data implementation plan
    and ensures unique, human-readable filenames per submission.

    Used by: build_submission() in this module.

    Args:
        student_id:    Student identifier (e.g., "S001").
        assignment_id: Assignment identifier (e.g., "HW1").
        attempt_no:    Attempt number (1, 2, or 3).

    Returns:
        The ZIP filename string (e.g., "S001_HW1_attempt1.zip").
    """
    return f"{student_id}_{assignment_id}_attempt{attempt_no}.zip"


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's contents.

    Reads the file in 8 KB chunks to avoid loading large files entirely
    into memory. Returns a lowercase 64-character hex string.

    Used by: _create_zip_artifact() (for computing ZIP file hash after
             the archive is written to disk).

    Args:
        file_path: Absolute path to the file to hash.

    Returns:
        A 64-character lowercase hex digest string.

    Raises:
        FileNotFoundError: If file_path does not exist.
    """
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()


def _compute_sha256_bytes(data: bytes) -> str:
    """Compute the SHA-256 hex digest of in-memory bytes.

    Used for computing hashes of Python file contents before or without
    writing them to disk, allowing SubmissionArtifact records to be
    created from GeneratedCodeFile content directly.

    Used by: _create_python_artifact() in this module.

    Args:
        data: The raw bytes to hash.

    Returns:
        A 64-character lowercase hex digest string.
    """
    return hashlib.sha256(data).hexdigest()


def _compute_submitted_at(
    due_date_str: str,
    is_late: bool,
    rng: random.Random,
) -> datetime:
    """Generate a simulated submission timestamp relative to the due date.

    For on-time submissions: submitted_at is within ON_TIME_WINDOW_HOURS
    (72 hours) before the due date, distributed uniformly.
    For late submissions: submitted_at is within LATE_WINDOW_HOURS
    (48 hours) after the due date, distributed uniformly.

    All timestamps are UTC-aware (timezone.utc).

    Used by: build_submission() in this module.

    Args:
        due_date_str: ISO 8601 date string (e.g., "2026-02-14")
                      from AssignmentDef.due_date.
        is_late:      Whether this submission should be late.
        rng:          Seeded Random instance for deterministic offset.

    Returns:
        A timezone-aware UTC datetime representing when the student
        submitted their work.
    """
    # Parse the due date string and set the deadline to 23:59:00 UTC,
    # which represents a typical end-of-day homework deadline.
    due_dt: datetime = datetime.fromisoformat(due_date_str).replace(
        hour=23, minute=59, second=0, tzinfo=timezone.utc
    )

    if is_late:
        # Late: submit between 1 minute and LATE_WINDOW_HOURS after deadline.
        offset_seconds: int = rng.randint(60, LATE_WINDOW_HOURS * 3600)
        return due_dt + timedelta(seconds=offset_seconds)
    else:
        # On-time: submit between ON_TIME_WINDOW_HOURS before and deadline.
        offset_seconds = rng.randint(0, ON_TIME_WINDOW_HOURS * 3600)
        return due_dt - timedelta(seconds=offset_seconds)


def _generate_padding_data(
    target_size: int,
    current_size: int,
    rng: random.Random,
) -> list[tuple[str, bytes]]:
    """Generate padding file entries to fill a ZIP to the target size.

    Creates one or more fake files (simulating student project artifacts
    like __pycache__ bytecode, IDE settings, test data, or notes) whose
    combined size brings the total ZIP content close to the target size.

    The padding content is deterministic pseudo-random bytes generated
    via rng.randbytes(), ensuring full reproducibility of the generated
    ZIP bundles given the same seed.

    Used by: _create_zip_bundle() in this module.

    Args:
        target_size:  Desired total uncompressed content size in bytes.
        current_size: Current total size of real code files in bytes.
        rng:          Seeded Random instance for reproducible content.

    Returns:
        A list of (filename, content_bytes) tuples. Each tuple represents
        one padding file to be added to the ZIP archive. Returns an empty
        list if current_size already meets or exceeds the target.
    """
    needed: int = target_size - current_size
    if needed <= 0:
        return []

    padding_files: list[tuple[str, bytes]] = []
    remaining: int = needed

    # Distribute padding across 2-4 files for realism. Students rarely
    # include just one extra file; they typically have a mix of cache,
    # config, and data files.
    file_count: int = rng.randint(2, min(4, len(_PADDING_FILENAMES)))
    selected_names: list[str] = rng.sample(list(_PADDING_FILENAMES), file_count)

    for i, name in enumerate(selected_names):
        if i == len(selected_names) - 1:
            # Last file gets all remaining bytes to ensure we hit the target.
            chunk_size: int = remaining
        else:
            # Each intermediate file gets a random fraction of remaining bytes.
            min_chunk: int = remaining // (file_count - i + 1)
            max_chunk: int = remaining // 2 + 1
            if min_chunk >= max_chunk:
                chunk_size = min_chunk
            else:
                chunk_size = rng.randint(min_chunk, max_chunk)

        if chunk_size <= 0:
            continue

        # Generate deterministic pseudo-random bytes for padding content.
        # randbytes() uses the instance's Mersenne Twister RNG, so output
        # is fully reproducible given the same seed and call sequence.
        content: bytes = rng.randbytes(chunk_size)
        padding_files.append((name, content))
        remaining -= chunk_size

    return padding_files


def _create_zip_bundle(
    submission_dir: Path,
    zip_filename: str,
    code_files: list[GeneratedCodeFile],
    rng: random.Random,
) -> Path:
    """Create a ZIP archive containing code files and padding data.

    Writes all generated Python source files into the ZIP, then adds
    deterministic padding files to bring the total ZIP size within
    the FILE_SIZE_ZIP range (100-300 KB). Uses ZIP_DEFLATED compression.

    The ZIP is written to submission_dir/zip_filename.

    Used by: build_submission() in this module.

    Args:
        submission_dir: Directory where the ZIP file will be created.
                        Must already exist (caller creates it).
        zip_filename:   Name for the ZIP file (e.g., "S001_HW1_attempt1.zip").
        code_files:     List of GeneratedCodeFile instances to include.
        rng:            Seeded Random instance for padding generation and
                        target size selection.

    Returns:
        The absolute Path to the created ZIP file.
    """
    zip_path: Path = submission_dir / zip_filename

    # Randomly select a target uncompressed size within FILE_SIZE_ZIP range.
    # FILE_SIZE_ZIP = (102_400, 307_200) i.e., 100-300 KB.
    min_zip, max_zip = FILE_SIZE_ZIP
    target_size: int = rng.randint(min_zip, max_zip)

    # Compute current size of all code files combined.
    current_size: int = sum(cf.size_bytes for cf in code_files)

    # Generate padding data to bridge the gap between code size and target.
    padding_files: list[tuple[str, bytes]] = _generate_padding_data(
        target_size, current_size, rng
    )

    # Write the ZIP archive with DEFLATED compression.
    # Random padding bytes are incompressible (~1:1 ratio), while code text
    # compresses ~50%, so the final ZIP size is close to the target.
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Add all Python source files first.
        for cf in code_files:
            zf.writestr(cf.filename, cf.content)

        # Add padding files to reach the target size.
        for pad_name, pad_data in padding_files:
            zf.writestr(pad_name, pad_data)

    return zip_path


def _create_python_artifact(
    submission_id: uuid.UUID,
    code_file: GeneratedCodeFile,
) -> SubmissionArtifact:
    """Create a SubmissionArtifact record for a single Python source file.

    Computes the SHA-256 hash from the in-memory content string
    (encoded as UTF-8) without requiring the file to exist on disk.

    Used by: build_submission() in this module.

    Args:
        submission_id: UUID of the parent Submission record.
        code_file:     The GeneratedCodeFile to create an artifact for.

    Returns:
        A SubmissionArtifact Pydantic model instance with artifact_type
        "python_file" and the correct SHA256 hash and size.
    """
    content_bytes: bytes = code_file.content.encode("utf-8")
    return SubmissionArtifact(
        submission_id=submission_id,
        artifact_type=ArtifactType.PYTHON_FILE,
        filename=code_file.filename,
        filetype=MIME_PYTHON,
        sha256=_compute_sha256_bytes(content_bytes),
        size_bytes=code_file.size_bytes,
    )


def _create_zip_artifact(
    submission_id: uuid.UUID,
    zip_path: Path,
    zip_filename: str,
) -> SubmissionArtifact:
    """Create a SubmissionArtifact record for a ZIP bundle file.

    Reads the ZIP file from disk to compute its SHA-256 hash and
    actual file size (post-compression).

    Used by: build_submission() in this module.

    Args:
        submission_id: UUID of the parent Submission record.
        zip_path:      Absolute path to the ZIP file on disk.
        zip_filename:  Bare filename of the ZIP (e.g., "S001_HW1_attempt1.zip").

    Returns:
        A SubmissionArtifact Pydantic model instance with artifact_type
        "zip_bundle" and the correct SHA256 hash and on-disk size.
    """
    return SubmissionArtifact(
        submission_id=submission_id,
        artifact_type=ArtifactType.ZIP_BUNDLE,
        filename=zip_filename,
        filetype=MIME_ZIP,
        sha256=_compute_sha256(zip_path),
        size_bytes=zip_path.stat().st_size,
    )


# ── Main Function ────────────────────────────────────────────────────────


def build_submission(
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    code_files: list[GeneratedCodeFile],
    rng: random.Random,
    output_dir: Path | None = None,
) -> SubmissionBundle:
    """Build a complete submission bundle: directory, ZIP, artifacts, records.

    This is the main entry point for Step 5. It performs the following
    operations in sequence:

        1. Compute submission directory path and create it on disk.
        2. Determine submission status (on_time vs late) based on
           the student's is_late_submitter flag and RNG.
        3. Compute the submitted_at timestamp relative to the due date.
        4. Create the Submission Pydantic model record.
        5. Write individual .py files to the submission directory.
        6. Create a ZIP bundle containing .py files + padding data.
        7. Compute SHA-256 hashes for all files.
        8. Create SubmissionArtifact records for every file.
        9. Assemble and return the frozen SubmissionBundle.

    Used by: generate_data.py (Step 10, called once per student-assignment-
             attempt triple in the main generation loop)

    Args:
        student:    The StudentProfile for this submission's author.
                    Used for student_id and is_late_submitter flag.
        assignment: The AssignmentDef for this submission's assignment.
                    Used for assignment_id, due_date, and required_files.
        attempt_no: Which attempt this is (1, 2, or 3).
        code_files: List of GeneratedCodeFile instances from
                    code_generator.generate_code_files(). Typically
                    1 file for HW1-HW3, 2 files for HW4-HW5.
        rng:        Seeded Random instance for all stochastic decisions
                    (submission timing, padding generation, status).
                    Must be created via config.create_rng().
        output_dir: Optional base directory for output. If None, defaults
                    to ASSIGNMENTS_DIR from config.py. Useful for testing
                    with tmp_path.

    Returns:
        A frozen SubmissionBundle containing the Submission record,
        all SubmissionArtifact records, the code files, the ZIP path,
        and the submission directory path.

    Raises:
        ValueError: If code_files is empty.

    Example::

        from make_simul_data.seed_data.config import create_rng
        from make_simul_data.seed_data.code_generator import generate_code_files

        rng = create_rng(42)
        code_files = generate_code_files(student, assignment, 1, rng)
        bundle = build_submission(student, assignment, 1, code_files, rng)
        assert bundle.zip_path.exists()
    """
    if not code_files:
        raise ValueError(
            "code_files must not be empty. At least one GeneratedCodeFile "
            "is required to build a submission."
        )

    # Step 1: Compute and create submission directory on disk.
    submission_dir: Path = _compute_submission_dir(
        student.student_id, assignment.assignment_id, attempt_no, output_dir
    )
    submission_dir.mkdir(parents=True, exist_ok=True)

    # Step 2: Determine submission status.
    # Late submitter students have a LATE_PROBABILITY (50%) chance of
    # actually being late on any given submission. Non-late students
    # are always on-time.
    is_late: bool = student.is_late_submitter and rng.random() < LATE_PROBABILITY
    status: SubmissionStatus = (
        SubmissionStatus.LATE if is_late else SubmissionStatus.ON_TIME
    )

    # Step 3: Compute submitted_at timestamp relative to the due date.
    submitted_at: datetime = _compute_submitted_at(assignment.due_date, is_late, rng)
    # Convert the due_date string to a datetime at 23:59:00 UTC for the
    # Submission record's due_at field.
    due_at: datetime = datetime.fromisoformat(assignment.due_date).replace(
        hour=23, minute=59, second=0, tzinfo=timezone.utc
    )

    # Step 4: Create the Submission Pydantic model record.
    submission: Submission = Submission(
        student_id=student.student_id,
        assignment_id=assignment.assignment_id,
        attempt_no=attempt_no,
        submitted_at=submitted_at,
        due_at=due_at,
        status=status.value,
    )

    # Step 5: Write individual .py files to the submission directory.
    for cf in code_files:
        py_path: Path = submission_dir / cf.filename
        py_path.write_text(cf.content, encoding="utf-8")

    # Step 6: Create ZIP bundle containing .py files + padding data.
    zip_filename: str = _compute_zip_filename(
        student.student_id, assignment.assignment_id, attempt_no
    )
    zip_path: Path = _create_zip_bundle(submission_dir, zip_filename, code_files, rng)

    # Steps 7-8: Create SubmissionArtifact records for all files.
    artifacts: list[SubmissionArtifact] = []

    # Create an artifact record for each Python source file.
    for cf in code_files:
        artifacts.append(_create_python_artifact(submission.submission_id, cf))

    # Create an artifact record for the ZIP bundle.
    artifacts.append(
        _create_zip_artifact(submission.submission_id, zip_path, zip_filename)
    )

    # Step 9: Assemble and return the frozen SubmissionBundle.
    return SubmissionBundle(
        submission=submission,
        artifacts=tuple(artifacts),
        code_files=tuple(code_files),
        zip_path=zip_path,
        submission_dir=submission_dir,
    )
