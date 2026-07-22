import logging

import aiohttp

from bot.config import settings

logger = logging.getLogger(__name__)

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenCodeClient:
    """Chat-клиент через OpenRouter API (совместимый с OpenAI format)."""

    def __init__(self):
        self.conversations: dict[int, list[dict]] = {}

    @property
    def api_key(self) -> str:
        return settings.openrouter_api_key

    @property
    def model(self) -> str:
        return settings.chat_model

    def _get_history(self, user_id: int) -> list[dict]:
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        return self.conversations[user_id]

    def clear_history(self, user_id: int) -> None:
        self.conversations.pop(user_id, None)

    async def health_check(self) -> bool:
        if not self.api_key:
            logger.warning("OpenRouter API key not configured")
            return False
        return True

    async def send_message(self, user_id: int, text: str) -> str | None:
        history = self._get_history(user_id)
        history.append({"role": "user", "content": text})

        messages = [
            {
                "role": "system",
                "content": (
                    "Ты — умный и дружелюбный AI-ассистент в Telegram-боте Лапка. "
                    "Отвечай на русском языке, кратко и по существу. "
                    "Если просят код — давай его. Если шутят — поддакивай."
                ),
            },
            *history[-20:],
        ]

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/lapka-bot",
            "X-Title": "Lapka Telegram Bot",
        }

        payload = {
            "model": self.model,
            "messages": messages,
            "max_tokens": 2048,
            "temperature": 0.7,
        }

        try:
            proxy = settings.proxy_url or None
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    OPENROUTER_API_URL,
                    json=payload,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                    proxy=proxy,
                ) as resp:
                    if resp.status != 200:
                        error = await resp.text()
                        logger.error("OpenRouter error %s: %s", resp.status, error)
                        history.pop()
                        return None

                    data = await resp.json()
                    content = data["choices"][0]["message"]["content"]
                    history.append({"role": "assistant", "content": content})

                    if len(history) > 20:
                        self.conversations[user_id] = history[-20:]

                    return content

        except asyncio.TimeoutError:
            logger.error("OpenRouter timeout")
            history.pop()
            return "⏱️ Превышено время ожидания. Попробуйте ещё раз."
        except Exception as e:
            logger.error("OpenRouter error: %s", e)
            history.pop()
            return None


import asyncio

opencode_client = OpenCodeClient()
