from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MessageCategoryEnum, NotificationTypeEnum


class Notification(TimestampMixin, Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str] = mapped_column(Text(), nullable=False)
    type: Mapped[NotificationTypeEnum] = mapped_column(
        Enum(NotificationTypeEnum),
        default=NotificationTypeEnum.SYSTEM,
        nullable=False,
    )
    related_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"))
    related_conversation_id: Mapped[int | None] = mapped_column(ForeignKey("conversations.id", ondelete="SET NULL"))
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="notifications")
    related_message = relationship("Message", back_populates="notifications")
    related_conversation = relationship("Conversation")

    @property
    def conversation_id(self) -> int | None:
        if self.related_conversation_id is not None:
            return self.related_conversation_id
        if self.related_message is None:
            return None
        return self.related_message.conversation_id

    @property
    def message_category(self) -> MessageCategoryEnum | None:
        if self.related_message is None:
            return None
        return self.related_message.category
