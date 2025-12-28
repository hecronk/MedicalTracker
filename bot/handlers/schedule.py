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
                    text += f"   ⏰ {time_str} - {schedule.dose} таблеток ({frequency_text})\n"
            
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

