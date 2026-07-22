import aiohttp

from bot.config import settings
from bot.services.ai_providers.base import AIProvider


class DalleProvider(AIProvider):
    """Провайдер DALL-E 3 через OpenAI API."""

    API_URL = "https://api.openai.com/v1/images/generations"

    @property
    def name(self) -> str:
        return "dalle"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        size = kwargs.get("size", "1024x1024")
        quality = kwargs.get("quality", "standard")

        headers = {
            "Authorization": f"Bearer {settings.openai_api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": size,
            "quality": quality,
            "response_format": "b64_json",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                self.API_URL, json=payload, headers=headers
            ) as response:
                if response.status != 200:
                    error = await response.text()
                    raise RuntimeError(
                        f"DALL-E API error {response.status}: {error}"
                    )

                data = await response.json()
                import base64

                return base64.b64decode(data["data"][0]["b64_json"])

    async def health_check(self) -> bool:
        if not settings.openai_api_key:
            return False
        try:
            headers = {"Authorization": f"Bearer {settings.openai_api_key}"}
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://api.openai.com/v1/models",
                    headers=headers,
                ) as response:
                    return response.status == 200
        except Exception:
            return False
