from fastapi import HTTPException, status
from sqlalchemy import and_, or_, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.time import utcnow
from app.models.conversation import Conversation, ConversationParticipant
from app.models.enums import (
    ConversationDisplayCategoryEnum,
    ConversationTypeEnum,
    MessageCategoryEnum,
    MessageStatusEnum,
    NotificationTypeEnum,
)
from app.models.message import Message
from app.models.notification import Notification
from app.models.user import User
from app.schemas.conversation import ConversationCreate
from app.schemas.message import MessageCreate, MessageUpdate
from app.services.audit_service import log_event
from app.services.classification_service import ClassificationResult, classifier
from app.services.notification_service import create_notification
from app.services.spam_service import SpamDetectionResult, spam_detector


def _is_profile_visible(user: User) -> bool:
    return bool((user.privacy_settings or {}).get("profile_visible", True))


def _build_message_notification_content(
    *,
    conversation: Conversation,
    sender: User,
    content: str,
) -> tuple[str, str]:
    preview = content[:120]
    if conversation.type == ConversationTypeEnum.GROUP:
        group_label = conversation.title or f"Grupa #{conversation.id}"
        return "Nowa wiadomość w grupie", f"Grupa: {group_label} • {sender.username}: {preview}"
    return "Nowa wiadomość", f"{sender.username}: {preview}"


async def get_user_conversations(session: AsyncSession, user_id: int) -> list[Conversation]:
    result = await session.execute(
        select(Conversation)
        .join(ConversationParticipant)
        .where(ConversationParticipant.user_id == user_id)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages).selectinload(Message.sender),
        )
        .order_by(Conversation.updated_at.desc())
    )
    return list(result.scalars().unique())


async def get_conversation_for_user(
    session: AsyncSession,
    *,
    conversation_id: int,
    user_id: int,
) -> Conversation:
    result = await session.execute(
        select(Conversation)
        .execution_options(populate_existing=True)
        .where(Conversation.id == conversation_id)
        .options(
            selectinload(Conversation.participants).selectinload(ConversationParticipant.user),
            selectinload(Conversation.messages).selectinload(Message.sender),
        )
    )
    conversation = result.scalar_one_or_none()
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono konwersacji.")

    if user_id not in {participant.user_id for participant in conversation.participants}:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak dostępu do konwersacji.")
    return conversation


async def get_conversation_participant_ids(
    session: AsyncSession,
    *,
    conversation_id: int,
    exclude_user_id: int | None = None,
) -> list[int]:
    result = await session.execute(
        select(ConversationParticipant.user_id).where(
            ConversationParticipant.conversation_id == conversation_id
        )
    )
    ids = list(result.scalars())
    return [item for item in ids if item != exclude_user_id]


async def _find_direct_conversation(
    session: AsyncSession,
    *,
    user_id: int,
    other_user_id: int,
) -> Conversation | None:
    conversations = await get_user_conversations(session, user_id)
    for conversation in conversations:
        if conversation.type != ConversationTypeEnum.DIRECT:
            continue
        participant_ids = {participant.user_id for participant in conversation.participants}
        if participant_ids == {user_id, other_user_id}:
            return conversation
    return None


