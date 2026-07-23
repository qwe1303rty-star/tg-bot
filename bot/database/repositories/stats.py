from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.generation import Generation
from bot.models.user import User


class StatsRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def count_total_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def count_new_users(self, days: int = 1) -> int:
        since = datetime.now() - timedelta(days=days)
        result = await self.session.execute(
            select(func.count(User.id)).where(User.created_at >= since)
        )
        return result.scalar_one()

    async def count_total_generations(self) -> int:
        result = await self.session.execute(select(func.count(Generation.id)))
        return result.scalar_one()

    async def count_generations_today(self) -> int:
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        result = await self.session.execute(
            select(func.count(Generation.id)).where(Generation.created_at >= today)
        )
        return result.scalar_one()

    async def count_video_generations(self) -> int:
        result = await self.session.execute(
            select(func.count(Generation.id)).where(
                Generation.prompt.like("[VIDEO]%")
            )
        )
        return result.scalar_one()

    async def count_by_provider(self) -> list[tuple[str, int]]:
        result = await self.session.execute(
            select(Generation.provider, func.count(Generation.id))
            .group_by(Generation.provider)
            .order_by(func.count(Generation.id).desc())
        )
        return list(result.all())

    async def get_all_users(
        self, limit: int = 10, offset: int = 0
    ) -> list[User]:
        result = await self.session.execute(
            select(User)
            .order_by(User.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_all_users(self) -> int:
        result = await self.session.execute(select(func.count(User.id)))
        return result.scalar_one()

    async def get_user_with_stats(self, user_id: int) -> tuple[User, int]:
        user = await self.session.get(User, user_id)
        if not user:
            return None, 0
        result = await self.session.execute(
            select(func.count(Generation.id)).where(Generation.user_id == user_id)
        )
        count = result.scalar_one()
        return user, count

    async def get_user_history(
        self, user_id: int, limit: int = 20, offset: int = 0
    ) -> list[Generation]:
        result = await self.session.execute(
            select(Generation)
            .where(Generation.user_id == user_id)
            .order_by(Generation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def count_user_generations(self, user_id: int) -> int:
        result = await self.session.execute(
            select(func.count(Generation.id)).where(Generation.user_id == user_id)
        )
        return result.scalar_one()
