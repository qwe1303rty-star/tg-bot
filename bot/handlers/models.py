from aiogram import Router
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from bot.database.repositories.user import UserRepository
from bot.keyboards.main import get_main_keyboard
from bot.services.ai_providers.info import PROVIDER_INFO

router = Router(name="models")

MODELS_TEXT = (
    "🤖 <b>Выберите модель для генерации:</b>\n\n"
    "Текущая модель: {current}\n"
    "Осталось генераций: {left}/{limit}"
)


def _get_models_keyboard(current_provider: str) -> InlineKeyboardMarkup:
    buttons = []
    for key, info in PROVIDER_INFO.items():
        check = " ✅" if key == current_provider else ""
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{info['emoji']} {info['name']}{check}",
                    callback_data=f"select_model:{key}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.message(lambda m: m.text == "🤖 Выбрать модель")
async def btn_models(message: Message, session) -> None:
    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("Отправьте /start", reply_markup=get_main_keyboard(message.from_user.id))
        return

    current = user.selected_provider
    info = PROVIDER_INFO.get(current, {})
    current_display = f"{info.get('emoji', '')} {info.get('name', current)}"

    text = MODELS_TEXT.format(
        current=current_display,
        left=user.generations_left,
        limit=user.daily_limit,
    )

    await message.answer(
        text,
        reply_markup=_get_models_keyboard(current),
    )


@router.callback_query(lambda c: c.data.startswith("select_model:"))
async def callback_select_model(callback: CallbackQuery, session):
    provider_key = callback.data.split(":")[1]

    if provider_key not in PROVIDER_INFO:
        await callback.answer("Неизвестная модель", show_alert=True)
        return

    repo = UserRepository(session)
    user = await repo.get_by_telegram_id(callback.from_user.id)

    if user:
        user.selected_provider = provider_key
        await session.commit()

    info = PROVIDER_INFO[provider_key]
    await callback.message.edit_text(
        f"✅ Модель изменена на <b>{info['name']}</b>\n\n"
        f"<i>{info['description']}</i>",
    )
    await callback.answer()
