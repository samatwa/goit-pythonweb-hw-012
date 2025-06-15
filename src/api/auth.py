from fastapi import APIRouter, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from src.schemas.user import UserCreate, Token, UserResponse, RequestEmail, UserUpdate
from src.schemas.user import PasswordResetRequest, PasswordResetConfirm, RefreshTokenRequest
from src.services.auth import (
    create_access_token,
    create_refresh_token,
    verify_token,
    Hash,
    get_email_from_token,
    get_current_user,
    get_current_admin_user
)
from src.services.auth import create_password_reset_token, verify_password_reset_token
from src.services.users import UserService
from src.services.email import send_email, send_password_reset_email
from src.database.db import get_db
from src.database.models import User


router = APIRouter(tags=["auth"])


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(
    user_data: UserCreate,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Реєстрація нового користувача
    """
    user_service = UserService(db)

    email_user = await user_service.get_user_by_email(user_data.email)
    if email_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким email вже існує",
        )

    username_user = await user_service.get_user_by_username(user_data.username)
    if username_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Користувач з таким іменем вже існує",
        )
    user_data.password = Hash().get_password_hash(user_data.password)
    new_user = await user_service.create_user(user_data)
    background_tasks.add_task(
        send_email, new_user.email, new_user.username, request.base_url
    )
    return new_user


@router.post("/login")
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    """
    Логін користувача, повертає токени доступу та оновлення
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_username(form_data.username)
    if not user or not Hash().verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неправильний логін або пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Електронна адреса не підтверджена",
        )

    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_access_token(body: RefreshTokenRequest):
    """
    Оновлення токену доступу за допомогою refresh токену
    """
    try:
        email = verify_token(body.refresh_token)
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access_token = create_access_token(data={"sub": email})
    return {"access_token": new_access_token, "token_type": "bearer"}


@router.get("/confirmed_email/{token}")
async def confirmed_email(token: str, db: AsyncSession = Depends(get_db)):
    """
    Підтвердження електронної пошти за токеном
    """
    email = await get_email_from_token(token)
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error"
        )
    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    await user_service.confirmed_email(email)
    return {"message": "Електронну пошту підтверджено"}


@router.post("/request_email")
async def request_email(
    body: RequestEmail,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Запит на підтвердження електронної пошти
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)

    if user.confirmed:
        return {"message": "Ваша електронна пошта вже підтверджена"}
    if user:
        background_tasks.add_task(
            send_email, user.email, user.username, request.base_url
        )
    return {"message": "Перевірте свою електронну пошту для підтвердження"}


@router.put("/users/me", response_model=UserResponse)
async def update_current_user(
    body: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Оновлення інформації про поточного користувача
    """
    user_service = UserService(db)

    # Перевірка: чи намагається змінити email на вже існуючий
    if body.email and body.email != current_user.email:
        existing_user = await user_service.get_user_by_email(body.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Користувач з таким email вже існує",
            )

    updated_user = await user_service.update_user(
        current_user.id, body.dict(exclude_unset=True)
    )
    return updated_user


@router.post("/password-reset/request")
async def request_password_reset(
    body: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Запит на скидання пароля — відправка листа з посиланням для скидання пароля.
    """
    user_service = UserService(db)
    user = await user_service.get_user_by_email(body.email)
    if not user:
        return {
            "message": "Якщо користувач з такою електронною поштою існує, лист буде надіслано."
        }
    if not user.confirmed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Електронна пошта не підтверджена",
        )

    reset_token = create_password_reset_token({"sub": user.email})
    reset_link = str(request.base_url) + f"password-reset/confirm?token={reset_token}"

    background_tasks.add_task(send_password_reset_email, user.email, reset_link)

    return {
        "message": "Якщо користувач з такою електронною поштою існує, лист буде надіслано."
    }


@router.post("/password-reset/confirm")
async def confirm_password_reset(
    body: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
):
    """
    Підтвердження скидання пароля за токеном.
    """
    try:
        email = verify_password_reset_token(body.token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Невірний токен для скидання пароля",
        )
    user_service = UserService(db)
    user = await user_service.get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=404, detail="Користувач не знайдений")

    hashed_password = Hash().get_password_hash(body.new_password)
    await user_service.update_user(user.id, {"hashed_password": hashed_password})

    return {"message": "Пароль успішно змінено"}


@router.get("/public")
def read_public():
    """ Публічний маршрут, доступний для всіх
    """
    return {"message": "Це публічний маршрут, доступний для всіх"}


@router.get("/admin")
def read_admin(current_user: User = Depends(get_current_admin_user)):
    """ Адміністративний маршрут, доступний тільки для адміністратора
    """
    return {"message": f"Вітаємо, {current_user.username}! Це адміністративний маршрут"}
