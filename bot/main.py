# main.py
import asyncio
import logging
import os

import uvicorn
from aiogram import Bot, Dispatcher
from dotenv import load_dotenv

from api.app import app
from database.db import init_db
from handlers.user import user_router
from handlers.courses import courses_router
from handlers.admin import admin_router
from handlers.teacher import teacher_router
from handlers.student import student_router

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
API_HOST = os.getenv("API_HOST", "127.0.0.1")
API_PORT = int(os.getenv("API_PORT", "8000"))

bot = Bot(token=TOKEN)
dp = Dispatcher()

dp.include_router(user_router)
dp.include_router(courses_router)
dp.include_router(admin_router)
dp.include_router(teacher_router)
dp.include_router(student_router)


async def start_bot():
    print("Bot ishga tushdi... 🚀")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


async def start_api():
    config = uvicorn.Config(
        app,
        host=API_HOST,
        port=API_PORT,
        log_level="info"
    )
    server = uvicorn.Server(config)
    print(f"FastAPI ishga tushdi... 🌐 http://{API_HOST}:{API_PORT}")
    await server.serve()


async def main():
    await init_db()

    await asyncio.gather(
        start_bot(),
        start_api()
    )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())