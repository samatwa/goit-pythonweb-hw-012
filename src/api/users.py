from fastapi import APIRouter, Depends, Request, UploadFile, File

from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas.user import UserResponse
from src.conf.config import settings
from src.services.auth import get_current_user, get_current_admin_user
from src.services.users import UserService
from src.services.upload_file import UploadFileService


router = APIRouter(tags=["users"])
limiter = Limiter(key_func=get_remote_address)


@router.get(
    "/me",
    response_model=UserResponse,
    description="No more than 10 requests per minute",
)
@limiter.limit("10/minute")
async def me(request: Request, user: UserResponse = Depends(get_current_user)):
    """
    Отримання інформації про поточного користувача
    """
    return user


@router.patch("/avatar", response_model=UserResponse)
async def update_avatar_user(
    file: UploadFile = File(),
    user: UserResponse = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Оновлення аватара користувача (доступно лише адміністраторам)
    """
    avatar_url = await UploadFileService(
        settings.CLD_NAME, settings.CLD_API_KEY, settings.CLD_API_SECRET
    ).upload_file(file, user.username)

    user_service = UserService(db)
    updated_user = await user_service.update_avatar_url(user.email, avatar_url)

    return updated_user
