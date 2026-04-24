from collections.abc import AsyncGenerator
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from starlette.testclient import TestClient

import app.api.v1.endpoints.conversations as conversations_module
import app.db.session as db_session_module
import app.main as main_module
import app.workers.tasks as tasks_module
from app.core.rate_limit import rate_limiter
from app.core.security import create_access_token, get_password_hash
from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.enums import ConversationTypeEnum, RoleEnum
from app.models.user import User
from app.schemas.conversation import ConversationCreate
from app.services import message_service
from app.websocket.manager import ws_manager

@pytest_asyncio.fixture
async def session_factory(tmp_path) -> AsyncGenerator[async_sessionmaker[AsyncSession], None]:
    test_db_path = tmp_path / "test.db"
    test_database_url = f"sqlite+aiosqlite:///{test_db_path.as_posix()}"
    test_engine = create_async_engine(test_database_url, connect_args={"check_same_thread": False})
    testing_session_local = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield testing_session_local

    await test_engine.dispose()


@pytest_asyncio.fixture(autouse=True)
async def setup_app(
    monkeypatch: pytest.MonkeyPatch,
    session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[None, None]:
    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        async with session_factory() as session:
            yield session

    monkeypatch.setattr(db_session_module, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(main_module, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(conversations_module, "AsyncSessionLocal", session_factory)
    monkeypatch.setattr(tasks_module, "AsyncSessionLocal", session_factory)
    app.dependency_overrides[get_db] = override_get_db
    ws_manager.active_connections.clear()
    ws_manager.connection_counts.clear()
    rate_limiter.storage.clear()

    yield

    app.dependency_overrides.clear()
    ws_manager.active_connections.clear()
    ws_manager.connection_counts.clear()
    rate_limiter.storage.clear()


@pytest_asyncio.fixture
async def session(session_factory: async_sessionmaker[AsyncSession]) -> AsyncGenerator[AsyncSession, None]:
    async with session_factory() as db:
        yield db


@pytest_asyncio.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client


@pytest.fixture
def sync_client() -> TestClient:
    return TestClient(app)


async def _create_user(
    session: AsyncSession,
    *,
    email: str,
    username: str,
    password: str,
    role: RoleEnum = RoleEnum.USER,
) -> User:
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


@pytest_asyncio.fixture
async def seeded_data(session: AsyncSession) -> dict[str, object]:
    admin = await _create_user(
        session,
        email="admin@example.com",
        username="admin",
        password="Admin123!",
        role=RoleEnum.ADMIN,
    )
    alice = await _create_user(
        session,
        email="alice@example.com",
        username="alice",
        password="Password123!",
    )
    bob = await _create_user(
        session,
        email="bob@example.com",
        username="bob",
        password="Password123!",
    )
    conversation = await message_service.create_conversation(
        session,
        owner=alice,
        payload=ConversationCreate(type=ConversationTypeEnum.DIRECT, participant_ids=[bob.id]),
    )

    return {
        "admin": admin,
        "alice": alice,
        "bob": bob,
        "conversation_id": conversation.id,
        "admin_token": create_access_token(admin.id),
        "alice_token": create_access_token(alice.id),
        "bob_token": create_access_token(bob.id),
    }


@pytest.fixture
def auth_headers() -> callable:
    def factory(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return factory
