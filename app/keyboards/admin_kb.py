from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)

from app.services.products import PRODUCTS


admin_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="🔗 Партнёрка")
        ],
        [
            KeyboardButton(text="🛒 Разделы"),
            KeyboardButton(text="📝 Тексты")
        ],
        [
            KeyboardButton(text="📂 Загрузить строки"),
            KeyboardButton(text="🔑 Остаток строк")
        ],
        [
            KeyboardButton(text="🗑 Очистить строки")
        ],
        [
            KeyboardButton(text="❌ Закрыть админку")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)


remove_admin_keyboard = ReplyKeyboardRemove()


def admin_products_keyboard(action: str):
    keyboard = []

    for product_code, product in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                text=product["title"],
                callback_data=f"{action}:{product_code}"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def clear_keys_confirm_keyboard(product_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Да, очистить",
                    callback_data=f"confirm_clear_keys:{product_code}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="❌ Отмена",
                    callback_data="cancel_clear_keys"
                )
            ]
        ]
    )


def admin_product_prices_keyboard(product_code: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="💲 Цена за 1 строку",
                    callback_data=f"admin_price:{product_code}:1"
                )
            ],
            [
                InlineKeyboardButton(
                    text="💲 Цена за 10 строк",
                    callback_data=f"admin_price:{product_code}:10"
                )
            ]
        ]
    )


def texts_inline_keyboard():
    keyboard = [
        [
            InlineKeyboardButton(
                text="📝 Приветствие",
                callback_data="admin_text_welcome"
            )
        ],
        [
            InlineKeyboardButton(
                text="📄 Общая оферта",
                callback_data="admin_text_offer"
            )
        ]
    ]

    for product_code, product in PRODUCTS.items():
        keyboard.append([
            InlineKeyboardButton(
                text=f"📘 Инструкция: {product['title']}",
                callback_data=f"admin_instruction:{product_code}"
            )
        ])

    return InlineKeyboardMarkup(
        inline_keyboard=keyboard
    )


def partner_users_keyboard(users, page, total_pages):
    buttons = []

    for user in users:
        telegram_id = user["telegram_id"]
        username = user.get("username")
        first_name = user.get("first_name")

        if username:
            button_text = f"@{username}"
        elif first_name:
            button_text = first_name
        else:
            button_text = str(telegram_id)

        buttons.append([
            InlineKeyboardButton(
                text=button_text,
                callback_data=f"partner_user_{telegram_id}_{page}"
            )
        ])

    navigation_buttons = []

    if page > 1:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="⬅️ Назад",
                callback_data=f"partner_page_{page - 1}"
            )
        )

    navigation_buttons.append(
        InlineKeyboardButton(
            text=f"{page}/{total_pages}",
            callback_data="partner_page_info"
        )
    )

    if page < total_pages:
        navigation_buttons.append(
            InlineKeyboardButton(
                text="➡️ Далее",
                callback_data=f"partner_page_{page + 1}"
            )
        )

    buttons.append(navigation_buttons)

    return InlineKeyboardMarkup(
        inline_keyboard=buttons
    )


def partner_user_detail_keyboard(page):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅️ Назад к списку",
                    callback_data=f"partner_page_{page}"
                )
            ]
        ]
    )