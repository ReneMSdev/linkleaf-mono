import asyncio
import uuid

import app.domain.user.models  # noqa: F401
import app.domain.subscription.models  # noqa: F401
import app.domain.profile.models  # noqa: F401
import app.domain.theme.models  # noqa: F401
import app.domain.media.models  # noqa: F401
import app.domain.link.models  # noqa: F401
import app.domain.contact.models  # noqa: F401
import app.domain.organization.models  # noqa: F401

from app.core.db.session import AsyncSessionLocal
from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus
from app.domain.subscription.service import update_from_webhook

USER_ID = "2521e423-86a1-4bce-a5fe-f5b8e340f52d"

async def test():
    async with AsyncSessionLocal() as db:
        await update_from_webhook(
            user_id=USER_ID,
            plan=SubscriptionPlan.FREE,
            status=SubscriptionStatus.ACTIVE,
            entitlements=[],
            db=db,
        )
        print("Downgrade to free")

asyncio.run(test())