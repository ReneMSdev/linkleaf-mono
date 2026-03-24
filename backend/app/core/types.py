"""Shared type aliases for domain identifiers.

These aliases improve readability across services, DTOs, and APIs while making
identifier refactors easier if storage or ID strategies change later.
"""

from uuid import UUID

UserID = UUID
ProfileID = UUID
ThemeID = UUID
SubscriptionID = UUID
MediaID = UUID
LinkID = UUID
ContactID = UUID

SUPPORTED_IMAGE_TYPES: frozenset[str] = frozenset(
    {
        "image/jpeg",
        "image/png",
        "image/webp",
    }
)

SUPPORTED_DOCUMENT_TYPES: frozenset[str] = frozenset(
    {
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }
)

SUPPORTED_MEDIA_TYPES: frozenset[str] = SUPPORTED_IMAGE_TYPES | SUPPORTED_DOCUMENT_TYPES

RESERVED_SLUGS: frozenset[str] = frozenset({
    "q", "p", "v1", "health", "admin", "api",
    "users", "profiles", "links", "contacts",
    "media", "themes", "subscriptions", "static",
    "support", "help", "about", "terms", "privacy",
    "app",
})
