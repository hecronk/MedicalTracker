"""Конфигурация приложения."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
env_path = Path(__file__).parent / '.env'
load_dotenv(dotenv_path=env_path)


class Config:
    """Класс конфигурации приложения."""
    
    # Telegram Bot Token
    BOT_TOKEN: str = os.getenv('BOT_TOKEN', '')
    
    # PostgreSQL настройки
    DB_HOST: str = os.getenv('DB_HOST', 'localhost')
    DB_PORT: int = int(os.getenv('DB_PORT', '5432'))
    DB_USER: str = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD: str = os.getenv('DB_PASSWORD', '')
    DB_NAME: str = os.getenv('DB_NAME', 'medicaltracker')
    
    @property
    def database_url(self) -> str:
        """Возвращает URL для подключения к PostgreSQL."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    # Настройки планировщика
    SCHEDULER_TIMEZONE: str = os.getenv('SCHEDULER_TIMEZONE', 'UTC')
    
    # Настройки повторных попыток
    MAX_RETRY_ATTEMPTS: int = int(os.getenv('MAX_RETRY_ATTEMPTS', '5'))
    RETRY_INTERVALS: list[int] = [5, 15, 30, 60, 120]  # минуты


config = Config()

