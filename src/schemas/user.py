from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from src.database.models import UserRole


class UserCreate(BaseModel):
    """
    Клас для створення нового користувача
    """

    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)
    role: Optional[UserRole] = UserRole.USER


class UserResponse(BaseModel):
    """
    Клас для отримання інформації про користувача
    """

    id: int
    email: EmailStr
    username: str
    confirmed: bool
    avatar_url: Optional[str]
    role: UserRole

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    username: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr] = None
    avatar_url: Optional[str] = None


class Token(BaseModel):
    """
    Клас для отримання токену
    """

    access_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    """
    Клас для запиту на отримання нового токену
    """
    refresh_token: str


class RequestEmail(BaseModel):
    """
    Клас для отримання електронної пошти
    """

    email: EmailStr


class PasswordResetRequest(BaseModel):
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8, max_length=100)
