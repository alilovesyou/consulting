# database/db.py
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()
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

# --- 1. UMUMIY FOYDALANUVCHILAR ---

async def add_user(telegram_id: int, full_name: str):
    """Yangi foydalanuvchini bazaga qo'shish"""
    query = """
    INSERT INTO users (telegram_id, full_name) 
    VALUES ($1, $2)
    ON CONFLICT (telegram_id) DO NOTHING;
    """
    async with pool.acquire() as connection:
        await connection.execute(query, telegram_id, full_name)

async def get_user_role(telegram_id: int):
    """Foydalanuvchining rolini aniqlash"""
    query = "SELECT role FROM users WHERE telegram_id = $1"
    async with pool.acquire() as connection:
        result = await connection.fetchval(query, telegram_id)
        return result if result else 'user'



async def update_user_profile(telegram_id: int, full_name: str, phone: str, region: str, age: int):
    """Foydalanuvchining FIO va qolgan ma'lumotlarini bazaga saqlash va rolini 'student' qilish"""
    query = """
    UPDATE users 
    SET full_name = $1, phone = $2, region = $3, age = $4, role = 'student' 
    WHERE telegram_id = $5;
    """
    async with pool.acquire() as connection:
        await connection.execute(query, full_name, phone, region, age, telegram_id)

async def get_user(telegram_id: int):
    """Foydalanuvchining ism, telefon va viloyatini olish"""
    query = "SELECT full_name, phone, region FROM users WHERE telegram_id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, telegram_id)

# --- 2. TO'LOVLAR UCHUN ---

async def add_payment(user_id: int, course_info: str, payment_method: str, receipt_path: str = None) -> int:
    """To'lovni bazaga 'pending' holatida saqlash"""
    query = """
    INSERT INTO payments (user_id, course_info, payment_method, receipt_path, status)
    VALUES ($1, $2, $3, $4, 'pending')
    RETURNING id;
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, user_id, course_info, payment_method, receipt_path)

async def get_payment(payment_id: int):
    """To'lov haqida ma'lumotni olish"""
    query = """
    SELECT 
        user_id,
        COALESCE(course_info, language) AS course_info,
        COALESCE(course_info, language) AS language,
        status
    FROM payments 
    WHERE id = $1
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, payment_id)

async def update_payment_status(payment_id: int, status: str):
    """To'lov holatini yangilash (approved yoki rejected)"""
    query = "UPDATE payments SET status = $1 WHERE id = $2"
    async with pool.acquire() as connection:
        await connection.execute(query, status, payment_id)

# --- 3. GURUHLAR UCHUN ---

async def get_active_groups():
    """Barcha faol guruhlarni bazadan tortib olish"""
    query = """
    SELECT 
        g.id,
        g.name,
        g.language,
        g.telegram_link,
        g.max_capacity,
        COUNT(gs.user_id)::INT AS current_count
    FROM groups g
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE g.is_active = TRUE
    GROUP BY g.id, g.name, g.language, g.telegram_link, g.max_capacity
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)

async def get_group_link(group_id: int):
    """Tanlangan guruhning ssilkasini olish"""
    query = "SELECT telegram_link, name FROM groups WHERE id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, group_id)

async def get_teacher_groups(teacher_id: int):
    """Ustozga biriktirilgan guruhlarni topish"""
    query = "SELECT id, name, language, max_capacity FROM groups WHERE teacher_id = $1 AND is_active = TRUE"
    async with pool.acquire() as connection:
        return await connection.fetch(query, teacher_id)

# --- 4. USTOZLAR (HR) UCHUN ---

# database/db.py

async def save_teacher_application(telegram_id: int, fio: str, phone: str, region: str, age: int, lang: str, experience: str):
    """Ustoz arizasini saqlash (Yosh qo'shildi)"""
    query = """
    UPDATE users 
    SET full_name = $1, phone = $2, region = $3, age = $4, teach_lang = $5, experience = $6, role = 'pending_teacher'
    WHERE telegram_id = $7;
    """
    async with pool.acquire() as connection:
        await connection.execute(query, fio, phone, region, age, lang, experience, telegram_id)

async def get_full_profile(telegram_id: int):
    """Profil uchun hamma ma'lumotni olish"""
    query = "SELECT full_name, phone, region, age, role, teach_lang FROM users WHERE telegram_id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, telegram_id)
    
async def update_teacher_status(telegram_id: int, status: str):
    """Admin qaroriga ko'ra ustoz rolini yangilash ('teacher' yoki 'rejected_teacher')"""
    query = "UPDATE users SET role = $1 WHERE telegram_id = $2"
    async with pool.acquire() as connection:
        await connection.execute(query, status, telegram_id)

async def get_teacher_info(telegram_id: int):
    """Admin qaror qabul qilayotganda ustoz haqidagi ma'lumotni olish"""
    query = "SELECT full_name, phone, region, teach_lang, experience FROM users WHERE telegram_id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, telegram_id)
    
async def get_student_status(user_id: int):
    """O'quvchining so'nggi kurs/to'lov arizasi holatini olish"""
    query = "SELECT status FROM payments WHERE user_id = $1 ORDER BY id DESC LIMIT 1"
    async with pool.acquire() as connection:
        return await connection.fetchval(query, user_id)
    

async def get_group_info(group_id: int):
    """Guruh haqida asosiy ma'lumotni olish"""
    query = """
    SELECT id, name, language, teacher_id, max_capacity
    FROM groups 
    WHERE id = $1 AND is_active = TRUE
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, group_id)

async def add_lesson(
    group_id: int,
    title: str,
    material_path: str,
    material_type: str = None,
    original_filename: str = None,
    file_size: int = None
):
    """Yangi darsni local file path bilan bazaga saqlash"""
    query = """
    INSERT INTO lessons (
        group_id,
        title,
        video_path,
        material_type,
        original_filename,
        file_size
    )
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING id
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(
            query,
            group_id,
            title,
            material_path,
            material_type,
            original_filename,
            file_size
        )

async def add_student_to_group(user_id: int, group_id: int):
    """O'quvchini guruhga biriktirish"""
    query = "INSERT INTO group_students (user_id, group_id) VALUES ($1, $2) ON CONFLICT DO NOTHING"
    async with pool.acquire() as connection:
        await connection.execute(query, user_id, group_id)

async def get_student_groups(user_id: int):
    """O'quvchining tasdiqlangan guruhlarini topish"""
    query = """
    SELECT g.id, g.name, g.language 
    FROM groups g
    JOIN group_students gs ON g.id = gs.group_id
    WHERE gs.user_id = $1
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, user_id)

async def get_group_lessons(group_id: int):
    """Guruhdagi barcha darslarni olish"""
    query = "SELECT id, title FROM lessons WHERE group_id = $1 ORDER BY id ASC"
    async with pool.acquire() as connection:
        return await connection.fetch(query, group_id)

async def get_lesson_by_id(lesson_id: int):
    """Tanlangan darsning faylini tortib olish"""
    query = """
    SELECT 
        title,
        video_path,
        material_type,
        original_filename
    FROM lessons 
    WHERE id = $1
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, lesson_id)


