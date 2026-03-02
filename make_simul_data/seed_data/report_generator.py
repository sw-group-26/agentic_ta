"""PDF report and OCR image generation for the seed data pipeline.

This module generates two types of artifacts for the Agentic TA system's
seed dataset:

1. **PDF Reports** (ReportLab): Lab report write-ups submitted by ~40% of
   students alongside their code. Each PDF contains a title page with
   student information, a "Reflection" section with Faker-generated
   paragraphs, a "What I Learned" section, and a "Challenges Faced"
   section. File sizes are controlled to fall within FILE_SIZE_PDF
   (50-500 KB) by varying paragraph count and embedding a decorative
   Pillow-generated image when the text-only PDF is too small.

2. **OCR Images** (Pillow): 100 standalone PNG images simulating
   handwritten student notes. Each image has slight rotation, font size
   variation, and noise overlay to mimic scanned handwriting. These
   are standalone images not tied to any specific submission, stored
   in a dedicated output directory.

Key exports:
    GeneratedPDFReport   -- Frozen dataclass holding PDF output metadata.
    GeneratedOCRImage    -- Frozen dataclass holding OCR image metadata.
    generate_pdf_report  -- Create a PDF report for one submission.
    generate_ocr_images  -- Create a batch of handwriting-simulation PNGs.

Module dependency graph:
    config.py          -->  report_generator.py  (FILE_SIZE_PDF, ArtifactType,
                                                    ASSIGNMENTS_DIR, AssignmentDef,
                                                    create_rng)
    models.py          -->  report_generator.py  (SubmissionArtifact)
    students.py        -->  report_generator.py  (StudentProfile)

Consumed by:
    generate_data.py   (Step 10, calls generate_pdf_report per submission
                        when student.generates_pdf is True, and calls
                        generate_ocr_images once for the 100-image batch)
    manifest.py        (Step 9, reads PDF artifacts for manifest.json)
"""

from __future__ import annotations

import hashlib
import io
import random
import uuid
from dataclasses import dataclass
from pathlib import Path

from faker import Faker
from PIL import Image, ImageDraw, ImageFilter, ImageFont
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image as RLImage
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from make_simul_data.seed_data.config import (
    ASSIGNMENTS_DIR,
    FILE_SIZE_PDF,
    ArtifactType,
    AssignmentDef,
    create_rng,
)
from make_simul_data.seed_data.models import SubmissionArtifact
from make_simul_data.seed_data.students import StudentProfile

# ── Constants ────────────────────────────────────────────────────────────

# MIME type for PDF files (RFC 6838).
# Used by: generate_pdf_report() when constructing SubmissionArtifact records.
MIME_PDF: str = "application/pdf"

# MIME type for PNG image files (RFC 2045).
# Used by: generate_ocr_images() when constructing GeneratedOCRImage records.
MIME_PNG: str = "image/png"

# Total number of standalone OCR images to generate across the entire dataset.
# These handwriting-simulation images are not tied to individual submissions.
# Used by: generate_ocr_images() as the default count parameter.
OCR_IMAGE_COUNT: int = 100

# Minimum number of reflection paragraphs in a PDF report's "Reflection" section.
# Controls the lower bound of text content length and thus the base PDF file size.
# Used by: _generate_report_sections() in this module.
MIN_PARAGRAPHS: int = 2

# Maximum number of reflection paragraphs in a PDF report's "Reflection" section.
# Controls the upper bound of text content length.
# Used by: _generate_report_sections() in this module.
MAX_PARAGRAPHS: int = 4

# Primary handwriting-style font path on macOS.
# MarkerFelt is a casual handwriting font bundled with all macOS installations.
# Used by: _resolve_handwriting_font() as the first choice for OCR image rendering.
_HANDWRITING_FONT_PATH: str = "/System/Library/Fonts/MarkerFelt.ttc"

# Fallback handwriting font path if MarkerFelt is unavailable.
# Noteworthy is another handwriting-like font on macOS.
# Used by: _resolve_handwriting_font() as a secondary fallback.
_HANDWRITING_FONT_FALLBACK: str = "/System/Library/Fonts/Noteworthy.ttc"

# Minimum font size in points for handwriting simulation.
# Variation between MIN and MAX simulates inconsistent handwriting pressure
# and pen control that is typical of handwritten notes.
# Used by: _render_handwriting_image() in this module.
HANDWRITING_FONT_SIZE_MIN: int = 18

