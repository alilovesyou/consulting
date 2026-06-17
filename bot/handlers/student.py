# handlers/student.py
import os
from aiogram.types import FSInputFile
from aiogram import Router, types, F, Bot
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import get_student_groups, get_group_lessons, get_lesson_by_id
from utils.states import StudentGroupCB, LessonCB

student_router = Router()

# --- 1. MENING DARSLARIM TUGMASI ---
@student_router.message(F.text == "📖 Mening darslarim")
async def show_my_lessons(message: types.Message):
    groups = await get_student_groups(message.from_user.id)
    
    if not groups:
        await message.answer("Siz hozircha hech qaysi guruhga qo'shilmagansiz yoki to'lovingiz tasdiqlanmagan.")
        return

    builder = InlineKeyboardBuilder()
    for grp in groups:
        builder.button(text=f"{grp['name']} ({grp['language']})", callback_data=StudentGroupCB(group_id=grp['id']))
    builder.adjust(1)
    
    await message.answer("📚 <b>Qaysi guruhdagi darslarni ko'rmoqchisiz?</b>", parse_mode="HTML", reply_markup=builder.as_markup())

# --- 2. GURUH TANLANGANDA -> DARSLAR RO'YXATI ---
@student_router.callback_query(StudentGroupCB.filter())
async def show_group_lessons(callback: types.CallbackQuery, callback_data: StudentGroupCB):
    group_id = callback_data.group_id
    lessons = await get_group_lessons(group_id)
    
    if not lessons:
        await callback.answer("Bu guruhga hali dars yuklanmagan.", show_alert=True)
        return
        
    builder = InlineKeyboardBuilder()
    for lesson in lessons:
        builder.button(text=f"▶️ {lesson['title']}", callback_data=LessonCB(lesson_id=lesson['id']))
    builder.adjust(1)
    
    await callback.message.edit_text("🎥 <b>Darsni tanlang:</b>", parse_mode="HTML", reply_markup=builder.as_markup())

# --- 3. DARS TANLANGANDA -> FAYLNI YUBORISH ---
@student_router.callback_query(LessonCB.filter())
async def send_lesson_file(callback: types.CallbackQuery, callback_data: LessonCB, bot: Bot):
    lesson_id = callback_data.lesson_id
    lesson = await get_lesson_by_id(lesson_id)

    if not lesson:
        await callback.answer("Dars topilmadi.", show_alert=True)
        return

    await callback.answer("Yuklanmoqda...")

    title = lesson["title"]
    material_path = lesson["video_path"]
    material_type = lesson["material_type"]
    original_filename = lesson["original_filename"] or os.path.basename(material_path)

    if material_path and os.path.exists(material_path):
        file = FSInputFile(material_path, filename=original_filename)

        if material_type == "video":
            await bot.send_video(
                chat_id=callback.message.chat.id,
                video=file,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
        elif material_type == "photo":
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=file,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
        else:
            await bot.send_document(
                chat_id=callback.message.chat.id,
                document=file,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
        return

    # Eski darslar uchun fallback: agar bazada hali Telegram file_id turgan bo'lsa
    try:
        await bot.send_video(
            chat_id=callback.message.chat.id,
            video=material_path,
            caption=f"📚 <b>{title}</b>",
            parse_mode="HTML"
        )
    except Exception:
        try:
            await bot.send_document(
                chat_id=callback.message.chat.id,
                document=material_path,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
        except Exception:
            try:
                await bot.send_photo(
                    chat_id=callback.message.chat.id,
                    photo=material_path,
                    caption=f"📚 <b>{title}</b>",
                    parse_mode="HTML"
                )
            except Exception:
                await callback.message.answer(
                    "❌ Fayl topilmadi. Iltimos, ustozdan darsni qayta yuklashni so'rang."
                )