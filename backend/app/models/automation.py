from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, ForeignKey, String, Text, Time
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.time import utcnow
from app.models.base import Base, TimestampMixin
from app.models.enums import AutoResponderTriggerEnum


class AutoResponderRule(TimestampMixin, Base):
    __tablename__ = "autoresponder_rules"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    trigger_type: Mapped[AutoResponderTriggerEnum] = mapped_column(
        Enum(AutoResponderTriggerEnum),
        nullable=False,
    )
    trigger_value: Mapped[str | None] = mapped_column(String(255), nullable=True)
    response_text: Mapped[str] = mapped_column(Text(), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active_from: Mapped[Any | None] = mapped_column(Time(timezone=False), nullable=True)
    active_to: Mapped[Any | None] = mapped_column(Time(timezone=False), nullable=True)

    user = relationship("User", back_populates="autoresponder_rules")


class AutomationLog(Base):
    __tablename__ = "automation_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), index=True)
    message_id: Mapped[int | None] = mapped_column(ForeignKey("messages.id", ondelete="SET NULL"), index=True)
    action_type: Mapped[str] = mapped_column(String(255), nullable=False)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    details: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    user = relationship("User", back_populates="automation_logs")
    message = relationship("Message", back_populates="automation_logs")
