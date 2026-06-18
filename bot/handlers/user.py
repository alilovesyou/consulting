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
)
from utils.states import Registration, RegionCB, DistrictCB, TeacherRegistration
from utils.data import UZB_REGIONS

user_router = Router()


# ==========================================
# KEYBOARDS
# ==========================================

def mini_app_button_row():
    """MINI_APP_URL bo'lsa, Mini App tugmasini qaytaradi"""
    mini_app_url = os.getenv("MINI_APP_URL")

    if not mini_app_url:
        return None

    return [
        types.KeyboardButton(
            text="🚀 Mini App ochish",
            web_app=WebAppInfo(url=mini_app_url)
        )
    ]


def back_kb():
    """Umumiy Orqaga tugmasi"""
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 Orqaga")]],
        resize_keyboard=True
    )


def student_main_menu():
    """O'quvchi asosiy menyusi"""
    keyboard = []

    mini_row = mini_app_button_row()
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text="📖 Mening darslarim")],
        [types.KeyboardButton(text="📚 Kurslar"), types.KeyboardButton(text="👤 Profil")]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def teacher_main_menu():
    """Ustoz asosiy menyusi"""
    keyboard = []

    mini_row = mini_app_button_row()
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text="📚 Mening guruhlarim")],
        [types.KeyboardButton(text="📝 Natija kiritish"), types.KeyboardButton(text="❌ Chetlatish so'rovi")],
        [types.KeyboardButton(text="👤 Profil")]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def admin_main_menu():
    """Oddiy admin menyusi: faqat to'lovlar va statistika uchun"""
    keyboard = []

    mini_row = mini_app_button_row()
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text="📊 Statistika")]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def superadmin_main_menu():
    """Superadmin menyusi"""
    keyboard = []

    mini_row = mini_app_button_row()
    if mini_row:
        keyboard.append(mini_row)

    keyboard += [
        [types.KeyboardButton(text="👨‍💻 Adminlarni boshqarish")],
        [
            types.KeyboardButton(text="👨‍🏫 Ustozlarni ko‘rish"),
            types.KeyboardButton(text="👨‍🎓 O‘quvchilarni ko‘rish"),
        ],
        [
            types.KeyboardButton(text="📚 Guruhlar ro'yxati"),
            types.KeyboardButton(text="📊 Barcha natijalar"),
        ],
        [types.KeyboardButton(text="📌 Admin harakatlari")],
        [types.KeyboardButton(text="📊 Statistika")]
    ]

    return types.ReplyKeyboardMarkup(
        keyboard=keyboard,
        resize_keyboard=True
    )


def first_start_menu():
    """Yangi foydalanuvchi uchun boshlang'ich menyu"""
    return types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="👨‍🎓 O'quvchi bo'lib o'qish")],
            [types.KeyboardButton(text="👨‍🏫 Ustoz bo'lib ishlash")]
        ],
        resize_keyboard=True
    )


# ==========================================
# 1. START VA ROLLLARGA AJRATISH
# ==========================================

@user_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    await add_user(message.from_user.id, message.from_user.full_name)
    await state.clear()

    role = await get_user_role(message.from_user.id)

    if role == "teacher":
        await message.answer(
            "👨‍🏫 Assalomu alaykum, Ustoz! Ish paneliga xush kelibsiz.",
            reply_markup=teacher_main_menu()
        )
        return

    elif role == "pending_teacher":
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[[types.KeyboardButton(text="👤 Profil")]],
            resize_keyboard=True
        )
        await message.answer(
            "⏳ Sizning ustozlik arizangiz ma'muriyat tomonidan ko'rib chiqilmoqda. Iltimos kuting.",
            reply_markup=keyboard
        )
        return

    elif role == "rejected_teacher":
        keyboard = types.ReplyKeyboardMarkup(
            keyboard=[
                [types.KeyboardButton(text="👨‍🏫 Ustoz bo'lib ishlash")],
                [types.KeyboardButton(text="👨‍🎓 O'quvchi bo'lib o'qish")]
            ],
            resize_keyboard=True
        )
        await message.answer(
            "❌ Sizning oldingi ustozlik arizangiz ma'muriyat tomonidan rad etilgan.\n\n"
            "Siz xatolarni to'g'rilab qaytadan ariza topshirishingiz yoki tizimdan oddiy o'quvchi sifatida foydalanishingiz mumkin:",
            reply_markup=keyboard
        )
        return

    elif role == "student":
        await message.answer(
            "🏠 Asosiy menyuga qaytdingiz.",
            reply_markup=student_main_menu()
        )
        return

    elif role == "superadmin":
        await message.answer(
            "👑 Assalomu alaykum, Superadmin! Boshqaruv paneliga xush kelibsiz.",
            reply_markup=superadmin_main_menu()
        )
        return

    elif role == "admin":
        await message.answer(
            "👨‍💻 Assalomu alaykum, Admin! To‘lovlarni tekshirish paneliga xush kelibsiz.",
            reply_markup=admin_main_menu()
        )
        return

    await message.answer(
        "Assalomu alaykum! Visa & Language Consulting tizimiga xush kelibsiz.\n\n"
        "Tizimdan qanday maqsadda foydalanmoqchisiz?",
        reply_markup=first_start_menu()
    )


