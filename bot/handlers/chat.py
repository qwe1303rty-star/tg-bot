import logging

from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.handlers.states import ChatState
from bot.keyboards.main import get_main_keyboard
from bot.services.opencode_client import opencode_client

logger = logging.getLogger(__name__)

router = Router(name="chat")


@router.message(lambda m: m.text == "💬 Чат с ИИ")
async def btn_chat(message: Message, state: FSMContext) -> None:
    await state.set_state(ChatState.chatting)
    await message.answer(
        "💬 <b>Режим чата активирован!</b>\n\n"
        "Отправьте сообщение — ИИ ответит.\n"
        "Для выхода нажмите /cancel.",
    )


@router.message(ChatState.chatting, lambda m: m.text in ("🔙 Назад", "/cancel"))
async def btn_exit_chat(message: Message, state: FSMContext) -> None:
    opencode_client.clear_history(message.from_user.id)
    await state.clear()
    await message.answer(
        "💬 Чат завершён.",
        reply_markup=get_main_keyboard(message.from_user.id),
    )


@router.message(ChatState.chatting)
async def handle_chat_message(message: Message, state: FSMContext) -> None:
    text = message.text
    if not text:
        await message.answer("Отправьте текстовое сообщение.")
        return

    loading = await message.answer("🤖 Думаю...")

    try:
        response = await opencode_client.send_message(message.from_user.id, text)

        if not response:
            await loading.edit_text(
                "❌ Не удалось получить ответ.\nПопробуйте ещё раз."
            )
            return

        await loading.delete()

        for chunk in _split_message(response, 4000):
            await message.answer(chunk)

    except Exception as e:
        logger.error("Chat error: %s", e)
        await loading.edit_text("❌ Ошибка при обработке сообщения.")


def _split_message(text: str, max_len: int = 4000) -> list[str]:
    if len(text) <= max_len:
        return [text]

    chunks = []
    while text:
        if len(text) <= max_len:
            chunks.append(text)
            break

        split_at = text.rfind("\n", 0, max_len)
        if split_at == -1:
            split_at = max_len

        chunks.append(text[:split_at])
        text = text[split_at:].lstrip("\n")

    return chunks
