import pytest

from app.schemas.message import MessageCreate
from app.services import message_service


@pytest.mark.asyncio
async def test_send_message_and_search(async_client, seeded_data, auth_headers):
    conversation_id = seeded_data["conversation_id"]
    headers = auth_headers(seeded_data["alice_token"])

    send_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Pilne pytanie o status zadania?"},
        headers=headers,
    )
    assert send_response.status_code == 201
    message = send_response.json()
    assert message["category"] in {"urgent", "question"}
    assert message["sender"]["username"] == "alice"
    assert message["status"] == "sent"

    history_response = await async_client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=headers,
    )
    assert history_response.status_code == 200
    assert len(history_response.json()) == 1

    search_response = await async_client.get(
        "/api/v1/conversations/messages/search",
        params={"q": "status"},
        headers=headers,
    )
    assert search_response.status_code == 200
    assert len(search_response.json()) == 1


@pytest.mark.asyncio
async def test_online_recipient_still_sees_message_as_sent(session, seeded_data):
    message, _ = await message_service.send_message(
        session,
        sender=seeded_data["alice"],
        conversation_id=seeded_data["conversation_id"],
        payload=MessageCreate(content="Wiadomosc do przeczytania pozniej"),
        online_user_ids={seeded_data["bob"].id},
    )
    assert message.status.value == "sent"


@pytest.mark.asyncio
async def test_message_status_changes_from_sent_to_read(async_client, seeded_data, auth_headers):
    conversation_id = seeded_data["conversation_id"]
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    send_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Status testowy"},
        headers=alice_headers,
    )
    assert send_response.status_code == 201
    sent_message = send_response.json()
    assert sent_message["status"] == "sent"

    read_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/read",
        headers=bob_headers,
    )
    assert read_response.status_code == 200
    assert sent_message["id"] in read_response.json()["message_ids"]

    history_response = await async_client.get(
        f"/api/v1/conversations/{conversation_id}/messages",
        headers=alice_headers,
    )
    assert history_response.status_code == 200
    updated_message = next(message for message in history_response.json() if message["id"] == sent_message["id"])
    assert updated_message["status"] == "read"


@pytest.mark.asyncio
async def test_message_can_be_edited_only_before_read(async_client, seeded_data, auth_headers):
    conversation_id = seeded_data["conversation_id"]
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    send_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Pierwotna tresc"},
        headers=alice_headers,
    )
    assert send_response.status_code == 201
    message_id = send_response.json()["id"]

    edit_before_read = await async_client.patch(
        f"/api/v1/conversations/messages/{message_id}",
        json={"content": "Tresc przed odczytem"},
        headers=alice_headers,
    )
    assert edit_before_read.status_code == 200
    assert edit_before_read.json()["content"] == "Tresc przed odczytem"

    read_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/read",
        headers=bob_headers,
    )
    assert read_response.status_code == 200
    assert message_id in read_response.json()["message_ids"]

    edit_after_read = await async_client.patch(
        f"/api/v1/conversations/messages/{message_id}",
        json={"content": "Tresc po odczycie"},
        headers=alice_headers,
    )
    assert edit_after_read.status_code == 400
    assert "odczytana" in edit_after_read.json()["detail"]


@pytest.mark.asyncio
async def test_group_message_notification_contains_group_name(async_client, seeded_data, auth_headers):
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    create_response = await async_client.post(
        "/api/v1/conversations",
        json={
            "type": "group",
            "title": "Zespol wdrozeniowy",
            "participant_ids": [seeded_data["bob"].id],
        },
        headers=alice_headers,
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    send_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Aktualizacja statusu wdrozenia"},
        headers=alice_headers,
    )
    assert send_response.status_code == 201

    notifications_response = await async_client.get(
        "/api/v1/notifications",
        headers=bob_headers,
    )
    assert notifications_response.status_code == 200
    message_notification = next(
        item for item in notifications_response.json() if item["related_message_id"] == send_response.json()["id"]
    )
    assert "grupie" in message_notification["title"].lower()
    assert "Zespol wdrozeniowy" in message_notification["body"]
    assert message_notification["conversation_id"] == conversation_id
    assert message_notification["message_category"] == "private"


