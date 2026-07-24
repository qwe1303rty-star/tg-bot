from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery

import logging
from bot.config import settings
from bot.database.repositories.credits import CreditsRepository
from bot.database.repositories.stats import StatsRepository
from bot.services.google_sheets import GoogleSheetsService
from bot.keyboards.admin import (
    get_admin_main_keyboard,
    get_admin_user_select_keyboard,
    get_admin_user_list_keyboard,
    get_admin_user_history_keyboard,
)
from bot.keyboards.main import get_main_keyboard

router = Router(name="admin")
logger = logging.getLogger(__name__)

USERS_PER_PAGE = 10
HISTORY_PER_PAGE = 10


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


@router.message(Command("give_credits"))
async def cmd_give_credits(message: Message, session) -> None:
    logger.info("give_credits: user_id=%s, admin_ids=%s", message.from_user.id, settings.admin_ids)

    if not _is_admin(message.from_user.id):
        logger.warning("give_credits: user %s is NOT admin", message.from_user.id)
        await message.answer(f"❌ Ты не админ. Твой ID: {message.from_user.id}")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /give_credits сумма\nПример: /give_credits 10")
        return

    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer("Сумма должна быть числом.")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть положительной.")
        return

    credits_repo = CreditsRepository(session)
    new_balance = await credits_repo.add_credits(
        message.from_user.id,
        amount,
        tx_type="admin",
        description=f"Выдано админом: +{amount}",
    )

    await message.answer(
        f"✅ Выдано {amount} кредитов.\n"
        f"💰 Баланс: {new_balance} кредитов"
    )


@router.message(Command("test_sheets"))
async def cmd_test_sheets(message: Message) -> None:
    logger.info("test_sheets: user_id=%s, admin_ids=%s", message.from_user.id, settings.admin_ids)

    if not _is_admin(message.from_user.id):
        logger.warning("test_sheets: user %s is NOT admin", message.from_user.id)
        await message.answer(f"❌ Ты не админ. Твой ID: {message.from_user.id}. Admin IDs: {settings.admin_ids}")
        return

    logger.info("test_sheets: user is admin, checking GOOGLE_SHEETS_URL")

    if not settings.google_sheets_url:
        logger.error("test_sheets: GOOGLE_SHEETS_URL is empty!")
        await message.answer("❌ GOOGLE_SHEETS_URL не задан в переменных Railway")
        return

    logger.info("test_sheets: GOOGLE_SHEETS_URL=%s", settings.google_sheets_url)
    await message.answer("⏳ Отправляю тестовую строку в Google Таблицу...")

    sheets = GoogleSheetsService(webhook_url=settings.google_sheets_url)
    result = await sheets.log_transaction(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        type_label="Тест",
        model="test_model",
        kie_credits=5.5,
        tg_credits=10,
        status="Успешно",
    )

    if result:
        await message.answer("✅ Тест прошёл! Проверь Google Таблицу — должна появиться строка с типом 'Тест'")
    else:
        await message.answer(
            "❌ Ошибка! Проверь:\n"
            "1. GOOGLE_SHEETS_URL задан в Railway?\n"
            "2. Apps Script задеплоен как 'Все'?\n"
            "3. В Apps Script есть функция doPost?"
        )


@router.message(F.text == "📊 Статистика")
async def cmd_admin_stats(message: Message, session) -> None:
    if not _is_admin(message.from_user.id):
        return

    stats = StatsRepository(session)

    total_users = await stats.count_total_users()
    new_today = await stats.count_new_users(days=1)
    new_week = await stats.count_new_users(days=7)
    total_gen = await stats.count_total_generations()
    gen_today = await stats.count_generations_today()
    video_gen = await stats.count_video_generations()
    providers = await stats.count_by_provider()

    providers_text = ""
    for prov, count in providers:
        providers_text += f"   {prov}: {count}\n"

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 <b>Пользователей</b>: {total_users}\n"
        f"   Новых сегодня: {new_today}\n"
        f"   Новых за неделю: {new_week}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎨 <b>Генераций</b>: {total_gen}\n"
        f"   Сегодня: {gen_today}\n"
        f"   Видео всего: {video_gen}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 <b>По моделям</b>:\n"
        f"{providers_text}"
    )

    await message.answer(
        text,
        reply_markup=get_admin_main_keyboard(),
    )


