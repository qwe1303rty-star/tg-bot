from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def get_admin_main_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📊 Общая статистика", callback_data="admin:stats"),
            ],
            [
                InlineKeyboardButton(text="👥 Пользователи", callback_data="admin:users:0"),
            ],
            [
                InlineKeyboardButton(text="📜 История запросов", callback_data="admin:history_select"),
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
                InlineKeyboardButton(text="← Назад", callback_data="admin:menu"),
            ],
        ]
    )


def get_admin_user_history_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    nav = []
    if page > 0:
        nav.append(InlineKeyboardButton(text="◀️", callback_data=f"admin:hist_page:{page - 1}"))
    nav.append(InlineKeyboardButton(text=f"{page + 1}/{total_pages}", callback_data="admin:noop"))
    if page < total_pages - 1:
        nav.append(InlineKeyboardButton(text="▶️", callback_data=f"admin:hist_page:{page + 1}"))
    return InlineKeyboardMarkup(
        inline_keyboard=[
            nav,
            [
                InlineKeyboardButton(text="← К списку", callback_data="admin:users:0"),
            ],
        ]
    )


def get_admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="← Назад", callback_data="admin:menu"),
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
        [InlineKeyboardButton(text="← Назад", callback_data="admin:menu")]
    )
    return InlineKeyboardMarkup(inline_keyboard=buttons)
