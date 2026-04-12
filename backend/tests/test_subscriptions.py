"""Tests for RevenueCat webhook handler — event mapping, cascade, auth."""

from __future__ import annotations

from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus
from app.domain.subscription.models import Subscription
from tests.conftest import (
    TEST_PREMIUM_USER_ID,
    TEST_REVENUECAT_WEBHOOK_SECRET,
    TEST_USER_ID,
)

WEBHOOK_URL = "/v1/subscriptions/webhook"
# Same value as os.environ / Settings — see app/api/subscriptions.py (raw Authorization header).
WEBHOOK_SECRET = TEST_REVENUECAT_WEBHOOK_SECRET


def _event_payload(event_type: str, user_id: str) -> dict:
    return {"event": {"type": event_type, "app_user_id": user_id}}


def _webhook_headers(secret: str | None = WEBHOOK_SECRET) -> dict[str, str]:
    if secret is None:
        return {}
    return {"Authorization": secret}


class TestWebhookAuth:
    """Webhook secret verification."""

    async def test_invalid_secret_returns_401(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_USER_ID)),
            headers=_webhook_headers("wrongsecret"),
        )
        assert response.status_code == 401

    async def test_missing_auth_header_returns_401(
        self,
        anon_client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await anon_client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_USER_ID)),
            headers=_webhook_headers(None),
        )
        assert response.status_code == 401

    async def test_valid_secret_processes_event(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("RENEWAL", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


class TestIgnoredEvents:
    """Events that return 200 ignored without processing."""

    async def test_unknown_event_type_ignored(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("UNKNOWN_EVENT", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    async def test_invalid_user_id_ignored(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", "not-a-uuid"),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    async def test_user_not_found_ignored(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload(
                "INITIAL_PURCHASE",
                "00000000-0000-0000-0000-000000000000",
            ),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"

    async def test_malformed_json_ignored(
        self,
        client: AsyncClient,
        seed_free_user,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            content=b"not json",
            headers={
                **_webhook_headers(),
                "Content-Type": "application/json",
            },
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ignored"


class TestPremiumEvents:
    """Events that upgrade to premium."""

    async def test_initial_purchase_upgrades_to_premium(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200
        assert response.json()["event_type"] == "INITIAL_PURCHASE"

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.PREMIUM
        assert sub.status == SubscriptionStatus.ACTIVE
        assert "premium" in sub.entitlements

    async def test_renewal_keeps_premium(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("RENEWAL", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.PREMIUM
        assert sub.status == SubscriptionStatus.ACTIVE

    async def test_restore_activates_premium(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("RESTORE", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.PREMIUM
        assert sub.status == SubscriptionStatus.ACTIVE

    async def test_product_change_activates_premium(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("PRODUCT_CHANGE", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.PREMIUM
        assert sub.status == SubscriptionStatus.ACTIVE


class TestCancelledEvents:
    """Events that keep entitlements but mark as cancelled."""

    async def test_cancellation_keeps_entitlements(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )

        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("CANCELLATION", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.status == SubscriptionStatus.CANCELLED
        assert "premium" in sub.entitlements

    async def test_billing_issue_keeps_entitlements(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("BILLING_ISSUE", str(TEST_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.PREMIUM
        assert sub.status == SubscriptionStatus.CANCELLED
        assert "premium" in sub.entitlements

    async def test_restore_free_user_after_cancelled_tests(
        self,
        client: AsyncClient,
        seed_free_user,
        db: AsyncSession,
    ) -> None:
        """Restore free user subscription to free tier — prevents cross-module state bleed."""
        from app.domain.subscription.service import update_from_webhook

        await update_from_webhook(
            user_id=TEST_USER_ID,
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            entitlements=[],
            db=db,
        )

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(Subscription.user_id == TEST_USER_ID)
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.FREE
        assert sub.entitlements == []


class TestExpirationCascade:
    """EXPIRATION event — downgrade and cascade soft deletes."""

    async def test_expiration_downgrades_to_free(
        self,
        client: AsyncClient,
        seed_premium_user,
        db: AsyncSession,
    ) -> None:
        await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_PREMIUM_USER_ID)),
            headers=_webhook_headers(),
        )

        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("EXPIRATION", str(TEST_PREMIUM_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200
        assert response.json()["event_type"] == "EXPIRATION"

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == TEST_PREMIUM_USER_ID
            )
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.FREE
        assert sub.status == SubscriptionStatus.EXPIRED
        assert sub.entitlements == []

    async def test_expiration_soft_deletes_excess_profiles(
        self,
        client: AsyncClient,
        premium_client: AsyncClient,
        seed_premium_user,
        db: AsyncSession,
    ) -> None:
        from app.domain.profile.models import Profile

        await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_PREMIUM_USER_ID)),
            headers=_webhook_headers(),
        )

        r1 = await premium_client.post(
            "/v1/profiles",
            json={"name": "Cascade Default"},
        )
        assert r1.status_code == 201
        r2 = await premium_client.post(
            "/v1/profiles",
            json={"name": "Cascade Extra"},
        )
        assert r2.status_code == 201

        await client.post(
            WEBHOOK_URL,
            json=_event_payload("EXPIRATION", str(TEST_PREMIUM_USER_ID)),
            headers=_webhook_headers(),
        )

        db.expire_all()
        result = await db.execute(
            select(Profile).where(
                Profile.user_id == TEST_PREMIUM_USER_ID,
                Profile.deleted_at.is_(None),
            )
        )
        active_profiles = result.scalars().all()
        assert len(active_profiles) == 1
        assert active_profiles[0].is_default is True

    async def test_restore_premium_after_expiration(
        self,
        client: AsyncClient,
        seed_premium_user,
        db: AsyncSession,
    ) -> None:
        """Restore premium user after expiration tests — prevents cross-module state bleed."""
        response = await client.post(
            WEBHOOK_URL,
            json=_event_payload("INITIAL_PURCHASE", str(TEST_PREMIUM_USER_ID)),
            headers=_webhook_headers(),
        )
        assert response.status_code == 200

        db.expire_all()
        result = await db.execute(
            select(Subscription).where(
                Subscription.user_id == TEST_PREMIUM_USER_ID
            )
        )
        sub = result.scalar_one()
        assert sub.plan == SubscriptionPlan.PREMIUM
        assert sub.status == SubscriptionStatus.ACTIVE
        assert "premium" in sub.entitlements
