import pytest
from unittest.mock import MagicMock
from src.services.auth import (
    Hash,
    create_access_token,
    create_email_token,
    get_email_from_token,
    get_current_user,
)
from src.services.auth import create_password_reset_token, verify_password_reset_token
from jose import jwt, JWTError
from datetime import datetime, timedelta, UTC
from unittest.mock import AsyncMock
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.conf.config import settings


def test_verify_password():
    """
    Тестує перевірку пароля.
    """
    hash_service = Hash()
    plain = "mysecret"
    hashed = hash_service.get_password_hash(plain)

    assert hash_service.verify_password(plain, hashed)
    assert not hash_service.verify_password("wrong", hashed)


def test_create_access_token_and_decode():
    """
    Тестує створення та декодування токену доступу.
    """
    email = "test@example.com"
    token = create_access_token({"sub": email})
    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert decoded["sub"] == email
    assert "exp" in decoded


def test_create_email_token_validity():
    """
    Тестує створення токену для електронної пошти та перевіряє термін дії.
    """
    email = "mail@example.com"
    token = create_email_token(email)
    decoded = jwt.decode(
        token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM]
    )

    assert decoded["sub"] == email
    exp = datetime.fromtimestamp(decoded["exp"], UTC)
    assert exp > datetime.now(UTC) + timedelta(days=6)


@pytest.mark.asyncio
async def test_get_email_from_token_valid():
    """
    Тестує отримання електронної пошти з токену.
    """
    email = "test@example.com"
    token = create_email_token(email)

    result = await get_email_from_token(token)

    assert result == email


@pytest.mark.asyncio
async def test_get_email_from_token_invalid():
    """
    Тестує отримання електронної пошти з некоректного токену.
    """
    bad_token = "invalid.token.value"

    with pytest.raises(HTTPException) as exc:
        await get_email_from_token(bad_token)

    assert exc.value.status_code == 422
    assert "Невірний токен" in exc.value.detail


@pytest.mark.asyncio
async def test_get_current_user_success():
    """
    Тестує отримання поточного користувача з валідним токеном.
    """
    email = "user@example.com"
    token = create_access_token({"sub": email})

    mock_db = AsyncMock(spec=AsyncSession)

    mock_user = User(id=1, email=email, username="tester", hashed_password="123")

    mock_scalars = AsyncMock()
    mock_scalars.first = MagicMock(return_value=mock_user)

    mock_result = AsyncMock()
    mock_result.scalars = AsyncMock(return_value=mock_scalars)

    mock_db.execute = AsyncMock(return_value=mock_result)

    user = await get_current_user(token=token, db=mock_db)

    assert user.email == email
    assert isinstance(user, User)


@pytest.mark.asyncio
async def test_get_current_user_invalid_token():
    """
    Тестує отримання поточного користувача з некоректним токеном.
    """
    bad_token = "bad.token"

    with pytest.raises(HTTPException) as exc:
        await get_current_user(token=bad_token, db=AsyncMock())

    assert exc.value.status_code == 401
    assert "Could not validate credentials" in exc.value.detail


def test_create_and_verify_password_reset_token():
    """
    Тестує створення та перевірку токену для скидання паролю.
    """
    email = "user@example.com"
    token = create_password_reset_token({"sub": email}, expires_delta=60)

    verified_email = verify_password_reset_token(token)
    assert verified_email == email


def test_verify_password_reset_token_invalid():
    """
    Тестує перевірку токену для скидання паролю з некоректним токеном.
    """
    with pytest.raises(HTTPException) as exc_info:
        verify_password_reset_token("invalidtoken")
    assert exc_info.value.status_code == 422
    assert "Невірний токен" in exc_info.value.detail