@pytest.mark.asyncio
async def test_direct_message_notification_contains_classification_category(
    async_client,
    seeded_data,
    auth_headers,
):
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    send_response = await async_client.post(
        f"/api/v1/conversations/{seeded_data['conversation_id']}/messages",
        json={"content": "Pilne pytanie o termin wdrozenia?"},
        headers=alice_headers,
    )
    assert send_response.status_code == 201
    assert send_response.json()["category"] == "urgent"

    notifications_response = await async_client.get(
        "/api/v1/notifications",
        headers=bob_headers,
    )
    assert notifications_response.status_code == 200
    message_notification = next(
        item for item in notifications_response.json() if item["related_message_id"] == send_response.json()["id"]
    )
    assert message_notification["type"] == "message"
    assert message_notification["message_category"] == "urgent"


@pytest.mark.asyncio
async def test_notifications_keep_only_latest_unread_item_per_conversation(
    async_client,
    seeded_data,
    auth_headers,
):
    alice_headers = auth_headers(seeded_data["alice_token"])
    admin_headers = auth_headers(seeded_data["admin_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    first_message_response = await async_client.post(
        f"/api/v1/conversations/{seeded_data['conversation_id']}/messages",
        json={"content": "Pierwsze powiadomienie"},
        headers=alice_headers,
    )
    assert first_message_response.status_code == 201

    second_message_response = await async_client.post(
        f"/api/v1/conversations/{seeded_data['conversation_id']}/messages",
        json={"content": "Nowsze powiadomienie"},
        headers=alice_headers,
    )
    assert second_message_response.status_code == 201

    second_conversation_response = await async_client.post(
        "/api/v1/conversations",
        json={
            "type": "direct",
            "participant_ids": [seeded_data["bob"].id],
        },
        headers=admin_headers,
    )
    assert second_conversation_response.status_code == 201
    second_conversation_id = second_conversation_response.json()["id"]

    third_message_response = await async_client.post(
        f"/api/v1/conversations/{second_conversation_id}/messages",
        json={"content": "Powiadomienie z innego czatu"},
        headers=admin_headers,
    )
    assert third_message_response.status_code == 201

    notifications_response = await async_client.get(
        "/api/v1/notifications",
        headers=bob_headers,
    )
    assert notifications_response.status_code == 200
    notifications = notifications_response.json()

    first_conversation_notifications = [
        item for item in notifications if item["conversation_id"] == seeded_data["conversation_id"]
    ]
    assert len(first_conversation_notifications) == 1
    assert first_conversation_notifications[0]["related_message_id"] == second_message_response.json()["id"]

    second_conversation_notifications = [
        item for item in notifications if item["conversation_id"] == second_conversation_id
    ]
    assert len(second_conversation_notifications) == 1
    assert second_conversation_notifications[0]["related_message_id"] == third_message_response.json()["id"]


@pytest.mark.asyncio
async def test_group_conversation_management(async_client, seeded_data, auth_headers):
    headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    create_response = await async_client.post(
        "/api/v1/conversations",
        json={
            "type": "group",
            "title": "Projekt badawczy",
            "participant_ids": [],
        },
        headers=headers,
    )
    assert create_response.status_code == 201
    conversation = create_response.json()
    assert conversation["type"] == "group"
    assert conversation["title"] == "Projekt badawczy"
    initial_ids = {participant["user_id"] for participant in conversation["participants"]}
    assert initial_ids == {seeded_data["alice"].id}

    conversation_id = conversation["id"]

    rename_response = await async_client.patch(
        f"/api/v1/conversations/{conversation_id}",
        json={"title": "Projekt dyplomowy"},
        headers=headers,
    )
    assert rename_response.status_code == 200
    assert rename_response.json()["title"] == "Projekt dyplomowy"

    add_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/participants",
        json={"participant_ids": [seeded_data["admin"].id, seeded_data["bob"].id]},
        headers=headers,
    )
    assert add_response.status_code == 200
    added_ids = {participant["user_id"] for participant in add_response.json()["participants"]}
    assert seeded_data["admin"].id in added_ids
    assert seeded_data["bob"].id in added_ids

    notifications_response = await async_client.get("/api/v1/notifications", headers=bob_headers)
    assert notifications_response.status_code == 200
    group_add_notification = next(
        item for item in notifications_response.json() if item["title"] == "Dodano Cię do grupy"
    )
    assert group_add_notification["conversation_id"] == conversation_id

    remove_response = await async_client.delete(
        f"/api/v1/conversations/{conversation_id}/participants/{seeded_data['bob'].id}",
        headers=headers,
    )
    assert remove_response.status_code == 200
    remaining_ids = {participant["user_id"] for participant in remove_response.json()["participants"]}
    assert seeded_data["bob"].id not in remaining_ids
    assert seeded_data["alice"].id in remaining_ids


