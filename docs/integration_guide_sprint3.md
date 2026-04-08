# Sprint 3 Integration Guide — Feedback Service

> **Author**: Wonbum Sohn
> **Last Updated**: 2026-04-05
> **Branch**: `feat/wonbum-s3-feedback-api`

This guide explains how to integrate with the Feedback Service API that Wonbum
implemented in Sprint 3. It covers router registration (Colleague A), frontend
API usage (Colleague B), and the overall feedback lifecycle.

---

## 1. Overview

The Feedback Service provides a **complete LLM-powered feedback pipeline** for
student submissions:

1. **Generate** — TA triggers LLM feedback generation for a submission
2. **Review** — TA views the generated draft with supporting evidence
3. **Approve** — TA approves the draft (`pending` → `approved`)
4. **Publish** — Instructor publishes the approved draft (`approved` → `published`)
5. **View** — Student sees the published feedback

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│  FastAPI App (Colleague A: main.py)                     │
│                                                         │
│  app.include_router(feedback_router, prefix="/api")     │
│                                                         │
│  ┌───────────────────────────────────────────────────┐  │
│  │  feedback_router (Wonbum: app/routers/feedback.py)│  │
│  │  5 REST endpoints                                 │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │  feedback_service (app/services/feedback_service.py)│ │
│  │  Business logic + state machine                    │ │
│  └──────┬──────────┬────────────────┬────────────────┘  │
│         │          │                │                    │
│  ┌──────▼──┐ ┌─────▼─────┐ ┌───────▼──────┐            │
│  │ feedback │ │ ollama    │ │ draft_saver  │            │
│  │ _packet  │ │ _client   │ │              │            │
│  └──────┬──┘ └─────┬─────┘ └───────┬──────┘            │
│         │          │                │                    │
│  ┌──────▼──────────▼────────────────▼──────┐            │
│  │  PostgreSQL + LocalStorageAdapter       │            │
│  └─────────────────────────────────────────┘            │
└─────────────────────────────────────────────────────────┘
```

### Status Lifecycle

```
  ┌─────────┐    approve    ┌──────────┐    publish    ┌───────────┐
  │ pending │──────────────▶│ approved │──────────────▶│ published │
  └─────────┘   (TA only)   └──────────┘  (Instructor) └───────────┘
