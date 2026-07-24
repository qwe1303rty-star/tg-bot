import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, Message, CallbackQuery

from bot.config import settings
from bot.database.repositories.admin_settings import AdminRepository
from bot.database.repositories.credits import CreditsRepository
from bot.database.repositories.stats import StatsRepository
from bot.database.repositories.user import UserRepository
from bot.keyboards.admin import (
    get_admin_dashboard_keyboard,
    get_admin_user_list_keyboard,
    get_admin_user_select_keyboard,
    get_admin_history_keyboard,
    get_admin_confirm_reset_keyboard,
    get_admin_broadcast_confirm_keyboard,
    get_admin_back_keyboard,
    get_admin_promos_keyboard,
    get_admin_prices_keyboard,
)
from bot.keyboards.main import get_main_keyboard
from bot.services.google_sheets import GoogleSheetsService

router = Router(name="admin")
logger = logging.getLogger(__name__)

USERS_PER_PAGE = 10
HISTORY_PER_PAGE = 10


class BroadcastState(StatesGroup):
    waiting_text = State()


class FindUserState(StatesGroup):
    waiting_id = State()


def _is_admin(user_id: int) -> bool:
    return user_id in settings.admin_ids


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{int(part / total * 100)}%"


async def _build_dashboard(session) -> tuple[str, InlineKeyboardMarkup]:
    stats = StatsRepository(session)
    admin_repo = AdminRepository(session)
    settings_obj = await admin_repo.get()

    total_users = await stats.count_total_users()
    new_today = await stats.count_new_users(days=1)
    new_week = await stats.count_new_users(days=7)

    total_gen = await stats.count_total_generations()
    gen_today = await stats.count_generations_today()

    used_limit = await stats.count_users_used_limit()
    opened_shop = await stats.count_users_opened_shop()
    paid = await stats.count_users_paid()

    revenue, expense = await stats.get_revenue_and_expense()

    limits_status = "🟢 ВКЛ" if settings_obj.limits_enabled else "🔴 ВЫКЛ"
    free_status = "🎁 ВКЛ" if settings_obj.free_mode else "🎁 ВЫКЛ"

    text = (
        f"📊 <b>Панель администратора</b>\n\n"

        f"👥 <b>Юзеры</b>\n"
        f"  За день: <b>{new_today}</b>\n"
        f"  За неделю: <b>{new_week}</b>\n"
        f"  Всего: <b>{total_users}</b>\n\n"

        f"💰 <b>Финансы</b>\n"
        f"  Выручка: <b>{revenue} руб</b>\n"
        f"  Расход: <b>{expense:.2f} руб</b>\n\n"

        f"📈 <b>Воронка конверсии</b>\n"
        f"  1️⃣ Зашли в бота: <b>{total_users} чел</b> (100%)\n"
        f"  2️⃣ Потратили лимит: <b>{used_limit} чел</b> ({_pct(used_limit, total_users)})\n"
        f"  3️⃣ Открыли магазин: <b>{opened_shop} чел</b> ({_pct(opened_shop, total_users)})\n"
        f"  4️⃣ Оплатили пакет: <b>{paid} чел</b> ({_pct(paid, total_users)})\n\n"

        f"⚙️ <b>Режим работы</b>\n"
        f"  Лимиты: {limits_status}\n"
        f"  Free Mode: {free_status}\n\n"

        f"🎨 <b>Генераций сегодня:</b> {gen_today}\n"
        f"🎨 <b>Всего:</b> {total_gen}"
    )

    return text, get_admin_dashboard_keyboard(settings_obj.limits_enabled, settings_obj.free_mode)


@router.message(Command("admin"))
async def cmd_admin(message: Message, session) -> None:
    if not _is_admin(message.from_user.id):
        return
    text, kb = await _build_dashboard(session)
    await message.answer(text, reply_markup=kb)


@router.message(F.text == "📊 Статистика")
async def btn_stats(message: Message, session) -> None:
    if not _is_admin(message.from_user.id):
        return
    text, kb = await _build_dashboard(session)
    await message.answer(text, reply_markup=kb)


@router.callback_query(F.data == "admin:dashboard")
async def cb_dashboard(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    text, kb = await _build_dashboard(session)
    await callback.message.edit_text(text, reply_markup=kb)
    await callback.answer()


@router.callback_query(F.data == "admin:noop")
async def cb_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "admin:toggle_limits")
async def cb_toggle_limits(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    admin_repo = AdminRepository(session)
    new_state = await admin_repo.toggle_limits()
    status = "включены" if new_state else "выключены"
    await callback.answer(f"Лимиты {status}", show_alert=True)
    text, kb = await _build_dashboard(session)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "admin:toggle_free")
