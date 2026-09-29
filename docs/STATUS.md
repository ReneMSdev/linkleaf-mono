# Status

_Last verified: 2026-09-29 at 9d3e6d1_

Abandoned MVP, being prepared as a portfolio piece (a minimal deploy may follow).
The backend API runs locally and passes its tests in CI. The Flutter app is a UI prototype
on mock data: it builds for the web and passes default analysis, but has no tests, no lint
config and no CI. The repo became a monorepo on 2026-09-28 (imported from `qr_backend` and
`linkleaf-frontend`, both now archived on GitHub). Public at `ReneMSdev/linkleaf-mono`;
`main` is at c14bf86 and `working` is 2 commits ahead (docs only).

## Backend

**State:** FastAPI app with `/v1` routers for users, profiles, themes, links, contacts,
media, and subscriptions. Public `/p/{slug}` and `/q/{qr_token}` URLs. One Alembic
revision (`acbd5984e864_initial_schema`). The `organization` domain files have no code
(0 statements). The API is limited to allowlisted Firebase UIDs (`ALLOWED_FIREBASE_UIDS`);
the local `.env` lists 2. Diagrams are in `ARCHITECTURE.md`.

| Check | Result | Evidence |
|---|---|---|
| Tests + coverage | passing | `pytest tests/ --cov=app --cov-fail-under=50`: 133 passed, 64.55% coverage (9d3e6d1, 2026-09-29). Local Python 3.13 venv; CI uses 3.12. No backend code changed since 905a8f1. |
| UID allowlist | passing | `tests/test_auth.py` (11 tests). The two rejection tests fail against the previous auth code, with "unlisted UID was provisioned" and "user is not None" (905a8f1, 2026-09-29). |
| Runs locally | passing | Local dev DB `qr_app_db` migrated to head (`alembic current`: acbd5984e864), 6 themes seeded; uvicorn `GET /health` → 200; unauthenticated `/v1/users/me` → 401 (9d3e6d1, 2026-09-29). |
| Migrations apply cleanly | passing | CI step `alembic upgrade head` on Postgres 16 succeeded (run 36531743990, 905a8f1, 2026-09-29). |
| CI on GitHub | passing | Backend CI run 36531743990 on `ReneMSdev/linkleaf-mono`: 133 passed, 64.55% coverage, Python 3.12, no repo secrets (905a8f1, 2026-09-29). |
| No secrets in history | passing | `gitleaks detect --log-opts=--all`: 3 findings, all CocoaPods SPEC CHECKSUMS in `mobile/ios/Podfile.lock` (false positives) (9d3e6d1, 2026-09-29). |
| Docker image builds | **unverified** | Not built. |

**Known issues:**
- Restoring a soft-deleted profile or media item checks only the 30-day window, not the plan, so a user who dropped to free can restore premium content (see TODO).
- Low coverage in services: `profile/service.py` 34%, `user/service.py` 30%, `theme/service.py` 44%. Coverage may be under-counted for async paths.
- Leftover `print()` debug lines in `app/auth/dependencies.py`.

## Mobile

**State:** Flutter app with auth screens (login, register) and a home screen (profile card, QR, links, edit mode, public-profile preview). Runs on mock data. `lib/services/api_service.dart` (dio + Firebase ID token) exists but nothing calls it, and Firebase isn't set up. Most providers are empty placeholders (`SubscriptionProvider` only holds a local tier flag), and the login screen is a stub that goes straight to home.

| Check | Result | Evidence |
|---|---|---|
| Static analysis | passing (weak) | `flutter analyze`: No issues found (9d3e6d1, 2026-09-29). `analysis_options.yaml` is empty, so the `flutter_lints` rules aren't applied. |
| Tests | **failing** | `flutter test`: `test/widget_test.dart` is empty and fails to compile ("Undefined name 'main'") (9d3e6d1, 2026-09-29). |
| Web build | passing | `flutter build web --release` succeeded; home, edit and preview screens render in headless Chrome at 390×844 (9d3e6d1, 2026-09-29). |
| Runs on a phone (iOS/Android) | **unverified** | Not run. |

**Known issues:** no tests and no CI (see TODO).

## Portfolio

The LinkLeaf portfolio handoff (`ENTRY.md` + `linkleaf-1.jpg`) is in `portfolio-website/docs/portfolio-handoff/linkleaf/`, committed there as 270f2b1 on its `working` branch and not pushed. One choice is still open in it: lessons-learned option A or B.

<!--
Rules for this file:
- Rewrite it to describe the current state. It isn't a log; history lives in git.
- Every "passing" or "works" claim needs evidence from a run, or it's marked unverified.
- Future work goes in TODO.md, and reasons in decisions.md.
-->
