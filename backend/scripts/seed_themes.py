"""Seed script — inserts initial themes into the database.

Run once after migrations:
    python scripts/seed_themes.py

Safe to re-run — skips themes that already exist by slug.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# ensure app is importable from project root
sys.path.append(str(Path(__file__).resolve().parent.parent))

import app.core.db.registry  # noqa: F401 — resolves all SQLAlchemy model relationships

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert

from app.core.db.session import AsyncSessionLocal
from app.domain.theme.models import Theme, ThemeTier

THEMES = [
    {
        "name": "Clean Light",
        "slug": "clean-light",
        "tier": ThemeTier.FREE,
        "is_active": True,
        "is_featured": True,
        "preview_url": None,
        "config": {
            "background_color": "#FFFFFF",
            "text_color": "#111111",
            "accent_color": "#3A7CA5",
            "font_family": "Inter",
            "card_style": "flat",
        },
    },
    {
        "name": "Dark Mode",
        "slug": "dark-mode",
        "tier": ThemeTier.FREE,
        "is_active": True,
        "is_featured": True,
        "preview_url": None,
        "config": {
            "background_color": "#111111",
            "text_color": "#F5F5F5",
            "accent_color": "#3A7CA5",
            "font_family": "Inter",
            "card_style": "flat",
        },
    },
    {
        "name": "Soft Neutral",
        "slug": "soft-neutral",
        "tier": ThemeTier.FREE,
        "is_active": True,
        "is_featured": False,
        "preview_url": None,
        "config": {
            "background_color": "#F5F0EB",
            "text_color": "#2E2E2E",
            "accent_color": "#A0785A",
            "font_family": "Georgia",
            "card_style": "rounded",
        },
    },
    {
        "name": "Midnight Pro",
        "slug": "midnight-pro",
        "tier": ThemeTier.PREMIUM,
        "is_active": True,
        "is_featured": True,
        "preview_url": None,
        "config": {
            "background_color": "#0D0D1A",
            "text_color": "#E8E8FF",
            "accent_color": "#7B61FF",
            "font_family": "Inter",
            "card_style": "glass",
        },
    },
    {
        "name": "Gold Executive",
        "slug": "gold-executive",
        "tier": ThemeTier.PREMIUM,
        "is_active": True,
        "is_featured": True,
        "preview_url": None,
        "config": {
            "background_color": "#1A1400",
            "text_color": "#F5E6C8",
            "accent_color": "#C9A84C",
            "font_family": "Playfair Display",
            "card_style": "bordered",
        },
    },
    {
        "name": "Neon City",
        "slug": "neon-city",
        "tier": ThemeTier.PREMIUM,
        "is_active": True,
        "is_featured": False,
        "preview_url": None,
        "config": {
            "background_color": "#0A0A0A",
            "text_color": "#FFFFFF",
            "accent_color": "#00FFB2",
            "font_family": "Space Grotesk",
            "card_style": "neon",
        },
    },
]


async def seed() -> None:
    async with AsyncSessionLocal() as db:
        inserted = 0
        skipped = 0

        for theme_data in THEMES:
            stmt = select(Theme).where(Theme.slug == theme_data["slug"])
            result = await db.execute(stmt)
            existing = result.scalar_one_or_none()

            if existing is not None:
                print(f"  skipped  {theme_data['slug']} — already exists")
                skipped += 1
                continue

            theme = Theme(**theme_data)
            db.add(theme)
            await db.flush()
            print(f"  inserted {theme_data['slug']} ({theme_data['tier']})")
            inserted += 1

        await db.commit()
        print(f"\nDone — {inserted} inserted, {skipped} skipped.")


if __name__ == "__main__":
    asyncio.run(seed())