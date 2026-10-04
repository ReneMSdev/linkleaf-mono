# TODO

## Now
<!-- What's actively being worked on. Keep this to a few items. -->
- [ ] Mobile: `test/widget_test.dart` is empty, so `flutter test` fails to compile. Add a real test or delete the file.

## Next
<!-- Planned soon, in priority order. -->

Minimal deploy for in-person networking, in order:

- [ ] Firebase console: keep Anonymous sign-in off. The UIDs are already in the local `backend/.env` (2 accounts); set the same list in Cloud Run when deploying. Optionally turn off self sign-up (Authentication → Settings → User actions). The backend allowlist is already in place.
- [ ] Deploy the backend to Cloud Run with a free Postgres (Neon or Supabase) instead of Cloud SQL. Set `--max-instances=1`, a billing budget alert, `DEBUG=false`, `ALLOWED_ORIGINS`, and a long random `REVENUECAT_WEBHOOK_SECRET`. Grant yourself premium with a direct DB update; no RevenueCat needed.
- [ ] Plan the public profile page (planning only, no code). Scanning the QR code currently ends at `/p/{slug}`, which returns JSON. Decide between the backend serving HTML to browsers and a small static site, and plan the "save contact" vCard link and scope. Inputs from the old docs:
  - The original plan was Next.js server-rendering `/p/{slug}` behind a CDN with a 60s TTL (see decisions.md).
  - `ProfilePublic` already carries `is_premium` (show or hide branding), `has_sensitive_data` (privacy warning), and `contact` (show "Save contact" when it isn't null).
  - Old open design questions: portfolio layout, how to display the résumé, typed vs plain link icons.
- [ ] Build the public profile page from that plan.
- [ ] Seed your own profile (script or API docs page), then print or share its QR code.

Other:

- [ ] Portfolio: in the `portfolio-website` session, pick lessons-learned option A or B in `docs/portfolio-handoff/linkleaf/entry.md` and import the entry (its commit 270f2b1 there isn't pushed yet).
- [ ] Bug: restoring a soft-deleted profile or media item only checks the 30-day window, not the plan. A user who dropped to free can restore premium profiles, portfolio images and résumés (`profile/service.py` `restore`, `media/service.py` `restore_media`).
- [ ] Portfolio cleanup (ask before doing): the `print()` debug lines in `app/auth/dependencies.py` (swap for structlog) and the empty `organization` domain scaffold.
- [ ] Mobile: fill `analysis_options.yaml` (`include: package:flutter_lints/flutter.yaml`). It's empty now, so the lint rules aren't enforced.
- [ ] Backend coverage may be under-counted: tested async paths (e.g. vCard, link reorder) show as uncovered. Try `concurrency = greenlet` in the coverage config.
- [ ] Add mobile CI (`flutter analyze` and `flutter test`) alongside `backend.yml`.
- [ ] Replace the default Flutter boilerplate in `mobile/README.md`.

## Later
<!-- Ideas and deferred scope. It's fine for items to sit here. -->
- [ ] Working phone prototype (after the deploy steps): add `firebase_core` and run `flutterfire configure`, build a real sign-in (email/password; Google optional, which needs `google_sign_in` plus the Android SHA-1 and iOS URL scheme), wire the providers to `api_service.dart`, and make edit mode save to the API. The old frontend plan had these screens:
  - Home: the card and QR
  - Preview: renders `GET /p/{slug}`
  - Edit: reorder links, upload the avatar, edit contact details
  - Profiles tab, Themes tab (with locked states), and a hamburger drawer

  Only Home and parts of Preview and Edit exist, all on mock data. To install on iPhone without paying:
  - **Free Apple ID, Xcode Personal Team (preferred).** Run `flutter run --release` over USB, with Developer Mode on and the profile trusted. The install expires every 7 days; AltStore or SideStore can automate re-signing. Limit of 3 sideloaded apps. Debug builds won't open from the home screen.
  - **Fallback: web build added to the home screen (PWA).** Build with `flutter build web`, host it for free, then use Safari → Add to Home Screen. No expiry, but the drag and snap animations on web are untested. The same hosting could also serve the public profile page.
- [ ] Post-MVP ideas from the old status docs, none started:
  - QR scan analytics (a `qr_scan` row per `/q/{token}` hit)
  - a premium "regenerate QR" endpoint (documented but never built)
  - a purge job for soft-deleted rows and GCS files after 30 days
  - the 3-day warning before expiry soft-deletes (the `warning_sent_at` column exists, but nothing uses it yet)
  - a promo code system
  - PostHog analytics
  - `DELETE /users/me`
- [ ] Backend tweaks from the old notes:
  - rename the structlog `level` field to `severity` for Cloud Logging's filters
  - `get_subscription()` loads full relationships; add `load_only(Subscription.entitlements)`
  - the first request after a cold start fetches Firebase keys (about 500 ms); `min-instances=1` fixes it but costs money
- [ ] `mobile/pubspec.yaml` package name is still `linkleaf_frontend`. Rename it if wanted.
- [ ] `mobile/lib/core/constants.dart` has an unused `AppConstants.baseUrl` pointing at port 8000 (the app uses `Env.apiBaseUrl`, which defaults to 8080). Remove it.
- [ ] `backend/docker-compose.yml` still uses the `qr_backend_*` container name and `qr_app_*` DB names from the old repo.

## Done recently
<!-- /wrapup moves finished items here with a date. Keep about the last 10. -->
- [x] Portfolio handoff for LinkLeaf: entry, screenshot and four diagrams, verified against the code (2026-09-29)
- [x] `docs/architecture.md` with system, auth, QR/public-profile and subscription diagrams (2026-09-29)
- [x] Old repos `qr_backend` and `linkleaf-frontend` archived (secrets deleted first); useful notes imported into `docs/` and `backend/CLAUDE.md` (2026-09-29)
- [x] Document local backend setup: README "Running locally" covers the settings and the `linkleaf_test` DB (2026-09-29)
- [x] Confirmed the backend runs locally: dev DB migrated, themes seeded, `/health` 200 (2026-09-29)
- [x] Backend `ALLOWED_FIREBASE_UIDS` allowlist: 403 for unlisted UIDs, no user created, and the app refuses to start in staging/production without it (2026-09-29)
