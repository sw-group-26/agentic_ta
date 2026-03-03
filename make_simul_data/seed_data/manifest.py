"""Per-submission manifest.json generation and serialization.

This module creates a machine-readable manifest for each submission attempt.
The manifest summarizes the submission's identity (student, assignment, attempt)
and lists all attached artifacts with their filenames, types, SHA-256 hashes,
and sizes.  Downstream consumers use manifests for integrity verification and
artifact discovery without scanning the file system.

Key exports:
    MANIFEST_FILENAME    -- Constant name of the manifest file ("manifest.json").
    generate_manifest    -- Build a Manifest model from a SubmissionBundle.
    write_manifest       -- Serialize a Manifest to a JSON file on disk.

Module dependency graph:
    models.py              -->  manifest.py  (Manifest, ManifestArtifact)
    submission_builder.py  -->  manifest.py  (SubmissionBundle)

Consumed by:
    generate_data.py  (Step 10, calls generate_manifest + write_manifest per bundle)
    validator.py      (Step 9, imports MANIFEST_FILENAME for file discovery)
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from make_simul_data.seed_data.models import Manifest, ManifestArtifact
from make_simul_data.seed_data.submission_builder import SubmissionBundle

# ── Constants ────────────────────────────────────────────────────────────

# Filename for the manifest JSON file placed in each submission directory.
# Every submission attempt directory (e.g., .../HW1/S001/attempt1/) gets
# one manifest file with this exact name.
# Used by: write_manifest() in this module,
#          validator.py (_validate_schema, _validate_checksums,
#                        _validate_file_existence use rglob with this name)
MANIFEST_FILENAME: str = "manifest.json"


# ── Public Functions ─────────────────────────────────────────────────────


def generate_manifest(bundle: SubmissionBundle) -> Manifest:
    """Build a Manifest Pydantic model from a completed SubmissionBundle.

    Extracts submission metadata (student_id, assignment_id, attempt_no)
    and converts each SubmissionArtifact record into a lightweight
    ManifestArtifact entry.  The resulting Manifest is ready for JSON
    serialization via write_manifest().

    Each SubmissionArtifact in the bundle is mapped to a ManifestArtifact,
    keeping only the fields relevant to the manifest (filename,
    artifact_type, sha256, size_bytes).  The artifact_id and submission_id
    are omitted because they are implicit from the parent Manifest.

    Used by: generate_data.py (Step 10 -- called once per SubmissionBundle
             after all artifacts, grading results, and reports are generated)

    Args:
        bundle: A fully populated SubmissionBundle produced by
                build_submission().  Must contain at least one artifact
                in bundle.artifacts.

    Returns:
        A Manifest Pydantic model instance with:
          - submission_id, student_id, assignment_id, attempt_no copied
            from bundle.submission
          - generated_at set to the current UTC timestamp
          - artifacts populated from bundle.artifacts

    Example::

        bundle = build_submission(student, assignment, 1, code_files, rng, out)
        manifest = generate_manifest(bundle)
        assert manifest.submission_id == bundle.submission.submission_id
        assert len(manifest.artifacts) == len(bundle.artifacts)
    """
    # Convert each SubmissionArtifact to the lighter ManifestArtifact.
    # ManifestArtifact omits artifact_id and submission_id since those
    # are derivable from the parent Manifest's submission_id.
    manifest_artifacts: list[ManifestArtifact] = [
        ManifestArtifact(
            filename=artifact.filename,
            artifact_type=artifact.artifact_type,
            sha256=artifact.sha256,
            size_bytes=artifact.size_bytes,
        )
        for artifact in bundle.artifacts
    ]

    return Manifest(
        submission_id=bundle.submission.submission_id,
        student_id=bundle.submission.student_id,
        assignment_id=bundle.submission.assignment_id,
        attempt_no=bundle.submission.attempt_no,
        generated_at=datetime.now(timezone.utc),
        artifacts=manifest_artifacts,
    )


def write_manifest(manifest: Manifest, output_dir: Path) -> Path:
    """Serialize a Manifest model to a JSON file on disk.

    Writes the manifest as a human-readable JSON file named
    'manifest.json' (MANIFEST_FILENAME) in the specified output
    directory.  Uses Pydantic v2's model_dump(mode="json") for
    automatic serialization of UUID and datetime fields to their
    string representations.

    The output JSON uses 2-space indentation for readability and
    ensure_ascii=False to preserve any Unicode characters in student
    names or filenames.

    Used by: generate_data.py (Step 10 -- writes manifest.json into
             the submission's attempt directory alongside the ZIP file)

    Args:
        manifest:   The Manifest model to serialize.
        output_dir: Directory where manifest.json will be created.
                    Typically bundle.submission_dir (e.g.,
                    .../HW1/S001/attempt1/).  The directory must
                    already exist; this function does not create it.

    Returns:
        Absolute Path to the written manifest.json file.

    Raises:
        FileNotFoundError: If output_dir does not exist.

    Example::

        path = write_manifest(manifest, bundle.submission_dir)
        assert path.name == "manifest.json"
        assert path.exists()
    """
    # Build the output file path using the constant filename.
    manifest_path: Path = output_dir / MANIFEST_FILENAME

    # Pydantic v2's model_dump(mode="json") converts UUID to string
    # and datetime to ISO 8601 string automatically, producing a
    # plain dict that json.dump can serialize without custom encoders.
    data: dict = manifest.model_dump(mode="json")

    with open(manifest_path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)

    return manifest_path
