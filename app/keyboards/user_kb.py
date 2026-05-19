from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

buy_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="💳 Купить",
                callback_data="buy"
            )
        ]
    ]
)

def check_payment_keyboard(invoice_id: int):

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check_{invoice_id}"
                )
            ]
        ]
    )