"""Скрипт инициализации базы данных через Alembic.

Для применения миграций из командной строки используйте:
    alembic upgrade head

Этот скрипт предназначен для проверки подключения и применения миграций
в автоматическом режиме (например, при первом запуске):
    python -m database.init_db
"""
import asyncio
from sqlalchemy import text
from database.base import engine


async def test_connection() -> bool:
    """Протестировать подключение к базе данных."""
    try:
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            result.scalar()
        print("✅ Подключение к базе данных успешно!")
        return True
    except Exception as e:
        print(f"❌ Ошибка подключения к базе данных: {e}")
        return False


def run_migrations() -> None:
    """Применить все ожидающие миграции Alembic."""
    from alembic.config import Config
    from alembic import command

    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    print("✅ Миграции успешно применены!")


async def main() -> None:
    """Главная функция."""
    print("🔌 Проверка подключения к базе данных...")
    if await test_connection():
        print("\n📦 Применение миграций Alembic...")
        run_migrations()
    else:
        print("\n⚠️  Убедитесь, что PostgreSQL запущен и настройки в .env файле корректны.")


if __name__ == "__main__":
    asyncio.run(main())

