# handlers/user.py
import os

from aiogram import Router, types, F, Bot
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    add_user,
    update_user_profile,
    get_user_role,
    save_teacher_application,
    get_full_profile,
    get_management_staff_ids,
    get_user_interface_lang,
    set_user_interface_lang,
)
from utils.states import (
    Registration,
    RegionCB,
    DistrictCB,
    TeacherRegistration,
    LangSelectCB,
)
from utils.data import UZB_REGIONS
from utils.i18n import t, all_texts

user_router = Router()


# ==========================================
# LOCAL TRANSLATIONS FOR USER.PY
# ==========================================

LOCAL_TEXTS = {
    "back": {
        "uz": "🔙 Orqaga",
        "ru": "🔙 Назад",
        "en": "🔙 Back",
    },
    "send_phone": {
        "uz": "📞 Raqamni yuborish",
        "ru": "📞 Отправить номер",
        "en": "📞 Send phone number",
    },
    "teacher_my_groups": {
        "uz": "📚 Mening guruhlarim",
        "ru": "📚 Мои группы",
        "en": "📚 My groups",
    },
    "teacher_results": {
        "uz": "📝 Natija kiritish",
        "ru": "📝 Ввести результат",
        "en": "📝 Enter result",
    },
    "teacher_kick": {
        "uz": "❌ Chetlatish so'rovi",
        "ru": "❌ Запрос на исключение",
        "en": "❌ Removal request",
    },
    "confirm": {
        "uz": "✅ Tasdiqlash",
        "ru": "✅ Подтвердить",
        "en": "✅ Confirm",
    },
    "confirm_send": {
        "uz": "✅ Tasdiqlash va Yuborish",
        "ru": "✅ Подтвердить и отправить",
        "en": "✅ Confirm and send",
    },
    "restart_edit": {
        "uz": "✏️ Tahrirlash (Boshidan)",
        "ru": "✏️ Изменить с начала",
        "en": "✏️ Edit from start",
    },
    "choose_language_full": {
        "uz": "Iltimos, bot tilini tanlang:\n\nПожалуйста, выберите язык:\n\nPlease choose a language:",
        "ru": "Iltimos, bot tilini tanlang:\n\nПожалуйста, выберите язык:\n\nPlease choose a language:",
        "en": "Iltimos, bot tilini tanlang:\n\nПожалуйста, выберите язык:\n\nPlease choose a language:",
    },
    "teacher_pending": {
        "uz": "⏳ Sizning ustozlik arizangiz ma'muriyat tomonidan ko'rib chiqilmoqda. Iltimos kuting.",
        "ru": "⏳ Ваша заявка преподавателя рассматривается администрацией. Пожалуйста, подождите.",
        "en": "⏳ Your teacher application is being reviewed by the administration. Please wait.",
    },
    "teacher_rejected": {
        "uz": "❌ Sizning oldingi ustozlik arizangiz ma'muriyat tomonidan rad etilgan.\n\nSiz xatolarni to'g'rilab qaytadan ariza topshirishingiz yoki tizimdan oddiy o'quvchi sifatida foydalanishingiz mumkin:",
        "ru": "❌ Ваша предыдущая заявка преподавателя была отклонена администрацией.\n\nВы можете исправить данные и подать заявку снова или пользоваться системой как студент:",
        "en": "❌ Your previous teacher application was rejected by the administration.\n\nYou can correct your information and apply again, or use the system as a student:",
    },
    "teacher_reg_start": {
        "uz": "👨‍🏫 <b>Ustozlikka nomzod anketasi</b>\n\nIltimos, pasportdagi to'liq ism-sharifingizni (F.I.O) kiriting:",
        "ru": "👨‍🏫 <b>Анкета кандидата в преподаватели</b>\n\nПожалуйста, введите полное имя как в паспорте:",
        "en": "👨‍🏫 <b>Teacher application form</b>\n\nPlease enter your full name as in your passport:",
    },
    "student_reg_start": {
        "uz": "👨‍🎓 <b>O'quvchi anketasi</b>\n\nIltimos, pasportdagi to'liq ism-sharifingizni (F.I.O) kiriting:\n<i>(Masalan: Eshmatov Toshmat G'ishmatovich)</i>",
        "ru": "👨‍🎓 <b>Анкета студента</b>\n\nПожалуйста, введите полное имя как в паспорте:\n<i>(Например: Иванов Иван Иванович)</i>",
        "en": "👨‍🎓 <b>Student registration form</b>\n\nPlease enter your full name as in your passport:\n<i>(Example: John Michael Smith)</i>",
    },
    "ask_phone_student": {
        "uz": "Endi telefon raqamingizni yuboring yoki yozib qoldiring:",
        "ru": "Теперь отправьте или введите ваш номер телефона:",
        "en": "Now send or type your phone number:",
    },
    "ask_phone_teacher": {
        "uz": "Endi telefon raqamingizni yuboring:",
        "ru": "Теперь отправьте ваш номер телефона:",
        "en": "Now send your phone number:",
    },
    "phone_ok": {
        "uz": "Raqam qabul qilindi ✅",
        "ru": "Номер принят ✅",
        "en": "Phone number received ✅",
    },
    "choose_region": {
        "uz": "Iltimos, yashash viloyatingizni tanlang:",
        "ru": "Пожалуйста, выберите ваш регион проживания:",
        "en": "Please choose your region:",
    },
    "region_selected": {
        "uz": "📍 Viloyat: <b>{region}</b>\nEndi tumaningizni tanlang:",
        "ru": "📍 Регион: <b>{region}</b>\nТеперь выберите район:",
        "en": "📍 Region: <b>{region}</b>\nNow choose your district:",
    },
    "back_regions": {
        "uz": "🔙 Viloyatlarga qaytish",
        "ru": "🔙 Назад к регионам",
        "en": "🔙 Back to regions",
    },
    "ask_age_teacher": {
        "uz": "Hudud qabul qilindi: {region} ✅\n\nYoshingizni faqat raqam bilan kiriting (Masalan: 28):",
        "ru": "Регион принят: {region} ✅\n\nВведите возраст только цифрами (например: 28):",
        "en": "Region saved: {region} ✅\n\nEnter your age using numbers only (example: 28):",
    },
    "ask_age_student": {
        "uz": "Hudud: <b>{region}</b> ✅\n\nYoshingizni faqat raqam bilan kiriting (Masalan: 24):",
        "ru": "Регион: <b>{region}</b> ✅\n\nВведите возраст только цифрами (например: 24):",
        "en": "Region: <b>{region}</b> ✅\n\nEnter your age using numbers only (example: 24):",
    },
    "age_digits": {
        "uz": "Iltimos, yoshingizni faqat raqamlar bilan yozing!",
        "ru": "Пожалуйста, введите возраст только цифрами!",
        "en": "Please enter your age using numbers only!",
    },
    "choose_teach_lang": {
        "uz": "Qaysi tilni o'qitasiz?",
        "ru": "Какой язык вы преподаёте?",
        "en": "Which language do you teach?",
    },
    "experience_request": {
        "uz": "📝 <b>Tajribangiz (CV / Resume)</b>\n\nO'zingiz haqingizda matn yozishingiz yoki <b>PDF, DOCX, Rasm</b> formatidagi CV faylingizni botga yuklashingiz mumkin:",
        "ru": "📝 <b>Ваш опыт (CV / резюме)</b>\n\nВы можете написать о себе текстом или загрузить CV в формате <b>PDF, DOCX, фото</b>:",
        "en": "📝 <b>Your experience (CV / Resume)</b>\n\nYou can write about yourself or upload your CV as <b>PDF, DOCX, or image</b>:",
    },
    "send_text_photo_doc": {
        "uz": "Iltimos, matn, rasm yoki hujjat yuboring.",
        "ru": "Пожалуйста, отправьте текст, фото или документ.",
        "en": "Please send text, a photo, or a document.",
    },
    "teacher_summary_title": {
        "uz": "📝 <b>Ma'lumotlaringizni tekshiring:</b>",
        "ru": "📝 <b>Проверьте ваши данные:</b>",
        "en": "📝 <b>Please check your information:</b>",
    },
    "student_summary_title": {
        "uz": "📝 <b>Ma'lumotlaringizni tekshiring:</b>",
        "ru": "📝 <b>Проверьте ваши данные:</b>",
        "en": "📝 <b>Please check your information:</b>",
    },
    "summary_warning": {
        "uz": "⚠️ <b>Barchasi to'g'riligini tekshirib, tasdiqlang yoki boshidan tahrirlang.</b>",
        "ru": "⚠️ <b>Проверьте правильность данных, подтвердите или измените с начала.</b>",
        "en": "⚠️ <b>Please check everything, then confirm or edit from the start.</b>",
    },
    "choose_button": {
        "uz": "Iltimos, pastdagi tugmalardan birini tanlang.",
        "ru": "Пожалуйста, выберите одну из кнопок ниже.",
        "en": "Please choose one of the buttons below.",
    },
    "teacher_application_sent": {
        "uz": "✅ Arizangiz muvaffaqiyatli qabul qilindi va ma'muriyatga yuborildi!\n\nTez orada bot orqali xabar beramiz.",
        "ru": "✅ Ваша заявка успешно принята и отправлена администрации!\n\nМы скоро сообщим вам через бота.",
        "en": "✅ Your application has been received and sent to the administration!\n\nWe will notify you through the bot soon.",
    },
    "student_registered": {
        "uz": "✅ <b>{fio}</b>, siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\nQuyidagi menyu orqali o'zingizga kerakli kursni tanlashingiz mumkin 👇",
        "ru": "✅ <b>{fio}</b>, вы успешно зарегистрировались!\n\nЧерез меню ниже вы можете выбрать нужный курс 👇",
        "en": "✅ <b>{fio}</b>, you have successfully registered!\n\nYou can choose the course you need from the menu below 👇",
    },
    "profile_not_found": {
        "uz": "Sizning profilingiz topilmadi. /start orqali ro'yxatdan o'ting.",
        "ru": "Ваш профиль не найден. Зарегистрируйтесь через /start.",
        "en": "Your profile was not found. Please register using /start.",
    },
    "profile_title": {
        "uz": "👤 <b>Shaxsiy Profilingiz</b>",
        "ru": "👤 <b>Ваш профиль</b>",
        "en": "👤 <b>Your Profile</b>",
    },
}