async def get_all_teachers():
    """Barcha tasdiqlangan ustozlarni olish"""
    query = "SELECT telegram_id, full_name, teach_lang FROM users WHERE role = 'teacher'"
    async with pool.acquire() as connection:
        return await connection.fetch(query)

async def create_new_group(name: str, language: str, max_capacity: int, telegram_link: str, teacher_id: int):
    """Yangi guruh yaratish va ustozni biriktirish"""
    query = """
    INSERT INTO groups (name, language, max_capacity, telegram_link, teacher_id, is_active)
    VALUES ($1, $2, $3, $4, $5, TRUE)
    """
    async with pool.acquire() as connection:
        await connection.execute(query, name, language, max_capacity, telegram_link, teacher_id)

async def get_bot_statistics():
    """Platformadagi umumiy statistikani hisoblash"""
    async with pool.acquire() as connection:
        students = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'student'")
        teachers = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
        groups = await connection.fetchval("SELECT COUNT(*) FROM groups WHERE is_active = TRUE")
        return {'students': students, 'teachers': teachers, 'groups': groups}
    
async def get_all_groups():
    """Admin barcha guruhlarni ko'rishi uchun"""
    query = "SELECT id, name, teacher_id FROM groups WHERE is_active = TRUE"
    async with pool.acquire() as connection:
        return await connection.fetch(query)

async def change_group_teacher(group_id: int, new_teacher_id: int):
    """Ustozni almashtirish"""
    query = "UPDATE groups SET teacher_id = $1 WHERE id = $2"
    async with pool.acquire() as connection:
        await connection.execute(query, new_teacher_id, group_id)

async def delete_group(group_id: int):
    """Guruhni o'chirish (aslida statusini o'zgartiramiz)"""
    query = "UPDATE groups SET is_active = FALSE WHERE id = $1"
    async with pool.acquire() as connection:
        await connection.execute(query, group_id)

async def get_teacher_group_students(teacher_id: int, group_id: int):
    """Ustozga tegishli guruhdagi o'quvchilarni olish"""
    query = """
    SELECT u.telegram_id, u.full_name, u.phone
    FROM group_students gs
    JOIN users u ON u.telegram_id = gs.user_id
    JOIN groups g ON g.id = gs.group_id
    WHERE gs.group_id = $1 AND g.teacher_id = $2
    ORDER BY u.full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, group_id, teacher_id)


async def add_student_result(user_id: int, group_id: int, teacher_id: int, result_title: str, score: str, comment: str):
    """O'quvchi natijasini bazaga yozish"""
    query = """
    INSERT INTO student_results (user_id, group_id, teacher_id, result_title, score, comment)
    VALUES ($1, $2, $3, $4, $5, $6)
    RETURNING id;
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, user_id, group_id, teacher_id, result_title, score, comment)


async def add_kick_request(user_id: int, group_id: int, teacher_id: int, reason: str):
    """Ustozdan chetlatish so'rovini saqlash"""
    query = """
    INSERT INTO kick_requests (user_id, group_id, teacher_id, reason, status)
    VALUES ($1, $2, $3, $4, 'pending')
    RETURNING id;
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, user_id, group_id, teacher_id, reason)


async def get_kick_request(request_id: int):
    """Chetlatish so'rovi haqida to'liq ma'lumot olish"""
    query = """
    SELECT 
        kr.id,
        kr.user_id,
        kr.group_id,
        kr.teacher_id,
        kr.reason,
        kr.status,
        s.full_name AS student_name,
        t.full_name AS teacher_name,
        g.name AS group_name
    FROM kick_requests kr
    LEFT JOIN users s ON s.telegram_id = kr.user_id
    LEFT JOIN users t ON t.telegram_id = kr.teacher_id
    LEFT JOIN groups g ON g.id = kr.group_id
    WHERE kr.id = $1
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, request_id)


async def update_kick_request_status(request_id: int, status: str):
    """Chetlatish so'rovi statusini yangilash"""
    query = "UPDATE kick_requests SET status = $1 WHERE id = $2"
    async with pool.acquire() as connection:
        await connection.execute(query, status, request_id)