async def create_conversation(
    session: AsyncSession,
    *,
    owner: User,
    payload: ConversationCreate,
) -> Conversation:
    participant_ids = list(dict.fromkeys([owner.id, *payload.participant_ids]))
    if payload.type == ConversationTypeEnum.DIRECT:
        if len(participant_ids) != 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Konwersacja prywatna musi mieć dokładnie 2 uczestników.",
            )
        other_user_id = next(item for item in participant_ids if item != owner.id)
        existing = await _find_direct_conversation(session, user_id=owner.id, other_user_id=other_user_id)
        if existing:
            return existing

    users_result = await session.execute(select(User).where(User.id.in_(participant_ids)))
    users_list = list(users_result.scalars().unique())
    if len(users_list) != len(participant_ids):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono wszystkich użytkowników.")
    if any(user.id != owner.id and not _is_profile_visible(user) for user in users_list):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna rozpoczac nowej rozmowy z użytkownikiem, który ma ukryty profil.",
        )

    conversation = Conversation(type=payload.type, title=payload.title, created_by_id=owner.id)
    session.add(conversation)
    await session.flush()

    for participant_id in participant_ids:
        session.add(ConversationParticipant(conversation_id=conversation.id, user_id=participant_id))

    await log_event(
        session,
        event_type="conversation.create",
        source="message_service",
        message=f"Utworzono konwersację {conversation.id}.",
        user_id=owner.id,
        payload={"participant_ids": participant_ids, "type": payload.type.value},
    )
    await session.commit()
    return await get_conversation_for_user(session, conversation_id=conversation.id, user_id=owner.id)


def _ensure_group_conversation(conversation: Conversation) -> None:
    if conversation.type != ConversationTypeEnum.GROUP:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ta operacja jest dostępna tylko dla czatów grupowych.",
        )


def _ensure_group_manager(*, conversation: Conversation, actor: User) -> None:
    is_creator = conversation.created_by_id == actor.id
    is_admin = getattr(actor.role, "value", actor.role) == "admin"
    if not (is_creator or is_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko właściciel grupy lub administrator może zarządzać jej składem.",
        )


def _ensure_group_owner(*, conversation: Conversation, actor: User) -> None:
    if conversation.created_by_id != actor.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tylko wlasciciel grupy moze usunac ten czat.",
        )


async def update_group_conversation(
    session: AsyncSession,
    *,
    conversation_id: int,
    actor: User,
    title: str,
) -> Conversation:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=actor.id)
    _ensure_group_conversation(conversation)
    _ensure_group_manager(conversation=conversation, actor=actor)

    conversation.title = title.strip()
    session.add(conversation)
    await log_event(
        session,
        event_type="conversation.update",
        source="message_service",
        message=f"Zmieniono nazwę grupy {conversation.id}.",
        user_id=actor.id,
        payload={"conversation_id": conversation.id, "title": conversation.title},
    )
    await session.commit()
    return await get_conversation_for_user(session, conversation_id=conversation.id, user_id=actor.id)


async def update_conversation_category(
    session: AsyncSession,
    *,
    conversation_id: int,
    actor: User,
    category: ConversationDisplayCategoryEnum,
) -> Conversation:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=actor.id)
    participant = next(
        (item for item in conversation.participants if item.user_id == actor.id),
        None,
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono ustawien konwersacji dla tego uzytkownika.",
        )

    participant.display_category = category
    session.add(participant)
    await log_event(
        session,
        event_type="conversation.category.update",
        source="message_service",
        message=f"Zmieniono kategorie konwersacji {conversation.id}.",
        user_id=actor.id,
        payload={"conversation_id": conversation.id, "category": category.value},
    )
    await session.commit()
    return await get_conversation_for_user(session, conversation_id=conversation.id, user_id=actor.id)


async def add_group_participants(
    session: AsyncSession,
    *,
    conversation_id: int,
    actor: User,
    participant_ids: list[int],
) -> tuple[Conversation, list[int]]:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=actor.id)
    _ensure_group_conversation(conversation)
    _ensure_group_manager(conversation=conversation, actor=actor)

    normalized_ids = list(dict.fromkeys(participant_ids))
    existing_ids = {participant.user_id for participant in conversation.participants}
    new_ids = [participant_id for participant_id in normalized_ids if participant_id not in existing_ids]
    if not new_ids:
        return conversation, []

    users_result = await session.execute(select(User).where(User.id.in_(new_ids)))
    users = list(users_result.scalars().unique())
    if len(users) != len(new_ids):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nie znaleziono wszystkich użytkowników do dodania.",
        )
    if any(not _is_profile_visible(user) for user in users):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna dodac do grupy użytkownika, który ma ukryty profil.",
        )

    for participant_id in new_ids:
        session.add(
            ConversationParticipant(
                conversation_id=conversation.id,
                user_id=participant_id,
            )
        )
        await create_notification(
            session,
            user_id=participant_id,
            title="Dodano Cię do grupy",
            body=f"Zostałeś dodany do grupy „{conversation.title or f'Grupa #{conversation.id}'}”.",
            notification_type=NotificationTypeEnum.SYSTEM,
            related_conversation_id=conversation.id,
        )

    await log_event(
        session,
        event_type="conversation.participants.add",
        source="message_service",
        message=f"Dodano uczestników do grupy {conversation.id}.",
        user_id=actor.id,
        payload={"conversation_id": conversation.id, "participant_ids": new_ids},
    )
    await session.commit()
    refreshed = await get_conversation_for_user(session, conversation_id=conversation.id, user_id=actor.id)
    return refreshed, new_ids


