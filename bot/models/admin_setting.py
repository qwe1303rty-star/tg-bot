from sqlalchemy import Boolean, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from bot.database.engine import Base


class AdminSetting(Base):
    __tablename__ = "admin_settings"

    id: Mapped[int] = mapped_column(primary_key=True)
    limits_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    free_mode: Mapped[bool] = mapped_column(Boolean, default=False)