async def cb_toggle_free(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    admin_repo = AdminRepository(session)
    new_state = await admin_repo.toggle_free_mode()
    if new_state:
        await callback.answer("Free Mode включён! Все лимиты сняты.", show_alert=True)
    else:
        await callback.answer("Free Mode выключен. Лимиты восстановлены.", show_alert=True)
    text, kb = await _build_dashboard(session)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "admin:reset_limits")
async def cb_reset_limits(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "⚠️ <b>Сбросить лимиты всем пользователям?</b>\n\n"
        "Все пользователи снова смогут генерировать по бесплатному лимиту.",
        reply_markup=get_admin_confirm_reset_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:reset_limits_confirm")
async def cb_reset_limits_confirm(callback: CallbackQuery, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    user_repo = UserRepository(session)
    count = await user_repo.reset_all_limits()
    await callback.answer(f"Лимиты сброшены для {count} пользователей", show_alert=True)
    text, kb = await _build_dashboard(session)
    await callback.message.edit_text(text, reply_markup=kb)


@router.callback_query(F.data == "admin:users:0")
async def cb_users_page(callback: CallbackQuery, session) -> None:
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
        reply_markup=get_admin_user_list_keyboard(page, total_pages),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:history_select")
async def cb_history_select(callback: CallbackQuery, session) -> None:
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
async def cb_user_history(callback: CallbackQuery, session) -> None:
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
        reply_markup=get_admin_history_keyboard(0, total_pages, db_user_id),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:hist_nav:"))
async def cb_history_nav(callback: CallbackQuery, session) -> None:
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
        reply_markup=get_admin_history_keyboard(page, total_pages, db_user_id),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:broadcast")
async def cb_broadcast(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(BroadcastState.waiting_text)
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\n"
        "Отправьте текст сообщения, которое хотите разослать всем пользователям.\n"
        "Поддерживается HTML-разметка.\n\n"
        "Для отмены нажмите /cancel",
    )
    await callback.answer()


@router.message(BroadcastState.waiting_text)
async def broadcast_receive(message: Message, state: FSMContext, session) -> None:
    if not _is_admin(message.from_user.id):
        return
    if message.text == "/cancel":
        await state.clear()
        text, kb = await _build_dashboard(session)
        await message.answer(text, reply_markup=kb)
        return

    await state.update_data(text=message.html_text)

    stats = StatsRepository(session)
    total = await stats.count_total_users()

    await message.answer(
        f"📢 <b>Подтвердите рассылку</b>\n\n"
        f"Получателей: <b>{total}</b>\n\n"
        f"Сообщение:\n{message.html_text}",
        reply_markup=get_admin_broadcast_confirm_keyboard(),
    )


@router.callback_query(F.data == "admin:broadcast_confirm")
async def cb_broadcast_confirm(callback: CallbackQuery, state: FSMContext, session) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return

    data = await state.get_data()
    await state.clear()

    broadcast_text = data.get("text", "")
    if not broadcast_text:
        await callback.answer("Нет текста для рассылки", show_alert=True)
        return

    stats = StatsRepository(session)
    users = await stats.get_all_users(limit=10000, offset=0)

    import bot.main as main_module
    _bot = main_module.bot_instance
    sent = 0
    for user in users:
        try:
            await _bot.send_message(user.telegram_id, broadcast_text, parse_mode="HTML")
            sent += 1
        except Exception:
            pass

    await callback.message.edit_text(
        f"✅ Рассылка завершена!\n"
        f"Отправлено: {sent}/{len(users)}",
    )
    await callback.answer()


@router.callback_query(F.data == "admin:find")
async def cb_find(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await state.set_state(FindUserState.waiting_id)
    await callback.message.edit_text(
        "🔍 <b>Найти пользователя по ID</b>\n\n"
        "Отправьте Telegram ID пользователя.\n\n"
        "Для отмены нажмите /cancel",
    )
    await callback.answer()


@router.message(FindUserState.waiting_id)
async def find_receive(message: Message, state: FSMContext, session) -> None:
    if not _is_admin(message.from_user.id):
        return
    if message.text == "/cancel":
        await state.clear()
        text, kb = await _build_dashboard(session)
        await message.answer(text, reply_markup=kb)
        return

    try:
        telegram_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Введите числовой Telegram ID")
        return

    await state.clear()

    stats = StatsRepository(session)
    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(telegram_id)

    if not user:
        await message.answer(
            f"❌ Пользователь с ID <code>{telegram_id}</code> не найден",
            reply_markup=get_admin_back_keyboard(),
        )
        return

    gen_count = await stats.count_user_generations(user.id)
    credits_repo = CreditsRepository(session)
    balance = await credits_repo.get_balance(user.telegram_id)

    name = f"@{user.username}" if user.username else user.first_name or "—"
    reg = user.created_at.strftime("%d.%m.%Y %H:%M")

    text = (
        f"👤 <b>{name}</b>\n\n"
        f"🆔 Telegram ID: <code>{user.telegram_id}</code>\n"
        f"📅 Регистрация: {reg}\n"
        f"🎨 Генераций: {gen_count}\n"
        f"💰 Кредитов: {balance}\n"
        f"⭐ Premium: {'Да' if user.is_premium else 'Нет'}\n\n"
        f"📊 <b>Лимиты</b>\n"
        f"  Фото: {user.generations_today}/{user.daily_limit}\n"
        f"  Видео: {user.video_generations_today}/{user.video_daily_limit}"
    )

    await message.answer(text, reply_markup=get_admin_back_keyboard())


@router.callback_query(F.data == "admin:promos")
async def cb_promos(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "🎟 <b>Промокоды</b>\n\n"
        "Управление промокодами:",
        reply_markup=get_admin_promos_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:promo_create")
async def cb_promo_create(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer("Функция в разработке", show_alert=True)


@router.callback_query(F.data == "admin:promo_list")
async def cb_promo_list(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer("Функция в разработке", show_alert=True)


@router.callback_query(F.data == "admin:prices")
async def cb_prices(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.message.edit_text(
        "💲 <b>Цены</b>\n\n"
        "Текущие цены (для справки):\n\n"
        "📸 <b>Фото:</b>\n"
        "  Pollinations: 0 кредитов\n"
        "  DALL-E: 6 кредитов\n"
        "  Stability: 6 кредитов\n"
        "  Flux: 6 кредитов\n\n"
        "🎬 <b>Видео:</b>\n"
        "  Grok: 10 кредитов\n"
        "  Seedance: 69 кредитов\n"
        "  Veo: 256 кредитов\n\n"
        "💰 <b>Пакеты:</b>\n"
        "  100 кредитов — 99 руб\n"
        "  300 кредитов — 249 руб\n"
        "  500 кредитов — 399 руб\n"
        "  1000 кредитов — 699 руб",
        reply_markup=get_admin_prices_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin:prices_"))
async def cb_prices_section(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer("Изменение цен в разработке", show_alert=True)


@router.callback_query(F.data == "admin:texts")
async def cb_texts(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer("Редактирование текстов в разработке", show_alert=True)


@router.callback_query(F.data == "admin:stars_link")
async def cb_stars_link(callback: CallbackQuery) -> None:
    if not _is_admin(callback.from_user.id):
        await callback.answer()
        return
    await callback.answer(
        "Оплата через Telegram Stars\n"
        "(интеграция в разработке)",
        show_alert=True,
    )


@router.message(Command("give_credits"))
async def cmd_give_credits(message: Message, session) -> None:
    logger.info("give_credits: user_id=%s, admin_ids=%s", message.from_user.id, settings.admin_ids)

    if not _is_admin(message.from_user.id):
        logger.warning("give_credits: user %s is NOT admin", message.from_user.id)
        await message.answer(f"❌ Ты не админ. Твой ID: {message.from_user.id}")
        return

    parts = message.text.split()
    if len(parts) < 2:
        await message.answer("Использование: /give_credits ID сумма\nПример: /give_credits 689105209 10")
        return

    try:
        target_id = int(parts[1])
        amount = int(parts[2])
    except (ValueError, IndexError):
        await message.answer("Использование: /give_credits ID сумма\nПример: /give_credits 689105209 10")
        return

    if amount <= 0:
        await message.answer("Сумма должна быть положительной.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(target_id)
    if not user:
        await message.answer(f"❌ Пользователь с ID {target_id} не найден")
        return

    credits_repo = CreditsRepository(session)
    new_balance = await credits_repo.add_credits(
        target_id,
        amount,
        tx_type="admin",
        description=f"Выдано админом: +{amount}",
    )

    await message.answer(
        f"✅ Выдано {amount} кредитов пользователю <code>{target_id}</code>.\n"
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
        await message.answer("✅ Тест прошёл! Проверь Google Таблицу")
    else:
        await message.answer(
            "❌ Ошибка! Проверь:\n"
            "1. GOOGLE_SHEETS_URL задан в Railway?\n"
            "2. Apps Script задеплоен как 'Все'?\n"
            "3. В Apps Script есть функция doPost?"
        )
