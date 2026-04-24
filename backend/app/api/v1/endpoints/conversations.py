import asyncio

from fastapi import APIRouter, BackgroundTasks, Depends, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.config import settings
from app.core.rate_limit import rate_limit
from app.db.session import AsyncSessionLocal, get_db
from app.models.enums import MessageCategoryEnum, MessageStatusEnum
from app.models.message import Message
from app.schemas.conversation import (
    ConversationCategoryUpdate,
    ConversationCreate,
    ConversationDetail,
    ConversationParticipantMutation,
    ConversationRead,
    ConversationUpdate,
)
from app.schemas.message import (
    MessageAnalysisPreview,
    MessageAnalysisRequest,
    MessageCreate,
    MessageRead,
    MessageUpdate,
)
from app.services import autoresponder_service, message_service
from app.workers.tasks import process_message_automation_task
from app.websocket.manager import ws_manager

router = APIRouter()


def _enqueue_message_automation(message_id: int) -> None:
    if not settings.enable_celery_dispatch:
        return
    try:
        process_message_automation_task.delay(message_id)
    except Exception:
        # Inline fallback i tak uruchamia automatyzację, więc brak Redisa nie blokuje pracy aplikacji.
        return


async def _run_inline_automation(message_id: int) -> None:
    async with AsyncSessionLocal() as session:
        auto_messages = await autoresponder_service.process_message_automation(session, message_id=message_id)
        for auto_message in auto_messages:
            result = await session.execute(
                select(Message).where(Message.id == auto_message.id).options(selectinload(Message.sender))
            )
            loaded_message = result.scalar_one()
            serialized = MessageRead.model_validate(loaded_message)
            participant_ids = await message_service.get_conversation_participant_ids(
                session,
                conversation_id=auto_message.conversation_id,
                exclude_user_id=None,
            )
            await ws_manager.broadcast_to_users(
                participant_ids,
                {"type": "message.new", "message": serialized.model_dump(mode="json")},
            )


async def _broadcast_conversation_update(
    *,
    session: AsyncSession,
    conversation_id: int,
    affected_user_ids: set[int] | list[int],
    removed_user_ids: set[int] | list[int] | None = None,
) -> None:
    payload = {
        "type": "conversation.updated",
        "conversation_id": conversation_id,
    }
    await ws_manager.broadcast_to_users(set(affected_user_ids), payload)
    if removed_user_ids:
        await ws_manager.broadcast_to_users(
            set(removed_user_ids),
            {
                "type": "conversation.removed",
                "conversation_id": conversation_id,
            },
        )


