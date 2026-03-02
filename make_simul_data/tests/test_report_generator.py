"""Unit tests for PDF report and OCR image generation.

Tests the generate_pdf_report() and generate_ocr_images() functions,
GeneratedPDFReport and GeneratedOCRImage dataclasses, and helper
functions from make_simul_data.seed_data.report_generator.

Run with: pytest make_simul_data/tests/test_report_generator.py -v

Test organization:
    TestGeneratedPDFReportDataclass   -- Frozen dataclass contract tests.
    TestGeneratedOCRImageDataclass    -- Frozen dataclass contract tests.
    TestGeneratePDFReportBasic        -- Core PDF generation behavior.
    TestPDFContent                    -- PDF file validity and content.
    TestPDFSizeConstraints            -- PDF within FILE_SIZE_PDF range.
    TestPDFArtifactRecords            -- SubmissionArtifact correctness.
    TestGenerateOCRImagesBasic        -- Core OCR generation behavior.
    TestOCRImageContent               -- PNG validity and visual properties.
    TestOCRImageSizeConstraints       -- PNG within expected size range.
    TestReproducibility               -- Same seed produces identical output.
    TestAllAssignments                -- All 5 assignments generate PDFs.
    TestEdgeCases                     -- Error handling and boundary conditions.
"""

from __future__ import annotations

import dataclasses
import uuid
from pathlib import Path

import pytest
from PIL import Image

from make_simul_data.seed_data.assignments import get_assignment_by_id
from make_simul_data.seed_data.config import FILE_SIZE_PDF, create_rng
from make_simul_data.seed_data.report_generator import (
    MIME_PDF,
    GeneratedPDFReport,
    generate_ocr_images,
    generate_pdf_report,
)
from make_simul_data.seed_data.students import StudentProfile

# ── Test Constants ───────────────────────────────────────────────────

# Seed for reproducible tests. Matches MASTER_SEED from config.py.
TEST_SEED: int = 42


# ── Test Fixtures ────────────────────────────────────────────────────


def _make_student(
    skill_level: float = 0.7,
    student_id: str = "S001",
    generates_pdf: bool = True,
) -> StudentProfile:
    """Create a minimal StudentProfile for testing.

    Args:
        skill_level: Override skill level (default 0.7 = medium tier).
        student_id: Override student ID.
        generates_pdf: Whether this student generates PDF reports.

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
        generates_pdf=generates_pdf,
    )


def _make_pdf_report(
    tmp_path: Path,
    student_id: str = "S001",
    hw_id: str = "HW1",
    seed: int = TEST_SEED,
) -> GeneratedPDFReport:
    """Helper to generate a PDF report for testing.

    Args:
        tmp_path: Pytest temporary directory fixture.
        student_id: Student ID for the report.
        hw_id: Assignment ID for the report.
        seed: Random seed for reproducibility.

    Returns:
        A GeneratedPDFReport instance with the PDF written to tmp_path.
    """
    student = _make_student(student_id=student_id)
    assignment = get_assignment_by_id(hw_id)
    submission_id = uuid.uuid4()
    submission_dir = tmp_path / hw_id / student_id / "attempt1"
    submission_dir.mkdir(parents=True, exist_ok=True)
    rng = create_rng(seed)
    return generate_pdf_report(
        student, assignment, 1, submission_id, submission_dir, rng
    )


# ── Test Classes ─────────────────────────────────────────────────────


class TestGeneratedPDFReportDataclass:
    """Verify GeneratedPDFReport is a frozen dataclass with correct fields."""

    def test_is_frozen(self, tmp_path) -> None:
        """Assigning to a GeneratedPDFReport field raises FrozenInstanceError."""
        report = _make_pdf_report(tmp_path)
        with pytest.raises(dataclasses.FrozenInstanceError):
            report.filename = "other.pdf"  # type: ignore[misc]

    def test_has_required_fields(self, tmp_path) -> None:
        """GeneratedPDFReport has all five required fields."""
        report = _make_pdf_report(tmp_path)
        assert hasattr(report, "filename")
        assert hasattr(report, "path")
        assert hasattr(report, "size_bytes")
        assert hasattr(report, "sha256")
        assert hasattr(report, "artifact")


class TestGeneratedOCRImageDataclass:
    """Verify GeneratedOCRImage is a frozen dataclass with correct fields."""

    def test_is_frozen(self, tmp_path) -> None:
        """Assigning to a GeneratedOCRImage field raises FrozenInstanceError."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        with pytest.raises(dataclasses.FrozenInstanceError):
            images[0].filename = "other.png"  # type: ignore[misc]

    def test_has_required_fields(self, tmp_path) -> None:
        """GeneratedOCRImage has all four required fields."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        img = images[0]
        assert hasattr(img, "filename")
        assert hasattr(img, "path")
        assert hasattr(img, "size_bytes")
        assert hasattr(img, "sha256")


class TestGeneratePDFReportBasic:
    """Core generate_pdf_report() behavior tests using tmp_path."""

    def test_returns_generated_pdf_report(self, tmp_path) -> None:
        """Return type is GeneratedPDFReport."""
        report = _make_pdf_report(tmp_path)
        assert isinstance(report, GeneratedPDFReport)

    def test_pdf_file_exists_on_disk(self, tmp_path) -> None:
        """report.path.exists() is True."""
        report = _make_pdf_report(tmp_path)
        assert report.path.exists()

    def test_pdf_in_submission_dir(self, tmp_path) -> None:
        """PDF file is in the correct submission directory."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        submission_dir = tmp_path / "HW1" / "S001" / "attempt1"
        submission_dir.mkdir(parents=True, exist_ok=True)
        rng = create_rng(TEST_SEED)
        report = generate_pdf_report(
            student, assignment, 1, uuid.uuid4(), submission_dir, rng
        )
        assert str(submission_dir) in str(report.path)

    def test_pdf_filename_convention(self, tmp_path) -> None:
        """Filename follows the {student_id}_{hw_id}_attempt{N}_report.pdf pattern."""
        report = _make_pdf_report(tmp_path, student_id="S042", hw_id="HW3")
        assert report.filename == "S042_HW3_attempt1_report.pdf"

    def test_pdf_filename_attempt2(self, tmp_path) -> None:
        """Filename correctly reflects attempt number 2."""
        student = _make_student(student_id="S010")
        assignment = get_assignment_by_id("HW2")
        submission_dir = tmp_path / "HW2" / "S010" / "attempt2"
        submission_dir.mkdir(parents=True, exist_ok=True)
        rng = create_rng(TEST_SEED)
        report = generate_pdf_report(
            student, assignment, 2, uuid.uuid4(), submission_dir, rng
        )
        assert report.filename == "S010_HW2_attempt2_report.pdf"


