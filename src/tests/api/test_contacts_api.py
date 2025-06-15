from unittest.mock import AsyncMock, MagicMock
from datetime import date, timedelta
import pytest
from src.repository.contacts import ContactRepository
from src.database.models import Contact, User
from src.schemas.contact import ContactCreate, ContactUpdate


@pytest.fixture
def mock_session():
    mock = AsyncMock()
    mock.add = MagicMock()  # синхронный мок для add()
    return mock


@pytest.fixture
def repo(mock_session):
    return ContactRepository(mock_session)


@pytest.fixture
def test_user():
    return User(id=1)


@pytest.mark.asyncio
async def test_get_contacts(repo, mock_session, test_user):
    contacts = [Contact(id=1, first_name="Alice")]

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = contacts

    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    result = await repo.get_contacts(0, 10, test_user)

    assert result == contacts


@pytest.mark.asyncio
async def test_get_contact_by_id_found(repo, mock_session, test_user):
    contact = Contact(id=1, user_id=1, first_name="Bob")

    mock_result = AsyncMock()
    mock_result.scalar_one_or_none.return_value = contact

    mock_session.execute.return_value = mock_result

    result = await repo.get_contact_by_id(1, test_user)

    assert result == contact


@pytest.mark.asyncio
async def test_create_contact(repo, mock_session, test_user):
    body = ContactCreate(
        first_name="New",
        last_name="Contact",
        email="test@example.com",
        phone="1234567890",
        birthday=date(1990, 1, 1),
        additional_info="info",
    )

    mock_session.refresh = AsyncMock()

    result = await repo.create_contact(body, test_user)

    assert isinstance(result, Contact)
    assert result.first_name == "New"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact_found(repo, mock_session, test_user):
    contact = Contact(id=1, first_name="Old", user_id=1)
    repo.get_contact_by_id = AsyncMock(return_value=contact)

    body = ContactUpdate(
        first_name="Updated",
        last_name="Old",
        email="old@example.com",
        phone="1234567890",
        birthday=date(1990, 1, 1),
        additional_info="info",
    )
    mock_session.refresh = AsyncMock()

    result = await repo.update_contact(1, body, test_user)

    assert result.first_name == "Updated"
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_update_contact_not_found(repo, test_user):
    repo.get_contact_by_id = AsyncMock(return_value=None)

    body = ContactUpdate(
        first_name="NoOne",
        last_name="None",
        email="none@example.com",
        phone="1234567890",
        birthday=date(1990, 1, 1),
        additional_info="nothing",
    )

    result = await repo.update_contact(1, body, test_user)

    assert result is None


@pytest.mark.asyncio
async def test_delete_contact_found(repo, mock_session, test_user):
    contact = Contact(id=1, user_id=1)
    repo.get_contact_by_id = AsyncMock(return_value=contact)

    result = await repo.delete_contact(1, test_user)

    assert result == contact
    mock_session.commit.assert_called_once()


@pytest.mark.asyncio
async def test_search_contacts(repo, mock_session, test_user):
    contacts = [Contact(id=1, first_name="Match")]

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = contacts

    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    result = await repo.search_contacts("mat", test_user)

    assert result == contacts


@pytest.mark.asyncio
async def test_get_upcoming_birthdays(repo, mock_session, test_user):
    today = date.today()
    next_week = today + timedelta(days=5)

    contact_1 = Contact(id=1, user_id=1, birthday=next_week)
    contact_2 = Contact(id=2, user_id=1, birthday=today - timedelta(days=1))
    contact_3 = Contact(id=3, user_id=1, birthday=None)

    mock_scalars = MagicMock()
    mock_scalars.all.return_value = [contact_1, contact_2, contact_3]

    mock_result = AsyncMock()
    mock_result.scalars.return_value = mock_scalars

    mock_session.execute.return_value = mock_result

    result = await repo.get_upcoming_birthdays(test_user)

    assert len(result) == 1
    assert result[0].id == 1
