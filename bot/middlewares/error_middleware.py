"""Middleware для обработки ошибок."""
import logging
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, ErrorEvent

logger = logging.getLogger(__name__)


class ErrorMiddleware(BaseMiddleware):
    """Middleware для глобальной обработки ошибок."""
    
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        """Обработка события с перехватом ошибок."""
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(f"Ошибка при обработке события: {e}", exc_info=True)
            
            # Если это сообщение, пытаемся отправить пользователю сообщение об ошибке
            if hasattr(event, 'answer'):
                try:
                    await event.answer(
                        "❌ Произошла непредвиденная ошибка. "
                        "Попробуйте позже или обратитесь в поддержку."
                    )
                except:
                    pass  # Если не удалось отправить сообщение, просто логируем
            
            # Пробрасываем ошибку дальше для логирования
            raise

