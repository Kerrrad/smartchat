from datetime import datetime, time
from typing import Any

from pydantic import Field

from app.models.enums import AutoResponderTriggerEnum
from app.schemas.common import OrmSchema


class AutoResponderRuleCreate(OrmSchema):
    name: str = Field(min_length=3, max_length=255)
    trigger_type: AutoResponderTriggerEnum
    trigger_value: str | None = Field(default=None, max_length=255)
    response_text: str = Field(min_length=1, max_length=4000)
    enabled: bool = True
    active_from: time | None = None
    active_to: time | None = None


class AutoResponderRuleUpdate(OrmSchema):
    name: str | None = Field(default=None, min_length=3, max_length=255)
    trigger_type: AutoResponderTriggerEnum | None = None
    trigger_value: str | None = Field(default=None, max_length=255)
    response_text: str | None = Field(default=None, min_length=1, max_length=4000)
    enabled: bool | None = None
    active_from: time | None = None
    active_to: time | None = None


class AutoResponderRuleRead(OrmSchema):
    id: int
    user_id: int
    name: str
    trigger_type: AutoResponderTriggerEnum
    trigger_value: str | None = None
    response_text: str
    enabled: bool
    active_from: time | None = None
    active_to: time | None = None
    created_at: datetime
    updated_at: datetime


class AutomationLogRead(OrmSchema):
    id: int
    user_id: int | None = None
    message_id: int | None = None
    action_type: str
    success: bool
    details: dict[str, Any]
    created_at: datetime

