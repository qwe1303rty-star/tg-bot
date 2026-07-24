import asyncio
import logging
from datetime import datetime

import aiohttp

logger = logging.getLogger(__name__)

GOOGLE_SHEETS_TIMEOUT = 60

KIE_PRICE_PER_CREDIT_RUB = 0.475
TG_PRICE_PER_CREDIT_RUB = 0.83


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
        cost_rub: float | None = None,
        sale_rub: float | None = None,
        profit: float | None = None,
        margin: float | None = None,
    ) -> bool:
        if not self.url:
            logger.warning("Google Sheets URL not configured, skipping")
            return False

        now = datetime.now()

        if cost_rub is None:
            cost_rub = round(kie_credits * KIE_PRICE_PER_CREDIT_RUB, 2)
        if sale_rub is None:
            sale_rub = round(tg_credits * TG_PRICE_PER_CREDIT_RUB, 2)
        if profit is None:
            profit = round(sale_rub - cost_rub, 2)
        if margin is None:
            margin = round((profit / sale_rub) * 100, 1) if sale_rub > 0 else 0

        payload = {
            "date": now.strftime("%d.%m.%Y"),
            "time": now.strftime("%H:%M:%S"),
            "user_id": telegram_id,
            "username": username or "",
            "type": type_label,
            "model": model,
            "kie_credits": kie_credits,
            "cost_rub": cost_rub,
            "tg_credits": tg_credits,
            "sale_rub": sale_rub,
            "profit": profit,
            "margin": margin,
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
