from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

import logging

logger = logging.getLogger(__name__)


class DebugMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        from aiogram.types import Message
        if isinstance(event, Message) and event.text:
            logger.info("DEBUG MIDDLEWARE: text=%s user=%s", event.text, event.from_user.id if event.from_user else None)
        return await handler(event, data)