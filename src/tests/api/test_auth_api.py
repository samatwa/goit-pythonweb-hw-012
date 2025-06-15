import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from src.api.auth import create_password_reset_token
from src.tests.conftest import client


@patch("src.api.auth.UserService")
@patch("src.api.auth.Hash.verify_password", return_value=True)
def test_login_success(mock_verify, mock_user_service, client):
    """
    Тестує успішний логін користувача.
    Перевіряє, що при правильному логіні повертається токен доступу.
    """
    fake_user = AsyncMock()
    fake_user.username = "deadpool"
    fake_user.email = "deadpool@example.com"
    fake_user.hashed_password = "hashed_password"
    fake_user.confirmed = True

    mock_user_service.return_value.get_user_by_username = AsyncMock(
        return_value=fake_user
    )

    response = client.post(
        "/auth/login",
        data={"username": "deadpool", "password": "12345678"},
    )

    assert response.status_code == 200
    assert "access_token" in response.json()


@patch("src.api.auth.UserService")
@patch("src.api.auth.Hash.verify_password", return_value=False)
def test_login_invalid_password(mock_verify, mock_user_service, client):
    """
    Тестує логін користувача з неправильним паролем.
    Перевіряє, що при неправильному паролі повертається статус 401.
    """
    fake_user = AsyncMock()
    fake_user.username = "deadpool"
    fake_user.email = "deadpool@example.com"
    fake_user.hashed_password = "wrong_hash"
    fake_user.confirmed = True

    mock_user_service.return_value.get_user_by_username = AsyncMock(
        return_value=fake_user
    )

    response = client.post(
        "/auth/login",
        data={"username": "deadpool", "password": "wrongpass"},
    )

    assert response.status_code == 401


@patch("src.api.auth.UserService")
def test_register_conflict_email(mock_user_service, client):
    """
    Тестує реєстрацію користувача з конфліктом email.
    Перевіряє, що при реєстрації користувача з конфліктом email повертається статус 409.
    """
    mock_user_service.return_value.get_user_by_email = AsyncMock(
        return_value={"email": "deadpool@example.com"}
    )
    mock_user_service.return_value.get_user_by_username = AsyncMock(return_value=None)

    response = client.post(
        "/auth/register",
        json={
            "username": "newuser",
            "email": "deadpool@example.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 409


@patch("src.api.auth.UserService")
def test_register_conflict_username(mock_user_service, client):
    """
    Тестує реєстрацію користувача з конфліктом імені користувача.
    Перевіряє, що при реєстрації користувача з конфліктом імені користувача повертається статус 409.
    """
    mock_user_service.return_value.get_user_by_email = AsyncMock(return_value=None)
    mock_user_service.return_value.get_user_by_username = AsyncMock(
        return_value={"username": "deadpool"}
    )

    response = client.post(
        "/auth/register",
        json={
            "username": "deadpool",
            "email": "unique@example.com",
            "password": "12345678",
        },
    )

    assert response.status_code == 409


def test_password_reset_request(client):
    email = "existing_user@example.com"
    response = client.post("/auth/password-reset/request", json={"email": email})
    assert response.status_code == 200
    assert "лист буде надіслано" in response.json().get("message")


def test_password_reset_request_non_existing_user(client):
    response = client.post(
        "/auth/password-reset/request", json={"email": "nonexistent@example.com"}
    )
    assert response.status_code == 200
    assert "лист буде надіслано" in response.json().get("message")


def test_password_reset_confirm(client):
    email = "deadpool@example.com"
    token = create_password_reset_token({"sub": email})
    new_password = "new_secure_password123"

    response = client.post(
        "/auth/password-reset/confirm",
        json={"token": token, "new_password": new_password},
    )
    assert response.status_code == 200
    assert "успішно змінено" in response.json().get("message")


def test_password_reset_confirm_invalid_token(client):
    response = client.post(
        "/auth/password-reset/confirm",
        json={"token": "invalidtoken", "new_password": "any_password123"},
    )
    assert response.status_code == 400
    assert "Невірний токен" in response.json().get("detail")
