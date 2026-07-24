from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_telegram_id(self, telegram_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> User:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def get_or_create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> tuple[User, bool]:
        user = await self.get_by_telegram_id(telegram_id)
        if user:
            return user, False
        user = await self.create(telegram_id, username, first_name, last_name)
        return user, True

    async def reset_all_limits(self) -> int:
        from sqlalchemy import update
        from datetime import date as date_type

        today = date_type.today()
        result = await self.session.execute(
            update(User)
            .where(User.last_generation_date == today)
            .values(generations_today=0)
        )
        result2 = await self.session.execute(
            update(User)
            .where(User.last_video_generation_date == today)
            .values(video_generations_today=0)
        )
        await self.session.commit()
        return result.rowcount + result2.rowcount
