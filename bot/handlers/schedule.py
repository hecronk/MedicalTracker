# -*- coding: utf-8 -*-
"""Обработчики для управления лекарствами."""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from sqlalchemy.ext.asyncio import AsyncSession

from bot.keyboards.inline import (
    get_medications_list_keyboard,
    get_delete_confirmation_keyboard
)
from database.base import async_session_maker
from services.medication_service import MedicationService

router = Router()


@router.message(Command("list_medications"))
@router.message(F.text == "📋 Список лекарств")
async def cmd_list_medications(message: Message, db_user):
    """Показать список всех лекарств пользователя."""
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            medications = await service.get_user_medications(db_user.id, active_only=True)
        
        if not medications:
            await message.answer(
                "📋 У вас пока нет добавленных лекарств.\n\n"
                "Используйте /add_medication, чтобы добавить первое лекарство."
            )
            return
        
        text = "📋 Ваши лекарства:\n\n"
        
        for idx, medication in enumerate(medications, 1):
            text += f"{idx}. 💊 {medication.name}\n"
            
            if medication.description:
                text += f"   📝 {medication.description}\n"
            
            # Показываем расписания
            if medication.schedules:
                for schedule in medication.schedules:
                    time_str = schedule.time.strftime("%H:%M")
                    frequency_text = "каждый день" if schedule.frequency_type == 'daily' else f"через каждые {schedule.interval_days} дней"
                    
                    text += f"   ⏰ {time_str} - {schedule.dose} препарата\n"
                    text += f"   📅 {frequency_text}\n"
                    
                    # Добавляем дату окончания приема
                    if schedule.end_date:
                        text += f"   📅 Дата окончания приема: {schedule.end_date.strftime('%d.%m.%Y')}\n"
                    else:
                        text += f"   📅 Дата окончания приема: бессрочно\n"
            
            text += "\n"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при получении списка лекарств: {str(e)}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )


@router.message(Command("delete_medication"))
@router.message(F.text == "🗑 Удалить лекарство")
async def cmd_delete_medication(message: Message, db_user):
    """Начать процесс удаления лекарства."""
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            medications = await service.get_user_medications(db_user.id, active_only=True)
        
        if not medications:
            await message.answer(
                "📋 У вас нет лекарств для удаления.\n\n"
                "Используйте /add_medication, чтобы добавить лекарство."
            )
            return
        
        await message.answer(
            "🗑 Выберите лекарство для удаления:",
            reply_markup=get_medications_list_keyboard(medications)
        )
    
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка: {str(e)}\n\n"
            "Попробуйте позже."
        )


@router.callback_query(F.data.startswith("delete_med:"))
async def select_medication_to_delete(callback: CallbackQuery):
    """Обработка выбора лекарства для удаления."""
    try:
        medication_id = int(callback.data.split(":")[1])
        
        async with async_session_maker() as session:
            service = MedicationService(session)
            medication = await service.get_medication_by_id(medication_id)
        
        if not medication:
            await callback.message.edit_text("❌ Лекарство не найдено.")
            await callback.answer("Лекарство не найдено")
            return
        
        await callback.message.edit_text(
            f"⚠️ Вы уверены, что хотите удалить лекарство?\n\n"
            f"💊 {medication.name}\n\n"
            "Это действие нельзя отменить.",
            reply_markup=get_delete_confirmation_keyboard(medication_id)
        )
        await callback.answer()
    
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Произошла ошибка: {str(e)}"
        )
        await callback.answer("Ошибка")


@router.callback_query(F.data.startswith("delete_confirm:"))
async def confirm_delete_medication(callback: CallbackQuery, db_user):
    """Подтверждение и удаление лекарства."""
    try:
        medication_id = int(callback.data.split(":")[1])
        
        # Проверяем, что лекарство принадлежит пользователю
        async with async_session_maker() as session:
            service = MedicationService(session)
            medication = await service.get_medication_by_id(medication_id)
        
        if not medication:
            await callback.message.edit_text("❌ Лекарство не найдено.")
            await callback.answer("Лекарство не найдено")
            return
        
        if medication.user_id != db_user.id:
            await callback.message.edit_text("❌ У вас нет прав для удаления этого лекарства.")
            await callback.answer("Нет прав")
            return
        
        # Удаляем лекарство
        async with async_session_maker() as session:
            service = MedicationService(session)
            success = await service.delete_medication(medication_id)
        
        if success:
            await callback.message.edit_text(
                f"✅ Лекарство '{medication.name}' успешно удалено."
            )
            await callback.answer("✅ Удалено")
        else:
            await callback.message.edit_text("❌ Не удалось удалить лекарство.")
            await callback.answer("Ошибка")
    
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Произошла ошибка при удалении: {str(e)}"
        )
        await callback.answer("Ошибка")


@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: CallbackQuery):
    """Отмена удаления."""
    await callback.message.edit_text("❌ Удаление отменено.")
    await callback.answer("Отменено")


@router.message(Command("schedule"))
@router.message(F.text == "📅 План приема")
async def cmd_schedule(message: Message, db_user):
    """Показать план приема лекарств на ближайшие дни."""
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            medications = await service.get_user_medications(db_user.id, active_only=True)
        
        if not medications:
            await message.answer(
                "📋 У вас пока нет добавленных лекарств.\n\n"
                "Используйте /add_medication, чтобы добавить первое лекарство."
            )
            return
        
        from datetime import date, datetime, timedelta
        import pytz
        
        # Получаем текущую дату в часовом поясе пользователя
        user_tz = pytz.timezone(db_user.timezone)
        now_utc = datetime.now(pytz.UTC)
        now_user_tz = now_utc.astimezone(user_tz)
        today = now_user_tz.date()
        
        text = f"📅 План приема лекарств (часовой пояс: {db_user.timezone}):\n\n"
        
        # Показываем план на 7 дней вперед
        for days_ahead in range(7):
            check_date = today + timedelta(days=days_ahead)
            date_str = check_date.strftime("%d.%m.%Y")
            day_name = ["Сегодня", "Завтра", "Послезавтра"][min(days_ahead, 2)] if days_ahead < 3 else ""
            
            if day_name:
                text += f"🗓️ {day_name} ({date_str}):\n"
            else:
                text += f"🗓️ {date_str}:\n"
            
            has_medications = False
            
            for medication in medications:
                for schedule in medication.schedules:
                    # Проверяем нужно ли принимать лекарство в этот день
                    if _should_take_medication(schedule, check_date):
                        time_str = schedule.time.strftime("%H:%M")
                        text += f"   💊 {time_str} - {medication.name} ({schedule.dose} препарата)\n"
                        has_medications = True
            
            if not has_medications:
                text += "   ✅ Нет приемов\n"
            
            text += "\n"
        
        await message.answer(text)
    
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при получении плана: {str(e)}\n\n"
            "Попробуйте позже или обратитесь в поддержку."
        )


def _should_take_medication(schedule, check_date):
    """Проверить нужно ли принимать лекарство в указанную дату."""
    # Проверяем дату окончания
    if schedule.end_date and check_date > schedule.end_date:
        return False
    
    # Проверяем дату начала
    if check_date < schedule.start_date:
        return False
    
    # Проверяем периодичность
    if schedule.frequency_type == 'daily':
        return True
    
    if schedule.frequency_type == 'interval' and schedule.interval_days:
        days_since_start = (check_date - schedule.start_date).days
        return days_since_start >= 0 and days_since_start % schedule.interval_days == 0
    
    return False

