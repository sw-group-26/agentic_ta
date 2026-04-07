# Version-Aware Submission Refactor - Change Log

## Scope
This document records what was modified and added in the SQL refactor for version-aware submissions.

## Updated Files
- `schema.sql`
- `migration_submission_version_refactor.sql` (new)

## What Was Modified in `schema.sql`

### 1. Submission model kept stable
- Kept `UNIQUE(assignment_id, student_id)` on `submission`.
- Preserved compatibility fields on `submission`:
  - `repo_url`
  - `commit_hash`
  - `code_snapshot_path`

### 2. `submission_version` expanded to carry version snapshot metadata
Added columns:
- `code_snapshot_path TEXT`
- `repo_url TEXT`
- `source_type TEXT`
- `notes TEXT`

### 3. `test_run` is now version-aware
Added:
- `version_id UUID NOT NULL REFERENCES submission_version(version_id) ON DELETE CASCADE`

### 4. `grading_record` is now version-aware
Added:
- `version_id UUID NOT NULL REFERENCES submission_version(version_id) ON DELETE CASCADE`

Changed uniqueness rule:
- Replaced submission-level uniqueness with `UNIQUE(version_id)`.

### 5. `llm_feedback_draft` is now version-aware
Added:
- `version_id UUID NOT NULL REFERENCES submission_version(version_id) ON DELETE CASCADE`

### 6. New indexes for version-based queries
Added indexes:
- `ix_test_run_version` on `test_run(version_id)`
- `ix_llm_draft_version` on `llm_feedback_draft(version_id)`

## New Migration Script

A new executable migration file was added:
- `migration_submission_version_refactor.sql`

### Migration Phases

#### Phase A: Additive schema changes (non-breaking)
- Add new snapshot columns to `submission_version`.
- Add nullable `version_id` columns to:
  - `test_run`
  - `grading_record`
  - `llm_feedback_draft`
- Create version-based indexes.

#### Phase B: Backfill legacy data
- Ensure every `submission` has at least one `submission_version` row.
- Auto-create attempt 1 for legacy submissions without versions.
- Backfill version snapshot metadata from legacy submission fields.
- Backfill `version_id` in dependent tables using latest version per submission.

#### Phase C: Enforce strict constraints
- Set `version_id` to `NOT NULL` in:
  - `test_run`
  - `grading_record`
  - `llm_feedback_draft`
- Drop old unique constraint on `grading_record(submission_id)` if present.
- Add/ensure `UNIQUE(version_id)` on `grading_record`.

## Result
The schema now supports one logical submission per student-assignment pair, with multiple attempts stored as explicit submission versions. All version-sensitive records (test runs, feedback drafts, and grading records) are bound to a concrete `version_id`.
