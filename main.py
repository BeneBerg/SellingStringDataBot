from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
load_dotenv()

import asyncio
import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import BotCommand

from app.handlers.user import router as user_router
from app.handlers.admin import router as admin_router
from app.services.database import init_db


BOT_TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)

dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(admin_router)


async def set_bot_commands():
    commands = [
        BotCommand(
            command="start",
            description="Запустить бота"
        ),
       
    ]

    await bot.set_my_commands(commands)


async def main():
    init_db()

    await set_bot_commands()

    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот остановлен вручную")