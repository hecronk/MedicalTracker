# -*- coding: utf-8 -*-
"""Обработчики для редактирования лекарств и настроек пользователя."""
from datetime import datetime, date, time
import pytz
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from bot.states.medication_states import EditMedicationStates, UserSettingsStates
from bot.keyboards.inline import (
    get_medications_list_keyboard,
    get_edit_fields_keyboard,
    get_edit_confirmation_keyboard,
    get_settings_keyboard,
    get_timezone_keyboard,
    get_cancel_keyboard,
    get_frequency_keyboard
)
from bot.keyboards.reply import get_main_menu_keyboard
from bot.utils.validators import validate_time, validate_dose, validate_interval
from database.base import async_session_maker
from services.medication_service import MedicationService
from database.repository import UserRepository

router = Router()


@router.message(Command("edit_medication"))
@router.message(F.text == "✏️ Редактировать лекарство")
async def cmd_edit_medication(message: Message, state: FSMContext):
    """Начать процесс редактирования лекарства."""
    async with async_session_maker() as session:
        service = MedicationService(session)
        medications = await service.get_user_medications(message.from_user.id)
        
        if not medications:
            await message.answer(
                "📋 У вас нет добавленных лекарств.\n\n"
                "Сначала добавьте лекарство командой /add_medication",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        await state.set_state(EditMedicationStates.choosing_medication)
        await message.answer(
            "💊 Выберите лекарство для редактирования:",
            reply_markup=get_medications_list_keyboard(medications, "edit")
        )


@router.callback_query(F.data.startswith("edit_med:"), EditMedicationStates.choosing_medication)
async def choose_medication_to_edit(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора лекарства для редактирования."""
    medication_id = int(callback.data.split(":")[1])
    
    async with async_session_maker() as session:
        service = MedicationService(session)
        medication = await service.get_medication_by_id(medication_id)
        
        if not medication or medication.user_id != callback.from_user.id:
            await callback.message.edit_text("❌ Лекарство не найдено.")
            await callback.answer()
            return
        
        # Сохраняем ID лекарства в состоянии
        await state.update_data(medication_id=medication_id, medication_data={
            'name': medication.name,
            'description': medication.description,
            'schedules': medication.schedules
        })
        
        await state.set_state(EditMedicationStates.choosing_field)
        await callback.message.edit_text(
            f"💊 Выбрано лекарство: {medication.name}\n\n"
            "Что хотите изменить?",
            reply_markup=get_edit_fields_keyboard()
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("edit_field:"), EditMedicationStates.choosing_field)
async def choose_field_to_edit(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора поля для редактирования."""
    field = callback.data.split(":")[1]
    await state.update_data(edit_field=field)
    
    prompts = {
        "name": "📝 Введите новое название препарата:",
        "description": "📋 Введите новое описание приема (или отправьте /skip, чтобы пропустить):",
        "time": "⏰ Введите новое время приема в формате HH:MM (например, 09:00):",
        "dose": "💊 Введите новое количество препарата:",
        "frequency": "📅 Выберите новую периодичность приема:",
        "end_date": "📆 Введите новую дату окончания в формате DD.MM.YYYY или 'бессрочно':"
    }
    
    if field == "frequency":
        from bot.keyboards.inline import get_frequency_keyboard
        await callback.message.edit_text(
            prompts[field],
            reply_markup=get_frequency_keyboard()
        )
    else:
        await callback.message.edit_text(
            prompts[field],
            reply_markup=get_cancel_keyboard()
        )
    
    await state.set_state(EditMedicationStates.waiting_for_new_value)
    await callback.answer()


@router.message(EditMedicationStates.waiting_for_new_value)
async def process_edit_value(message: Message, state: FSMContext):
    """Обработка нового значения для редактирования."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Редактирование отменено.", reply_markup=get_main_menu_keyboard())
        return
    
    data = await state.get_data()
    field = data['edit_field']
    new_value = message.text.strip()
    
    # Валидация в зависимости от поля
    if field == "time":
        is_valid, time_obj, error_msg = validate_time(new_value)
        if not is_valid:
            await message.answer(error_msg + "\n\nПопробуйте снова:")
            return
        new_value = time_obj
    
    elif field == "dose":
        is_valid, dose, error_msg = validate_dose(new_value)
        if not is_valid:
            await message.answer(error_msg + "\n\nПопробуйте снова:")
            return
        new_value = dose
    
    elif field == "frequency":
        # Обработка частоты через callback
        return
    
    elif field == "end_date":
        if new_value.lower() == "бессрочно":
            new_value = None
        else:
            try:
                new_value = datetime.strptime(new_value, "%d.%m.%Y").date()
                today = date.today()
                if new_value < today:
                    await message.answer("❌ Дата окончания не может быть в прошлом. Попробуйте снова:")
                    return
            except ValueError:
                await message.answer("❌ Неверный формат даты. Используйте DD.MM.YYYY или 'бессрочно':")
                return
    
    elif field == "description" and new_value == "/skip":
        new_value = None
    
    # Сохраняем новое значение
    await state.update_data(new_value=new_value)
    await show_edit_confirmation(message, state)


@router.callback_query(F.data.startswith("frequency:"), EditMedicationStates.waiting_for_new_value)
async def process_edit_frequency(callback: CallbackQuery, state: FSMContext):
    """Обработка изменения периодичности."""
    frequency_type = callback.data.split(":")[1]
    
    if frequency_type == "interval":
        await callback.message.edit_text(
            "📅 Введите новый интервал в днях:",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await state.update_data(new_value=frequency_type)
        await show_edit_confirmation(callback, state)
    
    await callback.answer()


@router.message(EditMedicationStates.waiting_for_new_value, F.text.regexp(r'^\d+$'))
async def process_edit_interval(message: Message, state: FSMContext):
    """Обработка изменения интервала дней."""
    data = await state.get_data()
    
    if data.get('edit_field') == 'frequency':
        is_valid, interval, error_msg = validate_interval(message.text)
        if not is_valid:
            await message.answer(error_msg + "\n\nПопробуйте снова:")
            return
        
        await state.update_data(new_value=('interval', interval))
        await show_edit_confirmation(message, state)


async def show_edit_confirmation(message_or_callback, state: FSMContext):
    """Показать подтверждение редактирования."""
    data = await state.get_data()
    field = data['edit_field']
    new_value = data['new_value']
    
    # Формируем текст для отображения нового значения
    display_values = {
        "name": new_value,
        "description": new_value or "Без описания",
        "time": new_value.strftime("%H:%M") if isinstance(new_value, time) else str(new_value),
        "dose": str(new_value),
        "frequency": "Каждый день" if new_value == "daily" else f"Через каждые {new_value[1]} дней" if isinstance(new_value, tuple) else str(new_value),
        "end_date": "Бессрочно" if new_value is None else new_value.strftime("%d.%m.%Y")
    }
    
    field_names = {
        "name": "Название",
        "description": "Описание",
        "time": "Время приема",
        "dose": "Количество",
        "frequency": "Периодичность",
        "end_date": "Дата окончания"
    }
    
    confirmation_text = (
        f"📋 Подтвердите изменение:\n\n"
        f"🔧 {field_names[field]}: {display_values[field]}\n\n"
        "Сохранить изменения?"
    )
    
    await state.set_state(EditMedicationStates.edit_confirmation)
    
    if hasattr(message_or_callback, 'message'):  # CallbackQuery
        await message_or_callback.message.edit_text(
            confirmation_text,
            reply_markup=get_edit_confirmation_keyboard()
        )
    else:  # Message
        await message_or_callback.answer(
            confirmation_text,
            reply_markup=get_edit_confirmation_keyboard()
        )


@router.callback_query(F.data == "edit_confirm:yes", EditMedicationStates.edit_confirmation)
async def confirm_edit(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и сохранение изменений."""
    data = await state.get_data()
    
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            medication = await service.get_medication_by_id(data['medication_id'])
            
            if not medication or medication.user_id != callback.from_user.id:
                await callback.message.edit_text("❌ Лекарство не найдено.")
                await callback.answer()
                return
            
            field = data['edit_field']
            new_value = data['new_value']
            
            # Применяем изменения
            if field == "name":
                medication.name = new_value
            elif field == "description":
                medication.description = new_value
            elif field in ["time", "dose", "frequency", "end_date"]:
                # Обновляем расписание
                if medication.schedules:
                    schedule = medication.schedules[0]  # Берем первое расписание
                    
                    if field == "time":
                        schedule.time = new_value
                    elif field == "dose":
                        schedule.dose = new_value
                    elif field == "frequency":
                        if isinstance(new_value, tuple):
                            schedule.frequency_type = new_value[0]
                            schedule.interval_days = new_value[1]
                        else:
                            schedule.frequency_type = new_value
                            schedule.interval_days = None
                    elif field == "end_date":
                        schedule.end_date = new_value
            
            await session.commit()
            
            await state.clear()
            await callback.message.edit_text(
                "✅ Изменения успешно сохранены!\n\n"
                f"💊 {medication.name}\n"
                "Данные обновлены."
            )
            await callback.answer("✅ Сохранено!")
    
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Произошла ошибка при сохранении: {str(e)}"
        )
        await callback.answer("❌ Ошибка")
        await state.clear()


@router.callback_query(F.data == "edit_confirm:no", EditMedicationStates.edit_confirmation)
async def cancel_edit(callback: CallbackQuery, state: FSMContext):
    """Отмена редактирования."""
    await state.clear()
    await callback.message.edit_text("❌ Редактирование отменено.")
    await callback.answer("Отменено")


# Настройки пользователя
@router.message(Command("settings"))
@router.message(F.text == "⚙️ Настройки")
async def cmd_settings(message: Message, state: FSMContext):
    """Открыть настройки."""
    await message.answer(
        "⚙️ Настройки профиля:",
        reply_markup=get_settings_keyboard()
    )


@router.callback_query(F.data == "settings:timezone")
async def settings_timezone(callback: CallbackQuery, state: FSMContext):
    """Настройки часового пояса."""
    async with async_session_maker() as session:
        user_repo = UserRepository(session)
        db_user = await user_repo.get_by_id(callback.from_user.id)
        current_timezone = db_user.timezone if db_user else 'UTC'
    
    await callback.message.edit_text(
        f"🌍 Текущий часовой пояс: {current_timezone}\n\n"
        "Выберите новый часовой пояс:",
        reply_markup=get_timezone_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("timezone:"))
async def process_timezone_choice(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора часового пояса."""
    timezone_choice = callback.data.split(":")[1]
    
    if timezone_choice == "custom":
        await callback.message.edit_text(
            "🌍 Введите ваш часовой пояс (например, Europe/Moscow, America/New_York):",
            reply_markup=get_cancel_keyboard()
        )
        await state.set_state(UserSettingsStates.waiting_for_timezone)
    else:
        # Сохраняем выбранный часовой пояс
        await save_timezone(callback.from_user.id, timezone_choice)
        await callback.message.edit_text(
            f"✅ Часовой пояс изменен на: {timezone_choice}",
            reply_markup=get_settings_keyboard()
        )

@router.message(UserSettingsStates.waiting_for_timezone)
async def process_custom_timezone(message: Message, state: FSMContext):
    """Обработка ввода кастомного часового пояса."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Операция отменена.", reply_markup=get_settings_keyboard())
        return
    
    timezone_str = message.text.strip()
    
    # Проверяем валидность часового пояса
    try:
        pytz.timezone(timezone_str)
        await save_timezone(message.from_user.id, timezone_str)
        await state.clear()
        await message.answer(
            f"✅ Часовой пояс изменен на: {timezone_str}",
            reply_markup=get_settings_keyboard()
        )
    except Exception:
        await message.answer(
            "❌ Неверный часовой пояс. Попробуйте снова (например, Europe/Moscow):",
            reply_markup=get_cancel_keyboard()
        )


async def save_timezone(user_id: int, timezone: str) -> bool:
    """Сохранение часового пояса пользователя."""
    try:
        async with async_session_maker() as session:
            user_repo = UserRepository(session)
            return await user_repo.update_timezone(user_id, timezone)
    except Exception:
        return False


@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена текущей операции."""
    current_state = await state.get_state()
    await state.clear()
    
    if current_state and "Settings" in current_state:
        await callback.message.edit_text("❌ Операция отменена.", reply_markup=get_settings_keyboard())
