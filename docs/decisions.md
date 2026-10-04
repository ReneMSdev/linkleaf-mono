# Decisions

Append-only log of choices made and why. Newest at the bottom. Don't edit old
entries: if a decision is reversed, add a new entry that references the old one.

<!-- Entry format:

## YYYY-MM-DD: {{Short title}}

**Decision:** {{what was chosen}}
**Alternatives:** {{what else was considered}}
**Why:** {{the reason, including constraints at the time}}

-->

## 2026-09-28: Public profile URLs are unversioned and permanent (imported)

**Decision:** `/p/{slug}` and `/q/{qr_token}` live outside the `/v1` router and never change.
**Alternatives:** Versioning them with the rest of the API.
**Why:** They are printed on business cards, encoded in QR codes, and shared on social media. Source: comment in `backend/app/main.py`.

## 2026-09-28: Merge backend and mobile into one monorepo (imported)

**Decision:** Combine `qr_backend` and `linkleaf-frontend` into `backend/` and `mobile/`, keeping each repo's history. Backend CI moved to the repo root with path filters.
**Alternatives:** Unknown.
**Why:** Unknown. Recorded from git history (commits `8282f49` to `120cdc2`).

## 2026-09-29: Backend CI uses fake credentials, no repository secrets

**Decision:** `backend.yml` sets placeholder values for required settings and generates a throwaway service-account key at run time. The `workflow_call` trigger and its required secrets were removed (the only caller, the stub `deploy.yml`, was deleted in `120cdc2`).
**Alternatives:** Copying the real `.env` values into GitHub secrets; a separate Firebase/GCP project for CI.
**Why:** Tests fake the logged-in user and mock storage, so CI never calls Firebase or GCS. Firebase only parses the key at import. Fake values keep production credentials out of CI and let a new repo run CI with no setup. Verified locally: 122 passed, 63.20% with no `.env`.

## 2026-09-29: Restrict the API to allowlisted Firebase UIDs, failing closed when deployed

**Decision:** `ALLOWED_FIREBASE_UIDS` limits who can use the API. Unlisted UIDs get a 403 on protected routes and are treated as anonymous on optional-auth routes, and they never get a user row. An empty list means no restriction, but settings refuse to load in `staging` or `production` with an empty list.
**Alternatives:** Relying only on Firebase's "disable sign-up" setting; allowlisting emails instead of UIDs.
**Why:** Any valid Firebase token auto-created a user, and a mobile app's Firebase config is public, so strangers could create accounts and upload to the public bucket. The backend check holds even if Firebase settings change. UIDs are fixed; emails in tokens can be unverified. Failing closed stops a deploy from going out open by accident.

## 2026-04 (imported): Backend design decisions from qr_backend

Carried over from `PROJECT_STATUS.md` and `CURSOR_INSTRUCTIONS.md` in the archived `qr_backend` repo. The ones that are easy to check (grace period, reserved slugs, signed URL expiry, vCard branding) were checked against the code on 2026-09-29.

- **Users are auto-provisioned on first Firebase login.** There's no `/register` endpoint. (Since 2026-09-29 this is restricted by the UID allowlist; see the entry above.)
- **`qr_token` is immutable** and `/q/{token}` redirects to the current slug, so slug changes never break printed codes. Old slugs go to `slug_history` for permanent 301s.
- **One umbrella `"premium"` entitlement**, not per-feature strings. The premium profile limit is 5, not unlimited, to prevent abuse. Résumés are premium-only.
- **Themes: every user sees every theme.** Premium themes show as locked rather than hidden, because visibility drives upgrades. `check_theme_allowed()` also blocks applying one by UUID through the API.
- **The vCard endpoint is public, and free-tier vCards carry a branding NOTE.** Every saved contact exposes the brand to someone new (organic acquisition). vCard 3.0 was chosen for compatibility.
- **Images are processed on the server.** Uploads go through FastAPI and Pillow to GCS; the app never uploads to GCS directly. MIME types are checked from file bytes (`python-magic`), so a renamed file can't fake its type.
- **There are two buckets.** A public one holds images; a private one holds résumés, served through 60-minute signed URLs that are generated on demand and never stored.
- **The RevenueCat webhook always returns 200** (except for a bad secret), so RevenueCat never retries edge cases. CANCELLATION keeps entitlements until EXPIRATION.
- **EXPIRATION soft-deletes content beyond the free limits.** The order matters: media on non-default profiles first, then those profiles, then the default profile's extra media.
- **Soft deletes have a 30-day grace period** and apply to profiles and media only. Owners can restore within that window through the restore endpoints. A purge job for rows and GCS files was planned but never built.
- **Planned architecture:** `linkleaf.co` would be Next.js, server-rendering `/p/{slug}` behind a CDN with a 60s TTL, and `api.linkleaf.co` would be FastAPI, both on Cloud Run. It was never built. An older note in the Cursor instructions assigned the profile viewer to Flutter web instead.

## 2026-09-29: Archive the old repos instead of deleting them; import only the useful notes

**Decision:** `qr_backend` and `linkleaf-frontend` are archived on GitHub (private, read-only, description pointing here) after their Actions secrets were deleted. Their tracking docs weren't copied wholesale: coding rules went to `backend/CLAUDE.md`, design reasons to the imported entry above, and post-MVP ideas to `TODO.md`. The local clones moved to `~/Dev/_archive/`.
**Alternatives:** Deleting the repos; copying the old status, handoff and Cursor docs into `docs/` as they were.
**Why:** All code history is already in this repo, but the old docs are only in the archived repos, and archiving is reversible. The secrets had to go first because archived repos are read-only. René didn't need the full handoff or status history, and several old claims no longer matched the code (portfolio limit 10 vs 100, an unbuilt "regenerate QR" endpoint).

## 2026-10-04: Lowercase file names in docs/

**Decision:** Every file in `docs/` uses a lowercase, hyphenated name (`status.md`, `todo.md`,
`decisions.md`, `architecture.md`, ...). A root `ARCHITECTURE.md` moves to
`docs/architecture.md`. `README.md` and `CLAUDE.md` stay uppercase at the root. Earlier
entries here keep the old names as written.
**Alternatives:** Keep the mixed casing (uppercase `STATUS.md`/`TODO.md`, lowercase
`decisions.md`).
**Why:** The user wanted consistent names. Lowercase with hyphens is the common convention
inside docs folders. Changed at the same time in the global config (`~/Dev/claude-config`).
