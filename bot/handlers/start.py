from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.config import settings
from bot.database.repositories.user import UserRepository
from bot.keyboards.main import get_main_keyboard

router = Router(name="start")

WELCOME_TEXT = (
    "👋 Привет, {name}!\n\n"
    "🎨 <b>Лапка</b> — ИИ-бот для создания картинок и видео.\n\n"
    "Отправьте описание — и я сгенерирую изображение или видео!\n\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🆓 <b>Бесплатно:</b>\n"
    "📸 Картинки: 10/день\n"
    "🎬 Видео: 10/день\n\n"
    "🎨 Модели картинок:\n"
    "⚡ Pollinations (Flux/SD)\n"
    "🖼 DALL-E 3\n"
    "🎨 Stability AI\n\n"
    "🎬 Модели видео:\n"
    "⚡ Grok Imagine\n"
    "✨ Seedance 2.0\n"
    "🎬 Veo 3.1\n\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "⬇️ <b>Как пользоваться?</b>\n"
    "Нажмите 🎨 <b>Создать фото</b> или 🎬 <b>Создать видео</b>.\n\n"
    "🤖 Выберите модель — 🤖 <b>Выбрать модель</b>\n"
    "🎬 Видео-модели — 🎬 <b>Выбрать видео-модель</b>\n"
    "👤 Профиль — 👤 <b>Профиль</b>"
)


@router.message(CommandStart())
async def cmd_start(message: Message, session) -> None:
    repo = UserRepository(session)
    user, is_new = await repo.get_or_create(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
    )

    name = message.from_user.first_name or "друг"

    if is_new:
        text = WELCOME_TEXT.format(name=name)
    else:
        text = (
            f"👋 С возвращением, {name}!\n\n"
            f"🎨 Модель картинок: {user.selected_provider}\n"
            f"📸 Сегодня: {user.generations_today}/{user.daily_limit}\n\n"
            f"🎬 Модель видео: {user.selected_video_provider}\n"
            f"🎥 Сегодня видео: {user.video_generations_today}/{user.video_daily_limit}\n\n"
            "Нажмите 🎨 <b>Создать фото</b> или 🎬 <b>Создать видео</b>, чтобы начать."
        )

    await message.answer(text, reply_markup=get_main_keyboard(message.from_user.id))

    if message.from_user.id in settings.admin_ids:
        admin_kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="📊 Статистика", callback_data="admin:stats")],
                [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users:0")],
            ]
        )
        await message.answer("🔧 <b>Панель администратора:</b>", reply_markup=admin_kb)
