from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession
from redis import asyncio as redis_async

from app.core.config import settings
from app.models.audit import AuditLog
from app.models.automation import AutomationLog
from app.models.conversation import Conversation
from app.models.enums import UserStatusEnum
from app.models.message import Message
from app.models.notification import Notification
from app.models.user import User
from app.schemas.admin import DiagnosticsCheck
from app.services.audit_service import log_event
from app.services.classification_service import classifier
from app.services.spam_service import spam_detector


async def get_admin_stats(session: AsyncSession) -> dict[str, int]:
    users_count = (await session.execute(select(func.count(User.id)))).scalar_one()
    active_users_count = (
        await session.execute(select(func.count(User.id)).where(User.status != UserStatusEnum.OFFLINE))
    ).scalar_one()
    conversations_count = (await session.execute(select(func.count(Conversation.id)))).scalar_one()
    messages_count = (await session.execute(select(func.count(Message.id)))).scalar_one()
    spam_messages_count = (
        await session.execute(select(func.count(Message.id)).where(Message.is_spam.is_(True)))
    ).scalar_one()
    automated_replies_count = (
        await session.execute(select(func.count(Message.id)).where(Message.is_automated.is_(True)))
    ).scalar_one()
    notifications_count = (await session.execute(select(func.count(Notification.id)))).scalar_one()

    return {
        "users_count": users_count,
        "active_users_count": active_users_count,
        "conversations_count": conversations_count,
        "messages_count": messages_count,
        "spam_messages_count": spam_messages_count,
        "automated_replies_count": automated_replies_count,
        "notifications_count": notifications_count,
    }


async def list_users(session: AsyncSession) -> list[User]:
    result = await session.execute(select(User).order_by(User.created_at.desc()))
    return list(result.scalars().unique())


async def list_spam_messages(session: AsyncSession) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.is_spam.is_(True))
        .order_by(Message.created_at.desc())
    )
    return list(result.scalars().unique())


async def list_audit_logs(session: AsyncSession) -> list[AuditLog]:
    result = await session.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(200))
    return list(result.scalars().unique())


async def list_automation_logs(session: AsyncSession) -> list[AutomationLog]:
    result = await session.execute(
        select(AutomationLog).order_by(AutomationLog.created_at.desc()).limit(200)
    )
    return list(result.scalars().unique())


async def set_user_block_status(
    session: AsyncSession,
    *,
    admin: User,
    user_id: int,
    is_blocked: bool,
) -> User:
    user = await session.get(User, user_id)
    if user is None:
        raise ValueError("Nie znaleziono użytkownika.")

    user.is_blocked = is_blocked
    session.add(user)
    await log_event(
        session,
        event_type="admin.user.block",
        source="admin_service",
        message=f"Administrator zmienił status blokady użytkownika {user.username}.",
        user_id=admin.id,
        payload={"target_user_id": user.id, "blocked": is_blocked},
    )
    await session.commit()
    await session.refresh(user)
    return user


async def run_diagnostics(session: AsyncSession) -> list[DiagnosticsCheck]:
    checks: list[DiagnosticsCheck] = []

    try:
        await session.execute(text("SELECT 1"))
        checks.append(DiagnosticsCheck(name="database", ok=True, details="Połączenie z bazą działa poprawnie."))
    except Exception as exc:  # pragma: no cover
        checks.append(DiagnosticsCheck(name="database", ok=False, details=str(exc)))

    preview = classifier.classify("Pilne pytanie o status wdrożenia?")
    checks.append(
        DiagnosticsCheck(
            name="classifier",
            ok=preview.category.value == "urgent",
            details=f"Przykładowa klasyfikacja: {preview.category.value}.",
        )
    )

    spam_preview = spam_detector.detect("FREE MONEY!!! Kliknij https://spam.local teraz!!!")
    checks.append(
        DiagnosticsCheck(
            name="spam_detector",
            ok=spam_preview.is_spam,
            details=f"Wynik przykładowego wykrycia spamu: {spam_preview.score:.2f}.",
        )
    )

    try:
        redis_client = redis_async.from_url(settings.redis_url)
        await redis_client.ping()
        await redis_client.aclose()
        checks.append(DiagnosticsCheck(name="redis", ok=True, details="Redis odpowiada na ping."))
    except Exception as exc:  # pragma: no cover
        checks.append(DiagnosticsCheck(name="redis", ok=False, details=str(exc)))

    return checks

