"""FastAPI application entry point.

Wiring only — no business logic. Lifespan, CORS, and health check.
"""

from __future__ import annotations

import app.core.db.registry  # noqa: E402 — first, before any other app imports

from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import contacts, links, media, profiles, themes, users
# from app.api import subscriptions
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

# v1 router — add new routers here as api files are written
v1 = APIRouter(prefix="/v1")
v1.include_router(users.router)
v1.include_router(profiles.router)
v1.include_router(themes.router)
v1.include_router(links.router)
v1.include_router(contacts.router)
v1.include_router(media.router)
# v1.include_router(subscriptions.router)

app.include_router(v1)
# Public profile URLs — intentionally unversioned. These are permanent URLs
# printed on business cards, embedded in QR codes, and shared on social media.
# /p/{slug} and /q/{qr_token} must never change or be versioned.
app.include_router(profiles.public_router)
# Public theme URLs — unversioned, no auth
app.include_router(themes.public_router)
# Public contact URLs — unversioned, no auth
app.include_router(contacts.public_router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    """Returns service status, environment, and version for Cloud Run health checks."""
    return {
        "status": "ok",
        "environment": settings.APP_ENV.value,
        "version": "0.1.0",
    }
