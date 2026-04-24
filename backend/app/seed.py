import asyncio

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.enums import AutoResponderTriggerEnum, ConversationTypeEnum, RoleEnum
from app.models.user import User
from app.schemas.automation import AutoResponderRuleCreate
from app.schemas.conversation import ConversationCreate
from app.schemas.message import MessageCreate
from app.services import autoresponder_service, message_service


async def _ensure_user(session: AsyncSession, *, email: str, username: str, password: str, role: RoleEnum) -> User:
    result = await session.execute(select(User).where(or_(User.email == email, User.username == username)))
    user = result.scalar_one_or_none()
    if user:
        return user

    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        role=role,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def seed() -> None:
    async with AsyncSessionLocal() as session:
        admin = await _ensure_user(
            session,
            email=settings.default_admin_email,
            username="admin",
            password=settings.default_admin_password,
            role=RoleEnum.ADMIN,
        )
        alice = await _ensure_user(
            session,
            email="alice@smartchat.local",
            username="alice",
            password="Password123!",
            role=RoleEnum.USER,
        )
        bob = await _ensure_user(
            session,
            email="bob@smartchat.local",
            username="bob",
            password="Password123!",
            role=RoleEnum.USER,
        )
        carol = await _ensure_user(
            session,
            email="carol@smartchat.local",
            username="carol",
            password="Password123!",
            role=RoleEnum.USER,
        )

        direct = await message_service.create_conversation(
            session,
            owner=alice,
            payload=ConversationCreate(type=ConversationTypeEnum.DIRECT, participant_ids=[bob.id]),
        )
        if not direct.messages:
            await message_service.send_message(
                session,
                sender=alice,
                conversation_id=direct.id,
                payload=MessageCreate(content="Cześć Bob, czy możemy jutro omówić wdrożenie?"),
                online_user_ids=set(),
            )

        group = await message_service.create_conversation(
            session,
            owner=admin,
            payload=ConversationCreate(
                type=ConversationTypeEnum.GROUP,
                title="Zespół projektu",
                participant_ids=[alice.id, bob.id, carol.id],
            ),
        )
        if len(group.messages) < 2:
            await message_service.send_message(
                session,
                sender=admin,
                conversation_id=group.id,
                payload=MessageCreate(content="Ogłoszenie: demo aplikacji odbędzie się w piątek o 10:00."),
                online_user_ids=set(),
            )
            await message_service.send_message(
                session,
                sender=carol,
                conversation_id=group.id,
                payload=MessageCreate(content="FREE MONEY!!! Kliknij https://spam.local teraz!!!"),
                online_user_ids=set(),
            )

        existing_rules = await autoresponder_service.list_rules(session, bob.id)
        if not existing_rules:
            await autoresponder_service.create_rule(
                session,
                user=bob,
                payload=AutoResponderRuleCreate(
                    name="Pytania po godzinach",
                    trigger_type=AutoResponderTriggerEnum.QUESTION,
                    response_text="Dziękuję za wiadomość. Odpowiem na pytanie w najbliższym oknie pracy.",
                    enabled=True,
                ),
            )


def main() -> None:
    asyncio.run(seed())


if __name__ == "__main__":
    main()