def lt(key: str, lang: str = "uz", **kwargs) -> str:
    item = LOCAL_TEXTS.get(key, {})
    text = item.get(lang) or item.get("uz") or key
    return text.format(**kwargs)


def all_local_texts(key: str):
    item = LOCAL_TEXTS.get(key, {})
    return list(item.values())


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


# ==========================================
# KEYBOARDS
# ==========================================

def mini_app_button_row(lang: str = "uz"):
    """MINI_APP_URL bo'lsa, Mini App tugmasini qaytaradi"""
    mini_app_url = os.getenv("MINI_APP_URL")

    if not mini_app_url:
        return None

    return [
        types.KeyboardButton(
            text=t("mini_app", lang),
            web_app=WebAppInfo(url=mini_app_url)
        )
    ]


def back_kb(lang: str = "uz"):
    """Umumiy Orqaga tugmasi"""
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=lt("back", lang))]],
        resize_keyboard=True
    )


def student_main_menu(lang: str = "uz"):
    """O'quvchi asosiy menyusi"""
    keyboard = []

    mini_row = mini_app_button_row(lang)
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text=t("my_lessons", lang))],
        [types.KeyboardButton(text=t("courses", lang)), types.KeyboardButton(text=t("profile", lang))]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def teacher_main_menu(lang: str = "uz"):
    """Ustoz asosiy menyusi"""
    keyboard = []

    mini_row = mini_app_button_row(lang)
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text=lt("teacher_my_groups", lang))],
        [types.KeyboardButton(text=lt("teacher_results", lang)), types.KeyboardButton(text=lt("teacher_kick", lang))],
        [types.KeyboardButton(text=t("profile", lang))]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def admin_main_menu(lang: str = "uz"):
    """
    Oddiy admin menyusi.
    Admin platformani boshqaradi, lekin adminlarni qo'shish/olib tashlash va admin actionlarni ko'rish superadmin uchun.
    """
    keyboard = []

    mini_row = mini_app_button_row(lang)
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text=t("teachers_view", lang))],
        [
            types.KeyboardButton(text=t("create_group", lang)),
            types.KeyboardButton(text=t("groups_list", lang)),
        ],
        [types.KeyboardButton(text=t("all_results", lang))],
        [types.KeyboardButton(text=t("statistics", lang))]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def accountant_main_menu(lang: str = "uz"):
    """Accountant menyusi: faqat to'lovlar bilan ishlaydi"""
    keyboard = []

    mini_row = mini_app_button_row(lang)
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text=t("accounting_panel", lang))],
        [types.KeyboardButton(text=t("profile", lang))]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )

