from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional


class UserCreate(BaseModel):
    """
    Клас для створення нового користувача
    """

    email: EmailStr
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=8, max_length=100)


class UserResponse(BaseModel):
    """
    Клас для отримання інформації про користувача
    """

    id: int
    email: EmailStr
    username: str
    is_verified: bool
    avatar_url: Optional[str]

    class Config:
        from_attributes = True


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


class RequestEmail(BaseModel):
    """
    Клас для отримання електронної пошти
    """
    email: EmailStr
