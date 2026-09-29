# TODO

## Now
<!-- What's actively being worked on. Keep this to a few items. -->
- [ ] Mobile: `test/widget_test.dart` is empty, so `flutter test` fails to compile. Add a real test or delete the file.

## Next
<!-- Planned soon, in priority order. -->
- [ ] Mobile: fill `analysis_options.yaml` (`include: package:flutter_lints/flutter.yaml`). It's empty now, so the lint rules aren't enforced.
- [ ] Backend coverage may be under-counted: tested async paths (e.g. vCard, link reorder) show as uncovered. Try `concurrency = greenlet` in the coverage config.
- [ ] Add mobile CI (`flutter analyze` and `flutter test`) alongside `backend.yml`.
- [ ] Document local backend setup: creating the `linkleaf_test` DB, and which `.env` vars are required (`backend/.env.example` doesn't exist).
- [ ] Replace the default Flutter boilerplate in `mobile/README.md`.

## Later
<!-- Ideas and deferred scope. It's fine for items to sit here. -->
- [ ] `mobile/pubspec.yaml` package name is still `linkleaf_frontend`. Rename it if wanted.
- [ ] `mobile/lib/core/constants.dart` has an unused `AppConstants.baseUrl` pointing at port 8000 (the app uses `Env.apiBaseUrl`, which defaults to 8080). Remove it.
- [ ] `backend/docker-compose.yml` still uses the `qr_backend_*` container name and `qr_app_*` DB names from the old repo.

## Done recently
<!-- /wrapup moves finished items here with a date. Keep about the last 10. -->
