from datetime import date

from aiogram import BaseMiddleware
from aiogram.types import Message

from bot.database.repositories.user import UserRepository


class LimitsMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        if not isinstance(event, Message) or not event.text:
            return await handler(event, data)

        session = data.get("session")
        if not session:
            return await handler(event, data)

        repo = UserRepository(session)
        user = await repo.get_by_telegram_id(event.from_user.id)

        if not user:
            return await handler(event, data)

        if user.is_premium:
            return await handler(event, data)

        today = date.today()
        if user.last_generation_date != today:
            user.generations_today = 0
            user.last_generation_date = today
            await session.commit()

        if user.generations_today >= user.daily_limit:
            await event.answer(
                "⚠️ Вы достигли дневного лимита генераций "
                f"({user.daily_limit}/день).\n\n"
                "⭐ Купите <b>Премиум</b> для безлимитных генераций!",
                reply_markup=None,
            )
            return None

        return await handler(event, data)