class TestPDFContent:
    """Verify PDF file validity and content."""

    def test_pdf_magic_bytes(self, tmp_path) -> None:
        """File starts with %PDF magic bytes (valid PDF header)."""
        report = _make_pdf_report(tmp_path)
        with open(report.path, "rb") as f:
            header = f.read(5)
        assert header == b"%PDF-"

    def test_pdf_has_nonzero_size(self, tmp_path) -> None:
        """PDF file has non-zero byte count."""
        report = _make_pdf_report(tmp_path)
        assert report.size_bytes > 0

    def test_size_bytes_matches_file(self, tmp_path) -> None:
        """report.size_bytes matches the actual file size on disk."""
        report = _make_pdf_report(tmp_path)
        assert report.size_bytes == report.path.stat().st_size


class TestPDFSizeConstraints:
    """Verify PDF size falls within expected range."""

    def test_pdf_size_above_minimum(self, tmp_path) -> None:
        """PDF is at least 80% of FILE_SIZE_PDF[0] (with tolerance)."""
        report = _make_pdf_report(tmp_path)
        min_pdf = FILE_SIZE_PDF[0]
        # Allow 20% tolerance because the two-pass approach may not hit
        # the exact target due to PNG compression variability.
        assert (
            report.size_bytes >= min_pdf * 0.8
        ), f"PDF too small: {report.size_bytes} bytes < {min_pdf * 0.8}"

    def test_pdf_size_below_maximum(self, tmp_path) -> None:
        """PDF is at most 120% of FILE_SIZE_PDF[1] (with tolerance)."""
        report = _make_pdf_report(tmp_path)
        max_pdf = FILE_SIZE_PDF[1]
        assert (
            report.size_bytes <= max_pdf * 1.2
        ), f"PDF too large: {report.size_bytes} bytes > {max_pdf * 1.2}"

    def test_multiple_seeds_varied_sizes(self, tmp_path) -> None:
        """Different seeds produce different PDF sizes (variety check)."""
        sizes = []
        for seed in [1, 2, 3, 4, 5]:
            report = _make_pdf_report(tmp_path / f"seed{seed}", seed=seed)
            sizes.append(report.size_bytes)
        # At least 2 different sizes among 5 runs (sizes are randomized).
        assert len(set(sizes)) >= 2, f"All sizes identical: {sizes}"