@pytest.mark.asyncio
async def test_group_can_be_deleted_only_by_owner(async_client, seeded_data, auth_headers):
    alice_headers = auth_headers(seeded_data["alice_token"])
    admin_headers = auth_headers(seeded_data["admin_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    create_response = await async_client.post(
        "/api/v1/conversations",
        json={
            "type": "group",
            "title": "Grupa do usuniecia",
            "participant_ids": [seeded_data["admin"].id, seeded_data["bob"].id],
        },
        headers=alice_headers,
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    forbidden_delete = await async_client.delete(
        f"/api/v1/conversations/{conversation_id}",
        headers=admin_headers,
    )
    assert forbidden_delete.status_code == 403
    assert "wlasciciel" in forbidden_delete.json()["detail"].lower()

    delete_response = await async_client.delete(
        f"/api/v1/conversations/{conversation_id}",
        headers=alice_headers,
    )
    assert delete_response.status_code == 204

    owner_conversations = await async_client.get("/api/v1/conversations", headers=alice_headers)
    assert owner_conversations.status_code == 200
    assert all(item["id"] != conversation_id for item in owner_conversations.json())

    participant_conversations = await async_client.get("/api/v1/conversations", headers=bob_headers)
    assert participant_conversations.status_code == 200
    assert all(item["id"] != conversation_id for item in participant_conversations.json())


@pytest.mark.asyncio
async def test_hidden_profile_blocks_new_conversations_but_not_existing_ones(
    async_client,
    seeded_data,
    auth_headers,
):
    bob_headers = auth_headers(seeded_data["bob_token"])
    alice_headers = auth_headers(seeded_data["alice_token"])
    admin_headers = auth_headers(seeded_data["admin_token"])

    hide_response = await async_client.patch(
        "/api/v1/users/me",
        json={
            "privacy_settings": {
                "profile_visible": False,
                "allow_group_invites": True,
                "show_online_status": True,
            }
        },
        headers=bob_headers,
    )
    assert hide_response.status_code == 200
    assert hide_response.json()["privacy_settings"]["profile_visible"] is False

    directory_response = await async_client.get("/api/v1/users/directory", headers=alice_headers)
    assert directory_response.status_code == 200
    assert all(user["id"] != seeded_data["bob"].id for user in directory_response.json()["items"])

    search_response = await async_client.get(
        "/api/v1/users/search",
        params={"q": "bob"},
        headers=alice_headers,
    )
    assert search_response.status_code == 200
    assert all(user["id"] != seeded_data["bob"].id for user in search_response.json()["items"])

    direct_create_response = await async_client.post(
        "/api/v1/conversations",
        json={"type": "direct", "participant_ids": [seeded_data["bob"].id]},
        headers=admin_headers,
    )
    assert direct_create_response.status_code == 400
    assert "ukryty profil" in direct_create_response.json()["detail"].lower()

    group_create_response = await async_client.post(
        "/api/v1/conversations",
        json={"type": "group", "title": "Widoczna grupa", "participant_ids": [seeded_data["admin"].id]},
        headers=alice_headers,
    )
    assert group_create_response.status_code == 201
    group_id = group_create_response.json()["id"]

    add_hidden_response = await async_client.post(
        f"/api/v1/conversations/{group_id}/participants",
        json={"participant_ids": [seeded_data["bob"].id]},
        headers=alice_headers,
    )
    assert add_hidden_response.status_code == 400
    assert "ukryty profil" in add_hidden_response.json()["detail"].lower()

    existing_conversation_response = await async_client.post(
        f"/api/v1/conversations/{seeded_data['conversation_id']}/messages",
        json={"content": "Ta rozmowa nadal dziala"},
        headers=alice_headers,
    )
    assert existing_conversation_response.status_code == 201
    assert existing_conversation_response.json()["content"] == "Ta rozmowa nadal dziala"

    show_response = await async_client.patch(
        "/api/v1/users/me",
        json={
            "privacy_settings": {
                "profile_visible": True,
                "allow_group_invites": True,
                "show_online_status": True,
            }
        },
        headers=bob_headers,
    )
    assert show_response.status_code == 200
    assert show_response.json()["privacy_settings"]["profile_visible"] is True

    directory_after_show = await async_client.get("/api/v1/users/directory", headers=alice_headers)
    assert directory_after_show.status_code == 200
    assert any(user["id"] == seeded_data["bob"].id for user in directory_after_show.json()["items"])


@pytest.mark.asyncio
async def test_group_member_can_leave_group(async_client, seeded_data, auth_headers):
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    create_response = await async_client.post(
        "/api/v1/conversations",
        json={
            "type": "group",
            "title": "Grupa do opuszczenia",
            "participant_ids": [seeded_data["bob"].id],
        },
        headers=alice_headers,
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    leave_response = await async_client.delete(
        f"/api/v1/conversations/{conversation_id}/leave",
        headers=bob_headers,
    )
    assert leave_response.status_code == 204

    bob_conversations = await async_client.get("/api/v1/conversations", headers=bob_headers)
    assert bob_conversations.status_code == 200
    assert all(item["id"] != conversation_id for item in bob_conversations.json())

    alice_conversations = await async_client.get("/api/v1/conversations", headers=alice_headers)
    assert alice_conversations.status_code == 200
    remaining_group = next(item for item in alice_conversations.json() if item["id"] == conversation_id)
    remaining_ids = {participant["user_id"] for participant in remaining_group["participants"]}
    assert remaining_ids == {seeded_data["alice"].id}

    denied_response = await async_client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=bob_headers,
    )
    assert denied_response.status_code == 403


@pytest.mark.asyncio
async def test_user_can_move_conversation_between_personal_categories(
    async_client,
    seeded_data,
    auth_headers,
):
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])
    conversation_id = seeded_data["conversation_id"]

    initial_list = await async_client.get("/api/v1/conversations", headers=alice_headers)
    assert initial_list.status_code == 200
    initial_conversation = next(item for item in initial_list.json() if item["id"] == conversation_id)
    alice_initial_participant = next(
        participant
        for participant in initial_conversation["participants"]
        if participant["user_id"] == seeded_data["alice"].id
    )
    assert alice_initial_participant["display_category"] == "other"

    update_response = await async_client.patch(
        f"/api/v1/conversations/{conversation_id}/category",
        json={"category": "work"},
        headers=alice_headers,
    )
    assert update_response.status_code == 200
    alice_participant = next(
        participant
        for participant in update_response.json()["participants"]
        if participant["user_id"] == seeded_data["alice"].id
    )
    assert alice_participant["display_category"] == "work"

    alice_list = await async_client.get("/api/v1/conversations", headers=alice_headers)
    assert alice_list.status_code == 200
    alice_conversation = next(item for item in alice_list.json() if item["id"] == conversation_id)
    alice_updated_participant = next(
        participant
        for participant in alice_conversation["participants"]
        if participant["user_id"] == seeded_data["alice"].id
    )
    assert alice_updated_participant["display_category"] == "work"

    bob_list = await async_client.get("/api/v1/conversations", headers=bob_headers)
    assert bob_list.status_code == 200
    bob_conversation = next(item for item in bob_list.json() if item["id"] == conversation_id)
    bob_participant = next(
        participant
        for participant in bob_conversation["participants"]
        if participant["user_id"] == seeded_data["bob"].id
    )
    assert bob_participant["display_category"] == "other"


