# Mobile (Flutter)

Flutter (Dart SDK ^3.11), with dio for HTTP, firebase_auth, qr_flutter, and google_fonts.
The package name is `linkleaf_frontend`.

## Layout

- `lib/core/`: env, router, theme, colors, constants. `env.dart` reads compile-time `--dart-define`s.
- `lib/models/`, `lib/providers/`, `lib/services/api_service.dart`: data layer.
- `lib/screens/`: `auth/` (login, register) and `home/` (main screen plus `widgets/`).

## Commands (run in `mobile/`)

| Purpose | Command |
|---|---|
| Install | `flutter pub get` |
| Run | `flutter run --dart-define-from-file=.env.dev` |
| Build | `flutter build apk\|ipa --dart-define-from-file=.env.<staging\|prod>` |
| Test | `flutter test` |
| Lint | `flutter analyze` |

## Conventions

- Env files `.env.dev/.env.staging/.env.prod` are git-ignored and copied from `.env.example`
  (`ENV`, `API_BASE_URL`, `APP_NAME`). The local backend runs on `http://localhost:8080`.
- `analysis_options.yaml` is currently empty, so the `flutter_lints` rules aren't applied yet.