class TestPDFArtifactRecords:
    """Verify SubmissionArtifact records for PDF reports."""

    def test_artifact_type_is_pdf_report(self, tmp_path) -> None:
        """artifact.artifact_type is 'pdf_report'."""
        report = _make_pdf_report(tmp_path)
        assert report.artifact.artifact_type == "pdf_report"

    def test_artifact_filetype_is_pdf_mime(self, tmp_path) -> None:
        """artifact.filetype is 'application/pdf'."""
        report = _make_pdf_report(tmp_path)
        assert report.artifact.filetype == MIME_PDF

    def test_artifact_sha256_length(self, tmp_path) -> None:
        """SHA256 hash is exactly 64 hex characters."""
        report = _make_pdf_report(tmp_path)
        assert len(report.artifact.sha256) == 64
        assert all(c in "0123456789abcdef" for c in report.artifact.sha256)

    def test_artifact_size_bytes_matches(self, tmp_path) -> None:
        """artifact.size_bytes matches report.size_bytes."""
        report = _make_pdf_report(tmp_path)
        assert report.artifact.size_bytes == report.size_bytes

    def test_artifact_submission_id_matches(self, tmp_path) -> None:
        """artifact.submission_id matches the input submission_id."""
        student = _make_student()
        assignment = get_assignment_by_id("HW1")
        submission_id = uuid.uuid4()
        submission_dir = tmp_path / "HW1" / "S001" / "attempt1"
        submission_dir.mkdir(parents=True, exist_ok=True)
        rng = create_rng(TEST_SEED)
        report = generate_pdf_report(
            student, assignment, 1, submission_id, submission_dir, rng
        )
        assert report.artifact.submission_id == submission_id

    def test_artifact_filename_matches(self, tmp_path) -> None:
        """artifact.filename matches report.filename."""
        report = _make_pdf_report(tmp_path)
        assert report.artifact.filename == report.filename


class TestGenerateOCRImagesBasic:
    """Core generate_ocr_images() behavior tests using tmp_path."""

    def test_returns_correct_count(self, tmp_path) -> None:
        """Returns exactly count images."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=5)
        assert len(images) == 5

    def test_all_files_exist_on_disk(self, tmp_path) -> None:
        """Every generated image file exists on disk."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=3)
        for img in images:
            assert img.path.exists(), f"{img.filename} not found on disk"

    def test_files_in_ocr_directory(self, tmp_path) -> None:
        """All files are under {output_dir}/ocr_images/."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=3)
        for img in images:
            assert "ocr_images" in str(img.path)

    def test_filename_convention(self, tmp_path) -> None:
        """Filenames follow the ocr_{NNN}.png pattern."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=3)
        assert images[0].filename == "ocr_001.png"
        assert images[1].filename == "ocr_002.png"
        assert images[2].filename == "ocr_003.png"

    def test_default_rng_creation(self, tmp_path) -> None:
        """Passing rng=None creates a default RNG from MASTER_SEED."""
        images = generate_ocr_images(output_dir=tmp_path, rng=None, count=1)
        assert len(images) == 1
        assert images[0].path.exists()


class TestOCRImageContent:
    """Verify PNG file validity and visual properties."""

    def test_png_magic_bytes(self, tmp_path) -> None:
        """File starts with PNG signature (\\x89PNG)."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        with open(images[0].path, "rb") as f:
            header = f.read(4)
        assert header == b"\x89PNG"

    def test_image_is_rgb(self, tmp_path) -> None:
        """Pillow opens the image as RGB mode."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        with Image.open(images[0].path) as img:
            assert img.mode == "RGB"

    def test_image_dimensions(self, tmp_path) -> None:
        """Image dimensions match OCR_IMAGE_WIDTH x OCR_IMAGE_HEIGHT."""
        from make_simul_data.seed_data.report_generator import (
            OCR_IMAGE_HEIGHT,
            OCR_IMAGE_WIDTH,
        )

        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        with Image.open(images[0].path) as img:
            assert img.size == (OCR_IMAGE_WIDTH, OCR_IMAGE_HEIGHT)

    def test_sha256_length(self, tmp_path) -> None:
        """SHA256 hash is exactly 64 hex characters."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        assert len(images[0].sha256) == 64
        assert all(c in "0123456789abcdef" for c in images[0].sha256)

    def test_size_bytes_matches_file(self, tmp_path) -> None:
        """size_bytes matches the actual file size on disk."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=1)
        assert images[0].size_bytes == images[0].path.stat().st_size


