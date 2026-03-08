"""Сервис для отправки уведомлений о приеме лекарств."""
import logging
from datetime import datetime, date, timedelta, timezone
from typing import List
import pytz
from aiogram import Bot
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import async_session_maker
from database.repository import (
    ScheduleRepository,
    NotificationRepository
)
from database.models import MedicationSchedule
from config import config

logger = logging.getLogger(__name__)


class NotificationService:
    """Сервис для управления уведомлениями."""
    
    def __init__(self, session: AsyncSession, bot: Bot):
        self.session = session
        self.bot = bot
        self.schedule_repo = ScheduleRepository(session)
        self.notification_repo = NotificationRepository(session)
    
    def should_take_today(self, schedule: MedicationSchedule, target_date: date) -> bool:
        """
        Проверить, нужно ли принимать лекарство в указанную дату.
        
        Args:
            schedule: Расписание приема
            target_date: Дата для проверки
        
        Returns:
            bool: True если нужно принять в эту дату
        """
        if schedule.end_date and target_date > schedule.end_date:
            return False
        
        if target_date < schedule.start_date:
            return False
        
        if schedule.frequency_type == 'daily':
            return True
        
        if schedule.frequency_type == 'interval':
            if not schedule.interval_days:
                return False
            
            # Вычисляем количество дней с начала приема
            days_since_start = (target_date - schedule.start_date).days
            
            # Проверяем, кратно ли количество дней интервалу
            return days_since_start >= 0 and days_since_start % schedule.interval_days == 0
        
        return False
    
    async def check_scheduled_medications(self) -> List[MedicationSchedule]:
        """
        Проверить расписания и найти те, для которых нужно отправить уведомление.
        
        Returns:
            List[MedicationSchedule]: Список расписаний, требующих уведомления
        """
        # Получаем текущее время в UTC
        now_utc = datetime.now(pytz.UTC)
        
        # Получаем все активные расписания
        all_schedules = await self.schedule_repo.get_active_schedules()
        
        schedules_to_notify = []
        
        for schedule in all_schedules:
            try:
                # Получаем часовой пояс пользователя
                user_tz = pytz.timezone(schedule.medication.user.timezone)
                
                # Конвертируем текущее время в часовой пояс пользователя
                now_user_tz = now_utc.astimezone(user_tz)
                
                # Получаем время приема из расписания
                medication_time = schedule.time
                
                # Сравниваем время (только часы и минуты)
                if now_user_tz.hour == medication_time.hour and \
                   now_user_tz.minute == medication_time.minute:
                    
                    # Проверяем, нужно ли принимать сегодня
                    target_date = now_user_tz.date()
                    if self.should_take_today(schedule, target_date):
                        # Проверяем, не было ли уже отправлено уведомление
                        already_notified = await self.notification_repo.check_notification_sent_today(
                            schedule.id,
                            target_date
                        )
                        
                        if not already_notified:
                            schedules_to_notify.append(schedule)
            
            except Exception as e:
                logger.error(f"Ошибка при проверке расписания {schedule.id}: {e}")
                continue
        
        return schedules_to_notify
    
    async def send_notification(self, schedule: MedicationSchedule) -> tuple[bool, int | None, str | None]:
        """
        Отправить уведомление пользователю.
        
        Returns:
            Tuple[bool, int | None, str | None]: (успех, message_id, ошибка)
        """
        try:
            user = schedule.medication.user
            medication = schedule.medication
            
            # Формируем текст уведомления
            time_str = schedule.time.strftime("%H:%M")
            frequency_text = "каждый день" if schedule.frequency_type == 'daily' else f"через каждые {schedule.interval_days} дней"
            
            notification_text = (
                "🔔 Напоминание о приеме лекарства!\n\n"
                f"💊 {medication.name}\n"
                f"⏰ Время: {time_str}\n"
                f"💊 Количество: {schedule.dose} препарата\n"
                f"📅 Периодичность: {frequency_text}\n"
            )
            
            if medication.description:
                notification_text += f"📝 {medication.description}\n"
            
            notification_text += "\n✅ Не забудьте принять лекарство!"
            
            # Отправляем простое сообщение без кнопок
            message = await self.bot.send_message(
                chat_id=user.id,
                text=notification_text
            )
            
            return True, message.message_id, None
        
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомления для расписания {schedule.id}: {e}")
            return False, None, str(e)
    
    async def log_notification(
        self,
        schedule: MedicationSchedule,
        scheduled_time: datetime,
        success: bool,
        message_id: int | None = None,
        error_message: str | None = None
    ) -> int:
        """
        Записать лог уведомления в БД.
        
        Returns:
            int: ID созданного лога
        """
        log = await self.notification_repo.create_log(schedule.id, scheduled_time)
        
        if success:
            status = 'sent'
            await self.notification_repo.update_log_status(
                log.id,
                status,
                message_id=message_id
            )
        else:
            status = 'failed'
            await self.notification_repo.update_log_status(
                log.id,
                status,
                error_message=error_message
            )
        
        return log.id
    
    async def schedule_retry(
        self,
        notification_log_id: int,
        attempt_number: int
    ) -> bool:
        """
        Запланировать повторную попытку отправки.
        
        Args:
            notification_log_id: ID лога уведомления
            attempt_number: Номер попытки (начиная с 1)
        
        Returns:
            bool: Успех создания записи о повторной попытке
        """
        if attempt_number > len(config.retry_intervals):
            logger.warning(f"Превышено максимальное количество попыток для лога {notification_log_id}")
            return False
        
        # Вычисляем время следующей попытки
        retry_interval_minutes = config.retry_intervals[attempt_number - 1]
        retry_at = datetime.now(timezone.utc).replace(tzinfo=None) + timedelta(minutes=retry_interval_minutes)
        
        try:
            await self.notification_repo.create_retry(
                notification_log_id,
                retry_at,
                attempt_number
            )
            return True
        except Exception as e:
            logger.error(f"Ошибка при создании записи о повторной попытке: {e}")
            return False
    
    async def process_notifications(self):
        """Обработать все запланированные уведомления."""
        schedules = await self.check_scheduled_medications()
        
        for schedule in schedules:
            try:
                # Получаем текущее время для логирования
                now_utc = datetime.now(pytz.UTC)
                user_tz = pytz.timezone(schedule.medication.user.timezone)
                now_user_tz = now_utc.astimezone(user_tz)
                
                # Отправляем уведомление
                success, message_id, error = await self.send_notification(schedule)
                
                # Логируем
                log_id = await self.log_notification(
                    schedule,
                    now_user_tz,
                    success,
                    message_id,
                    error
                )
                
                # Если не удалось отправить, планируем повторную попытку
                if not success:
                    await self.schedule_retry(log_id, 1)
                    logger.info(f"Запланирована повторная попытка для лога {log_id}")
            
            except Exception as e:
                logger.error(f"Ошибка при обработке уведомления для расписания {schedule.id}: {e}")

