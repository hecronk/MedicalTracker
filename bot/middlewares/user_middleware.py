"""Middleware для автоматического создания пользователей."""
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser
from sqlalchemy.ext.asyncio import AsyncSession

from database.base import async_session_maker
from database.repository import UserRepository


class UserMiddleware(BaseMiddleware):
    """Middleware для автоматического создания/обновления пользователя в БД."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события."""
        # Получаем пользователя из события
        user: TelegramUser | None = data.get("event_from_user")
        
        if user:
            # Создаем сессию БД
            async with async_session_maker() as session:
                user_repo = UserRepository(session)
                
                # Проверяем, существует ли пользователь
                db_user = await user_repo.get_by_id(user.id)
                
                if not db_user:
                    # Создаем нового пользователя
                    db_user = await user_repo.create(
                        user_id=user.id,
                        username=user.username,
                        first_name=user.first_name,
                        timezone='UTC'  # По умолчанию UTC, можно будет изменить позже
                    )
                else:
                    # Обновляем информацию о пользователе, если изменилась
                    if db_user.username != user.username or db_user.first_name != user.first_name:
                        # Можно добавить метод update в репозиторий, но пока пропустим
                        pass
                
                # Сохраняем пользователя в data для использования в handlers
                data["db_user"] = db_user
        
        return await handler(event, data)

