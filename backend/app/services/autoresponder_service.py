from datetime import datetime
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.time import utcnow
from app.models.automation import AutoResponderRule, AutomationLog
from app.models.conversation import Conversation
from app.models.conversation import ConversationParticipant
from app.models.enums import (
    AutoResponderTriggerEnum,
    ConversationTypeEnum,
    MessageCategoryEnum,
    NotificationTypeEnum,
)
from app.models.message import Message
from app.models.user import User
from app.schemas.automation import AutoResponderRuleCreate, AutoResponderRuleUpdate
from app.services.audit_service import log_event
from app.services.notification_service import create_notification


async def list_rules(session: AsyncSession, user_id: int) -> list[AutoResponderRule]:
    result = await session.execute(
        select(AutoResponderRule)
        .where(AutoResponderRule.user_id == user_id)
        .order_by(AutoResponderRule.created_at.desc())
    )
    return list(result.scalars().unique())


async def create_rule(
    session: AsyncSession,
    *,
    user: User,
    payload: AutoResponderRuleCreate,
) -> AutoResponderRule:
    rule = AutoResponderRule(user_id=user.id, **payload.model_dump())
    session.add(rule)
    await log_event(
        session,
        event_type="autoresponder.rule.create",
        source="autoresponder_service",
        message=f"Dodano regułę autorespondera {payload.name}.",
        user_id=user.id,
        payload={"trigger_type": payload.trigger_type.value},
    )
    await session.commit()
    await session.refresh(rule)
    return rule


async def update_rule(
    session: AsyncSession,
    *,
    user: User,
    rule_id: int,
    payload: AutoResponderRuleUpdate,
) -> AutoResponderRule:
    rule = await session.get(AutoResponderRule, rule_id)
    if rule is None or rule.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono reguły.")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, field, value)
    session.add(rule)
    await log_event(
        session,
        event_type="autoresponder.rule.update",
        source="autoresponder_service",
        message=f"Zmieniono regułę autorespondera {rule.name}.",
        user_id=user.id,
        payload={"rule_id": rule.id},
    )
    await session.commit()
    await session.refresh(rule)
    return rule


async def delete_rule(session: AsyncSession, *, user: User, rule_id: int) -> None:
    rule = await session.get(AutoResponderRule, rule_id)
    if rule is None or rule.user_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono reguły.")

    await log_event(
        session,
        event_type="autoresponder.rule.delete",
        source="autoresponder_service",
        message=f"Usunięto regułę autorespondera {rule.name}.",
        user_id=user.id,
        payload={"rule_id": rule.id},
    )
    await session.delete(rule)
    await session.commit()


def _matches_off_hours(rule: AutoResponderRule, now_local: datetime) -> bool:
    if rule.active_from is None or rule.active_to is None:
        return True
    current = now_local.time()
    return current < rule.active_from or current > rule.active_to


def _matches_keyword(rule: AutoResponderRule, message: Message) -> bool:
    if not rule.trigger_value:
        return False
    keywords = [item.strip().lower() for item in rule.trigger_value.split(",") if item.strip()]
    return any(keyword in message.content.lower() for keyword in keywords)


def _matches_question(rule: AutoResponderRule, message: Message) -> bool:
    return message.category == MessageCategoryEnum.QUESTION or "?" in message.content


def _find_matching_rule(rules: list[AutoResponderRule], message: Message) -> AutoResponderRule | None:
    now_local = datetime.now(ZoneInfo(settings.app_timezone))
    for rule in rules:
        if not rule.enabled:
            continue
        if rule.trigger_type == AutoResponderTriggerEnum.OFF_HOURS and _matches_off_hours(rule, now_local):
            return rule
        if rule.trigger_type == AutoResponderTriggerEnum.KEYWORD and _matches_keyword(rule, message):
            return rule
        if rule.trigger_type == AutoResponderTriggerEnum.QUESTION and _matches_question(rule, message):
            return rule
    return None


async def process_message_automation(
    session: AsyncSession,
    *,
    message_id: int,
) -> list[Message]:
    result = await session.execute(
        select(Message)
        .where(Message.id == message_id)
        .options(selectinload(Message.conversation), selectinload(Message.sender))
    )
    message = result.scalar_one_or_none()
    if message is None or message.is_deleted or message.is_automated or message.is_spam:
        return []
    if message.conversation is None or message.conversation.type != ConversationTypeEnum.DIRECT:
        return []

    participants_result = await session.execute(
        select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == message.conversation_id,
            ConversationParticipant.user_id != message.sender_id,
        )
    )
    recipient_ids = list(participants_result.scalars().unique())
    if not recipient_ids:
        return []

    rules_result = await session.execute(
        select(AutoResponderRule)
        .where(AutoResponderRule.user_id.in_(recipient_ids), AutoResponderRule.enabled.is_(True))
        .order_by(AutoResponderRule.id.asc())
    )
    rules_by_user: dict[int, list[AutoResponderRule]] = {}
    for rule in list(rules_result.scalars().unique()):
        rules_by_user.setdefault(rule.user_id, []).append(rule)

    created_messages: list[Message] = []

    for recipient_id in recipient_ids:
        duplicate_check = await session.execute(
            select(Message).where(
                Message.parent_message_id == message.id,
                Message.sender_id == recipient_id,
                Message.is_automated.is_(True),
            )
        )
        if duplicate_check.scalar_one_or_none():
            continue

        matched_rule = _find_matching_rule(rules_by_user.get(recipient_id, []), message)
        if matched_rule is None:
            continue

        auto_message = Message(
            conversation_id=message.conversation_id,
            sender_id=recipient_id,
            parent_message_id=message.id,
            content=matched_rule.response_text,
            category=MessageCategoryEnum.PRIVATE,
            status=message.status,
            is_automated=True,
            analysis_metadata={"rule_id": matched_rule.id, "rule_name": matched_rule.name},
        )
        session.add(auto_message)
        conversation = await session.get(Conversation, message.conversation_id)
        if conversation is not None:
            conversation.last_message_at = utcnow()
            session.add(conversation)
        await session.flush()

        session.add(
            AutomationLog(
                user_id=recipient_id,
                message_id=message.id,
                action_type="autoresponder.reply",
                success=True,
                details={
                    "rule_id": matched_rule.id,
                    "rule_name": matched_rule.name,
                    "generated_message_id": auto_message.id,
                },
            )
        )

        await create_notification(
            session,
            user_id=recipient_id,
            title="Automatyczna odpowiedź",
            body="Wygenerowano odpowiedź automatyczną.",
            notification_type=NotificationTypeEnum.AUTOMATION,
            related_message_id=auto_message.id,
        )

        await log_event(
            session,
            event_type="autoresponder.reply",
            source="autoresponder_service",
            message=f"Wygenerowano automatyczną odpowiedź dla wiadomości {message.id}.",
            user_id=recipient_id,
            payload={"rule_id": matched_rule.id, "message_id": message.id},
        )
        created_messages.append(auto_message)

    if created_messages:
        await session.commit()
        for auto_message in created_messages:
            await session.refresh(auto_message)
    return created_messages


async def list_automation_history(session: AsyncSession, *, user: User) -> list[AutomationLog]:
    result = await session.execute(
        select(AutomationLog)
        .where(AutomationLog.user_id == user.id)
        .order_by(AutomationLog.created_at.desc())
        .limit(100)
    )
    return list(result.scalars().unique())
