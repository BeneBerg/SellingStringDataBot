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

from app.services.keys import get_keys

from app.keyboards.user_kb import (
    buy_keyboard,
    offer_keyboard,
    check_payment_keyboard
)

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")

ADMINS = [
    int(admin_id.strip())
    for admin_id in ADMIN_IDS_RAW.split(",")
    if admin_id.strip()
]
router = Router()


def get_price_by_quantity(quantity: int) -> float:
    if quantity == 1:
        return float(get_setting("price_1", "20"))

    if quantity == 10:
        return float(get_setting("price_10", "150"))

    raise ValueError("Некорректное количество")


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
        "Добро пожаловать.\n\nВыберите нужный вариант покупки."
    )

    await message.answer(
        text,
        reply_markup=buy_keyboard
    )


@router.callback_query(lambda c: c.data in ["buy_1", "buy_10"])
async def buy_handler(callback: CallbackQuery):
    quantity = int(callback.data.split("_")[1])

    offer_text = get_setting(
        "offer_text",
        "Перед оплатой ознакомьтесь с условиями оферты."
    )

    await callback.message.answer(
        offer_text,
        reply_markup=offer_keyboard(quantity)
    )

    await callback.answer()

@router.callback_query(lambda c: c.data == "cancel_offer")
async def cancel_offer(callback: CallbackQuery):
    await callback.message.answer(
        "Покупка отменена."
    )

    await callback.answer()

@router.callback_query(lambda c: c.data.startswith("accept_offer_"))
async def accept_offer_handler(callback: CallbackQuery):
    quantity = int(callback.data.split("_")[2])
    price = get_price_by_quantity(quantity)

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
        quantity,
        price
    )

    await callback.message.answer(
        f"💳 Оплатите заказ\n\n"
        f"Количество: {quantity}\n"
        f"Сумма: {price} USDT\n\n"
        f"{pay_url}",
        reply_markup=check_payment_keyboard(invoice_id, quantity)
    )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("check_"))
async def check_payment(callback: CallbackQuery):
    parts = callback.data.split("_")

    invoice_id = int(parts[1])

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

    quantity = invoice_db["quantity"]
    amount = invoice_db["amount"]

    keys = get_keys(quantity)

    if not keys:
        await callback.message.answer(
            f"❌ Недостаточно строк в файле. Нужно: {quantity}"
        )
        await callback.answer()
        return

    add_purchase(
        callback.from_user.id,
        keys,
        amount,
        quantity
    )

    mark_invoice_paid(invoice_id)
    mark_invoice_delivered(invoice_id)

    keys_text = "\n".join(keys)

    instruction_text = get_setting(
        "instruction_text",
        "Инструкция:\n\nСкопируйте полученные данные и используйте их по назначению."
    )

    await callback.message.answer(
        f"✅ Оплата подтверждена\n\n"
        f"Ваши данные:\n\n"
        f"<code>{keys_text}</code>\n\n"
        f"{instruction_text}"
    )

    await callback.answer()