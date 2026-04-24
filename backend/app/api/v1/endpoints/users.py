from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import UserSearchResult, UserSummary, UserUpdate
from app.services.audit_service import log_event

router = APIRouter()


def _is_profile_visible(user: User) -> bool:
    return bool((user.privacy_settings or {}).get("profile_visible", True))


@router.get("/me", response_model=UserSummary)
async def get_me(current_user=Depends(get_current_user)) -> UserSummary:
    return UserSummary.model_validate(current_user)


@router.patch("/me", response_model=UserSummary)
async def update_me(
    payload: UserUpdate,
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> UserSummary:
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(current_user, field, value)
    session.add(current_user)
    await log_event(
        session,
        event_type="user.update",
        source="users_endpoint",
        message=f"Zaktualizowano profil użytkownika {current_user.username}.",
        user_id=current_user.id,
        payload={"fields": list(data.keys())},
    )
    await session.commit()
    await session.refresh(current_user)
    return UserSummary.model_validate(current_user)


@router.get("/search", response_model=UserSearchResult)
async def search_users(
    q: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserSearchResult:
    result = await session.execute(
        select(User)
        .where(
            User.id != current_user.id,
            or_(User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")),
        )
        .order_by(User.username.asc())
    )
    users = list(result.scalars().unique())
    users = [user for user in users if _is_profile_visible(user)][:25]
    return UserSearchResult(items=[UserSummary.model_validate(user) for user in users])


@router.get("/directory", response_model=UserSearchResult)
async def list_user_directory(
    q: str | None = Query(default=None),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> UserSearchResult:
    statement = select(User).where(User.id != current_user.id).order_by(User.username.asc())
    if q:
        statement = statement.where(or_(User.username.ilike(f"%{q}%"), User.email.ilike(f"%{q}%")))
    result = await session.execute(statement)
    users = list(result.scalars().unique())
    users = [user for user in users if _is_profile_visible(user)][:100]
    return UserSearchResult(items=[UserSummary.model_validate(user) for user in users])


@router.get("/{user_id}", response_model=UserSummary)
async def get_user(
    user_id: int,
    session: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> UserSummary:
    user = await session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono użytkownika.")
    return UserSummary.model_validate(user)
