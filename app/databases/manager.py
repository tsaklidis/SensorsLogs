import logging

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

logger = logging.getLogger(__name__)

class AsyncDatabaseManager:
    _engine = None
    _sessionmaker = None

    @classmethod
    def get_engine(cls):
        if cls._engine is None:
            cls._engine = create_async_engine(
                settings.DATABASE_URL,
                echo=False,
                future=True,
            )
        return cls._engine

    @classmethod
    def get_sessionmaker(cls):
        if cls._sessionmaker is None:
            cls._sessionmaker = async_sessionmaker(
                bind=cls.get_engine(),
                expire_on_commit=False,
                class_=AsyncSession,
            )
        return cls._sessionmaker

# Dependency for FastAPI
async def get_db():
    sessionmaker = AsyncDatabaseManager.get_sessionmaker()
    async with sessionmaker() as session:
        yield session