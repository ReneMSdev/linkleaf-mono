# Status

_Last verified: 2026-09-29 at e279ab1_

Abandoned MVP, being prepared as a portfolio piece (a minimal deploy may follow).
The backend API and its test suite run locally. The Flutter app passes
default analysis, but it has no tests, no lint config, and no CI. The repo became a
monorepo on 2026-09-28 (imported from `qr_backend` and `linkleaf-frontend`).

## Backend

**State:** FastAPI app with `/v1` routers for users, profiles, themes, links, contacts,
media, and subscriptions. Public `/p/{slug}` and `/q/{qr_token}` URLs. One Alembic
revision (`acbd5984e864_initial_schema`). The `organization` domain files have no code
(0 statements).

| Check | Result | Evidence |
|---|---|---|
| Tests + coverage | passing | `pytest tests/ --cov=app --cov-fail-under=50`: 133 passed, 64.55% coverage (uncommitted allowlist change on 14d3ace, 2026-09-29). Also passes on a clean checkout with CI's env and no `.env`. Local Python 3.13 venv; CI uses 3.12. |
| UID allowlist | passing | `tests/test_auth.py` (11 tests). The two rejection tests fail against the previous auth code. |
| Migrations apply cleanly | passing | CI step `alembic upgrade head` on Postgres 16 succeeded (run 36527877807, e279ab1, 2026-09-29). |
| CI on GitHub | passing | Backend CI run 36527877807 on `ReneMSdev/linkleaf-mono`: 122 passed, 63.20% coverage, Python 3.12, no repo secrets (e279ab1, 2026-09-29). |
| Docker image builds | **unverified** | Not built. |

**Known issues:** none found in the test run. Low coverage in services: `profile/service.py` 34%, `user/service.py` 30%, `theme/service.py` 44%.

## Mobile

**State:** Flutter app with auth screens (login, register) and a home screen (profile card, QR, links, edit mode). Runs on mock data. `lib/services/api_service.dart` (dio + Firebase ID token) exists but nothing calls it, and Firebase isn't set up. The providers are empty placeholders, and the login screen is a stub that goes straight to home.

| Check | Result | Evidence |
|---|---|---|
| Static analysis | passing (weak) | `flutter analyze`: No issues found (0a11d00, 2026-09-29). `analysis_options.yaml` is empty, so the `flutter_lints` rules aren't applied. |
| Tests | **failing** | `flutter test`: `test/widget_test.dart` is empty and fails to compile ("Undefined name 'main'") (0a11d00, 2026-09-29). |
| Builds / runs on a device | **unverified** | Not run. |

**Known issues:** no tests and no CI (see TODO).

<!--
Rules for this file:
- Rewrite it to describe the current state. It isn't a log; history lives in git.
- Every "passing" or "works" claim needs evidence from a run, or it's marked unverified.
- Future work goes in TODO.md, and reasons in decisions.md.
-->
