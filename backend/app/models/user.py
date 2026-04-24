from datetime import datetime
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin
from app.models.enums import RoleEnum, UserStatusEnum


def default_privacy_settings() -> dict[str, Any]:
    return {
        "profile_visible": True,
        "allow_group_invites": True,
        "show_online_status": True,
    }


def default_notification_settings() -> dict[str, Any]:
    return {
        "web_push": True,
        "email": False,
        "automation_alerts": True,
    }


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[RoleEnum] = mapped_column(Enum(RoleEnum), default=RoleEnum.USER, nullable=False)
    status: Mapped[UserStatusEnum] = mapped_column(
        Enum(UserStatusEnum),
        default=UserStatusEnum.OFFLINE,
        nullable=False,
    )
    bio: Mapped[str | None] = mapped_column(Text(), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(512), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_seen: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    privacy_settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=default_privacy_settings)
    notification_settings: Mapped[dict[str, Any]] = mapped_column(JSON, default=default_notification_settings)

    conversations = relationship("ConversationParticipant", back_populates="user", cascade="all, delete-orphan")
    sent_messages = relationship("Message", back_populates="sender")
    notifications = relationship("Notification", back_populates="user")
    autoresponder_rules = relationship(
        "AutoResponderRule",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    audit_logs = relationship("AuditLog", back_populates="user")
    automation_logs = relationship("AutomationLog", back_populates="user")
