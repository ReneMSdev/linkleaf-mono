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
