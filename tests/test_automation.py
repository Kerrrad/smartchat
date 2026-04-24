import asyncio

import pytest

from app.models.enums import ConversationTypeEnum
from app.schemas.automation import AutoResponderRuleCreate
from app.schemas.conversation import ConversationCreate
from app.services import autoresponder_service
from app.services.classification_service import classifier
from app.services import message_service
from app.services.spam_service import spam_detector


@pytest.mark.asyncio
async def test_classifier_and_spam_detector():
    classification = classifier.classify("Pilne pytanie o wdrożenie?")
    assert classification.category in {"urgent", "question"}

    spam = spam_detector.detect("FREE MONEY!!! Kliknij https://spam.local teraz!!!")
    assert spam.is_spam is True
    assert spam.score >= 0.6


@pytest.mark.asyncio
async def test_autoresponder_generates_reply(async_client, session, seeded_data, auth_headers):
    bob = seeded_data["bob"]
    conversation_id = seeded_data["conversation_id"]
    alice_headers = auth_headers(seeded_data["alice_token"])
    bob_headers = auth_headers(seeded_data["bob_token"])

    await autoresponder_service.create_rule(
        session,
        user=bob,
        payload=AutoResponderRuleCreate(
            name="Odpowiedź na pytania",
            trigger_type="question",
            response_text="Dziękuję za pytanie. Wrócę z odpowiedzią wkrótce.",
        ),
    )

    send_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Czy możesz potwierdzić termin spotkania?"},
        headers=alice_headers,
    )
    assert send_response.status_code == 201

    await asyncio.sleep(0.1)

    history_response = await async_client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=alice_headers,
    )
    assert history_response.status_code == 200
    messages = history_response.json()["messages"]
    auto_message = next(message for message in messages if message["is_automated"])

    alice_notifications_response = await async_client.get(
        "/api/v1/notifications",
        headers=alice_headers,
    )
    assert alice_notifications_response.status_code == 200
    assert all(item["type"] != "automation" for item in alice_notifications_response.json())

    bob_notifications_response = await async_client.get(
        "/api/v1/notifications",
        headers=bob_headers,
    )
    assert bob_notifications_response.status_code == 200
    automation_notification = next(
        item for item in bob_notifications_response.json() if item["type"] == "automation"
    )
    assert automation_notification["related_message_id"] == auto_message["id"]
    assert str(send_response.json()["id"]) not in automation_notification["body"]


@pytest.mark.asyncio
async def test_off_hours_rule_without_time_limits_acts_as_always_on(
    async_client, session, seeded_data, auth_headers
):
    bob = seeded_data["bob"]
    conversation_id = seeded_data["conversation_id"]

    await autoresponder_service.create_rule(
        session,
        user=bob,
        payload=AutoResponderRuleCreate(
            name="Stala regula poza godzinami",
            trigger_type="off_hours",
            response_text="Automatyczna odpowiedz aktywna stale.",
            active_from=None,
            active_to=None,
        ),
    )

    send_response = await async_client.post(
        f"/api/v1/conversations/{conversation_id}/messages",
        json={"content": "Czy jestes dostepny teraz?"},
        headers=auth_headers(seeded_data["alice_token"]),
    )
    assert send_response.status_code == 201

    await asyncio.sleep(0.1)

    history_response = await async_client.get(
        f"/api/v1/conversations/{conversation_id}",
        headers=auth_headers(seeded_data["alice_token"]),
    )
    assert history_response.status_code == 200
    messages = history_response.json()["messages"]
    assert any(
        message["is_automated"] and message["content"] == "Automatyczna odpowiedz aktywna stale."
        for message in messages
    )


@pytest.mark.asyncio
async def test_autoresponder_does_not_run_in_group_conversations(
    async_client, session, seeded_data, auth_headers
):
    alice = seeded_data["alice"]
    bob = seeded_data["bob"]

    group_conversation = await message_service.create_conversation(
        session,
        owner=alice,
        payload=ConversationCreate(
            type=ConversationTypeEnum.GROUP,
            title="Grupa bez autorespondera",
            participant_ids=[bob.id],
        ),
    )

    await autoresponder_service.create_rule(
        session,
        user=bob,
        payload=AutoResponderRuleCreate(
            name="Odpowiedz na pytania prywatne",
            trigger_type="question",
            response_text="To nie powinno pojawic sie w grupie.",
        ),
    )

    send_response = await async_client.post(
        f"/api/v1/conversations/{group_conversation.id}/messages",
        json={"content": "Czy slychac mnie na grupie?"},
        headers=auth_headers(seeded_data["alice_token"]),
    )
    assert send_response.status_code == 201

    await asyncio.sleep(0.1)

    history_response = await async_client.get(
        f"/api/v1/conversations/{group_conversation.id}",
        headers=auth_headers(seeded_data["alice_token"]),
    )
    assert history_response.status_code == 200
    messages = history_response.json()["messages"]
    assert not any(message["is_automated"] for message in messages)
