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


def get_medications_list_keyboard(medications: list, action: str = "delete") -> InlineKeyboardMarkup:
    """Клавиатура со списком лекарств для удаления или редактирования."""
    builder = InlineKeyboardBuilder()
    for medication in medications:
        callback_data = f"{action}_med:{medication.id}"
        builder.add(
            InlineKeyboardButton(
                text=f"💊 {medication.name}",
                callback_data=callback_data
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


def get_edit_fields_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора поля редактирования."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📝 Название", callback_data="edit_field:name"),
        InlineKeyboardButton(text="📋 Описание", callback_data="edit_field:description"),
        InlineKeyboardButton(text="⏰ Время", callback_data="edit_field:time"),
        InlineKeyboardButton(text="💊 Количество", callback_data="edit_field:dose"),
        InlineKeyboardButton(text="📅 Периодичность", callback_data="edit_field:frequency"),
        InlineKeyboardButton(text="📆 Дата окончания", callback_data="edit_field:end_date")
    )
    builder.adjust(2)
    builder.add(InlineKeyboardButton(text="❌ Отменить", callback_data="cancel"))
    return builder.as_markup()


def get_edit_confirmation_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для подтверждения редактирования."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="edit_confirm:yes"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="edit_confirm:no")
    )
    builder.adjust(2)
    return builder.as_markup()


def get_end_date_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора даты окончания."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="📅 Указать дату", callback_data="end_date:specific"),
        InlineKeyboardButton(text="♾️ Бессрочно", callback_data="end_date:never")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_settings_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура настроек."""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(text="🌍 Часовой пояс", callback_data="settings:timezone"),
    )
    builder.adjust(1)
    return builder.as_markup()


def get_timezone_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для выбора часового пояса."""
    builder = InlineKeyboardBuilder()
    
    # Популярные часовые пояса
    timezones = [
        ("UTC", "UTC"),
        ("Москва", "Europe/Moscow"),
        ("Екатеринбург", "Asia/Yekaterinburg"),
    ]
    
    for name, tz in timezones:
        builder.add(
            InlineKeyboardButton(text=f"🌍 {name}", callback_data=f"timezone:{tz}")
        )
    
    builder.add(
        InlineKeyboardButton(text="➕ Другой", callback_data="timezone:custom"),
        InlineKeyboardButton(text="❌ Отменить", callback_data="cancel")
    )
    builder.adjust(1)
    return builder.as_markup()
