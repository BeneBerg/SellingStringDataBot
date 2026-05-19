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
                text="🔑 Остаток ключей",
                callback_data="admin_keys"
            )
        ],

        [
            InlineKeyboardButton(
                text="💲 Изменить цену",
                callback_data="admin_change_price"
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
                text="📂 Загрузить ключи",
                callback_data="admin_upload_keys"
            )
        ]
    ]
)