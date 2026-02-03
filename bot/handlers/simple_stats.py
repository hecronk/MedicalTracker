# -*- coding: utf-8 -*-
"""Простые утилиты."""
from datetime import datetime, timedelta
import pytz
from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

from database.base import async_session_maker
from services.medication_service import MedicationService

router = Router()


def _should_take_today(schedule, target_date):
    """Проверить нужно ли принимать лекарство в указанную дату."""
    # Проверяем дату окончания
    if schedule.end_date and target_date > schedule.end_date:
        return False

    # Проверяем дату начала
    if target_date < schedule.start_date:
        return False

    # Проверяем периодичность
    if schedule.frequency_type == 'daily':
        return True

    if schedule.frequency_type == 'interval' and schedule.interval_days:
        days_since_start = (target_date - schedule.start_date).days
        return days_since_start >= 0 and days_since_start % schedule.interval_days == 0

    return False


@router.message(Command("quick_schedule"))
@router.message(F.text == "📅 Быстрый план")
async def cmd_quick_schedule(message: Message, db_user):
    """Быстрый план на сегодня."""
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            medications = await service.get_user_medications(db_user.id, active_only=True)
        
        if not medications:
            await message.answer(
                "📋 У вас нет добавленных лекарств.\n\n"
                "Используйте /add_medication, чтобы добавить первое лекарство."
            )
            return
        
        user_tz = pytz.timezone(db_user.timezone)
        now_utc = datetime.now(pytz.UTC)
        now_user_tz = now_utc.astimezone(user_tz)
        today = now_user_tz.date()
        
        text = f"📅 План приема лекарств на {today.strftime('%d.%m.%Y')}:\n\n"
        
        today_meds = []
        for medication in medications:
            for schedule in medication.schedules:
                if _should_take_today(schedule, today):
                    time_str = schedule.time.strftime("%H:%M")
                    frequency_text = "каждый день" if schedule.frequency_type == 'daily' else f"через {schedule.interval_days} дня"
                    
                    today_meds.append(f"💊 {medication.name}\n⏰ {time_str} - {schedule.dose} препарата\n📅 {frequency_text}")
        
        if not today_meds:
            await message.answer(
                f"✅ На {today.strftime('%d.%m.%Y')} нет запланированных приемов лекарств!\n"
                "Отличная работа! 🎉"
            )
            return
        
        text += "\n\n".join(today_meds)
        text += f"\n\n⏰ Текущее время: {now_user_tz.strftime('%H:%M')}"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(f"❌ Ошибка: {str(e)}")
