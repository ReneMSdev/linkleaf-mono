"""FastAPI application entry point.

Wiring only — no business logic. Lifespan, CORS, and health check.
"""

from __future__ import annotations

import app.core.db.registry  # noqa: E402 — first, before any other app imports

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # app.core.db.registry imported at module level above — all models registered at startup
    # firebase SDK initialized on first import of firebase_client in auth/dependencies.py
    yield
    # shutdown — nothing to teardown at MVP


app = FastAPI(
    title="QR Backend",
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# routers registered here as api files are written


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Returns service status, environment, and version for Cloud Run health checks."""
    return {
        "status": "ok",
        "environment": settings.APP_ENV.value,
        "version": "0.1.0",
    }