# Maximum font size in points for handwriting simulation.
# Used by: _render_handwriting_image() in this module.
HANDWRITING_FONT_SIZE_MAX: int = 28

# Image width in pixels for OCR images.
# Sized to simulate a standard US letter page scan at moderate resolution
# (~150 DPI for an 8-inch width). Produces realistic OCR-quality images.
# Used by: _render_handwriting_image() in this module.
OCR_IMAGE_WIDTH: int = 1200

# Image height in pixels for OCR images.
# Sized proportionally to US letter page aspect ratio (~1.33:1 width:height).
# Used by: _render_handwriting_image() in this module.
OCR_IMAGE_HEIGHT: int = 1600

# Maximum rotation angle in degrees (applied both clockwise and counterclockwise)
# to OCR images to simulate imperfect scanning alignment.
# A value of 3.0 means rotation is sampled from [-3.0, +3.0] degrees.
# Used by: _render_handwriting_image() in this module.
MAX_ROTATION_DEGREES: float = 3.0

# Directory name for standalone OCR images within the output directory.
# OCR images are stored under ASSIGNMENTS_DIR / OCR_OUTPUT_DIRNAME /.
# Used by: generate_ocr_images() to create the output directory.
OCR_OUTPUT_DIRNAME: str = "ocr_images"

# CS1-themed content fragments intermixed with Faker sentences in OCR images.
# These simulate the kind of notes a CS1 student would scribble during a lecture
# or study session: code snippets, reminders, and pseudocode.
# Used by: _generate_handwriting_text() in this module.
_CS1_FRAGMENTS: tuple[str, ...] = (
    "def main():",
    "    x = int(input())",
    "    print(x * 2)",
    "# remember: use for loop",
    "if grade >= 90: A",
    "while count < n:",
    "    total += numbers[i]",
    "# TODO: fix off-by-one",
    "return sorted(my_list)",
    "def factorial(n):",
    "    if n <= 1: return 1",
    "list comprehension: [x**2 for x in range(10)]",
    "remember: index starts at 0!",
    "edge case: empty list",
    "test with: input = 0, -1, 100",
    "for i in range(len(arr)):",
    "    result.append(arr[i])",
    "break vs continue",
    "nested loop: O(n^2)",
    "dictionary: key -> value",
)


# ── Data Structures ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class GeneratedPDFReport:
    """Immutable container for a single generated PDF report file.

    Represents one .pdf file produced by the report generation pipeline.
    Not all submissions have a PDF report; only students with
    generates_pdf=True produce these. The PDF is written to the same
    submission_dir as the ZIP bundle.

    Created by: generate_pdf_report() in this module.
    Consumed by: generate_data.py (Step 10, collects artifacts for metadata),
                 manifest.py (Step 9, includes PDF in the manifest).

    Attributes:
        filename:   Name of the PDF file on disk
                    (e.g., "S001_HW1_attempt1_report.pdf").
                    Does not include the directory path.
        path:       Absolute Path to the PDF file on disk.
                    Located inside the submission_dir alongside the ZIP.
        size_bytes: Actual file size in bytes after writing to disk.
                    Targeted to fall within FILE_SIZE_PDF range (51200-512000).
        sha256:     SHA-256 hex digest (64 characters) of the PDF file
                    contents. Computed by _compute_sha256() after writing.
        artifact:   The SubmissionArtifact Pydantic model record for this PDF.
                    Ready for serialization to metadata/artifacts.csv.
    """

    filename: str
    path: Path
    size_bytes: int
    sha256: str
    artifact: SubmissionArtifact


@dataclass(frozen=True)
class GeneratedOCRImage:
    """Immutable container for a single generated OCR handwriting image.

    Represents one .png file produced by the OCR image generation pipeline.
    These are standalone images across the entire dataset, not tied to any
    specific submission. They simulate scanned handwritten student work
    that might be submitted alongside digital files.

    Created by: generate_ocr_images() in this module.
    Consumed by: generate_data.py (Step 10, collects OCR image metadata).

    Attributes:
        filename:   Name of the PNG file on disk (e.g., "ocr_001.png").
                    Zero-padded 3-digit index in the format "ocr_{NNN}.png".
        path:       Absolute Path to the PNG file on disk.
                    Located inside {output_dir}/ocr_images/.
        size_bytes: Actual file size in bytes after writing to disk.
                    Typically 100 KB - 1 MB for 1200x1600 PNG images.
        sha256:     SHA-256 hex digest (64 characters) of the PNG file
                    contents. Computed by _compute_sha256() after writing.
    """

    filename: str
    path: Path
    size_bytes: int
    sha256: str


