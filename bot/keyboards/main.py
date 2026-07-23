import logging

from aiogram.types import KeyboardButton, ReplyKeyboardMarkup

from bot.config import settings

logger = logging.getLogger(__name__)


def get_main_keyboard(user_id: int = 0) -> ReplyKeyboardMarkup:
    keyboard = [
        [
            KeyboardButton(text="🎨 Создать фото"),
            KeyboardButton(text="🎬 Создать видео"),
        ],
        [
            KeyboardButton(text="💬 Чат с ИИ"),
            KeyboardButton(text="🤖 Выбрать модель"),
        ],
        [
            KeyboardButton(text="👤 Профиль"),
            KeyboardButton(text="⭐ Премиум"),
        ],
        [
            KeyboardButton(text="🎬 Выбрать видео-модель"),
            KeyboardButton(text="ℹ️ О боте"),
        ],
    ]

    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