@pytest.mark.asyncio
async def test_group_owner_can_leave_and_transfer_ownership(async_client, seeded_data, auth_headers):
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    create_response = await async_client.post(
        "/api/v1/conversations",
        json={
            "type": "group",
            "title": "Grupa z przekazaniem",
            "participant_ids": [seeded_data["bob"].id, seeded_data["admin"].id],
        },
        headers=alice_headers,
    )
    assert create_response.status_code == 201
    conversation_id = create_response.json()["id"]

    leave_response = await async_client.delete(
        f"/api/v1/conversations/{conversation_id}/leave",
        headers=alice_headers,
    )
    assert leave_response.status_code == 204

    alice_conversations = await async_client.get("/api/v1/conversations", headers=alice_headers)
    assert alice_conversations.status_code == 200
    assert all(item["id"] != conversation_id for item in alice_conversations.json())

    bob_conversations = await async_client.get("/api/v1/conversations", headers=bob_headers)
    assert bob_conversations.status_code == 200
    bob_group = next(item for item in bob_conversations.json() if item["id"] == conversation_id)
    assert bob_group["created_by_id"] == seeded_data["bob"].id
    remaining_ids = {participant["user_id"] for participant in bob_group["participants"]}
    assert seeded_data["alice"].id not in remaining_ids
    assert seeded_data["bob"].id in remaining_ids
