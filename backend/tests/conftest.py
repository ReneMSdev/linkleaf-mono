"""Shared fixtures for the LinkLeaf test suite."""

from __future__ import annotations

import os
import uuid
from collections.abc import AsyncGenerator, AsyncIterator
from datetime import datetime, timezone
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.core.db.registry  # noqa: F401 — register all models on Base.metadata
from app.auth.dependencies import get_current_user, get_optional_user
from app.core.db.base import Base
from app.core.db.session import get_db
from app.domain.subscription.dto import SubscriptionInternal
from app.domain.subscription.enums import SubscriptionPlan, SubscriptionStatus
from app.domain.subscription.models import Subscription
from app.domain.user.dto import UserInternal
from app.domain.user.models import User
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://qr_app_user:devpassword@localhost/linkleaf_test",
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    poolclass=NullPool,
)

TestSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

TEST_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
TEST_USER_EMAIL = "test@linkleaf.co"

TEST_PREMIUM_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000002")
TEST_PREMIUM_USER_EMAIL = "premium@linkleaf.co"


def make_user_internal(
    user_id: uuid.UUID,
    email: str,
    entitlements: list[str],
) -> UserInternal:
    plan = SubscriptionPlan.FREE if not entitlements else SubscriptionPlan.PREMIUM
    now = datetime.now(timezone.utc)
    return UserInternal(
        id=user_id,
        firebase_uid=f"firebase_{user_id.hex}",
        email=email,
        display_name="Test User",
        avatar_url=None,
        is_active=True,
        is_verified=True,
        last_login_at=None,
        subscription=SubscriptionInternal(
            plan=plan,
            status=SubscriptionStatus.ACTIVE,
            is_active=True,
            trial_end=None,
            current_period_end=None,
            grace_period_end=None,
            entitlements=entitlements,
        ),
        created_at=now,
        updated_at=now,
    )


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_database() -> AsyncGenerator[None, None]:
    async with test_engine.begin() as conn:
        await conn.execute(text('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"'))
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db(setup_database: object) -> AsyncIterator[AsyncSession]:
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(loop_scope="session")
async def client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    free_user = make_user_internal(TEST_USER_ID, TEST_USER_EMAIL, [])

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    async def override_get_current_user() -> UserInternal:
        return free_user

    async def override_get_optional_user() -> UserInternal:
        return free_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_user] = override_get_optional_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def premium_client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    premium_user = make_user_internal(
        TEST_PREMIUM_USER_ID,
        TEST_PREMIUM_USER_EMAIL,
        ["premium"],
    )

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    async def override_get_current_user() -> UserInternal:
        return premium_user

    async def override_get_optional_user() -> UserInternal:
        return premium_user

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    app.dependency_overrides[get_optional_user] = override_get_optional_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(loop_scope="session")
async def anon_client(db: AsyncSession) -> AsyncIterator[AsyncClient]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db

    async def override_get_optional_user() -> UserInternal | None:
        return None

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_optional_user] = override_get_optional_user

    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as ac:
            yield ac
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def seed_free_user(db: AsyncSession) -> AsyncIterator[User]:
    from sqlalchemy import select

    # Check if user already exists before inserting
    result = await db.execute(select(User).where(User.id == TEST_USER_ID))
    existing = result.scalar_one_or_none()
    if existing is not None:
        yield existing
        return

    user = User(
        id=TEST_USER_ID,
        firebase_uid=f"firebase_{TEST_USER_ID.hex}",
        email=TEST_USER_EMAIL,
        display_name="Test User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    subscription = Subscription(
        user_id=TEST_USER_ID,
        plan=SubscriptionPlan.FREE,
        status=SubscriptionStatus.ACTIVE,
        entitlements=[],
    )
    db.add(subscription)
    await db.commit()
    yield user


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def seed_premium_user(db: AsyncSession) -> AsyncIterator[User]:
    from sqlalchemy import select

    # Check if user already exists before inserting
    result = await db.execute(select(User).where(User.id == TEST_PREMIUM_USER_ID))
    existing = result.scalar_one_or_none()
    if existing is not None:
        yield existing
        return

    user = User(
        id=TEST_PREMIUM_USER_ID,
        firebase_uid=f"firebase_{TEST_PREMIUM_USER_ID.hex}",
        email=TEST_PREMIUM_USER_EMAIL,
        display_name="Premium User",
        is_active=True,
        is_verified=True,
    )
    db.add(user)
    await db.flush()

    subscription = Subscription(
        user_id=TEST_PREMIUM_USER_ID,
        plan=SubscriptionPlan.PREMIUM,
        status=SubscriptionStatus.ACTIVE,
        entitlements=["premium"],
    )
    db.add(subscription)
    await db.commit()
    yield user