async def remove_student_from_group(user_id: int, group_id: int):
    """O'quvchini guruhdan chiqarish"""
    query = "DELETE FROM group_students WHERE user_id = $1 AND group_id = $2"
    async with pool.acquire() as connection:
        await connection.execute(query, user_id, group_id)

async def teacher_owns_group(teacher_id: int, group_id: int) -> bool:
    """Ustoz shu guruh egasimi yoki yo'qmi tekshirish"""
    query = """
    SELECT EXISTS(
        SELECT 1 
        FROM groups 
        WHERE id = $1 AND teacher_id = $2 AND is_active = TRUE
    )
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, group_id, teacher_id)


async def add_student_to_group_if_capacity(user_id: int, group_id: int):
    """Guruh sig'imi to'lmagan bo'lsa o'quvchini qo'shish"""
    async with pool.acquire() as connection:
        async with connection.transaction():
            group = await connection.fetchrow(
                """
                SELECT id, name, max_capacity
                FROM groups
                WHERE id = $1 AND is_active = TRUE
                FOR UPDATE
                """,
                group_id
            )

            if not group:
                return {
                    "ok": False,
                    "reason": "not_found",
                    "message": "Guruh topilmadi yoki faol emas."
                }

            current_count = await connection.fetchval(
                "SELECT COUNT(*) FROM group_students WHERE group_id = $1",
                group_id
            )

            max_capacity = group["max_capacity"] or 10

            if current_count >= max_capacity:
                return {
                    "ok": False,
                    "reason": "full",
                    "message": f"{group['name']} guruhi to'lgan: {current_count}/{max_capacity}"
                }

            await connection.execute(
                """
                INSERT INTO group_students (user_id, group_id)
                VALUES ($1, $2)
                ON CONFLICT DO NOTHING
                """,
                user_id,
                group_id
            )

            new_count = await connection.fetchval(
                "SELECT COUNT(*) FROM group_students WHERE group_id = $1",
                group_id
            )

            return {
                "ok": True,
                "reason": "added",
                "message": f"O'quvchi guruhga qo'shildi: {new_count}/{max_capacity}",
                "current_count": new_count,
                "max_capacity": max_capacity
            }

async def get_api_user_profile(telegram_id: int):
    """Mini App uchun user profilini olish"""
    query = """
    SELECT 
        telegram_id,
        full_name,
        phone,
        region,
        age,
        role,
        teach_lang,
        created_at
    FROM users
    WHERE telegram_id = $1
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, telegram_id)


async def get_api_student_groups(user_id: int):
    """Mini App uchun o'quvchining guruhlarini olish"""
    query = """
    SELECT 
        g.id,
        g.name,
        g.language,
        g.max_capacity,
        COUNT(gs_all.user_id)::INT AS current_count,
        g.created_at
    FROM group_students gs
    JOIN groups g ON g.id = gs.group_id
    LEFT JOIN group_students gs_all ON gs_all.group_id = g.id
    WHERE gs.user_id = $1
      AND g.is_active = TRUE
    GROUP BY g.id, g.name, g.language, g.max_capacity, g.created_at
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, user_id)


async def api_user_has_group(user_id: int, group_id: int) -> bool:
    """Mini App uchun user shu guruhga tegishlimi yoki yo'qmi"""
    query = """
    SELECT EXISTS(
        SELECT 1
        FROM group_students gs
        JOIN groups g ON g.id = gs.group_id
        WHERE gs.user_id = $1
          AND gs.group_id = $2
          AND g.is_active = TRUE
    )
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, user_id, group_id)


async def get_api_group_lessons(user_id: int, group_id: int):
    """Mini App uchun guruh darslari"""
    query = """
    SELECT 
        l.id,
        l.title,
        l.material_type,
        l.original_filename,
        l.file_size,
        CASE 
            WHEN l.video_path IS NOT NULL THEN TRUE 
            ELSE FALSE 
        END AS has_material,
        CASE
            WHEN l.video_path LIKE 'media/lessons/%' THEN '/' || l.video_path
            ELSE NULL
        END AS material_url,
        l.created_at
    FROM lessons l
    JOIN group_students gs ON gs.group_id = l.group_id
    WHERE gs.user_id = $1
      AND l.group_id = $2
    ORDER BY l.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, user_id, group_id)


