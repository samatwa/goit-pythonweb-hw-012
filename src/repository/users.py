from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import User
from src.schemas.user import UserCreate


class UserRepository:
    """
    Клас для роботи з користувачами
    """

    def __init__(self, session: AsyncSession):
        self.db = session

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Повертає користувача за його id
        """
        stmt = select(User).filter_by(id=user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Повертає користувача за його email
        """
        stmt = select(User).filter_by(email=email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Повертає користувача за його username
        """
        stmt = select(User).filter_by(username=username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(self, user_data: UserCreate, avatar_url: str = None) -> User:
        """
        Створює нового користувача
        """
        user_dict = user_data.model_dump()
        if avatar_url:
            user_dict["avatar_url"] = avatar_url
        user = User(**user_dict)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Підтвердження електронної пошти користувача
        """
        user = await self.get_user_by_email(email)
        if user:
            user.is_verified = True
            await self.db.commit()

    async def update_avatar_url(self, email: str, url: str) -> Optional[User]:
        """
        Оновлення URL-адреси аватара користувача
        """
        user = await self.get_user_by_email(email)
        if user:
            user.avatar_url = url
            await self.db.commit()
            await self.db.refresh(user)
        return user

    async def update_user(self, user_id: int, data: dict) -> Optional[User]:
        """
        Оновлює дані користувача за його ID
        """
        user = await self.get_user_by_id(user_id)
        if user:
            allowed_fields = {"username", "email", "avatar_url"}
            for key, value in data.items():
                if key in allowed_fields:
                    setattr(user, key, value)
            await self.db.commit()
            await self.db.refresh(user)
        return user
