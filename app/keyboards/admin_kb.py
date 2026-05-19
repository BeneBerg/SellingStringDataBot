from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove
)


admin_reply_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [
            KeyboardButton(text="📊 Статистика"),
            KeyboardButton(text="🔑 Остаток строк")
        ],
        [
            KeyboardButton(text="💲 Цена за 1 строку"),
            KeyboardButton(text="💲 Цена за 10 строк")
        ],
        [
            KeyboardButton(text="📝 Изменить приветствие"),
            KeyboardButton(text="📂 Загрузить строки")
        ],
        [
            KeyboardButton(text="📄 Изменить оферту"),
            KeyboardButton(text="📘 Изменить инструкцию")
        ],
        [
            KeyboardButton(text="❌ Закрыть админку")
        ]
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие"
)


remove_admin_keyboard = ReplyKeyboardRemove()