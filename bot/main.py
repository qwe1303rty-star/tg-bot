import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.enums import ParseMode

from bot.config import settings
from bot.database.engine import Base, engine
from bot.services.google_sheets import GoogleSheetsService
from bot.handlers.about import router as about_router
from bot.handlers.admin import router as admin_router
from bot.handlers.case import router as case_router
from bot.handlers.credits import router as credits_router
from bot.handlers.generate import router as generate_router
from bot.handlers.models import router as models_router
from bot.handlers.premium import router as premium_router
from bot.handlers.profile import router as profile_router
from bot.handlers.start import router as start_router
from bot.handlers.video import router as video_router
from bot.handlers.video_models import router as video_models_router
from bot.middlewares.db import DatabaseMiddleware
from bot.services.ai_providers.dalle import DalleProvider
from bot.services.ai_providers.flux import FluxProvider
from bot.services.ai_providers.pollinations import PollinationsProvider
from bot.services.ai_providers.kie_video import KieVideoProvider
from bot.services.ai_providers.registry import ProviderRegistry
from bot.services.ai_providers.stability import StabilityProvider
from bot.services.ai_providers.stub import StubProvider

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)


async def on_startup() -> None:
    settings.media_path.mkdir(parents=True, exist_ok=True)
    db_dir = settings.db_url.split("///")[-1].rsplit("/", 1)[0] if "///" in settings.db_url else ""
    if db_dir:
        from pathlib import Path
        Path(db_dir).mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    ProviderRegistry.register(StubProvider())
    ProviderRegistry.register(PollinationsProvider(api_key=settings.pollinations_api_key))
    ProviderRegistry.register(KieVideoProvider(api_key=settings.kie_api_key))
    ProviderRegistry.register(DalleProvider())
    ProviderRegistry.register(StabilityProvider())
    ProviderRegistry.register(FluxProvider())

    sheets_service = GoogleSheetsService(webhook_url=settings.google_sheets_url)

    logger.info(
        "Bot started. Providers: %s. Admin IDs: %s. Sheets: %s",
        ProviderRegistry.list_providers(),
        settings.admin_ids,
        bool(settings.google_sheets_url),
    )


async def on_shutdown() -> None:
    await engine.dispose()
    logger.info("Database connection closed")


async def main() -> None:
    session = AiohttpSession(proxy=settings.proxy_url or None)
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        session=session,
    )
    dp = Dispatcher()

    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    db_middleware = DatabaseMiddleware()
    for r in [
        start_router,
        admin_router,
        generate_router,
        video_router,
        profile_router,
        models_router,
        video_models_router,
        premium_router,
        case_router,
        credits_router,
        about_router,
    ]:
        r.message.middleware(db_middleware)
        r.callback_query.middleware(db_middleware)

    dp.include_routers(
        start_router,
        admin_router,
        generate_router,
        video_router,
        profile_router,
        models_router,
        video_models_router,
        premium_router,
        case_router,
        credits_router,
        about_router,
    )

    dp["bot"] = bot
    dp["sheets"] = GoogleSheetsService(webhook_url=settings.google_sheets_url)

    logger.info("Bot starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
