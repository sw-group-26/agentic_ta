"""Central configuration for seed data generation.

This module serves as the single source of truth for all constants, enums,
and configuration dataclasses used across the seed data generation pipeline.

Every other module in ``make_simul_data.seed_data`` imports from here,
so changes to this file propagate throughout the entire pipeline.

Module dependency graph (downstream consumers):
    config.py  -->  models.py       (Pydantic models reference StrEnums)
               -->  students.py     (uses NUM_STUDENTS, create_rng)
               -->  assignments.py  (uses AssignmentDef, NUM_ASSIGNMENTS)
               -->  code_generator.py      (uses FILE_SIZE_PYTHON, ArtifactType)
               -->  submission_builder.py  (uses FILE_SIZE_ZIP, ASSIGNMENTS_DIR)
               -->  report_generator.py    (uses FILE_SIZE_PDF, ArtifactType)
               -->  grading_engine.py      (uses PASS_RATES, SCORE_*,
                                                RUNTIME_*)
               -->  plagiarism.py   (uses SimilarityMethod, TagType, TagSource)
               -->  manifest.py     (uses OUTPUT_ROOT, METADATA_DIR)
               -->  validator.py    (uses ASSIGNMENTS_DIR, METADATA_DIR,
                                         FILE_SIZE_*, NUM_*, LATE_RATE,
                                         SUBMISSION_DISTRIBUTION, ArtifactType)
               -->  generate_data.py (uses SeedDataConfig as the top-level config)
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path

# ── Global Constants ─────────────────────────────────────────────────────

# Master random seed for full pipeline reproducibility.
# Passed to create_rng() to produce deterministic random.Random instances.
# Used by: every generation module (students, assignments, grading, etc.)
MASTER_SEED: int = 42

# Total number of simulated students to generate.
# Each student gets an ID like "S001" through "S100".
# Used by: students.py (to create student records),
#          generate_data.py (main loop iterates over students)
NUM_STUDENTS: int = 100

# Total number of homework assignments in the simulated course.
# Each assignment gets an ID like "HW1" through "HW5".
# Used by: assignments.py (to define assignment metadata),
#          generate_data.py (main loop iterates over assignments)
NUM_ASSIGNMENTS: int = 5

# Probability distribution for how many submission attempts each student
# makes per assignment.
#   Key   = number of attempts (1, 2, or 3)
#   Value = probability of that attempt count
# Example: 60% of students submit once, 30% submit twice, 10% submit 3 times.
# Used by: generate_data.py (to sample attempt counts per student-assignment pair)
SUBMISSION_DISTRIBUTION: dict[int, float] = {1: 0.60, 2: 0.30, 3: 0.10}

# Fraction of non-missing submissions that arrive after the due date.
# A value of 0.20 means 20% of submissions are marked as "late".
# Used by: generate_data.py (when assigning SubmissionStatus to each submission),
#          students.py (to set StudentProfile.is_late_submitter flag)
LATE_RATE: float = 0.20

# Fraction of students who submit PDF lab reports alongside their code.
# A value of 0.40 means approximately 40% of students generate PDF write-ups.
# Used by: students.py (to set StudentProfile.generates_pdf flag),
#          report_generator.py (to decide whether to generate a PDF artifact)
PDF_GENERATION_RATE: float = 0.40

# Base probabilities for test-case pass outcomes, as a 3-tuple:
#   (all_pass, partial_pass, all_fail)
# These base rates are adjusted per student based on their skill level.
# Example: a high-skill student has boosted all_pass probability.
# Used by: grading.py (to simulate test case pass/fail results)
PASS_RATES: tuple[float, float, float] = (0.75, 0.20, 0.05)

# ── Score Distribution ───────────────────────────────────────────────────

# Shape parameters for the Beta distribution used to generate scores.
#   Beta(alpha=5, beta=2) produces a left-skewed distribution
#   with raw mean ~0.714 (i.e., scores cluster toward the high end).
# The raw [0,1] value is scaled to [0, max_score] and then adjusted
# by student skill level to target a class-wide mean of roughly 80%.
# Used by: grading.py (random.betavariate(SCORE_ALPHA, SCORE_BETA))
SCORE_ALPHA: float = 5.0
SCORE_BETA: float = 2.0

# ── Runtime Simulation ───────────────────────────────────────────────────

# Minimum simulated code execution time in milliseconds.
# Successful runs are sampled uniformly from [RUNTIME_MIN_MS, RUNTIME_MAX_MS].
# Used by: grading.py (to populate ExecutionResult.runtime_ms)
RUNTIME_MIN_MS: int = 100

# Maximum simulated code execution time in milliseconds for normal runs.
# Used by: grading.py (upper bound for successful execution runtime)
RUNTIME_MAX_MS: int = 2_000

# Simulated timeout threshold in milliseconds.
# When a submission's ExecutionStatus is TIMEOUT, runtime_ms is set to this value.
# Mirrors the SRS requirement of a 30-second execution time limit.
# Used by: grading.py (to set runtime_ms for timed-out submissions)
TIMEOUT_MS: int = 30_000

# ── File Size Ranges (bytes) ─────────────────────────────────────────────

# Min and max file sizes for generated Python source files (1 KB - 10 KB).
# A random size within this range is assigned to each SubmissionArtifact
# of type "python_file".
# Used by: code_gen.py (to determine generated .py file byte count),
#          models.py (SubmissionArtifact.size_bytes)
FILE_SIZE_PYTHON: tuple[int, int] = (1_024, 10_240)  # 1-10 KB

# Min and max file sizes for generated ZIP bundle artifacts (100 KB - 300 KB).
# Each submission is packaged into a ZIP containing the .py file(s) and
# optionally a PDF report.
# Used by: zip_gen.py (to create ZIP archives with realistic sizes)
FILE_SIZE_ZIP: tuple[int, int] = (102_400, 307_200)  # 100-300 KB

# Min and max file sizes for generated PDF report artifacts (50 KB - 500 KB).
# PDF reports contain simulated student write-ups using ReportLab.
# Used by: pdf_gen.py (to generate PDF files with realistic sizes)
FILE_SIZE_PDF: tuple[int, int] = (51_200, 512_000)  # 50-500 KB

# ── Output Paths ─────────────────────────────────────────────────────────

# Root directory for all generated seed data output.
# All generated files (ZIPs, PDFs, metadata CSVs, manifests) live under here.
# Used by: every generation module that writes files to disk,
#          SeedDataConfig.output_root defaults to this value
OUTPUT_ROOT: Path = Path("make_simul_data") / "output" / "seed_data"

# Directory for metadata CSV/JSON files (submissions.csv, artifacts.csv, etc.).
# These tabular files are used for database seeding and analytics testing.
# Used by: generate_data.py (to write consolidated metadata files)
METADATA_DIR: Path = OUTPUT_ROOT / "metadata"

# Directory for per-assignment submission folders.
# Structure: ASSIGNMENTS_DIR / "HW1" / "S001" / "attempt1" / files...
# Mirrors a realistic course file system layout.
# Used by: submission_builder.py (to organize submission ZIP files per assignment),
#          code_generator.py, report_generator.py (to place generated artifacts),
#          validator.py (to locate manifest.json files for QA checks)
ASSIGNMENTS_DIR: Path = OUTPUT_ROOT / "intro_cs" / "Assignments"

# ── Semester Timeline ────────────────────────────────────────────────────

# ISO 8601 start date of the simulated semester.
# Used by: assignments.py (to compute assignment due dates spaced across
#          the semester), generate_data.py (to generate submitted_at timestamps)
SEMESTER_START: str = "2026-01-12"

# ISO 8601 end date of the simulated semester.
# Used by: assignments.py (upper bound for due date generation)
SEMESTER_END: str = "2026-04-30"


# ── StrEnums ─────────────────────────────────────────────────────────────
# All enums inherit from StrEnum so their values serialize directly as
# strings in JSON/CSV output without needing .value calls.


class SubmissionStatus(StrEnum):
    """Status of a student submission relative to the due date.

    Used by: models.py (Submission.status field validator),
             generate_data.py (to assign status when creating submissions)

    Values:
        ON_TIME:  Submitted before or on the due date.
        LATE:     Submitted after the due date (controlled by LATE_RATE).
        MISSING:  Student did not submit for this assignment.
    """

    ON_TIME = "on_time"
    LATE = "late"
    MISSING = "missing"


class ArtifactType(StrEnum):
    """Types of file artifacts that can be attached to a submission.

    Each submission may contain one or more artifacts of different types.
    Used by: models.py (SubmissionArtifact.artifact_type field validator),
             code_gen.py (PYTHON_FILE), zip_gen.py (ZIP_BUNDLE),
             pdf_gen.py (PDF_REPORT), ocr generation (OCR_IMAGE)

    Values:
        PYTHON_FILE:  A .py source code file submitted by the student.
        ZIP_BUNDLE:   A .zip archive containing all submission files.
        PDF_REPORT:   A .pdf document (lab report, write-up, etc.).
        OCR_IMAGE:    A scanned image (.png/.jpg) of handwritten work,
                      processed by OCR to extract text.
    """

    PYTHON_FILE = "python_file"
    ZIP_BUNDLE = "zip_bundle"
    PDF_REPORT = "pdf_report"
    OCR_IMAGE = "ocr_image"


class ExecutionStatus(StrEnum):
    """Outcome status of running a student's submitted code.

    Used by: models.py (ExecutionResult.status field validator),
             grading.py (to simulate execution outcomes based on skill level)

    Values:
        SUCCESS:            Code ran without errors and exited with code 0.
        RUNTIME_ERROR:      Code crashed during execution (e.g., exception).
        TIMEOUT:            Code exceeded the TIMEOUT_MS limit and was killed.
        COMPILATION_ERROR:  Code failed to parse/compile (syntax errors).
    """

    SUCCESS = "success"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    COMPILATION_ERROR = "compilation_error"


class TagType(StrEnum):
    """Classification tags applied to submissions for filtering and analysis.

    Multiple tags can be applied to a single submission. Tags are used
    by the Agentic TA system for automated triage and quality flagging.
    Used by: models.py (SubmissionTag.tag field validator),
             generate_data.py (to assign tags based on submission properties)

    Values:
        CLEAN:              Submission passed all checks, no issues detected.
        PLAGIARISM_SUSPECT: Similarity score exceeded the threshold (see
                            SimilarityScore model). Requires manual review.
        CORRUPTED:          Submission file is damaged or cannot be processed.
        LATE_SUBMISSION:    Submitted after the due date. Auto-tagged when
                            SubmissionStatus is LATE.
        EXCELLENT:          High-quality submission scoring above 90%.
    """

    CLEAN = "clean"
    PLAGIARISM_SUSPECT = "plagiarism_suspect"
    CORRUPTED = "corrupted"
    LATE_SUBMISSION = "late_submission"
    EXCELLENT = "excellent"


class TagSource(StrEnum):
    """Origin of a submission tag — how the tag was assigned.

    Used by: models.py (SubmissionTag.source field validator),
             generate_data.py (all simulated tags use AUTOMATED)

    Values:
        AUTOMATED:  Tag was assigned by the automated grading pipeline.
        MANUAL:     Tag was assigned manually by a TA or instructor.
    """

    AUTOMATED = "automated"
    MANUAL = "manual"


class SimilarityMethod(StrEnum):
    """Algorithm used to compute code similarity between two submissions.

    Used by: models.py (SimilarityScore.method field validator),
             similarity.py (to simulate pairwise similarity checks)

    Values:
        TOKEN_BASED:  Compares lexical token sequences (similar to MOSS).
        AST_BASED:    Compares abstract syntax tree structures for
                      deeper semantic similarity detection.
        TEXT_BASED:   Simple text diff / edit-distance comparison
                      using rapidfuzz library.
    """

    TOKEN_BASED = "token_based"
    AST_BASED = "ast_based"
    TEXT_BASED = "text_based"


# ── Frozen Dataclasses ───────────────────────────────────────────────────
# Frozen (immutable) dataclasses ensure configuration objects cannot be
# accidentally modified after creation, providing thread-safety guarantees.


@dataclass(frozen=True)
class AssignmentDef:
    """Immutable definition of a single homework assignment.

    Instances of this class are created in assignments.py and define the
    metadata for each of the NUM_ASSIGNMENTS homework assignments. They
    are consumed by the main generation loop in generate_data.py to
    determine due dates, scoring rules, and expected submission files.

    Used by: assignments.py (creates a list of AssignmentDef instances),
             generate_data.py (iterates over assignments to generate
             submissions, execution results, and test case results),
             grading.py (uses max_score and num_test_cases for scoring)

    Attributes:
        assignment_id:  Unique identifier string (e.g., "HW1", "HW2").
                        Used as a foreign key in Submission records.
        title:          Human-readable assignment title
                        (e.g., "Variables and Data Types").
        description:    Brief description of the assignment's learning
                        objectives and tasks.
        due_date:       ISO 8601 date string (e.g., "2026-02-14").
                        Used to compute submitted_at timestamps and
                        determine on_time vs late status.
        max_score:      Maximum possible points for the assignment
                        (e.g., 100). Scores are generated in [0, max_score].
        num_test_cases: Number of automated test cases for this assignment.
                        Each test case produces a TestCaseResult record.
        difficulty:     Difficulty rating from 1 (easiest) to 5 (hardest).
                        Affects score distribution — harder assignments
                        have lower mean scores and more failures.
        required_files: Tuple of filenames the student must submit
                        (e.g., ("main.py",) or ("solution.py", "utils.py")).
                        Used by code_gen.py to generate matching files.
    """

    assignment_id: str
    title: str
    description: str
    due_date: str
    max_score: int
    num_test_cases: int
    difficulty: int
    required_files: tuple[str, ...]


@dataclass(frozen=True)
class SeedDataConfig:
    """Master configuration container for the entire seed data generation pipeline.

    This is an immutable, thread-safe configuration object that bundles all
    top-level parameters needed by the generation pipeline into a single
    object. It is instantiated once in generate_data.py and passed down
    to all generation functions.

    By centralizing configuration here, we avoid scattering magic numbers
    across multiple modules and make it easy to create alternative configs
    for testing (e.g., a smaller dataset with 10 students).

    Used by: generate_data.py (instantiated as the top-level config object),
             all generation modules receive this via function parameters

    Attributes:
        master_seed:             Random seed for full reproducibility.
                                 Passed to create_rng() to produce
                                 deterministic random number generators.
                                 Default: MASTER_SEED (42).
        num_students:            Number of simulated students to generate.
                                 Default: NUM_STUDENTS (100).
        num_assignments:         Number of homework assignments to generate.
                                 Default: NUM_ASSIGNMENTS (5).
        submission_distribution: Probability map for attempt counts.
                                 Keys are attempt counts (1, 2, 3),
                                 values are probabilities (must sum to 1.0).
                                 Default: SUBMISSION_DISTRIBUTION.
        late_rate:               Fraction of submissions marked as late.
                                 Default: LATE_RATE (0.20 = 20%).
        output_root:             Root directory for all generated output.
                                 Default: OUTPUT_ROOT.
    """

    master_seed: int = MASTER_SEED
    num_students: int = NUM_STUDENTS
    num_assignments: int = NUM_ASSIGNMENTS
    submission_distribution: dict[int, float] = field(
        default_factory=lambda: dict(SUBMISSION_DISTRIBUTION)
    )
    late_rate: float = LATE_RATE
    output_root: Path = OUTPUT_ROOT


# ── Utility Functions ────────────────────────────────────────────────────


def create_rng(seed: int | None = None) -> random.Random:
    """Create an isolated Random instance for reproducible random generation.

    This factory function is the ONLY way random number generators should
    be created in the seed data pipeline. Using isolated ``random.Random``
    instances (instead of the global ``random`` module functions) ensures:

    1. **Reproducibility**: Given the same seed, the same sequence of
       random numbers is always produced, regardless of call order.
    2. **Parallel safety**: Each module/function gets its own RNG instance,
       so concurrent or reordered calls don't affect each other's sequences.
    3. **Testability**: Tests can create RNG instances with known seeds
       to verify deterministic output.

    Used by: students.py (to generate student IDs and skill levels),
             assignments.py (to vary assignment parameters),
             code_gen.py (to generate random code content),
             grading.py (to simulate scores and pass/fail outcomes),
             plagiarism.py (to generate pairwise similarity scores),
             generate_data.py (to create per-module RNG instances
             derived from MASTER_SEED)

    Args:
        seed: Integer seed value for the RNG. If None, defaults to
              MASTER_SEED (42) for consistent pipeline-wide behavior.

    Returns:
        A seeded ``random.Random`` instance, independent of the global
        random state.

    Example::

        rng = create_rng(42)
        student_skill = rng.uniform(0.3, 1.0)  # deterministic result
    """
    return random.Random(seed if seed is not None else MASTER_SEED)
