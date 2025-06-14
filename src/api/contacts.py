from typing import List
from fastapi import APIRouter, Depends, status
from fastapi.exceptions import HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.auth import get_current_user, get_db
from src.repository.contacts import ContactRepository
from src.schemas.contact import ContactCreate, ContactUpdate, ContactResponse
from src.database.models import User

router = APIRouter(prefix="/contacts", tags=["contacts"])


def get_contact_repo(db: AsyncSession = Depends(get_db)) -> ContactRepository:
    return ContactRepository(db)


# Список контактів користувача
@router.get("/", response_model=List[ContactResponse])
async def list_contacts(
    skip: int = 0,
    limit: int = 100,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.get_contacts(skip=skip, limit=limit, user=user)


# Отримання контакту за ID
@router.get("/{contact_id}", response_model=ContactResponse)
async def retrieve_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    contact = await repo.get_contact_by_id(contact_id, user)
    if contact is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return contact


# Створення нового контакту
@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_new_contact(
    contact: ContactCreate,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.create_contact(contact, user)


# Оновлення існуючого контакту
@router.put("/{contact_id}", response_model=ContactResponse)
async def update_existing_contact(
    contact_id: int,
    contact: ContactUpdate,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    updated = await repo.update_contact(contact_id, contact, user)
    if updated is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return updated


# Видалення існуючого контакту
@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_existing_contact(
    contact_id: int,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    deleted = await repo.delete_contact(contact_id, user)
    if deleted is None:
        raise HTTPException(status_code=404, detail="Контакт не знайдено")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# Пошук контактів за запитом
@router.get("/search", response_model=List[ContactResponse])
async def search_contacts(
    query: str,
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.search_contacts(query=query, user=user)


# Отримання контактів з майбутніми днями народженнями
@router.get("/upcoming-birthdays", response_model=List[ContactResponse])
async def get_upcoming_birthdays(
    user: User = Depends(get_current_user),
    repo: ContactRepository = Depends(get_contact_repo),
):
    return await repo.get_upcoming_birthdays(user=user)