from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.engine import Base


class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    telegram_id: Mapped[int] = mapped_column(Integer)
    username: Mapped[str | None] = mapped_column(default=None)
    amount: Mapped[int] = mapped_column(Integer)
    tx_type: Mapped[str] = mapped_column(String(20))
    provider: Mapped[str | None] = mapped_column(String(50), default=None)
    tg_credits: Mapped[int] = mapped_column(Integer, default=0)
    kie_credits: Mapped[float] = mapped_column(Float, default=0.0)
    status: Mapped[str] = mapped_column(String(20), default="Успешно")
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<CreditTransaction {self.id} user={self.telegram_id} {self.tx_type} {self.amount}>"
