import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

# Bazaga ulanish hovuzi (pool) - bu bir vaqtda ko'p odam yozganda bot qotib qolmasligi uchun kerak
pool = None

async def init_db():
    """Bot yonganda bazaga ulanishni ochamiz"""
    global pool
    pool = await asyncpg.create_pool(
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME"),
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT")
    )
    print("PostgreSQL bazasiga muvaffaqiyatli ulandi! 🗄")

async def add_user(telegram_id: int, full_name: str):
    """Yangi foydalanuvchini bazaga qo'shish"""
    query = """
    INSERT INTO users (telegram_id, full_name) 
    VALUES ($1, $2)
    ON CONFLICT (telegram_id) DO NOTHING;
    """
    # ON CONFLICT DO NOTHING - agar bu odam oldin start bosgan bo'lsa, bazaga qayta yozib xato bermaydi.
    
    async with pool.acquire() as connection:
        await connection.execute(query, telegram_id, full_name)

async def update_user_profile(telegram_id: int, full_name: str, phone: str, region: str, age: int):
    """Foydalanuvchining FIO va qolgan ma'lumotlarini bazaga saqlash"""
    query = """
    UPDATE users 
    SET full_name = $1, phone = $2, region = $3, age = $4 
    WHERE telegram_id = $5;
    """
    async with pool.acquire() as connection:
        await connection.execute(query, full_name, phone, region, age, telegram_id)


async def get_user(telegram_id: int):
    """Foydalanuvchining ism, telefon va viloyatini olish (Adminga yuborish uchun)"""
    query = "SELECT full_name, phone, region FROM users WHERE telegram_id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, telegram_id)

async def add_payment(user_id: int, course_info: str, payment_method: str, receipt_path: str = None) -> int:
    """To'lovni bazaga 'pending' (kutilmoqda) holatida saqlash"""
    query = """
    INSERT INTO payments (user_id, language, payment_method, receipt_path, status)
    VALUES ($1, $2, $3, $4, 'pending')
    RETURNING id;
    """
    async with pool.acquire() as connection:
        # Bu yerda language ustuniga biz "Til - Paket" qilib birlashtirib saqlaymiz
        payment_id = await connection.fetchval(query, user_id, course_info, payment_method, receipt_path)
        return payment_id

async def get_payment(payment_id: int):
    """To'lov haqida ma'lumotni olish"""
    query = "SELECT user_id, language, status FROM payments WHERE id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, payment_id)

async def update_payment_status(payment_id: int, status: str):
    """To'lov holatini yangilash (approved yoki rejected)"""
    query = "UPDATE payments SET status = $1 WHERE id = $2"
    async with pool.acquire() as connection:
        await connection.execute(query, status, payment_id)

async def get_active_groups():
    """Barcha faol guruhlarni bazadan tortib olish"""
    query = "SELECT id, name, language, telegram_link FROM groups WHERE is_active = TRUE"
    async with pool.acquire() as connection:
        return await connection.fetch(query)

async def get_group_link(group_id: int):
    """Tanlangan guruhning ssilkasini olish"""
    query = "SELECT telegram_link, name FROM groups WHERE id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, group_id)
