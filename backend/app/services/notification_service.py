from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.time import utcnow
from app.models.message import Message
from app.models.enums import NotificationTypeEnum
from app.models.notification import Notification


async def _resolve_conversation_id(
    session: AsyncSession,
    *,
    related_message_id: int | None,
    related_conversation_id: int | None,
) -> int | None:
    if related_conversation_id is not None:
        return related_conversation_id
    if related_message_id is None:
        return None

    result = await session.execute(
        select(Message.conversation_id).where(Message.id == related_message_id)
    )
    return result.scalar_one_or_none()


async def create_notification(
    session: AsyncSession,
    *,
    user_id: int,
    title: str,
    body: str,
    notification_type: NotificationTypeEnum,
    related_message_id: int | None = None,
    related_conversation_id: int | None = None,
) -> Notification:
    conversation_id = await _resolve_conversation_id(
        session,
        related_message_id=related_message_id,
        related_conversation_id=related_conversation_id,
    )

    if conversation_id is not None:
        existing_notifications_result = await session.execute(
            select(Notification).where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
                or_(
                    Notification.related_conversation_id == conversation_id,
                    Notification.related_message_id.in_(
                        select(Message.id).where(Message.conversation_id == conversation_id)
                    ),
                ),
            )
        )
        for existing_notification in existing_notifications_result.scalars().unique():
            await session.delete(existing_notification)
        await session.flush()

    notification = Notification(
        user_id=user_id,
        title=title,
        body=body,
        type=notification_type,
        related_message_id=related_message_id,
        related_conversation_id=conversation_id,
    )
    session.add(notification)
    await session.flush()
    return notification


async def list_notifications(session: AsyncSession, user_id: int) -> list[Notification]:
    result = await session.execute(
        select(Notification)
        .where(Notification.user_id == user_id)
        .options(selectinload(Notification.related_message))
        .order_by(Notification.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().unique())


async def mark_notification_as_read(
    session: AsyncSession,
    *,
    user_id: int,
    notification_id: int,
) -> Notification | None:
    result = await session.execute(
        select(Notification)
        .where(Notification.id == notification_id, Notification.user_id == user_id)
        .options(selectinload(Notification.related_message))
    )
    notification = result.scalar_one_or_none()
    if notification is None or notification.user_id != user_id:
        return None
    notification.is_read = True
    notification.read_at = utcnow()
    session.add(notification)
    await session.flush()
    return notification
