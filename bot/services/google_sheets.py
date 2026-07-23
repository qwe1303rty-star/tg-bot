import asyncio
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

GOOGLE_SHEETS_TIMEOUT = 60


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
    ) -> bool:
        if not self.url:
            logger.warning("Google Sheets URL not configured, skipping")
            return False

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
                    timeout=aiohttp.ClientTimeout(total=GOOGLE_SHEETS_TIMEOUT),
                    allow_redirects=True,
                ) as resp:
                    body = await resp.text()
                    if resp.status == 200:
                        logger.info("Sheets OK: %s", body[:200])
                        return True
                    else:
                        logger.error(
                            "Sheets HTTP %s: %s", resp.status, body[:200]
                        )
                        return False
        except asyncio.TimeoutError:
            logger.error("Sheets timeout after %ss", GOOGLE_SHEETS_TIMEOUT)
            return False
        except Exception as e:
            logger.error("Sheets error: %s", e)
            return False
