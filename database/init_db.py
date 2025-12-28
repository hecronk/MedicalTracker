"""Скрипт инициализации базы данных."""
import asyncio
from sqlalchemy import text
from database.base import engine, Base
from database.models import User, Medication, MedicationSchedule, NotificationLog, NotificationRetry


async def init_db():
    """Создать все таблицы в базе данных."""
    async with engine.begin() as conn:
        # Удаляем все таблицы (для разработки)
        # В продакшене лучше использовать миграции Alembic
        await conn.run_sync(Base.metadata.drop_all)
        
        # Создаем все таблицы
        await conn.run_sync(Base.metadata.create_all)
        
        print("✅ База данных успешно инициализирована!")
        print("📋 Созданы таблицы:")
        print("   - users")
        print("   - medications")
        print("   - medication_schedules")
        print("   - notification_logs")
        print("   - notification_retries")


async def test_connection():
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


async def main():
    """Главная функция."""
    print("🔌 Проверка подключения к базе данных...")
    if await test_connection():
        print("\n📦 Инициализация таблиц...")
        await init_db()
    else:
        print("\n⚠️  Убедитесь, что PostgreSQL запущен и настройки в .env файле корректны.")


if __name__ == "__main__":
    asyncio.run(main())

