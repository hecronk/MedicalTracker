"""Inline клавиатуры для бота."""
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def get_frequency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора периодичности приема."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📅 Каждый день", callback_data="frequency:daily"),
        InlineKeyboardButton(text="⏰ Через X дней", callback_data="frequency:interval")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения добавления лекарства."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Подтвердить", callback_data="confirm:yes"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="confirm:no")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_cancel_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для отмены операции."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
    )
    return builder.as_markup()


def get_medications_list_keyboard(medications: list) -> InlineKeyboardMarkup:
    """Клавиатура со списком лекарств для удаления."""
    builder = InlineKeyboardBuilder()
    for medication in medications:
        builder.add(
            InlineKeyboardButton(
                text=f"💊 {medication.name}",
                callback_data=f"delete_med:{medication.id}"
            )
        )
    builder.adjust(1)
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    return builder.as_markup()


def get_delete_confirmation_keyboard(medication_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения удаления лекарства."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="✅ Да, удалить",
            callback_data=f"delete_confirm:{medication_id}"
        ),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel_delete")
    )
    builder.adjust(2)
    return builder.as_markup()

