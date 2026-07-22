import logging

from bot.services.ai_providers.base import AIProvider

logger = logging.getLogger(__name__)


class ProviderRegistry:
    """Реестр AI-провайдеров. Поддерживает регистрацию и получение по имени."""

    _providers: dict[str, AIProvider] = {}

    @classmethod
    def register(cls, provider: AIProvider) -> None:
        cls._providers[provider.name] = provider
        logger.info("AI provider registered: %s", provider.name)

    @classmethod
    def get(cls, name: str) -> AIProvider:
        if name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise KeyError(
                f"Provider '{name}' not found. Available: {available}"
            )
        return cls._providers[name]

    @classmethod
    def get_default(cls) -> AIProvider:
        if not cls._providers:
            raise RuntimeError("No AI providers registered")
        return next(iter(cls._providers.values()))

    @classmethod
    def list_providers(cls) -> list[str]:
        return list(cls._providers.keys())