# ==========================================
# 2. USTOZ BO'LIB ISHLASH JARAYONI
# ==========================================

@user_router.message(F.text == "👨‍🏫 Ustoz bo'lib ishlash")
async def start_teacher_reg(message: types.Message, state: FSMContext):
    await message.answer(
        "👨‍🏫 <b>Ustozlikka nomzod anketasi</b>\n\n"
        "Iltimos, pasportdagi to'liq ism-sharifingizni (F.I.O) kiriting:",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(TeacherRegistration.fio)


@user_router.message(TeacherRegistration.fio)
async def t_process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)],
            [types.KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

    await message.answer("Endi telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(TeacherRegistration.phone)


@user_router.message(TeacherRegistration.phone)
async def t_process_phone(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await start_teacher_reg(message, state)
        return

    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone_number)

    await message.answer("Raqam qabul qilindi ✅", reply_markup=types.ReplyKeyboardRemove())
    await show_regions(message)
    await state.set_state(TeacherRegistration.region)


@user_router.message(TeacherRegistration.age)
async def t_process_age(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, yoshingizni faqat raqamlar bilan yozing!")
        return

    await state.update_data(age=int(message.text))

    from utils.data import LANGUAGES

    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=f"tlang_{name}")

    builder.adjust(2)

    await message.answer("Qaysi tilni o'qitasiz?", reply_markup=builder.as_markup())
    await state.set_state(TeacherRegistration.lang)


@user_router.callback_query(TeacherRegistration.lang, F.data.startswith("tlang_"))
async def t_process_lang(callback: types.CallbackQuery, state: FSMContext):
    lang_name = callback.data.split("_", 1)[1]
    await state.update_data(lang=lang_name)

    await callback.message.delete()

    await callback.message.answer(
        "📝 <b>Tajribangiz (CV / Resume)</b>\n\n"
        "O'zingiz haqingizda matn yozishingiz yoki <b>PDF, DOCX, Rasm</b> formatidagi CV faylingizni botga yuklashingiz mumkin:",
        parse_mode="HTML"
    )
    await state.set_state(TeacherRegistration.experience)


@user_router.message(TeacherRegistration.experience, F.text | F.photo | F.document)
async def t_process_exp(message: types.Message, state: FSMContext):
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
        await message.answer("Iltimos, matn, rasm yoki hujjat yuboring.")
        return

    await state.update_data(cv_type=cv_type, cv_content=cv_content)
    data = await state.get_data()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ Tasdiqlash va Yuborish")],
            [types.KeyboardButton(text="✏️ Tahrirlash (Boshidan)")]
        ],
        resize_keyboard=True
    )

    summary = (
        f"📝 <b>Ma'lumotlaringizni tekshiring:</b>\n\n"
        f"👤 F.I.O: {data['fio']}\n"
        f"📞 Tel: {data['phone']}\n"
        f"📍 Hudud: {data['region']}\n"
        f"📅 Yosh: {data['age']}\n"
        f"📚 Fan: {data['lang']}\n\n"
        f"⚠️ <b>Barchasi to'g'riligini tekshirib, tasdiqlang yoki boshidan tahrirlang.</b>"
    )

    if cv_type == "text":
        summary = summary.replace("\n\n⚠️", f"\n📝 Tajriba:\n<i>{cv_content}</i>\n\n⚠️")
        await message.answer(summary, parse_mode="HTML", reply_markup=keyboard)
    elif cv_type == "photo":
        await message.answer_photo(photo=cv_content, caption=summary, parse_mode="HTML", reply_markup=keyboard)
    elif cv_type == "document":
        await message.answer_document(document=cv_content, caption=summary, parse_mode="HTML", reply_markup=keyboard)

    await state.set_state(TeacherRegistration.confirm)