async def get_api_student_results(user_id: int):
    """Mini App uchun o'quvchi natijalari"""
    query = """
    SELECT
        sr.id,
        sr.result_title,
        sr.score,
        sr.comment,
        sr.created_at,
        g.name AS group_name,
        g.language AS group_language,
        t.full_name AS teacher_name
    FROM student_results sr
    LEFT JOIN groups g ON g.id = sr.group_id
    LEFT JOIN users t ON t.telegram_id = sr.teacher_id
    WHERE sr.user_id = $1
    ORDER BY sr.created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, user_id)

async def get_api_teacher_groups(teacher_id: int):
    """Mini App uchun teacher guruhlarini olish"""
    query = """
    SELECT
        g.id,
        g.name,
        g.language,
        g.max_capacity,
        COUNT(gs.user_id)::INT AS current_count,
        g.telegram_link,
        g.created_at
    FROM groups g
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE g.teacher_id = $1
      AND g.is_active = TRUE
    GROUP BY g.id, g.name, g.language, g.max_capacity, g.telegram_link, g.created_at
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, teacher_id)


async def get_api_teacher_group_lessons(teacher_id: int, group_id: int):
    """Teacher o'z guruhidagi darslarni ko'rishi uchun"""
    query = """
    SELECT
        l.id,
        l.title,
        l.video_path,
        l.material_type,
        l.original_filename,
        l.file_size,
        l.created_at
    FROM lessons l
    JOIN groups g ON g.id = l.group_id
    WHERE l.group_id = $1
      AND g.teacher_id = $2
      AND g.is_active = TRUE
    ORDER BY l.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, group_id, teacher_id)


async def get_api_teacher_results(teacher_id: int):
    """Teacher kiritgan natijalar ro'yxati"""
    query = """
    SELECT
        sr.id,
        sr.user_id,
        u.full_name AS student_name,
        sr.group_id,
        g.name AS group_name,
        sr.result_title,
        sr.score,
        sr.comment,
        sr.created_at
    FROM student_results sr
    LEFT JOIN users u ON u.telegram_id = sr.user_id
    LEFT JOIN groups g ON g.id = sr.group_id
    WHERE sr.teacher_id = $1
    ORDER BY sr.created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, teacher_id)


async def get_api_teacher_kick_requests(teacher_id: int):
    """Teacher yuborgan chetlatish so'rovlari"""
    query = """
    SELECT
        kr.id,
        kr.user_id,
        u.full_name AS student_name,
        kr.group_id,
        g.name AS group_name,
        kr.reason,
        kr.status,
        kr.created_at
    FROM kick_requests kr
    LEFT JOIN users u ON u.telegram_id = kr.user_id
    LEFT JOIN groups g ON g.id = kr.group_id
    WHERE kr.teacher_id = $1
    ORDER BY kr.created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, teacher_id)


async def api_student_is_in_teacher_group(teacher_id: int, group_id: int, student_id: int) -> bool:
    """Student aynan shu teacher guruhidami yoki yo'qmi"""
    query = """
    SELECT EXISTS(
        SELECT 1
        FROM group_students gs
        JOIN groups g ON g.id = gs.group_id
        WHERE gs.user_id = $1
          AND gs.group_id = $2
          AND g.teacher_id = $3
          AND g.is_active = TRUE
    )
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(query, student_id, group_id, teacher_id)
    
async def get_api_admin_statistics():
    """Mini App Admin Dashboard statistikasi"""
    async with pool.acquire() as connection:
        students = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'student'")
        teachers = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
        admins = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role IN ('admin', 'superadmin')")
        groups = await connection.fetchval("SELECT COUNT(*) FROM groups WHERE is_active = TRUE")
        pending_payments = await connection.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
        approved_payments = await connection.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'approved'")
        pending_teachers = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'pending_teacher'")
        pending_kicks = await connection.fetchval("SELECT COUNT(*) FROM kick_requests WHERE status = 'pending'")

        return {
            "students": students,
            "teachers": teachers,
            "admins": admins,
            "groups": groups,
            "pending_payments": pending_payments,
            "approved_payments": approved_payments,
            "pending_teachers": pending_teachers,
            "pending_kicks": pending_kicks
        }


async def get_api_admin_payments(status: str = None):
    """Admin uchun to'lovlar ro'yxati"""
    base_query = """
    SELECT
        p.id,
        p.user_id,
        u.full_name AS student_name,
        u.phone AS student_phone,
        u.region AS student_region,
        COALESCE(p.course_info, p.language) AS course_info,
        p.payment_method,
        p.receipt_path,
        p.status,
        p.created_at
    FROM payments p
    LEFT JOIN users u ON u.telegram_id = p.user_id
    """

    params = []

    if status:
        base_query += " WHERE p.status = $1"
        params.append(status)

    base_query += " ORDER BY p.created_at DESC"

    async with pool.acquire() as connection:
        return await connection.fetch(base_query, *params)


async def get_api_admin_groups():
    """Admin uchun barcha faol guruhlar"""
    query = """
    SELECT
        g.id,
        g.name,
        g.language,
        g.teacher_id,
        t.full_name AS teacher_name,
        t.teach_lang AS teacher_lang,
        g.max_capacity,
        COUNT(gs.user_id)::INT AS current_count,
        g.telegram_link,
        g.is_active,
        g.created_at
    FROM groups g
    LEFT JOIN users t ON t.telegram_id = g.teacher_id
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE g.is_active = TRUE
    GROUP BY 
        g.id, g.name, g.language, g.teacher_id, t.full_name, 
        t.teach_lang, g.max_capacity, g.telegram_link, g.is_active, g.created_at
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)


