"""Базовые классы для работы с базой данных."""
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from config import config


# Создаем async engine
engine = create_async_engine(
    config.database_url,
    echo=True,  # Логирование SQL запросов (можно отключить в продакшене)
    future=True,
)

# Создаем session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Базовый класс для всех моделей."""
    pass


async def get_session() -> AsyncSession:
    """Получить сессию базы данных."""
    async with async_session_maker() as session:
        yield session

