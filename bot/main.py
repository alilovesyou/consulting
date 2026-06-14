# main.py
import asyncio
import logging
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv
import os

from database.db import init_db
from handlers.user import user_router
from handlers.courses import courses_router 
from handlers.admin import admin_router

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Userlarga oid barcha komandalarni botga ulaymiz
dp.include_router(user_router)
dp.include_router(courses_router)
dp.include_router(admin_router)

async def main():
    await init_db()
    print("Bot ishga tushdi... 🚀")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())