@user_router.message(TeacherRegistration.confirm)
async def t_confirm_registration(message: types.Message, state: FSMContext, bot: Bot):
    if message.text == "✏️ Tahrirlash (Boshidan)":
        await start_teacher_reg(message, state)
        return

    if message.text != "✅ Tasdiqlash va Yuborish":
        await message.answer("Iltimos, pastdagi tugmalardan birini tanlang.")
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

    admin_id = os.getenv("ADMIN_ID")

    if admin_id:
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

        if data["cv_type"] == "text":
            admin_text += f"\n📝 Tajriba:\n<i>{data['cv_content']}</i>"
            await bot.send_message(
                chat_id=int(admin_id),
                text=admin_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        elif data["cv_type"] == "photo":
            await bot.send_photo(
                chat_id=int(admin_id),
                photo=data["cv_content"],
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )
        elif data["cv_type"] == "document":
            await bot.send_document(
                chat_id=int(admin_id),
                document=data["cv_content"],
                caption=admin_text,
                parse_mode="HTML",
                reply_markup=builder.as_markup()
            )

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="👤 Profil")]],
        resize_keyboard=True
    )

    await message.answer(
        "✅ Arizangiz muvaffaqiyatli qabul qilindi va ma'muriyatga yuborildi!\n\n"
        "Tez orada bot orqali xabar beramiz.",
        reply_markup=keyboard
    )
    await state.clear()


# ==========================================
# 3. O'QUVCHI BO'LIB O'QISH JARAYONI
# ==========================================

@user_router.message(F.text == "👨‍🎓 O'quvchi bo'lib o'qish")
async def start_student_reg(message: types.Message, state: FSMContext):
    await message.answer(
        "👨‍🎓 <b>O'quvchi anketasi</b>\n\n"
        "Iltimos, pasportdagi to'liq ism-sharifingizni (F.I.O) kiriting:\n"
        "<i>(Masalan: Eshmatov Toshmat G'ishmatovich)</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Registration.fio)


@user_router.message(Registration.fio)
async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)],
            [types.KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

    await message.answer("Endi telefon raqamingizni yuboring yoki yozib qoldiring:", reply_markup=keyboard)
    await state.set_state(Registration.phone)


@user_router.message(Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await cmd_start(message, state)
        return

    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone_number)

    await message.answer("Raqam qabul qilindi ✅", reply_markup=types.ReplyKeyboardRemove())

    await show_regions(message)
    await state.set_state(Registration.region)


# ==========================================
# 4. UMUMIY HUDUD TANLASH
# ==========================================

async def show_regions(message_or_callback):
    builder = InlineKeyboardBuilder()

    for region in UZB_REGIONS.keys():
        builder.button(text=region, callback_data=RegionCB(name=region))

    builder.button(text="🔙 Orqaga", callback_data="back_to_phone")
    builder.adjust(2)

    text = "Iltimos, yashash viloyatingizni tanlang:"

    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=builder.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup())


@user_router.callback_query(Registration.region, RegionCB.filter())
@user_router.callback_query(TeacherRegistration.region, RegionCB.filter())
async def process_region_selection(callback: types.CallbackQuery, callback_data: RegionCB, state: FSMContext):
    selected_region = callback_data.name
    districts = UZB_REGIONS.get(selected_region, [])

    builder = InlineKeyboardBuilder()

    for district in districts:
        builder.button(
            text=district,
            callback_data=DistrictCB(reg_name=selected_region, name=district)
        )

    builder.button(text="🔙 Viloyatlarga qaytish", callback_data="back_to_regions")
    builder.adjust(2)

    await callback.message.edit_text(
        f"📍 Viloyat: <b>{selected_region}</b>\nEndi tumaningizni tanlang:",
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )


@user_router.callback_query(Registration.region, DistrictCB.filter())
@user_router.callback_query(TeacherRegistration.region, DistrictCB.filter())
async def process_district_selection(callback: types.CallbackQuery, callback_data: DistrictCB, state: FSMContext):
    full_region = f"{callback_data.reg_name}, {callback_data.name}"
    await state.update_data(region=full_region)
    await callback.message.delete()

    current_state = await state.get_state()

    if current_state == TeacherRegistration.region.state:
        await callback.message.answer(
            f"Hudud qabul qilindi: {full_region} ✅\n\n"
            "Yoshingizni faqat raqam bilan kiriting (Masalan: 28):"
        )
        await state.set_state(TeacherRegistration.age)
    else:
        await callback.message.answer(
            f"Hudud: <b>{full_region}</b> ✅\n\n"
            "Yoshingizni faqat raqam bilan kiriting (Masalan: 24):",
            parse_mode="HTML",
            reply_markup=back_kb()
        )
        await state.set_state(Registration.age)


