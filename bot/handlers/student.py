# handlers/student.py
import os

from aiogram import Router, types, F, Bot
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    get_student_groups,
    get_group_lessons,
    get_lesson_by_id,
    get_user_interface_lang,
)
from utils.states import StudentGroupCB, LessonCB
from utils.i18n import all_texts

student_router = Router()


# ==========================================
# LOCAL TRANSLATIONS FOR STUDENT.PY
# ==========================================

LOCAL_TEXTS = {
    "no_groups": {
        "uz": "Siz hozircha hech qaysi guruhga qo'shilmagansiz yoki to'lovingiz tasdiqlanmagan.",
        "ru": "Вы пока не добавлены ни в одну группу или ваша оплата ещё не подтверждена.",
        "en": "You have not been added to any group yet, or your payment has not been approved.",
    },
    "choose_group": {
        "uz": "📚 <b>Qaysi guruhdagi darslarni ko'rmoqchisiz?</b>",
        "ru": "📚 <b>Из какой группы вы хотите посмотреть уроки?</b>",
        "en": "📚 <b>Which group’s lessons would you like to view?</b>",
    },
    "no_lessons": {
        "uz": "Bu guruhga hali dars yuklanmagan.",
        "ru": "В эту группу ещё не загружены уроки.",
        "en": "No lessons have been uploaded to this group yet.",
    },
    "choose_lesson": {
        "uz": "🎥 <b>Darsni tanlang:</b>",
        "ru": "🎥 <b>Выберите урок:</b>",
        "en": "🎥 <b>Choose a lesson:</b>",
    },
    "lesson_not_found": {
        "uz": "Dars topilmadi.",
        "ru": "Урок не найден.",
        "en": "Lesson not found.",
    },
    "loading": {
        "uz": "Yuklanmoqda...",
        "ru": "Загружается...",
        "en": "Loading...",
    },
    "file_not_found": {
        "uz": "❌ Fayl topilmadi. Iltimos, ustozdan darsni qayta yuklashni so'rang.",
        "ru": "❌ Файл не найден. Пожалуйста, попросите преподавателя загрузить урок заново.",
        "en": "❌ File not found. Please ask the teacher to upload the lesson again.",
    },
}


def st(key: str, lang: str = "uz", **kwargs) -> str:
    item = LOCAL_TEXTS.get(key, {})
    text = item.get(lang) or item.get("uz") or key
    return text.format(**kwargs)


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


def record_value(record, key: str, default=None):
    """asyncpg.Record uchun xavfsiz getter."""
    if not record:
        return default

    try:
        if key in record.keys():
            return record[key]
    except Exception:
        pass

    return default


# ==========================================
# 1. MENING DARSLARIM TUGMASI
# ==========================================

@student_router.message(F.text.in_(all_texts("my_lessons")))
async def show_my_lessons(message: types.Message):
    lang = await user_lang(message.from_user.id)

    groups = await get_student_groups(message.from_user.id)

    if not groups:
        await message.answer(st("no_groups", lang))
        return

    builder = InlineKeyboardBuilder()

    for grp in groups:
        builder.button(
            text=f"{grp['name']} ({grp['language']})",
            callback_data=StudentGroupCB(group_id=grp["id"])
        )

    builder.adjust(1)

    await message.answer(
        st("choose_group", lang),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 2. GURUH TANLANGANDA -> DARSLAR RO'YXATI
# ==========================================

@student_router.callback_query(StudentGroupCB.filter())
async def show_group_lessons(callback: types.CallbackQuery, callback_data: StudentGroupCB):
    lang = await user_lang(callback.from_user.id)

    group_id = callback_data.group_id
    lessons = await get_group_lessons(group_id)

    if not lessons:
        await callback.answer(st("no_lessons", lang), show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    for lesson in lessons:
        builder.button(
            text=f"▶️ {lesson['title']}",
            callback_data=LessonCB(lesson_id=lesson["id"])
        )

    builder.adjust(1)

    await callback.message.edit_text(
        st("choose_lesson", lang),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 3. DARS TANLANGANDA -> FAYLNI YUBORISH
# ==========================================

@student_router.callback_query(LessonCB.filter())
async def send_lesson_file(callback: types.CallbackQuery, callback_data: LessonCB, bot: Bot):
    lang = await user_lang(callback.from_user.id)

    lesson_id = callback_data.lesson_id
    lesson = await get_lesson_by_id(lesson_id)

    if not lesson:
        await callback.answer(st("lesson_not_found", lang), show_alert=True)
        return

    await callback.answer(st("loading", lang))

    title = record_value(lesson, "title", "Lesson")
    material_path = record_value(lesson, "video_path")
    material_type = record_value(lesson, "material_type")
    original_filename = record_value(lesson, "original_filename")

    if material_path:
        original_filename = original_filename or os.path.basename(str(material_path))

    # Local storage orqali yuborish
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
    if material_path:
        try:
            await bot.send_video(
                chat_id=callback.message.chat.id,
                video=material_path,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
            return
        except Exception:
            pass

        try:
            await bot.send_document(
                chat_id=callback.message.chat.id,
                document=material_path,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
            return
        except Exception:
            pass

        try:
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=material_path,
                caption=f"📚 <b>{title}</b>",
                parse_mode="HTML"
            )
            return
        except Exception:
            pass

    await callback.message.answer(st("file_not_found", lang))