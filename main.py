"""Точка входа приложения."""
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from config import config
from bot.middlewares.user_middleware import UserMiddleware
from bot.middlewares.error_middleware import ErrorMiddleware
from bot.handlers import start, medication, schedule
from scheduler.notification_scheduler import setup_scheduler

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """Главная функция запуска бота."""
    # Проверка наличия токена
    if not config.BOT_TOKEN:
        logger.error("❌ BOT_TOKEN не установлен! Проверьте файл .env")
        return
    
    # Инициализация бота и диспетчера
    bot = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Регистрация middleware (порядок важен - последний добавленный выполняется первым)
    dp.message.middleware(ErrorMiddleware())
    dp.callback_query.middleware(ErrorMiddleware())
    dp.message.middleware(UserMiddleware())
    dp.callback_query.middleware(UserMiddleware())
    
    # Регистрация роутеров
    dp.include_router(start.router)
    dp.include_router(medication.router)
    dp.include_router(schedule.router)
    
    # Настройка планировщика
    scheduler = setup_scheduler(bot)
    scheduler.start()
    logger.info("✅ Планировщик запущен")
    
    try:
        logger.info("🚀 Бот запущен!")
        # Запуск polling
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Ошибка при запуске бота: {e}")
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
