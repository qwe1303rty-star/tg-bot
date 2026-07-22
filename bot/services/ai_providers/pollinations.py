import logging
import time
from urllib.parse import quote

import aiohttp

from bot.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

PROGRESS_STAGES = [
    (0.0,  10),
    (0.15, 30),
    (0.30, 50),
    (0.50, 70),
    (0.70, 85),
    (0.85, 95),
]


class PollinationsProvider(AIProvider):
    """Провайдер Pollinations.ai — бесплатная генерация изображений."""

    BASE_URL = "https://image.pollinations.ai"
    TIMEOUT_SECONDS = 90

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "pollinations"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        width = kwargs.get("width", 1024)
        height = kwargs.get("height", 1024)

        encoded = quote(prompt)
        url = f"{self.BASE_URL}/prompt/{encoded}?width={width}&height={height}&nologo=true"

        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
        logger.info("Pollinations: generating %dx%d, prompt=%.50s...", width, height, prompt)

        start = time.time()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                elapsed = time.time() - start
                if response.status != 200:
                    error = await response.text()
                    logger.error("Pollinations: HTTP %d after %.1fs: %s", response.status, elapsed, error[:200])
                    raise RuntimeError(f"Pollinations API error {response.status}: {error[:200]}")

                content_type = response.headers.get("Content-Type", "")
                logger.info("Pollinations: HTTP 200, Content-Type=%s, Time=%.1fs", content_type, elapsed)

                data = await response.read()
                logger.info("Pollinations: got %d bytes in %.1fs", len(data), elapsed)

                if len(data) < 1000:
                    text_preview = data.decode("utf-8", errors="replace")[:200]
                    logger.error("Pollinations: response too small (%d bytes), probably error: %s", len(data), text_preview)
                    raise RuntimeError(f"Pollinations returned too small response: {text_preview}")

                return data

    def estimate_progress(self, elapsed: float) -> int:
        for threshold, pct in PROGRESS_STAGES:
            if elapsed < self.TIMEOUT_SECONDS * threshold:
                return pct
        return 99

    async def health_check(self) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(f"{self.BASE_URL}/prompt/test?width=64&height=64&nologo=true") as response:
                    return response.status == 200
        except Exception:
            return False
