"""Сервис для работы с лекарствами."""
from typing import Optional, List
from datetime import date, time
from sqlalchemy.ext.asyncio import AsyncSession

from database.repository import (
    MedicationRepository,
    ScheduleRepository,
    UserRepository
)
from database.models import Medication, MedicationSchedule


class MedicationService:
    """Сервис для управления лекарствами."""
    
    def __init__(self, session: AsyncSession):
        self.session = session
        self.medication_repo = MedicationRepository(session)
        self.schedule_repo = ScheduleRepository(session)
        self.user_repo = UserRepository(session)
    
    async def add_medication(
        self,
        user_id: int,
        name: str,
        description: Optional[str],
        frequency_type: str,
        dose: int,
        time: time,
        start_date: date,
        interval_days: Optional[int] = None,
        end_date: Optional[date] = None
    ) -> tuple[Medication, MedicationSchedule]:
        """
        Добавить новое лекарство с расписанием.
        
        Returns:
            Tuple[Medication, MedicationSchedule]: Созданные лекарство и расписание
        """
        # Создаем лекарство
        medication = await self.medication_repo.create(
            user_id=user_id,
            name=name,
            description=description
        )
        
        # Создаем расписание
        schedule = await self.schedule_repo.create(
            medication_id=medication.id,
            frequency_type=frequency_type,
            dose=dose,
            time=time,
            start_date=start_date,
            interval_days=interval_days,
            end_date=end_date
        )
        
        return medication, schedule
    
    async def get_user_medications(
        self,
        user_id: int,
        active_only: bool = True
    ) -> List[Medication]:
        """Получить все лекарства пользователя."""
        return await self.medication_repo.get_by_user(user_id, active_only)
    
    async def get_medication_by_id(self, medication_id: int) -> Optional[Medication]:
        """Получить лекарство по ID."""
        return await self.medication_repo.get_by_id(medication_id)
    
    async def delete_medication(self, medication_id: int) -> bool:
        """Удалить лекарство (каскадно удалит расписания)."""
        return await self.medication_repo.delete(medication_id)
    
    async def deactivate_medication(self, medication_id: int) -> bool:
        """Деактивировать лекарство."""
        return await self.medication_repo.deactivate(medication_id)

