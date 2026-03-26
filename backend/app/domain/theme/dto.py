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
    is_locked: bool = False  # computed at service layer — never stored

    model_config = ConfigDict(from_attributes=True)


class ThemeInternal(BaseModel):
    id: ThemeID
    name: str
    slug: str
    tier: str
    config: dict
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
