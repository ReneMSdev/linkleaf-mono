from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from app.core.types import ThemeID


class ThemeResponse(BaseModel):
    id: ThemeID
    name: str
    slug: str
    tier: str
    preview_url: str | None
    config: dict
    is_locked: bool = False
    is_featured: bool = False

    model_config = ConfigDict(from_attributes=True)


class ThemeInternal(BaseModel):
    id: ThemeID
    name: str
    slug: str
    tier: str
    config: dict
    is_active: bool
    is_featured: bool

    model_config = ConfigDict(from_attributes=True)
