from aiogram import Router
from aiogram.types import Message

from bot.database.repositories.generation import GenerationRepository
from bot.database.repositories.user import UserRepository
from bot.keyboards.main import get_main_keyboard
from bot.services.ai_providers.info import get_provider_display

router = Router(name="profile")


@router.message(lambda m: m.text == "👤 Профиль")
async def cmd_profile(message: Message, session) -> None:
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer(
            "❌ Профиль не найден. Отправьте /start",
            reply_markup=get_main_keyboard(),
        )
        return

    gen_repo = GenerationRepository(session)
    generations = await gen_repo.get_by_user(user.id, limit=1000)

    name = user.first_name or user.username or "друг"
    username = f"@{user.username}" if user.username else "нет"
    reg_date = user.created_at.strftime("%d.%m.%Y")
    count = len(generations)
    provider_display = get_provider_display(user.selected_provider)

    text = (
        f"👤 <b>Профиль</b>\n\n"
        f"📛 Имя: {name}\n"
        f"🔗 Username: {username}\n"
        f"🆔 ID: <code>{user.telegram_id}</code>\n"
        f"📅 Регистрация: {reg_date}\n"
        f"🖼 Всего генераций: {count}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎨 Модель картинок: {provider_display}\n"
        f"📸 Сегодня картинок: {user.generations_today}/{user.daily_limit}\n\n"
        f"🎬 Модель видео: {user.selected_video_provider}\n"
        f"🎥 Сегодня видео: {user.video_generations_today}/{user.video_daily_limit}\n\n"
        f"📋 Статус: {user.status}"
    )

    await message.answer(text, reply_markup=get_main_keyboard())
