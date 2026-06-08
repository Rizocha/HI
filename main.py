import asyncio, logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from config import BOT_TOKEN
from handlers_admin import router as admin_router
from handlers_user import router as user_router
from keep_alive import start_web, self_ping

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

bot = Bot(token=BOT_TOKEN, parse_mode=None)
dp  = Dispatcher()
dp.include_router(admin_router)
dp.include_router(user_router)

async def main():
    await start_web()
    asyncio.create_task(self_ping())
    await bot.set_my_commands([
        BotCommand(command="start", description="Bosh menyu"),
        BotCommand(command="admin", description="Admin panel"),
    ])
    me = await bot.get_me()
    logging.info(f"Bot: @{me.username}")
    await dp.start_polling(bot, allowed_updates=["message","callback_query"])

if __name__ == "__main__":
    asyncio.run(main())
