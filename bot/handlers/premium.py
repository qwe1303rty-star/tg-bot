from aiogram import Router
from aiogram.types import Message

from bot.keyboards.main import get_main_keyboard

router = Router(name="premium")


@router.message(lambda m: m.text == "⭐ Премиум")
async def btn_premium(message: Message) -> None:
    text = (
        "⭐ <b>Премиум</b>\n\n"
        "Скоро будет доступно!\n\n"
        "Что входит в Премиум:\n"
        "• Безлимитные генерации\n"
        "• Расширенные модели (Midjourney, DALL-E 4)\n"
        "• Приоритетная очередь\n"
        "• Генерация в HD качестве\n\n"
        "Следите за обновлениями!"
    )
    await message.answer(text, reply_markup=get_main_keyboard())
