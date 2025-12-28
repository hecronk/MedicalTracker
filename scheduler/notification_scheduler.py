"""Планировщик для проверки расписаний и отправки уведомлений."""
import logging
from datetime import datetime, timezone
import pytz
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import async_session_maker
from database.repository import NotificationRepository
from services.notification_service import NotificationService
from config import config

logger = logging.getLogger(__name__)


async def check_and_send_notifications(bot: Bot):
    """Проверить расписания и отправить уведомления."""
    try:
        async with async_session_maker() as session:
            service = NotificationService(session, bot)
            await service.process_notifications()
            logger.info("Проверка расписаний завершена")
    except Exception as e:
        logger.error(f"Ошибка при проверке расписаний: {e}")


async def process_retries(bot: Bot):
    """Обработать повторные попытки отправки уведомлений."""
    try:
        async with async_session_maker() as session:
            notification_repo = NotificationRepository(session)
            service = NotificationService(session, bot)
            
            # Получаем все ожидающие повторные попытки
            current_time = datetime.now(timezone.utc).replace(tzinfo=None)
            retries = await notification_repo.get_pending_retries(current_time)
            
            logger.info(f"Найдено {len(retries)} повторных попыток для обработки")
            
            for retry in retries:
                try:
                    # Получаем расписание из лога
                    notification_log = retry.notification_log
                    schedule = notification_log.schedule
                    
                    # Пытаемся отправить уведомление снова
                    success, message_id, error = await service.send_notification(schedule)
                    
                    if success:
                        # Обновляем статус лога
                        await notification_repo.update_log_status(
                            notification_log.id,
                            'sent',
                            message_id=message_id
                        )
                        
                        # Помечаем retry как выполненный
                        await notification_repo.update_retry_status(retry.id, 'completed')
                        
                        logger.info(f"Повторная отправка успешна для лога {notification_log.id}")
                    
                    else:
                        # Увеличиваем номер попытки
                        next_attempt = retry.attempt_number + 1
                        
                        if next_attempt <= config.MAX_RETRY_ATTEMPTS:
                            # Планируем следующую попытку
                            await service.schedule_retry(
                                notification_log.id,
                                next_attempt
                            )
                            
                            # Помечаем текущую попытку как failed
                            await notification_repo.update_retry_status(retry.id, 'failed')
                            
                            logger.info(
                                f"Повторная отправка не удалась для лога {notification_log.id}, "
                                f"запланирована попытка {next_attempt}"
                            )
                        else:
                            # Превышено максимальное количество попыток
                            await notification_repo.update_log_status(
                                notification_log.id,
                                'failed',
                                error_message=f"Превышено максимальное количество попыток ({config.MAX_RETRY_ATTEMPTS})"
                            )
                            await notification_repo.update_retry_status(retry.id, 'failed')
                            
                            logger.warning(
                                f"Превышено максимальное количество попыток для лога {notification_log.id}"
                            )
                
                except Exception as e:
                    logger.error(f"Ошибка при обработке повторной попытки {retry.id}: {e}")
                    continue
        
        logger.info("Обработка повторных попыток завершена")
    
    except Exception as e:
        logger.error(f"Ошибка при обработке повторных попыток: {e}")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    """
    Настроить и запустить планировщик задач.
    
    Args:
        bot: Экземпляр бота для отправки сообщений
    
    Returns:
        AsyncIOScheduler: Настроенный планировщик
    """
    scheduler = AsyncIOScheduler(timezone=pytz.UTC)
    
    # Задача проверки расписаний
    scheduler.add_job(
        check_and_send_notifications,
        trigger=CronTrigger(minute='*'),
        args=[bot],
        id='check_notifications',
        replace_existing=True,
        max_instances=1
    )
    
    # Задача обработки повторных попыток
    scheduler.add_job(
        process_retries,
        trigger=CronTrigger(minute='*'),
        args=[bot],
        id='process_retries',
        replace_existing=True,
        max_instances=1
    )
    
    logger.info("Планировщик настроен:")
    logger.info("  - Проверка расписаний: каждый час в :00 минут")
    logger.info("  - Обработка повторных попыток: каждые 5 минут")
    
    return scheduler

