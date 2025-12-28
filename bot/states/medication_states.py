"""FSM состояния для добавления лекарства."""
from aiogram.fsm.state import State, StatesGroup


class MedicationStates(StatesGroup):
    """Состояния для процесса добавления лекарства."""
    
    waiting_for_name = State()  # Ожидание названия препарата
    waiting_for_description = State()  # Ожидание описания приема
    waiting_for_frequency = State()  # Выбор периодичности (каждый день / через X дней)
    waiting_for_interval = State()  # Ввод интервала дней (если выбран interval)
    waiting_for_time = State()  # Ввод времени приема
    waiting_for_dose = State()  # Ввод количества таблеток
    waiting_for_confirmation = State()  # Подтверждение всех данных