# ── Private Helper Functions ─────────────────────────────────────────────


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 hex digest of a file's contents.

    Reads the file in 8 KB chunks to avoid loading large files entirely
    into memory. Returns a lowercase 64-character hex string.

    This is the same pattern used in submission_builder.py. A future
    refactoring could extract this into a shared utility module, but
    for now each module is self-contained following the project convention.

    Used by: generate_pdf_report() (for PDF hash),
             generate_ocr_images() (for PNG hash) in this module.

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


def _generate_report_sections(
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    rng: random.Random,
    fake: Faker,
) -> list[tuple[str, str]]:
    """Generate the text sections for a student's PDF lab report.

    Produces a list of (heading, body_text) tuples representing the
    sections of the report. The content simulates a CS1 student's
    reflection on a homework assignment, written in English.

    The three sections are:
        1. "Reflection" — 2-4 paragraphs describing the assignment experience.
        2. "What I Learned" — 1-2 paragraphs summarizing learning outcomes.
        3. "Challenges Faced" — 1-2 paragraphs describing difficulties.

    Paragraph count is randomly varied using rng to produce diverse PDF
    sizes across different students and assignments.

    Used by: _build_pdf_document() in this module (with image_buf=None for
             text-only, or image_buf set for the image-embedded variant).

    Args:
        student:    The StudentProfile (name and ID for context, though not
                    directly embedded in the section text — that's in the title).
        assignment: The AssignmentDef (title used as context for Faker text).
        attempt_no: Attempt number (unused in section text, but available
                    for future enhancements).
        rng:        Seeded Random instance for paragraph count selection.
        fake:       Seeded Faker instance for text generation.

    Returns:
        A list of 3 (heading_str, body_str) tuples. Body strings may
        contain multiple paragraphs separated by double newlines.
    """
    sections: list[tuple[str, str]] = []

    # Section 1: Reflection — the main body of the report.
    # Paragraph count varies from MIN_PARAGRAPHS (2) to MAX_PARAGRAPHS (4).
    # More paragraphs = larger PDF text content.
    num_paragraphs: int = rng.randint(MIN_PARAGRAPHS, MAX_PARAGRAPHS)
    reflection_paragraphs: list[str] = [
        fake.paragraph(nb_sentences=rng.randint(4, 8)) for _ in range(num_paragraphs)
    ]
    sections.append(("Reflection", "\n\n".join(reflection_paragraphs)))

    # Section 2: What I Learned — shorter summary section.
    num_learned: int = rng.randint(1, 2)
    learned_paragraphs: list[str] = [
        fake.paragraph(nb_sentences=rng.randint(3, 6)) for _ in range(num_learned)
    ]
    sections.append(("What I Learned", "\n\n".join(learned_paragraphs)))

    # Section 3: Challenges Faced — difficulties encountered.
    num_challenges: int = rng.randint(1, 2)
    challenges_paragraphs: list[str] = [
        fake.paragraph(nb_sentences=rng.randint(3, 6)) for _ in range(num_challenges)
    ]
    sections.append(("Challenges Faced", "\n\n".join(challenges_paragraphs)))

    return sections


