# handlers/teacher.py
import os
import uuid

from aiogram import Router, types, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    get_teacher_groups,
    get_user_role,
    get_group_info,
    add_lesson,
    get_teacher_group_students,
    add_student_result,
    add_kick_request,
    get_full_profile,
    teacher_owns_group,
    get_user_interface_lang,
    get_payment_admin_ids,
)
from utils.states import (
    UploadLesson,
    GroupManageCB,
    ResultEntry,
    KickRequestState,
    TeacherGroupCB,
    TeacherStudentCB,
    KickApproveCB,
    KickRejectCB,
)

teacher_router = Router()


# ==========================================
# LOCAL TRANSLATIONS FOR TEACHER.PY
# ==========================================

LOCAL_TEXTS = {
    "my_groups_button": {
        "uz": "📚 Mening guruhlarim",
        "ru": "📚 Мои группы",
        "en": "📚 My groups",
    },
    "enter_result_button": {
        "uz": "📝 Natija kiritish",
        "ru": "📝 Ввести результат",
        "en": "📝 Enter result",
    },
    "kick_request_button": {
        "uz": "❌ Chetlatish so'rovi",
        "ru": "❌ Запрос на исключение",
        "en": "❌ Removal request",
    },
    "only_teachers": {
        "uz": "Bu bo'lim faqat ustozlar uchun.",
        "ru": "Этот раздел только для преподавателей.",
        "en": "This section is only for teachers.",
    },
    "no_groups": {
        "uz": "Sizga hozircha hech qanday guruh biriktirilmagan.",
        "ru": "Вам пока не назначена ни одна группа.",
        "en": "No groups have been assigned to you yet.",
    },
    "your_groups": {
        "uz": "📚 <b>Sizning faol guruhlaringiz:</b>\n\n",
        "ru": "📚 <b>Ваши активные группы:</b>\n\n",
        "en": "📚 <b>Your active groups:</b>\n\n",
    },
    "limit": {
        "uz": "👥 Limit",
        "ru": "👥 Лимит",
        "en": "👥 Limit",
    },
    "management": {
        "uz": "⚙️ Boshqaruv",
        "ru": "⚙️ Управление",
        "en": "⚙️ Management",
    },
    "wrong_group_id": {
        "uz": "Guruh ID noto'g'ri kiritildi.",
        "ru": "ID группы введён неверно.",
        "en": "Group ID is incorrect.",
    },
    "no_access_group": {
        "uz": "⛔ Siz bu guruhni boshqara olmaysiz.",
        "ru": "⛔ Вы не можете управлять этой группой.",
        "en": "⛔ You cannot manage this group.",
    },
    "group_not_found": {
        "uz": "Guruh topilmadi yoki faol emas!",
        "ru": "Группа не найдена или неактивна!",
        "en": "Group was not found or is not active!",
    },
    "add_lesson": {
        "uz": "➕ Dars yuklash",
        "ru": "➕ Загрузить урок",
        "en": "➕ Upload lesson",
    },
    "students": {
        "uz": "👥 O'quvchilar",
        "ru": "👥 Студенты",
        "en": "👥 Students",
    },
    "group_panel": {
        "uz": "⚙️ <b>{group_name}</b> guruhini boshqarish paneli.\n\nNima ish qilinadi?",
        "ru": "⚙️ Панель управления группой <b>{group_name}</b>.\n\nЧто нужно сделать?",
        "en": "⚙️ Management panel for <b>{group_name}</b>.\n\nWhat would you like to do?",
    },
    "lesson_title_request": {
        "uz": "📝 <b>Yangi dars mavzusini kiriting:</b>\n<i>(Masalan: 1-Dars. Present Simple)</i>",
        "ru": "📝 <b>Введите тему нового урока:</b>\n<i>(Например: Урок 1. Present Simple)</i>",
        "en": "📝 <b>Enter the new lesson title:</b>\n<i>(Example: Lesson 1. Present Simple)</i>",
    },
    "lesson_material_request": {
        "uz": "📂 Endi dars materialini (Video, PDF yoki rasm) botga yuboring.",
        "ru": "📂 Теперь отправьте материал урока боту: видео, PDF или изображение.",
        "en": "📂 Now send the lesson material to the bot: video, PDF, or image.",
    },
    "missing_data": {
        "uz": "Ma'lumotlar to'liq emas. Iltimos, jarayonni qaytadan boshlang.",
        "ru": "Данные неполные. Пожалуйста, начните процесс заново.",
        "en": "The data is incomplete. Please start the process again.",
    },
    "no_access_upload": {
        "uz": "⛔ Siz bu guruhga dars yuklay olmaysiz.",
        "ru": "⛔ Вы не можете загрузить урок в эту группу.",
        "en": "⛔ You cannot upload a lesson to this group.",
    },
    "send_material": {
        "uz": "Iltimos, video, PDF yoki rasm yuboring.",
        "ru": "Пожалуйста, отправьте видео, PDF или изображение.",
        "en": "Please send a video, PDF, or image.",
    },
    "lesson_saved": {
        "uz": "✅ <b>{title}</b> nomli dars local storage'ga saqlandi!\n\n🆔 Dars ID: {lesson_id}\n📁 Fayl yo'li: <code>{local_path}</code>\n\nO'quvchilar bu darsni Mini App orqali ko'rishi mumkin.",
        "ru": "✅ Урок <b>{title}</b> сохранён в local storage!\n\n🆔 ID урока: {lesson_id}\n📁 Путь файла: <code>{local_path}</code>\n\nСтуденты смогут посмотреть этот урок через Mini App.",
        "en": "✅ Lesson <b>{title}</b> has been saved to local storage!\n\n🆔 Lesson ID: {lesson_id}\n📁 File path: <code>{local_path}</code>\n\nStudents can view this lesson through the Mini App.",
    },
    "no_students": {
        "uz": "Bu guruhda hozircha o'quvchilar yo'q.",
        "ru": "В этой группе пока нет студентов.",
        "en": "There are no students in this group yet.",
    },
    "group_students": {
        "uz": "👥 <b>Guruhdagi o'quvchilar:</b>\n\n",
        "ru": "👥 <b>Студенты группы:</b>\n\n",
        "en": "👥 <b>Students in this group:</b>\n\n",
    },
    "name_empty": {
        "uz": "Ism kiritilmagan",
        "ru": "Имя не указано",
        "en": "Name not entered",
    },
    "phone_empty": {
        "uz": "Telefon yo'q",
        "ru": "Телефон не указан",
        "en": "No phone",
    },
    "choose_group_result": {
        "uz": "📝 Qaysi guruh uchun natija kiritmoqchisiz?",
        "ru": "📝 Для какой группы вы хотите ввести результат?",
        "en": "📝 Which group would you like to enter a result for?",
    },
    "choose_student_result": {
        "uz": "Qaysi o'quvchiga natija kiritamiz?",
        "ru": "Какому студенту вводим результат?",
        "en": "Which student should receive the result?",
    },
    "result_title_request": {
        "uz": "📝 Natija nomini kiriting:\n\nMasalan:\n1-test\nOraliq imtihon\nSpeaking natijasi",
        "ru": "📝 Введите название результата:\n\nНапример:\nТест 1\nПромежуточный экзамен\nSpeaking result",
        "en": "📝 Enter the result title:\n\nExamples:\nTest 1\nMidterm exam\nSpeaking result",
    },
    "score_request": {
        "uz": "📊 Ball yoki natijani kiriting:\n\nMasalan: 85/100 yoki Passed",
        "ru": "📊 Введите балл или результат:\n\nНапример: 85/100 или Passed",
        "en": "📊 Enter the score or result:\n\nExample: 85/100 or Passed",
    },
    "comment_request": {
        "uz": "💬 Izoh kiriting.\n\nAgar izoh yo'q bo'lsa, `-` yuboring.",
        "ru": "💬 Введите комментарий.\n\nЕсли комментария нет, отправьте `-`.",
        "en": "💬 Enter a comment.\n\nIf there is no comment, send `-`.",
    },
    "no_access_result": {
        "uz": "⛔ Siz bu guruhga natija kirita olmaysiz.",
        "ru": "⛔ Вы не можете вводить результаты для этой группы.",
        "en": "⛔ You cannot enter results for this group.",
    },
    "result_saved": {
        "uz": "✅ Natija saqlandi!\n\n🆔 Natija ID: {result_id}\n📚 Guruh: {group_name}\n📝 Natija: {result_title}\n📊 Ball: {score}",
        "ru": "✅ Результат сохранён!\n\n🆔 ID результата: {result_id}\n📚 Группа: {group_name}\n📝 Результат: {result_title}\n📊 Балл: {score}",
        "en": "✅ Result saved!\n\n🆔 Result ID: {result_id}\n📚 Group: {group_name}\n📝 Result: {result_title}\n📊 Score: {score}",
    },
    "student_new_result": {
        "uz": "📊 <b>Sizga yangi natija kiritildi.</b>\n\n📚 Guruh: {group_name}\n📝 Natija: {result_title}\n📊 Ball: {score}",
        "ru": "📊 <b>Вам добавлен новый результат.</b>\n\n📚 Группа: {group_name}\n📝 Результат: {result_title}\n📊 Балл: {score}",
        "en": "📊 <b>A new result has been added for you.</b>\n\n📚 Group: {group_name}\n📝 Result: {result_title}\n📊 Score: {score}",
    },
    "comment_label": {
        "uz": "💬 Izoh",
        "ru": "💬 Комментарий",
        "en": "💬 Comment",
    },
    "choose_group_kick": {
        "uz": "❌ Qaysi guruhdan o'quvchini chetlatish so'rovi yubormoqchisiz?",
        "ru": "❌ Из какой группы вы хотите отправить запрос на исключение студента?",
        "en": "❌ From which group would you like to request a student removal?",
    },
    "choose_student_kick": {
        "uz": "Qaysi o'quvchi bo'yicha so'rov yuboramiz?",
        "ru": "По какому студенту отправляем запрос?",
        "en": "Which student should the request be about?",
    },
    "kick_reason_request": {
        "uz": "❌ <b>{student_name}</b> bo'yicha chetlatish sababini yozing:\n\nMasalan: 3 marta darsga kelmadi, testlarni topshirmadi.",
        "ru": "❌ Напишите причину исключения для <b>{student_name}</b>:\n\nНапример: 3 раза не пришёл на урок, не сдавал тесты.",
        "en": "❌ Write the reason for removing <b>{student_name}</b>:\n\nExample: missed 3 classes, did not submit tests.",
    },
    "no_access_kick": {
        "uz": "⛔ Siz bu guruh bo'yicha chetlatish so'rovi yubora olmaysiz.",
        "ru": "⛔ Вы не можете отправить запрос на исключение по этой группе.",
        "en": "⛔ You cannot send a removal request for this group.",
    },
    "kick_sent": {
        "uz": "✅ Chetlatish so'rovi adminga yuborildi.\n\nAdmin qaror qabul qilgandan keyin sizga xabar beriladi.",
        "ru": "✅ Запрос на исключение отправлен администратору.\n\nПосле решения администратора вы получите уведомление.",
        "en": "✅ Removal request has been sent to the admin.\n\nYou will be notified after the admin makes a decision.",
    },
}


