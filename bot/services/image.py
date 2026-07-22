import logging
import uuid
from pathlib import Path

from bot.config import settings
from bot.services.ai_providers.registry import ProviderRegistry

logger = logging.getLogger(__name__)


def _detect_extension(data: bytes) -> str:
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return ".png"
    if data[:2] == b"\xff\xd8":
        return ".jpg"
    if data[:4] == b"GIF8":
        return ".gif"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".png"


async def generate_image(
    prompt: str,
    provider_name: str | None = None,
    **kwargs,
) -> tuple[bytes, str, str]:
    if provider_name:
        provider = ProviderRegistry.get(provider_name)
    else:
        provider = ProviderRegistry.get_default()

    logger.info("generate_image: provider=%s, prompt=%.50s", provider.name, prompt)
    image_bytes = await provider.generate(prompt, **kwargs)
    logger.info("generate_image: got %d bytes from %s", len(image_bytes), provider.name)

    ext = _detect_extension(image_bytes)
    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = settings.media_path / filename
    file_path.write_bytes(image_bytes)
    logger.info("generate_image: saved to %s", file_path)

    return image_bytes, str(file_path), provider.name
