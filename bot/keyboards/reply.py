"""Reply клавиатуры для бота."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder


def get_main_menu_keyboard() -> ReplyKeyboardMarkup:
    """Главное меню с основными командами."""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="💊 Добавить лекарство"),
        KeyboardButton(text="📋 Список лекарств"),
        KeyboardButton(text="📅 План приема"),
        KeyboardButton(text="📅 Быстрый план"),
        KeyboardButton(text="✏️ Редактировать лекарство"),
        KeyboardButton(text="📊 Статистика"),
        KeyboardButton(text="📅 История"),
        KeyboardButton(text="🗑 Удалить лекарство"),
        KeyboardButton(text="⚙️ Настройки"),
        KeyboardButton(text="ℹ️ Помощь")
    )
    builder.adjust(3, 3, 2, 2)
    return builder.as_markup(resize_keyboard=True)
