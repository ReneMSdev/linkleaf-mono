"""Auth-domain exceptions used for consistent unauthorized responses.

These exceptions are raised by `auth/firebase_client.py` and caught in
`auth/dependencies.py` so request handlers can return clean 401 Unauthorized
HTTP responses without coupling auth internals to web framework code.
"""


class AuthException(Exception):
    """Base class for all authentication errors raised by auth components."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message

    def __str__(self) -> str:
        return self.message


class MissingTokenError(AuthException):
    """Raised when a protected request is missing an Authorization token."""

    def __init__(self, message: str = "Authentication token is missing.") -> None:
        super().__init__(message)


class InvalidTokenError(AuthException):
    """Raised when Firebase token verification fails for non-expiry reasons."""

    def __init__(self, message: str = "Authentication token is invalid.") -> None:
        super().__init__(message)


class TokenExpiredError(AuthException):
    """Raised when a provided Firebase authentication token has expired."""

    def __init__(self, message: str = "Authentication token has expired.") -> None:
        super().__init__(message)
