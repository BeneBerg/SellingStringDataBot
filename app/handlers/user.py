from aiogram import Router
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from app.services.database import add_user
from app.services.database import add_purchase

from app.services.database import (
    add_user,
    add_purchase,
    get_setting
)

from app.services.cryptobot import (
    create_invoice,
    get_invoice
)

from app.services.keys import get_key

from app.keyboards.user_kb import (
    buy_keyboard,
    check_payment_keyboard
)

router = Router()
price = float(
        get_setting("price")
    )



@router.message(CommandStart())
async def start_handler(message: Message):

    add_user(
        message.from_user.id,
        message.from_user.username
    )
    
    text = get_setting(
    "welcome_text"
)

    await message.answer(
        text,
        reply_markup=buy_keyboard
    )


@router.callback_query(lambda c: c.data == "buy")
async def buy_handler(callback: CallbackQuery):

    

    invoice = await create_invoice(
    price,
    callback.from_user.id
)

    result = invoice["result"]

    pay_url = result["pay_url"]
    invoice_id = result["invoice_id"]

    await callback.message.answer(
        f"💳 Оплатите заказ:\n\n{pay_url}",
        reply_markup=check_payment_keyboard(invoice_id)
    )

    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("check_"))
async def check_payment(callback: CallbackQuery):

    invoice_id = int(callback.data.split("_")[1])

    invoice_data = await get_invoice(invoice_id)

    items = invoice_data["result"]["items"]

    if not items:

        await callback.answer(
            "Счёт не найден",
            show_alert=True
        )

        return

    invoice = items[0]
    
    status = invoice["status"]
    
    if status != "paid":

        await callback.answer(
            "Оплата ещё не поступила",
            show_alert=True
        )

        return

    key = get_key()
   

    if not key:

        await callback.message.answer(
            "❌ Ключи закончились"
        )

        return
    
     
    add_purchase(
            callback.from_user.id,
            key,
            price
        )

    await callback.message.answer(
        f"✅ Оплата подтверждена\n\n"
        f"Ваш ключ:\n\n"
        f"<code>{key}</code>"
    )

    await callback.answer()

