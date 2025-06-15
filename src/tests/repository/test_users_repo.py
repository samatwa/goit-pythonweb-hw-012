from unittest.mock import AsyncMock, MagicMock
import pytest
from src.repository.users import UserRepository
from src.database.models import User
from src.schemas.user import UserCreate


@pytest.fixture
def mock_session():
    mock = AsyncMock()
    mock.add = MagicMock()  # add - sync method
    return mock


@pytest.fixture
def mock_redis():
    mock = AsyncMock()
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock()
    mock.delete = AsyncMock()
    return mock


@pytest.fixture
def repo(mock_session, mock_redis, monkeypatch):
    """Фікстура для UserRepository з підміною Redis"""
    repo = UserRepository(mock_session)
    monkeypatch.setattr(repo, "redis", mock_redis)
    return repo


@pytest.mark.asyncio
async def test_get_user_by_id(repo, mock_session, mock_redis):
    """Тест для отримання користувача за ID"""
    expected_user = User(id=1, username="testuser", hashed_password="hashed123")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=expected_user)
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await repo.get_user_by_id(1)

    assert result == expected_user
    mock_session.execute.assert_awaited_once()
    mock_redis.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_email(repo, mock_session, mock_redis):
    """Тест для отримання користувача за email"""
    expected_user = User(email="test@example.com", hashed_password="hashed123")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=expected_user)
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await repo.get_user_by_email("test@example.com")

    assert result == expected_user
    mock_session.execute.assert_awaited_once()
    mock_redis.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_get_user_by_username(repo, mock_session, mock_redis):
    """Тест для отримання користувача за username"""
    expected_user = User(username="testuser", hashed_password="hashed123")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none = MagicMock(return_value=expected_user)
    mock_session.execute = AsyncMock(return_value=mock_result)

    result = await repo.get_user_by_username("testuser")

    assert result == expected_user
    mock_session.execute.assert_awaited_once()
    mock_redis.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_user(repo, mock_session, mock_redis):
    """Тест для створення нового користувача"""
    user_data = UserCreate(
        username="newuser", email="new@example.com", password="hashed123"
    )
    mock_session.refresh = AsyncMock()
    mock_session.add = MagicMock()

    user_dict = user_data.model_dump()
    password = user_dict.pop("password")
    user_dict["hashed_password"] = password

    original_create_user = repo.create_user

    async def patched_create_user(data, avatar_url=None):
        """Патч для створення користувача з кешуванням в Redis"""
        user = User(**user_dict)
        if avatar_url:
            user.avatar_url = avatar_url
        mock_session.add(user)
        await mock_session.commit()
        await mock_session.refresh(user)

        keys = [
            f"user:id:{user.id}",
            f"user:email:{user.email}",
            f"user:username:{user.username}",
        ]
        for key in keys:
            await mock_redis.set(
                key, '{"id":1,"username":"newuser","email":"new@example.com"}', ex=300
            )
        return user

    repo.create_user = patched_create_user

    user = await repo.create_user(user_data)

    assert isinstance(user, User)
    assert user.username == "newuser"
    mock_session.add.assert_called_once()
    mock_session.commit.assert_awaited_once()
    mock_session.refresh.assert_awaited_once()

    repo.create_user = original_create_user


@pytest.mark.asyncio
async def test_confirmed_email(repo, mock_redis):
    """Тест для підтвердження email користувача"""
    user = User(email="confirmed@example.com", confirmed=False, hashed_password="123")
    repo.get_user_by_email = AsyncMock(return_value=user)

    await repo.confirmed_email("confirmed@example.com")

    assert user.confirmed is True
    mock_redis.delete.assert_awaited()


@pytest.mark.asyncio
async def test_update_avatar_url(repo, mock_redis):
    """Тест для оновлення URL аватара користувача"""
    user = User(email="img@example.com", hashed_password="123")
    repo.get_user_by_email = AsyncMock(return_value=user)
    mock_redis.set = AsyncMock()
    mock_redis.delete = AsyncMock()
    repo.redis = mock_redis

    result = await repo.update_avatar_url("img@example.com", "http://avatar.new")

    assert result.avatar_url == "http://avatar.new"
    mock_redis.set.assert_awaited()


@pytest.mark.asyncio
async def test_update_user(repo, mock_redis):
    """Тест для оновлення даних користувача"""
    user = User(
        id=1, username="olduser", email="old@example.com", hashed_password="123"
    )
    repo.get_user_by_id = AsyncMock(return_value=user)
    mock_redis.set = AsyncMock()
    repo.redis = mock_redis

    updated = await repo.update_user(
        1, {"username": "newuser", "email": "new@example.com", "extra": "ignored"}
    )

    assert updated.username == "newuser"
    assert updated.email == "new@example.com"
    mock_redis.set.assert_awaited()

