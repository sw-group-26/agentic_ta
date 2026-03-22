-- Version-aware submission refactor migration (PostgreSQL)
-- Phase A: add columns and indexes without breaking old logic
-- Phase B: backfill historical data
-- Phase C: tighten constraints and switch grading uniqueness

BEGIN;

-- ==================================
-- Phase A: additive schema changes
-- ==================================

ALTER TABLE submission_version
  ADD COLUMN IF NOT EXISTS code_snapshot_path TEXT,
  ADD COLUMN IF NOT EXISTS repo_url TEXT,
  ADD COLUMN IF NOT EXISTS source_type TEXT,
  ADD COLUMN IF NOT EXISTS notes TEXT;

ALTER TABLE test_run
  ADD COLUMN IF NOT EXISTS version_id UUID REFERENCES submission_version(version_id) ON DELETE CASCADE;

ALTER TABLE grading_record
  ADD COLUMN IF NOT EXISTS version_id UUID REFERENCES submission_version(version_id) ON DELETE CASCADE;

ALTER TABLE llm_feedback_draft
  ADD COLUMN IF NOT EXISTS version_id UUID REFERENCES submission_version(version_id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS ix_test_run_version ON test_run(version_id);
CREATE INDEX IF NOT EXISTS ix_llm_draft_version ON llm_feedback_draft(version_id);

-- ==================================
-- Phase B: data backfill
-- ==================================

-- 1) Ensure every submission has at least one version row.
INSERT INTO submission_version (
  submission_id,
  attempt_no,
  created_at,
  commit_hash,
  diff_summary,
  code_snapshot_path,
  repo_url,
  source_type,
  notes
)
SELECT
  s.submission_id,
  1,
  COALESCE(s.submitted_at, s.created_at, now()),
  s.commit_hash,
  NULL,
  s.code_snapshot_path,
  s.repo_url,
  'legacy',
  'Auto-created by migration for legacy submission rows'
FROM submission s
WHERE NOT EXISTS (
  SELECT 1
  FROM submission_version sv
  WHERE sv.submission_id = s.submission_id
);

-- 2) Backfill version snapshot metadata for existing version rows when values are missing.
WITH latest_version AS (
  SELECT DISTINCT ON (sv.submission_id)
    sv.submission_id,
    sv.version_id
  FROM submission_version sv
  ORDER BY sv.submission_id, sv.attempt_no DESC, sv.created_at DESC, sv.version_id DESC
)
UPDATE submission_version sv
SET
  commit_hash = COALESCE(sv.commit_hash, s.commit_hash),
  code_snapshot_path = COALESCE(sv.code_snapshot_path, s.code_snapshot_path),
  repo_url = COALESCE(sv.repo_url, s.repo_url),
  source_type = COALESCE(sv.source_type, 'legacy')
FROM latest_version lv
JOIN submission s ON s.submission_id = lv.submission_id
WHERE sv.version_id = lv.version_id;

-- 3) Backfill version_id on dependent tables using latest version per submission.
WITH latest_version AS (
  SELECT DISTINCT ON (sv.submission_id)
    sv.submission_id,
    sv.version_id
  FROM submission_version sv
  ORDER BY sv.submission_id, sv.attempt_no DESC, sv.created_at DESC, sv.version_id DESC
)
UPDATE test_run tr
SET version_id = lv.version_id
FROM latest_version lv
WHERE tr.submission_id = lv.submission_id
  AND tr.version_id IS NULL;

WITH latest_version AS (
  SELECT DISTINCT ON (sv.submission_id)
    sv.submission_id,
    sv.version_id
  FROM submission_version sv
  ORDER BY sv.submission_id, sv.attempt_no DESC, sv.created_at DESC, sv.version_id DESC
)
UPDATE grading_record gr
SET version_id = lv.version_id
FROM latest_version lv
WHERE gr.submission_id = lv.submission_id
  AND gr.version_id IS NULL;

WITH latest_version AS (
  SELECT DISTINCT ON (sv.submission_id)
    sv.submission_id,
    sv.version_id
  FROM submission_version sv
  ORDER BY sv.submission_id, sv.attempt_no DESC, sv.created_at DESC, sv.version_id DESC
)
UPDATE llm_feedback_draft lfd
SET version_id = lv.version_id
FROM latest_version lv
WHERE lfd.submission_id = lv.submission_id
  AND lfd.version_id IS NULL;

-- ==================================
-- Phase C: enforce constraints
-- ==================================

ALTER TABLE test_run
  ALTER COLUMN version_id SET NOT NULL;

ALTER TABLE grading_record
  ALTER COLUMN version_id SET NOT NULL;

ALTER TABLE llm_feedback_draft
  ALTER COLUMN version_id SET NOT NULL;

-- Drop old unique(submission_id) on grading_record if it exists.
DO $$
DECLARE
  rec RECORD;
BEGIN
  FOR rec IN
    SELECT c.conname
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = current_schema()
      AND t.relname = 'grading_record'
      AND c.contype = 'u'
      AND array_length(c.conkey, 1) = 1
      AND EXISTS (
        SELECT 1
        FROM pg_attribute a
        WHERE a.attrelid = t.oid
          AND a.attnum = c.conkey[1]
          AND a.attname = 'submission_id'
          AND NOT a.attisdropped
      )
  LOOP
    EXECUTE format('ALTER TABLE grading_record DROP CONSTRAINT %I', rec.conname);
  END LOOP;
END $$;

-- Ensure unique(version_id) exists on grading_record.
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM pg_constraint c
    JOIN pg_class t ON t.oid = c.conrelid
    JOIN pg_namespace n ON n.oid = t.relnamespace
    WHERE n.nspname = current_schema()
      AND t.relname = 'grading_record'
      AND c.contype = 'u'
      AND array_length(c.conkey, 1) = 1
      AND EXISTS (
        SELECT 1
        FROM pg_attribute a
        WHERE a.attrelid = t.oid
          AND a.attnum = c.conkey[1]
          AND a.attname = 'version_id'
          AND NOT a.attisdropped
      )
  ) THEN
    ALTER TABLE grading_record
      ADD CONSTRAINT uq_grading_record_version UNIQUE(version_id);
  END IF;
END $$;

COMMIT;