async def remove_group_participant(
    session: AsyncSession,
    *,
    conversation_id: int,
    actor: User,
    participant_user_id: int,
) -> tuple[Conversation, list[int]]:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=actor.id)
    _ensure_group_conversation(conversation)
    _ensure_group_manager(conversation=conversation, actor=actor)

    if participant_user_id == conversation.created_by_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie można usunąć właściciela grupy.",
        )

    participant = next(
        (item for item in conversation.participants if item.user_id == participant_user_id),
        None,
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie jest członkiem tej grupy.",
        )

    await session.delete(participant)
    await create_notification(
        session,
        user_id=participant_user_id,
        title="Usunięto Cię z grupy",
        body=f"Nie należysz już do grupy „{conversation.title or f'Grupa #{conversation.id}'}”.",
        notification_type=NotificationTypeEnum.SYSTEM,
    )
    await log_event(
        session,
        event_type="conversation.participants.remove",
        source="message_service",
        message=f"Usunięto uczestnika z grupy {conversation.id}.",
        user_id=actor.id,
        payload={"conversation_id": conversation.id, "participant_user_id": participant_user_id},
    )
    await session.commit()
    refreshed = await get_conversation_for_user(session, conversation_id=conversation.id, user_id=actor.id)
    return refreshed, [participant_user_id]


async def leave_group_conversation(
    session: AsyncSession,
    *,
    conversation_id: int,
    actor: User,
) -> tuple[list[int], list[int], bool]:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=actor.id)
    _ensure_group_conversation(conversation)

    participant = next(
        (item for item in conversation.participants if item.user_id == actor.id),
        None,
    )
    if participant is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Użytkownik nie jest członkiem tej grupy.",
        )

    remaining_participants = [item for item in conversation.participants if item.user_id != actor.id]
    removed_ids = [actor.id]

    if not remaining_participants:
        notifications_result = await session.execute(
            select(Notification).where(Notification.related_conversation_id == conversation.id)
        )
        for notification in notifications_result.scalars().unique():
            await session.delete(notification)

        await log_event(
            session,
            event_type="conversation.leave",
            source="message_service",
            message=f"Użytkownik opuścił i zamknął grupę {conversation.id}.",
            user_id=actor.id,
            payload={"conversation_id": conversation.id, "deleted": True},
        )
        await session.delete(conversation)
        await session.commit()
        return [], removed_ids, True

    if conversation.created_by_id == actor.id:
        conversation.created_by_id = remaining_participants[0].user_id
        session.add(conversation)

    await session.delete(participant)
    await log_event(
        session,
        event_type="conversation.leave",
        source="message_service",
        message=f"Użytkownik opuścił grupę {conversation.id}.",
        user_id=actor.id,
        payload={
            "conversation_id": conversation.id,
            "deleted": False,
            "new_owner_id": conversation.created_by_id,
        },
    )
    await session.commit()
    return [item.user_id for item in remaining_participants], removed_ids, False


