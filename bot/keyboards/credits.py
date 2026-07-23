from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

CREDIT_PACKS = [
    {"id": "credits_100", "credits": 100, "price": 99, "label": "100 кредитов — 99 руб"},
    {"id": "credits_300", "credits": 300, "price": 249, "label": "300 кредитов — 249 руб"},
    {"id": "credits_500", "credits": 500, "price": 399, "label": "500 кредитов — 399 руб"},
    {"id": "credits_1000", "credits": 1000, "price": 699, "label": "1000 кредитов — 699 руб"},
]


def get_credits_keyboard() -> InlineKeyboardMarkup:
    buttons = []
    for pack in CREDIT_PACKS:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=pack["label"],
                    callback_data=f"buy:{pack['id']}",
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def get_pack_by_id(pack_id: str) -> dict | None:
    for pack in CREDIT_PACKS:
        if pack["id"] == pack_id:
            return pack
    return None
