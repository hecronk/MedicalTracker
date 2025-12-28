"""Обработчики для добавления лекарств."""
from datetime import date, time
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from sqlalchemy.ext.asyncio import AsyncSession

from bot.states.medication_states import MedicationStates
from bot.keyboards.inline import (
    get_frequency_keyboard,
    get_confirmation_keyboard,
    get_cancel_keyboard
)
from bot.keyboards.reply import get_cancel_reply_keyboard
from bot.utils.validators import validate_time, validate_dose, validate_interval
from database.base import async_session_maker
from services.medication_service import MedicationService

router = Router()


@router.message(Command("add_medication"))
@router.message(F.text == "💊 Добавить лекарство")
async def cmd_add_medication(message: Message, state: FSMContext):
    """Начать процесс добавления лекарства."""
    await state.set_state(MedicationStates.waiting_for_name)
    await message.answer(
        "💊 Давайте добавим новое лекарство!\n\n"
        "📝 Введите название препарата:",
        reply_markup=get_cancel_reply_keyboard()
    )


@router.message(MedicationStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    """Обработка названия препарата."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название не может быть пустым. Попробуйте снова:")
        return
    
    await state.update_data(name=name)
    await state.set_state(MedicationStates.waiting_for_description)
    await message.answer(
        "📋 Введите описание приема (или отправьте /skip, чтобы пропустить):",
        reply_markup=get_cancel_reply_keyboard()
    )


@router.message(MedicationStates.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    """Обработка описания приема."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    description = None
    if message.text and message.text.strip() != "/skip":
        description = message.text.strip()
    
    await state.update_data(description=description)
    await state.set_state(MedicationStates.waiting_for_frequency)
    await message.answer(
        "⏰ Выберите периодичность приема:",
        reply_markup=get_frequency_keyboard()
    )


@router.callback_query(F.data.startswith("frequency:"), MedicationStates.waiting_for_frequency)
async def process_frequency(callback: CallbackQuery, state: FSMContext):
    """Обработка выбора периодичности."""
    frequency_type = callback.data.split(":")[1]
    await state.update_data(frequency_type=frequency_type)
    
    if frequency_type == "interval":
        await state.set_state(MedicationStates.waiting_for_interval)
        await callback.message.edit_text(
            "📅 Введите интервал в днях (например, 2 для приема через каждые 2 дня):",
            reply_markup=get_cancel_keyboard()
        )
    else:
        await state.set_state(MedicationStates.waiting_for_time)
        await callback.message.edit_text(
            "⏰ Введите время приема в формате HH:MM (например, 09:00):",
            reply_markup=get_cancel_keyboard()
        )
    
    await callback.answer()


@router.message(MedicationStates.waiting_for_interval)
async def process_interval(message: Message, state: FSMContext):
    """Обработка интервала дней."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    is_valid, interval, error_msg = validate_interval(message.text)
    if not is_valid:
        await message.answer(error_msg + "\n\nПопробуйте снова:")
        return
    
    await state.update_data(interval_days=interval)
    await state.set_state(MedicationStates.waiting_for_time)
    await message.answer(
        "⏰ Введите время приема в формате HH:MM (например, 09:00):",
        reply_markup=get_cancel_reply_keyboard()
    )


@router.message(MedicationStates.waiting_for_time)
async def process_time(message: Message, state: FSMContext):
    """Обработка времени приема."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    is_valid, time_obj, error_msg = validate_time(message.text)
    if not is_valid:
        await message.answer(error_msg + "\n\nПопробуйте снова:")
        return
    
    await state.update_data(time=time_obj)
    await state.set_state(MedicationStates.waiting_for_dose)
    await message.answer(
        "💊 Сколько таблеток нужно принять?",
        reply_markup=get_cancel_reply_keyboard()
    )


@router.message(MedicationStates.waiting_for_dose)
async def process_dose(message: Message, state: FSMContext):
    """Обработка количества таблеток."""
    if message.text == "❌ Отменить":
        await state.clear()
        await message.answer("❌ Операция отменена.")
        return
    
    is_valid, dose, error_msg = validate_dose(message.text)
    if not is_valid:
        await message.answer(error_msg + "\n\nПопробуйте снова:")
        return
    
    await state.update_data(dose=dose)
    
    # Получаем все данные
    data = await state.get_data()
    
    # Формируем текст для подтверждения
    frequency_text = "Каждый день" if data['frequency_type'] == 'daily' else f"Через каждые {data.get('interval_days', 'N/A')} дней"
    time_str = data['time'].strftime("%H:%M")
    description_text = data.get('description') or "Не указано"
    
    confirmation_text = (
        "📋 Проверьте введенные данные:\n\n"
        f"💊 Название: {data['name']}\n"
        f"📝 Описание: {description_text}\n"
        f"⏰ Периодичность: {frequency_text}\n"
        f"🕐 Время приема: {time_str}\n"
        f"💊 Количество таблеток: {data['dose']}\n\n"
        "Подтвердите добавление:"
    )
    
    await state.set_state(MedicationStates.waiting_for_confirmation)
    await message.answer(
        confirmation_text,
        reply_markup=get_confirmation_keyboard()
    )


@router.callback_query(F.data == "confirm:yes", MedicationStates.waiting_for_confirmation)
async def confirm_medication(callback: CallbackQuery, state: FSMContext):
    """Подтверждение и сохранение лекарства."""
    data = await state.get_data()
    
    try:
        async with async_session_maker() as session:
            service = MedicationService(session)
            
            medication, schedule = await service.add_medication(
                user_id=callback.from_user.id,
                name=data['name'],
                description=data.get('description'),
                frequency_type=data['frequency_type'],
                dose=data['dose'],
                time=data['time'],
                start_date=date.today(),
                interval_days=data.get('interval_days'),
                end_date=None  # Бессрочно
            )
        
        await state.clear()
        await callback.message.edit_text(
            "✅ Лекарство успешно добавлено!\n\n"
            f"💊 {medication.name}\n"
            f"⏰ Время приема: {schedule.time.strftime('%H:%M')}\n"
            f"💊 Количество: {schedule.dose} таблеток\n\n"
            "Я буду напоминать вам о приеме в установленное время."
        )
        await callback.answer("✅ Лекарство добавлено!")
    
    except Exception as e:
        await callback.message.edit_text(
            f"❌ Произошла ошибка при сохранении: {str(e)}\n\n"
            "Попробуйте снова позже."
        )
        await callback.answer("❌ Ошибка")
        await state.clear()


@router.callback_query(F.data == "confirm:no", MedicationStates.waiting_for_confirmation)
async def cancel_medication(callback: CallbackQuery, state: FSMContext):
    """Отмена добавления лекарства."""
    await state.clear()
    await callback.message.edit_text("❌ Добавление лекарства отменено.")
    await callback.answer("Отменено")


@router.callback_query(F.data == "cancel")
async def cancel_operation(callback: CallbackQuery, state: FSMContext):
    """Отмена операции."""
    await state.clear()
    await callback.message.edit_text("❌ Операция отменена.")
    await callback.answer("Отменено")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext):
    """Отмена текущей операции."""
    current_state = await state.get_state()
    if current_state is None:
        await message.answer("Нет активных операций для отмены.")
        return
    
    await state.clear()
    await message.answer("❌ Операция отменена.")

