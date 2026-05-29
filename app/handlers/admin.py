import os
import math

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext


from app.services.updater import (
    check_updates,
    start_update_in_background
)

from app.keyboards.admin_kb import (
    remove_admin_keyboard,
    texts_inline_keyboard,
    admin_products_keyboard,
    admin_product_prices_keyboard,
    clear_keys_confirm_keyboard,
    partner_users_keyboard,
    partner_user_detail_keyboard,
    referral_link_keyboard,
    referral_users_keyboard,
    referral_user_detail_keyboard,
    update_available_keyboard
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
    get_partner_referral_user_purchases,
    create_referral_link,
    get_referral_links_count,
    get_referral_link_by_page,
    get_referral_link_by_code
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

PARTNER_USERS_PER_PAGE = 15
REFERRAL_USERS_PER_PAGE = 15

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



@router.message(lambda message: message.text == "🔑 Остаток строк")
async def admin_keys(message: Message):
    if message.from_user.id not in ADMINS:
        return

    text = "🔑 Остаток строк по разделам:\n\n"

    for product_code, product in PRODUCTS.items():
        count = count_keys_in_file(product["file"])

        text += f"{product['title']}: {count}\n"

    await message.answer(text)



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



async def show_referral_page(message_or_callback, page):
    total_links = get_referral_links_count()

    if total_links <= 0:
        text = (
            "🔗 Реферальные ссылки\n\n"
            "Пока нет ни одной реферальной ссылки."
        )

        if isinstance(message_or_callback, Message):
            await message_or_callback.answer(text)
        else:
            await message_or_callback.message.edit_text(text)

        return

    total_pages = total_links

    if page < 1:
        page = 1

    if page > total_pages:
        page = total_pages

    referral = get_referral_link_by_page(page)

    if not referral:
        return

    referral_code = referral["referral_code"]

    total_users, total_purchases, total_amount = get_partner_referral_summary(
        referral_code
    )

    if isinstance(message_or_callback, Message):
        bot_info = await message_or_callback.bot.get_me()
    else:
        bot_info = await message_or_callback.bot.get_me()

    link = f"https://t.me/{bot_info.username}?start={referral_code}"

    text = (
        f"🔗 Реферальная ссылка\n\n"
        f"Название: <b>{referral['title']}</b>\n"
        f"Код: <code>{referral_code}</code>\n\n"
        f"{link}\n\n"
        f"📊 Статистика:\n\n"
        f"👥 Перешло пользователей: {total_users}\n"
        f"💳 Всего покупок: {total_purchases}\n"
        f"💰 Общая сумма: {total_amount} USDT\n\n"
        f"Страница {page} из {total_pages}"
    )

    keyboard = referral_link_keyboard(
        page,
        total_pages,
        referral_code
    )

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(
            text,
            reply_markup=keyboard
        )
    else:
        await message_or_callback.message.edit_text(
            text,
            reply_markup=keyboard
        )


@router.message(lambda message: message.text == "🔗 Партнёрка")
async def referrals_menu_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await show_referral_page(message, 1)

@router.callback_query(lambda callback: callback.data.startswith("ref_page:"))
async def referral_page_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    page = int(callback.data.split(":")[1])

    await show_referral_page(callback, page)

    await callback.answer()


@router.callback_query(lambda callback: callback.data == "ref_page_info")
async def referral_page_info(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(lambda callback: callback.data == "ref_add")
async def referral_add_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_referral_title
    )

    await callback.message.answer(
        "➕ Введите название новой реферальной ссылки.\n\n"
        "Например:\n"
        "Партнёр Иван\n"
        "Telegram-канал"
    )

    await callback.answer()


@router.message(AdminStates.waiting_for_referral_title)
async def referral_add_save(
    message: Message,
    state: FSMContext
):
    if message.from_user.id not in ADMINS:
        return

    title = message.text.strip()

    if not title:
        await message.answer(
            "Название не может быть пустым. Введите название рефералки."
        )
        return

    referral_code = create_referral_link(title)

    bot_info = await message.bot.get_me()

    link = f"https://t.me/{bot_info.username}?start={referral_code}"

    await message.answer(
        f"✅ Реферальная ссылка создана\n\n"
        f"Название: <b>{title}</b>\n"
        f"Код: <code>{referral_code}</code>\n\n"
        f"{link}"
    )

    await state.clear()

@router.callback_query(lambda callback: callback.data.startswith("ref_users:"))
async def referral_users_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    parts = callback.data.split(":")

    referral_code = parts[1]
    users_page = int(parts[2])

    if len(parts) >= 4:
        referral_page = int(parts[3])
    else:
        referral_page = 1

    referral = get_referral_link_by_code(referral_code)

    if not referral:
        await callback.answer(
            "Рефералка не найдена",
            show_alert=True
        )
        return

    users_count = get_partner_referral_users_count(
        referral_code
    )

    total_pages = max(
        1,
        math.ceil(users_count / REFERRAL_USERS_PER_PAGE)
    )

    users = get_partner_referral_users_page(
        referral_code,
        page=users_page,
        per_page=REFERRAL_USERS_PER_PAGE
    )

    text = (
        f"👥 Пользователи рефералки\n\n"
        f"Название: <b>{referral['title']}</b>\n"
        f"Код: <code>{referral_code}</code>\n\n"
        f"Всего пользователей: {users_count}\n"
        f"Страница {users_page} из {total_pages}"
    )

    await callback.message.edit_text(
        text,
        reply_markup=referral_users_keyboard(
            users,
            referral_code,
            users_page,
            total_pages,
            referral_page
        )
    )

    await callback.answer()


@router.callback_query(lambda callback: callback.data == "ref_users_page_info")
async def referral_users_page_info(callback: CallbackQuery):
    await callback.answer()

@router.callback_query(lambda callback: callback.data.startswith("ref_user:"))
async def referral_user_detail_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    _, referral_code, telegram_id, users_page, referral_page = callback.data.split(":")

    telegram_id = int(telegram_id)
    users_page = int(users_page)
    referral_page = int(referral_page)

    referral = get_referral_link_by_code(referral_code)

    if not referral:
        await callback.answer(
            "Рефералка не найдена",
            show_alert=True
        )
        return

    user = get_partner_referral_user_detail(
        referral_code,
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
        f"👤 Пользователь рефералки\n\n"
        f"Рефералка: <b>{referral['title']}</b>\n"
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
        reply_markup=referral_user_detail_keyboard(
            referral_code,
            users_page,
            referral_page
        )
    )

    await callback.answer()

@router.message(lambda message: message.text == "🔄 Обновление")
async def update_check_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return

    update_info = check_updates()

    if not update_info["ok"]:
        await message.answer(
            f"❌ Не удалось проверить обновления.\n\n"
            f"<code>{update_info['error']}</code>"
        )
        return

    if not update_info["has_update"]:
        current_commit = update_info.get("current_commit")

        text = "✅ Обновлений нет.\n\n"

        if current_commit:
            text += (
                f"Текущая версия:\n"
                f"<code>{current_commit['hash']}</code> — "
                f"{current_commit['message']}"
            )

        await message.answer(text)
        return

    remote_commit = update_info["remote_commit"]

    await message.answer(
        f"🔔 Доступно обновление\n\n"
        f"Новых коммитов: {update_info['behind_count']}\n\n"
        f"Последний коммит:\n"
        f"<code>{remote_commit['hash']}</code> — {remote_commit['message']}\n\n"
        f"Можно обновить бота.",
        reply_markup=update_available_keyboard()
    )

@router.callback_query(lambda callback: callback.data == "update_bot")
async def update_bot_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer(
            "Нет доступа",
            show_alert=True
        )
        return

    update_info = check_updates()

    if not update_info["ok"]:
        await callback.message.answer(
            f"❌ Не удалось проверить обновления.\n\n"
            f"<code>{update_info['error']}</code>"
        )
        await callback.answer()
        return

    if not update_info["has_update"]:
        await callback.message.answer(
            "✅ Обновлений нет. Бот уже на актуальной версии."
        )
        await callback.answer()
        return

    remote_commit = update_info["remote_commit"]

    log_file = start_update_in_background()

    await callback.message.answer(
        f"🔄 Обновление запущено.\n\n"
        f"Будет установлен коммит:\n"
        f"<code>{remote_commit['hash']}</code> — {remote_commit['message']}\n\n"
        f"Бот перезапустится автоматически.\n\n"
        f"Лог обновления на сервере:\n"
        f"<code>{log_file}</code>"
    )

    await callback.answer()