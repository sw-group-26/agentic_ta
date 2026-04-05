"""Local dev FastAPI application.

Temporary entry point until Colleague A provides the shared app.
Once Colleague A's app is ready, register feedback_router there
and retire or keep this file for local-only development.

Usage::

    uvicorn app.main:app --reload --port 8000
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Agentic TA (Local Dev)",
    version="0.1.0",
    description="AI-Powered Grading Assistant — local dev server",
)

# ---------------------------------------------------------------------------
# CORS middleware (for Colleague B frontend integration)
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # dev only; restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health check endpoint
# ---------------------------------------------------------------------------
@app.get("/health")
def health_check() -> dict[str, str]:
    """Return server health status.

    Returns:
        {"status": "ok"}
    """
    return {"status": "ok"}


# ---------------------------------------------------------------------------
# Router registration (activate after Step 4 creates feedback_router)
# ---------------------------------------------------------------------------
# TODO: Uncomment after Step 4 completion
# from app.routers.feedback import router as feedback_router
# app.include_router(feedback_router, prefix="/api")
