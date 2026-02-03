"""Репозитории для работы с базой данных."""
from typing import Optional, List
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from datetime import date, datetime, time

from database.models import User, Medication, MedicationSchedule, NotificationLog, NotificationRetry


class BaseRepository:
    """Базовый репозиторий с общими методами."""
    
    def __init__(self, session: AsyncSession):
        self.session = session


class UserRepository(BaseRepository):
    """Репозиторий для работы с пользователями."""
    
    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Получить пользователя по ID."""
        result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create(self, user_id: int, username: Optional[str] = None, 
                    first_name: Optional[str] = None, timezone: str = 'UTC') -> User:
        """Создать нового пользователя."""
        user = User(
            id=user_id,
            username=username,
            first_name=first_name,
            timezone=timezone
        )
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user
    
    async def update_timezone(self, user_id: int, timezone: str) -> bool:
        """Обновить часовой пояс пользователя."""
        result = await self.session.execute(
            update(User)
            .where(User.id == user_id)
            .values(timezone=timezone, updated_at=datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount > 0


class MedicationRepository(BaseRepository):
    """Репозиторий для работы с лекарствами."""
    
    async def create(self, user_id: int, name: str, description: Optional[str] = None) -> Medication:
        """Создать новое лекарство."""
        medication = Medication(
            user_id=user_id,
            name=name,
            description=description
        )
        self.session.add(medication)
        await self.session.commit()
        await self.session.refresh(medication)
        return medication
    
    async def get_by_id(self, medication_id: int) -> Optional[Medication]:
        """Получить лекарство по ID."""
        result = await self.session.execute(
            select(Medication)
            .where(Medication.id == medication_id)
            .options(selectinload(Medication.schedules))
        )
        return result.scalar_one_or_none()
    
    async def get_by_user(self, user_id: int, active_only: bool = True) -> List[Medication]:
        """Получить все лекарства пользователя."""
        query = select(Medication).where(Medication.user_id == user_id)
        if active_only:
            query = query.where(Medication.is_active == True)
        query = query.options(selectinload(Medication.schedules))
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def delete(self, medication_id: int) -> bool:
        """Удалить лекарство (каскадно удалит расписания)."""
        result = await self.session.execute(
            delete(Medication).where(Medication.id == medication_id)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def deactivate(self, medication_id: int) -> bool:
        """Деактивировать лекарство."""
        result = await self.session.execute(
            update(Medication)
            .where(Medication.id == medication_id)
            .values(is_active=False, updated_at=datetime.utcnow())
        )
        await self.session.commit()
        return result.rowcount > 0


class ScheduleRepository(BaseRepository):
    """Репозиторий для работы с расписаниями."""
    
    async def create(self, medication_id: int, frequency_type: str, dose: int,
                    time: time, start_date: date, interval_days: Optional[int] = None,
                    end_date: Optional[date] = None) -> MedicationSchedule:
        """Создать новое расписание."""
        schedule = MedicationSchedule(
            medication_id=medication_id,
            frequency_type=frequency_type,
            interval_days=interval_days,
            dose=dose,
            time=time,
            start_date=start_date,
            end_date=end_date
        )
        self.session.add(schedule)
        await self.session.commit()
        await self.session.refresh(schedule)
        return schedule
    
    async def get_by_id(self, schedule_id: int) -> Optional[MedicationSchedule]:
        """Получить расписание по ID."""
        result = await self.session.execute(
            select(MedicationSchedule)
            .where(MedicationSchedule.id == schedule_id)
            .options(selectinload(MedicationSchedule.medication).selectinload(Medication.user))
        )
        return result.scalar_one_or_none()
    
    async def get_active_schedules(self) -> List[MedicationSchedule]:
        """Получить все активные расписания с активными лекарствами."""
        result = await self.session.execute(
            select(MedicationSchedule)
            .join(Medication)
            .where(Medication.is_active == True)
            .options(
                selectinload(MedicationSchedule.medication).selectinload(Medication.user)
            )
        )
        return list(result.scalars().all())


class NotificationRepository(BaseRepository):
    """Репозиторий для работы с уведомлениями."""
    
    async def create_log(self, schedule_id: int, scheduled_time: datetime) -> NotificationLog:
        """Создать лог уведомления."""
        log = NotificationLog(
            schedule_id=schedule_id,
            scheduled_time=scheduled_time,
            status='pending'
        )
        self.session.add(log)
        await self.session.commit()
        await self.session.refresh(log)
        return log
    
    async def update_log_status(self, log_id: int, status: str, 
                               message_id: Optional[int] = None,
                               error_message: Optional[str] = None) -> bool:
        """Обновить статус лога уведомления."""
        values = {
            'status': status,
            'sent_at': datetime.utcnow() if status in ('sent', 'delivered') else None,
            'attempts': NotificationLog.attempts + 1
        }
        if message_id:
            values['message_id'] = message_id
        if error_message:
            values['error_message'] = error_message
        
        result = await self.session.execute(
            update(NotificationLog)
            .where(NotificationLog.id == log_id)
            .values(**values)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def create_retry(self, notification_log_id: int, retry_at: datetime, 
                          attempt_number: int) -> NotificationRetry:
        """Создать запись о повторной попытке."""
        retry = NotificationRetry(
            notification_log_id=notification_log_id,
            retry_at=retry_at,
            attempt_number=attempt_number,
            status='pending'
        )
        self.session.add(retry)
        await self.session.commit()
        await self.session.refresh(retry)
        return retry
    
    async def get_pending_retries(self, current_time: datetime) -> List[NotificationRetry]:
        """Получить все ожидающие повторные попытки."""
        result = await self.session.execute(
            select(NotificationRetry)
            .where(
                NotificationRetry.status == 'pending',
                NotificationRetry.retry_at <= current_time
            )
            .options(
                selectinload(NotificationRetry.notification_log)
                .selectinload(NotificationLog.schedule)
                .selectinload(MedicationSchedule.medication)
                .selectinload(Medication.user)
            )
        )
        return list(result.scalars().all())
    
    async def check_notification_sent_today(self, schedule_id: int, target_date: date) -> bool:
        """Проверить, было ли отправлено уведомление для этого расписания сегодня."""
        start_of_day = datetime.combine(target_date, datetime.min.time())
        end_of_day = datetime.combine(target_date, datetime.max.time())
        
        result = await self.session.execute(
            select(NotificationLog)
            .where(
                NotificationLog.schedule_id == schedule_id,
                NotificationLog.scheduled_time >= start_of_day,
                NotificationLog.scheduled_time <= end_of_day,
                NotificationLog.status.in_(['sent', 'delivered'])
            )
        )
        return result.scalar_one_or_none() is not None
    
    async def update_retry_status(self, retry_id: int, status: str) -> bool:
        """Обновить статус повторной попытки."""
        result = await self.session.execute(
            update(NotificationRetry)
            .where(NotificationRetry.id == retry_id)
            .values(status=status)
        )
        await self.session.commit()
        return result.rowcount > 0
    
    async def get_user_notification_logs(self, user_id: int, since_date: datetime) -> List[NotificationLog]:
        """Получить все логи уведомлений пользователя с указанной даты."""
        result = await self.session.execute(
            select(NotificationLog)
            .join(NotificationLog.schedule)
            .join(MedicationSchedule.medication)
            .where(
                Medication.user_id == user_id,
                NotificationLog.scheduled_time >= since_date
            )
            .order_by(NotificationLog.scheduled_time.desc())
            .options(
                selectinload(NotificationLog.schedule)
                .selectinload(MedicationSchedule.medication)
            )
        )
        return list(result.scalars().all())

