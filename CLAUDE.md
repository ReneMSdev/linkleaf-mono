# LinkLeaf

Digital profile / link page app: users build a public profile (links, contacts,
media, themes) reachable by URL and QR code, with free and premium tiers.
Stage: prototype.

## Layout

- `backend/`: FastAPI API (Python 3.12, Postgres 16, Alembic). Deployed as a Docker image to Cloud Run. See `backend/CLAUDE.md`.
- `mobile/`: Flutter client app. See `mobile/CLAUDE.md`.
- `.github/workflows/backend.yml`: backend CI (runs only on changes under `backend/`). The mobile app has no CI.
- `docs/`: project state files.

## Commands

Run from the app folder. Details are in each app's `CLAUDE.md`.

| Purpose | Command |
|---|---|
| Backend install | `cd backend && pip install -r requirements-dev.txt` |
| Backend local DB | `cd backend && docker compose up -d db` |
| Backend run | `cd backend && alembic upgrade head && uvicorn app.main:app --reload --port 8080` |
| Backend test | `cd backend && pytest tests/ --cov=app --cov-fail-under=50` |
| Mobile install | `cd mobile && flutter pub get` |
| Mobile run | `cd mobile && flutter run --dart-define-from-file=.env.dev` |
| Mobile test | `cd mobile && flutter test` |
| Mobile lint | `cd mobile && flutter analyze` |

## Project rules

- The public profile routes `/p/{slug}` and `/q/{qr_token}` are permanent (printed on
  cards and encoded in QR codes). Never rename them, version them, or change their behavior.
- The secrets files `backend/.env` and `mobile/.env.{dev,staging,prod}` are
  git-ignored. Never commit them. `mobile/.env.example` is the committed template.

## State

Current state: `docs/STATUS.md`. Backlog: `docs/TODO.md`. Decisions: `docs/decisions.md`.
