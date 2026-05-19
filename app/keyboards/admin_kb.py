from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton
)


admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📊 Статистика",
                callback_data="admin_stats"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔑 Остаток строк",
                callback_data="admin_keys"
            )
        ],
        [
            InlineKeyboardButton(
                text="💲 Цена за 1 строку",
                callback_data="admin_change_price_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="💲 Цена за 10 строк",
                callback_data="admin_change_price_10"
            )
        ],
        [
            InlineKeyboardButton(
                text="📝 Изменить приветствие",
                callback_data="admin_change_text"
            )
        ],
        [
            InlineKeyboardButton(
                text="📂 Загрузить строки",
                callback_data="admin_upload_keys"
            )
        ]
    ]
)