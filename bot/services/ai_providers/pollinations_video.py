import logging
import time
from urllib.parse import quote

import aiohttp

from bot.config import settings
from bot.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

VIDEO_PROGRESS_STAGES = [
    (0.0,  5),
    (0.08, 15),
    (0.15, 25),
    (0.25, 40),
    (0.35, 55),
    (0.50, 70),
    (0.65, 80),
    (0.80, 90),
    (0.90, 95),
]

VIDEO_MODELS = {
    "wan": {"name": "Wan", "emoji": "🎬", "desc": "2-15 сек, с аудио"},
    "wan-fast": {"name": "Wan Fast", "emoji": "⚡", "desc": "2-15 сек, быстрая"},
    "wan-pro": {"name": "Wan Pro", "emoji": "💎", "desc": "2-15 сек, высокое качество"},
    "veo": {"name": "Veo", "emoji": "🔵", "desc": "4-8 сек, Google Veo"},
    "seedance": {"name": "Seedance", "emoji": "💃", "desc": "2-10 сек, ByteDance"},
    "nova-reel": {"name": "Nova Reel", "emoji": "🎞", "desc": "6-120 сек,最长 duration"},
}


class PollinationsVideoProvider(AIProvider):
    """Провайдер Pollinations.ai — генерация видео."""

    BASE_URL = "https://gen.pollinations.ai"
    TIMEOUT_SECONDS = 180

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "pollinations_video"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        model = kwargs.get("model", "wan")
        width = kwargs.get("width", 720)
        height = kwargs.get("height", 1280)
        duration = kwargs.get("duration", 5)
        audio = kwargs.get("audio", False)

        encoded = quote(prompt)
        url = (
            f"{self.BASE_URL}/video/{encoded}"
            f"?model={model}&width={width}&height={height}"
            f"&duration={duration}"
        )
        if audio:
            url += "&audio=true"

        if self._api_key:
            url += f"&key={self._api_key}"

        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
        logger.info(
            "PollinationsVideo: generating model=%s %dx%d %ds, prompt=%.50s...",
            model, width, height, duration, prompt,
        )

        start = time.time()
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url) as response:
                elapsed = time.time() - start
                if response.status != 200:
                    error = await response.text()
                    logger.error(
                        "PollinationsVideo: HTTP %d after %.1fs: %s",
                        response.status, elapsed, error[:200],
                    )
                    raise RuntimeError(
                        f"Pollinations Video API error {response.status}: {error[:200]}"
                    )

                content_type = response.headers.get("Content-Type", "")
                logger.info(
                    "PollinationsVideo: HTTP 200, Content-Type=%s, Time=%.1fs",
                    content_type, elapsed,
                )

                data = await response.read()
                logger.info(
                    "PollinationsVideo: got %d bytes in %.1fs", len(data), elapsed,
                )

                if len(data) < 10_000:
                    text_preview = data.decode("utf-8", errors="replace")[:200]
                    logger.error(
                        "PollinationsVideo: response too small (%d bytes): %s",
                        len(data), text_preview,
                    )
                    raise RuntimeError(
                        f"Pollinations Video returned too small response: {text_preview}"
                    )

                if not self._is_valid_video(data):
                    logger.error(
                        "PollinationsVideo: not a valid video file (%d bytes)", len(data),
                    )
                    raise RuntimeError("Pollinations Video returned invalid video file")

                return data

    def estimate_progress(self, elapsed: float) -> int:
        for threshold, pct in VIDEO_PROGRESS_STAGES:
            if elapsed < self.TIMEOUT_SECONDS * threshold:
                return pct
        return 99

    async def health_check(self) -> bool:
        try:
            timeout = aiohttp.ClientTimeout(total=15)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                url = f"{self.BASE_URL}/video/test?model=wan&duration=2"
                if self._api_key:
                    url += f"&key={self._api_key}"
                async with session.get(url) as response:
                    return response.status == 200
        except Exception:
            return False

    @staticmethod
    def _is_valid_video(data: bytes) -> bool:
        if len(data) < 12:
            return False
        if data[4:8] == b"ftyp":
            return True
        if data[:3] == b"\x00\x00\x00":
            return True
        if data[:4] == b"\x1a\x45\xdf\xa3":
            return True
        return True
