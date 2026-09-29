# Backend (FastAPI)

Python 3.12 (CI and Dockerfile), FastAPI, SQLAlchemy 2 async + asyncpg, Alembic,
Pydantic settings, structlog. Auth via Firebase Admin; storage on GCS; billing
webhooks from RevenueCat.

## Layout

- `app/main.py`: wiring only (lifespan, CORS, routers). API is under `/v1`.
- `app/api/`: routers, one per domain.
- `app/domain/<name>/`: `models.py` (SQLAlchemy), `dto.py` (Pydantic), `service.py` (logic).
- `app/core/db/registry.py`: imports all models. It must be imported before other app modules.
- `app/config/settings.py`: env-driven settings. Env vars are listed in `.github/workflows/backend.yml`.
- `migrations/versions/`: Alembic revisions.
- `scripts/seed_themes.py`: seeds themes. It's idempotent: `python scripts/seed_themes.py`.

## Commands (run in `backend/`)

| Purpose | Command |
|---|---|
| Install | `pip install -r requirements-dev.txt` |
| Local Postgres | `docker compose up -d db` (user `qr_app_user` / `devpassword`, db `qr_app_db`) |
| Migrate | `alembic upgrade head` |
| Run | `uvicorn app.main:app --reload --port 8080` |
| Test | `pytest tests/ --cov=app --cov-fail-under=50` |

Tests need Postgres and a `linkleaf_test` database (override it with `TEST_DATABASE_URL`).
`tests/conftest.py` creates the tables from the models and overrides auth with fake
users (`client`, `premium_client`, `anon_client`).

## Conventions

- Schema changes go through a new Alembic revision (`alembic revision --autogenerate -m "..."`).
- CI enforces at least 50% coverage.
