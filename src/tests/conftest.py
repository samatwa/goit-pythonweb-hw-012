from unittest.mock import patch, AsyncMock, MagicMock
import asyncio
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from main import app
from src.database.models import Base, User
from src.database.db import get_db
from src.services.auth import create_access_token, Hash

# Використання бази даних SQLite для тестування
SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./test.db"

engine = create_async_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)

test_user_data = {
    "username": "deadpool",
    "email": "deadpool@example.com",
    "password": "12345678",
}


# Фікстура для ініціалізації бази даних перед тестами
@pytest.fixture(scope="session", autouse=True)
def init_db():
    async def init_models():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        async with TestingSessionLocal() as session:
            hash_password = Hash().get_password_hash(test_user_data["password"])
            user = User(
                username=test_user_data["username"],
                email=test_user_data["email"],
                hashed_password=hash_password,
                confirmed=True,
                avatar_url="https://example.com/avatar.jpg",
            )
            session.add(user)
            await session.commit()

    asyncio.run(init_models())


# Фікстура для отримання токена доступу
@pytest.fixture
def get_token():
    return create_access_token(data={"sub": test_user_data["email"]})


# Фікстура для клієнта тестування
@pytest.fixture
def client():
    async def override_get_db():
        async with TestingSessionLocal() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# Фікстура для мокання Redis
@pytest.fixture(autouse=True)
def mock_redis():
    with patch("src.repository.users.Redis") as mock_redis_class:
        mock_redis_instance = MagicMock()
        mock_redis_instance.get = AsyncMock(return_value=None)
        mock_redis_instance.set = AsyncMock(return_value=True)
        mock_redis_instance.delete = AsyncMock(return_value=True)
        mock_redis_class.return_value = mock_redis_instance

        yield mock_redis_instance