async def get_api_admin_teachers():
    """Admin uchun tasdiqlangan ustozlar"""
    query = """
    SELECT
        telegram_id,
        full_name,
        phone,
        region,
        age,
        teach_lang,
        experience,
        role,
        created_at
    FROM users
    WHERE role = 'teacher'
    ORDER BY full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)


async def get_api_teacher_applications(status: str = "pending_teacher"):
    """Admin uchun ustozlik arizalari"""
    query = """
    SELECT
        telegram_id,
        full_name,
        phone,
        region,
        age,
        teach_lang,
        experience,
        role,
        created_at
    FROM users
    WHERE role = $1
    ORDER BY created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, status)


async def get_api_admin_kick_requests(status: str = None):
    """Admin uchun chetlatish so'rovlari"""
    base_query = """
    SELECT
        kr.id,
        kr.user_id,
        s.full_name AS student_name,
        s.phone AS student_phone,
        kr.group_id,
        g.name AS group_name,
        kr.teacher_id,
        t.full_name AS teacher_name,
        kr.reason,
        kr.status,
        kr.created_at
    FROM kick_requests kr
    LEFT JOIN users s ON s.telegram_id = kr.user_id
    LEFT JOIN users t ON t.telegram_id = kr.teacher_id
    LEFT JOIN groups g ON g.id = kr.group_id
    """

    params = []

    if status:
        base_query += " WHERE kr.status = $1"
        params.append(status)

    base_query += " ORDER BY kr.created_at DESC"

    async with pool.acquire() as connection:
        return await connection.fetch(base_query, *params)
    
async def get_api_superadmin_statistics():
    """Superadmin uchun kengaytirilgan statistika"""
    async with pool.acquire() as connection:
        total_users = await connection.fetchval("SELECT COUNT(*) FROM users")
        users = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'user'")
        students = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'student'")
        teachers = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'teacher'")
        pending_teachers = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'pending_teacher'")
        rejected_teachers = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'rejected_teacher'")
        admins = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'admin'")
        superadmins = await connection.fetchval("SELECT COUNT(*) FROM users WHERE role = 'superadmin'")

        groups = await connection.fetchval("SELECT COUNT(*) FROM groups WHERE is_active = TRUE")
        inactive_groups = await connection.fetchval("SELECT COUNT(*) FROM groups WHERE is_active = FALSE")

        payments_total = await connection.fetchval("SELECT COUNT(*) FROM payments")
        payments_pending = await connection.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
        payments_approved = await connection.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'approved'")
        payments_rejected = await connection.fetchval("SELECT COUNT(*) FROM payments WHERE status = 'rejected'")

        lessons = await connection.fetchval("SELECT COUNT(*) FROM lessons")
        results = await connection.fetchval("SELECT COUNT(*) FROM student_results")
        kick_requests = await connection.fetchval("SELECT COUNT(*) FROM kick_requests")
        kick_pending = await connection.fetchval("SELECT COUNT(*) FROM kick_requests WHERE status = 'pending'")

        return {
            "users": {
                "total": total_users,
                "user": users,
                "student": students,
                "teacher": teachers,
                "pending_teacher": pending_teachers,
                "rejected_teacher": rejected_teachers,
                "admin": admins,
                "superadmin": superadmins
            },
            "groups": {
                "active": groups,
                "inactive": inactive_groups
            },
            "payments": {
                "total": payments_total,
                "pending": payments_pending,
                "approved": payments_approved,
                "rejected": payments_rejected
            },
            "education": {
                "lessons": lessons,
                "results": results
            },
            "kick_requests": {
                "total": kick_requests,
                "pending": kick_pending
            }
        }


async def get_api_superadmin_users(role: str = None, search: str = None, limit: int = 100, offset: int = 0):
    """Superadmin uchun foydalanuvchilar ro'yxati"""
    query = """
    SELECT
        telegram_id,
        full_name,
        phone,
        region,
        age,
        role,
        teach_lang,
        experience,
        created_at
    FROM users
    WHERE 1 = 1
    """

    params = []
    param_index = 1

    if role:
        query += f" AND role = ${param_index}"
        params.append(role)
        param_index += 1

    if search:
        query += f"""
        AND (
            full_name ILIKE ${param_index}
            OR phone ILIKE ${param_index}
            OR CAST(telegram_id AS TEXT) ILIKE ${param_index}
        )
        """
        params.append(f"%{search}%")
        param_index += 1

    query += f" ORDER BY created_at DESC LIMIT ${param_index} OFFSET ${param_index + 1}"
    params.extend([limit, offset])

    async with pool.acquire() as connection:
        return await connection.fetch(query, *params)