```

- **One-way only** — no reverse transitions allowed
- `published` is the terminal state
- Direct `pending` → `published` is **not allowed**

---

## 2. Module Reference

| File | Purpose | Owner |
|------|---------|-------|
| `app/routers/feedback.py` | 5 REST endpoints for the feedback workflow | Wonbum |
| `app/services/feedback_service.py` | Business logic: CRUD + state machine (5 public functions) | Wonbum |
| `app/services/feedback_packet.py` | Assembles LLM input context from DB + storage | Wonbum |
| `app/services/draft_saver.py` | Persists LLM output (draft + evidence) to DB | Wonbum |
| `app/llm/ollama_client.py` | Calls local Ollama LLM, returns structured feedback | Wonbum |
| `app/storage/local_store.py` | File system storage adapter (swappable interface) | Wonbum |
| `app/deps.py` | FastAPI dependency injection (`get_db`, `get_storage`) | Wonbum (temporary) |
| `app/schemas/feedback.py` | Pydantic v2 request/response schemas | Wonbum |
| `db/migrations/add_draft_status.sql` | Adds status/approval columns to `llm_feedback_draft` | Wonbum |

---

## 3. For Colleague A (DB + API Developer)

### 3.0 Temporary vs Production — What to Replace

Wonbum created several files for local development that should be **replaced**
when building the production application:

| Wonbum's Temporary File | Role | How to Replace |
|------------------------|------|----------------|
| `app/main.py` | Local dev FastAPI app instance | Add `feedback_router` to your production `main.py` via `include_router()`. Remove or keep Wonbum's `main.py` for local-only use. |
| `app/deps.py` → `get_db()` | Simple sync psycopg2 connection | Replace with your own DB connection (connection pool, async, SQLAlchemy, etc.). The function must be a generator that `yield`s a connection and closes it on teardown. |
| `app/deps.py` → `get_storage()` | Returns `LocalStorageAdapter` (file system) | When implementing S3/MinIO, return your adapter here. It must implement: `save_file()`, `save_json()`, `load_text()`, `exists()`. |
| CORS `allow_origins=["*"]` | Dev-only unrestricted CORS | Restrict to your frontend origin in production. |

**Files that should NOT be replaced** (use as-is):

- `app/routers/feedback.py` — plug-in router via `include_router()`
- `app/services/*` — full service layer (business logic)
- `app/schemas/*` — Pydantic request/response schemas
- `app/llm/*` — LLM client

### 3.1 Router Registration (2 lines)

Add these two lines to your production `main.py`:

```python
from app.routers.feedback import router as feedback_router

app.include_router(feedback_router, prefix="/api")
```

That's it. The router is self-contained — all service imports, error handling,
and dependency injection are internal.

### 3.2 Database Migration

Run the migration to add workflow columns to `llm_feedback_draft`:

```bash
psql $DATABASE_URL -f db/migrations/add_draft_status.sql
```

This adds 4 columns (idempotent — safe to run multiple times):
Run the required migrations (run in this order):

```bash
psql $DATABASE_URL -f db/migration_submission_version_refactor.sql
psql $DATABASE_URL -f db/migrations/add_draft_status.sql
```

This setup enables version-aware feedback.

`migration_submission_version_refactor.sql` adds the version-aware linkage (`version_id`) and backfills legacy rows.

`add_draft_status.sql` adds 4 workflow columns (idempotent — safe to run multiple times):

| Column | Type | Description |
|--------|------|-------------|
| `status` | `TEXT NOT NULL DEFAULT 'pending'` | `'pending'`, `'approved'`, or `'published'` |
| `approved_by` | `UUID REFERENCES ta(ta_id)` | TA who approved the draft |
| `approved_at` | `TIMESTAMPTZ` | Timestamp of approval |
| `published_at` | `TIMESTAMPTZ` | Timestamp of publication |

A CHECK constraint enforces: `status IN ('pending', 'approved', 'published')`.

### 3.3 Dependency Injection — Interface Contract

If you replace `app/deps.py`, your functions must follow these interfaces:

**`get_db()`** — Database connection generator

```python
def get_db():
    """Yield a psycopg2-compatible connection, close on teardown."""
    conn = your_connection_pool.getconn()
    try:
        yield conn
    finally:
        conn.close()  # or pool.putconn(conn)
```

Requirements:
- Must be a **generator** (uses `yield`)
- The yielded object must support: `.cursor()` (context manager), `.commit()`
- Cursors must support: `.execute()`, `.fetchone()`, `.fetchall()`, `.description`

**`get_storage()`** — Storage adapter factory

```python
def get_storage():
    """Return a storage adapter with save_file/save_json/load_text/exists."""
    return YourStorageAdapter()
```

Required methods on the returned adapter:
- `save_file(local_path: str, object_key: str) -> str`
- `save_json(data: dict, object_key: str) -> str`
- `load_text(object_key: str) -> str`
- `exists(object_key: str) -> bool`

### 3.4 CORS Configuration

Current dev config (in `app/main.py`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # <-- change this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

For production, restrict `allow_origins` to your frontend's actual origin
(e.g., `["https://your-frontend.example.com"]`).

---

## 4. For Colleague B (UI Developer)

### 4.1 Base URL and Content Type

| Property | Value |
|----------|-------|
| Base URL (dev) | `http://localhost:8000/api` |
| Content-Type | `application/json` |
| ID format | UUID v4 strings (e.g., `"cbca2439-5fa7-4a69-b4d5-57515f2ca8df"`) |

### 4.2 API Endpoints

#### Endpoint 1: List Feedback Drafts

**`GET /api/submissions/{submission_id}/feedback-drafts`**

Returns all drafts for a submission, ordered by most recent first.

```bash
curl -X GET http://localhost:8000/api/submissions/cbca2439-5fa7-4a69-b4d5-57515f2ca8df/feedback-drafts
```

**Response (200):**

```json
{
  "submission_id": "cbca2439-5fa7-4a69-b4d5-57515f2ca8df",
  "drafts": [
    {
      "draft_id": "a1b2c3d4-...",
      "model_name": "llama3.2",
      "prompt_version": "v1.0",
      "generated_at": "2026-04-05T12:00:00Z",
      "draft_text_preview": "Overall good work on HW1. Your solution correctly handles the base cases...",
      "confidence": 0.82,
      "status": "pending"
    }
  ],
  "count": 1
}
```

> **Note**: `draft_text_preview` is truncated to 200 characters. Use endpoint 2
> for the full text.

---

#### Endpoint 2: Get Draft Detail

**`GET /api/feedback-drafts/{draft_id}`**

Returns the full draft text plus all evidence items.

```bash
curl -X GET http://localhost:8000/api/feedback-drafts/a1b2c3d4-...
```

**Response (200):**

```json
{
  "draft_id": "a1b2c3d4-...",
  "submission_id": "cbca2439-...",
  "model_name": "llama3.2",
  "prompt_version": "v1.0",
  "generated_at": "2026-04-05T12:00:00Z",
  "draft_text": "Overall good work on HW1. Your solution correctly handles the base cases. Consider adding edge-case checks for empty input.",
  "confidence": 0.82,
  "status": "pending",
  "approved_by": null,
  "approved_at": null,
  "published_at": null,
  "evidence": [
    {
      "evidence_id": "e1f2g3h4-...",
      "evidence_type": "test_run",
      "pointer": "test_run:abc123",
      "snippet": "5/5 tests passed"
    },
    {
      "evidence_id": "e5f6g7h8-...",
      "evidence_type": "code_snippet",
      "pointer": "main.py:L12-L18",
      "snippet": "def solve(n): ..."
    }
  ]
}
```

**Error (404):** Draft not found.

> **Tip**: Use `evidence_type` to render different UI components (e.g., code
> block for `code_snippet`, test result panel for `test_run`).

---

#### Endpoint 3: Approve Draft

**`POST /api/feedback-drafts/{draft_id}/approve`**

TA approves a pending draft. Requires `ta_id` in the request body.

```bash
curl -X POST http://localhost:8000/api/feedback-drafts/a1b2c3d4-.../approve \
  -H "Content-Type: application/json" \
  -d '{"ta_id": "f9e8d7c6-..."}'
```

**Response (200):**

```json
{
  "draft_id": "a1b2c3d4-...",
  "status": "approved",
  "approved_by": "f9e8d7c6-...",
  "approved_at": "2026-04-05T12:05:00Z"
}
```

**Error (409):** Draft is not in `pending` status (already approved or published).

---

#### Endpoint 4: Publish Draft

**`POST /api/feedback-drafts/{draft_id}/publish`**

Instructor/Professor publishes an approved draft. No request body needed.

```bash
curl -X POST http://localhost:8000/api/feedback-drafts/a1b2c3d4-.../publish
```

**Response (200):**

```json
{
  "draft_id": "a1b2c3d4-...",
  "status": "published",
  "published_at": "2026-04-05T12:10:00Z"
}
```

**Error (409):** Draft is not in `approved` status.

---

#### Endpoint 5: Generate Feedback (Trigger LLM)

**`POST /api/submissions/{submission_id}/generate-feedback`**
**`POST /api/submissions/{submission_id}/generate-feedback?version_id={version_id}`**

Triggers the full LLM feedback generation pipeline. This is a **synchronous**
call that may take 60–120 seconds with a real LLM.

```bash
curl -X POST http://localhost:8000/api/submissions/cbca2439-.../generate-feedback
curl -X POST "http://localhost:8000/api/submissions/cbca2439-.../generate-feedback?version_id=7a2a6d6f-..."
```

**Response (200):**

```json
{
  "draft_id": "a1b2c3d4-...",
  "submission_id": "cbca2439-...",
  "version_id": "7a2a6d6f-...",
  "status": "pending",
  "message": "Feedback draft generated successfully"
}
```

**Error (503):** LLM service unavailable (Ollama offline or timeout).

> **Important**: Set a client-side timeout of at least **120 seconds** for this
> endpoint. The default browser `fetch()` timeout may be too short.

---

### 4.3 JavaScript / TypeScript Integration Examples

```typescript
const BASE_URL = "http://localhost:8000/api";

// --- 1. List drafts for a submission ---
async function listDrafts(submissionId: string) {
  const res = await fetch(
    `${BASE_URL}/submissions/${submissionId}/feedback-drafts`
  );
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // DraftListOut
}

// --- 2. Get draft detail ---
async function getDraftDetail(draftId: string) {
  const res = await fetch(`${BASE_URL}/feedback-drafts/${draftId}`);
  if (res.status === 404) return null; // draft not found
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // DraftDetailOut
}

// --- 3. Approve a draft (TA action) ---
async function approveDraft(draftId: string, taId: string) {
  const res = await fetch(`${BASE_URL}/feedback-drafts/${draftId}/approve`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ta_id: taId }),
  });
  if (res.status === 409) throw new Error("Draft already processed");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // ApproveOut
}

// --- 4. Publish a draft (Instructor action) ---
async function publishDraft(draftId: string) {
  const res = await fetch(`${BASE_URL}/feedback-drafts/${draftId}/publish`, {
    method: "POST",
  });
  if (res.status === 409) throw new Error("Draft not approved yet");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // PublishOut
}

// --- 5. Generate feedback (TA triggers LLM) ---
async function generateFeedback(submissionId: string) {
  const res = await fetch(
    `${BASE_URL}/submissions/${submissionId}/generate-feedback`,
async function generateFeedback(submissionId: string, versionId?: string) {
  const qs = versionId ? `?version_id=${versionId}` : "";
  const res = await fetch(
    `${BASE_URL}/submissions/${submissionId}/generate-feedback${qs}`,
    {
      method: "POST",
      signal: AbortSignal.timeout(120_000), // 120s timeout for LLM
    }
  );
  if (res.status === 503) throw new Error("LLM service unavailable");
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json(); // GenerateFeedbackOut
}
```

### 4.4 Error Handling

| HTTP Status | Meaning | Suggested UI Message |
|-------------|---------|---------------------|
| 200 | Success | (update UI with response data) |
| 404 | Resource not found | "Feedback draft not found." |
| 409 | Invalid state transition | "This feedback has already been processed. Please refresh." |
| 422 | Validation error (bad UUID, missing field) | Show field-level errors from response body |
| 503 | LLM service unavailable | "AI feedback service is currently unavailable. Please try again later." |

### 4.5 Button State Rules

Use the draft's `status` field to control button visibility:

| Draft Status | "Generate Feedback" | "Approve" | "Publish" |
|-------------|-------------------|-----------|-----------|
| (no draft exists) | **enabled** | disabled | disabled |
| `pending` | disabled | **enabled** (TA only) | disabled |
| `approved` | disabled | disabled | **enabled** (Instructor only) |
| `published` | disabled | disabled | disabled |

### 4.6 Typical UI Flow

```
1. TA opens submission detail page
2. Call GET /submissions/{id}/feedback-drafts
3. If count == 0 → show "Generate Feedback" button
4. If count > 0 → show latest draft with status badge
5. TA clicks "Generate Feedback" → POST /submissions/{id}/generate-feedback
5. TA clicks "Generate Feedback" → POST /submissions/{id}/generate-feedback (optionally with `?version_id=...`, default is latest)
   (show spinner — may take 60-120s)
6. On success → refresh draft list
7. TA clicks on a draft → GET /feedback-drafts/{id} → show detail + evidence
8. TA clicks "Approve" → POST /feedback-drafts/{id}/approve
9. Instructor sees approved drafts → clicks "Publish"
   → POST /feedback-drafts/{id}/publish
10. Student views published feedback via GET /feedback-drafts/{id}
    (only show if status == "published")
```

---

## 5. State Machine

### Transition Table

| Current Status | Action | New Status | Who | Endpoint |
|---------------|--------|------------|-----|----------|
| (none) | generate | `pending` | TA | `POST /submissions/{id}/generate-feedback` |
| (none) | generate | `pending` | TA | `POST /submissions/{id}/generate-feedback?version_id={optional}` |
| `pending` | approve | `approved` | TA | `POST /feedback-drafts/{id}/approve` |
| `approved` | publish | `published` | Instructor | `POST /feedback-drafts/{id}/publish` |

### Invalid Transitions (return 409 Conflict)

| Current Status | Attempted Action | Reason |
|---------------|-----------------|--------|
| `pending` | publish | Must be approved first |
| `approved` | approve | Already approved |
| `published` | approve | Terminal state |
| `published` | publish | Terminal state |

### Concurrency

State transitions use `SELECT ... FOR UPDATE` (PostgreSQL row-level locking)
to prevent race conditions when multiple users attempt simultaneous transitions.

---

## 6. Logging

The feedback service provides three levels of logging:

### Service Layer Logging
- All service functions log at `INFO` level via Python's `logging` module
- Logger name: `app.services.feedback_service`
- Example log entries:
  ```
  INFO  feedback_service: list_drafts submission_id=cbca2439... count=2
  INFO  feedback_service: approve_draft draft_id=abc123... pending→approved by ta_id=xyz...
  INFO  feedback_service: trigger_generation submission_id=cbca2439... llm_time=45.2s confidence=0.82
  ```

### Demo Script Logging
- `scripts/demo_e2e.py` writes detailed logs to `logs/demo_e2e_{timestamp}.log`
- Dual handler: console (INFO) + file (DEBUG)

### Integration Test Logging
- `tests/test_e2e_integration.py` writes logs to `logs/test_integration_{date}.log`

---

## 7. Environment Setup

### Required Environment Variables

Create a `.env` file in the project root (see `.env.example` for reference):

```env
DATABASE_URL=postgresql://user:password@localhost:5432/agentic_ta
LOCAL_STORAGE_ROOT=./storage
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
OLLAMA_PROMPT_VERSION=v1.0
OLLAMA_REQUEST_TIMEOUT_SEC=120
```

### Quick Start

```bash
# 1. Setup virtual environment
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"

# 2. Copy and configure .env
cp .env.example .env
# Edit .env with your DATABASE_URL

# 3. Run database migration
psql $DATABASE_URL -f db/migration_submission_version_refactor.sql
psql $DATABASE_URL -f db/migrations/add_draft_status.sql

# 4. Start API server
uvicorn app.main:app --reload --port 8000

# 5. Verify health
curl http://localhost:8000/health
# → {"status": "ok"}

# 6. Run E2E demo (mock LLM, no Ollama required)
python scripts/demo_e2e.py --mock-llm
```

---

## 8. Testing

```bash
# Run all tests (46 total: 44 unit + 2 integration)
pytest tests/ -v

# Run only integration tests
pytest tests/ -v -m integration

# Run only unit tests (skip integration)
pytest tests/ -v -m "not integration"

# Run with coverage (if installed)
pytest tests/ -v --cov=app
```

### Test Breakdown

| Test File | Count | Scope |
|-----------|-------|-------|
| `test_local_store.py` | 12 | Storage adapter |
| `test_feedback_service.py` | 8 | Service layer business logic |
| `test_feedback_router.py` | 7 | REST endpoint integration |
| `test_llm_client.py` | 5 | LLM client (Ollama) |
| `test_schemas.py` | 3 | Pydantic schema validation |
| `test_ingestion.py` | 3 | Seed data ingestion |
| `test_feedback_packet.py` | 2 | Feedback packet builder |
| `test_deps.py` | 2 | Dependency injection |
| `test_draft_saver.py` | 2 | Draft persistence |
| `test_e2e_integration.py` | 2 | Full pipeline E2E |
| **Total** | **46** | |

---

## 9. Demo Submission IDs (Pre-loaded Seed Data)

Use these IDs when testing with the ingested seed data:

| Submission ID | Student | Assignment | Notes |
|--------------|---------|------------|-------|
| `cbca2439-5fa7-4a69-b4d5-57515f2ca8df` | S001 | HW1 | Normal, on-time, 100pts |
| `707ca4fc-2544-4810-b5f0-1f6e2bcff216` | S037 | HW1 | High similarity flag (>=0.8) |
| `9d1f65ce-3975-41de-ba09-5b4220598737` | S001 | HW1 | Attempt 2, late resubmit |

---

## 10. Quick Reference Card

```
┌─────────────────────────────────────────────────────────────────────┐
│  FEEDBACK API — QUICK REFERENCE                                     │
│                                                                     │
│  Base URL: http://localhost:8000/api                                │
│                                                                     │
│  GET  /submissions/{id}/feedback-drafts   → List drafts             │
│  GET  /feedback-drafts/{id}               → Draft detail + evidence │
│  POST /feedback-drafts/{id}/approve       → TA approves   (pending) │
│  POST /feedback-drafts/{id}/publish       → Prof publishes(approved)│
│  POST /submissions/{id}/generate-feedback → Trigger LLM   (120s!)  │
│  POST /submissions/{id}/generate-feedback?version_id={opt}     │
│      → Trigger LLM on that version (default: latest, 120s!)    │
│                                                                     │
│  Status: pending ──▶ approved ──▶ published (one-way only)          │
│                                                                     │
│  Errors: 404=not found, 409=bad transition, 503=LLM offline        │
└─────────────────────────────────────────────────────────────────────┘
```
