from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

    bot_token: str = ""

    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "ai_image_bot"
    db_user: str = "postgres"
    db_password: str = "postgres"
    db_url: str = "sqlite+aiosqlite:///bot.db"

    openai_api_key: str = ""
    stability_api_key: str = ""
    openrouter_api_key: str = ""
    pollinations_api_key: str = ""
    replicate_api_token: str = ""
    chat_model: str = "google/gemini-2.5-flash"
    proxy_url: str = ""

    default_ai_provider: str = "dalle"
    media_path: Path = Path("./media/generated")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
