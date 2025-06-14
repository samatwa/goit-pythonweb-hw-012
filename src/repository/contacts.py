from typing import List, Optional
from sqlalchemy import select, or_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Contact, User
from src.schemas.contact import ContactCreate, ContactUpdate
from datetime import date, timedelta


class ContactRepository:
    """
    Клас для роботи з контактами
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_contacts(self, skip: int, limit: int, user: User) -> List[Contact]:
        """
        Повертає список контактів користувача
        """
        stmt = select(Contact).filter_by(user_id=user.id).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_contact_by_id(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Повертає контакт за його id
        """
        stmt = select(Contact).filter_by(id=contact_id, user_id=user.id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_contact(self, body: ContactCreate, user: User) -> Contact:
        """
        Створює новий контакт
        """
        contact = Contact(**body.model_dump(), user_id=user.id)
        self.db.add(contact)
        await self.db.commit()
        await self.db.refresh(contact)
        return contact

    async def update_contact(
        self, contact_id: int, body: ContactUpdate, user: User
    ) -> Optional[Contact]:
        """
        Оновлює контакт за його id
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            for key, value in body.model_dump(exclude_unset=True).items():
                setattr(contact, key, value)
            await self.db.commit()
            await self.db.refresh(contact)
        return contact

    async def delete_contact(self, contact_id: int, user: User) -> Optional[Contact]:
        """
        Видаляє контакт за його id
        """
        contact = await self.get_contact_by_id(contact_id, user)
        if contact:
            await self.db.delete(contact)
            await self.db.commit()
        return contact

    async def search_contacts(self, query: str, user: User) -> List[Contact]:
        """
        Пошук контактів за запитом
        """
        stmt = select(Contact).filter(
            Contact.user_id == user.id,
            or_(
                Contact.first_name.ilike(f"%{query}%"),
                Contact.last_name.ilike(f"%{query}%"),
                Contact.email.ilike(f"%{query}%"),
                Contact.phone.ilike(f"%{query}%"),
            ),
        )
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def get_upcoming_birthdays(self, user: User) -> List[Contact]:
        """
        Повертає контакти з днем народження в найближчі 7 днів (включно), незалежно від місяця
        """
        today = date.today()
        end_date = today + timedelta(days=7)

        stmt = select(Contact).where(Contact.user_id == user.id)
        result = await self.db.execute(stmt)
        contacts = result.scalars().all()

        upcoming_contacts = []
        for contact in contacts:
            if contact.birthday:
                try:
                    bd_this_year = contact.birthday.replace(year=today.year)
                except ValueError:
                    # Наприклад, якщо день народження 29 лютого, а рік не високосний
                    continue
                if today <= bd_this_year <= end_date:
                    upcoming_contacts.append(contact)

        return upcoming_contacts