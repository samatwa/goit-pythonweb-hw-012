from pydantic_settings import BaseSettings
from pydantic import ConfigDict, EmailStr


class Settings(BaseSettings):
    """
    Налаштування додатку
    """
    DATABASE_URL: str
    app_title: str = "Contacts API"
    app_description: str = "REST API для управління контактами"
    app_version: str = "1.0.0"
    debug: bool = False

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_SECONDS: int = 3600
    JWT_REFRESH_EXPIRATION_DAYS: int = 3

    MAIL_USERNAME: EmailStr 
    MAIL_PASSWORD: str
    MAIL_FROM: EmailStr
    MAIL_PORT: int 
    MAIL_SERVER: str 
    MAIL_FROM_NAME: str
    MAIL_STARTTLS: bool
    MAIL_SSL_TLS: bool
    USE_CREDENTIALS: bool
    VALIDATE_CERTS: bool

    CLD_NAME: str
    CLD_API_KEY: str
    CLD_API_SECRET: str

    model_config = ConfigDict(env_file=".env", extra="ignore")

settings = Settings()