async def count_api_superadmin_users(role: str = None, search: str = None):
    """Superadmin users pagination uchun umumiy son"""
    query = """
    SELECT COUNT(*)
    FROM users
    WHERE 1 = 1
    """

    params = []
    param_index = 1

    if role:
        query += f" AND role = ${param_index}"
        params.append(role)
        param_index += 1

    if search:
        query += f"""
        AND (
            full_name ILIKE ${param_index}
            OR phone ILIKE ${param_index}
            OR CAST(telegram_id AS TEXT) ILIKE ${param_index}
        )
        """
        params.append(f"%{search}%")

    async with pool.acquire() as connection:
        return await connection.fetchval(query, *params)


async def get_api_superadmin_user(telegram_id: int):
    """Bitta user haqida to'liq ma'lumot"""
    query = """
    SELECT
        telegram_id,
        full_name,
        phone,
        region,
        age,
        role,
        teach_lang,
        experience,
        created_at
    FROM users
    WHERE telegram_id = $1
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, telegram_id)


async def update_user_role(telegram_id: int, role: str):
    """User rolini o'zgartirish"""
    query = """
    UPDATE users
    SET role = $1
    WHERE telegram_id = $2
    """
    async with pool.acquire() as connection:
        await connection.execute(query, role, telegram_id)


async def count_superadmins():
    """Superadminlar sonini hisoblash"""
    query = "SELECT COUNT(*) FROM users WHERE role = 'superadmin'"
    async with pool.acquire() as connection:
        return await connection.fetchval(query)


async def get_api_superadmin_admins():
    """Admin va superadminlar ro'yxati"""
    query = """
    SELECT
        telegram_id,
        full_name,
        phone,
        region,
        age,
        role,
        created_at
    FROM users
    WHERE role IN ('admin', 'superadmin')
    ORDER BY 
        CASE 
            WHEN role = 'superadmin' THEN 1
            WHEN role = 'admin' THEN 2
            ELSE 3
        END,
        created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)
    
async def log_admin_action(admin_id: int, action: str, entity_type: str = None, entity_id: int = None, details: dict = None):
    """Admin qilgan harakatni log qilish"""
    import json

    query = """
    INSERT INTO admin_actions (admin_id, action, entity_type, entity_id, details)
    VALUES ($1, $2, $3, $4, $5::jsonb)
    RETURNING id
    """
    async with pool.acquire() as connection:
        return await connection.fetchval(
            query,
            admin_id,
            action,
            entity_type,
            entity_id,
            json.dumps(details or {})
        )


async def get_superadmin_ids():
    """Barcha superadmin telegram_id larini olish"""
    query = "SELECT telegram_id FROM users WHERE role = 'superadmin'"
    async with pool.acquire() as connection:
        rows = await connection.fetch(query)
        return [row["telegram_id"] for row in rows]
    
async def get_payment_admin_ids():
    """
    To'lov cheklari va ustoz arizalarini oladigan adminlar:
    oddiy admin + superadmin.
    """
    query = """
    SELECT telegram_id
    FROM users
    WHERE role IN ('admin', 'superadmin')
    """
    async with pool.acquire() as connection:
        rows = await connection.fetch(query)
        return [row["telegram_id"] for row in rows]


async def get_api_superadmin_admin_actions(limit: int = 100, offset: int = 0):
    """Superadmin uchun admin action history"""
    query = """
    SELECT
        aa.id,
        aa.admin_id,
        u.full_name AS admin_name,
        aa.action,
        aa.entity_type,
        aa.entity_id,
        aa.details,
        aa.created_at
    FROM admin_actions aa
    LEFT JOIN users u ON u.telegram_id = aa.admin_id
    ORDER BY aa.created_at DESC
    LIMIT $1 OFFSET $2
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)


async def upsert_admin_user(telegram_id: int, full_name: str = None):
    """Superadmin yangi admin qo'shishi uchun"""
    query = """
    INSERT INTO users (telegram_id, full_name, role)
    VALUES ($1, $2, 'admin')
    ON CONFLICT (telegram_id)
    DO UPDATE SET role = 'admin',
                  full_name = COALESCE($2, users.full_name)
    """
    async with pool.acquire() as connection:
        await connection.execute(query, telegram_id, full_name)


async def remove_admin_role(telegram_id: int):
    """Adminni oddiy userga tushirish. Superadminni o'zgartirmaydi."""
    query = """
    UPDATE users
    SET role = 'user'
    WHERE telegram_id = $1
      AND role = 'admin'
    """
    async with pool.acquire() as connection:
        await connection.execute(query, telegram_id)


