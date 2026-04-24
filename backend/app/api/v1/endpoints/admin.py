from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.db.session import get_db
from app.schemas.admin import AdminStats, AdminUserList, AuditLogRead, DiagnosticsResponse
from app.schemas.automation import AutomationLogRead
from app.schemas.message import MessageRead
from app.schemas.user import UserSummary
from app.services import admin_service

router = APIRouter()


@router.get("/stats", response_model=AdminStats)
async def get_stats(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_admin),
) -> AdminStats:
    return AdminStats(**(await admin_service.get_admin_stats(session)))


@router.get("/users", response_model=AdminUserList)
async def list_users(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_admin),
) -> AdminUserList:
    users = await admin_service.list_users(session)
    return AdminUserList(items=[UserSummary.model_validate(user) for user in users])


@router.post("/users/{user_id}/block", response_model=UserSummary)
async def block_user(
    user_id: int,
    is_blocked: bool = True,
    session: AsyncSession = Depends(get_db),
    admin=Depends(get_current_admin),
) -> UserSummary:
    try:
        user = await admin_service.set_user_block_status(
            session,
            admin=admin,
            user_id=user_id,
            is_blocked=is_blocked,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return UserSummary.model_validate(user)


@router.get("/spam", response_model=list[MessageRead])
async def list_spam(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_admin),
) -> list[MessageRead]:
    messages = await admin_service.list_spam_messages(session)
    return [MessageRead.model_validate(message) for message in messages]


@router.get("/audit-logs", response_model=list[AuditLogRead])
async def list_audit_logs(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_admin),
) -> list[AuditLogRead]:
    logs = await admin_service.list_audit_logs(session)
    return [AuditLogRead.model_validate(log) for log in logs]


@router.get("/automation-logs", response_model=list[AutomationLogRead])
async def list_automation_logs(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_admin),
) -> list[AutomationLogRead]:
    logs = await admin_service.list_automation_logs(session)
    return [AutomationLogRead.model_validate(log) for log in logs]


@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def diagnostics(
    session: AsyncSession = Depends(get_db),
    _: object = Depends(get_current_admin),
) -> DiagnosticsResponse:
    return DiagnosticsResponse(checks=await admin_service.run_diagnostics(session))

