"""RevenueCat webhook — subscription state sync from server notifications.

Thin route handler: verifies shared secret, maps event types, delegates to domain services.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.logging import get_logger
from app.config.settings import get_settings
from app.core.db.session import get_db
from app.core.exceptions import NotFoundError
from app.core.types import UserID
from app.domain.media import service as media_service
from app.domain.profile import service as profile_service
from app.domain.subscription import service as subscription_service
from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus
from app.domain.user import service as user_service

logger = get_logger(__name__)

# RevenueCat event type → (SubscriptionPlan, SubscriptionStatus, entitlements)
EVENT_MAP: dict[str, tuple[SubscriptionPlan, SubscriptionStatus, list[str]]] = {
    "INITIAL_PURCHASE": (SubscriptionPlan.PREMIUM, SubscriptionStatus.ACTIVE, ["premium"]),
    "RENEWAL": (SubscriptionPlan.PREMIUM, SubscriptionStatus.ACTIVE, ["premium"]),
    "RESTORE": (SubscriptionPlan.PREMIUM, SubscriptionStatus.ACTIVE, ["premium"]),
    "PRODUCT_CHANGE": (SubscriptionPlan.PREMIUM, SubscriptionStatus.ACTIVE, ["premium"]),
    "CANCELLATION": (SubscriptionPlan.PREMIUM, SubscriptionStatus.CANCELLED, ["premium"]),
    "BILLING_ISSUE": (SubscriptionPlan.PREMIUM, SubscriptionStatus.CANCELLED, ["premium"]),
    "EXPIRATION": (SubscriptionPlan.FREE, SubscriptionStatus.EXPIRED, []),
}

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


# -----------------------------------------------------------------------------
# RevenueCat POST endpoint. Authorization header must match REVENUECAT_WEBHOOK_SECRET.
# Malformed payloads and domain misses return 200 with ignored status so RevenueCat
# does not retry; only invalid secret yields 401.
# -----------------------------------------------------------------------------
@router.post("/webhook", status_code=200)
async def revenuecat_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    settings = get_settings()
    auth_header = request.headers.get("Authorization")
    if auth_header != settings.REVENUECAT_WEBHOOK_SECRET.get_secret_value():
        raise HTTPException(status_code=401, detail="Invalid webhook secret.")

    try:
        payload: dict = await request.json()
    except Exception:
        logger.warning(
            "webhook_ignored",
            reason="invalid_json",
            event_type="unknown",
        )
        return {"status": "ignored", "reason": "invalid_json"}

    event = payload.get("event") or {}
    event_type = event.get("type")
    app_user_id = event.get("app_user_id")

    if event_type not in EVENT_MAP:
        logger.warning(
            "webhook_ignored",
            reason="unknown_event_type",
            event_type=str(event_type),
        )
        return {"status": "ignored", "event_type": str(event_type)}

    try:
        user_id = UUID(app_user_id)
    except (ValueError, TypeError):
        logger.warning(
            "webhook_ignored",
            reason="invalid_user_id",
            event_type=str(event_type),
        )
        return {"status": "ignored", "reason": "invalid_user_id"}

    typed_user_id: UserID = user_id

    try:
        await user_service.get_by_id(typed_user_id, db)
    except NotFoundError:
        logger.warning(
            "webhook_ignored",
            reason="user_not_found",
            event_type=str(event_type),
        )
        return {"status": "ignored", "reason": "user_not_found"}

    plan, status, entitlements = EVENT_MAP[event_type]

    try:
        await subscription_service.update_from_webhook(
            user_id=typed_user_id,
            plan=plan,
            status=status,
            entitlements=entitlements,
            db=db,
        )
    except NotFoundError:
        logger.warning(
            "webhook_ignored",
            reason="subscription_not_found",
            event_type=str(event_type),
        )
        return {"status": "ignored", "reason": "subscription_not_found"}

    if event_type == "EXPIRATION":
        try:
            # Clear premium media on non-default profiles before those rows are soft-deleted.
            profiles_before = await profile_service.get_all(typed_user_id, db)
            for profile in profiles_before:
                if not profile.is_default:
                    await media_service.soft_delete_excess_media(profile.id, db)

            await profile_service.soft_delete_excess_profiles(typed_user_id, db)

            profiles_remaining = await profile_service.get_all(typed_user_id, db)
            for profile in profiles_remaining:
                await media_service.soft_delete_excess_media(profile.id, db)
        except Exception:
            logger.warning(
                "webhook_ignored",
                reason="expiration_cascade_failed",
                event_type=str(event_type),
            )
            return {"status": "ignored", "reason": "expiration_cascade_failed"}

        logger.info(
            "expiration_cascade_complete",
            user_id=str(typed_user_id),
        )

    logger.info(
        "webhook_processed",
        event_type=event_type,
        user_id=str(typed_user_id),
    )

    return {"status": "ok", "event_type": event_type}
