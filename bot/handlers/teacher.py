# handlers/teacher.py
import os
import uuid
from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    get_teacher_groups, get_user_role, get_group_info, add_lesson,
    get_teacher_group_students, add_student_result, add_kick_request,
    get_full_profile, teacher_owns_group
)
from utils.states import (
    UploadLesson, GroupManageCB,
    ResultEntry, KickRequestState,
    TeacherGroupCB, TeacherStudentCB,
    KickApproveCB, KickRejectCB
)

teacher_router = Router()


# Faqat ustozlar ishlata olishi uchun himoya filtri
async def is_teacher(message: types.Message):
    role = await get_user_role(message.from_user.id)
    return role == "teacher"


async def is_teacher_callback(callback: types.CallbackQuery):
    role = await get_user_role(callback.from_user.id)
    return role == "teacher"


# --- 1. MENING GURUHLARIM ---
@teacher_router.message(F.text == "📚 Mening guruhlarim")
async def show_my_groups(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        return

    await state.clear()
    groups = await get_teacher_groups(message.from_user.id)

    if not groups:
        await message.answer("Sizga hozircha hech qanday guruh biriktirilmagan.")
        return

    text = "📚 <b>Sizning faol guruhlaringiz:</b>\n\n"
    for idx, grp in enumerate(groups, start=1):
        text += f"{idx}. <b>{grp['name']}</b> <i>({grp['language']})</i>\n"
        text += f"👥 Limit: {grp['max_capacity']} kishi\n"
        text += f"⚙️ Boshqaruv: /group_{grp['id']}\n\n"

    await message.answer(text, parse_mode="HTML")


# --- 2. GURUH PANELIGA KIRISH (Masalan: /group_1) ---
@teacher_router.message(F.text.startswith("/group_"))
async def group_panel(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        return

    await state.clear()

    try:
        group_id = int(message.text.split("_")[1])
    except Exception:
        await message.answer("Guruh ID noto'g'ri kiritildi.")
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer("⛔ Siz bu guruhni boshqara olmaysiz.")
        return

    group_data = await get_group_info(group_id)

    if not group_data:
        await message.answer("Guruh topilmadi yoki faol emas!")
        return

    builder = InlineKeyboardBuilder()
    builder.button(
        text="➕ Dars yuklash",
        callback_data=GroupManageCB(group_id=group_id, action="add_lesson")
    )
    builder.button(
        text="👥 O'quvchilar",
        callback_data=GroupManageCB(group_id=group_id, action="list_students")
    )
    builder.adjust(2)

    await message.answer(
        f"⚙️ <b>{group_data['name']}</b> guruhini boshqarish paneli.\n\n"
        f"Nima ish qilinadi?",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# --- 3. DARS YUKLASH JARAYONI BOSHLANISHI ---
@teacher_router.callback_query(GroupManageCB.filter(F.action == "add_lesson"))
async def start_add_lesson(callback: types.CallbackQuery, callback_data: GroupManageCB, state: FSMContext):
    if not await is_teacher_callback(callback):
        await callback.answer("Bu bo'lim faqat ustozlar uchun.", show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer("Siz bu guruhni boshqara olmaysiz.", show_alert=True)
        return

    await state.update_data(group_id=callback_data.group_id)

    await callback.message.edit_text(
        "📝 <b>Yangi dars mavzusini kiriting:</b>\n"
        "<i>(Masalan: 1-Dars. Present Simple)</i>",
        parse_mode="HTML"
    )
    await state.set_state(UploadLesson.title)


@teacher_router.message(UploadLesson.title)
async def process_lesson_title(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        await state.clear()
        return

    await state.update_data(title=message.text)

    await message.answer(
        "📂 Endi dars materialini (Video yoki PDF fayl) botga yuboring.\n\n",
        parse_mode="HTML"
    )
    await state.set_state(UploadLesson.material)


# --- 4. FAYL QABUL QILISH VA BAZAGA SAQLASH ---
@teacher_router.message(UploadLesson.material, F.video | F.document | F.photo)
async def process_lesson_material(message: types.Message, state: FSMContext, bot: Bot):
    if not await is_teacher(message):
        await state.clear()
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    title = data.get("title")

    if not group_id or not title:
        await message.answer("Ma'lumotlar to'liq emas. Iltimos, jarayonni qaytadan boshlang.")
        await state.clear()
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer("⛔ Siz bu guruhga dars yuklay olmaysiz.")
        await state.clear()
        return

    file_id = None
    material_type = None
    original_filename = None
    file_size = None
    ext = None

    if message.video:
        file_id = message.video.file_id
        material_type = "video"
        original_filename = message.video.file_name or "lesson_video.mp4"
        file_size = message.video.file_size
        ext = os.path.splitext(original_filename)[1] or ".mp4"

    elif message.document:
        file_id = message.document.file_id
        material_type = "document"
        original_filename = message.document.file_name or "lesson_file"
        file_size = message.document.file_size
        ext = os.path.splitext(original_filename)[1] or ".bin"

    elif message.photo:
        file_id = message.photo[-1].file_id
        material_type = "photo"
        original_filename = "lesson_photo.jpg"
        file_size = message.photo[-1].file_size
        ext = ".jpg"

    if not file_id:
        await message.answer("Iltimos, video, PDF yoki rasm yuboring.")
        return

    folder_path = f"media/lessons/group_{group_id}"
    os.makedirs(folder_path, exist_ok=True)

    unique_name = f"lesson_{uuid.uuid4().hex}{ext}"
    local_path = f"{folder_path}/{unique_name}"

    telegram_file = await bot.get_file(file_id)
    await bot.download_file(telegram_file.file_path, local_path)

    lesson_id = await add_lesson(
        group_id=group_id,
        title=title,
        material_path=local_path,
        material_type=material_type,
        original_filename=original_filename,
        file_size=file_size
    )

    await message.answer(
        f"✅ <b>{title}</b> nomli dars local storage'ga saqlandi!\n\n"
        f"🆔 Dars ID: {lesson_id}\n"
        f"📁 Fayl yo'li: <code>{local_path}</code>\n\n"
        "O'quvchilar bu darsni Mini App orqali ko'rishi mumkin.",
        parse_mode="HTML"
    )
    await state.clear()


# --- 5. GURUH ICHIDAGI O'QUVCHILARNI KO'RISH ---
@teacher_router.callback_query(GroupManageCB.filter(F.action == "list_students"))
async def list_students_in_group(callback: types.CallbackQuery, callback_data: GroupManageCB):
    if not await is_teacher_callback(callback):
        await callback.answer("Bu bo'lim faqat ustozlar uchun.", show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer("Siz bu guruhni boshqara olmaysiz.", show_alert=True)
        return

    students = await get_teacher_group_students(callback.from_user.id, callback_data.group_id)

    if not students:
        await callback.answer("Bu guruhda hozircha o'quvchilar yo'q.", show_alert=True)
        return

    text = "👥 <b>Guruhdagi o'quvchilar:</b>\n\n"
    for idx, student in enumerate(students, start=1):
        full_name = student["full_name"] or "Ism kiritilmagan"
        phone = student["phone"] or "Telefon yo'q"
        text += f"{idx}. <b>{full_name}</b>\n📞 {phone}\n\n"

    await callback.message.edit_text(text, parse_mode="HTML")


# ==========================================
# NATIJA KIRITISH MODULI
# ==========================================

@teacher_router.message(F.text == "📝 Natija kiritish")
async def enter_results(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        return

    await state.clear()
    groups = await get_teacher_groups(message.from_user.id)

    if not groups:
        await message.answer("Sizga hozircha hech qanday guruh biriktirilmagan.")
        return

    builder = InlineKeyboardBuilder()
    for grp in groups:
        builder.button(
            text=f"{grp['name']} ({grp['language']})",
            callback_data=TeacherGroupCB(group_id=grp["id"], action="result")
        )
    builder.adjust(1)

    await message.answer(
        "📝 Qaysi guruh uchun natija kiritmoqchisiz?",
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherGroupCB.filter(F.action == "result"))
async def choose_group_for_result(callback: types.CallbackQuery, callback_data: TeacherGroupCB):
    if not await is_teacher_callback(callback):
        await callback.answer("Bu bo'lim faqat ustozlar uchun.", show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer("Siz bu guruhni boshqara olmaysiz.", show_alert=True)
        return

    students = await get_teacher_group_students(callback.from_user.id, callback_data.group_id)

    if not students:
        await callback.answer("Bu guruhda hozircha o'quvchilar yo'q.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for student in students:
        full_name = student["full_name"] or str(student["telegram_id"])
        builder.button(
            text=full_name,
            callback_data=TeacherStudentCB(
                group_id=callback_data.group_id,
                student_id=student["telegram_id"],
                action="result"
            )
        )
    builder.adjust(1)

    await callback.message.edit_text(
        "Qaysi o'quvchiga natija kiritamiz?",
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherStudentCB.filter(F.action == "result"))
async def choose_student_for_result(callback: types.CallbackQuery, callback_data: TeacherStudentCB, state: FSMContext):
    if not await is_teacher_callback(callback):
        await callback.answer("Bu bo'lim faqat ustozlar uchun.", show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer("Siz bu guruhni boshqara olmaysiz.", show_alert=True)
        return

    await state.update_data(
        group_id=callback_data.group_id,
        student_id=callback_data.student_id
    )

    await callback.message.edit_text(
        "📝 Natija nomini kiriting:\n\n"
        "Masalan:\n"
        "1-test\n"
        "Oraliq imtihon\n"
        "Speaking natijasi"
    )
    await state.set_state(ResultEntry.title)


@teacher_router.message(ResultEntry.title)
async def process_result_title(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        await state.clear()
        return

    await state.update_data(result_title=message.text)

    await message.answer(
        "📊 Ball yoki natijani kiriting:\n\n"
        "Masalan: 85/100 yoki Passed"
    )
    await state.set_state(ResultEntry.score)


@teacher_router.message(ResultEntry.score)
async def process_result_score(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        await state.clear()
        return

    await state.update_data(score=message.text)

    await message.answer(
        "💬 Izoh kiriting.\n\n"
        "Agar izoh yo'q bo'lsa, `-` yuboring."
    )
    await state.set_state(ResultEntry.comment)


@teacher_router.message(ResultEntry.comment)
async def process_result_comment(message: types.Message, state: FSMContext, bot: Bot):
    if not await is_teacher(message):
        await state.clear()
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    student_id = data.get("student_id")

    if not group_id or not student_id:
        await message.answer("Ma'lumotlar to'liq emas. Iltimos, jarayonni qaytadan boshlang.")
        await state.clear()
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer("⛔ Siz bu guruhga natija kirita olmaysiz.")
        await state.clear()
        return

    comment = message.text
    if comment.strip() in ["-", "yo'q", "yoq", "Yo'q", "Yoq"]:
        comment = ""

    result_id = await add_student_result(
        user_id=student_id,
        group_id=group_id,
        teacher_id=message.from_user.id,
        result_title=data["result_title"],
        score=data["score"],
        comment=comment
    )

    group = await get_group_info(group_id)
    group_name = group["name"] if group else str(group_id)

    await message.answer(
        f"✅ Natija saqlandi!\n\n"
        f"🆔 Natija ID: {result_id}\n"
        f"📚 Guruh: {group_name}\n"
        f"📝 Natija: {data['result_title']}\n"
        f"📊 Ball: {data['score']}",
        parse_mode="HTML"
    )

    try:
        student_text = (
            f"📊 <b>Sizga yangi natija kiritildi.</b>\n\n"
            f"📚 Guruh: {group_name}\n"
            f"📝 Natija: {data['result_title']}\n"
            f"📊 Ball: {data['score']}"
        )
        if comment:
            student_text += f"\n💬 Izoh: {comment}"

        await bot.send_message(
            chat_id=student_id,
            text=student_text,
            parse_mode="HTML"
        )
    except Exception:
        pass

    await state.clear()


# ==========================================
# CHETLATISH SO'ROVI MODULI
# ==========================================

@teacher_router.message(F.text == "❌ Chetlatish so'rovi")
async def kick_request_start(message: types.Message, state: FSMContext):
    if not await is_teacher(message):
        return

    await state.clear()
    groups = await get_teacher_groups(message.from_user.id)

    if not groups:
        await message.answer("Sizga hozircha hech qanday guruh biriktirilmagan.")
        return

    builder = InlineKeyboardBuilder()
    for grp in groups:
        builder.button(
            text=f"{grp['name']} ({grp['language']})",
            callback_data=TeacherGroupCB(group_id=grp["id"], action="kick")
        )
    builder.adjust(1)

    await message.answer(
        "❌ Qaysi guruhdan o'quvchini chetlatish so'rovi yubormoqchisiz?",
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherGroupCB.filter(F.action == "kick"))
async def choose_group_for_kick(callback: types.CallbackQuery, callback_data: TeacherGroupCB):
    if not await is_teacher_callback(callback):
        await callback.answer("Bu bo'lim faqat ustozlar uchun.", show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer("Siz bu guruhni boshqara olmaysiz.", show_alert=True)
        return

    students = await get_teacher_group_students(callback.from_user.id, callback_data.group_id)

    if not students:
        await callback.answer("Bu guruhda hozircha o'quvchilar yo'q.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()
    for student in students:
        full_name = student["full_name"] or str(student["telegram_id"])
        builder.button(
            text=full_name,
            callback_data=TeacherStudentCB(
                group_id=callback_data.group_id,
                student_id=student["telegram_id"],
                action="kick"
            )
        )
    builder.adjust(1)

    await callback.message.edit_text(
        "Qaysi o'quvchi bo'yicha so'rov yuboramiz?",
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherStudentCB.filter(F.action == "kick"))
async def choose_student_for_kick(callback: types.CallbackQuery, callback_data: TeacherStudentCB, state: FSMContext):
    if not await is_teacher_callback(callback):
        await callback.answer("Bu bo'lim faqat ustozlar uchun.", show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer("Siz bu guruhni boshqara olmaysiz.", show_alert=True)
        return

    await state.update_data(
        group_id=callback_data.group_id,
        student_id=callback_data.student_id
    )

    student = await get_full_profile(callback_data.student_id)
    student_name = student["full_name"] if student else str(callback_data.student_id)

    await callback.message.edit_text(
        f"❌ <b>{student_name}</b> bo'yicha chetlatish sababini yozing:\n\n"
        f"Masalan: 3 marta darsga kelmadi, testlarni topshirmadi.",
        parse_mode="HTML"
    )
    await state.set_state(KickRequestState.reason)


@teacher_router.message(KickRequestState.reason)
async def process_kick_reason(message: types.Message, state: FSMContext, bot: Bot):
    if not await is_teacher(message):
        await state.clear()
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    student_id = data.get("student_id")
    reason = message.text

    if not group_id or not student_id:
        await message.answer("Ma'lumotlar to'liq emas. Iltimos, jarayonni qaytadan boshlang.")
        await state.clear()
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer("⛔ Siz bu guruh bo'yicha chetlatish so'rovi yubora olmaysiz.")
        await state.clear()
        return

    request_id = await add_kick_request(
        user_id=student_id,
        group_id=group_id,
        teacher_id=message.from_user.id,
        reason=reason
    )

    student = await get_full_profile(student_id)
    group = await get_group_info(group_id)

    student_name = student["full_name"] if student else str(student_id)
    group_name = group["name"] if group else str(group_id)

    admin_id = os.getenv("ADMIN_ID")

    if admin_id:
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Chetlatishni tasdiqlash",
            callback_data=KickApproveCB(request_id=request_id)
        )
        builder.button(
            text="❌ Rad etish",
            callback_data=KickRejectCB(request_id=request_id)
        )
        builder.adjust(1)

        admin_text = (
            f"❌ <b>Yangi chetlatish so'rovi!</b>\n\n"
            f"🆔 So'rov ID: {request_id}\n"
            f"👨‍🏫 Ustoz: {message.from_user.full_name}\n"
            f"👤 O'quvchi: {student_name}\n"
            f"📚 Guruh: {group_name}\n\n"
            f"📝 Sabab:\n{reason}"
        )

        await bot.send_message(
            chat_id=int(admin_id),
            text=admin_text,
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

    await message.answer(
        "✅ Chetlatish so'rovi adminga yuborildi.\n\n"
        "Admin qaror qabul qilgandan keyin sizga xabar beriladi."
    )

    await state.clear()