# LinkLeaf

[![Backend CI](https://github.com/ReneMSdev/linkleaf-mono/actions/workflows/backend.yml/badge.svg)](https://github.com/ReneMSdev/linkleaf-mono/actions/workflows/backend.yml)

LinkLeaf is a digital business card. You build a profile with your links,
contact details, media and a theme, and share it through a short URL or a QR code.

**Status:** an MVP I stopped working on, kept here as a portfolio piece.
- **Backend:** a complete API with an automated test suite. Firebase, storage and billing are mocked in the tests, and it has never been deployed.
- **Mobile:** a UI prototype that runs on mock data and isn't connected to the API yet.

## Repository layout

| Folder | What it is |
|---|---|
| [`backend/`](backend/) | REST API: FastAPI, async SQLAlchemy, PostgreSQL, Alembic |
| [`mobile/`](mobile/) | Flutter app: profile, QR and edit-mode UI |
| [`docs/`](docs/) | Current status, backlog and decision log |

Diagrams of the system, the auth flow, the QR/public-profile flow and the subscription
lifecycle are in [`docs/architecture.md`](docs/architecture.md).

## Backend

FastAPI app running on Python 3.12, with Postgres 16. It includes a Dockerfile
aimed at Cloud Run, which hasn't been built or deployed yet. It uses these services:

- **Firebase Authentication:** verifies ID tokens.
- **Google Cloud Storage:** stores media.
- **RevenueCat:** sends subscription webhooks.

**What it does**

- **Profiles:** free users get one profile; premium users get up to five and pick a default.
  Deleted profiles can be restored within 30 days.
- **Public URLs:**
  - `/p/{slug}` returns a profile's public data as JSON. There's no web page that displays it yet.
  - `/q/{qr_token}` redirects to that page, so a printed QR code keeps working if the slug changes.
  - Old slugs are remembered and return a 301 redirect to the new one.
- **Links:** create, edit and delete links, reorder them, and count clicks.
- **Contacts:** contact details, downloadable as a vCard.
- **Media:**
  - Avatar and image uploads are converted to WebP (up to 10 MB).
  - Résumés can be PDF or Word documents (up to 5 MB).
  - Résumés and portfolio images (up to 100) are premium features.
  - Files go to public or private GCS buckets, and private files are served through signed URLs.
  - Deleted media can be restored.
- **Access control:** `ALLOWED_FIREBASE_UIDS` limits the API to listed Firebase accounts.
  Unlisted accounts get a 403 on protected routes, are treated as anonymous on public ones,
  and never get a user row. The app refuses to start in staging or production if the list is empty.
- **Themes and plans:** there are free and premium themes. Premium themes are shown as
  locked, and applying one requires a premium subscription. Subscription status is kept in
  sync through RevenueCat webhooks. When a subscription lapses, profiles and media beyond
  the free limits are soft-deleted.

**Code structure:** each domain (`app/domain/<name>/`) has three files:
- `models.py`: SQLAlchemy models
- `dto.py`: Pydantic schemas
- `service.py`: business logic

The routers in `app/api/` are mostly thin, and the API sits under `/v1`. The public
`/p` and `/q` routes sit outside it so that printed URLs never change.

**Tests:** 133 async API tests (pytest + httpx) run against a real Postgres database.
CI applies the migrations, runs the suite, and fails if coverage drops below 50%
(it's currently about 65%). CI needs no secrets: the tests fake the signed-in user and
mock storage and image processing, and the workflow generates a throwaway service-account key.

## Mobile

A Flutter app built around the profile card:

- a draggable card sheet with snap points
- a QR code that grows as you pull the card down
- link and contact "pills"
- a portfolio carousel and a résumé widget
- a full-screen edit mode with animated transitions
- sections locked for free-tier users

In debug builds, a button switches between the free and premium layouts.

It currently shows mock data. The login screen is a stub: its button goes straight to the home
screen. An API client (`lib/services/api_service.dart`, built on dio and Firebase ID tokens)
exists but isn't connected yet, and Firebase isn't set up in the app. The state providers are
placeholders, and there are no tests yet (`test/widget_test.dart` is empty).

## Running locally

**Backend** (needs Docker, Python 3.12 and libmagic, e.g. `brew install libmagic`):

```bash
cd backend
docker compose up -d db                        # Postgres 16 on localhost:5432
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
# create backend/.env (see below), then:
alembic upgrade head
python scripts/seed_themes.py
uvicorn app.main:app --reload --port 8080
```

`backend/.env` needs these settings:

- `APP_NAME`, `DATABASE_URL`, `SECRET_KEY`, `PUBLIC_BASE_URL` (and optionally `ALLOWED_ORIGINS`)
- `FIREBASE_PROJECT_ID`, `FIREBASE_SERVICE_ACCOUNT_JSON`
- `GCS_PROJECT_ID`, `GCS_PUBLIC_BUCKET_NAME`, `GCS_PRIVATE_BUCKET_NAME`, `GCS_SERVICE_ACCOUNT_JSON`
- `REVENUECAT_WEBHOOK_SECRET`
- `ALLOWED_FIREBASE_UIDS`, a JSON list such as `["uid1","uid2"]`. It's required when
  `APP_ENV` is `staging` or `production`. Locally, leave it unset (or set it to `[]`) to allow
  any account; a bare `ALLOWED_FIREBASE_UIDS=` with no value fails to parse.

Both `*_SERVICE_ACCOUNT_JSON` values must be well-formed service-account JSON, because the
Firebase SDK parses the key at startup. Real sign-in and uploads need real Firebase and GCS
credentials.

To run the tests, create a `linkleaf_test` database in the same Postgres server, then:

```bash
pytest tests/ --cov=app --cov-fail-under=50
```

**Mobile** (needs the Flutter SDK):

```bash
cd mobile
cp .env.example .env.dev
flutter pub get
flutter run --dart-define-from-file=.env.dev
```

## History

This repo merges two earlier repositories, `qr_backend` and `linkleaf-frontend`, with
their full commit history kept. Design decisions are logged in
[`docs/decisions.md`](docs/decisions.md).