async def delete_group_conversation(
    session: AsyncSession,
    *,
    conversation_id: int,
    actor: User,
) -> list[int]:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=actor.id)
    _ensure_group_conversation(conversation)
    _ensure_group_owner(conversation=conversation, actor=actor)

    participant_ids = [participant.user_id for participant in conversation.participants]

    notifications_result = await session.execute(
        select(Notification).where(Notification.related_conversation_id == conversation.id)
    )
    for notification in notifications_result.scalars().unique():
        await session.delete(notification)

    await log_event(
        session,
        event_type="conversation.delete",
        source="message_service",
        message=f"Usunieto grupe {conversation.id}.",
        user_id=actor.id,
        payload={
            "conversation_id": conversation.id,
            "title": conversation.title,
            "participant_ids": participant_ids,
        },
    )
    await session.delete(conversation)
    await session.commit()
    return participant_ids


def analyze_message(content: str) -> tuple[ClassificationResult, SpamDetectionResult]:
    classification = classifier.classify(content)
    spam = spam_detector.detect(content)
    return classification, spam


async def send_message(
    session: AsyncSession,
    *,
    sender: User,
    conversation_id: int,
    payload: MessageCreate,
    online_user_ids: set[int] | None = None,
) -> tuple[Message, list[int]]:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=sender.id)
    participant_ids = [participant.user_id for participant in conversation.participants]
    recipient_ids = [participant_id for participant_id in participant_ids if participant_id != sender.id]

    classification, spam = analyze_message(payload.content)
    category = MessageCategoryEnum.SPAM if spam.is_spam else classification.category
    # Wiadomość pozostaje w stanie "sent", dopóki inny uczestnik faktycznie
    # nie otworzy rozmowy i nie oznaczy jej jako przeczytanej.
    message_status = MessageStatusEnum.SENT

    message = Message(
        conversation_id=conversation.id,
        sender_id=sender.id,
        content=payload.content,
        category=category,
        status=message_status,
        is_spam=spam.is_spam,
        spam_score=spam.score,
        spam_reason="; ".join(spam.reasons) if spam.is_spam else None,
        analysis_metadata={
            "classification_labels": classification.labels,
            "classification_reasons": classification.reasons,
            "classification_confidence": classification.confidence,
            "spam_reasons": spam.reasons,
        },
    )
    conversation.last_message_at = utcnow()
    session.add(message)
    await session.flush()

    notification_title, notification_body = _build_message_notification_content(
        conversation=conversation,
        sender=sender,
        content=payload.content,
    )

    for recipient_id in recipient_ids:
        await create_notification(
            session,
            user_id=recipient_id,
            title=notification_title,
            body=notification_body,
            notification_type=NotificationTypeEnum.MESSAGE,
            related_message_id=message.id,
            related_conversation_id=conversation.id,
        )

    await log_event(
        session,
        event_type="message.send",
        source="message_service",
        message=f"Użytkownik {sender.username} wysłał wiadomość {message.id}.",
        user_id=sender.id,
        payload={"conversation_id": conversation_id, "category": category.value, "spam": spam.is_spam},
    )
    await session.commit()

    result = await session.execute(
        select(Message).where(Message.id == message.id).options(selectinload(Message.sender))
    )
    return result.scalar_one(), recipient_ids


async def list_messages(
    session: AsyncSession,
    *,
    conversation_id: int,
    user_id: int,
    query: str | None = None,
    category: MessageCategoryEnum | None = None,
    sender_id: int | None = None,
    status_filter: MessageStatusEnum | None = None,
) -> list[Message]:
    await get_conversation_for_user(session, conversation_id=conversation_id, user_id=user_id)

    statement = (
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.asc())
    )
    filters = []
    if query:
        filters.append(Message.content.ilike(f"%{query}%"))
    if category:
        filters.append(Message.category == category)
    if sender_id:
        filters.append(Message.sender_id == sender_id)
    if status_filter:
        filters.append(Message.status == status_filter)
    if filters:
        statement = statement.where(and_(*filters))

    result = await session.execute(statement)
    return list(result.scalars().unique())


