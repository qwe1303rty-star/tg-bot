from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.engine import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(default=None)
    first_name: Mapped[str | None] = mapped_column(default=None)
    last_name: Mapped[str | None] = mapped_column(default=None)

    selected_provider: Mapped[str] = mapped_column(String(50), default="pollinations")
    daily_limit: Mapped[int] = mapped_column(Integer, default=10)
    generations_today: Mapped[int] = mapped_column(Integer, default=0)
    last_generation_date: Mapped[date | None] = mapped_column(Date, default=None)
    is_premium: Mapped[bool] = mapped_column(default=False)

    selected_video_provider: Mapped[str] = mapped_column(String(50), default="grok")
    video_daily_limit: Mapped[int] = mapped_column(Integer, default=3)
    video_generations_today: Mapped[int] = mapped_column(Integer, default=0)
    last_video_generation_date: Mapped[date | None] = mapped_column(Date, default=None)

    credits: Mapped[int] = mapped_column(Integer, default=0)
    last_daily_case: Mapped[date | None] = mapped_column(Date, default=None)
    referral_code: Mapped[str | None] = mapped_column(String(20), default=None, unique=True)
    referred_by: Mapped[int | None] = mapped_column(BigInteger, default=None)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<User {self.telegram_id}>"

    @property
    def generations_left(self) -> int:
        return max(0, self.daily_limit - self.generations_today)

    @property
    def video_generations_left(self) -> int:
        return max(0, self.video_daily_limit - self.video_generations_today)

    @property
    def status(self) -> str:
        return "⭐ Premium" if self.is_premium else "🆓 Free"
