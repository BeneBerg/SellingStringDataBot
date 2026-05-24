from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


buy_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Купить 1 ЛК",
                callback_data="buy_1"
            )
        ],
        [
            InlineKeyboardButton(
                text="💳 Купить 10 ЛК",
                callback_data="buy_10"
            )
        ]
    ]
)


def offer_keyboard(quantity: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принимаю",
                    callback_data=f"accept_offer_{quantity}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_offer"
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