"""CLI orchestrator for the seed data generation pipeline.

Wires all 9 pipeline modules together into a single command-line entry
point that generates a complete simulated CS1 course dataset: student
profiles, code submissions, ZIP bundles, PDF reports, OCR images,
grading results, plagiarism analysis, manifests, and CSV metadata.

Usage (from make_simul_data/ directory):
    python generate_data.py                  # Default (100 students, 5 HWs)
    python generate_data.py --students 50 --assignments 3  # Smaller run
    python generate_data.py --seed 42 --output-dir out/    # Custom settings
    python generate_data.py --validate-only                # Run validation only
    python generate_data.py -v                             # Verbose logging

Or from project root:
    python -m make_simul_data.generate_data

Module dependency graph (imports from every pipeline module):
    config.py            -> SeedDataConfig, create_rng, OUTPUT_ROOT,
                            MASTER_SEED, NUM_STUDENTS, NUM_ASSIGNMENTS,
                            SubmissionStatus
    models.py            -> SubmissionArtifact (type hint for PDF list)
    students.py          -> generate_students, StudentProfile, get_attempt_count
    assignments.py       -> ASSIGNMENTS
    code_generator.py    -> generate_code_files
    submission_builder.py -> build_submission, SubmissionBundle
    report_generator.py  -> generate_pdf_report, generate_ocr_images
    grading_engine.py    -> simulate_grading, GradingOutcome
    plagiarism.py        -> generate_plagiarism_pairs, PlagiarismResult
    manifest.py          -> generate_manifest, write_manifest
    validator.py         -> validate_all, ValidationResult
"""

from __future__ import annotations

import argparse
import logging
import statistics
import sys
import time
from pathlib import Path
from typing import Any

import pandas as pd

from make_simul_data.seed_data.assignments import ASSIGNMENTS
from make_simul_data.seed_data.code_generator import generate_code_files
from make_simul_data.seed_data.config import (
    MASTER_SEED,
    NUM_ASSIGNMENTS,
    NUM_STUDENTS,
    OUTPUT_ROOT,
    SeedDataConfig,
    SubmissionStatus,
    create_rng,
)
from make_simul_data.seed_data.grading_engine import (
    GradingOutcome,
    simulate_grading,
)
from make_simul_data.seed_data.manifest import (
    generate_manifest,
    write_manifest,
)
from make_simul_data.seed_data.models import SubmissionArtifact
from make_simul_data.seed_data.plagiarism import (
    PlagiarismResult,
    generate_plagiarism_pairs,
)
from make_simul_data.seed_data.report_generator import (
    GeneratedOCRImage,
    generate_ocr_images,
    generate_pdf_report,
)
from make_simul_data.seed_data.students import (
    StudentProfile,
    generate_students,
    get_attempt_count,
)
from make_simul_data.seed_data.submission_builder import (
    SubmissionBundle,
    build_submission,
)
from make_simul_data.seed_data.validator import (
    ValidationResult,
    validate_all,
)

# ── Module Logger ───────────────────────────────────────────────────────
# Standard Python logger for this module. Log level is controlled by the
# -v / --verbose CLI flag via _configure_logging().
# Used by: every function in this module for progress and debug output.
logger: logging.Logger = logging.getLogger(__name__)

# ── RNG Seed Offsets ────────────────────────────────────────────────────
# Each pipeline stage gets a unique seed derived from MASTER_SEED + offset
# to ensure reproducibility and isolation between stages. Changing one
# stage's RNG sequence does not affect any other stage.
# Used by: run_pipeline() when creating per-stage and per-attempt RNGs.

# Offset for student profile generation (generate_students).
_RNG_OFFSET_STUDENTS: int = 0

# Offset for Python code file generation (generate_code_files).
_RNG_OFFSET_CODE_GEN: int = 1000

# Offset for ZIP bundle and submission building (build_submission).
_RNG_OFFSET_SUBMISSION: int = 2000

