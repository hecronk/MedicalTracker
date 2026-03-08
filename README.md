# Medical Tracker - Telegram бот для отслеживания приема лекарств

Специализированный Telegram-бот для управления приемом лекарств. Заменяет приложение Medisafe и предоставляет удобный интерфейс для отслеживания расписания приема препаратов.

## Возможности

- 💊 Добавление лекарств с описанием приема
- ⏰ Настройка расписания (каждый день или через X дней)
- 🔔 Автоматические напоминания в установленное время
- 🌍 Поддержка часовых поясов
- 🔄 Гарантированная доставка уведомлений с системой повторных попыток
- 📋 Просмотр списка всех лекарств
- 🗑 Удаление лекарств

## Технологический стек

- **Python 3.10+**
- **aiogram 3.x** - асинхронный фреймворк для Telegram ботов
- **PostgreSQL** - база данных
- **SQLAlchemy (async)** - ORM
- **Alembic** - миграции базы данных
- **pydantic-settings** - типобезопасная конфигурация из переменных окружения
- **APScheduler** - планировщик задач
- **pytz** - работа с часовыми поясами

## Установка

### 1. Клонирование репозитория

```bash
git clone <repository_url>
cd MedicalTracker
```

### 2. Установка зависимостей

Проект использует Poetry для управления зависимостями:

```bash
poetry install
```

Или установите зависимости вручную:

```bash
pip install aiogram asyncpg sqlalchemy[asyncio] alembic apscheduler python-dotenv pytz pydantic-settings psycopg2-binary
```

### 3. Настройка базы данных

1. Убедитесь, что PostgreSQL запущен
2. Создайте базу данных:

```sql
CREATE DATABASE medical-tracker;
```

### 4. Настройка переменных окружения

Создайте файл `.env` в корне проекта:

```env
# Telegram Bot Token
BOT_TOKEN=your_bot_token_here

# PostgreSQL Database Configuration
DB_HOST=localhost
DB_PORT=5432
DB_USER=postgres
DB_PASSWORD=your_password_here
DB_NAME=medical-tracker

# Scheduler Timezone
SCHEDULER_TIMEZONE=UTC

# Retry Configuration
MAX_RETRY_ATTEMPTS=5

# Set to true to log SQL queries (useful for debugging)
DB_ECHO=false
```

### 5. Применение миграций базы данных

Используйте Alembic для создания таблиц и управления схемой:

```bash
# Применить все миграции (создать таблицы)
alembic upgrade head

# Создать новую миграцию после изменения моделей
alembic revision --autogenerate -m "описание изменения"

# Откатить последнюю миграцию
alembic downgrade -1
```

Для быстрой проверки подключения и применения миграций:

```bash
poetry run python -m database.init_db
```

## Запуск

```bash
poetry run python main.py
```

## Использование

### Команды бота

- `/start` - Начать работу с ботом
- `/add_medication` - Добавить новое лекарство
- `/list_medications` - Показать список всех лекарств
- `/delete_medication` - Удалить лекарство
- `/help` - Справка по использованию
- `/cancel` - Отменить текущую операцию

### Процесс добавления лекарства

1. Используйте команду `/add_medication`
2. Введите название препарата
3. Введите описание приема (или пропустите)
4. Выберите периодичность (каждый день или через X дней)
5. Если выбрано "через X дней", введите интервал
6. Введите время приема в формате HH:MM (например, 09:00)
7. Введите количество препарата
8. Подтвердите добавление

### Система уведомлений

- Бот проверяет расписания
- Уведомления отправляются в установленное время с учетом часового пояса пользователя
- При ошибке отправки система автоматически повторяет попытку:
  - 1-я попытка: через 5 минут
  - 2-я попытка: через 15 минут
  - 3-я попытка: через 30 минут
  - 4-я попытка: через 1 час
  - 5-я попытка: через 2 часа
- Максимум 5 попыток доставки

## Структура проекта

```
MedicalTracker/
├── main.py                    # Точка входа
├── config.py                  # Конфигурация (pydantic-settings)
├── alembic.ini                # Конфигурация Alembic
├── alembic/                   # Миграции базы данных
│   ├── env.py                 # Окружение Alembic (async-aware)
│   ├── script.py.mako         # Шаблон миграций
│   └── versions/              # Файлы миграций
│       └── 0001_initial_schema.py
├── bot/                       # Код бота
│   ├── handlers/              # Обработчики команд
│   ├── keyboards/             # Клавиатуры
│   ├── middlewares/           # Middleware
│   ├── states/                # FSM состояния
│   └── utils/                 # Утилиты
├── database/                  # Работа с БД
│   ├── models.py              # SQLAlchemy модели
│   ├── base.py                # Базовые классы
│   ├── repository.py          # Репозитории
│   └── init_db.py             # Применение миграций через Alembic
├── services/                  # Бизнес-логика
│   ├── medication_service.py
│   └── notification_service.py
└── scheduler/                 # Планировщик задач
    └── notification_scheduler.py
```

## Получение токена бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям для создания бота
4. Скопируйте полученный токен в файл `.env`

## Разработка

### Запуск в режиме разработки

Для отладки можно изменить уровень логирования в `main.py`:

```python
logging.basicConfig(
    level=logging.DEBUG,  # Изменить на DEBUG для подробных логов
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

## Лицензия

MIT

## Автор

damir (1damiraminov@gmail.com)

