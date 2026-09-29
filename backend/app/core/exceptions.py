from __future__ import annotations


class AppException(Exception):
    """Base class for domain-level application errors.

    Raise this class (or one of its subclasses) from domain services to
    communicate business failures without coupling to HTTP/FastAPI concerns.
    """

    def __init__(
        self,
        message: str = "Application error.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        return self.message


class NotFoundError(AppException):
    """Raised when a requested resource does not exist.

    Examples include a missing profile slug or a missing user record.
    """

    def __init__(
        self,
        message: str = "Requested resource was not found.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class PermissionDeniedError(AppException):
    """Raised when a user is not allowed to perform an action.

    Use this when ownership checks fail or a user's plan does not permit
    accessing a protected capability.
    """

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ConflictError(AppException):
    """Raised when an operation would violate uniqueness or state constraints.

    A common example is trying to create or update a resource with a slug that
    is already in use.
    """

    def __init__(
        self,
        message: str = "Operation conflicts with existing data.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class ValidationError(AppException):
    """Raised when business-rule validation fails beyond schema validation.

    Use this for domain logic violations that Pydantic shape/type checks cannot
    express, such as setting a second default profile for the same user.
    """

    def __init__(
        self,
        message: str = "Business validation failed.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message=message, details=details)


class SlugMoved(Exception):
    """Raised when a slug has moved to a new value. Not an error — expected behavior.

    Carries the new slug so the API layer can issue a 301 redirect.
    """

    def __init__(self, new_slug: str) -> None:
        self.new_slug = new_slug


class PlanLimitError(PermissionDeniedError):
    """Raised when a subscription plan limit is exceeded.

    Use this when a free-tier user attempts premium-only actions, such as
    creating more profiles than their current plan allows.
    """

    def __init__(
        self,
        message: str = "Current plan limit reached.",
        details: dict | None = None,
    ) -> None:
        super().__init__(message=message, details=details)
