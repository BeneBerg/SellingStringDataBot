import os
import math

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext



from app.keyboards.admin_kb import (
    remove_admin_keyboard,
    texts_inline_keyboard,
    admin_products_keyboard,
    admin_product_prices_keyboard,
    clear_keys_confirm_keyboard,
    partner_users_keyboard,
    partner_user_detail_keyboard
)
from app.states.admin_states import AdminStates

from app.services.database import (
    get_stats,
    set_setting,
    get_setting,
    get_partner_referral_summary,
    get_partner_referral_users_page,
    get_partner_referral_users_count,
    get_partner_referral_user_detail,
    get_partner_referral_user_purchases
)

from app.services.keys import (
    append_keys_to_file,
    count_keys_in_file,
    clear_keys_file
)

from app.services.products import (
    PRODUCTS,
    get_product,
    get_product_title,
    get_price_setting_key,
    get_instruction_setting_key
)


router = Router()

PARTNER_REFERRAL_CODE = "partner_main"
PARTNER_USERS_PER_PAGE = 15

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

@router.message(lambda message: message.text == "🔗 Партнёрка")
async def partner_menu_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return

    bot_info = await message.bot.get_me()

    link = (
        f"https://t.me/{bot_info.username}"
        f"?start={PARTNER_REFERRAL_CODE}"
    )

    total_users, total_purchases, total_amount = get_partner_referral_summary(
        PARTNER_REFERRAL_CODE
    )

    users_count = get_partner_referral_users_count(
        PARTNER_REFERRAL_CODE
    )

    total_pages = max(
        1,
        math.ceil(users_count / PARTNER_USERS_PER_PAGE)
    )

    users = get_partner_referral_users_page(
        PARTNER_REFERRAL_CODE,
        page=1,
        per_page=PARTNER_USERS_PER_PAGE
    )

    text = (
        f"🔗 Партнёрская ссылка:\n\n"
        f"{link}\n\n"
        f"📊 Статистика по ссылке:\n\n"
        f"👥 Перешло пользователей: {total_users}\n"
        f"💳 Всего покупок: {total_purchases}\n"
        f"💰 Общая сумма: {total_amount} USDT\n\n"
        f"Ниже список пользователей по страницам."
    )

    await message.answer(
        text,
        reply_markup=partner_users_keyboard(
            users,
            page=1,
            total_pages=total_pages
        )
    )

@router.message(lambda message: message.text == "🛒 Разделы")
async def admin_products_menu(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "🛒 Выберите раздел для настройки цен:",
        reply_markup=admin_products_keyboard("product_prices")
    )

@router.callback_query(lambda callback: callback.data.startswith("product_prices:"))
async def admin_product_prices_menu(
    callback: CallbackQuery
):
    if callback.from_user.id not in ADMINS:
        return

    product_code = callback.data.split(":")[1]
    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    await callback.message.answer(
        f"💲 Настройка цен раздела:\n\n"
        f"{product['title']}",
        reply_markup=admin_product_prices_keyboard(product_code)
    )

    await callback.answer()

@router.callback_query(lambda callback: callback.data.startswith("partner_page_"))
async def partner_page_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    if callback.data == "partner_page_info":
        await callback.answer()
        return

    page = int(callback.data.split("_")[2])

    total_users, total_purchases, total_amount = get_partner_referral_summary(
        PARTNER_REFERRAL_CODE
    )

    users_count = get_partner_referral_users_count(
        PARTNER_REFERRAL_CODE
    )

    total_pages = max(
        1,
        math.ceil(users_count / PARTNER_USERS_PER_PAGE)
    )

    users = get_partner_referral_users_page(
        PARTNER_REFERRAL_CODE,
        page=page,
        per_page=PARTNER_USERS_PER_PAGE
    )

    bot_info = await callback.bot.get_me()

    link = (
        f"https://t.me/{bot_info.username}"
        f"?start={PARTNER_REFERRAL_CODE}"
    )

    text = (
        f"🔗 Партнёрская ссылка:\n\n"
        f"{link}\n\n"
        f"📊 Статистика по ссылке:\n\n"
        f"👥 Перешло пользователей: {total_users}\n"
        f"💳 Всего покупок: {total_purchases}\n"
        f"💰 Общая сумма: {total_amount} USDT\n\n"
        f"Страница {page} из {total_pages}."
    )

    await callback.message.edit_text(
        text,
        reply_markup=partner_users_keyboard(
            users,
            page=page,
            total_pages=total_pages
        )
    )

    await callback.answer()

