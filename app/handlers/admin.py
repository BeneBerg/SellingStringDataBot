import os
import math

from aiogram import Router
from aiogram.types import Message
from aiogram.fsm.context import FSMContext



from app.keyboards.admin_kb import (
    remove_admin_keyboard,
    texts_inline_keyboard,
    prices_inline_keyboard,
    partner_users_keyboard,
    partner_user_detail_keyboard,
    clear_keys_confirm_keyboard
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

from app.services.keys import append_keys_from_text, count_keys, clear_keys


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
        reply_markup=texts_inline_keyboard
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

@router.callback_query(lambda callback: callback.data == "admin_text_instruction")
async def change_instruction_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    await state.set_state(
        AdminStates.waiting_for_instruction
    )

    current_instruction = get_setting(
        "instruction_text",
        "Инструкция пока не задана."
    )

    await callback.message.answer(
        f"Текущий текст инструкции:\n\n"
        f"{current_instruction}\n\n"
        f"Введите новый текст инструкции:"
    )

    await callback.answer()

@router.message(lambda message: message.text == "💲 Цены")
async def admin_prices_menu(message: Message):
    if message.from_user.id not in ADMINS:
        return

    await message.answer(
        "💲 Выберите тариф, цену которого нужно изменить:",
        reply_markup=prices_inline_keyboard
    )

@router.callback_query(lambda callback: callback.data == "admin_price_1")
async def change_price_1_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    await state.update_data(
        price_key="price_1",
        quantity="1"
    )

    await state.set_state(
        AdminStates.waiting_for_price
    )

    current_price = get_setting("price_1", "20")

    await callback.message.answer(
        f"Введите новую цену для тарифа 1 строка.\n"
        f"Текущая цена: {current_price} USDT"
    )

    await callback.answer()


@router.callback_query(lambda callback: callback.data == "admin_price_10")
async def change_price_10_start(
    callback: CallbackQuery,
    state: FSMContext
):
    if callback.from_user.id not in ADMINS:
        return

    await state.update_data(
        price_key="price_10",
        quantity="10"
    )

    await state.set_state(
        AdminStates.waiting_for_price
    )

    current_price = get_setting("price_10", "150")

    await callback.message.answer(
        f"Введите новую цену для тарифа 10 строк.\n"
        f"Текущая цена: {current_price} USDT"
    )

    await callback.answer()

@router.message(lambda message: message.text == "🔑 Остаток строк")
async def admin_keys(message: Message):
    if message.from_user.id not in ADMINS:
        return

    count = count_keys()

    await message.answer(
        f"🔑 Осталось строк: {count}"
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

    downloaded_file = await message.bot.download_file(
        file.file_path
    )

    file_content = downloaded_file.read().decode("utf-8")

    before_count = count_keys()

    added_count = append_keys_from_text(file_content)

    after_count = count_keys()

    await message.answer(
        f"✅ Строки успешно добавлены\n\n"
        f"Было строк: {before_count}\n"
        f"Добавлено строк: {added_count}\n"
        f"Теперь строк: {after_count}"
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

PARTNER_REFERRAL_CODE = "partner_main"


@router.message(lambda message: message.text == "🔗 Партнёрская ссылка")
async def partner_link_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return

    bot_info = await message.bot.get_me()

    link = (
        f"https://t.me/{bot_info.username}"
        f"?start={PARTNER_REFERRAL_CODE}"
    )

    await message.answer(
        f"🔗 Партнёрская ссылка:\n\n"
        f"{link}\n\n"
        f"Эту ссылку можно выдать одному конкретному человеку. "
        f"Все пользователи, которые перейдут по ней, будут отображаться "
        f"в партнёрской статистике."
    )


@router.message(lambda message: message.text == "📊 Партнёрская статистика")
async def partner_stats_handler(message: Message):
    if message.from_user.id not in ADMINS:
        return

    total_users, total_purchases, total_amount = get_partner_referral_summary(
        PARTNER_REFERRAL_CODE
    )

    users = get_partner_referral_users(
        PARTNER_REFERRAL_CODE
    )

    text = (
        f"📊 Партнёрская статистика\n\n"
        f"🔗 Код ссылки: <code>{PARTNER_REFERRAL_CODE}</code>\n\n"
        f"👥 Перешло пользователей: {total_users}\n"
        f"💳 Всего покупок: {total_purchases}\n"
        f"💰 Общая сумма покупок: {total_amount} USDT\n\n"
    )

    if not users:
        text += "Пока по ссылке никто не переходил."
        await message.answer(text)
        return

    text += "👤 Пользователи:\n\n"

    for user in users[:20]:
        username = user["username"]
        first_name = user["first_name"]
        telegram_id = user["telegram_id"]
        purchases_count = user["purchases_count"]
        purchases_amount = user["purchases_amount"]

        if username:
            user_display = f"@{username}"
        elif first_name:
            user_display = first_name
        else:
            user_display = str(telegram_id)

        text += (
            f"• {user_display}\n"
            f"  ID: <code>{telegram_id}</code>\n"
            f"  Покупок: {purchases_count}\n"
            f"  Сумма: {purchases_amount} USDT\n\n"
        )

    if len(users) > 20:
        text += f"Показаны первые 20 пользователей из {len(users)}."

    await message.answer(text)

@router.message(lambda message: message.text == "🗑 Очистить строки")
async def clear_keys_start(message: Message):
    if message.from_user.id not in ADMINS:
        return

    count = count_keys()

    await message.answer(
        f"⚠️ Вы действительно хотите полностью очистить файл со строками?\n\n"
        f"Сейчас в файле строк: {count}\n\n"
        f"После подтверждения все оставшиеся строки будут удалены.",
        reply_markup=clear_keys_confirm_keyboard
    )

@router.callback_query(lambda callback: callback.data == "confirm_clear_keys")
async def confirm_clear_keys(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        return

    before_count = count_keys()

    clear_keys()

    await callback.message.edit_text(
        f"✅ Файл со строками очищен.\n\n"
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