from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.rate_limit import rate_limit
from app.core.security import create_access_token
from app.db.session import get_db
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserSummary
from app.services import auth_service
from app.services.audit_service import log_event

router = APIRouter()


@router.post("/register", response_model=UserSummary, status_code=status.HTTP_201_CREATED)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit(5, 60, "auth-register")),
) -> UserSummary:
    try:
        user = await auth_service.register_user(session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return UserSummary.model_validate(user)


@router.post("/login", response_model=TokenResponse)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_db),
    _: None = Depends(rate_limit(10, 60, "auth-login")),
) -> TokenResponse:
    user = await auth_service.authenticate_user(session, payload.login, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Nieprawidłowy login lub hasło.")

    await log_event(
        session,
        event_type="auth.login",
        source="auth_endpoint",
        message=f"Użytkownik {user.username} zalogował się do systemu.",
        user_id=user.id,
    )
    await session.commit()
    return TokenResponse(access_token=create_access_token(user.id))


@router.post("/logout")
async def logout(
    current_user=Depends(get_current_user),
    session: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    await log_event(
        session,
        event_type="auth.logout",
        source="auth_endpoint",
        message=f"Użytkownik {current_user.username} wylogował się.",
        user_id=current_user.id,
    )
    await session.commit()
    return {"detail": "Wylogowanie wykonane po stronie klienta. Token należy usunąć lokalnie."}
