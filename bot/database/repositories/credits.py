from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from bot.models.transaction import CreditTransaction
from bot.models.user import User


class CreditsRepository:
    def __init__(self, session: AsyncSession):
        self._session = session

    async def get_balance(self, telegram_id: int) -> int:
        result = await self._session.execute(
            select(User.credits).where(User.telegram_id == telegram_id)
        )
        row = result.scalar_one_or_none()
        return row or 0

    async def add_credits(
        self,
        telegram_id: int,
        amount: int,
        tx_type: str = "earn",
        description: str | None = None,
    ) -> int:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return 0
        user.credits += amount

        tx = CreditTransaction(
            user_id=user.id,
            telegram_id=telegram_id,
            username=user.username,
            amount=amount,
            tx_type=tx_type,
            tg_credits=amount,
            description=description,
        )
        self._session.add(tx)
        await self._session.commit()
        return user.credits

    async def spend_credits(
        self,
        telegram_id: int,
        amount: int,
        tx_type: str = "spend",
        provider: str | None = None,
        kie_credits: float = 0.0,
        description: str | None = None,
    ) -> bool:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user or user.credits < amount:
            return False
        user.credits -= amount

        tx = CreditTransaction(
            user_id=user.id,
            telegram_id=telegram_id,
            username=user.username,
            amount=-amount,
            tx_type=tx_type,
            provider=provider,
            tg_credits=amount,
            kie_credits=kie_credits,
            description=description,
        )
        self._session.add(tx)
        await self._session.commit()
        return True

    async def has_enough(self, telegram_id: int, amount: int) -> bool:
        balance = await self.get_balance(telegram_id)
        return balance >= amount

    async def can_open_case(self, telegram_id: int) -> bool:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return False
        return user.last_daily_case != date.today()

    async def claim_daily_case(self, telegram_id: int, credits: int) -> int:
        result = await self._session.execute(
            select(User).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return 0
        user.credits += credits
        user.last_daily_case = date.today()

        tx = CreditTransaction(
            user_id=user.id,
            telegram_id=telegram_id,
            username=user.username,
            amount=credits,
            tx_type="case",
            tg_credits=credits,
            description=f"Ежедневный кейс: {credits} кредитов",
        )
        self._session.add(tx)
        await self._session.commit()
        return user.credits
