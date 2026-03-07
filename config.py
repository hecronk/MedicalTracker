"""Конфигурация приложения."""
from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    """Класс конфигурации приложения, загружаемый из переменных окружения."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Telegram Bot Token
    bot_token: str = Field(..., validation_alias="BOT_TOKEN")

    # PostgreSQL настройки
    db_host: str = Field("localhost", validation_alias="DB_HOST")
    db_port: int = Field(5432, validation_alias="DB_PORT")
    db_user: str = Field("postgres", validation_alias="DB_USER")
    db_password: str = Field("", validation_alias="DB_PASSWORD")
    db_name: str = Field("medicaltracker", validation_alias="DB_NAME")

    @computed_field  # type: ignore[misc]
    @property
    def database_url(self) -> str:
        """Возвращает URL для подключения к PostgreSQL."""
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def sync_database_url(self) -> str:
        """Возвращает синхронный URL для подключения к PostgreSQL (используется Alembic)."""
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    # Настройки планировщика
    scheduler_timezone: str = Field("UTC", validation_alias="SCHEDULER_TIMEZONE")

    # Настройки повторных попыток
    max_retry_attempts: int = Field(5, validation_alias="MAX_RETRY_ATTEMPTS")
    retry_intervals: list[int] = [5, 15, 30, 60, 120]  # минуты

    # Настройки логирования БД
    db_echo: bool = Field(False, validation_alias="DB_ECHO")


config = Config()

