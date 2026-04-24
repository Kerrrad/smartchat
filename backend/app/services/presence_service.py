from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.enums import UserStatusEnum
from app.models.user import User


async def update_presence(
    session: AsyncSession,
    *,
    user: User,
    status: UserStatusEnum,
) -> User:
    user.status = status
    user.last_seen = utcnow()
    session.add(user)
    await session.flush()
    return user


async def reset_stale_online_users(session: AsyncSession) -> None:
    await session.execute(
        update(User)
        .where(User.status == UserStatusEnum.ONLINE)
        .values(status=UserStatusEnum.OFFLINE, last_seen=utcnow())
    )
    await session.flush()