async def get_api_superadmin_teachers_overview():
    """Superadmin uchun barcha ustozlar va ularning guruh/student soni"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        u.teach_lang,
        u.created_at,
        COUNT(DISTINCT g.id)::INT AS groups_count,
        COUNT(gs.user_id)::INT AS students_count
    FROM users u
    LEFT JOIN groups g ON g.teacher_id = u.telegram_id AND g.is_active = TRUE
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE u.role = 'teacher'
    GROUP BY u.telegram_id, u.full_name, u.phone, u.region, u.age, u.teach_lang, u.created_at
    ORDER BY u.full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)


async def get_api_superadmin_teacher_groups(teacher_id: int):
    """Superadmin uchun bitta ustoz guruhlari"""
    query = """
    SELECT
        g.id,
        g.name,
        g.language,
        g.max_capacity,
        COUNT(gs.user_id)::INT AS current_count,
        g.telegram_link,
        g.created_at
    FROM groups g
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE g.teacher_id = $1
      AND g.is_active = TRUE
    GROUP BY g.id, g.name, g.language, g.max_capacity, g.telegram_link, g.created_at
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, teacher_id)


async def get_api_superadmin_groups_overview():
    """Superadmin uchun barcha guruhlar"""
    query = """
    SELECT
        g.id,
        g.name,
        g.language,
        g.teacher_id,
        t.full_name AS teacher_name,
        g.max_capacity,
        COUNT(gs.user_id)::INT AS current_count,
        g.telegram_link,
        g.is_active,
        g.created_at
    FROM groups g
    LEFT JOIN users t ON t.telegram_id = g.teacher_id
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE g.is_active = TRUE
    GROUP BY g.id, g.name, g.language, g.teacher_id, t.full_name, g.max_capacity, g.telegram_link, g.is_active, g.created_at
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)


async def get_api_superadmin_group_students(group_id: int):
    """Superadmin uchun guruh ichidagi o'quvchilar"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        gs.created_at AS joined_at
    FROM group_students gs
    JOIN users u ON u.telegram_id = gs.user_id
    WHERE gs.group_id = $1
    ORDER BY u.full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, group_id)


async def get_api_superadmin_students_overview(limit: int = 100, offset: int = 0):
    """Superadmin uchun o'quvchilar ro'yxati"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        u.created_at,
        COUNT(DISTINCT gs.group_id)::INT AS groups_count,
        COUNT(sr.id)::INT AS results_count
    FROM users u
    LEFT JOIN group_students gs ON gs.user_id = u.telegram_id
    LEFT JOIN student_results sr ON sr.user_id = u.telegram_id
    WHERE u.role = 'student'
    GROUP BY u.telegram_id, u.full_name, u.phone, u.region, u.age, u.created_at
    ORDER BY u.created_at DESC
    LIMIT $1 OFFSET $2
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)


async def get_api_superadmin_student_results(student_id: int):
    """Superadmin uchun bitta o'quvchi baholari"""
    query = """
    SELECT
        sr.id,
        sr.result_title,
        sr.score,
        sr.comment,
        sr.created_at,
        g.name AS group_name,
        g.language AS group_language,
        t.full_name AS teacher_name
    FROM student_results sr
    LEFT JOIN groups g ON g.id = sr.group_id
    LEFT JOIN users t ON t.telegram_id = sr.teacher_id
    WHERE sr.user_id = $1
    ORDER BY sr.created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, student_id)


async def get_api_superadmin_all_results(limit: int = 100, offset: int = 0):
    """Superadmin uchun barcha baholar"""
    query = """
    SELECT
        sr.id,
        sr.user_id,
        s.full_name AS student_name,
        sr.teacher_id,
        t.full_name AS teacher_name,
        sr.group_id,
        g.name AS group_name,
        sr.result_title,
        sr.score,
        sr.comment,
        sr.created_at
    FROM student_results sr
    LEFT JOIN users s ON s.telegram_id = sr.user_id
    LEFT JOIN users t ON t.telegram_id = sr.teacher_id
    LEFT JOIN groups g ON g.id = sr.group_id
    ORDER BY sr.created_at DESC
    LIMIT $1 OFFSET $2
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)
    
async def get_api_superadmin_admin_actions(limit: int = 100, offset: int = 0):
    """Superadmin uchun admin action history"""
    query = """
    SELECT
        aa.id,
        aa.admin_id,
        u.full_name AS admin_name,
        aa.action,
        aa.entity_type,
        aa.entity_id,
        aa.details,
        aa.created_at
    FROM admin_actions aa
    LEFT JOIN users u ON u.telegram_id = aa.admin_id
    ORDER BY aa.created_at DESC
    LIMIT $1 OFFSET $2
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)


async def get_api_superadmin_teachers_overview():
    """Superadmin uchun barcha ustozlar va ularning guruh/student soni"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        u.teach_lang,
        u.created_at,
        COUNT(DISTINCT g.id)::INT AS groups_count,
        COUNT(gs.user_id)::INT AS students_count
    FROM users u
    LEFT JOIN groups g ON g.teacher_id = u.telegram_id AND g.is_active = TRUE
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE u.role = 'teacher'
    GROUP BY u.telegram_id, u.full_name, u.phone, u.region, u.age, u.teach_lang, u.created_at
    ORDER BY u.full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query)


