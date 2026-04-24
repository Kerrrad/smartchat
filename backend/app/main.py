from pathlib import Path

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import logger, setup_logging
from app.core.security import decode_access_token
from app.db.session import AsyncSessionLocal
from app.models.enums import UserStatusEnum
from app.models.user import User
from app.services import message_service, presence_service
from app.websocket.manager import ws_manager

setup_logging()

BASE_DIR = Path(__file__).resolve().parents[2]
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="Komunikator webowy z automatyzacja, klasyfikacja wiadomosci i panelem administracyjnym.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.api_v1_prefix)
app.mount("/static", StaticFiles(directory=FRONTEND_DIR / "static"), name="static")
templates = Jinja2Templates(directory=str(FRONTEND_DIR / "templates"))


@app.on_event("startup")
async def reset_presence_on_startup() -> None:
    async with AsyncSessionLocal() as session:
        await presence_service.reset_stale_online_users(session)
        await session.commit()


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", {"app_name": settings.app_name})


async def _get_websocket_user(token: str | None) -> User | None:
    if not token:
        return None
    try:
        payload = decode_access_token(token)
        user_id = int(payload["sub"])
    except Exception:
        return None

    async with AsyncSessionLocal() as session:
        user = await session.get(User, user_id)
        if user is None or user.is_blocked or not user.is_active:
            return None
        return user


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    token = websocket.query_params.get("token")
    user = await _get_websocket_user(token)
    if user is None:
        await websocket.close(code=4401)
        return

    async with AsyncSessionLocal() as session:
        session_user = await session.get(User, user.id)
        if session_user is None:
            await websocket.close(code=4401)
            return
        await ws_manager.connect(session_user.id, websocket)
        await presence_service.update_presence(session, user=session_user, status=UserStatusEnum.ONLINE)
        await session.commit()

    await ws_manager.broadcast_all(
        {"type": "presence.changed", "user_id": user.id, "status": UserStatusEnum.ONLINE.value}
    )

    try:
        while True:
            payload = await websocket.receive_json()
            event_type = payload.get("type")

            async with AsyncSessionLocal() as session:
                session_user = await session.get(User, user.id)
                if session_user is None:
                    await websocket.close(code=4401)
                    return

                if event_type == "typing":
                    conversation_id = int(payload["conversation_id"])
                    participant_ids = await message_service.get_conversation_participant_ids(
                        session,
                        conversation_id=conversation_id,
                        exclude_user_id=session_user.id,
                    )
                    await ws_manager.broadcast_to_users(
                        participant_ids,
                        {
                            "type": "conversation.typing",
                            "conversation_id": conversation_id,
                            "user_id": session_user.id,
                            "username": session_user.username,
                            "is_typing": bool(payload.get("is_typing", True)),
                        },
                    )
                elif event_type == "mark_read":
                    conversation_id = int(payload["conversation_id"])
                    message_ids = await message_service.mark_conversation_as_read(
                        session,
                        conversation_id=conversation_id,
                        user=session_user,
                    )
                    participant_ids = await message_service.get_conversation_participant_ids(
                        session,
                        conversation_id=conversation_id,
                        exclude_user_id=None,
                    )
                    await ws_manager.broadcast_to_users(
                        participant_ids,
                        {
                            "type": "message.status",
                            "conversation_id": conversation_id,
                            "status": "read",
                            "message_ids": message_ids,
                            "user_id": session_user.id,
                        },
                    )
                else:
                    await websocket.send_json({"type": "error", "detail": "Nieobslugiwany typ zdarzenia."})
    except WebSocketDisconnect:
        logger.info("Rozlaczono websocket uzytkownika %s", user.username)
    finally:
        is_last_connection = await ws_manager.disconnect(user.id, websocket)
        if is_last_connection:
            async with AsyncSessionLocal() as session:
                session_user = await session.get(User, user.id)
                if session_user is not None:
                    await presence_service.update_presence(session, user=session_user, status=UserStatusEnum.OFFLINE)
                    await session.commit()
            await ws_manager.broadcast_all(
                {"type": "presence.changed", "user_id": user.id, "status": UserStatusEnum.OFFLINE.value}
            )