# Offset for PDF lab report generation (generate_pdf_report).
_RNG_OFFSET_PDF_REPORT: int = 3000

# Offset for grading simulation (simulate_grading).
_RNG_OFFSET_GRADING: int = 4000

# Offset for plagiarism pair generation (generate_plagiarism_pairs).
_RNG_OFFSET_PLAGIARISM: int = 5000

# Offset for OCR handwriting image generation (generate_ocr_images).
_RNG_OFFSET_OCR: int = 6000

# ── Relative Path Segments ──────────────────────────────────────────────
# Subdirectory names under output_root for metadata CSVs and assignment
# submission files. These match the structure expected by validator.py.

# Relative path from output_root to the metadata CSV directory.
# Used by: run_pipeline() to create and pass the metadata output directory.
_METADATA_REL: str = "metadata"

# Relative path from output_root to the assignments directory containing
# per-student submission folders.
# Used by: run_pipeline() to pass the assignments base directory to
#          build_submission() and generate_ocr_images().
_ASSIGNMENTS_REL: str = str(Path("intro_cs") / "Assignments")


# ── CLI Argument Parsing ────────────────────────────────────────────────


def build_arg_parser() -> argparse.ArgumentParser:
    """Build and return the CLI argument parser for generate_data.py.

    Defines all command-line options with defaults matching config.py
    constants. Supports --students, --assignments, --seed, --output-dir,
    --validate-only, and --verbose flags.

    Used by: main() to parse sys.argv.

    Returns:
        A configured argparse.ArgumentParser instance ready for
        parse_args().
    """
    parser = argparse.ArgumentParser(
        description=(
            "Generate simulated CS1 course seed data for the Agentic TA system."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python generate_data.py                                "
            "# Default (100 students, 5 assignments)\n"
            "  python generate_data.py --students 50 --assignments 3  "
            "# Smaller test run\n"
            "  python generate_data.py --validate-only                "
            "# Validate existing data\n"
            "  python generate_data.py -v --seed 123                  "
            "# Verbose, custom seed\n"
        ),
    )
    parser.add_argument(
        "--students",
        type=int,
        default=NUM_STUDENTS,
        help=f"Number of students to generate (default: {NUM_STUDENTS}).",
    )
    parser.add_argument(
        "--assignments",
        type=int,
        default=NUM_ASSIGNMENTS,
        help=(
            f"Number of assignments to generate, 1-{len(ASSIGNMENTS)} "
            f"(default: {NUM_ASSIGNMENTS})."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=MASTER_SEED,
        help=f"Master random seed for reproducibility (default: {MASTER_SEED}).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_ROOT,
        help=f"Root output directory (default: {OUTPUT_ROOT}).",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        default=False,
        help="Skip generation; only run validation on existing data.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        default=False,
        help="Enable verbose (DEBUG) logging output.",
    )
    return parser


# ── Logging Configuration ───────────────────────────────────────────────


def _configure_logging(verbose: bool) -> None:
    """Configure the root logger based on the verbose flag.

    Sets the logging level to DEBUG when verbose is True, otherwise INFO.
    Output is directed to stdout with a timestamp, level, and module prefix.

    Used by: main() at startup before any pipeline work begins.

    Args:
        verbose: If True, set level to DEBUG for detailed trace output;
                 otherwise set to INFO for progress-only output.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
        stream=sys.stdout,
    )


# ── Argument Validation ─────────────────────────────────────────────────


def _validate_args(args: argparse.Namespace) -> None:
    """Validate CLI arguments for logical consistency.

    Checks that --students >= 1 and --assignments is within the valid
    range [1, len(ASSIGNMENTS)]. Exits with a descriptive error message
    if any check fails.

    Used by: main() immediately after argument parsing.

    Args:
        args: Parsed command-line arguments from argparse.

    Raises:
        SystemExit: If any argument is out of valid range.
    """
    if args.students < 1:
        print("Error: --students must be >= 1.", file=sys.stderr)
        sys.exit(1)
    if args.assignments < 1 or args.assignments > len(ASSIGNMENTS):
        print(
            f"Error: --assignments must be between 1 and {len(ASSIGNMENTS)}.",
            file=sys.stderr,
        )
        sys.exit(1)


# ── CSV Metadata Export ─────────────────────────────────────────────────


def export_csv_metadata(
    students: list[StudentProfile],
    bundles: list[SubmissionBundle],
    grading_outcomes: list[GradingOutcome],
    plagiarism_result: PlagiarismResult,
    metadata_dir: Path,
) -> None:
    """Export all pipeline metadata to 7 CSV files using pandas.

    Creates one CSV file per database table in the metadata directory.
    Pydantic models are serialized via model_dump(mode="json") which
    automatically converts UUID and datetime fields to strings.
    StudentProfile (a frozen dataclass) is manually converted to dicts.

    Note: PDF artifacts are NOT passed as a separate parameter because
    they are already merged into bundle.artifacts via SubmissionBundle
    reconstruction in run_pipeline() Stage 4c. All artifact types
    (python_file, zip_bundle, pdf_report) are exported from bundles.

    Used by: run_pipeline() after all generation stages complete.

    Args:
        students:          All generated StudentProfile instances.
                           Written to: students.csv.
        bundles:           All SubmissionBundle instances from the main loop.
                           PDF artifacts are already merged into
                           bundle.artifacts via bundle reconstruction.
                           Used for: submissions.csv, submission_artifacts.csv.
        grading_outcomes:  All GradingOutcome instances from grading simulation.
                           Used for: execution_results.csv, test_case_results.csv,
                           submission_tags.csv.
        plagiarism_result: PlagiarismResult from plagiarism simulation.
                           Used for: similarity_scores.csv, submission_tags.csv
                           (merged with grading tags).
        metadata_dir:      Path to the metadata output directory. Must already
                           exist (created by run_pipeline Stage 1).

    CSV files created (names must match validator.py expectations):
        - students.csv
        - submissions.csv
        - submission_artifacts.csv
        - execution_results.csv
        - test_case_results.csv
        - submission_tags.csv
        - similarity_scores.csv
    """
    # 1. students.csv — StudentProfile is a frozen dataclass (not Pydantic),
    #    so we manually extract the fields needed for the CSV.
    student_records: list[dict[str, Any]] = [
        {
            "student_id": s.student_id,
            "name": s.name,
            "email": s.email,
            "skill_level": round(s.skill_level, 4),
            "is_late_submitter": s.is_late_submitter,
            "generates_pdf": s.generates_pdf,
        }
        for s in students
    ]
    pd.DataFrame(student_records).to_csv(metadata_dir / "students.csv", index=False)
    logger.info("Wrote students.csv (%d rows).", len(student_records))

    # 2. submissions.csv — Pydantic Submission model auto-serializes
    #    UUID to string and datetime to ISO 8601 via model_dump(mode="json").
    submission_records: list[dict[str, Any]] = [
        bundle.submission.model_dump(mode="json") for bundle in bundles
    ]
    pd.DataFrame(submission_records).to_csv(
        metadata_dir / "submissions.csv", index=False
    )
    logger.info("Wrote submissions.csv (%d rows).", len(submission_records))

    # 3. submission_artifacts.csv — Merge artifacts from bundles (python_file
    #    + zip_bundle) with PDF report artifacts. Note: PDF artifacts were
    #    already merged into bundle.artifacts via bundle reconstruction in
    #    run_pipeline(), so we only need to iterate bundle.artifacts here.
    artifact_records: list[dict[str, Any]] = []
    for bundle in bundles:
        for artifact in bundle.artifacts:
            artifact_records.append(artifact.model_dump(mode="json"))
    pd.DataFrame(artifact_records).to_csv(
        metadata_dir / "submission_artifacts.csv", index=False
    )
    logger.info("Wrote submission_artifacts.csv (%d rows).", len(artifact_records))

    # 4. execution_results.csv — One ExecutionResult per submission.
    exec_records: list[dict[str, Any]] = [
        outcome.execution_result.model_dump(mode="json") for outcome in grading_outcomes
    ]
    pd.DataFrame(exec_records).to_csv(
        metadata_dir / "execution_results.csv", index=False
    )
    logger.info("Wrote execution_results.csv (%d rows).", len(exec_records))

    # 5. test_case_results.csv — Flatten the per-submission test case tuples
    #    into a single list of records. N test cases per submission where N
    #    is determined by the assignment's num_test_cases.
    test_case_records: list[dict[str, Any]] = []
    for outcome in grading_outcomes:
        for tc_result in outcome.test_case_results:
            test_case_records.append(tc_result.model_dump(mode="json"))
    pd.DataFrame(test_case_records).to_csv(
        metadata_dir / "test_case_results.csv", index=False
    )
    logger.info("Wrote test_case_results.csv (%d rows).", len(test_case_records))

    # 6. submission_tags.csv — Merge tags from two sources:
    #    a) grading_engine tags (CLEAN, EXCELLENT, LATE_SUBMISSION)
    #    b) plagiarism tags (PLAGIARISM_SUSPECT, CORRUPTED)
    tag_records: list[dict[str, Any]] = []
    for outcome in grading_outcomes:
        for tag in outcome.tags:
            tag_records.append(tag.model_dump(mode="json"))
    for tag in plagiarism_result.tags:
        tag_records.append(tag.model_dump(mode="json"))
    pd.DataFrame(tag_records).to_csv(metadata_dir / "submission_tags.csv", index=False)
    logger.info("Wrote submission_tags.csv (%d rows).", len(tag_records))

    # 7. similarity_scores.csv — All pairwise similarity comparisons
    #    (both flagged plagiarism pairs and background comparisons).
    sim_records: list[dict[str, Any]] = [
        score.model_dump(mode="json") for score in plagiarism_result.similarity_scores
    ]
    pd.DataFrame(sim_records).to_csv(
        metadata_dir / "similarity_scores.csv", index=False
    )
    logger.info("Wrote similarity_scores.csv (%d rows).", len(sim_records))


# ── Validation Results Printer ──────────────────────────────────────────


def _print_validation_results(results: list[ValidationResult]) -> None:
    """Print validation results in a human-readable format.

    Displays each validation check's pass/fail status and message,
    followed by a summary count of passed and failed checks.

    Used by: run_pipeline() and _run_validate_only() after calling
             validate_all().

    Args:
        results: List of ValidationResult instances from validate_all().
    """
    passed: int = sum(1 for r in results if r.passed)
    failed: int = sum(1 for r in results if not r.passed)

    print(f"\nValidation: {passed} passed, {failed} failed")
    for r in results:
        status_label = "PASS" if r.passed else "FAIL"
        print(f"  [{status_label}] {r.check_name}: {r.message}")

    if failed > 0:
        logger.warning("Validation completed with %d failure(s).", failed)


# ── Summary Statistics Printer ──────────────────────────────────────────


def _print_summary(
    students: list[StudentProfile],
    bundles: list[SubmissionBundle],
    grading_outcomes: list[GradingOutcome],
    pdf_artifacts: list[SubmissionArtifact],
    plagiarism_result: PlagiarismResult,
    ocr_images: list[GeneratedOCRImage],
    validation_results: list[ValidationResult],
    num_assignments: int,
) -> None:
    """Print human-readable summary statistics to stdout.

    Displays key metrics about the generated dataset including counts,
    score distributions, submission status breakdown, plagiarism stats,
    and validation results.

    Used by: run_pipeline() as the final output step.

    Args:
        students:            All generated student profiles.
        bundles:             All submission bundles from the main loop.
        grading_outcomes:    All grading outcomes from grading simulation.
        pdf_artifacts:       All PDF SubmissionArtifact instances.
        plagiarism_result:   Plagiarism simulation results.
        ocr_images:          All generated OCR image instances.
        validation_results:  Validation check results.
        num_assignments:     Number of assignments used in this run.
    """
    # Compute score statistics from all grading outcomes.
    scores: list[float] = [o.total_score for o in grading_outcomes]

    # Count total artifacts across all bundles (includes python_file,
    # zip_bundle, and pdf_report types that were merged into bundles).
    total_artifacts: int = sum(len(b.artifacts) for b in bundles)

    # Count submissions by status (on_time vs late).
    on_time_count: int = sum(
        1 for b in bundles if b.submission.status == SubmissionStatus.ON_TIME
    )
    late_count: int = sum(
        1 for b in bundles if b.submission.status == SubmissionStatus.LATE
    )
    total_submissions: int = len(bundles)

    # Validation summary.
    val_passed: int = sum(1 for r in validation_results if r.passed)
    val_failed: int = sum(1 for r in validation_results if not r.passed)

    print("\n" + "=" * 48)
    print("  SEED DATA GENERATION SUMMARY")
    print("=" * 48)
    print(f"Students:            {len(students)}")
    print(f"Assignments:         {num_assignments}")
    print(f"Total submissions:   {total_submissions}")
    print(f"Total artifacts:     {total_artifacts}")

    if scores:
        print("\nScore statistics:")
        print(f"  Mean:    {statistics.mean(scores):>7.2f}")
        print(f"  Median:  {statistics.median(scores):>7.2f}")
        print(f"  Min:     {min(scores):>7.2f}")
        print(f"  Max:     {max(scores):>7.2f}")
        # statistics.stdev() requires at least 2 data points.
        if len(scores) >= 2:
            print(f"  Std:     {statistics.stdev(scores):>7.2f}")
        else:
            print("  Std:        N/A (need >= 2 samples)")

    print("\nSubmission status breakdown:")
    if total_submissions > 0:
        on_time_pct = on_time_count / total_submissions * 100
        late_pct = late_count / total_submissions * 100
        print(f"  on_time: {on_time_count:>5} ({on_time_pct:.1f}%)")
        print(f"  late:    {late_count:>5} ({late_pct:.1f}%)")

    print("\nPlagiarism:")
    print(f"  Pairs flagged:     " f"{len(plagiarism_result.plagiarism_pairs)}")
    print(f"  Similarity scores: " f"{len(plagiarism_result.similarity_scores)}")
    print(f"  Corrupted files:   " f"{len(plagiarism_result.corrupted_ids)}")

    print(f"\nPDF reports generated: {len(pdf_artifacts)}")
    print(f"OCR images generated:  {len(ocr_images)}")

    print("\nValidation:")
    print(f"  Passed: {val_passed}")
    print(f"  Failed: {val_failed}")
    print("=" * 48)


# ── Validate-Only Mode ──────────────────────────────────────────────────


def _run_validate_only(output_dir: Path) -> None:
    """Run only the validation step on existing generated data.

    Skips all generation stages and directly calls validate_all() on
    the specified output directory. Exits with code 1 if any validation
    check fails, code 0 if all pass.

    Used by: main() when --validate-only flag is set.

    Args:
        output_dir: Root output directory containing the previously
                    generated seed data. Must have the expected
                    subdirectory structure (intro_cs/Assignments/,
                    metadata/).
    """
    logger.info("Running validation only on: %s", output_dir)
    results: list[ValidationResult] = validate_all(output_dir=output_dir)
    _print_validation_results(results)

    failed: int = sum(1 for r in results if not r.passed)
    if failed > 0:
        sys.exit(1)
    else:
        print("\nAll validation checks passed.")


# ── Main Pipeline Orchestration ─────────────────────────────────────────


def run_pipeline(config: SeedDataConfig) -> dict[str, Any]:
    """Execute the full seed data generation pipeline.

    This is the core orchestration function that calls all 9 pipeline
    modules in the correct sequence. It generates student profiles,
    iterates over (student x assignment x attempt) triples to produce
    code files, ZIP bundles, PDF reports, and grading results, then
    generates OCR images, plagiarism analysis, manifests, CSV metadata,
    and runs validation.

    Used by: main() after argument parsing and configuration.

    Args:
        config: Immutable SeedDataConfig with all pipeline parameters
                (num_students, num_assignments, master_seed, output_root).

    Returns:
        A dictionary containing all collected pipeline data for
        potential programmatic use:
            "students":          list[StudentProfile]
            "bundles":           list[SubmissionBundle]
            "grading_outcomes":  list[GradingOutcome]
            "pdf_artifacts":     list[SubmissionArtifact]
            "plagiarism_result": PlagiarismResult
            "ocr_images":        list[GeneratedOCRImage]
    """
    # ── Stage 1: Create output directories ──────────────────────────
    # Ensure the metadata and assignments directories exist before any
    # module attempts to write files.
    output_root: Path = config.output_root
    metadata_dir: Path = output_root / _METADATA_REL
    assignments_dir: Path = output_root / _ASSIGNMENTS_REL
    metadata_dir.mkdir(parents=True, exist_ok=True)
    assignments_dir.mkdir(parents=True, exist_ok=True)
    logger.info("Output directories created under: %s", output_root)

    # ── Stage 2: Generate student profiles ──────────────────────────
    # Creates NUM_STUDENTS StudentProfile instances with Faker-generated
    # identities, Beta-distributed skill levels, and pre-computed
    # attempt counts per assignment.
    students: list[StudentProfile] = generate_students(
        num=config.num_students,
        seed=config.master_seed + _RNG_OFFSET_STUDENTS,
        num_assignments=config.num_assignments,
    )
    logger.info("Generated %d student profiles.", len(students))

    # ── Stage 3: Determine active assignments ───────────────────────
    # Slice the full ASSIGNMENTS tuple to respect --assignments flag.
    # If num_assignments < 5, only HW1..HW{N} are used. This works
    # because ASSIGNMENTS is ordered HW1-HW5 and generate_students()
    # received the same num_assignments for attempt_counts generation.
    active_assignments = ASSIGNMENTS[: config.num_assignments]
    logger.info(
        "Using %d assignments: %s",
        len(active_assignments),
        [a.assignment_id for a in active_assignments],
    )

    # ── Stage 4: Main triple loop ───────────────────────────────────
    # Iterate over every (student, assignment, attempt) combination.
    # For each triple, generate code files, build ZIP bundle, optionally
    # generate PDF report, and simulate grading.

    # Accumulator lists for metadata CSV export and downstream stages.
    # all_bundles: SubmissionBundle instances including reconstructed
    #              bundles with PDF artifacts merged in.
    # all_grading_outcomes: GradingOutcome instances for all submissions.
    # all_pdf_artifacts: SubmissionArtifact records for PDF reports only,
    #                    tracked separately for the summary statistics.
    all_bundles: list[SubmissionBundle] = []
    all_grading_outcomes: list[GradingOutcome] = []
    all_pdf_artifacts: list[SubmissionArtifact] = []

    for student_idx, student in enumerate(students):
        for assign_idx, assignment in enumerate(active_assignments):
            # Look up the pre-computed attempt count for this
            # student-assignment pair (1, 2, or 3).
            num_attempts: int = get_attempt_count(student, assignment.assignment_id)

            for attempt_no in range(1, num_attempts + 1):
                # Derive a unique seed for this specific submission attempt.
                # Formula: master_seed + stage_offset + student_idx * 1000
                #          + assign_idx * 100 + attempt_no
                # Guarantees reproducible, isolated RNG per triple.
                attempt_seed: int = (
                    config.master_seed
                    + _RNG_OFFSET_CODE_GEN
                    + student_idx * 1000
                    + assign_idx * 100
                    + attempt_no
                )

                # Stage 4a: Generate Python code files for this submission.
                # Returns 1 file for HW1-HW3, 2 files for HW4-HW5.
                code_rng = create_rng(attempt_seed)
                code_files = generate_code_files(
                    student, assignment, attempt_no, code_rng
                )

                # Stage 4b: Build ZIP bundle + Submission record.
                # Creates the submission directory on disk, writes .py files,
                # creates ZIP archive, computes SHA-256 hashes, and returns
                # the frozen SubmissionBundle.
                sub_rng = create_rng(attempt_seed + _RNG_OFFSET_SUBMISSION)
                bundle = build_submission(
                    student,
                    assignment,
                    attempt_no,
                    code_files,
                    sub_rng,
                    output_dir=assignments_dir,
                )

                # Stage 4c: Generate PDF report if student generates PDFs.
                # PDF artifact is merged into the bundle so that
                # generate_manifest() includes it in manifest.json.
                if student.generates_pdf:
                    pdf_rng = create_rng(attempt_seed + _RNG_OFFSET_PDF_REPORT)
                    pdf_report = generate_pdf_report(
                        student,
                        assignment,
                        attempt_no,
                        bundle.submission.submission_id,
                        bundle.submission_dir,
                        pdf_rng,
                    )
                    all_pdf_artifacts.append(pdf_report.artifact)

                    # Reconstruct the frozen bundle with PDF artifact added.
                    # SubmissionBundle is frozen, so we create a new instance
                    # with the extended artifacts tuple.
                    bundle = SubmissionBundle(
                        submission=bundle.submission,
                        artifacts=bundle.artifacts + (pdf_report.artifact,),
                        code_files=bundle.code_files,
                        zip_path=bundle.zip_path,
                        submission_dir=bundle.submission_dir,
                    )

                all_bundles.append(bundle)

                # Stage 4d: Simulate grading for this submission.
                # Produces ExecutionResult, TestCaseResults, SubmissionTags,
                # and total_score without executing any student code.
                grading_rng = create_rng(attempt_seed + _RNG_OFFSET_GRADING)
                is_late: bool = bundle.submission.status == SubmissionStatus.LATE
                outcome: GradingOutcome = simulate_grading(
                    student,
                    assignment,
                    bundle.submission.submission_id,
                    attempt_no,
                    grading_rng,
                    is_late=is_late,
                    submitted_at=bundle.submission.submitted_at,
                )
                all_grading_outcomes.append(outcome)

                logger.debug(
                    "  %s / %s / attempt %d -> score=%.1f, status=%s",
                    student.student_id,
                    assignment.assignment_id,
                    attempt_no,
                    outcome.total_score,
                    bundle.submission.status,
                )

        # Log progress every 10 students for user feedback during long runs.
        if (student_idx + 1) % 10 == 0:
            logger.info(
                "Progress: %d/%d students processed.",
                student_idx + 1,
                len(students),
            )

    logger.info(
        "Main loop complete: %d submissions, %d grading outcomes.",
        len(all_bundles),
        len(all_grading_outcomes),
    )

    # ── Stage 5: Generate OCR images ────────────────────────────────
    # Creates 100 standalone PNG images simulating handwritten notes.
    # These are not tied to individual submissions.
    ocr_rng = create_rng(config.master_seed + _RNG_OFFSET_OCR)
    ocr_images: list[GeneratedOCRImage] = generate_ocr_images(
        output_dir=assignments_dir,
        rng=ocr_rng,
        count=100,
    )
    logger.info("Generated %d OCR images.", len(ocr_images))

    # ── Stage 6: Generate plagiarism pairs + corrupted files ────────
    # Selects ~10% of submissions for plagiarism simulation and ~3%
    # for corruption tagging. Produces SimilarityScore records and
    # SubmissionTag records for PLAGIARISM_SUSPECT and CORRUPTED.
    plag_rng = create_rng(config.master_seed + _RNG_OFFSET_PLAGIARISM)
    plagiarism_result: PlagiarismResult = generate_plagiarism_pairs(
        all_bundles, plag_rng
    )
    logger.info(
        "Plagiarism: %d similarity scores, %d tags, " "%d corrupted, %d pairs.",
        len(plagiarism_result.similarity_scores),
        len(plagiarism_result.tags),
        len(plagiarism_result.corrupted_ids),
        len(plagiarism_result.plagiarism_pairs),
    )

    # ── Stage 7: Write manifests ────────────────────────────────────
    # Generate and write a manifest.json file for each submission bundle.
    # Each manifest lists the submission's artifacts with filenames,
    # types, SHA-256 hashes, and sizes.
    for bundle in all_bundles:
        manifest = generate_manifest(bundle)
        write_manifest(manifest, bundle.submission_dir)
    logger.info("Wrote %d manifest.json files.", len(all_bundles))

    # ── Stage 8: Export CSV metadata ────────────────────────────────
    # Write 7 CSV files to the metadata directory using pandas.
    export_csv_metadata(
        students=students,
        bundles=all_bundles,
        grading_outcomes=all_grading_outcomes,
        plagiarism_result=plagiarism_result,
        metadata_dir=metadata_dir,
    )
    logger.info("CSV metadata exported to %s.", metadata_dir)

    # ── Stage 9: Run validation ─────────────────────────────────────
    # Execute all 6 QA validation checks on the generated data.
    validation_results: list[ValidationResult] = validate_all(output_dir=output_root)
    _print_validation_results(validation_results)

    # ── Stage 10: Print summary statistics ──────────────────────────
    _print_summary(
        students=students,
        bundles=all_bundles,
        grading_outcomes=all_grading_outcomes,
        pdf_artifacts=all_pdf_artifacts,
        plagiarism_result=plagiarism_result,
        ocr_images=ocr_images,
        validation_results=validation_results,
        num_assignments=config.num_assignments,
    )

    return {
        "students": students,
        "bundles": all_bundles,
        "grading_outcomes": all_grading_outcomes,
        "pdf_artifacts": all_pdf_artifacts,
        "plagiarism_result": plagiarism_result,
        "ocr_images": ocr_images,
    }


# ── CLI Entry Point ─────────────────────────────────────────────────────


def main() -> None:
    """Entry point for the seed data generation CLI.

    Parses command-line arguments, configures logging, validates inputs,
    and dispatches to either the full generation pipeline or
    validation-only mode. Reports total elapsed time at completion.

    Used by: ``if __name__ == "__main__"`` guard and
             ``python -m make_simul_data.generate_data`` module execution.
    """
    parser = build_arg_parser()
    args = parser.parse_args()

    _configure_logging(args.verbose)
    _validate_args(args)

    start_time: float = time.time()

    # Handle --validate-only mode: skip all generation, run QA only.
    if args.validate_only:
        _run_validate_only(args.output_dir)
        elapsed = time.time() - start_time
        print(f"\nTotal time: {elapsed:.1f} seconds")
        return

    # Build the immutable configuration object from CLI arguments.
    # SeedDataConfig is a frozen dataclass that bundles all top-level
    # parameters and is passed to run_pipeline().
    config = SeedDataConfig(
        master_seed=args.seed,
        num_students=args.students,
        num_assignments=args.assignments,
        output_root=args.output_dir,
    )

    logger.info("Starting seed data generation with config:")
    logger.info("  Students:    %d", config.num_students)
    logger.info("  Assignments: %d", config.num_assignments)
    logger.info("  Seed:        %d", config.master_seed)
    logger.info("  Output:      %s", config.output_root)

    # Run the full generation pipeline.
    run_pipeline(config)

    elapsed = time.time() - start_time
    print(f"\nTotal time: {elapsed:.1f} seconds")


if __name__ == "__main__":
    main()
