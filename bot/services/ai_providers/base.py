from abc import ABC, abstractmethod


class AIProvider(ABC):
    """Абстрактный базовый класс для AI-провайдеров генерации изображений."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Уникальное имя провайдера (например, 'dalle', 'stability')."""
        ...

    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> bytes:
        """
        Генерирует изображение по текстовому запросу.

        Args:
            prompt: Текстовое описание изображения.
            **kwargs: Дополнительные параметры провайдера.

        Returns:
            bytes: PNG-данные изображения.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Проверяет доступность провайдера."""
        ...