class TestOCRImageSizeConstraints:
    """Verify OCR image sizes are within expected bounds."""

    def test_image_size_above_minimum(self, tmp_path) -> None:
        """Each OCR image is at least 50 KB (reasonable lower bound)."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=3)
        for img in images:
            assert img.size_bytes >= 50_000, f"Image too small: {img.size_bytes} bytes"

    def test_image_size_below_maximum(self, tmp_path) -> None:
        """Each OCR image is at most 2 MB (reasonable upper bound)."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=3)
        for img in images:
            assert (
                img.size_bytes <= 2_000_000
            ), f"Image too large: {img.size_bytes} bytes"


class TestReproducibility:
    """Verify that the same seed produces identical output."""

    def test_same_seed_similar_pdf_size(self, tmp_path) -> None:
        """Two PDF generations with same seed produce same-size PDFs.

        Note: Exact hash matching is not possible because ReportLab embeds
        the current timestamp (/CreationDate, /ModDate) in PDF metadata,
        which changes between runs. Instead, we verify that identical seeds
        produce identical file sizes (same content, only metadata differs).
        """
        report1 = _make_pdf_report(tmp_path / "run1", seed=TEST_SEED)
        report2 = _make_pdf_report(tmp_path / "run2", seed=TEST_SEED)
        assert report1.size_bytes == report2.size_bytes

    def test_different_seed_different_pdf_hash(self, tmp_path) -> None:
        """Different seeds produce different PDFs."""
        report1 = _make_pdf_report(tmp_path / "run1", seed=1)
        report2 = _make_pdf_report(tmp_path / "run2", seed=999)
        assert report1.sha256 != report2.sha256

    def test_same_seed_identical_ocr_hashes(self, tmp_path) -> None:
        """Two OCR batches with same seed produce same SHA256 hashes."""
        rng1 = create_rng(TEST_SEED)
        images1 = generate_ocr_images(output_dir=tmp_path / "run1", rng=rng1, count=3)

        rng2 = create_rng(TEST_SEED)
        images2 = generate_ocr_images(output_dir=tmp_path / "run2", rng=rng2, count=3)

        for img1, img2 in zip(images1, images2):
            assert img1.sha256 == img2.sha256

    def test_different_seed_different_ocr_hashes(self, tmp_path) -> None:
        """Different seeds produce different OCR images."""
        rng1 = create_rng(1)
        images1 = generate_ocr_images(output_dir=tmp_path / "run1", rng=rng1, count=1)

        rng2 = create_rng(999)
        images2 = generate_ocr_images(output_dir=tmp_path / "run2", rng=rng2, count=1)

        assert images1[0].sha256 != images2[0].sha256


class TestAllAssignments:
    """Verify that all 5 assignments generate PDFs successfully."""

    @pytest.mark.parametrize("hw_id", ["HW1", "HW2", "HW3", "HW4", "HW5"])
    def test_pdf_for_all_assignments(self, hw_id: str, tmp_path) -> None:
        """generate_pdf_report runs without error for all assignments."""
        report = _make_pdf_report(tmp_path, hw_id=hw_id)
        assert report.path.exists()
        assert report.size_bytes > 0
        assert report.artifact.artifact_type == "pdf_report"


class TestEdgeCases:
    """Error handling and boundary conditions."""

    def test_ocr_count_zero(self, tmp_path) -> None:
        """generate_ocr_images(count=0) returns empty list."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=0)
        assert images == []

    def test_ocr_small_count(self, tmp_path) -> None:
        """generate_ocr_images(count=2) returns exactly 2 images."""
        rng = create_rng(TEST_SEED)
        images = generate_ocr_images(output_dir=tmp_path, rng=rng, count=2)
        assert len(images) == 2
        assert all(img.path.exists() for img in images)

    def test_different_seeds_produce_different_pdfs(self, tmp_path) -> None:
        """Different seeds produce different PDF content."""
        report1 = _make_pdf_report(tmp_path / "s1", seed=1)
        report2 = _make_pdf_report(tmp_path / "s2", seed=999)
        assert report1.sha256 != report2.sha256

    def test_different_students_produce_different_filenames(self, tmp_path) -> None:
        """Different student IDs produce different PDF filenames."""
        report1 = _make_pdf_report(tmp_path / "s1", student_id="S001", seed=TEST_SEED)
        report2 = _make_pdf_report(tmp_path / "s2", student_id="S050", seed=TEST_SEED)
        assert report1.filename != report2.filename
        assert "S001" in report1.filename
        assert "S050" in report2.filename
