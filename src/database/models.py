from typing import Optional, List
from enum import Enum
from sqlalchemy import Integer, String, Boolean, ForeignKey, Enum as SqlEnum
from sqlalchemy.sql.sqltypes import Date, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.orm import DeclarativeBase
from src.database.db import Base
from datetime import date

class Base(DeclarativeBase):
    pass

class UserRole(str, Enum):
    """
    Перерахування ролей користувача
    """
    ADMIN = "admin"
    USER = "user"

class User(Base):
    """
    Модель користувача для бази даних
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True, index=True
    )
    username: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)
    hashed_password: Mapped[str] = mapped_column(String(100), nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    contacts: Mapped[List["Contact"]] = relationship(
        "Contact", back_populates="user", cascade="all, delete"
    )
    role: Mapped[str] = mapped_column(SqlEnum(UserRole), default=UserRole.USER, nullable=False)


class Contact(Base):
    """
    Модель контакту для бази даних
    """
    __tablename__ = "contacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    first_name: Mapped[str] = mapped_column(String(50), nullable=False)
    last_name: Mapped[str] = mapped_column(String(50), nullable=False)
    email: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    birthday: Mapped[date] = mapped_column(Date, nullable=False)
    additional_data: Mapped[str] = mapped_column(Text, nullable=True)

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    user: Mapped["User"] = relationship("User", back_populates="contacts")