@user_router.callback_query(F.data == "back_to_phone")
async def inline_back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)],
            [types.KeyboardButton(text="🔙 Orqaga")]
        ],
        resize_keyboard=True
    )

    await callback.message.answer("Telefon raqamingizni yuboring:", reply_markup=keyboard)

    current_state = await state.get_state()

    if current_state == TeacherRegistration.region.state:
        await state.set_state(TeacherRegistration.phone)
    else:
        await state.set_state(Registration.phone)


@user_router.callback_query(F.data == "back_to_regions")
async def inline_back_to_regions(callback: types.CallbackQuery, state: FSMContext):
    await show_regions(callback)


# ==========================================
# 5. O'QUVCHI YOSH KELGANDA -> TASDIQLASH
# ==========================================

@user_router.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        await message.answer("Viloyatni qayta tanlang:", reply_markup=types.ReplyKeyboardRemove())
        await show_regions(message)
        await state.set_state(Registration.region)
        return

    if not message.text.isdigit():
        await message.answer("Iltimos, yoshingizni faqat raqamlar bilan yozing!")
        return

    await state.update_data(age=int(message.text))
    data = await state.get_data()

    keyboard = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="✅ Tasdiqlash")],
            [types.KeyboardButton(text="✏️ Tahrirlash (Boshidan)")]
        ],
        resize_keyboard=True
    )

    summary = (
        f"📝 <b>Ma'lumotlaringizni tekshiring:</b>\n\n"
        f"👤 F.I.O: {data['fio']}\n"
        f"📞 Tel: {data['phone']}\n"
        f"📍 Hudud: {data['region']}\n"
        f"📅 Yosh: {data['age']}\n\n"
        f"⚠️ Barchasi to'g'riligini tekshirib, tasdiqlang yoki tahrirlang."
    )

    await message.answer(summary, parse_mode="HTML", reply_markup=keyboard)
    await state.set_state(Registration.confirm)


# ==========================================
# 6. O'QUVCHI TASDIQLAGANDA -> BAZAGA SAQLASH
# ==========================================

@user_router.message(Registration.confirm)
async def s_confirm_registration(message: types.Message, state: FSMContext):
    if message.text == "✏️ Tahrirlash (Boshidan)":
        await start_student_reg(message, state)
        return

    if message.text != "✅ Tasdiqlash":
        await message.answer("Iltimos, pastdagi tugmalardan birini tanlang.")
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
        f"✅ <b>{data['fio']}</b>, siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
        "Quyidagi menyu orqali o'zingizga kerakli kursni tanlashingiz mumkin 👇",
        parse_mode="HTML",
        reply_markup=student_main_menu()
    )


# ==========================================
# 7. SHAXSIY PROFIL
# ==========================================

@user_router.message(F.text == "👤 Profil")
async def show_profile(message: types.Message):
    profile = await get_full_profile(message.from_user.id)

    if not profile:
        await message.answer("Sizning profilingiz topilmadi. /start orqali ro'yxatdan o'ting.")
        return

    role = profile["role"]

    text = (
        f"👤 <b>Shaxsiy Profilingiz</b>\n\n"
        f"<b>F.I.O:</b> {profile['full_name']}\n"
        f"<b>Telefon:</b> {profile['phone']}\n"
        f"<b>Hudud:</b> {profile['region']}\n"
        f"<b>Yosh:</b> {profile['age']}\n"
    )

    if role == "teacher":
        status_text = "✅ Tasdiqlangan Ustoz"
        text += f"<b>Fan:</b> {profile['teach_lang']}\n"

    elif role == "pending_teacher":
        status_text = "⏳ Ko'rib chiqilmoqda (Ustozlik arizasi)"

    elif role == "rejected_teacher":
        status_text = "❌ Rad etilgan (Ma'muriyat tasdiqlamadi)"

    elif role == "admin":
        status_text = "👨‍💻 Admin"

    elif role == "superadmin":
        status_text = "👑 Superadmin"

    else:
        from database.db import get_student_status

        student_status = await get_student_status(message.from_user.id)

        if student_status == "pending":
            status_text = "⏳ Ko'rib chiqilmoqda (To'lov tasdig'i kutilmoqda)"
        elif student_status == "approved":
            status_text = "✅ Tasdiqlangan O'quvchi (Guruhga qo'shilgan)"
        elif student_status == "rejected":
            status_text = "❌ Rad etilgan (To'lov cheki tasdiqlanmadi)"
        else:
            status_text = "🆕 Yangi O'quvchi (Hali kurs tanlanmagan)"

    text += f"\n📊 <b>Status:</b> {status_text}"

    await message.answer(text, parse_mode="HTML")