async def update_message(
    session: AsyncSession,
    *,
    user: User,
    message_id: int,
    payload: MessageUpdate,
) -> Message:
    result = await session.execute(
        select(Message).where(Message.id == message_id).options(selectinload(Message.sender))
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono wiadomości.")
    if message.sender_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Możesz edytować tylko własne wiadomości.")
    if message.is_deleted:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Nie można edytować usuniętej wiadomości.")

    classification, spam = analyze_message(payload.content)
    if message.status == MessageStatusEnum.READ:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nie mozna edytowac wiadomosci, ktora zostala juz odczytana.",
        )

    message.content = payload.content
    message.category = MessageCategoryEnum.SPAM if spam.is_spam else classification.category
    message.is_spam = spam.is_spam
    message.spam_score = spam.score
    message.spam_reason = "; ".join(spam.reasons) if spam.is_spam else None
    message.analysis_metadata = {
        "classification_labels": classification.labels,
        "classification_reasons": classification.reasons,
        "classification_confidence": classification.confidence,
        "spam_reasons": spam.reasons,
    }
    message.is_edited = True
    message.edited_at = utcnow()
    session.add(message)
    await log_event(
        session,
        event_type="message.update",
        source="message_service",
        message=f"Zaktualizowano wiadomość {message.id}.",
        user_id=user.id,
        payload={"message_id": message.id},
    )
    await session.commit()
    await session.refresh(message)
    return message


async def delete_message(session: AsyncSession, *, user: User, message_id: int) -> Message:
    result = await session.execute(
        select(Message).where(Message.id == message_id).options(selectinload(Message.sender))
    )
    message = result.scalar_one_or_none()
    if message is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nie znaleziono wiadomości.")
    if message.sender_id != user.id and user.role.value != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Brak uprawnień do usunięcia wiadomości.")

    message.is_deleted = True
    message.status = MessageStatusEnum.DELETED
    message.content = "[Wiadomość została usunięta]"
    session.add(message)
    await log_event(
        session,
        event_type="message.delete",
        source="message_service",
        message=f"Usunięto wiadomość {message.id}.",
        user_id=user.id,
        payload={"message_id": message.id},
    )
    await session.commit()
    await session.refresh(message)
    return message


async def mark_conversation_as_read(
    session: AsyncSession,
    *,
    conversation_id: int,
    user: User,
) -> list[int]:
    conversation = await get_conversation_for_user(session, conversation_id=conversation_id, user_id=user.id)
    updated_ids: list[int] = []
    read_at = utcnow()

    for participant in conversation.participants:
        if participant.user_id == user.id:
            participant.last_read_at = read_at
            session.add(participant)

    for message in conversation.messages:
        if (
            message.sender_id != user.id
            and message.status not in {MessageStatusEnum.DELETED, MessageStatusEnum.READ}
        ):
            message.status = MessageStatusEnum.READ
            session.add(message)
            updated_ids.append(message.id)

    if updated_ids:
        await log_event(
            session,
            event_type="message.read",
            source="message_service",
            message=f"Użytkownik {user.username} oznaczył wiadomości jako przeczytane.",
            user_id=user.id,
            payload={"conversation_id": conversation_id, "message_ids": updated_ids},
        )

    await session.commit()
    return updated_ids


async def search_messages_globally(
    session: AsyncSession,
    *,
    user: User,
    query: str,
) -> list[Message]:
    conversation_ids_result = await session.execute(
        select(ConversationParticipant.conversation_id).where(ConversationParticipant.user_id == user.id)
    )
    conversation_ids = list(conversation_ids_result.scalars())
    if not conversation_ids:
        return []

    result = await session.execute(
        select(Message)
        .where(
            Message.conversation_id.in_(conversation_ids),
            or_(
                Message.content.ilike(f"%{query}%"),
                Message.spam_reason.ilike(f"%{query}%"),
            ),
        )
        .options(selectinload(Message.sender))
        .order_by(Message.created_at.desc())
    )
    return list(result.scalars().unique())
