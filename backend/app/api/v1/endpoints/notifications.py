from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.notification import NotificationRead
from app.services import notification_service

router = APIRouter()


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[NotificationRead]:
    items = await notification_service.list_notifications(session, current_user.id)
    return [NotificationRead.model_validate(item) for item in items]


@router.post("/{notification_id}/read", response_model=NotificationRead)
async def mark_notification_as_read(
    notification_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> NotificationRead:
    notification = await notification_service.mark_notification_as_read(
        session,
        user_id=current_user.id,
        notification_id=notification_id,
    )
    if notification is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono powiadomienia.")
    await session.commit()
    await session.refresh(notification)
    return NotificationRead.model_validate(notification)

