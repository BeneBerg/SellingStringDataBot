import aiohttp
import os



CRYPTOBOT_TOKEN = os.getenv("CRYPTOBOT_TOKEN")
HEADERS = {
    "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN
}

BASE_URL = "https://pay.crypt.bot/api"


async def create_invoice(amount: float, telegram_id: int):

    headers = {
        "Crypto-Pay-API-Token": CRYPTOBOT_TOKEN
    }

    payload = {
        "asset": "USDT",
        "amount": amount,
        "description": "Purchase",
        "payload": str(telegram_id)
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/createInvoice",
            json=payload,
            headers=headers
        ) as response:

            data = await response.json()
            return data
        

async def get_invoice(invoice_id: int):

    url = f"{BASE_URL}/getInvoices"

    params = {
        "invoice_ids": invoice_id
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            params=params,
            headers=HEADERS
        ) as response:

            data = await response.json()

            return data