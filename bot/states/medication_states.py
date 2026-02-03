"""FSM состояния для добавления лекарства."""
from aiogram.fsm.state import State, StatesGroup


class MedicationStates(StatesGroup):
    """Состояния для процесса добавления лекарства."""
    
    waiting_for_name = State()  # Ожидание названия препарата
    waiting_for_description = State()  # Ожидание описания приема
    waiting_for_frequency = State()  # Выбор периодичности (каждый день / через X дней)
    waiting_for_interval = State()  # Ввод интервала дней (если выбран interval)
    waiting_for_time = State()  # Ввод времени приема
    waiting_for_dose = State()  # Ввод количества препарата
    waiting_for_end_date = State()  # Ввод даты окончания приема
    waiting_for_confirmation = State()  # Подтверждение всех данных


class EditMedicationStates(StatesGroup):
    """Состояния для процесса редактирования лекарства."""
    
    choosing_medication = State()  # Выбор лекарства для редактирования
    choosing_field = State()  # Выбор поля для редактирования
    waiting_for_new_value = State()  # Ввод нового значения
    edit_confirmation = State()  # Подтверждение изменений


class UserSettingsStates(StatesGroup):
    """Состояния для настроек пользователя."""
    
    waiting_for_timezone = State()  # Ввод часового пояса

