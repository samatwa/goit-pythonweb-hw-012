import pytest
from unittest.mock import AsyncMock
from fastapi import status

from src.database.db import get_db


def test_healthchecker_ok(client, monkeypatch):
    """
    Успішна відповідь при здоровій БД.
    """

    class FakeSession:
        async def execute(self, *_):
            class Result:
                def scalar_one_or_none(self):
                    return 1

            return Result()

        async def close(self):
            pass

    async def fake_get_db():
        yield FakeSession()

    monkeypatch.setitem(client.app.dependency_overrides, get_db, fake_get_db)

    response = client.get("/utils/healthchecker")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to FastAPI!"}


def test_healthchecker_db_failure(client, monkeypatch):
    """
    Помилка при виконанні запиту до БД — повинно повернути 500.
    """

    class BrokenSession:
        async def execute(self, *_):
            raise Exception("Database broken")

        async def close(self):
            pass

    async def broken_get_db():
        yield BrokenSession()

    monkeypatch.setitem(client.app.dependency_overrides, get_db, broken_get_db)

    response = client.get("/utils/healthchecker")  
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()["detail"] == "Error connecting to the database"
