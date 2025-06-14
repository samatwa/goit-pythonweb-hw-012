from pydantic import BaseModel, EmailStr, Field
from datetime import date
from typing import Optional


class ContactBase(BaseModel):
    """
    Клас для створення контакту
    """

    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr
    phone: str = Field(..., min_length=10, max_length=30)
    birthday: date
    additional_data: Optional[str] = Field(None, max_length=500)


class ContactCreate(ContactBase):
    """
    Клас для створення контакту
    """

    pass


class ContactUpdate(BaseModel):
    """
    Клас для оновлення контакту
    """

    first_name: Optional[str] = Field(None, min_length=1, max_length=50)
    last_name: Optional[str] = Field(None, min_length=1, max_length=50)
    email: Optional[EmailStr]
    phone: Optional[str] = Field(None, min_length=10, max_length=30)
    birthday: Optional[date]
    additional_data: Optional[str] = Field(None, max_length=500)


class ContactResponse(ContactBase):
    """
    Клас для отримання контакту
    """

    id: int

    class Config:
        from_attributes = True
