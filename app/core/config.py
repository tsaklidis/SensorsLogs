import os
import secrets
import warnings
from random import random

from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()

class EnvSettings(BaseSettings):
    BASE_URL: str = os.getenv("BASE_URL", "http://localhost:8000")

    # Redis (cache)
    REDIS_CACHE_HOST: str = os.getenv("REDIS_CACHE_HOST", "redis-cache")
    REDIS_CACHE_PORT: int = int(os.getenv("REDIS_CACHE_PORT", 6369))
    REDIS_CACHE_USE_SSL: bool = bool(int(os.getenv("REDIS_CACHE_USE_SSL", 0)))
    REDIS_CACHE_PASSWORD: str = os.getenv("REDIS_CACHE_PASSWORD", "")
    REDIS_CACHE_DB: int = int(os.getenv("REDIS_CACHE_DB", 0))
    REDIS_CACHE_URL: str = os.getenv("REDIS_CACHE_URL", f"redis://redis-cache:{REDIS_CACHE_PORT}/0")

    # Postgres
    POSTGRES_HOST: str = os.getenv("POSTGRES_HOST", "postgres")
    POSTGRES_PORT: int = int(os.getenv("POSTGRES_PORT", 5432))
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "sensors_db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "sensorsuser")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "strongpassword")
    DATABASE_URL_ASYNC: str = os.getenv(
        "DATABASE_URL_ASYNC",
        f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )
    DATABASE_URL_SYNC: str = os.getenv(
        "DATABASE_URL_SYNC",
        f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
    )

    # CRITICAL = 50
    # FATAL = CRITICAL
    # ERROR = 40
    # WARNING = 30
    # INFO = 20
    # DEBUG = 10
    LOG_LEVEL : int = int(os.getenv("LOG_LEVEL", 30))
    SQL_LOG_LEVEL : int = int(os.getenv("SQL_LOG_LEVEL", 30))

    DB_NAME: str = os.getenv("DB_NAME", "sensors_db.db")
    APP_API_TOKEN: str = os.getenv("APP_API_TOKEN", secrets.token_urlsafe(32))
    ADMIN_URL: str = os.getenv("ADMIN_URL", secrets.token_urlsafe(32))

    # JWT Settings - SECURITY: No random defaults!
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", 7))

    # SECURITY: Account lockout settings to prevent brute force attacks
    MAX_LOGIN_ATTEMPTS: int = int(os.getenv("MAX_LOGIN_ATTEMPTS", 5))
    LOCKOUT_DURATION_MINUTES: int = int(os.getenv("LOCKOUT_DURATION_MINUTES", 15))
    # Reset failed attempts counter after this many minutes of no failures
    FAILED_ATTEMPTS_RESET_MINUTES: int = int(os.getenv("FAILED_ATTEMPTS_RESET_MINUTES", 60))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # SECURITY: Validate critical settings
        if not self.JWT_SECRET_KEY:
            raise ValueError(
                "SECURITY ERROR: JWT_SECRET_KEY must be set in environment variables!\n"
                "Generate one with: python -c \"import secrets; print(secrets.token_urlsafe(32))\"\n"
                "Add it to your .env file: JWT_SECRET_KEY=<generated_key>"
            )

        if len(self.JWT_SECRET_KEY) < 32:
            raise ValueError(
                "SECURITY ERROR: JWT_SECRET_KEY must be at least 32 characters long for adequate security!"
            )

        # Warn about weak admin URL
        if self.ADMIN_URL in ['admin', '/admin', 'admin-panel', '/admin-panel']:
            warnings.warn(
                "SECURITY WARNING: ADMIN_URL is easily guessable! "
                "Use a random string: python -c \"import secrets; print('/admin-' + secrets.token_urlsafe(16))\""
            )

settings = EnvSettings()
