from aiogram.types import KeyboardButton, ReplyKeyboardMarkup


def get_main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
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
        ],
        resize_keyboard=True,
    )
