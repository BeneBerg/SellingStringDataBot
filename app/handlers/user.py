import os

from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from app.keyboards.admin_kb import admin_reply_keyboard


from app.services.database import (
    add_user,
    add_purchase,
    get_setting,
    add_invoice,
    get_invoice_from_db,
    mark_invoice_paid,
    mark_invoice_delivered,
    add_partner_referral
)

from app.services.cryptobot import (
    create_invoice,
    get_invoice
)

from app.services.keys import (
    get_keys_from_file,
    count_keys_in_file
)

from app.keyboards.user_kb import (
    products_keyboard,
    product_tariffs_keyboard,
    offer_keyboard,
    check_payment_keyboard
)

from app.services.products import (
    get_product,
    get_price_setting_key,
    get_instruction_setting_key
)

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")

ADMINS = [
    int(admin_id.strip())
    for admin_id in ADMIN_IDS_RAW.split(",")
    if admin_id.strip()
]
router = Router()



@router.message(CommandStart())
async def start_handler(message: Message):
    add_user(
        message.from_user.id,
        message.from_user.username
    )

    args = message.text.split()

    if len(args) > 1:
        start_param = args[1]

        if start_param.startswith("partner_"):
            add_partner_referral(
                start_param,
                message.from_user.id,
                message.from_user.username,
                message.from_user.first_name
            )

    if message.from_user.id in ADMINS:
        await message.answer(
            "⚙️ Админ-панель открыта.\n\nВыберите действие в меню снизу.",
            reply_markup=admin_reply_keyboard
        )
        return

    text = get_setting(
        "welcome_text",
        "Добро пожаловать.\n\nВыберите раздел для покупки."
    )

    await message.answer(
        text,
        reply_markup=products_keyboard()
    )

@router.callback_query(lambda c: c.data == "back_to_products")
async def back_to_products(callback: CallbackQuery):
    text = get_setting(
        "welcome_text",
        "Добро пожаловать.\n\nВыберите раздел для покупки."
    )

    await callback.message.edit_text(
        text,
        reply_markup=products_keyboard()
    )

    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("product:"))
async def product_handler(callback: CallbackQuery):
    product_code = callback.data.split(":")[1]

    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    price_1_key = get_price_setting_key(product_code, 1)
    price_10_key = get_price_setting_key(product_code, 10)

    price_1 = get_setting(
        price_1_key,
        product["default_price_1"]
    )

    price_10 = get_setting(
        price_10_key,
        product["default_price_10"]
    )

    await callback.message.edit_text(
        f"Вы выбрали: {product['title']}\n\n"
        f"Выберите вариант покупки:",
        reply_markup=product_tariffs_keyboard(
            product_code,
            price_1,
            price_10
        )
    )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("buy:"))
async def buy_handler(callback: CallbackQuery):
    _, product_code, quantity = callback.data.split(":")
    quantity = int(quantity)

    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    available_count = count_keys_in_file(product["file"])

    if available_count <= 0:
        await callback.answer(
            "❌ В данный момент товар отсутствует",
            show_alert=True
        )
        return

    if available_count < quantity:
        await callback.answer(
            f"❌ Недостаточно товара.\n\n"
            f"Доступно: {available_count}\n"
            f"Вы выбрали: {quantity}",
            show_alert=True
        )
        return

    offer_text = get_setting(
        "offer_text",
        "Перед оплатой ознакомьтесь с условиями оферты."
    )

    await callback.message.answer(
        f"{offer_text}\n\n"
        f"Раздел: {product['title']}\n"
        f"Количество строк: {quantity}",
        reply_markup=offer_keyboard(product_code, quantity)
    )

    await callback.answer()

@router.callback_query(lambda c: c.data == "cancel_offer")
async def cancel_offer(callback: CallbackQuery):
    await callback.message.edit_text(
        "❌ Покупка отменена."
    )

    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("accept_offer:"))
async def accept_offer_handler(callback: CallbackQuery):
    _, product_code, quantity = callback.data.split(":")
    quantity = int(quantity)

    product = get_product(product_code)

    if not product:
        await callback.answer(
            "Раздел не найден",
            show_alert=True
        )
        return

    price_key = get_price_setting_key(product_code, quantity)

    price = float(
        get_setting(
            price_key,
            product[f"default_price_{quantity}"]
        )
    )

    invoice = await create_invoice(
        price,
        callback.from_user.id
    )

    if not invoice.get("ok"):
        await callback.message.answer(
            f"❌ Ошибка создания счёта:\n{invoice}"
        )
        await callback.answer()
        return

    result = invoice["result"]

    pay_url = result["pay_url"]
    invoice_id = result["invoice_id"]

    add_invoice(
        invoice_id,
        callback.from_user.id,
        product_code,
        quantity,
        price
    )

    await callback.message.answer(
        f"💳 Оплатите заказ\n\n"
        f"Раздел: {product['title']}\n"
        f"Количество: {quantity}\n"
        f"Сумма: {price} USDT\n\n"
        f"{pay_url}",
        reply_markup=check_payment_keyboard(invoice_id)
    )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("check:") or c.data.startswith("check_"))
async def check_payment(callback: CallbackQuery):
    invoice_id = int(callback.data.split(":")[1])

    invoice_db = get_invoice_from_db(invoice_id)

    if not invoice_db:
        await callback.answer(
            "Счёт не найден в базе",
            show_alert=True
        )
        return

    if invoice_db["telegram_id"] != callback.from_user.id:
        await callback.answer(
            "Этот счёт принадлежит другому пользователю",
            show_alert=True
        )
        return

    if invoice_db["delivered"] == 1:
        await callback.answer(
            "По этому счёту данные уже были выданы",
            show_alert=True
        )
        return

    invoice_data = await get_invoice(invoice_id)

    if not invoice_data.get("ok"):
        await callback.message.answer(
            f"❌ Ошибка проверки оплаты:\n{invoice_data}"
        )
        await callback.answer()
        return

    items = invoice_data["result"]["items"]

    if not items:
        await callback.answer(
            "Счёт не найден",
            show_alert=True
        )
        return

    invoice = items[0]
    status = invoice["status"]

    # ВАЖНО:
    # для реальной работы должно быть invoice["status"]
    # для теста можно временно поставить status = "paid"

    if status != "paid":
        await callback.answer(
            "Оплата ещё не поступила",
            show_alert=True
        )
        return

    product_code = invoice_db["product_code"]
    quantity = invoice_db["quantity"]
    amount = invoice_db["amount"]

    product = get_product(product_code)

    if not product:
        await callback.message.answer(
            "❌ Раздел не найден. Обратитесь к администратору."
        )
        await callback.answer()
        return

    keys = get_keys_from_file(
        product["file"],
        quantity
    )

    if not keys:
        await callback.message.answer(
            f"❌ Недостаточно строк в разделе «{product['title']}».\n"
            f"Нужно строк: {quantity}"
        )
        await callback.answer()
        return

    add_purchase(
        callback.from_user.id,
        product_code,
        keys,
        amount,
        quantity
    )

    mark_invoice_paid(invoice_id)
    mark_invoice_delivered(invoice_id)

    instruction_text = get_setting(
        get_instruction_setting_key(product_code),
        product["default_instruction"]
    )

    keys_text = "\n".join(keys)

    await callback.message.answer(
        f"✅ Оплата подтверждена\n\n"
        f"Раздел: {product['title']}\n\n"
        f"Ваши данные:\n\n"
        f"<code>{keys_text}</code>\n\n"
        f"{instruction_text}"
    )

    await callback.answer()