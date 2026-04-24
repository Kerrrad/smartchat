import asyncio

from app.db.session import AsyncSessionLocal
from app.services.autoresponder_service import process_message_automation
from app.workers.celery_app import celery_app


@celery_app.task(name="smartchat.process_message_automation")
def process_message_automation_task(message_id: int) -> int:
    async def runner() -> int:
        async with AsyncSessionLocal() as session:
            generated = await process_message_automation(session, message_id=message_id)
            return len(generated)

    return asyncio.run(runner())

