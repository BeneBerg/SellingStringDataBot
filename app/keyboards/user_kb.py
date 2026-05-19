from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


buy_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Купить 1 строку",
                callback_data="buy_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Купить 10 строк",
                callback_data="buy_10"
            )
        ]
    ]
)


def check_payment_keyboard(invoice_id: int, quantity: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_{invoice_id}_{quantity}"
                )
            ]
        ]
    )