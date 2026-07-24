import logging

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from sqlalchemy import select

from bot.database.repositories.credits import CreditsRepository
from bot.keyboards.credits import get_credits_keyboard, get_pack_by_id
from bot.keyboards.main import get_main_keyboard
from bot.models.transaction import CreditTransaction
from bot.models.user import User

logger = logging.getLogger(__name__)

router = Router(name="credits")


async def _log_shop_open(session, user: User) -> None:
    existing = await session.execute(
        select(CreditTransaction).where(
            CreditTransaction.user_id == user.id,
            CreditTransaction.tx_type == "shop_open",
        ).limit(1)
    )
    if existing.scalar_one_or_none():
        return
    tx = CreditTransaction(
        user_id=user.id,
        telegram_id=user.telegram_id,
        username=user.username,
        amount=0,
        tx_type="shop_open",
        description="Открыл магазин кредитов",
    )
    session.add(tx)
    await session.commit()


@router.message(lambda m: m.text == "💰 Кредиты")
async def btn_credits(message: Message, session) -> None:
    credits_repo = CreditsRepository(session)
    balance = await credits_repo.get_balance(message.from_user.id)

    user_repo_result = await session.execute(
        select(User).where(User.telegram_id == message.from_user.id)
    )
    user = user_repo_result.scalar_one_or_none()
    if user:
        await _log_shop_open(session, user)

    text = (
        f"💰 <b>Ваш баланс: {balance} кредитов</b>\n\n"
        "Купить кредиты:\n"
        "Выберите пакет ниже 👇"
    )

    await message.answer(text, reply_markup=get_credits_keyboard())


@router.callback_query(lambda c: c.data.startswith("buy:"))
async def callback_buy_credits(callback: CallbackQuery, session) -> None:
    pack_id = callback.data.split(":")[1]
    pack = get_pack_by_id(pack_id)

    if not pack:
        await callback.answer("Пакет не найден", show_alert=True)
        return

    await callback.answer()

    text = (
        f"💳 <b>Покупка: {pack['label']}</b>\n\n"
        f"💰 Кредитов: {pack['credits']}\n"
        f"💵 Цена: {pack['price']} руб\n\n"
        "Оплата через Telegram Stars\n"
        "(комиссия ~4%)\n\n"
        "Нажмите кнопку ниже для оплаты 👇"
    )

    await callback.message.edit_text(text, reply_markup=get_credits_keyboard())


@router.callback_query(lambda c: c.data == "cancel_buy")
async def callback_cancel_buy(callback: CallbackQuery) -> None:
    await callback.answer()
    await callback.message.edit_text("Покупка отменена.")
    await callback.message.answer(
        "Выберите действие:", reply_markup=get_main_keyboard(callback.from_user.id)
    )