@router.message(lambda message: message.text == "🔑 Остаток строк")
async def admin_keys(message: Message):
    if message.from_user.id not in ADMINS:
        return

    text = "🔑 Остаток строк по разделам:\n\n"

    for product_code, product in PRODUCTS.items():
        count = count_keys_in_file(product["file"])

        text += f"{product['title']}: {count}\n"

    await message.answer(text)

@router.callback_query(lambda callback: callback.data.startswith("partner_user_"))
async def partner_user_detail_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    parts = callback.data.split("_")

    telegram_id = int(parts[2])
    page = int(parts[3])

    user = get_partner_referral_user_detail(
        PARTNER_REFERRAL_CODE,
        telegram_id
    )

    if not user:
        await callback.answer(
            "Пользователь не найден",
            show_alert=True
        )
        return

    purchases = get_partner_referral_user_purchases(
        telegram_id
    )

    username = user["username"]
    first_name = user["first_name"]

    if username:
        user_display = f"@{username}"
    elif first_name:
        user_display = first_name
    else:
        user_display = str(telegram_id)

    text = (
        f"👤 Пользователь партнёрской ссылки\n\n"
        f"Пользователь: {user_display}\n"
        f"ID: <code>{telegram_id}</code>\n"
        f"Дата перехода: {user['created_at']}\n\n"
        f"💳 Покупок: {user['purchases_count']}\n"
        f"💰 Сумма покупок: {user['purchases_amount']} USDT\n\n"
    )

    if purchases:
        text += "🧾 Последние покупки:\n\n"

        for purchase in purchases[:10]:
            text += (
                f"• Покупка #{purchase['id']}\n"
                f"  Количество: {purchase['quantity']}\n"
                f"  Сумма: {purchase['amount']} USDT\n"
                f"  Дата: {purchase['created_at']}\n\n"
            )
    else:
        text += "Покупок пока нет."

    await callback.message.edit_text(
        text,
        reply_markup=partner_user_detail_keyboard(page)
    )

    await callback.answer()

@router.message(lambda message: message.text == "📝 Тексты")
async def admin_texts_menu(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "📝 Выберите, какой текст нужно изменить:",
        reply_markup=texts_inline_keyboard()
    )

@router.callback_query(lambda callback: callback.data == "admin_text_welcome")
async def change_welcome_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_welcome
    )

    current_text = get_setting(
        "welcome_text",
        "Приветствие пока не задано."
    )

    await callback.message.answer(
        f"Текущий текст приветствия:\n\n"
        f"{current_text}\n\n"
        f"Введите новый текст приветствия:"
    )

    await callback.answer()

@router.callback_query(lambda callback: callback.data == "admin_text_offer")
async def change_offer_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_offer
    )

    current_offer = get_setting(
        "offer_text",
        "Оферта пока не задана."
    )

    await callback.message.answer(
        f"Текущий текст оферты:\n\n"
        f"{current_offer}\n\n"
        f"Введите новый текст оферты:"
    )

    await callback.answer()

@router.callback_query(lambda callback: callback.data.startswith("admin_instruction:"))
async def change_instruction_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    product_code = callback.data.split(":")[1]
    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    instruction_key = get_instruction_setting_key(product_code)

    await state.update_data(
        instruction_key=instruction_key,
        product_code=product_code
    )

    await state.set_state(
        AdminStates.waiting_for_instruction
    )

    current_instruction = get_setting(
        instruction_key,
        product["default_instruction"]
    )

    await callback.message.answer(
        f"Текущая инструкция раздела «{product['title']}»:\n\n"
        f"{current_instruction}\n\n"
        f"Введите новую инструкцию:"
    )

    await callback.answer()


