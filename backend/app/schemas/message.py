from datetime import datetime
from typing import Any

from pydantic import Field

from app.models.enums import MessageCategoryEnum, MessageStatusEnum
from app.schemas.common import OrmSchema


class MessageCreate(OrmSchema):
    content: str = Field(min_length=1, max_length=5000)


class MessageUpdate(OrmSchema):
    content: str = Field(min_length=1, max_length=5000)


class MessageSender(OrmSchema):
    id: int
    username: str
    avatar_url: str | None = None
    role: str


class MessageRead(OrmSchema):
    id: int
    conversation_id: int
    sender_id: int
    parent_message_id: int | None = None
    content: str
    category: MessageCategoryEnum
    status: MessageStatusEnum
    is_spam: bool
    spam_score: float
    spam_reason: str | None = None
    is_edited: bool
    edited_at: datetime | None = None
    is_deleted: bool
    is_automated: bool
    analysis_metadata: dict[str, Any]
    created_at: datetime
    updated_at: datetime
    sender: MessageSender


class MessageAnalysisRequest(OrmSchema):
    content: str = Field(min_length=1, max_length=5000)


class MessageAnalysisPreview(OrmSchema):
    category: MessageCategoryEnum
    labels: list[str]
    reasons: list[str]
    is_spam: bool
    spam_score: float
    spam_reasons: list[str]
