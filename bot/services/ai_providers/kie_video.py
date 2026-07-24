import asyncio
import json
import logging
import time

import aiohttp

from bot.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)

KIE_API_BASE = "https://api.kie.ai/api/v1"

KIE_VIDEO_MODELS = {
    "grok": {
        "name": "Grok Imagine",
        "emoji": "⚡",
        "desc": "6-30 сек, бюджетное",
        "model_id": "grok-imagine/text-to-video",
        "cost_per_sec": 0.008,
    },
    "seedance": {
        "name": "Seedance 2.0",
        "emoji": "✨",
        "desc": "5-10 сек,高质量",
        "model_id": "bytedance/seedance-2",
        "cost_per_sec": 0.057,
    },
    "veo": {
        "name": "Veo 3.1",
        "emoji": "🎬",
        "desc": "1080p, Google DeepMind",
        "model_id": "google/veo-3-1",
        "cost_per_sec": 0.256,
    },
}

KIE_CREDIT_COSTS_ESTIMATE = {
    "grok": 9.6,
    "seedance": 68.4,
    "veo": 256.0,
}

VIDEO_PROGRESS_STAGES = [
    (0.0, 5),
    (0.10, 15),
    (0.20, 30),
    (0.35, 50),
    (0.50, 65),
    (0.65, 78),
    (0.80, 88),
    (0.90, 95),
]


class KieVideoProvider(AIProvider):
    """Провайдер KIE.ai — генерация видео через единый API."""

    TIMEOUT_SECONDS = 300
    POLL_INTERVAL = 5

    def __init__(self, api_key: str = ""):
        self._api_key = api_key
        self.last_credits_used: float = 0.0

    @property
    def name(self) -> str:
        return "kie_video"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        model_key = kwargs.get("model", "grok")
        model_info = KIE_VIDEO_MODELS.get(model_key, KIE_VIDEO_MODELS["grok"])
        model_id = model_info["model_id"]

        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
        }

        input_params = {
            "prompt": prompt,
            "aspect_ratio": "9:16",
            "mode": "normal",
            "duration": 6,
            "resolution": "480p",
        }

        payload = {
            "model": model_id,
            "input": input_params,
        }

        timeout = aiohttp.ClientTimeout(total=self.TIMEOUT_SECONDS)
        logger.info(
            "KieVideo: creating task model=%s, prompt=%.50s...",
            model_id, prompt,
        )

        start = time.time()

        async with aiohttp.ClientSession(timeout=timeout) as session:
            create_url = f"{KIE_API_BASE}/jobs/createTask"
            async with session.post(create_url, json=payload, headers=headers) as response:
                elapsed = time.time() - start
                if response.status not in (200, 201):
                    error = await response.text()
                    logger.error(
                        "KieVideo: create HTTP %d after %.1fs: %s",
                        response.status, elapsed, error[:300],
                    )
                    raise RuntimeError(
                        f"KIE API error {response.status}: {error[:300]}"
                    )

                data = await response.json()
                if data.get("code") != 200:
                    raise RuntimeError(
                        f"KIE API error {data.get('code')}: {data.get('msg', 'unknown')}"
                    )

                task_id = data["data"]["taskId"]
                logger.info(
                    "KieVideo: task %s created, Time=%.1fs",
                    task_id, elapsed,
                )

            poll_url = f"{KIE_API_BASE}/jobs/recordInfo"
            status = "waiting"

            while status in ("waiting", "queuing", "generating"):
                await asyncio.sleep(self.POLL_INTERVAL)

                async with session.get(
                    poll_url, params={"taskId": task_id}, headers=headers
                ) as response:
                    if response.status != 200:
                        error = await response.text()
                        raise RuntimeError(
                            f"KIE poll error {response.status}: {error[:200]}"
                        )

                    data = await response.json()
                    if data.get("code") != 200:
                        raise RuntimeError(
                            f"KIE poll error {data.get('code')}: {data.get('msg')}"
                        )

                    task_data = data.get("data", {})
                    status = task_data.get("state", "unknown")
                    elapsed = time.time() - start
                    logger.info(
                        "KieVideo: task %s status=%s, elapsed=%.1fs",
                        task_id, status, elapsed,
                    )
                    logger.info(
                        "KieVideo: task %s full data keys: %s",
                        task_id, list(task_data.keys()),
                    )
                    for key in ("credits", "cost", "creditCost", "credit_cost", "creditsUsed", "credits_used", "totalCost", "total_cost", "balance", "balanceAfter"):
                        if key in task_data:
                            logger.info("KieVideo: task %s %s=%s", task_id, key, task_data[key])

                    if status == "success":
                        result_json = task_data.get("resultJson", "{}")
                        if isinstance(result_json, str):
                            result_obj = json.loads(result_json)
                        else:
                            result_obj = result_json

                        actual_credits = 0.0
                        for key in ("credits", "cost", "creditCost", "credit_cost", "creditsUsed", "credits_used", "totalCost", "total_cost"):
                            if key in task_data and task_data[key]:
                                try:
                                    actual_credits = float(task_data[key])
                                    logger.info("KieVideo: task %s actual credits from '%s' = %s", task_id, key, actual_credits)
                                    break
                                except (ValueError, TypeError):
                                    pass

                        if actual_credits <= 0:
                            actual_credits = KIE_CREDIT_COSTS_ESTIMATE.get(model_key, 9.6)
                            logger.info("KieVideo: task %s using estimate credits = %.2f (no credit field in response)", task_id, actual_credits)

                        self.last_credits_used = actual_credits

                        result_urls = result_obj.get("resultUrls", [])
                        if not result_urls:
                            raise RuntimeError(
                                f"KIE returned no video URLs: {result_obj}"
                            )

                        video_url = result_urls[0]
                        logger.info(
                            "KieVideo: downloading video from %s", video_url[:100],
                        )

                        async with session.get(video_url) as video_response:
                            if video_response.status != 200:
                                raise RuntimeError(
                                    f"Failed to download video: HTTP {video_response.status}"
                                )
                            video_bytes = await video_response.read()
                            elapsed = time.time() - start
                            logger.info(
                                "KieVideo: got %d bytes in %.1fs",
                                len(video_bytes), elapsed,
                            )

                            if len(video_bytes) < 10_000:
                                raise RuntimeError(
                                    f"KIE returned too small file: {len(video_bytes)} bytes"
                                )

                            return video_bytes

                    elif status == "fail":
                        fail_msg = task_data.get("failMsg", "Unknown error")
                        raise RuntimeError(f"KIE task failed: {fail_msg}")

        raise RuntimeError(f"KieVideo: unexpected final status: {status}")

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
                    f"{KIE_API_BASE}/chat/credit", headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        logger.info("KieVideo health: credits=%s", data)
                        return True
                    return False
        except Exception:
            return False
