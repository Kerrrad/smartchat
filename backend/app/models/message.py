from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, Float, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import MessageCategoryEnum, MessageStatusEnum


class Message(TimestampMixin, Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    conversation_id: Mapped[int] = mapped_column(ForeignKey("conversations.id", ondelete="CASCADE"), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    parent_message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"))
    content: Mapped[str] = mapped_column(Text(), nullable=False)
    category: Mapped[MessageCategoryEnum] = mapped_column(
        Enum(MessageCategoryEnum),
        default=MessageCategoryEnum.PRIVATE,
        nullable=False,
    )
    status: Mapped[MessageStatusEnum] = mapped_column(
        Enum(MessageStatusEnum),
        default=MessageStatusEnum.SENT,
        nullable=False,
    )
    is_spam: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    spam_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    spam_reason: Mapped[str | None] = mapped_column(Text(), nullable=True)
    is_edited: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    edited_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_automated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    analysis_metadata: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    conversation = relationship("Conversation", back_populates="messages")
    sender = relationship("User", back_populates="sent_messages")
    parent_message = relationship("Message", remote_side=[id])
    notifications = relationship("Notification", back_populates="related_message")
    automation_logs = relationship("AutomationLog", back_populates="message")