def _create_pdf_flowables(
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    sections: list[tuple[str, str]],
    image_buf: io.BytesIO | None = None,
) -> list:
    """Create ReportLab flowable objects for a PDF document.

    Builds a list of Platypus flowables (Paragraph, Spacer, Image) that
    define the content and layout of the PDF. This function is called by
    _build_pdf_document() to avoid duplicating layout logic. The same
    function handles both text-only PDFs (image_buf=None) and PDFs with
    an embedded decorative image (image_buf set).

    The PDF layout contains:
        - Title block: assignment title + "Lab Report"
        - Student info: name, ID, assignment ID, attempt number
        - Each section from the sections list as heading + body paragraphs
        - (Optional) An embedded decorative image at the end

    Used by: _build_pdf_document() in this module.

    Args:
        student:    StudentProfile for the title block.
        assignment: AssignmentDef for the title block.
        attempt_no: Attempt number for the title block.
        sections:   List of (heading, body) tuples from _generate_report_sections().
        image_buf:  Optional BytesIO containing a PNG image to embed.
                    If provided, appended as an "Appendix: Diagram" section.

    Returns:
        A list of ReportLab Platypus flowable objects ready for doc.build().
    """
    styles = getSampleStyleSheet()

    # Custom styles for the lab report layout.
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontSize=18,
        spaceAfter=12,
    )
    heading_style = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontSize=14,
        spaceBefore=18,
        spaceAfter=8,
    )
    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["BodyText"],
        fontSize=11,
        leading=16,
        spaceAfter=10,
    )

    flowables: list = []

    # Title block: assignment title + "Lab Report" header.
    flowables.append(Paragraph(f"{assignment.title} - Lab Report", title_style))
    flowables.append(Spacer(1, 6))

    # Student identification information.
    flowables.append(
        Paragraph(f"Student: {student.name} ({student.student_id})", body_style)
    )
    flowables.append(
        Paragraph(
            f"Assignment: {assignment.assignment_id} | Attempt: {attempt_no}",
            body_style,
        )
    )
    flowables.append(Spacer(1, 18))

    # Render each section as a heading followed by body paragraphs.
    for heading, body in sections:
        flowables.append(Paragraph(heading, heading_style))
        # Split body into individual paragraphs (separated by double newlines).
        for para_text in body.split("\n\n"):
            stripped: str = para_text.strip()
            if stripped:
                flowables.append(Paragraph(stripped, body_style))
                flowables.append(Spacer(1, 6))

    # Optional embedded decorative image (used to reach target file size).
    if image_buf is not None:
        flowables.append(Spacer(1, 12))
        flowables.append(Paragraph("Appendix: Diagram", heading_style))
        flowables.append(Spacer(1, 6))
        # Reset BytesIO position before ReportLab reads it.
        image_buf.seek(0)
        rl_image = RLImage(image_buf, width=4 * inch, height=4 * inch)
        flowables.append(rl_image)

    return flowables


def _build_pdf_document(
    output_path: Path,
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    sections: list[tuple[str, str]],
    image_buf: io.BytesIO | None = None,
) -> None:
    """Build a PDF document from report sections using ReportLab.

    Creates a PDF file at output_path using SimpleDocTemplate with
    Platypus flowables for automatic page breaking and consistent layout.
    Uses US Letter page size (8.5 x 11 inches) with 1-inch margins.

    Used by: _build_pdf_to_target_size() in this module.

    Args:
        output_path: Absolute path where the PDF file will be written.
        student:     StudentProfile for the title page header.
        assignment:  AssignmentDef for the title page header.
        attempt_no:  Attempt number for the title page header.
        sections:    List of (heading, body) tuples from _generate_report_sections().
        image_buf:   Optional BytesIO containing a PNG image to embed.
                     If provided, appended as "Appendix: Diagram".
    """
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        leftMargin=1 * inch,
        rightMargin=1 * inch,
        topMargin=1 * inch,
        bottomMargin=1 * inch,
    )

    flowables: list = _create_pdf_flowables(
        student, assignment, attempt_no, sections, image_buf
    )
    doc.build(flowables)


