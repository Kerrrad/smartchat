import asyncio

import pytest
from sqlalchemy import select

from app.models.enums import UserStatusEnum
from app.models.user import User
from app.schemas.message import MessageCreate
from app.services import message_service, presence_service
from app.websocket.manager import ws_manager


@pytest.mark.asyncio
async def test_websocket_mark_read_event(sync_client, session, seeded_data):
    await message_service.send_message(
        session,
        sender=seeded_data["bob"],
        conversation_id=seeded_data["conversation_id"],
        payload=MessageCreate(content="Czy widzisz tę wiadomość?"),
        online_user_ids=set(),
    )

    with sync_client.websocket_connect(f"/ws?token={seeded_data['alice_token']}") as socket:
        socket.send_json(
            {
                "type": "mark_read",
                "conversation_id": seeded_data["conversation_id"],
            }
        )

        received = []
        for _ in range(3):
            payload = socket.receive_json()
            received.append(payload)
            if payload["type"] == "message.status":
                break

        status_event = next(item for item in received if item["type"] == "message.status")
        assert status_event["status"] == "read"
        assert status_event["conversation_id"] == seeded_data["conversation_id"]
        assert len(status_event["message_ids"]) == 1


@pytest.mark.asyncio
async def test_reset_stale_online_users_marks_only_online_as_offline(session, seeded_data):
    alice = await session.get(User, seeded_data["alice"].id)
    bob = await session.get(User, seeded_data["bob"].id)
    alice.status = UserStatusEnum.ONLINE
    bob.status = UserStatusEnum.AWAY
    session.add_all([alice, bob])
    await session.commit()

    await presence_service.reset_stale_online_users(session)
    await session.commit()

    refreshed = await session.execute(select(User).order_by(User.id))
    users = {user.id: user for user in refreshed.scalars().unique()}
    assert users[seeded_data["alice"].id].status == UserStatusEnum.OFFLINE
    assert users[seeded_data["bob"].id].status == UserStatusEnum.AWAY


@pytest.mark.asyncio
async def test_user_stays_online_while_second_websocket_connection_is_active(
    sync_client,
    session_factory,
    seeded_data,
):
    alice_id = seeded_data["alice"].id

    async def fetch_status() -> UserStatusEnum:
        async with session_factory() as verification_session:
            result = await verification_session.execute(
                select(User).execution_options(populate_existing=True).where(User.id == alice_id)
            )
            return result.scalar_one().status

    with sync_client.websocket_connect(f"/ws?token={seeded_data['alice_token']}") as socket_one:
        socket_one.receive_json()

        with sync_client.websocket_connect(f"/ws?token={seeded_data['alice_token']}") as socket_two:
            socket_two.receive_json()
            assert await fetch_status() == UserStatusEnum.ONLINE

        assert await fetch_status() == UserStatusEnum.ONLINE

    if alice_id in ws_manager.online_user_ids():
        for _ in range(20):
            await asyncio.sleep(0.05)
            if alice_id not in ws_manager.online_user_ids():
                break

    assert alice_id not in ws_manager.online_user_ids()
