from aiogram import Router
from aiogram.types import Message

from bot.keyboards.main import get_main_keyboard

router = Router(name="about")

ABOUT_TEXT = (
    "ℹ️ <b>О боте «Лапка»</b>\n\n"
    "🤖 <b>Что умеет:</b>\n"
    "• Генерация картинок по описанию (ИИ)\n"
    "• Генерация видео по описанию (ИИ)\n"
    "• Чат с ИИ (Gemini 2.5 Flash)\n\n"
    "🎨 <b>Модели для картинок:</b>\n"
    "• Pollinations (Flux/SD)\n"
    "• DALL-E 3 (OpenAI)\n"
    "• Stability AI\n"
    "• Flux\n\n"
    "🎬 <b>Модели для видео:</b>\n"
    "• Wan 2.1\n"
    "• MiniMax\n"
    "• LTX Video\n\n"
    "💬 <b>Чат:</b>\n"
    "• Google Gemini 2.5 Flash через OpenRouter\n\n"
    "📊 <b>Лимиты:</b>\n"
    "• Картинки: 10/день\n"
    "• Видео: 10/день\n"
    "• Премиум: скоро\n\n"
    "⚠️ <b>Приватность:</b>\n"
    "Запросы обрабатываются через внешние API\n"
    "(OpenRouter, Google, Pollinations). Не отправляйте\n"
    "конфиденциальные данные в чат с ИИ.\n\n"
    "🤖 Версия: 0.2.0"
)


@router.message(lambda m: m.text == "ℹ️ О боте")
async def btn_about(message: Message) -> None:
    await message.answer(ABOUT_TEXT, reply_markup=get_main_keyboard())