@router.callback_query(lambda callback: callback.data.startswith("admin_price:"))
async def change_product_price_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    _, product_code, quantity = callback.data.split(":")
    quantity = int(quantity)

    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    price_key = get_price_setting_key(
        product_code,
        quantity
    )

    await state.update_data(
        price_key=price_key,
        quantity=quantity,
        product_code=product_code
    )

    await state.set_state(
        AdminStates.waiting_for_price
    )

    current_price = get_setting(
        price_key,
        product[f"default_price_{quantity}"]
    )

    await callback.message.answer(
        f"Введите новую цену.\n\n"
        f"Раздел: {product['title']}\n"
        f"Количество строк: {quantity}\n"
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
        await message.answer(
            "Введите число, например: 20 или 150"
        )
        return

    data = await state.get_data()

    price_key = data["price_key"]
    quantity = data["quantity"]
    product_code = data["product_code"]

    product = get_product(product_code)

    set_setting(
        price_key,
        str(price)
    )

    await message.answer(
        f"✅ Цена изменена\n\n"
        f"Раздел: {product['title']}\n"
        f"Количество строк: {quantity}\n"
        f"Новая цена: {price} USDT"
    )

    await state.clear()



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


@router.message(AdminStates.waiting_for_instruction)
async def change_instruction_save(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    data = await state.get_data()

    instruction_key = data.get("instruction_key")
    product_code = data.get("product_code")

    product = get_product(product_code)

    if not instruction_key or not product:
        await message.answer(
            "❌ Не удалось определить раздел. Попробуйте снова."
        )
        await state.clear()
        return

    set_setting(
        instruction_key,
        message.text
    )

    await message.answer(
        f"✅ Инструкция обновлена\n\n"
        f"Раздел: {product['title']}"
    )

    await state.clear()


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

    data = await state.get_data()
    product_code = data.get("product_code")

    product = get_product(product_code)

    if not product:
        await message.answer(
            "❌ Раздел не найден. Попробуйте загрузить файл заново."
        )
        await state.clear()
        return

    file = await message.bot.get_file(
        document.file_id
    )

    downloaded_file = await message.bot.download_file(
        file.file_path
    )

    file_content = downloaded_file.read().decode("utf-8")

    before_count = count_keys_in_file(product["file"])

    added_count = append_keys_to_file(
        product["file"],
        file_content
    )

    after_count = count_keys_in_file(product["file"])

    await message.answer(
        f"✅ Строки успешно добавлены\n\n"
        f"Раздел: {product['title']}\n"
        f"Было строк: {before_count}\n"
        f"Добавлено строк: {added_count}\n"
        f"Теперь строк: {after_count}"
    )

    await state.clear()

@router.message(lambda message: message.text == "📂 Загрузить строки")
async def upload_keys_choose_product(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "📂 Выберите раздел, в который нужно добавить строки:",
        reply_markup=admin_products_keyboard("upload_keys")
    )

@router.callback_query(lambda callback: callback.data.startswith("upload_keys:"))
async def upload_keys_product_selected(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    product_code = callback.data.split(":")[1]
    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    await state.update_data(
        product_code=product_code
    )

    await state.set_state(
        AdminStates.waiting_for_keys
    )

    await callback.message.answer(
        f"📂 Отправьте txt-файл со строками для раздела:\n\n"
        f"{product['title']}"
    )

    await callback.answer()





@router.message(lambda message: message.text == "❌ Закрыть админку")
async def close_admin_panel(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "Админ-панель закрыта.",
        reply_markup=remove_admin_keyboard
    )



@router.message(lambda message: message.text == "🗑 Очистить строки")
async def clear_keys_choose_product(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "🗑 Выберите раздел, в котором нужно очистить строки:",
        reply_markup=admin_products_keyboard("clear_keys")
    )

@router.callback_query(lambda callback: callback.data.startswith("clear_keys:"))
async def clear_keys_product_selected(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    product_code = callback.data.split(":")[1]

    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    count = count_keys_in_file(product["file"])

    await callback.message.answer(
        f"⚠️ Вы действительно хотите очистить строки в разделе?\n\n"
        f"Раздел: {product['title']}\n"
        f"Сейчас строк: {count}\n\n"
        f"После подтверждения все строки этого раздела будут удалены.",
        reply_markup=clear_keys_confirm_keyboard(product_code)
    )

    await callback.answer()

@router.callback_query(lambda callback: callback.data.startswith("confirm_clear_keys:"))
async def confirm_clear_keys(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    product_code = callback.data.split(":")[1]

    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    before_count = count_keys_in_file(product["file"])

    clear_keys_file(product["file"])

    await callback.message.edit_text(
        f"✅ Файл со строками очищен.\n\n"
        f"Раздел: {product['title']}\n"
        f"Удалено строк: {before_count}\n"
        f"Теперь строк: 0"
    )

    await callback.answer()



@router.callback_query(lambda callback: callback.data == "cancel_clear_keys")
async def cancel_clear_keys(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    await callback.message.edit_text(
        "❌ Очистка файла отменена."
    )

    await callback.answer()