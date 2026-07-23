from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.database.repositories.user import UserRepository
from bot.keyboards.main import get_main_keyboard
from bot.services.ai_providers.kie_video import KIE_VIDEO_MODELS

router = Router(name="video_models")

VIDEO_MODELS_TEXT = (
    "🎬 <b>Выберите модель для видео:</b>\n\n"
    "Текущая модель: {current}\n"
    "Осталось генераций: {left}/{limit}"
)


def _get_video_models_keyboard(current_provider: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, info in KIE_VIDEO_MODELS.items():
        check = " ✅" if key == current_provider else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{info['emoji']} {info['name']} — {info['desc']}{check}",
                    callback_data=f"select_video_model:{key}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(lambda m: m.text == "🎬 Выбрать видео-модель")
async def btn_video_models(message: Message, session) -> None:
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Отправьте /start", reply_markup=get_main_keyboard())
        return

    current = user.selected_video_provider
    model_info = KIE_VIDEO_MODELS.get(current, KIE_VIDEO_MODELS["grok"])
    current_display = f"{model_info['emoji']} {model_info['name']}"

    text = VIDEO_MODELS_TEXT.format(
        current=current_display,
        left=user.video_generations_left,
        limit=user.video_daily_limit,
    )

    await message.answer(
        text,
        reply_markup=_get_video_models_keyboard(current),
    )


@router.callback_query(lambda c: c.data.startswith("select_video_model:"))
async def callback_select_video_model(callback: CallbackQuery, session):
    provider_key = callback.data.split(":")[1]

    if provider_key not in KIE_VIDEO_MODELS:
        await callback.answer("Неизвестная модель", show_alert=True)
        return

    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(callback.from_user.id)

    if user:
        user.selected_video_provider = provider_key
        await session.commit()

    info = KIE_VIDEO_MODELS[provider_key]
    await callback.message.edit_text(
        f"✅ Модель видео изменена на <b>{info['name']}</b>\n\n"
        f"<i>{info['desc']}</i>",
    )
    await callback.answer()
