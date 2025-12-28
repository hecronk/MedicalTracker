"""Reply клавиатуры для бота."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с основными командами."""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="💊 Добавить лекарство"),
        KeyboardButton(text="📋 Список лекарств"),
        KeyboardButton(text="🗑 Удалить лекарство"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def get_cancel_reply_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура с кнопкой отмены."""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="❌ Отменить"))
    return builder.as_markup(resize_keyboard=True)

