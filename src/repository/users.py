import json
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from redis.asyncio import Redis
from src.database.models import User
from src.schemas.user import UserCreate


def user_to_dict(user: User) -> dict:
    """
    Перетворює об'єкт User в словник для кешування.
    Використовується для зберігання в Redis.
    """
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "avatar_url": user.avatar_url,
        "confirmed": user.confirmed,
    }


class UserRepository:
    """
    Репозиторій для роботи з користувачами, використовує Redis для кешування
    та SQLAlchemy для роботи з базою даних.
    """

    def __init__(self, session: AsyncSession):
        self.db = session
        self.redis = Redis(host="localhost", port=6379, decode_responses=True)

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Отримує користувача за ID, використовуючи кеш Redis.
        """
        cache_key = f"user:id:{user_id}"
        cached = await self.redis.get(cache_key)
        if cached:
            user_dict = json.loads(cached)
            return User(**user_dict)

        stmt = select(User).filter_by(id=user_id)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            await self.redis.set(cache_key, json.dumps(user_to_dict(user)), ex=300)
        return user

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Отримує користувача за email, використовуючи кеш Redis.
        """
        cache_key = f"user:email:{email}"
        cached = await self.redis.get(cache_key)
        if cached:
            user_dict = json.loads(cached)
            return User(**user_dict)

        stmt = select(User).filter_by(email=email)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            await self.redis.set(cache_key, json.dumps(user_to_dict(user)), ex=300)
        return user

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Отримує користувача за username, використовуючи кеш Redis.
        """
        cache_key = f"user:username:{username}"
        cached = await self.redis.get(cache_key)
        if cached:
            user_dict = json.loads(cached)
            return User(**user_dict)

        stmt = select(User).filter_by(username=username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            await self.redis.set(cache_key, json.dumps(user_to_dict(user)), ex=300)
        return user

    async def create_user(self, user_data: UserCreate, avatar_url: str = None) -> User:
        """
        Створює нового користувача в базі даних та кешує його в Redis.
        """
        user_dict = user_data.model_dump()
        if avatar_url:
            user_dict["avatar_url"] = avatar_url
        user = User(**user_dict)
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)

        keys = [
            f"user:id:{user.id}",
            f"user:email:{user.email}",
            f"user:username:{user.username}",
        ]
        for key in keys:
            await self.redis.set(key, json.dumps(user_to_dict(user)), ex=300)
        return user

    async def confirmed_email(self, email: str) -> None:
        """
        Підтверджує електронну адресу користувача.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.confirmed = True
            await self.db.commit()

            await self.redis.delete(f"user:email:{email}")
            await self.redis.delete(f"user:id:{user.id}")
            await self.redis.delete(f"user:username:{user.username}")

    async def update_avatar_url(self, email: str, url: str) -> Optional[User]:
        """
        Оновлює URL аватара користувача за email.
        """
        user = await self.get_user_by_email(email)
        if user:
            user.avatar_url = url
            await self.db.commit()
            await self.db.refresh(user)

            keys = [
                f"user:email:{email}",
                f"user:id:{user.id}",
                f"user:username:{user.username}",
            ]
            for key in keys:
                await self.redis.set(key, json.dumps(user_to_dict(user)), ex=300)
        return user

    async def update_user(self, user_id: int, data: dict) -> Optional[User]:
        """
        Оновлює інформацію про користувача за його ID.
        """
        user = await self.get_user_by_id(user_id)
        if user:
            allowed_fields = {"username", "email", "avatar_url"}
            for key, value in data.items():
                if key in allowed_fields:
                    setattr(user, key, value)
            await self.db.commit()
            await self.db.refresh(user)

            keys = [
                f"user:id:{user_id}",
                f"user:email:{user.email}",
                f"user:username:{user.username}",
            ]
            for key in keys:
                await self.redis.set(key, json.dumps(user_to_dict(user)), ex=300)
        return user
