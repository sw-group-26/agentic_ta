-- =============================================================================
-- Migration 002: Add instructor role tables and publishing metadata
--
-- Purpose:
--   - store instructor identities in the database instead of only as text
--   - map instructors to course offerings, similar to ta_assignment
--   - keep course_offering.instructor as a compatibility/display cache
--   - add published_by_instructor_id for auditability when feedback is released
--
-- Usage:
--   psql agentic_ta -f db/migrations/add_instructor_roles.sql
--
-- Idempotent: safe to run multiple times
-- =============================================================================

BEGIN;

CREATE TABLE IF NOT EXISTS instructor (
  instructor_id   UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name            TEXT NOT NULL,
  email           TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(email)
);

CREATE TABLE IF NOT EXISTS instructor_assignment (
  instructor_assignment_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  offering_id             UUID NOT NULL REFERENCES course_offering(offering_id) ON DELETE CASCADE,
  instructor_id           UUID NOT NULL REFERENCES instructor(instructor_id) ON DELETE CASCADE,
  role                    TEXT NOT NULL DEFAULT 'primary_instructor',
  created_at              TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(offering_id, instructor_id)
);

ALTER TABLE llm_feedback_draft
  ADD COLUMN IF NOT EXISTS published_by_instructor_id UUID REFERENCES instructor(instructor_id);

-- Backfill existing free-text instructor names into the normalized tables.
INSERT INTO instructor (name, email)
SELECT DISTINCT btrim(co.instructor), NULL
FROM course_offering co
WHERE co.instructor IS NOT NULL
  AND btrim(co.instructor) <> ''
  AND lower(btrim(co.instructor)) <> 'tba'
  AND NOT EXISTS (
    SELECT 1
    FROM instructor i
    WHERE lower(btrim(i.name)) = lower(btrim(co.instructor))
  );

WITH canonical_instructor AS (
  SELECT DISTINCT ON (lower(btrim(name)))
    instructor_id,
    lower(btrim(name)) AS normalized_name
  FROM instructor
  ORDER BY lower(btrim(name)), created_at, instructor_id
)
INSERT INTO instructor_assignment (instructor_assignment_id, offering_id, instructor_id, role)
SELECT gen_random_uuid(), co.offering_id, ci.instructor_id, 'primary_instructor'
FROM course_offering co
JOIN canonical_instructor ci
  ON ci.normalized_name = lower(btrim(co.instructor))
WHERE co.instructor IS NOT NULL
  AND btrim(co.instructor) <> ''
  AND lower(btrim(co.instructor)) <> 'tba'
ON CONFLICT (offering_id, instructor_id) DO NOTHING;

COMMIT;
