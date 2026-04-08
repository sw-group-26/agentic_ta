-- Agentic TA (CS grading assistant) - PostgreSQL schema
-- Works as a clean MVP+upgrade: cross-semester memory, rubric scoring, test runs,
-- LLM feedback drafts with evidence, similarity/plagiarism checks, student flags, notifications.

BEGIN;

-- Extensions (optional; comment out if your managed PG disallows)
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ===============
-- Core: course + offering
-- ===============
CREATE TABLE IF NOT EXISTS course (
  course_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_code     TEXT NOT NULL,
  course_name     TEXT NOT NULL,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(course_code)
);

CREATE TABLE IF NOT EXISTS course_offering (
  offering_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  course_id       UUID NOT NULL REFERENCES course(course_id) ON DELETE CASCADE,
  semester        TEXT NOT NULL,          -- e.g., "Spring"
  year            INT  NOT NULL,          -- e.g., 2026
  section         TEXT,                   -- e.g., "002"
  instructor      TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
-- UNIQUE constraint with expression: section NULL treated as empty string
CREATE UNIQUE INDEX IF NOT EXISTS ux_offering_course_semester_section
  ON course_offering(course_id, semester, year, COALESCE(section,''));

-- ===============
-- People
-- ===============
CREATE TABLE IF NOT EXISTS student (
  student_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  email           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(email)
);

CREATE TABLE IF NOT EXISTS ta (
  ta_id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  email           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(email)
);

CREATE TABLE IF NOT EXISTS enrollment (
  enrollment_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id     UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  student_id      UUID NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(offering_id, student_id)
);

CREATE TABLE IF NOT EXISTS ta_assignment (
  ta_assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id      UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  ta_id            UUID NOT NULL REFERENCES ta(ta_id) ON DELETE CASCADE,
  role             TEXT, -- e.g., "lead_ta", "grader"
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(offering_id, ta_id)
);

-- ===============
-- Assignments + Rubric
-- ===============
CREATE TABLE IF NOT EXISTS assignment (
  assignment_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id     UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  title           TEXT NOT NULL,
  due_at          TIMESTAMPTZ,
  language        TEXT, -- e.g., "python", "java"
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS rubric (
  rubric_id       UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id   UUID NOT NULL REFERENCES assignment(assignment_id) ON DELETE CASCADE,
  total_points    NUMERIC(6,2) NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(assignment_id)
);

CREATE TABLE IF NOT EXISTS rubric_item (
  rubric_item_id  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  rubric_id       UUID NOT NULL REFERENCES rubric(rubric_id) ON DELETE CASCADE,
  description     TEXT NOT NULL,
  category        TEXT,                   -- e.g., "Correctness", "Style"
  max_points      NUMERIC(6,2) NOT NULL,
  order_index     INT NOT NULL DEFAULT 0,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ===============
-- Submissions + versions
-- ===============
CREATE TABLE IF NOT EXISTS submission (
  submission_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assignment_id   UUID NOT NULL REFERENCES assignment(assignment_id) ON DELETE CASCADE,
  student_id      UUID NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
  submitted_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  repo_url        TEXT,        -- compatibility/latest cache; version-level source lives on submission_version
  commit_hash     TEXT,        -- compatibility/latest cache; version-level commit lives on submission_version
  code_snapshot_path TEXT,     -- compatibility/latest cache; version-level snapshot lives on submission_version
  status          TEXT NOT NULL DEFAULT 'submitted', -- submitted|graded|flagged
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(assignment_id, student_id)  -- one logical submission per student-assignment pair
);

CREATE TABLE IF NOT EXISTS submission_version (
  version_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id   UUID NOT NULL REFERENCES submission(submission_id) ON DELETE CASCADE,
  attempt_no      INTEGER NOT NULL DEFAULT 1,  -- 1-based attempt number per submission
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  commit_hash     TEXT,
  diff_summary    TEXT,
  code_snapshot_path TEXT,
  repo_url        TEXT,
  source_type     TEXT,                  -- e.g. "upload", "git", "lms", "legacy"
  notes           TEXT,
  UNIQUE(submission_id, attempt_no)            -- one version row per attempt
);

-- ===============
-- Test runs (objective signals for feedback)
-- ===============
CREATE TABLE IF NOT EXISTS test_run (
  test_run_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id   UUID NOT NULL REFERENCES submission(submission_id) ON DELETE CASCADE,
  version_id      UUID NOT NULL REFERENCES submission_version(version_id) ON DELETE CASCADE,
  run_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  score           NUMERIC(6,2),
  runtime_ms      INT,
  results_json_path TEXT,  -- path to structured results
  stdout_path     TEXT,
  stderr_path     TEXT
);

-- ===============
-- Grading records + rubric scores
-- ===============
CREATE TABLE IF NOT EXISTS grading_record (
  grading_id      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id   UUID NOT NULL REFERENCES submission(submission_id) ON DELETE CASCADE,
  version_id      UUID NOT NULL REFERENCES submission_version(version_id) ON DELETE CASCADE,
  ta_id           UUID REFERENCES ta(ta_id) ON DELETE SET NULL,
  total_score     NUMERIC(6,2),
  final_feedback  TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(version_id) -- one final grade per version
);

CREATE TABLE IF NOT EXISTS rubric_score (
  rubric_score_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  grading_id      UUID NOT NULL REFERENCES grading_record(grading_id) ON DELETE CASCADE,
  rubric_item_id  UUID NOT NULL REFERENCES rubric_item(rubric_item_id) ON DELETE CASCADE,
  score           NUMERIC(6,2) NOT NULL,
  comment         TEXT
);

-- ===============
-- LLM feedback drafts + evidence grounding
-- ===============
CREATE TABLE IF NOT EXISTS llm_feedback_draft (
  draft_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  submission_id   UUID NOT NULL REFERENCES submission(submission_id) ON DELETE CASCADE,
  version_id      UUID NOT NULL REFERENCES submission_version(version_id) ON DELETE CASCADE,
  model_name      TEXT NOT NULL,           -- e.g., "qwen2.5-coder-7b"
  prompt_version  TEXT,                    -- e.g., "v1.0"
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  draft_text      TEXT NOT NULL,
  confidence      NUMERIC(4,3),            -- optional heuristic
  status          TEXT NOT NULL DEFAULT 'pending',
  approved_by     UUID REFERENCES ta(ta_id),
  approved_at     TIMESTAMPTZ,
  published_at    TIMESTAMPTZ,
  CONSTRAINT chk_draft_status CHECK (status IN ('pending', 'approved', 'published'))
);

-- Evidence pointers (keeps LLM "grounded" and explainable)
CREATE TABLE IF NOT EXISTS llm_evidence (
  evidence_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  draft_id        UUID NOT NULL REFERENCES llm_feedback_draft(draft_id) ON DELETE CASCADE,
  evidence_type   TEXT NOT NULL,           -- "test_run", "stderr", "code_snippet", "rubric_item"
  pointer         TEXT NOT NULL,           -- e.g., "test_run:<id>" or "file:path#L10-L30"
  snippet         TEXT                      -- optional excerpt
);

-- ===============
-- Similarity / plagiarism checks (cross-semester)
-- ===============
CREATE TABLE IF NOT EXISTS similarity_check (
  check_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id     UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  assignment_id   UUID NOT NULL REFERENCES assignment(assignment_id) ON DELETE CASCADE,
  submission_a    UUID NOT NULL REFERENCES submission(submission_id) ON DELETE CASCADE,
  submission_b    UUID NOT NULL REFERENCES submission(submission_id) ON DELETE CASCADE,
  similarity_score NUMERIC(5,4) NOT NULL,  -- 0..1
  method          TEXT NOT NULL,           -- e.g., "moss", "token_jaccard"
  checked_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  report_path     TEXT
);

-- Prevent duplicates A-B vs B-A
CREATE UNIQUE INDEX IF NOT EXISTS ux_similarity_pair
ON similarity_check (assignment_id, LEAST(submission_a, submission_b), GREATEST(submission_a, submission_b), method);

-- ===============
-- Student flags (under-performing, suspected plagiarism, etc.)
-- ===============
CREATE TABLE IF NOT EXISTS student_flag (
  flag_id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id     UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  student_id      UUID NOT NULL REFERENCES student(student_id) ON DELETE CASCADE,
  flag_type       TEXT NOT NULL,           -- "underperforming"|"plagiarism"|"missing_submissions"
  reason          TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  status          TEXT NOT NULL DEFAULT 'open' -- open|resolved|ignored
);

-- ===============
-- Notifications
-- ===============
CREATE TABLE IF NOT EXISTS notification (
  notification_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id     UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  target_type     TEXT NOT NULL,           -- "student"|"ta"|"instructor"
  target_id       UUID NOT NULL,           -- references student_id/ta_id (polymorphic)
  channel         TEXT NOT NULL,           -- "email"|"in_app"
  message         TEXT NOT NULL,
  sent_at         TIMESTAMPTZ,
  status          TEXT NOT NULL DEFAULT 'pending' -- pending|sent|failed
);

-- ===============
-- Helpful indexes
-- ===============
CREATE INDEX IF NOT EXISTS ix_assignment_offering ON assignment(offering_id);
CREATE INDEX IF NOT EXISTS ix_submission_assignment ON submission(assignment_id);
CREATE INDEX IF NOT EXISTS ix_submission_student ON submission(student_id);
CREATE INDEX IF NOT EXISTS ix_test_run_submission ON test_run(submission_id);
CREATE INDEX IF NOT EXISTS ix_test_run_version ON test_run(version_id);
CREATE INDEX IF NOT EXISTS ix_llm_draft_submission ON llm_feedback_draft(submission_id);
CREATE INDEX IF NOT EXISTS ix_llm_draft_version ON llm_feedback_draft(version_id);
CREATE INDEX IF NOT EXISTS ix_llm_draft_submission_status ON llm_feedback_draft(submission_id, status);
CREATE INDEX IF NOT EXISTS ix_flag_student ON student_flag(student_id);

COMMIT;
