from datetime import datetime

from pydantic import Field

from app.models.enums import ConversationDisplayCategoryEnum, ConversationTypeEnum
from app.schemas.common import OrmSchema
from app.schemas.message import MessageRead
from app.schemas.user import UserSummary


class ConversationCreate(OrmSchema):
    type: ConversationTypeEnum = ConversationTypeEnum.DIRECT
    title: str | None = Field(default=None, max_length=255)
    participant_ids: list[int] = Field(default_factory=list)


class ConversationUpdate(OrmSchema):
    title: str = Field(min_length=3, max_length=255)


class ConversationCategoryUpdate(OrmSchema):
    category: ConversationDisplayCategoryEnum


class ConversationParticipantMutation(OrmSchema):
    participant_ids: list[int] = Field(default_factory=list, min_length=1)


class ConversationParticipantRead(OrmSchema):
    id: int
    conversation_id: int
    user_id: int
    joined_at: datetime
    last_read_at: datetime | None = None
    is_muted: bool
    display_category: ConversationDisplayCategoryEnum
    user: UserSummary


class ConversationRead(OrmSchema):
    id: int
    type: ConversationTypeEnum
    title: str | None = None
    created_by_id: int | None = None
    last_message_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    participants: list[ConversationParticipantRead]


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]
