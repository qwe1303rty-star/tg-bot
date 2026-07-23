import asyncio
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)


class GoogleSheetsService:
    def __init__(self, webhook_url: str):
        self.url = webhook_url

    async def log_transaction(
        self,
        telegram_id: int,
        username: str | None,
        type_label: str,
        model: str,
        kie_credits: float,
        tg_credits: int,
        status: str = "Успешно",
    ) -> None:
        if not self.url:
            return

        now = datetime.now()
        payload = {
            "date": now.strftime("%d.%m.%Y"),
            "time": now.strftime("%H:%M:%S"),
            "user_id": telegram_id,
            "username": username or "",
            "type": type_label,
            "model": model,
            "kie_credits": kie_credits,
            "tg_credits": tg_credits,
            "status": status,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    self.url,
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as resp:
                    if resp.status != 200:
                        logger.warning("Sheets webhook returned %s", resp.status)
        except Exception as e:
            logger.warning("Failed to log to Google Sheets: %s", e)