@router.get("", response_model=list[ConversationRead])
async def list_conversations(
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[ConversationRead]:
    conversations = await message_service.get_user_conversations(session, current_user.id)
    return [ConversationRead.model_validate(conversation) for conversation in conversations]


@router.post("", response_model=ConversationRead, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationRead:
    conversation = await message_service.create_conversation(session, owner=current_user, payload=payload)
    return ConversationRead.model_validate(conversation)


@router.patch("/{conversation_id}", response_model=ConversationRead)
async def update_conversation(
    conversation_id: int,
    payload: ConversationUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationRead:
    conversation = await message_service.update_group_conversation(
        session,
        conversation_id=conversation_id,
        actor=current_user,
        title=payload.title,
    )
    participant_ids = await message_service.get_conversation_participant_ids(
        session,
        conversation_id=conversation_id,
        exclude_user_id=None,
    )
    await _broadcast_conversation_update(
        session=session,
        conversation_id=conversation_id,
        affected_user_ids=participant_ids,
    )
    return ConversationRead.model_validate(conversation)


@router.patch("/{conversation_id}/category", response_model=ConversationRead)
async def update_conversation_category(
    conversation_id: int,
    payload: ConversationCategoryUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationRead:
    conversation = await message_service.update_conversation_category(
        session,
        conversation_id=conversation_id,
        actor=current_user,
        category=payload.category,
    )
    await _broadcast_conversation_update(
        session=session,
        conversation_id=conversation_id,
        affected_user_ids=[current_user.id],
    )
    return ConversationRead.model_validate(conversation)


@router.post("/{conversation_id}/participants", response_model=ConversationRead)
async def add_participants(
    conversation_id: int,
    payload: ConversationParticipantMutation,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationRead:
    conversation, added_ids = await message_service.add_group_participants(
        session,
        conversation_id=conversation_id,
        actor=current_user,
        participant_ids=payload.participant_ids,
    )
    all_ids = await message_service.get_conversation_participant_ids(
        session,
        conversation_id=conversation_id,
        exclude_user_id=None,
    )
    await _broadcast_conversation_update(
        session=session,
        conversation_id=conversation_id,
        affected_user_ids=set(all_ids + added_ids),
    )
    return ConversationRead.model_validate(conversation)


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    participant_ids = await message_service.delete_group_conversation(
        session,
        conversation_id=conversation_id,
        actor=current_user,
    )
    await ws_manager.broadcast_to_users(
        set(participant_ids),
        {
            "type": "conversation.removed",
            "conversation_id": conversation_id,
        },
    )


@router.delete("/{conversation_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> None:
    remaining_ids, removed_ids, deleted = await message_service.leave_group_conversation(
        session,
        conversation_id=conversation_id,
        actor=current_user,
    )
    if deleted:
        await ws_manager.broadcast_to_users(
            set(removed_ids),
            {
                "type": "conversation.removed",
                "conversation_id": conversation_id,
            },
        )
        return

    await _broadcast_conversation_update(
        session=session,
        conversation_id=conversation_id,
        affected_user_ids=remaining_ids,
        removed_user_ids=removed_ids,
    )


@router.delete("/{conversation_id}/participants/{participant_user_id}", response_model=ConversationRead)
async def remove_participant(
    conversation_id: int,
    participant_user_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationRead:
    conversation, removed_ids = await message_service.remove_group_participant(
        session,
        conversation_id=conversation_id,
        actor=current_user,
        participant_user_id=participant_user_id,
    )
    remaining_ids = await message_service.get_conversation_participant_ids(
        session,
        conversation_id=conversation_id,
        exclude_user_id=None,
    )
    await _broadcast_conversation_update(
        session=session,
        conversation_id=conversation_id,
        affected_user_ids=remaining_ids,
        removed_user_ids=removed_ids,
    )
    return ConversationRead.model_validate(conversation)


@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> ConversationDetail:
    conversation = await message_service.get_conversation_for_user(
        session,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return ConversationDetail.model_validate(conversation)


@router.get("/{conversation_id}/messages", response_model=list[MessageRead])
async def list_messages(
    conversation_id: int,
    query_text: str | None = Query(default=None, alias="query"),
    category: MessageCategoryEnum | None = None,
    sender_id: int | None = None,
    status_filter: MessageStatusEnum | None = Query(default=None, alias="status"),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[MessageRead]:
    messages = await message_service.list_messages(
        session,
        conversation_id=conversation_id,
        user_id=current_user.id,
        query=query_text,
        category=category,
        sender_id=sender_id,
        status_filter=status_filter,
    )
    return [MessageRead.model_validate(message) for message in messages]


@router.post("/{conversation_id}/messages", response_model=MessageRead, status_code=status.HTTP_201_CREATED)
async def send_message(
    conversation_id: int,
    payload: MessageCreate,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
    _: None = Depends(rate_limit(25, 60, "send-message")),
) -> MessageRead:
    message, recipient_ids = await message_service.send_message(
        session,
        sender=current_user,
        conversation_id=conversation_id,
        payload=payload,
        online_user_ids=ws_manager.online_user_ids(),
    )
    serialized = MessageRead.model_validate(message)
    await ws_manager.broadcast_to_users(
        set(recipient_ids + [current_user.id]),
        {"type": "message.new", "message": serialized.model_dump(mode="json")},
    )

    asyncio.create_task(_run_inline_automation(message.id))
    background_tasks.add_task(_enqueue_message_automation, message.id)
    return serialized


@router.patch("/messages/{message_id}", response_model=MessageRead)
async def update_message(
    message_id: int,
    payload: MessageUpdate,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MessageRead:
    message = await message_service.update_message(session, user=current_user, message_id=message_id, payload=payload)
    serialized = MessageRead.model_validate(message)
    recipient_ids = await message_service.get_conversation_participant_ids(
        session,
        conversation_id=message.conversation_id,
        exclude_user_id=None,
    )
    await ws_manager.broadcast_to_users(
        recipient_ids,
        {"type": "message.updated", "message": serialized.model_dump(mode="json")},
    )
    return serialized


@router.delete("/messages/{message_id}", response_model=MessageRead)
async def delete_message(
    message_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> MessageRead:
    message = await message_service.delete_message(session, user=current_user, message_id=message_id)
    serialized = MessageRead.model_validate(message)
    recipient_ids = await message_service.get_conversation_participant_ids(
        session,
        conversation_id=message.conversation_id,
        exclude_user_id=None,
    )
    await ws_manager.broadcast_to_users(
        recipient_ids,
        {"type": "message.deleted", "message": serialized.model_dump(mode="json")},
    )
    return serialized


@router.post("/{conversation_id}/read")
async def mark_conversation_as_read(
    conversation_id: int,
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> dict[str, list[int]]:
    updated_ids = await message_service.mark_conversation_as_read(
        session,
        conversation_id=conversation_id,
        user=current_user,
    )
    recipient_ids = await message_service.get_conversation_participant_ids(
        session,
        conversation_id=conversation_id,
        exclude_user_id=None,
    )
    await ws_manager.broadcast_to_users(
        recipient_ids,
        {
            "type": "message.status",
            "conversation_id": conversation_id,
            "status": "read",
            "message_ids": updated_ids,
            "user_id": current_user.id,
        },
    )
    return {"message_ids": updated_ids}


@router.get("/messages/search", response_model=list[MessageRead])
async def search_messages_globally(
    q: str = Query(..., min_length=1),
    session: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
) -> list[MessageRead]:
    messages = await message_service.search_messages_globally(session, user=current_user, query=q)
    return [MessageRead.model_validate(message) for message in messages]


@router.post("/messages/analyze", response_model=MessageAnalysisPreview)
async def analyze_message(payload: MessageAnalysisRequest) -> MessageAnalysisPreview:
    classification, spam = message_service.analyze_message(payload.content)
    return MessageAnalysisPreview(
        category=classification.category,
        confidence=classification.confidence,
        labels=classification.labels,
        reasons=classification.reasons,
        is_spam=spam.is_spam,
        spam_score=spam.score,
        spam_reasons=spam.reasons,
    )
