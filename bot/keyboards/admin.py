from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def _pct(part: int, total: int) -> str:
    if total == 0:
        return "0%"
    return f"{int(part / total * 100)}%"


def get_admin_dashboard_keyboard(limits_enabled: bool, free_mode: bool) -> InlineKeyboardMarkup:
    limits_label = "🟢 Лимиты ВКЛ" if limits_enabled else "🔴 Лимиты ВЫКЛ"
    free_label = "🎁 Free Mode ВЫКЛ" if free_mode else "🎁 Free Mode ВКЛ"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=limits_label, callback_data="admin:toggle_limits"),
                InlineKeyboardButton(text=free_label, callback_data="admin:toggle_free"),
            ],
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="admin:broadcast"),
                InlineKeyboardButton(text="🎟 Промокоды", callback_data="admin:promos"),
            ],
            [
                InlineKeyboardButton(text="👥 Все юзеры", callback_data="admin:users:0"),
                InlineKeyboardButton(text="🔍 Найти по ID", callback_data="admin:find"),
            ],
            [
                InlineKeyboardButton(text="💲 Цены", callback_data="admin:prices"),
                InlineKeyboardButton(text="📝 Тексты", callback_data="admin:texts"),
            ],
            [
                InlineKeyboardButton(text="⭐ Ссылка на Звезды", callback_data="admin:stars_link"),
            ],
            [
                InlineKeyboardButton(text="🎁 Сбросить лимиты всем", callback_data="admin:reset_limits"),
            ],
        ]
    )


def get_admin_user_list_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"admin:users:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="admin:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"admin:users:{page + 1}"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            nav,
            [
                InlineKeyboardButton(text="← Назад", callback_data="admin:dashboard"),
            ],
        ]
    )


def get_admin_user_select_keyboard(
    users: list, page: int, total_pages: int
) -> InlineKeyboardMarkup:
    buttons = []
    for user in users:
        name = user.username or user.first_name or str(user.telegram_id)
        buttons.append(
            [InlineKeyboardButton(
                text=f"@{name} (ID: {user.telegram_id})",
                callback_data=f"admin:hist:{user.id}",
            )]
        )
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"admin:users:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="admin:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"admin:users:{page + 1}"))
    if nav:
        buttons.append(nav)
    buttons.append(
        [InlineKeyboardButton(text="← Назад", callback_data="admin:dashboard")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="← Назад", callback_data="admin:dashboard"),
            ],
        ]
    )


def get_admin_confirm_reset_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да, сбросить", callback_data="admin:reset_limits_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="admin:dashboard"),
            ],
        ]
    )


def get_admin_broadcast_confirm_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Отправить", callback_data="admin:broadcast_confirm"),
                InlineKeyboardButton(text="❌ Отмена", callback_data="admin:dashboard"),
            ],
        ]
    )


def get_admin_history_keyboard(page: int, total_pages: int, db_user_id: int):
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
        InlineKeyboardButton(text="← К списку", callback_data="admin:users:0"),
    ])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_admin_promos_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="➕ Создать промокод", callback_data="admin:promo_create"),
            ],
            [
                InlineKeyboardButton(text="📋 Список промокодов", callback_data="admin:promo_list"),
            ],
            [
                InlineKeyboardButton(text="← Назад", callback_data="admin:dashboard"),
            ],
        ]
    )


def get_admin_prices_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📸 Фото модели", callback_data="admin:prices_photo"),
            ],
            [
                InlineKeyboardButton(text="🎬 Видео модели", callback_data="admin:prices_video"),
            ],
            [
                InlineKeyboardButton(text="💰 Пакеты кредитов", callback_data="admin:prices_credits"),
            ],
            [
                InlineKeyboardButton(text="← Назад", callback_data="admin:dashboard"),
            ],
        ]
    )