@router.callback_query(F.data == "admin:menu")
async def cb_admin_menu(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    stats = StatsRepository(session)
    total_users = await stats.count_total_users()
    new_today = await stats.count_new_users(days=1)
    new_week = await stats.count_new_users(days=7)
    total_gen = await stats.count_total_generations()
    gen_today = await stats.count_generations_today()
    video_gen = await stats.count_video_generations()
    providers = await stats.count_by_provider()

    providers_text = ""
    for prov, count in providers:
        providers_text += f"   {prov}: {count}\n"

    text = (
        f"📊 <b>Статистика бота</b>\n\n"
        f"👥 <b>Пользователей</b>: {total_users}\n"
        f"   Новых сегодня: {new_today}\n"
        f"   Новых за неделю: {new_week}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🎨 <b>Генераций</b>: {total_gen}\n"
        f"   Сегодня: {gen_today}\n"
        f"   Видео всего: {video_gen}\n\n"
        f"━━━━━━━━━━━━━━━━━━\n\n"
        f"🏆 <b>По моделям</b>:\n"
        f"{providers_text}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_main_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:noop")
async def cb_admin_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("admin:users:"))
async def cb_admin_users(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    page = int(callback.data.split(":")[-1])
    stats = StatsRepository(session)

    total_users = await stats.count_all_users()
    total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    users = await stats.get_all_users(limit=USERS_PER_PAGE, offset=page * USERS_PER_PAGE)

    lines = [f"👥 <b>Пользователи</b> ({total_users} всего)\n"]
    for i, user in enumerate(users, start=page * USERS_PER_PAGE + 1):
        name = f"@{user.username}" if user.username else user.first_name or "—"
        reg = user.created_at.strftime("%d.%m.%y")
        gen_count = await stats.count_user_generations(user.id)
        prem = "⭐" if user.is_premium else ""
        lines.append(
            f"{i}. {name} (ID: <code>{user.telegram_id}</code>) — {gen_count} ген. — {reg} {prem}"
        )

    text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_user_select_keyboard(users, page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:history_select")
async def cb_admin_history_select(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    stats = StatsRepository(session)
    total_users = await stats.count_all_users()
    total_pages = max(1, (total_users + USERS_PER_PAGE - 1) // USERS_PER_PAGE)

    users = await stats.get_all_users(limit=USERS_PER_PAGE, offset=0)

    lines = ["📜 <b>Выберите пользователя:</b>\n"]
    for i, user in enumerate(users, start=1):
        name = f"@{user.username}" if user.username else user.first_name or "—"
        gen_count = await stats.count_user_generations(user.id)
        lines.append(f"{i}. {name} (ID: <code>{user.telegram_id}</code>) — {gen_count} ген.")

    text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=get_admin_user_select_keyboard(users, 0, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:hist:"))
async def cb_admin_user_history(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    db_user_id = int(callback.data.split(":")[-1])
    stats = StatsRepository(session)

    user, gen_count = await stats.get_user_with_stats(db_user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    total_pages = max(1, (gen_count + HISTORY_PER_PAGE - 1) // HISTORY_PER_PAGE)

    generations = await stats.get_user_history(db_user_id, limit=HISTORY_PER_PAGE, offset=0)

    name = f"@{user.username}" if user.username else user.first_name or "—"

    lines = [f"📜 <b>История {name}</b> (ID: <code>{user.telegram_id}</code>)\n"]
    for gen in generations:
        date_str = gen.created_at.strftime("%d.%m %H:%M")
        prompt = gen.prompt[:50] + "..." if len(gen.prompt) > 50 else gen.prompt
        lines.append(f"• {prompt} — {gen.provider} — {date_str}")

    if not generations:
        lines.append("Нет генераций")

    text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=_history_keyboard(0, total_pages, db_user_id),
    )
    await callback.answer()


def _history_keyboard(page: int, total_pages: int, db_user_id: int):
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(
            text="◀️", callback_data=f"admin:hist_nav:{db_user_id}:{page - 1}"
        ))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="admin:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(
            text="▶️", callback_data=f"admin:hist_nav:{db_user_id}:{page + 1}"
        ))

    buttons = []
    if nav:
        buttons.append(nav)
    buttons.append([
        InlineKeyboardButton(text="← К списку", callback_data="admin:history_select"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


@router.callback_query(F.data.startswith("admin:hist_nav:"))
async def cb_admin_history_nav(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    parts = callback.data.split(":")
    db_user_id = int(parts[2])
    page = int(parts[3])

    stats = StatsRepository(session)
    user, gen_count = await stats.get_user_with_stats(db_user_id)
    if not user:
        await callback.answer("Пользователь не найден", show_alert=True)
        return

    total_pages = max(1, (gen_count + HISTORY_PER_PAGE - 1) // HISTORY_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    generations = await stats.get_user_history(
        db_user_id, limit=HISTORY_PER_PAGE, offset=page * HISTORY_PER_PAGE
    )

    name = f"@{user.username}" if user.username else user.first_name or "—"

    lines = [f"📜 <b>История {name}</b> (ID: <code>{user.telegram_id}</code>)\n"]
    for gen in generations:
        date_str = gen.created_at.strftime("%d.%m %H:%M")
        prompt = gen.prompt[:50] + "..." if len(gen.prompt) > 50 else gen.prompt
        lines.append(f"• {prompt} — {gen.provider} — {date_str}")

    if not generations:
        lines.append("Нет генераций")

    text = "\n".join(lines)

    await callback.message.edit_text(
        text,
        reply_markup=_history_keyboard(page, total_pages, db_user_id),
    )
    await callback.answer()
