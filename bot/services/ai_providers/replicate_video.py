import asyncio
import logging
import time

import aiohttp

from bot.config import settings
from bot.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

REPLICATE_API_URL = "https://api.replicate.com/v1"

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
    "wan": {
        "name": "Wan 2.5 T2V",
        "emoji": "🎬",
        "desc": "5-10 сек, высокое качество",
        "model_id": "wan-video/wan-2.5-t2v-fast",
    },
    "seedance": {
        "name": "Seedance 2.0",
        "emoji": "✨",
        "desc": "5-10 сек, ByteDance",
        "model_id": "bytedance/seedance-2.0",
    },
    "seedance_mini": {
        "name": "Seedance Mini",
        "emoji": "⚡",
        "desc": "Быстрая генерация, ниже цена",
        "model_id": "bytedance/seedance-2.0-mini",
    },
    "happyhorse": {
        "name": "Happy Horse",
        "emoji": "🐴",
        "desc": "5 сек, Alibaba",
        "model_id": "alibaba/happyhorse-1.1",
    },
    "luma": {
        "name": "Luma Ray",
        "emoji": "🎞",
        "desc": "5 сек, Luma AI",
        "model_id": "luma/ray-3.2",
    },
}


class ReplicateVideoProvider(AIProvider):
    """Провайдер Replicate — генерация видео через API."""

    TIMEOUT_SECONDS = 300
    POLL_INTERVAL = 3

    def __init__(self, api_key: str = ""):
        self._api_key = api_key

    @property
    def name(self) -> str:
        return "replicate_video"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        model_key = kwargs.get("model", "wan")
        model_info = VIDEO_MODELS.get(model_key, VIDEO_MODELS["wan"])
        model_id = model_info["model_id"]

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "input": {
                "prompt": prompt,
            }
        }

        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
        logger.info(
            "ReplicateVideo: creating prediction model=%s, prompt=%.50s...",
            model_id, prompt,
        )

        start = time.time()

        async with aiohttp.ClientSession(timeout=timeout) as session:
            create_url = f"{REPLICATE_API_URL}/models/{model_id}/predictions"
            async with session.post(create_url, json=payload, headers=headers) as response:
                elapsed = time.time() - start
                if response.status not in (200, 201):
                    error = await response.text()
                    logger.error(
                        "ReplicateVideo: create HTTP %d after %.1fs: %s",
                        response.status, elapsed, error[:300],
                    )
                    raise RuntimeError(
                        f"Replicate API error {response.status}: {error[:300]}"
                    )

                data = await response.json()
                prediction_id = data["id"]
                status = data.get("status", "starting")
                logger.info(
                    "ReplicateVideo: prediction %s created, status=%s, Time=%.1fs",
                    prediction_id, status, elapsed,
                )

            poll_url = f"{REPLICATE_API_URL}/predictions/{prediction_id}"

            while status in ("starting", "processing"):
                await asyncio.sleep(self.POLL_INTERVAL)

                async with session.get(poll_url, headers=headers) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise RuntimeError(f"Replicate poll error {response.status}: {error[:200]}")

                    data = await response.json()
                    status = data.get("status", "unknown")
                    elapsed = time.time() - start
                    logger.info(
                        "ReplicateVideo: prediction %s status=%s, elapsed=%.1fs",
                        prediction_id, status, elapsed,
                    )

                    if status == "succeeded":
                        output = data.get("output")
                        if isinstance(output, list) and len(output) > 0:
                            video_url = output[0]
                        elif isinstance(output, str):
                            video_url = output
                        else:
                            raise RuntimeError(f"Replicate returned unexpected output: {output}")

                        logger.info(
                            "ReplicateVideo: downloading video from %s", video_url[:100],
                        )
                        async with session.get(video_url) as video_response:
                            if video_response.status != 200:
                                raise RuntimeError(
                                    f"Failed to download video: HTTP {video_response.status}"
                                )
                            video_bytes = await video_response.read()
                            elapsed = time.time() - start
                            logger.info(
                                "ReplicateVideo: got %d bytes in %.1fs",
                                len(video_bytes), elapsed,
                            )

                            if len(video_bytes) < 10_000:
                                raise RuntimeError(
                                    f"Replicate Video returned too small file: {len(video_bytes)} bytes"
                                )

                            return video_bytes

                    elif status == "failed":
                        error = data.get("error", "Unknown error")
                        raise RuntimeError(f"Replicate prediction failed: {error}")

                    elif status == "canceled":
                        raise RuntimeError("Replicate prediction was canceled")

        raise RuntimeError(f"ReplicateVideo: unexpected final status: {status}")

    def estimate_progress(self, elapsed: float) -> int:
        for threshold, pct in VIDEO_PROGRESS_STAGES:
            if elapsed < self.TIMEOUT_SECONDS * threshold:
                return pct
        return 99

    async def health_check(self) -> bool:
        if not self._api_key:
            return False
        try:
            timeout = aiohttp.ClientTimeout(total=10)
            headers = {"Authorization": f"Bearer {self._api_key}"}
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(
                    f"{REPLICATE_API_URL}/account", headers=headers
                ) as response:
                    return response.status == 200
        except Exception:
            return False
