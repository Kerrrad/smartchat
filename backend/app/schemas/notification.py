from datetime import datetime

from app.models.enums import MessageCategoryEnum, NotificationTypeEnum
from app.schemas.common import OrmSchema


class NotificationRead(OrmSchema):
    id: int
    title: str
    body: str
    type: NotificationTypeEnum
    message_category: MessageCategoryEnum | None = None
    related_message_id: int | None = None
    conversation_id: int | None = None
    is_read: bool
    read_at: datetime | None = None
    created_at: datetime
