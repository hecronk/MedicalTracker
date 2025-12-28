"""Валидаторы для ввода данных."""
from datetime import time
from typing import Tuple


def validate_time(time_str: str) -> Tuple[bool, time | None, str]:
    """
    Валидация времени в формате HH:MM.
    
    Returns:
        Tuple[bool, time | None, str]: (успех, объект time, сообщение об ошибке)
    """
    try:
        parts = time_str.strip().split(':')
        if len(parts) != 2:
            return False, None, "❌ Неверный формат времени. Используйте HH:MM (например, 09:00)"
        
        hour = int(parts[0])
        minute = int(parts[1])
        
        if not (0 <= hour <= 23):
            return False, None, "❌ Часы должны быть от 0 до 23"
        
        if not (0 <= minute <= 59):
            return False, None, "❌ Минуты должны быть от 0 до 59"
        
        time_obj = time(hour=hour, minute=minute)
        return True, time_obj, ""
    
    except ValueError:
        return False, None, "❌ Неверный формат времени. Используйте HH:MM (например, 09:00)"


def validate_dose(dose_str: str) -> Tuple[bool, float | None, str]:
    """
    Валидация количества таблеток.
    
    Returns:
        Tuple[bool, int | None, str]: (успех, количество, сообщение об ошибке)
    """
    try:
        dose = float(dose_str.strip())
        if dose <= 0:
            return False, None, "❌ Количество таблеток должно быть положительным числом"
        if dose > 100:
            return False, None, "❌ Количество таблеток не может быть больше 100"
        return True, dose, ""
    
    except ValueError:
        return False, None, "❌ Введите число (например, 0.5, 1, 1.5, 2, 3)"


def validate_interval(interval_str: str) -> Tuple[bool, int | None, str]:
    """
    Валидация интервала дней.
    
    Returns:
        Tuple[bool, int | None, str]: (успех, интервал, сообщение об ошибке)
    """
    try:
        interval = int(interval_str.strip())
        if interval <= 0:
            return False, None, "❌ Интервал должен быть положительным числом"
        if interval > 365:
            return False, None, "❌ Интервал не может быть больше 365 дней"
        return True, interval, ""
    
    except ValueError:
        return False, None, "❌ Введите число дней (например, 2, 3, 7)"

