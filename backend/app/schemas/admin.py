from datetime import datetime
from typing import Any

from app.schemas.common import OrmSchema
from app.schemas.user import UserSummary


class AdminStats(OrmSchema):
    users_count: int
    active_users_count: int
    conversations_count: int
    messages_count: int
    spam_messages_count: int
    automated_replies_count: int
    notifications_count: int


class AuditLogRead(OrmSchema):
    id: int
    user_id: int | None = None
    event_type: str
    level: str
    source: str
    message: str
    payload: dict[str, Any]
    created_at: datetime


class DiagnosticsCheck(OrmSchema):
    name: str
    ok: bool
    details: str


class DiagnosticsResponse(OrmSchema):
    checks: list[DiagnosticsCheck]


class AdminUserList(OrmSchema):
    items: list[UserSummary]

