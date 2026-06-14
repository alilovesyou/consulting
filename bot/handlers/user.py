# handlers/user.py
from aiogram import Router, types, F
from aiogram.filters import CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import add_user, update_user_profile
from utils.states import Registration, RegionCB, DistrictCB
from utils.data import UZB_REGIONS

user_router = Router()

# Umumiy "Orqaga" tugmasi (oddiy klaviatura uchun)
def back_kb():
    return types.ReplyKeyboardMarkup(
        keyboard=[[types.KeyboardButton(text="🔙 Orqaga")]], 
        resize_keyboard=True
    )

# --- 1. START VA F.I.O ---
@user_router.message(CommandStart())
async def cmd_start(message: types.Message, state: FSMContext):
    # Dastlabki bazaga yozish (ID ni saqlab qolish uchun)
    await add_user(message.from_user.id, message.from_user.full_name)
    
    # Orqaga qaytishlar to'qnashmasligi uchun xotirani tozalaymiz
    await state.clear()
    
    await message.answer(
        f"Assalomu alaykum! 👋\n"
        "Visa & Language Consulting tizimiga xush kelibsiz.\n\n"
        "Iltimos, pasportdagi to'liq ism-sharifingizni (F.I.O) kiriting:\n"
        "<i>(Masalan: Eshmatov Toshmat G'ishmatovich)</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(Registration.fio)

# --- 2. FIO KELGANDA -> TELEFON ---
@user_router.message(Registration.fio)
async def process_fio(message: types.Message, state: FSMContext):
    await state.update_data(fio=message.text)
    
    kb = [
        [types.KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)],
        [types.KeyboardButton(text="🔙 Orqaga")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await message.answer("Endi telefon raqamingizni yuboring yoki yozib qoldiring:", reply_markup=keyboard)
    await state.set_state(Registration.phone)

# --- 3. TELEFON KELGANDA -> VILOYAT (INLINE) ---
@user_router.message(Registration.phone)
async def process_phone(message: types.Message, state: FSMContext):
    # "Orqaga" bosilgan bo'lsa
    if message.text == "🔙 Orqaga":
        await cmd_start(message, state)
        return

    # Raqamni saqlaymiz (Contact tugma yoki qo'lda yozilgan bo'lishi mumkin)
    phone_number = message.contact.phone_number if message.contact else message.text
    await state.update_data(phone=phone_number)
    
    # Pasdagi klaviaturani yopamiz
    await message.answer("Raqam qabul qilindi ✅", reply_markup=types.ReplyKeyboardRemove())
    
    # Viloyatlar klaviaturasini chaqiramiz
    await show_regions(message)
    await state.set_state(Registration.region)

# Viloyatlarni ko'rsatish funksiyasi (Qayta ishlatish uchun)
async def show_regions(message_or_callback):
    builder = InlineKeyboardBuilder()
    for region in UZB_REGIONS.keys():
        builder.button(text=region, callback_data=RegionCB(name=region))
    
    # Inline Orqaga tugmasi
    builder.button(text="🔙 Orqaga", callback_data="back_to_phone")
    builder.adjust(2) # 2 tadan ustun
    
    text = "Iltimos, yashash viloyatingizni tanlang:"
    if isinstance(message_or_callback, types.Message):
        await message_or_callback.answer(text, reply_markup=builder.as_markup())
    else:
        await message_or_callback.message.edit_text(text, reply_markup=builder.as_markup())

# --- 4. VILOYAT TANLANGANDA -> TUMAN (INLINE) ---
@user_router.callback_query(Registration.region, RegionCB.filter())
async def process_region_selection(callback: types.CallbackQuery, callback_data: RegionCB, state: FSMContext):
    selected_region = callback_data.name
    districts = UZB_REGIONS.get(selected_region, [])
    
    builder = InlineKeyboardBuilder()
    for district in districts:
        builder.button(text=district, callback_data=DistrictCB(reg_name=selected_region, name=district))
    
    # Viloyatlarga qaytish tugmasi
    builder.button(text="🔙 Viloyatlarga qaytish", callback_data="back_to_regions")
    builder.adjust(2)
    
    await callback.message.edit_text(
        f"📍 Viloyat: <b>{selected_region}</b>\nEndi tumaningizni tanlang:", 
        reply_markup=builder.as_markup(),
        parse_mode="HTML"
    )

# --- INLINE ORQAGA QAYTISH TUGMALARI ---
@user_router.callback_query(F.data == "back_to_phone")
async def inline_back_to_phone(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    # Telefon so'rash holatiga qaytamiz
    kb = [
        [types.KeyboardButton(text="📞 Raqamni yuborish", request_contact=True)],
        [types.KeyboardButton(text="🔙 Orqaga")]
    ]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    await callback.message.answer("Telefon raqamingizni yuboring:", reply_markup=keyboard)
    await state.set_state(Registration.phone)

@user_router.callback_query(F.data == "back_to_regions")
async def inline_back_to_regions(callback: types.CallbackQuery, state: FSMContext):
    await show_regions(callback)

# --- 5. TUMAN TANLANGANDA -> YOSH ---
@user_router.callback_query(Registration.region, DistrictCB.filter())
async def process_district_selection(callback: types.CallbackQuery, callback_data: DistrictCB, state: FSMContext):
    full_region = f"{callback_data.reg_name}, {callback_data.name}"
    await state.update_data(region=full_region)
    
    await callback.message.delete()
    await callback.message.answer(
        f"Hudud: <b>{full_region}</b> ✅\n\n"
        "Yoshingizni faqat raqam bilan kiriting (Masalan: 24):",
        parse_mode="HTML",
        reply_markup=back_kb() # Pastki oddiy orqaga tugmasi
    )
    await state.set_state(Registration.age)

# --- 6. YOSH KELGANDA -> YAKUNLASH ---
@user_router.message(Registration.age)
async def process_age(message: types.Message, state: FSMContext):
    if message.text == "🔙 Orqaga":
        # Tumanlarga qaytish qiyin bo'lgani uchun, viloyat tanlashni boshidan beramiz
        await message.answer("Viloyatni qayta tanlang:", reply_markup=types.ReplyKeyboardRemove())
        await show_regions(message)
        await state.set_state(Registration.region)
        return

    if not message.text.isdigit():
        await message.answer("Iltimos, yoshingizni faqat raqamlar bilan yozing!")
        return

    data = await state.get_data()
    fio = data['fio']
    phone = data['phone']
    region = data['region']
    age = int(message.text)

    # Bazaga to'liq saqlaymiz
    await update_user_profile(message.from_user.id, fio, phone, region, age)
    await state.clear()

    # Asosiy menyu klaviaturasi
    menu_kb = types.ReplyKeyboardMarkup(
        keyboard=[
            [types.KeyboardButton(text="📚 Kurslar"), types.KeyboardButton(text="👤 Profil")]
        ],
        resize_keyboard=True
    )
    
    await message.answer(
        f"✅ <b>{fio}</b>, siz muvaffaqiyatli ro'yxatdan o'tdingiz!\n\n"
        "Quyidagi menyu orqali o'zingizga kerakli kursni tanlashingiz mumkin 👇",
        parse_mode="HTML",
        reply_markup=menu_kb
    )
