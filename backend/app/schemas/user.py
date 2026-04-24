from datetime import datetime
from typing import Any

from pydantic import Field, field_validator

from app.models.enums import RoleEnum, UserStatusEnum
from app.schemas.common import OrmSchema


class UserSummary(OrmSchema):
    id: int
    email: str
    username: str
    role: RoleEnum
    status: UserStatusEnum
    avatar_url: str | None = None
    bio: str | None = None
    is_active: bool
    is_blocked: bool
    last_seen: datetime | None = None
    privacy_settings: dict[str, Any]
    notification_settings: dict[str, Any]
    created_at: datetime
    updated_at: datetime


class UserUpdate(OrmSchema):
    username: str | None = Field(default=None, min_length=3, max_length=50)
    bio: str | None = Field(default=None, max_length=40)
    avatar_url: str | None = Field(default=None, max_length=512)
    status: UserStatusEnum | None = None
    privacy_settings: dict[str, Any] | None = None
    notification_settings: dict[str, Any] | None = None

    @field_validator("bio")
    @classmethod
    def validate_bio_length(cls, value: str | None) -> str | None:
        if value is not None and len(value) > 40:
            raise ValueError("Bio moze miec maksymalnie 40 znakow.")
        return value


class UserSearchResult(OrmSchema):
    items: list[UserSummary]
