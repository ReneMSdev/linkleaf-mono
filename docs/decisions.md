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