def superadmin_main_menu(lang: str = "uz"):
    """
    Superadmin menyusi.
    Superadmin admin qiladigan hamma narsani qiladi + adminlarni boshqaradi + admin harakatlarini ko'radi.
    """
    keyboard = []

    mini_row = mini_app_button_row(lang)
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text=t("admin_manage", lang))],
        [types.KeyboardButton(text=t("teachers_view", lang))],
        [
            types.KeyboardButton(text=t("create_group", lang)),
            types.KeyboardButton(text=t("groups_list", lang)),
        ],
        [types.KeyboardButton(text=t("all_results", lang))],
        [types.KeyboardButton(text=t("admin_actions", lang))],
        [types.KeyboardButton(text=t("statistics", lang))]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def first_start_menu(lang: str = "uz"):
    """Yangi foydalanuvchi uchun boshlang'ich menyu"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=t("student_register", lang))],
            [types.KeyboardButton(text=t("teacher_register", lang))]
        ],
        resize_keyboard=True
    )


def language_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O‘zbekcha", callback_data=LangSelectCB(lang="uz"))
    builder.button(text="🇷🇺 Русский", callback_data=LangSelectCB(lang="ru"))
    builder.button(text="🇬🇧 English", callback_data=LangSelectCB(lang="en"))
    builder.adjust(1)
    return builder.as_markup()


# ==========================================
# MAIN MENU LOGIC
# ==========================================

async def show_role_menu(message: types.Message, user_id: int, full_name: str, state: FSMContext):
    await add_user(user_id, full_name)
    await state.clear()

    lang = await get_user_interface_lang(user_id)

    if not lang:
        await message.answer(
            lt("choose_language_full", "uz"),
            reply_markup=language_keyboard()
        )
        return

    role = await get_user_role(user_id)

    if role == "teacher":
        await message.answer(
            t("teacher_welcome", lang),
            reply_markup=teacher_main_menu(lang)
        )
        return

    elif role == "pending_teacher":
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text=t("profile", lang))]],
            resize_keyboard=True
        )
        await message.answer(
            lt("teacher_pending", lang),
            reply_markup=keyboard
        )
        return

    elif role == "rejected_teacher":
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text=t("teacher_register", lang))],
                [types.KeyboardButton(text=t("student_register", lang))]
            ],
            resize_keyboard=True
        )
        await message.answer(
            lt("teacher_rejected", lang),
            reply_markup=keyboard
        )
        return

    elif role == "student":
        await message.answer(
            t("student_home", lang),
            reply_markup=student_main_menu(lang)
        )
        return

    elif role == "superadmin":
        await message.answer(
            t("superadmin_welcome", lang),
            reply_markup=superadmin_main_menu(lang)
        )
        return

    elif role == "accountant":
        await message.answer(
            t("accountant_welcome", lang),
            reply_markup=accountant_main_menu(lang)
        )
        return

    elif role == "admin":
        await message.answer(
            t("admin_welcome", lang),
            reply_markup=admin_main_menu(lang)
        )
        return

    await message.answer(
        t("welcome", lang),
        reply_markup=first_start_menu(lang)
    )


# ==========================================
# 1. START VA TIL TANLASH
# ==========================================

@user_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await show_role_menu(
        message=message,
        user_id=message.from_user.id,
        full_name=message.from_user.full_name,
        state=state
    )


@user_router.callback_query(LangSelectCB.filter())
async def set_interface_language(callback: types.CallbackQuery, callback_data: LangSelectCB, state: FSMContext):
    if callback_data.lang not in ["uz", "ru", "en"]:
        await callback.answer("Language not supported.", show_alert=True)
        return

    await add_user(callback.from_user.id, callback.from_user.full_name)
    await set_user_interface_lang(callback.from_user.id, callback_data.lang)

    await callback.message.delete()
    await callback.message.answer(t("language_saved", callback_data.lang))

    await show_role_menu(
        message=callback.message,
        user_id=callback.from_user.id,
        full_name=callback.from_user.full_name,
        state=state
    )


# ==========================================
# 2. USTOZ BO'LIB ISHLASH JARAYONI
# ==========================================

@user_router.message(F.text.in_(all_texts("teacher_register")))
async def start_teacher_reg(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await message.answer(
        lt("teacher_reg_start", lang),
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TeacherRegistration.fio)


@user_router.message(TeacherRegistration.fio)
async def t_process_fio(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await state.update_data(fio=message.text)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=lt("send_phone", lang), request_contact=True)],
            [types.KeyboardButton(text=lt("back", lang))]
        ],
        resize_keyboard=True
    )

    await message.answer(lt("ask_phone_teacher", lang), reply_markup=keyboard)
    await state.set_state(TeacherRegistration.phone)


@user_router.message(TeacherRegistration.phone)
async def t_process_phone(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if message.text in all_local_texts("back"):
        await start_teacher_reg(message, state)
        return

    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone_number)

    await message.answer(lt("phone_ok", lang), reply_markup=types.ReplyKeyboardRemove())
    await show_regions(message, lang)
    await state.set_state(TeacherRegistration.region)


@user_router.message(TeacherRegistration.age)
async def t_process_age(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if not message.text.isdigit():
        await message.answer(lt("age_digits", lang))
        return

    await state.update_data(age=int(message.text))

    from utils.data import LANGUAGES

    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=f"tlang_{name}")

    builder.adjust(2)

    await message.answer(lt("choose_teach_lang", lang), reply_markup=builder.as_markup())
    await state.set_state(TeacherRegistration.lang)


@user_router.callback_query(TeacherRegistration.lang, F.data.startswith("tlang_"))
async def t_process_lang(callback: types.CallbackQuery, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    lang_name = callback.data.split("_", 1)[1]
    await state.update_data(lang=lang_name)

    await callback.message.delete()

    await callback.message.answer(
        lt("experience_request", lang),
        parse_mode="HTML"
    )
    await state.set_state(TeacherRegistration.experience)


@user_router.message(TeacherRegistration.experience, F.text | F.photo | F.document)
async def t_process_exp(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    cv_type = None
    cv_content = None

    if message.text:
        cv_type = "text"
        cv_content = message.text
    elif message.photo:
        cv_type = "photo"
        cv_content = message.photo[-1].file_id
    elif message.document:
        cv_type = "document"
        cv_content = message.document.file_id

    if not cv_type:
        await message.answer(lt("send_text_photo_doc", lang))
        return

    await state.update_data(cv_type=cv_type, cv_content=cv_content)
    data = await state.get_data()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=lt("confirm_send", lang))],
            [types.KeyboardButton(text=lt("restart_edit", lang))]
        ],
        resize_keyboard=True
    )

    summary = (
        f"{lt('teacher_summary_title', lang)}\n\n"
        f"👤 F.I.O: {data['fio']}\n"
        f"📞 Tel: {data['phone']}\n"
        f"📍 Hudud: {data['region']}\n"
        f"📅 Yosh: {data['age']}\n"
        f"📚 Fan: {data['lang']}\n\n"
        f"{lt('summary_warning', lang)}"
    )

    if cv_type == "text":
        summary = summary.replace(
            f"\n\n{lt('summary_warning', lang)}",
            f"\n📝 Tajriba:\n<i>{cv_content}</i>\n\n{lt('summary_warning', lang)}"
        )
        await message.answer(summary, parse_mode="HTML", reply_markup=keyboard)
    elif cv_type == "photo":
        await message.answer_photo(photo=cv_content, caption=summary, parse_mode="HTML", reply_markup=keyboard)
    elif cv_type == "document":
        await message.answer_document(document=cv_content, caption=summary, parse_mode="HTML", reply_markup=keyboard)

    await state.set_state(TeacherRegistration.confirm)


@user_router.message(TeacherRegistration.confirm)
async def t_confirm_registration(message: types.Message, state: FSMContext, bot: Bot):
    lang = await user_lang(message.from_user.id)

    if message.text in all_local_texts("restart_edit"):
        await start_teacher_reg(message, state)
        return

    if message.text not in all_local_texts("confirm_send"):
        await message.answer(lt("choose_button", lang))
        return

    data = await state.get_data()

    await save_teacher_application(
        message.from_user.id,
        data["fio"],
        data["phone"],
        data["region"],
        data["age"],
        data["lang"],
        data["cv_content"]
    )

    admin_ids = await get_management_staff_ids()

    if admin_ids:
        from utils.states import AdminTeacherApproveCB, AdminTeacherRejectCB

        admin_text = (
            f"👨‍🏫 <b>Yangi USTOZ arizasi!</b>\n\n"
            f"👤 F.I.O: {data['fio']}\n"
            f"📞 Tel: {data['phone']}\n"
            f"📍 Hudud: {data['region']}\n"
            f"📅 Yosh: {data['age']}\n"
            f"📚 Fan: {data['lang']}\n"
        )

        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ Ishga qabul qilish",
            callback_data=AdminTeacherApproveCB(teacher_id=message.from_user.id)
        )
        builder.button(
            text="❌ Rad etish",
            callback_data=AdminTeacherRejectCB(teacher_id=message.from_user.id)
        )
        builder.adjust(2)

        for admin_id in admin_ids:
            try:
                if data["cv_type"] == "text":
                    text_with_cv = admin_text + f"\n📝 Tajriba:\n<i>{data['cv_content']}</i>"
                    await bot.send_message(
                        chat_id=admin_id,
                        text=text_with_cv,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )

                elif data["cv_type"] == "photo":
                    await bot.send_photo(
                        chat_id=admin_id,
                        photo=data["cv_content"],
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )

                elif data["cv_type"] == "document":
                    await bot.send_document(
                        chat_id=admin_id,
                        document=data["cv_content"],
                        caption=admin_text,
                        parse_mode="HTML",
                        reply_markup=builder.as_markup()
                    )
            except Exception:
                pass

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text=t("profile", lang))]],
        resize_keyboard=True
    )

    await message.answer(
        lt("teacher_application_sent", lang),
        reply_markup=keyboard
    )
    await state.clear()


# ==========================================
# 3. O'QUVCHI BO'LIB O'QISH JARAYONI
# ==========================================

@user_router.message(F.text.in_(all_texts("student_register")))
async def start_student_reg(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await message.answer(
        lt("student_reg_start", lang),
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Registration.fio)


@user_router.message(Registration.fio)
async def process_fio(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    await state.update_data(fio=message.text)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=lt("send_phone", lang), request_contact=True)],
            [types.KeyboardButton(text=lt("back", lang))]
        ],
        resize_keyboard=True
    )

    await message.answer(lt("ask_phone_student", lang), reply_markup=keyboard)
    await state.set_state(Registration.phone)


@user_router.message(Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if message.text in all_local_texts("back"):
        await cmd_start(message, state)
        return

    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone_number)

    await message.answer(lt("phone_ok", lang), reply_markup=types.ReplyKeyboardRemove())

    await show_regions(message, lang)
    await state.set_state(Registration.region)


# ==========================================
# 4. UMUMIY HUDUD TANLASH
# ==========================================

async def show_regions(message_or_callback, lang: str = "uz"):
    builder = InlineKeyboardBuilder()

    for region in UZB_REGIONS.keys():
        builder.button(text=region, callback_data=RegionCB(name=region))

    builder.button(text=lt("back", lang), callback_data="back_to_phone")
    builder.adjust(2)

    text = lt("choose_region", lang)

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=builder.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup())


@user_router.callback_query(Registration.region, RegionCB.filter())
@user_router.callback_query(TeacherRegistration.region, RegionCB.filter())
async def process_region_selection(callback: types.CallbackQuery, callback_data: RegionCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    selected_region = callback_data.name
    districts = UZB_REGIONS.get(selected_region, [])

    builder = InlineKeyboardBuilder()

    for district in districts:
        builder.button(
            text=district,
            callback_data=DistrictCB(reg_name=selected_region, name=district)
        )

    builder.button(text=lt("back_regions", lang), callback_data="back_to_regions")
    builder.adjust(2)

    await callback.message.edit_text(
        lt("region_selected", lang, region=selected_region),
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@user_router.callback_query(Registration.region, DistrictCB.filter())
@user_router.callback_query(TeacherRegistration.region, DistrictCB.filter())
async def process_district_selection(callback: types.CallbackQuery, callback_data: DistrictCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    full_region = f"{callback_data.reg_name}, {callback_data.name}"
    await state.update_data(region=full_region)
    await callback.message.delete()

    current_state = await state.get_state()

    if current_state == TeacherRegistration.region.state:
        await callback.message.answer(
            lt("ask_age_teacher", lang, region=full_region)
        )
        await state.set_state(TeacherRegistration.age)
    else:
        await callback.message.answer(
            lt("ask_age_student", lang, region=full_region),
            parse_mode="HTML",
            reply_markup=back_kb(lang)
        )
        await state.set_state(Registration.age)


@user_router.callback_query(F.data == "back_to_phone")
async def inline_back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    await callback.message.delete()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=lt("send_phone", lang), request_contact=True)],
            [types.KeyboardButton(text=lt("back", lang))]
        ],
        resize_keyboard=True
    )

    await callback.message.answer(lt("ask_phone_student", lang), reply_markup=keyboard)

    current_state = await state.get_state()

    if current_state == TeacherRegistration.region.state:
        await state.set_state(TeacherRegistration.phone)
    else:
        await state.set_state(Registration.phone)


@user_router.callback_query(F.data == "back_to_regions")
async def inline_back_to_regions(callback: types.CallbackQuery, state: FSMContext):
    lang = await user_lang(callback.from_user.id)
    await show_regions(callback, lang)


# ==========================================
# 5. O'QUVCHI YOSH KELGANDA -> TASDIQLASH
# ==========================================

@user_router.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if message.text in all_local_texts("back"):
        await message.answer(lt("choose_region", lang), reply_markup=types.ReplyKeyboardRemove())
        await show_regions(message, lang)
        await state.set_state(Registration.region)
        return

    if not message.text.isdigit():
        await message.answer(lt("age_digits", lang))
        return

    await state.update_data(age=int(message.text))
    data = await state.get_data()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text=lt("confirm", lang))],
            [types.KeyboardButton(text=lt("restart_edit", lang))]
        ],
        resize_keyboard=True
    )

    summary = (
        f"{lt('student_summary_title', lang)}\n\n"
        f"👤 F.I.O: {data['fio']}\n"
        f"📞 Tel: {data['phone']}\n"
        f"📍 Hudud: {data['region']}\n"
        f"📅 Yosh: {data['age']}\n\n"
        f"{lt('summary_warning', lang)}"
    )

    await message.answer(summary, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(Registration.confirm)


# ==========================================
# 6. O'QUVCHI TASDIQLAGANDA -> BAZAGA SAQLASH
# ==========================================

@user_router.message(Registration.confirm)
async def s_confirm_registration(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    if message.text in all_local_texts("restart_edit"):
        await start_student_reg(message, state)
        return

    if message.text not in all_local_texts("confirm"):
        await message.answer(lt("choose_button", lang))
        return

    data = await state.get_data()

    await update_user_profile(
        message.from_user.id,
        data["fio"],
        data["phone"],
        data["region"],
        data["age"]
    )

    await state.clear()

    await message.answer(
        lt("student_registered", lang, fio=data["fio"]),
        parse_mode="HTML",
        reply_markup=student_main_menu(lang)
    )


# ==========================================
# 7. SHAXSIY PROFIL
# ==========================================

@user_router.message(F.text.in_(all_texts("profile")))
async def show_profile(message: types.Message):
    lang = await user_lang(message.from_user.id)

    profile = await get_full_profile(message.from_user.id)

    if not profile:
        await message.answer(lt("profile_not_found", lang))
        return

    role = profile["role"]

    text = (
        f"{lt('profile_title', lang)}\n\n"
        f"<b>F.I.O:</b> {profile['full_name']}\n"
        f"<b>Telefon:</b> {profile['phone']}\n"
        f"<b>Hudud:</b> {profile['region']}\n"
        f"<b>Yosh:</b> {profile['age']}\n"
    )

    if role == "teacher":
        status_text = {
            "uz": "✅ Tasdiqlangan Ustoz",
            "ru": "✅ Подтверждённый преподаватель",
            "en": "✅ Approved Teacher",
        }.get(lang, "✅ Tasdiqlangan Ustoz")
        text += f"<b>Fan:</b> {profile['teach_lang']}\n"

    elif role == "pending_teacher":
        status_text = {
            "uz": "⏳ Ko'rib chiqilmoqda (Ustozlik arizasi)",
            "ru": "⏳ На рассмотрении (заявка преподавателя)",
            "en": "⏳ Under review (teacher application)",
        }.get(lang, "⏳ Ko'rib chiqilmoqda")

    elif role == "rejected_teacher":
        status_text = {
            "uz": "❌ Rad etilgan (Ma'muriyat tasdiqlamadi)",
            "ru": "❌ Отклонено администрацией",
            "en": "❌ Rejected by administration",
        }.get(lang, "❌ Rad etilgan")

    elif role == "admin":
        status_text = "👨‍💻 Admin"

    elif role == "accountant":
        status_text = {
            "uz": "💰 Accountant",
            "ru": "💰 Бухгалтерия",
            "en": "💰 Accountant",
        }.get(lang, "💰 Accountant")

    elif role == "superadmin":
        status_text = "👑 Superadmin"

    else:
        from database.db import get_student_status

        student_status = await get_student_status(message.from_user.id)

        if student_status == "pending":
            status_text = {
                "uz": "⏳ Ko'rib chiqilmoqda (To'lov tasdig'i kutilmoqda)",
                "ru": "⏳ На рассмотрении (ожидается подтверждение оплаты)",
                "en": "⏳ Under review (payment confirmation pending)",
            }.get(lang, "⏳ Pending")
        elif student_status == "approved":
            status_text = {
                "uz": "✅ Tasdiqlangan O'quvchi (Guruhga qo'shilgan)",
                "ru": "✅ Подтверждённый студент (добавлен в группу)",
                "en": "✅ Approved Student (added to group)",
            }.get(lang, "✅ Approved")
        elif student_status == "rejected":
            status_text = {
                "uz": "❌ Rad etilgan (To'lov cheki tasdiqlanmadi)",
                "ru": "❌ Отклонено (чек оплаты не подтверждён)",
                "en": "❌ Rejected (payment receipt not approved)",
            }.get(lang, "❌ Rejected")
        else:
            status_text = {
                "uz": "🆕 Yangi O'quvchi (Hali kurs tanlanmagan)",
                "ru": "🆕 Новый студент (курс ещё не выбран)",
                "en": "🆕 New Student (no course selected yet)",
            }.get(lang, "🆕 New Student")

    text += f"\n📊 <b>Status:</b> {status_text}"

    await message.answer(text, parse_mode="HTML")