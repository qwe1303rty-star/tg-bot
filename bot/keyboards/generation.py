from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_generation_keyboard(generation_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Повторить",
                    callback_data=f"repeat:{generation_id}",
                ),
                InlineKeyboardButton(
                    text="✏️ Изменить промпт",
                    callback_data=f"edit:{generation_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬇️ Скачать HD",
                    callback_data=f"download:{generation_id}",
                ),
            ],
        ]
    )


def get_video_keyboard(generation_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🔄 Повторить",
                    callback_data=f"repeat_video:{generation_id}",
                ),
                InlineKeyboardButton(
                    text="✏️ Изменить промпт",
                    callback_data=f"edit_video:{generation_id}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="⬇️ Скачать",
                    callback_data=f"download_video:{generation_id}",
                ),
            ],
        ]
    )


def get_cancel_keyboard(callback_prefix: str = "cancel_generation") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data=callback_prefix,
                )
            ],
        ]
    )
