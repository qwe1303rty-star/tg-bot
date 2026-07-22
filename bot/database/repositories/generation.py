from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.generation import Generation


class GenerationRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: int,
        prompt: str,
        provider: str,
        image_path: str | None = None,
    ) -> Generation:
        generation = Generation(
            user_id=user_id,
            prompt=prompt,
            provider=provider,
            image_path=image_path,
        )
        self.session.add(generation)
        await self.session.flush()
        return generation

    async def get_by_user(
        self, user_id: int, limit: int = 10, offset: int = 0
    ) -> list[Generation]:
        result = await self.session.execute(
            select(Generation)
            .where(Generation.user_id == user_id)
            .order_by(Generation.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def get_by_id(self, generation_id: int) -> Generation | None:
        result = await self.session.execute(
            select(Generation).where(Generation.id == generation_id)
        )
        return result.scalar_one_or_none()
