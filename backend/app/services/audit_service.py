from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit import AuditLog


async def log_event(
    session: AsyncSession,
    *,
    event_type: str,
    source: str,
    message: str,
    user_id: int | None = None,
    level: str = "INFO",
    payload: dict[str, Any] | None = None,
) -> AuditLog:
    log = AuditLog(
        user_id=user_id,
        event_type=event_type,
        level=level,
        source=source,
        message=message,
        payload=payload or {},
    )
    session.add(log)
    await session.flush()
    return log

