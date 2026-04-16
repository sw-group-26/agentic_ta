# PostgreSQL Setup and Demo Guide

This guide brings up a local PostgreSQL database for the project, loads demo data, and verifies that the data is available for other modules.

## 1. Prerequisites

- PostgreSQL 16 running locally on port `5432`
- Python 3.11
- Project virtual environment at `.venv`

## 2. Environment

Create `.env` in the project root with at least:

```env
DATABASE_URL=postgresql:///agentic_ta
LOCAL_STORAGE_ROOT=./storage
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_PROMPT_VERSION=v1.0
OLLAMA_REQUEST_TIMEOUT_SEC=120
```

## 3. Create the database

```bash
createdb agentic_ta
```

If the database already exists, skip this step.

## 4. Apply the schema

For a fresh database, use the canonical schema:

```bash
/opt/homebrew/opt/postgresql@16/bin/psql -d agentic_ta -v ON_ERROR_STOP=1 -f db/schema.sql
```

For an existing database that needs upgrading, apply the migrations instead:

```bash
/opt/homebrew/opt/postgresql@16/bin/psql -d agentic_ta -v ON_ERROR_STOP=1 -f db/migration_submission_version_refactor.sql
/opt/homebrew/opt/postgresql@16/bin/psql -d agentic_ta -v ON_ERROR_STOP=1 -f db/migrations/add_draft_status.sql
```

## 5. Install runtime dependencies

```bash
python3.11 -m venv .venv
. .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install fastapi 'uvicorn[standard]' httpx python-dotenv psycopg2-binary pydantic pandas
```

## 6. Load demo data

```bash
. .venv/bin/activate
python scripts/ingest_seed_data.py --sample demo_case_01
```

This imports:
- 2 students
- 1 assignment
- 2 logical submissions
- 3 submission versions
- 3 test runs

## 7. Verify the database contents

Row counts:

```bash
/opt/homebrew/opt/postgresql@16/bin/psql -d agentic_ta -P pager=off -c "SELECT 'student' AS table_name, COUNT(*) AS row_count FROM student UNION ALL SELECT 'assignment', COUNT(*) FROM assignment UNION ALL SELECT 'submission', COUNT(*) FROM submission UNION ALL SELECT 'submission_version', COUNT(*) FROM submission_version UNION ALL SELECT 'test_run', COUNT(*) FROM test_run UNION ALL SELECT 'similarity_check', COUNT(*) FROM similarity_check UNION ALL SELECT 'llm_feedback_draft', COUNT(*) FROM llm_feedback_draft;"
```

Submission/version/test run proof:

```bash
/opt/homebrew/opt/postgresql@16/bin/psql -d agentic_ta -P pager=off -c "SELECT s.submission_id, st.name, a.title, sv.attempt_no, tr.test_run_id, tr.score, tr.run_at FROM submission s JOIN student st ON st.student_id = s.student_id JOIN assignment a ON a.assignment_id = s.assignment_id JOIN submission_version sv ON sv.submission_id = s.submission_id LEFT JOIN test_run tr ON tr.version_id = sv.version_id ORDER BY st.name, sv.attempt_no;"
```

## 8. Verify service-layer access

Build a feedback packet from the database without calling the LLM:

```bash
. .venv/bin/activate
python scripts/generate_feedback_draft.py --demo --dry-run
```

This proves the feedback service can read:
- submission metadata
- version-aware artifacts
- test results
- student history

## 9. Run the local API

```bash
. .venv/bin/activate
uvicorn app.main:app --reload --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Expected response:

```json
{"status":"ok"}
```
