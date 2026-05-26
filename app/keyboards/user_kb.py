from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from app.services.products import PRODUCTS


def products_keyboard():
    keyboard = []

    for product_code, product in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                text=product["title"],
                callback_data=f"product:{product_code}"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def product_tariffs_keyboard(product_code: str, price_1, price_10):
    product = PRODUCTS[product_code]

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"{product['button_1']} ({price_1} USDT)",
                    callback_data=f"buy:{product_code}:1"
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"{product['button_10']} ({price_10} USDT)",
                    callback_data=f"buy:{product_code}:10"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к разделам",
                    callback_data="back_to_products"
                )
            ]
        ]
    )


def offer_keyboard(product_code: str, quantity: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принимаю",
                    callback_data=f"accept_offer:{product_code}:{quantity}"
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


def check_payment_keyboard(invoice_id: int):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Проверить оплату",
                    callback_data=f"check:{invoice_id}"
                )
            ]
        ]
    )