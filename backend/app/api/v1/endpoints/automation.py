from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.automation import (
    AutoResponderRuleCreate,
    AutoResponderRuleRead,
    AutoResponderRuleUpdate,
    AutomationLogRead,
)
from app.services import autoresponder_service

router = APIRouter()


@router.get("/rules", response_model=list[AutoResponderRuleRead])
async def list_rules(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[AutoResponderRuleRead]:
    rules = await autoresponder_service.list_rules(session, current_user.id)
    return [AutoResponderRuleRead.model_validate(rule) for rule in rules]


@router.post("/rules", response_model=AutoResponderRuleRead, status_code=status.HTTP_201_CREATED)
async def create_rule(
    payload: AutoResponderRuleCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AutoResponderRuleRead:
    rule = await autoresponder_service.create_rule(session, user=current_user, payload=payload)
    return AutoResponderRuleRead.model_validate(rule)


@router.patch("/rules/{rule_id}", response_model=AutoResponderRuleRead)
async def update_rule(
    rule_id: int,
    payload: AutoResponderRuleUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> AutoResponderRuleRead:
    rule = await autoresponder_service.update_rule(session, user=current_user, rule_id=rule_id, payload=payload)
    return AutoResponderRuleRead.model_validate(rule)


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, str]:
    await autoresponder_service.delete_rule(session, user=current_user, rule_id=rule_id)
    return {"detail": "Reguła została usunięta."}


@router.get("/history", response_model=list[AutomationLogRead])
async def list_history(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[AutomationLogRead]:
    logs = await autoresponder_service.list_automation_history(session, user=current_user)
    return [AutomationLogRead.model_validate(log) for log in logs]