def tt(key: str, lang: str = "uz", **kwargs) -> str:
    item = LOCAL_TEXTS.get(key, {})
    text = item.get(lang) or item.get("uz") or key
    return text.format(**kwargs)


def all_teacher_texts(key: str):
    item = LOCAL_TEXTS.get(key, {})
    return list(item.values())


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


# ==========================================
# TEACHER ACCESS CHECKS
# ==========================================

async def is_teacher(message: types.Message):
    role = await get_user_role(message.from_user.id)
    return role == "teacher"


async def is_teacher_callback(callback: types.CallbackQuery):
    role = await get_user_role(callback.from_user.id)
    return role == "teacher"


# ==========================================
# 1. MENING GURUHLARIM
# ==========================================

@teacher_router.message(F.text.in_(all_teacher_texts("my_groups_button")))
async def show_my_groups(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        return

    await state.clear()
    groups = await get_teacher_groups(message.from_user.id)

    if not groups:
        await message.answer(tt("no_groups", lang))
        return

    text = tt("your_groups", lang)

    for idx, grp in enumerate(groups, start=1):
        text += f"{idx}. <b>{grp['name']}</b> <i>({grp['language']})</i>\n"
        text += f"{tt('limit', lang)}: {grp['max_capacity']} kishi\n"
        text += f"{tt('management', lang)}: /group_{grp['id']}\n\n"

    await message.answer(text, parse_mode="HTML")


# ==========================================
# 2. GURUH PANELIGA KIRISH
# ==========================================

@teacher_router.message(F.text.startswith("/group_"))
async def group_panel(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        return

    await state.clear()

    try:
        group_id = int(message.text.split("_")[1])
    except Exception:
        await message.answer(tt("wrong_group_id", lang))
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer(tt("no_access_group", lang))
        return

    group_data = await get_group_info(group_id)

    if not group_data:
        await message.answer(tt("group_not_found", lang))
        return

    builder = InlineKeyboardBuilder()
    builder.button(
        text=tt("add_lesson", lang),
        callback_data=GroupManageCB(group_id=group_id, action="add_lesson")
    )
    builder.button(
        text=tt("students", lang),
        callback_data=GroupManageCB(group_id=group_id, action="list_students")
    )
    builder.adjust(2)

    await message.answer(
        tt("group_panel", lang, group_name=group_data["name"]),
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 3. DARS YUKLASH JARAYONI BOSHLANISHI
# ==========================================

@teacher_router.callback_query(GroupManageCB.filter(F.action == "add_lesson"))
async def start_add_lesson(callback: types.CallbackQuery, callback_data: GroupManageCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    if not await is_teacher_callback(callback):
        await callback.answer(tt("only_teachers", lang), show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer(tt("no_access_group", lang), show_alert=True)
        return

    await state.update_data(group_id=callback_data.group_id)

    await callback.message.edit_text(
        tt("lesson_title_request", lang),
        parse_mode="HTML"
    )
    await state.set_state(UploadLesson.title)


@teacher_router.message(UploadLesson.title)
async def process_lesson_title(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        await state.clear()
        return

    await state.update_data(title=message.text)

    await message.answer(
        tt("lesson_material_request", lang),
        parse_mode="HTML"
    )
    await state.set_state(UploadLesson.material)


# ==========================================
# 4. FAYL QABUL QILISH VA BAZAGA SAQLASH
# ==========================================

@teacher_router.message(UploadLesson.material, F.video | F.document | F.photo)
async def process_lesson_material(message: types.Message, state: FSMContext, bot: Bot):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        await state.clear()
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    title = data.get("title")

    if not group_id or not title:
        await message.answer(tt("missing_data", lang))
        await state.clear()
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer(tt("no_access_upload", lang))
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
        await message.answer(tt("send_material", lang))
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
        tt(
            "lesson_saved",
            lang,
            title=title,
            lesson_id=lesson_id,
            local_path=local_path
        ),
        parse_mode="HTML"
    )
    await state.clear()


# ==========================================
# 5. GURUH ICHIDAGI O'QUVCHILARNI KO'RISH
# ==========================================

@teacher_router.callback_query(GroupManageCB.filter(F.action == "list_students"))
async def list_students_in_group(callback: types.CallbackQuery, callback_data: GroupManageCB):
    lang = await user_lang(callback.from_user.id)

    if not await is_teacher_callback(callback):
        await callback.answer(tt("only_teachers", lang), show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer(tt("no_access_group", lang), show_alert=True)
        return

    students = await get_teacher_group_students(callback.from_user.id, callback_data.group_id)

    if not students:
        await callback.answer(tt("no_students", lang), show_alert=True)
        return

    text = tt("group_students", lang)

    for idx, student in enumerate(students, start=1):
        full_name = student["full_name"] or tt("name_empty", lang)
        phone = student["phone"] or tt("phone_empty", lang)
        text += f"{idx}. <b>{full_name}</b>\n📞 {phone}\n\n"

    await callback.message.edit_text(text, parse_mode="HTML")


# ==========================================
# 6. NATIJA KIRITISH MODULI
# ==========================================

@teacher_router.message(F.text.in_(all_teacher_texts("enter_result_button")))
async def enter_results(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        return

    await state.clear()
    groups = await get_teacher_groups(message.from_user.id)

    if not groups:
        await message.answer(tt("no_groups", lang))
        return

    builder = InlineKeyboardBuilder()

    for grp in groups:
        builder.button(
            text=f"{grp['name']} ({grp['language']})",
            callback_data=TeacherGroupCB(group_id=grp["id"], action="result")
        )

    builder.adjust(1)

    await message.answer(
        tt("choose_group_result", lang),
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherGroupCB.filter(F.action == "result"))
async def choose_group_for_result(callback: types.CallbackQuery, callback_data: TeacherGroupCB):
    lang = await user_lang(callback.from_user.id)

    if not await is_teacher_callback(callback):
        await callback.answer(tt("only_teachers", lang), show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer(tt("no_access_group", lang), show_alert=True)
        return

    students = await get_teacher_group_students(callback.from_user.id, callback_data.group_id)

    if not students:
        await callback.answer(tt("no_students", lang), show_alert=True)
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
        tt("choose_student_result", lang),
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherStudentCB.filter(F.action == "result"))
async def choose_student_for_result(callback: types.CallbackQuery, callback_data: TeacherStudentCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    if not await is_teacher_callback(callback):
        await callback.answer(tt("only_teachers", lang), show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer(tt("no_access_group", lang), show_alert=True)
        return

    await state.update_data(
        group_id=callback_data.group_id,
        student_id=callback_data.student_id
    )

    await callback.message.edit_text(tt("result_title_request", lang))
    await state.set_state(ResultEntry.title)


@teacher_router.message(ResultEntry.title)
async def process_result_title(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        await state.clear()
        return

    await state.update_data(result_title=message.text)

    await message.answer(tt("score_request", lang))
    await state.set_state(ResultEntry.score)


@teacher_router.message(ResultEntry.score)
async def process_result_score(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        await state.clear()
        return

    await state.update_data(score=message.text)

    await message.answer(tt("comment_request", lang))
    await state.set_state(ResultEntry.comment)


@teacher_router.message(ResultEntry.comment)
async def process_result_comment(message: types.Message, state: FSMContext, bot: Bot):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        await state.clear()
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    student_id = data.get("student_id")

    if not group_id or not student_id:
        await message.answer(tt("missing_data", lang))
        await state.clear()
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer(tt("no_access_result", lang))
        await state.clear()
        return

    comment = message.text.strip()

    if comment in ["-", "yo'q", "yoq", "Yo'q", "Yoq", "нет", "Нет", "no", "No"]:
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
        tt(
            "result_saved",
            lang,
            result_id=result_id,
            group_name=group_name,
            result_title=data["result_title"],
            score=data["score"]
        ),
        parse_mode="HTML"
    )

    try:
        student_lang = await user_lang(student_id)

        student_text = tt(
            "student_new_result",
            student_lang,
            group_name=group_name,
            result_title=data["result_title"],
            score=data["score"]
        )

        if comment:
            student_text += f"\n{tt('comment_label', student_lang)}: {comment}"

        await bot.send_message(
            chat_id=student_id,
            text=student_text,
            parse_mode="HTML"
        )
    except Exception:
        pass

    await state.clear()


# ==========================================
# 7. CHETLATISH SO'ROVI MODULI
# ==========================================

@teacher_router.message(F.text.in_(all_teacher_texts("kick_request_button")))
async def kick_request_start(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        return

    await state.clear()
    groups = await get_teacher_groups(message.from_user.id)

    if not groups:
        await message.answer(tt("no_groups", lang))
        return

    builder = InlineKeyboardBuilder()

    for grp in groups:
        builder.button(
            text=f"{grp['name']} ({grp['language']})",
            callback_data=TeacherGroupCB(group_id=grp["id"], action="kick")
        )

    builder.adjust(1)

    await message.answer(
        tt("choose_group_kick", lang),
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherGroupCB.filter(F.action == "kick"))
async def choose_group_for_kick(callback: types.CallbackQuery, callback_data: TeacherGroupCB):
    lang = await user_lang(callback.from_user.id)

    if not await is_teacher_callback(callback):
        await callback.answer(tt("only_teachers", lang), show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer(tt("no_access_group", lang), show_alert=True)
        return

    students = await get_teacher_group_students(callback.from_user.id, callback_data.group_id)

    if not students:
        await callback.answer(tt("no_students", lang), show_alert=True)
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
        tt("choose_student_kick", lang),
        reply_markup=builder.as_markup()
    )


@teacher_router.callback_query(TeacherStudentCB.filter(F.action == "kick"))
async def choose_student_for_kick(callback: types.CallbackQuery, callback_data: TeacherStudentCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    if not await is_teacher_callback(callback):
        await callback.answer(tt("only_teachers", lang), show_alert=True)
        return

    if not await teacher_owns_group(callback.from_user.id, callback_data.group_id):
        await callback.answer(tt("no_access_group", lang), show_alert=True)
        return

    await state.update_data(
        group_id=callback_data.group_id,
        student_id=callback_data.student_id
    )

    student = await get_full_profile(callback_data.student_id)
    student_name = student["full_name"] if student else str(callback_data.student_id)

    await callback.message.edit_text(
        tt("kick_reason_request", lang, student_name=student_name),
        parse_mode="HTML"
    )

    await state.set_state(KickRequestState.reason)


@teacher_router.message(KickRequestState.reason)
async def process_kick_reason(message: types.Message, state: FSMContext, bot: Bot):
    lang = await user_lang(message.from_user.id)

    if not await is_teacher(message):
        await state.clear()
        return

    data = await state.get_data()
    group_id = data.get("group_id")
    student_id = data.get("student_id")
    reason = message.text

    if not group_id or not student_id:
        await message.answer(tt("missing_data", lang))
        await state.clear()
        return

    if not await teacher_owns_group(message.from_user.id, group_id):
        await message.answer(tt("no_access_kick", lang))
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

    admin_ids = await get_payment_admin_ids()

    if admin_ids:
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

        for admin_id in admin_ids:
            try:
                await bot.send_message(
                    chat_id=admin_id,
                    text=admin_text,
                    parse_mode="HTML",
                    reply_markup=builder.as_markup()
                )
            except Exception:
                pass

    await message.answer(tt("kick_sent", lang))

    await state.clear()