from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, verify_password
from app.models.enums import RoleEnum
from app.models.user import User
from app.schemas.auth import RegisterRequest
from app.services.audit_service import log_event


async def get_user_by_login(session: AsyncSession, login: str) -> User | None:
    result = await session.execute(
        select(User).where(or_(User.email == login.lower(), User.username == login))
    )
    return result.scalar_one_or_none()


async def register_user(session: AsyncSession, payload: RegisterRequest) -> User:
    existing = await session.execute(
        select(User).where(or_(User.email == payload.email.lower(), User.username == payload.username))
    )
    if existing.scalar_one_or_none():
        raise ValueError("Użytkownik o podanym adresie e-mail lub nazwie już istnieje.")

    user = User(
        email=payload.email.lower(),
        username=payload.username,
        hashed_password=get_password_hash(payload.password),
        role=RoleEnum.USER,
    )
    session.add(user)
    await session.flush()
    await log_event(
        session,
        event_type="auth.register",
        source="auth_service",
        message=f"Zarejestrowano użytkownika {user.username}.",
        user_id=user.id,
        payload={"email": user.email},
    )
    await session.commit()
    await session.refresh(user)
    return user


async def authenticate_user(session: AsyncSession, login: str, password: str) -> User | None:
    user = await get_user_by_login(session, login)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    if user.is_blocked or not user.is_active:
        return None
    return user