def _generate_decorative_image(
    target_bytes: int,
    rng: random.Random,
) -> io.BytesIO:
    """Generate a decorative PNG image of approximately target_bytes size.

    Creates an image filled with random pixel noise overlaid with a few
    colored rectangles and lines to simulate a student-drawn diagram.
    The noise base ensures the PNG is nearly incompressible, giving
    predictable file sizes close to the target.

    Heuristic: Pure random noise PNG is approximately equal to the raw
    RGB data size (noise is incompressible). So for a target of N bytes,
    we need an image where width * height * 3 ≈ N.
    side = sqrt(N / 3) gives the correct square image dimension.

    Used by: _build_pdf_to_target_size() in this module (pass 2, when
             the text-only PDF is smaller than the target size).

    Args:
        target_bytes: Approximate desired PNG file size in bytes. The
                      actual size may vary ±20% due to PNG header
                      overhead and residual compression.
        rng:          Seeded Random instance for deterministic content.

    Returns:
        A BytesIO buffer containing the PNG image data, seeked to position 0.
    """
    # For random noise images, PNG size ≈ raw RGB data size because
    # noise is incompressible by deflate. raw_size = side * side * 3.
    # Solving for side: side = sqrt(target_bytes / 3).
    side: int = max(100, int((target_bytes / 3) ** 0.5))
    side = min(side, 3000)  # Cap at reasonable resolution to avoid memory issues.

    # Create base image from random noise bytes (incompressible by PNG).
    # randbytes() produces deterministic output from the seeded RNG.
    noise_bytes: bytes = rng.randbytes(side * side * 3)
    img = Image.frombytes("RGB", (side, side), noise_bytes)

    draw = ImageDraw.Draw(img)

    # Draw a few colored rectangles on top of the noise to make the
    # image look like a student-drawn diagram rather than pure static.
    num_shapes: int = rng.randint(3, 8)
    for _ in range(num_shapes):
        x1: int = rng.randint(0, side - 20)
        y1: int = rng.randint(0, side - 20)
        x2: int = x1 + rng.randint(20, max(21, side // 4))
        y2: int = y1 + rng.randint(20, max(21, side // 4))
        color: tuple[int, int, int] = (
            rng.randint(50, 255),
            rng.randint(50, 255),
            rng.randint(50, 255),
        )
        draw.rectangle([x1, y1, x2, y2], fill=color, outline=(0, 0, 0))

    # Draw a few lines (simulating arrows/connections between boxes).
    num_lines: int = rng.randint(3, 8)
    for _ in range(num_lines):
        x1 = rng.randint(0, side)
        y1 = rng.randint(0, side)
        x2 = rng.randint(0, side)
        y2 = rng.randint(0, side)
        draw.line([x1, y1, x2, y2], fill=(0, 0, 0), width=2)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf


def _build_pdf_to_target_size(
    output_path: Path,
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    rng: random.Random,
    fake: Faker,
    target_size: int,
) -> None:
    """Build a PDF targeting a specific file size using a two-pass approach.

    Pass 1: Generate a text-only PDF from Faker-generated sections and
            measure its size on disk.
    Pass 2: If the text PDF is smaller than target_size, compute the
            deficit and embed a Pillow-generated decorative PNG image
            to fill the remaining space. Rebuild the PDF with both
            text and the embedded image.

    This two-pass approach is necessary because plain-text ReportLab PDFs
    are typically only 5-20 KB, well below the FILE_SIZE_PDF minimum of
    50 KB. The embedded image brings the total to the target range.

    Used by: generate_pdf_report() in this module.

    Args:
        output_path: Where to write the final PDF file.
        student:     StudentProfile for header content.
        assignment:  AssignmentDef for header content.
        attempt_no:  Attempt number for header.
        rng:         Seeded Random instance for all stochastic decisions.
        fake:        Seeded Faker instance for text generation.
        target_size: Target file size in bytes, sampled from FILE_SIZE_PDF range.
    """
    # Generate text sections for the report body.
    sections: list[tuple[str, str]] = _generate_report_sections(
        student, assignment, attempt_no, rng, fake
    )

    # Pass 1: Build text-only PDF and measure its size.
    _build_pdf_document(output_path, student, assignment, attempt_no, sections)
    text_size: int = output_path.stat().st_size

    if text_size >= target_size:
        # Text alone already meets or exceeds the target (unlikely but handled).
        return

    # Pass 2: Embed a decorative image to reach target_size.
    # The deficit is the number of additional bytes needed. We apply a 0.85
    # scaling factor because embedding a PNG inside a PDF adds ~10-20%
    # overhead from PDF stream encoding.
    deficit: int = target_size - text_size
    image_target: int = int(deficit * 0.85)

    if image_target > 0:
        image_buf: io.BytesIO = _generate_decorative_image(image_target, rng)
        _build_pdf_document(
            output_path, student, assignment, attempt_no, sections, image_buf
        )


# ── OCR Image Helpers ────────────────────────────────────────────────────


def _resolve_handwriting_font(
    size: int,
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Load a handwriting-style font at the given size.

    Attempts to load MarkerFelt (primary) or Noteworthy (fallback) from
    macOS system fonts. If neither is available (e.g., on Linux CI), falls
    back to Pillow's default bitmap font.

    The three-tier fallback ensures the module works on any platform,
    though the handwriting appearance will degrade with the default font.

    Used by: _render_handwriting_image() in this module.

    Args:
        size: Font size in points (typically 18-28 for handwriting sim).

    Returns:
        A Pillow font object (FreeTypeFont for system fonts, or
        ImageFont for the default bitmap fallback).
    """
    for font_path in (_HANDWRITING_FONT_PATH, _HANDWRITING_FONT_FALLBACK):
        try:
            return ImageFont.truetype(font_path, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _generate_handwriting_text(
    fake: Faker,
    rng: random.Random,
) -> str:
    """Generate realistic handwritten-note text content for OCR images.

    Produces multi-line text simulating CS1 student notes: a header line
    with a date, followed by 8-20 lines mixing Faker sentences with
    CS1-themed code/pseudocode fragments. This mixture creates realistic
    handwritten content that an OCR system might need to process.

    The probability of inserting a CS1 fragment vs a Faker sentence is
    40%/60%, producing a natural mix of code and prose.

    Used by: generate_ocr_images() in this module.

    Args:
        fake: Seeded Faker instance for sentence generation.
        rng:  Seeded Random instance for line count and content selection.

    Returns:
        A multi-line string with lines separated by newline characters.
    """
    lines: list[str] = []

    # Header: course name and date (simulates notebook page header).
    lines.append(f"CS1 Notes - {fake.date_this_year()}")
    lines.append("")

    # Body: mix of CS1 code fragments and Faker English sentences.
    num_lines: int = rng.randint(8, 20)
    for _ in range(num_lines):
        if rng.random() < 0.4:
            # Insert a CS1-themed code/pseudocode fragment.
            lines.append(rng.choice(_CS1_FRAGMENTS))
        else:
            # Insert a Faker-generated English sentence.
            lines.append(fake.sentence(nb_words=rng.randint(5, 12)))

    return "\n".join(lines)


def _render_handwriting_image(
    text: str,
    rng: random.Random,
) -> Image.Image:
    """Render text onto an image simulating handwritten notes on paper.

    Creates a white/off-white background image (simulating scanned paper)
    and draws text line-by-line with visual variations to simulate natural
    handwriting:
        - Per-line font size variation (18-28pt)
        - Horizontal jitter for each line start (-5 to +10 pixels)
        - Dark blue/black ink color variation per line
        - Slight rotation after rendering (-3 to +3 degrees)
        - Optional Gaussian blur (50% chance, radius 0.5)

    The rendering stops if text would overflow the bottom margin,
    ensuring all content stays within the image bounds.

    Used by: generate_ocr_images() in this module.

    Args:
        text: Multi-line text from _generate_handwriting_text().
        rng:  Seeded Random instance for all visual variation decisions.

    Returns:
        A Pillow Image object (RGB mode, OCR_IMAGE_WIDTH x OCR_IMAGE_HEIGHT)
        containing the rendered handwriting simulation.
    """
    # Off-white background color simulating scanned paper.
    # Slight random variation in RGB channels for realism.
    bg_color: tuple[int, int, int] = (
        rng.randint(240, 255),
        rng.randint(240, 255),
        rng.randint(235, 250),
    )
    img = Image.new("RGB", (OCR_IMAGE_WIDTH, OCR_IMAGE_HEIGHT), bg_color)
    draw = ImageDraw.Draw(img)

    # Draw text line by line with handwriting-style visual variation.
    y_pos: int = 60  # Top margin in pixels.
    lines: list[str] = text.split("\n")

    for line in lines:
        if not line.strip():
            # Blank line: add vertical spacing (simulates paragraph break).
            y_pos += 20
            continue

        # Vary font size per line to simulate inconsistent writing pressure.
        font_size: int = rng.randint(
            HANDWRITING_FONT_SIZE_MIN, HANDWRITING_FONT_SIZE_MAX
        )
        font = _resolve_handwriting_font(font_size)

        # Slight horizontal jitter for each line start (simulates uneven margins).
        x_pos: int = 40 + rng.randint(-5, 10)

        # Ink color: dark blue-black with slight per-line variation.
        # Simulates different pen pressure and ink flow.
        ink_color: tuple[int, int, int] = (
            rng.randint(0, 30),
            rng.randint(0, 30),
            rng.randint(40, 100),
        )

        draw.text((x_pos, y_pos), line, fill=ink_color, font=font)
        # Line spacing: font height + random gap (simulates uneven line spacing).
        y_pos += font_size + rng.randint(8, 18)

        # Stop rendering if we've run out of vertical space (bottom margin).
        if y_pos > OCR_IMAGE_HEIGHT - 80:
            break

    # Apply slight rotation to simulate imperfect scanner alignment.
    rotation_angle: float = rng.uniform(-MAX_ROTATION_DEGREES, MAX_ROTATION_DEGREES)
    img = img.rotate(
        rotation_angle, resample=Image.BICUBIC, expand=False, fillcolor=bg_color
    )

    # Apply optional Gaussian blur for slight softening (50% probability).
    # Simulates print/scan quality degradation.
    if rng.random() < 0.5:
        img = img.filter(ImageFilter.GaussianBlur(radius=0.5))

    return img


def _add_noise_to_image(
    img: Image.Image,
    rng: random.Random,
) -> Image.Image:
    """Add sparse speckle noise to an image to simulate scanner artifacts.

    Draws small randomly-placed dots (200-500 spots) on the image to
    simulate dust, paper imperfections, and scanner artifacts. This
    approach produces realistic scanned-paper appearance while keeping
    the PNG file compressible (unlike full-image noise blending which
    would defeat PNG's deflate compression entirely).

    The spots are small gray/dark ellipses (1-3 pixel radius) scattered
    randomly across the image, simulating the kind of imperfections seen
    in flatbed scans of handwritten documents.

    Used by: generate_ocr_images() after _render_handwriting_image().

    Args:
        img: The source image to add noise to (RGB mode).
             Modified in-place and returned (Pillow draw mutates the image).
        rng: Seeded Random instance for deterministic noise placement.

    Returns:
        The same Image object with speckle noise added.
    """
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Add sparse dust/speckle spots. The count (200-500) produces a
    # subtle but visible scanned-paper appearance without significantly
    # increasing PNG file size (large uniform areas remain compressible).
    num_spots: int = rng.randint(200, 500)
    for _ in range(num_spots):
        x: int = rng.randint(0, width - 1)
        y: int = rng.randint(0, height - 1)
        # Gray spots simulating paper imperfections and dust particles.
        gray: int = rng.randint(100, 200)
        radius: int = rng.randint(1, 3)
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=(gray, gray, gray),
        )

    return img


# ── Public Functions ─────────────────────────────────────────────────────


def generate_pdf_report(
    student: StudentProfile,
    assignment: AssignmentDef,
    attempt_no: int,
    submission_id: uuid.UUID,
    submission_dir: Path,
    rng: random.Random,
) -> GeneratedPDFReport:
    """Generate a PDF lab report for a single student submission.

    Creates a PDF document containing the student's simulated reflection
    on the assignment, writes it to submission_dir, computes its SHA-256
    hash and file size, and returns a GeneratedPDFReport with both the
    file metadata and a SubmissionArtifact Pydantic model record.

    This function should only be called when student.generates_pdf is True.
    The caller (generate_data.py) is responsible for checking this flag
    before calling this function.

    The PDF filename follows the convention:
        {student_id}_{assignment_id}_attempt{N}_report.pdf
    Example: "S001_HW1_attempt1_report.pdf"

    File size is targeted within FILE_SIZE_PDF range (50-500 KB) using
    a two-pass strategy: first build a text-only PDF, then embed a
    decorative image if the text alone is insufficient.

    Used by: generate_data.py (Step 10, called once per submission for
             students with generates_pdf=True)

    Args:
        student:        StudentProfile for report content and header.
        assignment:     AssignmentDef for report header and context.
        attempt_no:     Which attempt (1-3) this report accompanies.
        submission_id:  UUID of the parent Submission. Used to create
                        the SubmissionArtifact foreign key reference.
        submission_dir: Path to the submission directory where the PDF
                        will be written (same dir as the ZIP bundle).
                        Must already exist (created by build_submission).
        rng:            Seeded Random instance for all stochastic
                        decisions (paragraph count, target size, etc.).
                        Must be created via config.create_rng().

    Returns:
        A frozen GeneratedPDFReport containing the filename, path, size,
        SHA-256 hash, and SubmissionArtifact record.

    Example::

        from make_simul_data.seed_data.config import create_rng

        rng = create_rng(42)
        if student.generates_pdf:
            pdf_report = generate_pdf_report(
                student, assignment, 1, submission.submission_id,
                submission_dir, rng
            )
            # pdf_report.artifact is a SubmissionArtifact ready for CSV export
    """
    # Create a seeded Faker instance for deterministic text generation.
    # Derive the seed from rng to ensure reproducibility while allowing
    # each call to get a different Faker sequence.
    fake = Faker()
    fake.seed_instance(rng.randint(0, 2**31))

    # Compute filename following the project naming convention.
    filename: str = (
        f"{student.student_id}_{assignment.assignment_id}"
        f"_attempt{attempt_no}_report.pdf"
    )
    output_path: Path = submission_dir / filename

    # Select a target file size within FILE_SIZE_PDF range (51200-512000 bytes).
    min_pdf, max_pdf = FILE_SIZE_PDF
    target_size: int = rng.randint(min_pdf, max_pdf)

    # Build the PDF to the target size using the two-pass strategy.
    _build_pdf_to_target_size(
        output_path, student, assignment, attempt_no, rng, fake, target_size
    )

    # Compute metadata from the written file.
    actual_size: int = output_path.stat().st_size
    sha256: str = _compute_sha256(output_path)

    # Create the SubmissionArtifact Pydantic model record.
    artifact = SubmissionArtifact(
        submission_id=submission_id,
        artifact_type=ArtifactType.PDF_REPORT,
        filename=filename,
        filetype=MIME_PDF,
        sha256=sha256,
        size_bytes=actual_size,
    )

    return GeneratedPDFReport(
        filename=filename,
        path=output_path,
        size_bytes=actual_size,
        sha256=sha256,
        artifact=artifact,
    )


def generate_ocr_images(
    output_dir: Path | None = None,
    rng: random.Random | None = None,
    count: int = OCR_IMAGE_COUNT,
) -> list[GeneratedOCRImage]:
    """Generate a batch of handwriting-simulation OCR PNG images.

    Creates ``count`` PNG images (default: 100) simulating scanned
    handwritten student notes. Each image features:
        - Handwriting-style text rendered with MarkerFelt/Noteworthy font
        - Per-line font size variation (18-28pt)
        - Slight rotation (-3 to +3 degrees)
        - Sparse speckle noise (200-500 random spots simulating scanner dust)
        - Dark blue/black ink color variation

    Images are written to ``{output_dir}/ocr_images/`` and named
    ``ocr_{NNN}.png`` (e.g., "ocr_001.png" through "ocr_100.png").

    These are standalone images not tied to any individual submission.
    The caller (generate_data.py) may optionally create SubmissionArtifact
    records for them during Step 10 integration.

    Used by: generate_data.py (Step 10, called once to generate the
             entire batch of OCR images for the dataset)

    Args:
        output_dir: Base output directory. If None, uses ASSIGNMENTS_DIR
                    from config.py. OCR images are placed in a subdirectory
                    named OCR_OUTPUT_DIRNAME ("ocr_images").
        rng:        Seeded Random instance. If None, creates one from
                    MASTER_SEED via create_rng().
        count:      Number of images to generate. Default: OCR_IMAGE_COUNT (100).
                    Pass 0 to generate no images (returns empty list).

    Returns:
        A list of GeneratedOCRImage instances, one per generated PNG file.
        Returns an empty list if count is 0.

    Example::

        from make_simul_data.seed_data.config import create_rng

        rng = create_rng(42)
        ocr_images = generate_ocr_images(rng=rng, count=10)
        assert len(ocr_images) == 10
        assert all(img.path.exists() for img in ocr_images)
    """
    if count <= 0:
        return []

    if rng is None:
        rng = create_rng()

    # Determine output directory and ensure it exists.
    base_dir: Path = output_dir if output_dir is not None else ASSIGNMENTS_DIR
    ocr_dir: Path = base_dir / OCR_OUTPUT_DIRNAME
    ocr_dir.mkdir(parents=True, exist_ok=True)

    # Create a seeded Faker instance for text generation.
    fake = Faker()
    fake.seed_instance(rng.randint(0, 2**31))

    images: list[GeneratedOCRImage] = []

    for i in range(1, count + 1):
        # Filename: zero-padded 3-digit index (e.g., "ocr_001.png").
        filename: str = f"ocr_{i:03d}.png"
        file_path: Path = ocr_dir / filename

        # Step 1: Generate handwriting text content (CS1 fragments + Faker).
        text: str = _generate_handwriting_text(fake, rng)

        # Step 2: Render text onto image with handwriting simulation.
        img: Image.Image = _render_handwriting_image(text, rng)

        # Step 3: Add scanner noise overlay.
        img = _add_noise_to_image(img, rng)

        # Step 4: Save as PNG.
        img.save(file_path, format="PNG")

        # Step 5: Compute file metadata.
        actual_size: int = file_path.stat().st_size
        sha256: str = _compute_sha256(file_path)

        images.append(
            GeneratedOCRImage(
                filename=filename,
                path=file_path,
                size_bytes=actual_size,
                sha256=sha256,
            )
        )

    return images
