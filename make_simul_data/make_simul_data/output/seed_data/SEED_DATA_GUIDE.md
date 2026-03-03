# Agentic TA - Seed Data Reference Guide

> **Generated:** 2026-03-02
> **Author:** Wonbum Sohn
> **Master Seed:** 42 (deterministic — same seed always reproduces the exact same dataset)

---

## Table of Contents

1. [Overview](#1-overview)
2. [Quick Start](#2-quick-start)
3. [Output Directory Structure](#3-output-directory-structure)
4. [CSV Metadata Reference](#4-csv-metadata-reference)
5. [Entity Relationship Diagram](#5-entity-relationship-diagram)
6. [Assignment Definitions](#6-assignment-definitions)
7. [Generation Parameters](#7-generation-parameters)
8. [Plagiarism and Corruption Simulation](#8-plagiarism-and-corruption-simulation)
9. [Manifest Schema](#9-manifest-schema)
10. [Validation Checks](#10-validation-checks)
11. [Notes for DB Engineers](#11-notes-for-db-engineers)
12. [Notes for UI and LLM Engineers](#12-notes-for-ui-and-llm-engineers)

---

## 1. Overview

This dataset is a **fully synthetic** simulation of student submissions for an **Intro to Computer Science (CS1)** course. It was generated to serve as seed data for developing and testing the Agentic TA system — an AI-powered teaching assistant platform.

### Dataset at a Glance

| Metric | Value |
|--------|-------|
| Students | 100 |
| Assignments | 5 (HW1 through HW5) |
| Total submissions | 754 |
| Total file artifacts | 2,150 |
| Execution results | 6,372 |
| Test case results | 5,538 |
| Submission tags | 1,535 |
| Similarity comparisons | 164 |
| PDF lab reports | 334 |
| OCR handwriting images | 100 |
| Total disk size | ~262 MB |

### What This Data Represents

The dataset simulates a realistic semester where:

- **100 students** with varying skill levels submit homework assignments.
- Each student may submit **1 to 3 attempts** per assignment (60% submit once, 30% twice, 10% three times).
- Each submission includes **Python source code**, a **ZIP archive**, and optionally a **PDF lab report**.
- An **automated grading system** evaluates each submission, producing execution results, per-test-case scores, and classification tags.
- **~10% of submissions** have simulated plagiarism (copied code with variable renaming, dead code insertion, and reformatting).
- **~3% of submissions** are intentionally corrupted (broken ZIP files, encoding errors).

### Reproducibility

Every random value in this dataset is derived from `MASTER_SEED = 42` using isolated, per-stage random number generators. Running the pipeline with the same seed produces **byte-identical** output.

---

## 2. Quick Start

### Regenerating the Dataset

From the project root:

```bash
# Install dependencies (one-time)
pip install -e ".[seed]"

# Generate full dataset (100 students x 5 assignments, ~60 seconds)
cd make_simul_data
python generate_data.py --seed 42

# Generate a smaller test dataset
python generate_data.py --students 10 --assignments 2

# Run validation only (no generation)
python generate_data.py --validate-only

# Verbose mode (DEBUG logging)
python generate_data.py -v
```

### CLI Arguments

| Argument | Default | Description |
|----------|---------|-------------|
| `--students N` | 100 | Number of simulated students |
| `--assignments N` | 5 | Number of assignments (1-5) |
| `--seed N` | 42 | Master random seed for reproducibility |
| `--output-dir PATH` | `make_simul_data/output/seed_data` | Output root directory |
| `--validate-only` | off | Skip generation, run QA validation only |
| `-v, --verbose` | off | Enable DEBUG-level logging |

---

## 3. Output Directory Structure

```
seed_data/                              # Root output directory
|
+-- SEED_DATA_GUIDE.md                  # This file
|
+-- metadata/                           # CSV tables (structured metadata)
|   +-- students.csv                    #   100 student profiles
|   +-- submissions.csv                 #   754 submission records
|   +-- submission_artifacts.csv        #   2,150 file artifact records
|   +-- execution_results.csv           #   6,372 code execution results
|   +-- test_case_results.csv           #   5,538 per-test-case outcomes
|   +-- submission_tags.csv             #   1,535 classification tags
|   +-- similarity_scores.csv           #   164 plagiarism comparison scores
|
+-- intro_cs/                           # Course namespace
    +-- Assignments/                    # All assignment directories
        +-- HW1/                        # Assignment 1: Variables, I/O, Arithmetic
        |   +-- S001/                   # Student S001's submissions
        |   |   +-- attempt1/           # First attempt
        |   |   |   +-- hw1_solution.py           # Python source code
        |   |   |   +-- S001_HW1_attempt1.zip     # ZIP bundle (contains .py + padding files)
        |   |   |   +-- S001_HW1_attempt1_report.pdf  # PDF lab report (if student generates PDFs)
        |   |   |   +-- manifest.json             # Artifact inventory with SHA-256 checksums
        |   |   +-- attempt2/           # Second attempt (if applicable)
        |   |   +-- attempt3/           # Third attempt (if applicable)
        |   +-- S002/
        |   +-- ...
        |   +-- S100/
        +-- HW2/                        # Assignment 2: Conditionals
        +-- HW3/                        # Assignment 3: Loops
        +-- HW4/                        # Assignment 4: Functions (includes hw4_utils.py)
        +-- HW5/                        # Assignment 5: Lists (includes hw5_utils.py)
        +-- ocr_images/                 # 100 standalone OCR handwriting simulation PNGs
            +-- ocr_001.png
            +-- ocr_002.png
            +-- ...
            +-- ocr_100.png
```

### File Descriptions

| File/Directory | Description |
|---------------|-------------|
| `metadata/*.csv` | Structured tabular data for database import. Each CSV has a header row followed by data rows. |
| `HW{N}/S{NNN}/attempt{M}/` | Per-student, per-attempt directory. Path encodes assignment ID, student ID, and attempt number. |
| `hw{n}_solution.py` | Main Python source file for the assignment. Quality varies by student skill level. |
| `hw{n}_utils.py` | Helper module (HW4 and HW5 only). Contains utility functions imported by the solution. |
| `S{NNN}_HW{N}_attempt{M}.zip` | ZIP archive containing the Python source files plus realistic padding files (e.g., `__pycache__/`, `.vscode/settings.json`, `notes.txt`). |
| `S{NNN}_HW{N}_attempt{M}_report.pdf` | PDF lab report with student reflection. Only present for ~40% of students. |
| `manifest.json` | Machine-readable inventory of all artifacts in the attempt directory, with SHA-256 checksums and file sizes. |
| `ocr_images/ocr_{NNN}.png` | Simulated handwritten notes as PNG images. Not tied to individual submissions — standalone artifacts for OCR testing. |

### Naming Conventions

- **Student IDs**: `S001` through `S100` (zero-padded to 3 digits)
- **Assignment IDs**: `HW1` through `HW5`
- **Attempt numbers**: `1`, `2`, or `3`
- **ZIP files**: `{student_id}_{assignment_id}_attempt{N}.zip`
- **PDF files**: `{student_id}_{assignment_id}_attempt{N}_report.pdf`
- **Python files**: `hw{n}_solution.py` (and `hw{n}_utils.py` for HW4-HW5)

---

## 4. CSV Metadata Reference

All CSV files use UTF-8 encoding with a header row. UUIDs are formatted as lowercase hyphenated strings (e.g., `cbca2439-5fa7-4a69-b4d5-57515f2ca8df`). Timestamps are in ISO 8601 UTC format (e.g., `2026-01-28T04:52:51Z`).

### 4.1 students.csv

**Rows:** 100 (one per student)

| Column | Type | Description | Example |
|--------|------|-------------|---------|
| `student_id` | STRING | Unique student identifier. Format: `S` + 3-digit zero-padded number. | `S001` |
| `name` | STRING | Realistic fake name (generated by Faker library). | `Allison Hill` |
| `email` | STRING | Realistic fake email address. | `donaldgarcia@example.net` |
| `skill_level` | FLOAT | Student's programming ability on a 0.0-1.0 scale. Drawn from Beta(5, 2) distribution (mean ~0.714, right-skewed — most students are above average). | `0.8412` |
| `is_late_submitter` | BOOLEAN | Whether the student tends to submit late. 20% of students are flagged `True`. | `True` |
| `generates_pdf` | BOOLEAN | Whether the student submits PDF lab reports. 40% are `True`. | `True` |

**Sample Row:**
```
S001,Allison Hill,donaldgarcia@example.net,0.8412,True,True
```

---

### 4.2 submissions.csv

**Rows:** 754 (one per student-assignment-attempt combination)

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `submission_id` | UUID | Unique identifier for this submission attempt. **Primary key.** | `cbca2439-5fa7-...` |
| `student_id` | STRING | FK to `students.csv`. | `S001` - `S100` |
| `assignment_id` | STRING | Which homework assignment. | `HW1`, `HW2`, `HW3`, `HW4`, `HW5` |
| `attempt_no` | INTEGER | Attempt number for this student-assignment pair. | `1`, `2`, or `3` |
| `submitted_at` | DATETIME | When the student submitted (UTC, ISO 8601). | `2026-01-28T04:52:51Z` |
| `due_at` | DATETIME | Assignment due date (UTC, always at 23:59:00). | `2026-01-30T23:59:00Z` |
| `status` | STRING | Submission timeliness. | `on_time`, `late` |

**Sample Row:**
```
cbca2439-5fa7-4a69-b4d5-57515f2ca8df,S001,HW1,1,2026-01-28T04:52:51Z,2026-01-30T23:59:00Z,on_time
```

**Notes:**
- `status = "on_time"` means `submitted_at <= due_at`.
- `status = "late"` means `submitted_at > due_at` (up to 48 hours after).
- ~93% of submissions are on-time; ~7% are late.

---

### 4.3 submission_artifacts.csv

**Rows:** 2,150 (multiple artifacts per submission)

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `artifact_id` | UUID | Unique identifier for this file artifact. **Primary key.** | UUID string |
| `submission_id` | UUID | FK to `submissions.csv`. | UUID string |
| `artifact_type` | STRING | Category of the artifact. | `python_file`, `zip_bundle`, `pdf_report` |
| `filename` | STRING | Name of the file on disk. | `hw1_solution.py`, `S001_HW1_attempt1.zip` |
| `filetype` | STRING | MIME type of the file. | `text/x-python`, `application/zip`, `application/pdf` |
| `sha256` | STRING | SHA-256 hash of the file contents (64-char lowercase hex). | `cb143497cec24a7b...` |
| `size_bytes` | INTEGER | File size in bytes. | See ranges below |

**File Size Ranges:**

| Artifact Type | MIME Type | Min Size | Max Size |
|--------------|-----------|----------|----------|
| `python_file` | `text/x-python` | 1,024 B (1 KB) | 10,240 B (10 KB) |
| `zip_bundle` | `application/zip` | 102,400 B (100 KB) | 307,200 B (300 KB) |
| `pdf_report` | `application/pdf` | 51,200 B (50 KB) | 512,000 B (500 KB) |

**Notes:**
- Every submission has at least one `python_file` and one `zip_bundle`.
- HW4 and HW5 submissions have two `python_file` artifacts (solution + utils).
- `pdf_report` is present only if the student's `generates_pdf` flag is `True` (~40% of students).
- SHA-256 hashes can be verified against the corresponding `manifest.json`.

---

### 4.4 execution_results.csv

**Rows:** 6,372 (one per submission, but each row can be very long due to stdout/stderr)

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `exec_id` | UUID | Unique execution result identifier. **Primary key.** | UUID string |
| `submission_id` | UUID | FK to `submissions.csv`. | UUID string |
| `started_at` | DATETIME | When code execution started (UTC). | ISO 8601 |
| `finished_at` | DATETIME | When execution ended (UTC). | ISO 8601 |
| `status` | STRING | Execution outcome. | `success`, `runtime_error`, `timeout`, `compilation_error` |
| `exit_code` | INTEGER | Simulated process exit code. | `0` (success), `1` (runtime_error), `-1` (timeout), `2` (compilation_error) |
| `stdout` | STRING | Simulated standard output (test results). | Multi-line text, e.g. `"Test 1: PASS\nTest 2: PASS..."` |
| `stderr` | STRING | Simulated standard error (error messages). | Empty string or error traceback |
| `runtime_ms` | INTEGER | Simulated execution time in milliseconds. | See ranges below |

**Execution Time Ranges:**

| Status | Runtime Range | Notes |
|--------|--------------|-------|
| `success` | 100 - 2,000 ms | Log-normal distribution |
| `runtime_error` | 100 - 2,000 ms | Log-normal distribution |
| `timeout` | 30,000 ms (fixed) | ~2% of all-fail scenarios |
| `compilation_error` | 10 - 100 ms | Uniform distribution (fails fast) |

**Notes:**
- The `stdout` field contains formatted test results like `"Test 1: PASS\nTest 2: FAIL\nExpected: 32.0\nGot: 31.0"`.
- The `stderr` field contains error messages like `"NameError: name 'x' is not defined"` for runtime errors, or `"SyntaxError: invalid syntax (line 15)"` for compilation errors.
- These are **simulated** — no actual code was executed. Results are probabilistically generated based on student skill level and assignment difficulty.

---

### 4.5 test_case_results.csv

**Rows:** 5,538 (5-8 test cases per submission depending on assignment)

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `test_id` | UUID | Unique test result identifier. **Primary key.** | UUID string |
| `exec_id` | UUID | FK to `execution_results.csv`. | UUID string |
| `test_case_id` | STRING | Identifies which test case. Format: `HW{N}_TC{NN}`. | `HW1_TC01`, `HW5_TC08` |
| `passed` | BOOLEAN | Whether the test case passed. | `True`, `False` |
| `score_awarded` | FLOAT | Points earned for this test case. 0.0 if failed, full points if passed. | `0.0` - `20.0` |
| `output` | STRING | Brief test output. | `"PASS"` or `"Expected: 32.0, Got: 31.0"` |

**Points Per Test Case (each assignment totals 100 points):**

| Assignment | Test Cases | Points Distribution |
|-----------|------------|-------------------|
| HW1 | 5 tests (TC01-TC05) | 20 + 20 + 20 + 20 + 20 = 100 |
| HW2 | 6 tests (TC01-TC06) | 17 + 17 + 17 + 16 + 16 + 16 = 99* |
| HW3 | 7 tests (TC01-TC07) | 15 + 15 + 14 + 14 + 14 + 14 + 14 = 100 |
| HW4 | 8 tests (TC01-TC08) | 13 + 13 + 12 + 12 + 12 + 12 + 13 + 13 = 100 |
| HW5 | 8 tests (TC01-TC08) | 13 + 13 + 12 + 12 + 12 + 12 + 13 + 13 = 100 |

*\*HW2 sums to 99 due to integer rounding; the total awarded score is still normalized to 100.*

---

### 4.6 submission_tags.csv

**Rows:** 1,535 (zero or more tags per submission)

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `submission_id` | UUID | FK to `submissions.csv`. | UUID string |
| `tag` | STRING | Classification label. | See tag types below |
| `source` | STRING | How the tag was assigned. | `automated` (all tags in this dataset) |
| `confidence` | FLOAT | Confidence level of the tag assignment. | `0.0` - `1.0` |

**Tag Types:**

| Tag | Meaning | Trigger | Confidence Range |
|-----|---------|---------|-----------------|
| `clean` | No issues detected. | Execution succeeds with no negative flags. | 0.85 - 1.0 |
| `excellent` | Exceptional performance. | Total score >= 90 out of 100. | 0.95 - 1.0 |
| `late_submission` | Submitted after deadline. | `submitted_at > due_at`. | 1.0 (always certain) |
| `plagiarism_suspect` | Possible plagiarism detected. | Part of a high-similarity pair (>= 80%). | 0.85 - 0.99 |
| `corrupted` | Submission file is damaged. | Intentionally corrupted ZIP or encoding error. | 0.70 - 1.0 |

**Notes:**
- A submission can have **multiple tags** (e.g., both `excellent` and `late_submission`).
- `clean` and `plagiarism_suspect` / `corrupted` are mutually exclusive — a submission flagged as plagiarized or corrupted will not receive a `clean` tag.

---

### 4.7 similarity_scores.csv

**Rows:** 164 (pairwise comparisons between submissions)

| Column | Type | Description | Values / Range |
|--------|------|-------------|----------------|
| `sim_id` | UUID | Unique comparison identifier. **Primary key.** | UUID string |
| `submission_id` | UUID | First submission in the pair. FK to `submissions.csv`. | UUID string |
| `compared_to` | UUID | Second submission in the pair. FK to `submissions.csv`. | UUID string |
| `method` | STRING | Similarity algorithm used. | `ast_based`, `token_based`, `text_based` |
| `similarity_pct` | FLOAT | Similarity percentage. | `0.0` - `100.0` |
| `flagged` | BOOLEAN | Whether this pair is flagged as suspicious. | `True` if `similarity_pct >= 80.0` |

**Similarity Methods:**

| Method | Description |
|--------|-------------|
| `ast_based` | Compares Abstract Syntax Tree node structures. Detects structural copying even with variable renaming. |
| `token_based` | Tokenizes code and compares token sequences using edit distance. |
| `text_based` | Raw text comparison using Levenshtein distance (via `rapidfuzz`). |

**Notes:**
- Each plagiarism pair generates **3 rows** (one per method) so you can compare detection approaches.
- **Background pairs** (low similarity) are also included as negative examples — these are random, non-plagiarized pairs with expected low similarity.
- `flagged = True` means `similarity_pct >= 80.0` for that specific method.

---

## 5. Entity Relationship Diagram

```
+------------------+       +--------------------+       +------------------------+
|   students.csv   |       |  submissions.csv   |       | submission_artifacts.csv|
+------------------+       +--------------------+       +------------------------+
| student_id  [PK] |<------| student_id    [FK] |       | artifact_id       [PK] |
| name             |       | submission_id [PK] |<------| submission_id     [FK] |
| email            |       | assignment_id      |       | artifact_type          |
| skill_level      |       | attempt_no         |       | filename               |
| is_late_submitter|       | submitted_at       |       | filetype               |
| generates_pdf    |       | due_at             |       | sha256                 |
+------------------+       | status             |       | size_bytes             |
                           +--------------------+       +------------------------+
                                    |
                    +---------------+----------------+
                    |               |                |
                    v               v                v
        +-------------------+  +-----------------+  +---------------------+
        |execution_results  |  |submission_tags  |  | similarity_scores   |
        +-------------------+  +-----------------+  +---------------------+
        | exec_id      [PK] |  | submission_id[FK]|  | sim_id         [PK] |
        | submission_id[FK] |  | tag              |  | submission_id  [FK] |
        | started_at        |  | source           |  | compared_to    [FK] |
        | finished_at       |  | confidence       |  | method              |
        | status            |  +-----------------+  | similarity_pct      |
        | exit_code         |                       | flagged             |
        | stdout            |                       +---------------------+
        | stderr            |
        | runtime_ms        |
        +-------------------+
                 |
                 v
        +-------------------+
        |test_case_results  |
        +-------------------+
        | test_id      [PK] |
        | exec_id      [FK] |
        | test_case_id      |
        | passed            |
        | score_awarded     |
        | output            |
        +-------------------+
```

**Relationship Summary:**

| Parent | Child | Cardinality | Join Key |
|--------|-------|-------------|----------|
| students | submissions | 1:N | `student_id` |
| submissions | submission_artifacts | 1:N | `submission_id` |
| submissions | execution_results | 1:N | `submission_id` |
| submissions | submission_tags | 1:N | `submission_id` |
| submissions | similarity_scores | 1:N | `submission_id` or `compared_to` |
| execution_results | test_case_results | 1:N | `exec_id` |

---

## 6. Assignment Definitions

All assignments are for an **Intro to Computer Science (CS1)** course. The semester runs from **January 12, 2026** to **April 30, 2026**.

### 6.1 HW1: Variables, I/O, and Arithmetic

| Property | Value |
|----------|-------|
| **Difficulty** | 0.20 (easiest) |
| **Due Date** | January 30, 2026 |
| **Max Score** | 100 |
| **Test Cases** | 5 |
| **Files** | `hw1_solution.py` (1 file) |

**Test Cases:**

| ID | Description | Input | Expected Output | Points |
|----|-------------|-------|-----------------|--------|
| HW1_TC01 | Add two integers | `3\n5` | `8` | 20 |
| HW1_TC02 | Celsius to Fahrenheit | `0` | `32.0` | 20 |
| HW1_TC03 | Celsius to Fahrenheit | `100` | `212.0` | 20 |
| HW1_TC04 | Area of a circle (r=5) | `5` | `78.54` | 20 |
| HW1_TC05 | Integer division (17/5) | `17\n5` | `3 2` | 20 |

### 6.2 HW2: Conditionals and Boolean Logic

| Property | Value |
|----------|-------|
| **Difficulty** | 0.35 |
| **Due Date** | February 17, 2026 |
| **Max Score** | 100 |
| **Test Cases** | 6 |
| **Files** | `hw2_solution.py` (1 file) |

**Test Cases:**

| ID | Description | Input | Expected Output | Points |
|----|-------------|-------|-----------------|--------|
| HW2_TC01 | Letter grade (95) | `95` | `A` | 17 |
| HW2_TC02 | Letter grade (85) | `85` | `B` | 17 |
| HW2_TC03 | Letter grade (45) | `45` | `F` | 17 |
| HW2_TC04 | Leap year (2024) | `2024` | `True` | 16 |
| HW2_TC05 | Leap year (1900) | `1900` | `False` | 16 |
| HW2_TC06 | Leap year (2000) | `2000` | `True` | 16 |

### 6.3 HW3: Loops and Iteration

| Property | Value |
|----------|-------|
| **Difficulty** | 0.50 |
| **Due Date** | March 7, 2026 |
| **Max Score** | 100 |
| **Test Cases** | 7 |
| **Files** | `hw3_solution.py` (1 file) |

**Test Cases:**

| ID | Description | Input | Expected Output | Points |
|----|-------------|-------|-----------------|--------|
| HW3_TC01 | Sum of first N (5) | `5` | `15` | 15 |
| HW3_TC02 | Factorial (6) | `6` | `720` | 15 |
| HW3_TC03 | Fibonacci (7th) | `7` | `13` | 14 |
| HW3_TC04 | Count digits (12345) | `12345` | `5` | 14 |
| HW3_TC05 | Reverse number (1234) | `1234` | `4321` | 14 |
| HW3_TC06 | Sum of digits (9876) | `9876` | `30` | 14 |
| HW3_TC07 | Multiplication (3x5) | `3\n5` | `15` | 14 |

### 6.4 HW4: Functions and Modular Design

| Property | Value |
|----------|-------|
| **Difficulty** | 0.65 |
| **Due Date** | March 25, 2026 |
| **Max Score** | 100 |
| **Test Cases** | 8 |
| **Files** | `hw4_solution.py` + `hw4_utils.py` (2 files) |

**Test Cases:**

| ID | Description | Input | Expected Output | Points |
|----|-------------|-------|-----------------|--------|
| HW4_TC01 | is_prime(7) | `7` | `True` | 13 |
| HW4_TC02 | is_prime(4) | `4` | `False` | 13 |
| HW4_TC03 | factorial(5) | `5` | `120` | 12 |
| HW4_TC04 | find_max([3,1,4,1,5]) | `3 1 4 1 5` | `5` | 12 |
| HW4_TC05 | reverse_string('hello') | `hello` | `olleh` | 12 |
| HW4_TC06 | is_palindrome('racecar') | `racecar` | `True` | 12 |
| HW4_TC07 | power(2, 10) | `2\n10` | `1024` | 13 |
| HW4_TC08 | gcd(48, 18) | `48\n18` | `6` | 13 |

### 6.5 HW5: Lists and Data Structures

| Property | Value |
|----------|-------|
| **Difficulty** | 0.80 (hardest) |
| **Due Date** | April 12, 2026 |
| **Max Score** | 100 |
| **Test Cases** | 8 |
| **Files** | `hw5_solution.py` + `hw5_utils.py` (2 files) |

**Test Cases:**

| ID | Description | Input | Expected Output | Points |
|----|-------------|-------|-----------------|--------|
| HW5_TC01 | Average [10,20,30] | `10 20 30` | `20.0` | 13 |
| HW5_TC02 | Deduplicate [1,2,2,3] | `1 2 2 3` | `1 2 3` | 13 |
| HW5_TC03 | Sort [5,3,1,4,2] | `5 3 1 4 2` | `1 2 3 4 5` | 12 |
| HW5_TC04 | Second largest [3,1,4,1,5] | `3 1 4 1 5` | `4` | 12 |
| HW5_TC05 | Count value (3 in [1,3,3,3,2]) | `3\n1 3 3 3 2` | `3` | 12 |
| HW5_TC06 | Merge sorted lists | `1 3 5\n2 4 6` | `1 2 3 4 5 6` | 12 |
| HW5_TC07 | Squares 1..4 | `4` | `1 4 9 16` | 13 |
| HW5_TC08 | Flatten [[1,2],[3,4]] | `1,2;3,4` | `1 2 3 4` | 13 |

---

## 7. Generation Parameters

### 7.1 Student Skill Distribution

Students are assigned a `skill_level` from a **Beta(5, 2)** distribution:

```
  skill_level range    ~% of students    Description
  ─────────────────    ──────────────    ────────────────────────────
  [0.30 - 0.50)        ~10%             Low skill (frequent errors, poor style)
  [0.50 - 0.70)        ~25%             Medium skill (working code, inconsistent style)
  [0.70 - 0.90)        ~50%             High skill (good code, proper formatting)
  [0.90 - 1.00]        ~15%             Excellent (PEP8, docstrings, type hints)
```

The Beta(5, 2) distribution is **right-skewed**, meaning most students perform above average — reflecting a realistic CS1 class.

### 7.2 Submission Attempt Distribution

For each student-assignment pair, the number of attempts is drawn from:

| Attempts | Probability | Meaning |
|----------|-------------|---------|
| 1 | 60% | Student submits once (pass or fail) |
| 2 | 30% | Student revises and resubmits once |
| 3 | 10% | Student makes a third attempt |

Later attempts show **skill improvement**: `effective_skill = min(1.0, skill_level + 0.1 * (attempt_no - 1))` and a **score bonus** of 5-15 points per retry (capped at 100).

### 7.3 Score Distribution

Scores are computed probabilistically, not by running actual code:

```
base_score  = Beta(5, 2) sample * 100          # Raw score from beta distribution
skill_factor = student.skill_level             # Student ability
difficulty_penalty = difficulty_weight * 0.3   # Harder assignments reduce score
effective_score = base_score * skill_factor * (1 - difficulty_penalty)
```

**Difficulty Weights:**

| Assignment | Difficulty Weight | Score Reduction |
|-----------|------------------|-----------------|
| HW1 | 0.20 | 6% penalty |
| HW2 | 0.35 | 10.5% penalty |
| HW3 | 0.50 | 15% penalty |
| HW4 | 0.65 | 19.5% penalty |
| HW5 | 0.80 | 24% penalty |

**Pass Rate Categories:**

| Category | Base Probability | Meaning |
|----------|-----------------|---------|
| ALL_PASS | 75% | All test cases pass |
| PARTIAL_PASS | 20% | Some tests pass, some fail |
| ALL_FAIL | 5% | All tests fail |

These rates are adjusted by the student's effective skill level — higher-skill students have a higher ALL_PASS rate.

### 7.4 Submission Timing

- **Semester:** January 12, 2026 - April 30, 2026
- **On-time window:** Up to 72 hours before the due date
- **Late window:** Up to 48 hours after the due date
- **Late probability:** For students flagged as `is_late_submitter`, there is a 50% chance each submission is late.
- **Overall late rate:** ~7% of all submissions (varies due to probabilistic generation)

### 7.5 Code Quality by Skill Level

| Skill Range | Code Characteristics |
|------------|---------------------|
| > 0.8 (High) | PEP8 compliant, docstrings present, type hints, descriptive variable names, proper structure |
| 0.5 - 0.8 (Medium) | Working code but style inconsistencies, some missing comments, basic variable names |
| < 0.5 (Low) | Contains intentional bugs: off-by-one errors, wrong operators, missing type conversions, indentation issues |

Each assignment has **3 code template variations** to ensure diversity. A template is randomly selected per student, and the quality tier (high/medium/low) is chosen based on the student's effective skill level.

### 7.6 PDF Lab Reports

- **Generation rate:** 40% of students produce PDF reports (determined by `generates_pdf` flag).
- **Content:** Student ID, assignment title, 2-4 reflection paragraphs, "What I Learned" section, "Challenges Faced" section.
- **Text:** Generated by Faker library (realistic-looking English paragraphs).
- **Size:** 50 KB - 500 KB per PDF.
- **Format:** US Letter (8.5" x 11"), 1-inch margins, generated with ReportLab.

### 7.7 OCR Handwriting Images

- **Count:** 100 standalone PNG images (not tied to individual submissions).
- **Dimensions:** 1200 x 1600 pixels.
- **Visual Effects:** Variable font sizes (18-28pt), slight rotation (up to 3 degrees), ink color variation, scanner noise (200-500 speckle spots), optional Gaussian blur.
- **Content:** Mix of code-related fragments and Faker-generated sentences.
- **Purpose:** For testing OCR capabilities of the Agentic TA system.

---

## 8. Plagiarism and Corruption Simulation

### 8.1 Plagiarism Pairs

- **Rate:** ~10% of submissions are involved in plagiarism pairs.
- **Pairs generated:** 38 pairs in the default dataset.
- **Detection threshold:** Similarity >= 80% is flagged as suspicious.

**How plagiarism is simulated:**

For each plagiarism pair, one student's code is taken as the "source" and transformed into the "copy" using three AST-based techniques:

1. **Variable Renaming (`VariableRenamer`):** Replaces variable and function names with synonyms (e.g., `result` -> `output`, `answer`, `res`) or appends suffixes (e.g., `x` -> `x_v2`). Python built-in names (`print`, `input`, `range`) are preserved.

2. **Dead Code Insertion (`DeadCodeInserter`):** Adds non-functional code at a 30% density: unused variable assignments (`_unused_var = 0`), no-op function definitions (`def _helper(): pass`).

3. **Code Reformatting:** Changes quote styles (single <-> double), adds/removes comments, adjusts blank lines.

**Each pair generates 3 similarity scores** (one per method):
- `ast_based`: Compares AST node type sequences — high similarity even after renaming.
- `token_based`: Compares tokenized code sequences using edit distance.
- `text_based`: Raw text comparison using Levenshtein ratio (via rapidfuzz).

Additionally, **background pairs** (10 per assignment) are included with naturally low similarity scores, serving as negative examples.

### 8.2 Corrupted Files

- **Rate:** ~3% of submissions are intentionally corrupted.
- **Count:** 20 corrupted files in the default dataset.
- **Types of corruption:**
  - Invalid ZIP structure (truncated or random bytes appended).
  - Encoding errors in Python files.
  - Oversized binary data inserted into source files.
- **Tag:** These submissions receive a `corrupted` tag with confidence 0.70-1.00.

---

## 9. Manifest Schema

Each attempt directory contains a `manifest.json` file that serves as an artifact inventory for integrity verification.

### Structure

```json
{
  "submission_id": "82fd05f4-45a4-450e-9aa2-55778a5f5666",
  "student_id": "S050",
  "assignment_id": "HW3",
  "attempt_no": 1,
  "generated_at": "2026-03-03T03:57:47.017886Z",
  "artifacts": [
    {
      "filename": "hw3_solution.py",
      "artifact_type": "python_file",
      "sha256": "e02d14d8c55f16945f1f577bf351e67bcde63ad57c0481df1bf9cfac6e491515",
      "size_bytes": 1693
    },
    {
      "filename": "S050_HW3_attempt1.zip",
      "artifact_type": "zip_bundle",
      "sha256": "394427d5e868a4ba21dcc1beb59254a1389a410dec4eba2a276aba4255ae3a2e",
      "size_bytes": 267485
    },
    {
      "filename": "S050_HW3_attempt1_report.pdf",
      "artifact_type": "pdf_report",
      "sha256": "3e00451f2df75736ccbe24b4b7c4934f3ee3083c5edfc44f9fbded7f0c6f9030",
      "size_bytes": 133736
    }
  ]
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `submission_id` | UUID string | Links to `submissions.csv` |
| `student_id` | String | Format: `S` + 3 digits (e.g., `S050`) |
| `assignment_id` | String | Format: `HW` + 1 digit (e.g., `HW3`) |
| `attempt_no` | Integer | 1, 2, or 3 |
| `generated_at` | ISO 8601 datetime | When the manifest was created (UTC) |
| `artifacts` | Array | List of file artifacts in this directory |
| `artifacts[].filename` | String | Filename on disk |
| `artifacts[].artifact_type` | String | `python_file`, `zip_bundle`, or `pdf_report` |
| `artifacts[].sha256` | String | 64-character lowercase hex SHA-256 digest |
| `artifacts[].size_bytes` | Integer | File size in bytes |

### Validation Schema Rules

- `student_id` must match regex `^S\d{3}$`
- `assignment_id` must match regex `^HW\d$`
- `attempt_no` must be in range `[1, 3]`
- `sha256` must match regex `^[0-9a-f]{64}$`
- `size_bytes` must be >= 1
- `artifacts` must have at least 1 entry

---

## 10. Validation Checks

The generation pipeline includes 6 automated QA checks. Run `python generate_data.py --validate-only` to execute them.

| # | Check | What It Verifies | Pass Criteria |
|---|-------|-----------------|---------------|
| 1 | **Schema Validation** | Every `manifest.json` conforms to the JSON Schema (required fields, types, regex patterns). | All manifests pass schema validation. |
| 2 | **SHA-256 Checksums** | Recomputes SHA-256 for every artifact file and compares against manifest records. | All hashes match exactly. |
| 3 | **File Existence** | Every file referenced in a manifest actually exists on disk. | All files found. |
| 4 | **Submission Count** | Total submissions in `submissions.csv` falls within `[NUM_STUDENTS * NUM_ASSIGNMENTS, NUM_STUDENTS * NUM_ASSIGNMENTS * 3]`. | 500 <= count <= 1500 for default parameters. |
| 5 | **Distribution Checks** | Attempt count distribution and late rate are within ±15% of configured targets. | Attempt 1 rate ~ 60%, Attempt 2 rate ~ 30%, Attempt 3 rate ~ 10%, Late rate ~ 20%. |
| 6 | **File Size Ranges** | Artifact file sizes fall within the configured min/max for each artifact type. | All files within bounds. |

**Default dataset validation results:** 5,071 passed, 3 failed (minor deviations in late rate and a few files slightly outside size bounds due to probabilistic generation).

---

## 11. Notes for DB Engineers

### Importing CSV Data

1. **Import Order (respecting foreign keys):**
   1. `students.csv` (no FKs)
   2. `submissions.csv` (FK: `student_id`)
   3. `submission_artifacts.csv` (FK: `submission_id`)
   4. `execution_results.csv` (FK: `submission_id`)
   5. `test_case_results.csv` (FK: `exec_id`)
   6. `submission_tags.csv` (FK: `submission_id`)
   7. `similarity_scores.csv` (FKs: `submission_id`, `compared_to`)

2. **Primary Keys:**
   - `students`: `student_id` (STRING, not auto-increment)
   - `submissions`: `submission_id` (UUID)
   - `submission_artifacts`: `artifact_id` (UUID)
   - `execution_results`: `exec_id` (UUID)
   - `test_case_results`: `test_id` (UUID)
   - `submission_tags`: composite (`submission_id`, `tag`) — a submission can have multiple different tags but not duplicate tags
   - `similarity_scores`: `sim_id` (UUID)

3. **Data Types to Watch:**
   - UUIDs are stored as lowercase hyphenated strings (36 characters). Use `UUID` or `VARCHAR(36)` column type.
   - `stdout` and `stderr` in `execution_results.csv` can contain **newlines** and be quite long (multi-line test output). Use `TEXT` column type, not `VARCHAR`.
   - `skill_level`, `confidence`, and `similarity_pct` are floating point values. Use `FLOAT` or `DECIMAL`.
   - `size_bytes` and `runtime_ms` are integers.
   - Boolean columns (`passed`, `is_late_submitter`, `generates_pdf`, `flagged`) are stored as Python `True`/`False` strings. Map to your DB's boolean type.

4. **Indexes to Consider:**
   - `submissions(student_id)` — for looking up all submissions by a student
   - `submissions(assignment_id)` — for looking up all submissions for an assignment
   - `submission_artifacts(submission_id)` — for fetching artifacts for a submission
   - `execution_results(submission_id)` — for grading lookups
   - `test_case_results(exec_id)` — for detailed test results
   - `similarity_scores(submission_id)` + `similarity_scores(compared_to)` — for plagiarism queries

5. **File Path Resolution:**
   - The physical file for an artifact can be found at:
     ```
     seed_data/intro_cs/Assignments/{assignment_id}/{student_id}/attempt{attempt_no}/{filename}
     ```
   - Derive this path by joining data from `submissions.csv` and `submission_artifacts.csv`.

---

## 12. Notes for UI and LLM Engineers

### Data Available for UI Display

1. **Student Dashboard:**
   - Student list with skill levels from `students.csv`.
   - Per-student submission history by joining `students` -> `submissions` -> `execution_results`.
   - Score trends across assignments and attempts.

2. **Submission Detail View:**
   - Python source code is available as plain text files (`.py`). Read directly from disk for code display.
   - ZIP contents can be extracted for file browser views.
   - PDF reports can be rendered in-browser or as download links.
   - Manifest provides a structured summary of all files in a submission.

3. **Grading Results:**
   - Per-test-case pass/fail from `test_case_results.csv`.
   - Execution status, runtime, stdout, and stderr from `execution_results.csv`.
   - Tags (excellent, late, plagiarism_suspect, corrupted) from `submission_tags.csv`.

4. **Plagiarism Dashboard:**
   - Flagged pairs from `similarity_scores.csv` where `flagged = True`.
   - Three similarity methods per pair for comparison.
   - Link to both submissions' source code for side-by-side display.

### Data Available for LLM Context

1. **Code Review / Feedback Generation:**
   - `hw{n}_solution.py` provides the actual student code to analyze.
   - `execution_results.csv` provides test outcomes and error messages the LLM can reference.
   - `test_case_results.csv` provides granular per-test pass/fail data.
   - `submission_tags.csv` provides pre-classified labels (excellent, plagiarism, etc.).
   - Code quality intentionally varies by skill level — low-skill code contains real bugs (off-by-one, type errors) that an LLM should be able to identify and explain.

2. **Score Prediction / Analytics:**
   - Score distributions follow Beta(5, 2) * skill_level * difficulty — a predictable pattern the LLM can learn.
   - Multi-attempt improvement is baked in: later attempts score 5-15 points higher.

3. **Plagiarism Explanation:**
   - Plagiarism pairs have known transformation types (variable renaming, dead code, reformatting).
   - The LLM can explain detected similarities and identify specific transformation patterns.

4. **OCR Processing:**
   - 100 handwriting-simulation images in `ocr_images/` for testing OCR -> text extraction.
   - Images contain CS1-related code snippets and notes with realistic noise/rotation.

### Important Caveats

- **All data is synthetic.** Student names, emails, and submissions are entirely fake. No real student data is used.
- **Scores are simulated, not computed.** The Python source code is NOT actually executed — scores are probabilistically generated based on student skill and assignment difficulty. The code may or may not produce the expected test case outputs.
- **Reproducible:** Re-running `python generate_data.py --seed 42` generates the exact same dataset. Use a different seed for a fresh dataset.
- **Semester context:** All dates fall within Spring 2026 (Jan 12 - Apr 30) at Georgia State University.

---

## Appendix: Summary Statistics (Default Dataset)

```
Students:            100
Assignments:         5
Total submissions:   754
Total artifacts:     2,150

Score statistics:
  Mean:      92.49
  Median:   100.00
  Min:        0.00
  Max:      100.00
  Std Dev:   21.59

Submission status breakdown:
  on_time:   702 (93.1%)
  late:       52 (6.9%)

Plagiarism:
  Pairs flagged:     38
  Similarity scores: 164
  Corrupted files:   20

PDF reports generated: 334
OCR images generated:  100

Disk usage: ~262 MB
Generation time: ~60 seconds
```
