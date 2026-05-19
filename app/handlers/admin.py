import os
from aiogram.filters import Command
from app.keyboards.admin_kb import admin_keyboard
from app.services.database import get_stats
from aiogram.fsm.context import FSMContext
from app.states.admin_states import AdminStates

from app.services.database import (
    get_stats,
    set_setting,
    get_setting
)
from aiogram import Router
from aiogram.types import (
    Message,
    CallbackQuery
)



router = Router()

ADMINS = [1033823491]

@router.message(Command("admin"))
async def admin_panel(message: Message):

    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "⚙️ Админ-панель",
        reply_markup=admin_keyboard
    )

@router.callback_query(lambda c: c.data == "admin_keys")
async def admin_keys(callback: CallbackQuery):

    if callback.from_user.id not in ADMINS:
        return

    path = "data/keys.txt"

    if not os.path.exists(path):

        await callback.message.answer(
            "Файл ключей не найден"
        )

        return

    with open(path, "r", encoding="utf-8") as file:

        keys = file.readlines()

    count = len(keys)

    await callback.message.answer(
        f"🔑 Осталось ключей: {count}"
    )

    await callback.answer()

@router.callback_query(lambda c: c.data == "admin_stats")
async def admin_stats(callback: CallbackQuery):

    if callback.from_user.id not in ADMINS:
        return

    users, purchases = get_stats()

    await callback.message.answer(
        f"📊 Статистика\n\n"
        f"👤 Пользователей: {users}\n"
        f"💳 Покупок: {purchases}"
    )

    await callback.answer()

@router.callback_query(
    lambda c: c.data == "admin_upload_keys"
)
async def upload_keys_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_keys
    )

    await callback.message.answer(
        "📂 Отправьте txt файл с ключами"
    )

    await callback.answer()

@router.message(AdminStates.waiting_for_keys)
async def upload_keys_file(
    message: Message,
    state: FSMContext
):

    if message.from_user.id not in ADMINS:
        return

    if not message.document:

        await message.answer(
            "Отправьте именно txt файл"
        )

        return

    document = message.document

    if not document.file_name.endswith(".txt"):

        await message.answer(
            "Нужен txt файл"
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
        "✅ Ключи успешно загружены"
    )

    await state.clear()

@router.callback_query(lambda c: c.data in ["admin_change_price_1", "admin_change_price_10"])
async def change_price_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    quantity = callback.data.split("_")[-1]

    await state.update_data(
        price_key=f"price_{quantity}",
        quantity=quantity
    )

    await state.set_state(
        AdminStates.waiting_for_price
    )

    current_price = get_setting(f"price_{quantity}", "20" if quantity == "1" else "150")

    await callback.message.answer(
        f"Введите новую цену для тарифа {quantity} шт.\n"
        f"Текущая цена: {current_price} USDT"
    )

    await callback.answer()


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
        await message.answer("Введите число, например: 20 или 150")
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

async def change_price_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_price
    )

    await callback.message.answer(
        "Введите новую цену:"
    )

    await callback.answer()

@router.message(
    AdminStates.waiting_for_price
)
async def change_price_save(
    message: Message,
    state: FSMContext
):

    try:

        price = float(message.text)

    except:

        await message.answer(
            "Введите число"
        )

        return

    set_setting(
        "price",
        str(price)
    )

    await message.answer(
        f"✅ Цена изменена: {price} USDT"
    )

    await state.clear()

@router.callback_query(
    lambda c: c.data == "admin_change_text"
)
async def change_text_start(
    callback: CallbackQuery,
    state: FSMContext
):

    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_welcome
    )

    await callback.message.answer(
        "Введите новый текст приветствия"
    )

    await callback.answer()

@router.message(
    AdminStates.waiting_for_welcome
)
async def change_text_save(
    message: Message,
    state: FSMContext
):

    set_setting(
        "welcome_text",
        message.text
    )

    await message.answer(
        "✅ Приветствие обновлено"
    )

    await state.clear()