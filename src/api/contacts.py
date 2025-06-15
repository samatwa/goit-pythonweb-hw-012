from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth import get_current_user, get_db
from src.repository.contacts import ContactRepository
from src.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from src.database.models import User

router = APIRouter(tags=["contacts"])


def get_contact_repo(db: AsyncSession = Depends(get_db)) -> ContactRepository:
    """
    Функція для отримання репозиторію контактів
    """
    return ContactRepository(db)


@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Отримання списку контактів з пагінацією
    """
    return await repo.get_contacts(skip=skip, limit=limit, user=user)


@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(
    query: str,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Пошук контактів за запитом
    """
    return await repo.search_contacts(query=query, user=user)


@router.get("/upcoming-birthdays", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Отримання контактів з найближчими днями народження
    """
    return await repo.get_upcoming_birthdays(user=user)


@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_new_contact(
    contact: ContactCreate,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Створення нового контакту
    """
    return await repo.create_contact(contact, user)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_existing_contact(
    contact_id: int,
    contact: ContactUpdate,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Оновлення існуючого контакту
    """
    updated = await repo.update_contact(contact_id, contact, user)
    if updated is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return updated


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Видалення існуючого контакту
    """
    deleted = await repo.delete_contact(contact_id, user)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/{contact_id}", response_model=ContactResponse)
async def retrieve_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    """
    Отримання контакту за ID
    """
    contact = await repo.get_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return contact
