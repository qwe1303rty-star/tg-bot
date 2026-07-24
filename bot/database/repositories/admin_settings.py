from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.admin_setting import AdminSetting


class AdminRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get(self) -> AdminSetting:
        result = await self.session.execute(select(AdminSetting).limit(1))
        row = result.scalar_one_or_none()
        if not row:
            row = AdminSetting()
            self.session.add(row)
            await self.session.commit()
        return row

    async def toggle_limits(self) -> bool:
        settings = await self.get()
        settings.limits_enabled = not settings.limits_enabled
        await self.session.commit()
        return settings.limits_enabled

    async def toggle_free_mode(self) -> bool:
        settings = await self.get()
        settings.free_mode = not settings.free_mode
        await self.session.commit()
        return settings.free_mode

    async def set_limits(self, enabled: bool) -> None:
        settings = await self.get()
        settings.limits_enabled = enabled
        await self.session.commit()

    async def set_free_mode(self, enabled: bool) -> None:
        settings = await self.get()
        settings.free_mode = enabled
        await self.session.commit()
