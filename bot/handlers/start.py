from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from bot.database.repositories.credits import CreditsRepository
from bot.database.repositories.user import UserRepository
from bot.keyboards.main import get_main_keyboard

router = Router(name="start")

WELCOME_TEXT = (
    "👋 Привет, {name}!\n\n"
    "🎨 <b>Лапка</b> — ИИ-бот для создания картинок и видео.\n\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "🆓 <b>Бесплатно:</b>\n"
    "📸 Картинки Pollinations — безлимит\n"
    "🎰 Кейс — 1 раз/день\n\n"
    "💰 <b>Платные генерации:</b>\n"
    "🖼 GPT Image / Nano Banana\n"
    "🎬 Grok / Seedance / Kling / Veo\n\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "⬇️ <b>Как пользоваться?</b>\n"
    "Нажмите 🎨 <b>Создать фото</b> или 🎬 <b>Создать видео</b>.\n\n"
    "🎰 Испытай удачу — ежедневный бонус\n"
    "💰 Кредиты — купить кредиты\n"
    "👤 Профиль — баланс и настройки"
)

WELCOME_BACK_TEXT = (
    "👋 С возвращением, {name}!\n\n"
    "💰 Кредитов: {credits}\n\n"
    "Нажмите 🎨 <b>Создать фото</b> или 🎬 <b>Создать видео</b>, чтобы начать."
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

    args = message.text.split()
    if len(args) > 1 and args[1].startswith("ref_"):
        try:
            referrer_id = int(args[1][4:])
            if referrer_id != message.from_user.id and not user.referred_by:
                user.referred_by = referrer_id
                await session.commit()

                credits_repo = CreditsRepository(session)
                await credits_repo.add_credits(
                    message.from_user.id, 20,
                    tx_type="referral",
                    description=f"Реферал: +20 от {referrer_id}",
                )
                await credits_repo.add_credits(
                    referrer_id, 10,
                    tx_type="referral",
                    description=f"Реферал: +10 от {message.from_user.id}",
                )
        except (ValueError, IndexError):
            pass

    name = message.from_user.first_name or "друг"

    if is_new:
        text = WELCOME_TEXT.format(name=name)
    else:
        text = WELCOME_BACK_TEXT.format(name=name, credits=user.credits)

    await message.answer(text, reply_markup=get_main_keyboard(message.from_user.id))
