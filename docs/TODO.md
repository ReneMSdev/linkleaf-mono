# TODO

## Now
<!-- What's actively being worked on. Keep this to a few items. -->
- [ ] Mobile: `test/widget_test.dart` is empty, so `flutter test` fails to compile. Add a real test or delete the file.

## Next
<!-- Planned soon, in priority order. -->

Minimal deploy for in-person networking, in order:

- [ ] Firebase console: copy the UIDs of your account and the test accounts, and add them to `ALLOWED_FIREBASE_UIDS`. Keep Anonymous sign-in off. Optionally turn off self sign-up (Authentication → Settings → User actions). The backend allowlist is already in place.
- [ ] Deploy the backend to Cloud Run with a free Postgres (Neon or Supabase) instead of Cloud SQL. Set `--max-instances=1`, a billing budget alert, `DEBUG=false`, `ALLOWED_ORIGINS`, and a long random `REVENUECAT_WEBHOOK_SECRET`. Grant yourself premium with a direct DB update; no RevenueCat needed.
- [ ] Plan the public profile page (planning only, no code). Scanning the QR code currently ends at `/p/{slug}`, which returns JSON. Decide between the backend serving HTML to browsers and a small static site, and plan the "save contact" vCard link and scope.
- [ ] Build the public profile page from that plan.
- [ ] Seed your own profile (script or API docs page), then print or share its QR code.

Other:

- [ ] Mobile: fill `analysis_options.yaml` (`include: package:flutter_lints/flutter.yaml`). It's empty now, so the lint rules aren't enforced.
- [ ] Backend coverage may be under-counted: tested async paths (e.g. vCard, link reorder) show as uncovered. Try `concurrency = greenlet` in the coverage config.
- [ ] Add mobile CI (`flutter analyze` and `flutter test`) alongside `backend.yml`.
- [ ] Document local backend setup: creating the `linkleaf_test` DB, and which `.env` vars are required (`backend/.env.example` doesn't exist).
- [ ] Replace the default Flutter boilerplate in `mobile/README.md`.

## Later
<!-- Ideas and deferred scope. It's fine for items to sit here. -->
- [ ] Working phone prototype (after the deploy steps): add `firebase_core` and run `flutterfire configure`, build a real sign-in (email/password; Google optional, which needs `google_sign_in` plus the Android SHA-1 and iOS URL scheme), wire the providers to `api_service.dart`, and make edit mode save to the API. To install on iPhone without paying:
  - **Free Apple ID, Xcode Personal Team (preferred).** Run `flutter run --release` over USB, with Developer Mode on and the profile trusted. The install expires every 7 days; AltStore or SideStore can automate re-signing. Limit of 3 sideloaded apps. Debug builds won't open from the home screen.
  - **Fallback: web build added to the home screen (PWA).** Build with `flutter build web`, host it for free, then use Safari → Add to Home Screen. No expiry, but the drag and snap animations on web are untested. The same hosting could also serve the public profile page.
- [ ] `mobile/pubspec.yaml` package name is still `linkleaf_frontend`. Rename it if wanted.
- [ ] `mobile/lib/core/constants.dart` has an unused `AppConstants.baseUrl` pointing at port 8000 (the app uses `Env.apiBaseUrl`, which defaults to 8080). Remove it.
- [ ] `backend/docker-compose.yml` still uses the `qr_backend_*` container name and `qr_app_*` DB names from the old repo.

## Done recently
<!-- /wrapup moves finished items here with a date. Keep about the last 10. -->
- [x] Backend `ALLOWED_FIREBASE_UIDS` allowlist: 403 for unlisted UIDs, no user created, and the app refuses to start in staging/production without it (2026-09-29)
