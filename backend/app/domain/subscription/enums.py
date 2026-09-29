from __future__ import annotations

from enum import StrEnum


class SubscriptionPlan(StrEnum):
    FREE = "free"
    PREMIUM = "premium"


class SubscriptionStatus(StrEnum):
    ACTIVE = "active"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIALING = "trialing"


class SubscriptionProvider(StrEnum):
    STRIPE = "stripe"
    APPLE = "apple"
    GOOGLE_PLAY = "google_play"