async def get_api_superadmin_teacher_groups(teacher_id: int):
    """Superadmin uchun bitta ustoz guruhlari"""
    query = """
    SELECT
        g.id,
        g.name,
        g.language,
        g.max_capacity,
        COUNT(gs.user_id)::INT AS current_count,
        g.telegram_link,
        g.created_at
    FROM groups g
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE g.teacher_id = $1
      AND g.is_active = TRUE
    GROUP BY g.id, g.name, g.language, g.max_capacity, g.telegram_link, g.created_at
    ORDER BY g.id ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, teacher_id)


async def get_api_superadmin_group_students(group_id: int):
    """Superadmin uchun guruh ichidagi o'quvchilar"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        gs.created_at AS joined_at
    FROM group_students gs
    JOIN users u ON u.telegram_id = gs.user_id
    WHERE gs.group_id = $1
    ORDER BY u.full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, group_id)


async def get_api_superadmin_students_overview(limit: int = 100, offset: int = 0):
    """Superadmin uchun o'quvchilar ro'yxati"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        u.created_at,
        COUNT(DISTINCT gs.group_id)::INT AS groups_count,
        COUNT(sr.id)::INT AS results_count
    FROM users u
    LEFT JOIN group_students gs ON gs.user_id = u.telegram_id
    LEFT JOIN student_results sr ON sr.user_id = u.telegram_id
    WHERE u.role = 'student'
    GROUP BY u.telegram_id, u.full_name, u.phone, u.region, u.age, u.created_at
    ORDER BY u.created_at DESC
    LIMIT $1 OFFSET $2
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)


async def get_api_superadmin_student_results(student_id: int):
    """Superadmin uchun bitta o'quvchi baholari"""
    query = """
    SELECT
        sr.id,
        sr.result_title,
        sr.score,
        sr.comment,
        sr.created_at,
        g.name AS group_name,
        g.language AS group_language,
        t.full_name AS teacher_name
    FROM student_results sr
    LEFT JOIN groups g ON g.id = sr.group_id
    LEFT JOIN users t ON t.telegram_id = sr.teacher_id
    WHERE sr.user_id = $1
    ORDER BY sr.created_at DESC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, student_id)


async def get_api_superadmin_all_results(limit: int = 100, offset: int = 0):
    """Superadmin uchun barcha baholar"""
    query = """
    SELECT
        sr.id,
        sr.user_id,
        s.full_name AS student_name,
        sr.teacher_id,
        t.full_name AS teacher_name,
        sr.group_id,
        g.name AS group_name,
        sr.result_title,
        sr.score,
        sr.comment,
        sr.created_at
    FROM student_results sr
    LEFT JOIN users s ON s.telegram_id = sr.user_id
    LEFT JOIN users t ON t.telegram_id = sr.teacher_id
    LEFT JOIN groups g ON g.id = sr.group_id
    ORDER BY sr.created_at DESC
    LIMIT $1 OFFSET $2
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, limit, offset)
    
async def get_api_superadmin_teachers_by_language(language: str):
    """Til bo'yicha ustozlar ro'yxati"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        u.teach_lang,
        u.created_at,
        COUNT(DISTINCT g.id)::INT AS groups_count,
        COUNT(gs.user_id)::INT AS students_count
    FROM users u
    LEFT JOIN groups g ON g.teacher_id = u.telegram_id AND g.is_active = TRUE
    LEFT JOIN group_students gs ON gs.group_id = g.id
    WHERE u.role = 'teacher'
      AND u.teach_lang = $1
    GROUP BY u.telegram_id, u.full_name, u.phone, u.region, u.age, u.teach_lang, u.created_at
    ORDER BY u.full_name ASC
    """
    async with pool.acquire() as connection:
        return await connection.fetch(query, language)


async def get_api_superadmin_student_profile(student_id: int):
    """Bitta o'quvchi haqida to'liqroq ma'lumot"""
    query = """
    SELECT
        u.telegram_id,
        u.full_name,
        u.phone,
        u.region,
        u.age,
        u.role,
        u.created_at,
        COUNT(DISTINCT gs.group_id)::INT AS groups_count,
        COUNT(sr.id)::INT AS results_count
    FROM users u
    LEFT JOIN group_students gs ON gs.user_id = u.telegram_id
    LEFT JOIN student_results sr ON sr.user_id = u.telegram_id
    WHERE u.telegram_id = $1
    GROUP BY u.telegram_id, u.full_name, u.phone, u.region, u.age, u.role, u.created_at
    """
    async with pool.acquire() as connection:
        return await connection.fetchrow(query, student_id)
async def get_user_interface_lang(telegram_id: int):
    """Foydalanuvchining bot interface tilini olish"""
    query = "SELECT interface_lang FROM users WHERE telegram_id = $1"
    async with pool.acquire() as connection:
        return await connection.fetchval(query, telegram_id)


async def set_user_interface_lang(telegram_id: int, lang: str):
    """Foydalanuvchining bot interface tilini saqlash"""
    query = """
    UPDATE users
    SET interface_lang = $1
    WHERE telegram_id = $2
    """
    async with pool.acquire() as connection:
        await connection.execute(query, lang, telegram_id)