from __future__ import annotations

import asyncio

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from bot.config import load_settings
from bot.database import Database
from bot.handlers import create_router


async def main() -> None:
    settings = load_settings()
    bot = Bot(settings.bot_token, default=DefaultBotProperties(parse_mode="HTML"))
    database = Database(settings.database_path)
    await database.connect()
    await database.setup()

    dp = Dispatcher()
    dp.include_router(create_router(database, settings))

    try:
        await dp.start_polling(bot)
    finally:
        await database.close()


if __name__ == "__main__":
    asyncio.run(main())
