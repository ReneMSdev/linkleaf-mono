"""Firebase Admin SDK bootstrap and token verification helpers.

This module initializes the Firebase Admin SDK once at import time and exposes
`verify_token()` for validating Firebase ID tokens and returning decoded claims.
"""

from __future__ import annotations

import json

import firebase_admin
import firebase_admin.auth
import firebase_admin.credentials

from app.auth.exceptions import InvalidTokenError, TokenExpiredError
from app.config.settings import get_settings

settings = get_settings()
service_account_dict = json.loads(
    settings.FIREBASE_SERVICE_ACCOUNT_JSON.get_secret_value()
)

if not firebase_admin._apps:
    firebase_admin.initialize_app(
        firebase_admin.credentials.Certificate(service_account_dict)
    )


def verify_token(token: str) -> dict:
    """Verify a Firebase ID token and return decoded claims."""
    try:
        return firebase_admin.auth.verify_id_token(token)
    except firebase_admin.auth.ExpiredIdTokenError as exc:
        raise TokenExpiredError() from exc
    except firebase_admin.auth.InvalidIdTokenError as exc:
        raise InvalidTokenError() from exc
    except Exception as exc:
        raise InvalidTokenError(str(exc)) from exc
