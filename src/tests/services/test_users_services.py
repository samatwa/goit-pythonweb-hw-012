import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from src.services.users import UserService
from src.schemas.user import UserCreate
from src.database.models import User


@pytest.fixture
def mock_repo():
    """
    Фікстура для створення мок репозиторію користувачів.
    """
    return AsyncMock()


@pytest.fixture
def service(mock_repo):
    """
    Фікстура для створення сервісу користувачів з мок репозиторієм.
    """
    with patch("src.services.users.UserRepository", return_value=mock_repo):
        yield UserService(db=AsyncMock())


@pytest.mark.asyncio
@patch("src.services.users.Gravatar")
async def test_create_user_with_gravatar(mock_gravatar, service, mock_repo):
    """
    Тестує створення користувача з Gravatar.
    """
    mock_gravatar_instance = MagicMock()
    mock_gravatar_instance.get_image.return_value = "http://gravatar.com/avatar.png"
    mock_gravatar.return_value = mock_gravatar_instance

    user_data = UserCreate(
        username="testuser", email="test@example.com", password="hashedpass"
    )

    await service.create_user(user_data)

    mock_gravatar.assert_called_once_with("test@example.com")
    mock_gravatar_instance.get_image.assert_called_once()
    mock_repo.create_user.assert_awaited_once_with(
        user_data, "http://gravatar.com/avatar.png"
    )


@pytest.mark.asyncio
@patch("src.services.users.Gravatar", side_effect=Exception("fail"))
async def test_create_user_without_gravatar(mock_gravatar, service, mock_repo):
    """
    Тестує створення користувача без Gravatar.
    """
    user_data = UserCreate(
        username="noavatar", email="fail@example.com", password="secure123"
    )

    await service.create_user(user_data)

    mock_gravatar.assert_called_once_with("fail@example.com")
    mock_repo.create_user.assert_awaited_once_with(user_data, None)


@pytest.mark.asyncio
async def test_get_user_by_id(service, mock_repo):
    """
    Тестує отримання користувача за ID.
    """
    mock_repo.get_user_by_id.return_value = User(id=1)

    result = await service.get_user_by_id(1)

    assert result.id == 1
    mock_repo.get_user_by_id.assert_awaited_once_with(1)


@pytest.mark.asyncio
async def test_get_user_by_username(service, mock_repo):
    """
    Тестує отримання користувача за іменем користувача.
    """
    await service.get_user_by_username("admin")

    mock_repo.get_user_by_username.assert_awaited_once_with("admin")


@pytest.mark.asyncio
async def test_get_user_by_email(service, mock_repo):
    """
    Тестує отримання користувача за email.
    """
    await service.get_user_by_email("user@example.com")

    mock_repo.get_user_by_email.assert_awaited_once_with("user@example.com")


@pytest.mark.asyncio
async def test_confirmed_email(service, mock_repo):
    """
    Тестує підтвердження email користувача.
    """
    await service.confirmed_email("test@example.com")

    mock_repo.confirmed_email.assert_awaited_once_with("test@example.com")


@pytest.mark.asyncio
async def test_update_avatar_url(service, mock_repo):
    """
    Тестує оновлення URL аватара користувача.
    """
    await service.update_avatar_url("test@example.com", "http://avatar")

    mock_repo.update_avatar_url.assert_awaited_once_with(
        "test@example.com", "http://avatar"
    )


@pytest.mark.asyncio
async def test_update_user(service, mock_repo):
    """
    Тестує оновлення інформації про користувача.
    """
    await service.update_user(1, {"email": "new@example.com"})

    mock_repo.update_user.assert_awaited_once_with(1, {"email": "new@example.com"})
