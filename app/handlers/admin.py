import os

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext

from app.keyboards.admin_kb import remove_admin_keyboard
from app.states.admin_states import AdminStates

from app.services.database import (
    get_stats,
    set_setting,
    get_setting
)

from app.services.keys import count_keys


router = Router()

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")

ADMINS = [
    int(admin_id.strip())
    for admin_id in ADMIN_IDS_RAW.split(",")
    if admin_id.strip()
]


@router.message(lambda message: message.text == "📊 Статистика")
async def admin_stats(message: Message):
    if message.from_user.id not in ADMINS:
        return

    users, purchases = get_stats()

    await message.answer(
        f"📊 Статистика\n\n"
        f"👤 Пользователей: {users}\n"
        f"💳 Покупок: {purchases}"
    )


@router.message(lambda message: message.text == "🔑 Остаток строк")
async def admin_keys(message: Message):
    if message.from_user.id not in ADMINS:
        return

    count = count_keys()

    await message.answer(
        f"🔑 Осталось строк: {count}"
    )


@router.message(lambda message: message.text == "💲 Цена за 1 строку")
async def change_price_1_start(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await state.update_data(
        price_key="price_1",
        quantity="1"
    )

    await state.set_state(
        AdminStates.waiting_for_price
    )

    current_price = get_setting("price_1", "20")

    await message.answer(
        f"Введите новую цену для тарифа 1 строка.\n"
        f"Текущая цена: {current_price} USDT"
    )


@router.message(lambda message: message.text == "💲 Цена за 10 строк")
async def change_price_10_start(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await state.update_data(
        price_key="price_10",
        quantity="10"
    )

    await state.set_state(
        AdminStates.waiting_for_price
    )

    current_price = get_setting("price_10", "150")

    await message.answer(
        f"Введите новую цену для тарифа 10 строк.\n"
        f"Текущая цена: {current_price} USDT"
    )


@router.message(AdminStates.waiting_for_price)
async def change_price_save(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    try:
        price = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer(
            "Введите число, например: 20 или 150"
        )
        return

    data = await state.get_data()

    price_key = data["price_key"]
    quantity = data["quantity"]

    set_setting(
        price_key,
        str(price)
    )

    await message.answer(
        f"✅ Цена для тарифа {quantity} шт. изменена: {price} USDT"
    )

    await state.clear()


@router.message(lambda message: message.text == "📝 Изменить приветствие")
async def change_text_start(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_welcome
    )

    await message.answer(
        "Введите новый текст приветствия:"
    )


@router.message(AdminStates.waiting_for_welcome)
async def change_text_save(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    set_setting(
        "welcome_text",
        message.text
    )

    await message.answer(
        "✅ Приветствие обновлено"
    )

    await state.clear()


@router.message(lambda message: message.text == "📄 Изменить оферту")
async def change_offer_start(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_offer
    )

    current_offer = get_setting(
        "offer_text",
        "Оферта пока не задана."
    )

    await message.answer(
        f"Текущий текст оферты:\n\n{current_offer}\n\n"
        f"Введите новый текст оферты:"
    )


@router.message(AdminStates.waiting_for_offer)
async def change_offer_save(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    set_setting(
        "offer_text",
        message.text
    )

    await message.answer(
        "✅ Оферта обновлена"
    )

    await state.clear()


@router.message(lambda message: message.text == "📘 Изменить инструкцию")
async def change_instruction_start(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_instruction
    )

    current_instruction = get_setting(
        "instruction_text",
        "Инструкция пока не задана."
    )

    await message.answer(
        f"Текущий текст инструкции:\n\n{current_instruction}\n\n"
        f"Введите новый текст инструкции:"
    )


@router.message(AdminStates.waiting_for_instruction)
async def change_instruction_save(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    set_setting(
        "instruction_text",
        message.text
    )

    await message.answer(
        "✅ Инструкция обновлена"
    )

    await state.clear()


@router.message(lambda message: message.text == "📂 Загрузить строки")
async def upload_keys_start(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_keys
    )

    await message.answer(
        "📂 Отправьте txt-файл со строками."
    )


@router.message(AdminStates.waiting_for_keys)
async def upload_keys_file(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    if not message.document:
        await message.answer(
            "Отправьте именно txt-файл."
        )
        return

    document = message.document

    if not document.file_name.endswith(".txt"):
        await message.answer(
            "Нужен файл с расширением .txt"
        )
        return

    file = await message.bot.get_file(
        document.file_id
    )

    await message.bot.download_file(
        file.file_path,
        "data/keys.txt"
    )

    await message.answer(
        "✅ Строки успешно загружены"
    )

    await state.clear()


@router.message(lambda message: message.text == "❌ Закрыть админку")
async def close_admin_panel(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "Админ-панель закрыта.",
        reply_markup=remove_admin_keyboard
    )