from pydantic import EmailStr
import pytest
from io import BytesIO
from unittest.mock import patch, AsyncMock
from types import SimpleNamespace
from fastapi.testclient import TestClient

from main import app
from src.services.auth import get_current_user

# Mock користувача для тестів
mock_user_obj = SimpleNamespace(
    id=1,
    email="deadpool@example.com",
    username="deadpool",
    confirmed=True,  # обязательно!
    avatar_url="https://example.com/avatar.jpg",
)


@pytest.fixture(scope="module")
def client():
    """
    Створює тестовий клієнт FastAPI з підміною залежності get_current_user.
    Використовується для тестування API користувачів.
    """
    def override_get_current_user():
        return mock_user_obj

    app.dependency_overrides[get_current_user] = override_get_current_user
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@patch("src.api.users.UserService")
def test_get_me(mock_service, client):
    """
    Тестує отримання поточного користувача.
    """
    mock_service.return_value.get_user_by_email.return_value = mock_user_obj

    response = client.get("/users/me", headers={"Authorization": "Bearer test_token"})

    assert response.status_code == 200
    assert response.json()["email"] == "deadpool@example.com"
    assert response.json()["username"] == "deadpool"


@patch("src.api.users.UserService")
@patch("src.api.users.UploadFileService")
def test_update_avatar(mock_upload_service, mock_user_service, client):
    """
    Тестує оновлення аватара користувача.
    """
    mock_upload_service.return_value.upload_file.return_value = (
        "https://cdn.cloud/avatar.png"
    )

    mock_user_service.return_value.update_avatar_url = AsyncMock(
        return_value={
            "id": 1,
            "email": "deadpool@example.com",
            "username": "deadpool",
            "confirmed": True,
            "avatar_url": "https://cdn.cloud/avatar.png",
        }
    )

    fake_file = BytesIO(b"fake image content")

    response = client.patch(
        "/users/avatar",
        headers={"Authorization": "Bearer test_token"},
        files={"file": ("avatar.png", fake_file, "image/png")},
    )

    assert response.status_code == 200
    data = response.json()
    assert "avatar_url" in data
    assert data["avatar_url"] == "https://cdn.cloud/avatar.png"
