import asyncio
import random
import string

from aiogram import Router
from aiogram.types import Message

from bot.database.repositories.credits import CreditsRepository
from bot.keyboards.main import get_main_keyboard

router = Router(name="case")

CASE_PRIZES = [
    (64, 50, "777"),
    (50, 10, "77x"),
    (30, 5, "x7x"),
    (10, 3, "xx7"),
    (1, 1, "xxx"),
]

SLOT_SYMBOLS = ["7", "⭐", "💎", "🔔", "🍀"]


def _roll_prize() -> tuple[int, str]:
    value = random.randint(1, 64)
    if value == 64:
        return 50, "777"
    elif value >= 50:
        return 10, "77" + random.choice(SLOT_SYMBOLS)
    elif value >= 30:
        return 5, random.choice(SLOT_SYMBOLS) + "7" + random.choice(SLOT_SYMBOLS)
    elif value >= 10:
        return 3, random.choice(SLOT_SYMBOLS) + random.choice(SLOT_SYMBOLS) + "7"
    else:
        return 1, random.choice(SLOT_SYMBOLS) * 3


def _slot_frame(symbols: list[str]) -> str:
    return (
        "╔═══════════════════╗\n"
        f"║  {symbols[0]}  {symbols[1]}  {symbols[2]}  ║\n"
        "╚═══════════════════╝"
    )


@router.message(lambda m: m.text == "🎰 Испытай удачу")
async def btn_open_case(message: Message, session) -> None:
    credits_repo = CreditsRepository(session)

    if not await credits_repo.can_open_case(message.from_user.id):
        await message.answer(
            "🎰 Кейс уже открыт сегодня!\n"
            "Приходи завтра за новым бонусом.",
            reply_markup=get_main_keyboard(message.from_user.id),
        )
        return

    prize_credits, result_text = _roll_prize()

    symbols_pool = [random.choice(SLOT_SYMBOLS) for _ in range(6)]

    msg = await message.answer(
        "🎰 Открываю кейс...\n\n"
        + _slot_frame(symbols_pool[:3])
        + "\n\n░░░░░░░░░░░░░░░░░░░░"
    )
    await asyncio.sleep(0.5)

    await msg.edit_text(
        "🎰 Крутится...\n\n"
        + _slot_frame(symbols_pool[1:4])
        + "\n\n████████░░░░░░░░░░░░"
    )
    await asyncio.sleep(0.5)

    await msg.edit_text(
        "🎰 Почти готово...\n\n"
        + _slot_frame(symbols_pool[2:5])
        + "\n\n██████████████░░░░░░"
    )
    await asyncio.sleep(0.5)

    if result_text == "777":
        final_symbols = ["7", "7", "7"]
        header = "🎉🎉🎉 ДЖЕКПОТ!!! 🎉🎉🎉"
    elif result_text.startswith("77"):
        final_symbols = ["7", "7", random.choice(SLOT_SYMBOLS)]
        header = "🎉 Отлично!"
    elif result_text[1] == "7":
        final_symbols = [random.choice(SLOT_SYMBOLS), "7", random.choice(SLOT_SYMBOLS)]
        header = "✨ Неплохо!"
    elif result_text.endswith("7"):
        final_symbols = [random.choice(SLOT_SYMBOLS), random.choice(SLOT_SYMBOLS), "7"]
        header = "👍 неплохо"
    else:
        final_symbols = [random.choice(SLOT_SYMBOLS) for _ in range(3)]
        header = "В следующий раз повезёт!"

    new_balance = await credits_repo.claim_daily_case(
        message.from_user.id, prize_credits
    )

    await msg.edit_text(
        f"{header}\n\n"
        + _slot_frame(final_symbols)
        + f"\n\n💰 +{prize_credits} кредитов\n"
        f"💰 Баланс: {new_balance} кредитов"
    )
