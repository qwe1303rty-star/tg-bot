from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.config import settings


def get_main_keyboard(user_id: int = 0) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🎨 Создать фото"),
            KeyboardButton(text="🎬 Создать видео"),
        ],
        [
            KeyboardButton(text="🎰 Испытай удачу"),
            KeyboardButton(text="🤖 Выбрать модель"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="💰 Кредиты"),
        ],
        [
            KeyboardButton(text="🎬 Выбрать видео-модель"),
            KeyboardButton(text="ℹ️ О боте"),
        ],
    ]

    if user_id in settings.admin_ids:
        keyboard.append([KeyboardButton(text="📊 Статистика")])

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
