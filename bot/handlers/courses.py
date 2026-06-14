# handlers/courses.py
import os
from aiogram import Bot
from aiogram.types import FSInputFile
from database.db import add_payment, get_user
from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder


from utils.states import OrderCourse, LangCB, PackCB, AdminApproveCB, AdminRejectCB
from utils.data import LANGUAGES, PACKAGES

courses_router = Router()

# --- 1. KURS TUGMASI BOSILGANDA (TILLARNI CHIQARISH) ---
@courses_router.message(F.text == "📚 Kurslar")
async def show_languages(message: types.Message):
    builder = InlineKeyboardBuilder()
    
    # Tillar ro'yxatidan tugmalar yasash
    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=LangCB(code=code))
    
    builder.adjust(2) # 2 tadan ustun
    
    await message.answer("Qaysi tilni o'rganmoqchisiz? Tanlang:", reply_markup=builder.as_markup())

# --- 2. TIL TANLANGANDA (PAKETLARNI CHIQARISH) ---
@courses_router.callback_query(LangCB.filter())
async def show_packages(callback: types.CallbackQuery, callback_data: LangCB):
    lang_code = callback_data.code
    lang_name = LANGUAGES[lang_code]
    
    builder = InlineKeyboardBuilder()
    # Paketlar uchun tugmalar
    for p_type, p_name in PACKAGES.items():
        builder.button(
            text=p_name, 
            callback_data=PackCB(lang_code=lang_code, pack_type=p_type)
        )
    
    # Orqaga (Tillarga qaytish)
    builder.button(text="🔙 Tillarga qaytish", callback_data="back_to_langs")
    builder.adjust(1) # Paketlar uzun yozuv bo'lgani uchun 1 tadan qatorda turadi
    
    await callback.message.edit_text(
        f"📚 Tanlangan til: <b>{lang_name}</b>\n\n"
        "O'qish formatini (Paketni) tanlang:\n"
        "<i>Guruh darslarida max 10 kishi bo'ladi. Individual darsda faqat siz va ustoz.</i>",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# Tillarga qaytish tugmasi mantiqi
@courses_router.callback_query(F.data == "back_to_langs")
async def back_to_langs(callback: types.CallbackQuery):
    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=LangCB(code=code))
    builder.adjust(2)
    
    await callback.message.edit_text("Qaysi tilni o'rganmoqchisiz? Tanlang:", reply_markup=builder.as_markup())

# --- 3. PAKET TANLANGANDA (TO'LOV TURINI SO'RASH) ---
@courses_router.callback_query(PackCB.filter())
async def show_payment_options(callback: types.CallbackQuery, callback_data: PackCB, state: FSMContext):
    lang_name = LANGUAGES[callback_data.lang_code]
    pack_name = PACKAGES[callback_data.pack_type]
    
    # Tanlangan ma'lumotlarni xotirada saqlaymiz (To'lovda ishlatish uchun)
    await state.update_data(selected_lang=lang_name, selected_pack=pack_name)
    
    # To'lov turlari tugmasi
    builder = InlineKeyboardBuilder()
    builder.button(text="💳 Karta orqali", callback_data="pay_card")
    builder.button(text="💵 Naqd pul orqali", callback_data="pay_cash")
    builder.button(text="🔙 Orqaga", callback_data=LangCB(code=callback_data.lang_code).pack())
    builder.adjust(2, 1)
    
    await callback.message.edit_text(
        f"📝 <b>Sizning tanlovingiz:</b>\n"
        f"Til: {lang_name}\n"
        f"Paket: {pack_name}\n\n"
        f"To'lovni qanday usulda amalga oshirasiz?",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# --- 4. KARTA ORQALI TO'LOV TANLANGANDA ---
@courses_router.callback_query(F.data == "pay_card")
async def pay_card(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "💳 <b>Karta orqali to'lov</b>\n\n"
        "Karta raqami: <code>8600 1234 5678 9012</code>\n"
        "Qabul qiluvchi: Visa & Language Consulting\n\n"
        "To'lovni amalga oshirgach, <b>chek rasmini (skrinshot) yoki PDF faylini</b> shu yerga yuboring:",
        parse_mode="HTML"
    )
    # Endi bot foydalanuvchidan rasm kutadi
    await state.set_state(OrderCourse.receipt)

# --- 5. NAQD PUL ORQALI TANLANGANDA ---
@courses_router.callback_query(F.data == "pay_cash")
async def pay_cash(callback: types.CallbackQuery, state: FSMContext, bot: Bot):
    data = await state.get_data()
    course_info = f"{data['selected_lang']} ({data['selected_pack']})"
    
    # Bazaga yozamiz (Naqd pul bo'lsa rasm yo'q)
    payment_id = await add_payment(callback.from_user.id, course_info, 'cash', None)
    user_data = await get_user(callback.from_user.id)
    
    # Adminga xabar beramiz
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        admin_text = (
            f"💵 <b>Yangi NAQD to'lov so'rovi!</b>\n\n"
            f"🆔 ID: {payment_id}\n"
            f"👤 O'quvchi: {user_data['full_name']}\n"
            f"📞 Telefon: {user_data['phone']}\n"
            f"📚 Kurs: {course_info}"
        )
        await bot.send_message(chat_id=admin_id, text=admin_text, parse_mode="HTML")
    
    await callback.message.edit_text(
        "🏢 <b>Ofisimiz manzili:</b> Sirdaryo viloyati, Guliston shahri, IT Park binosi.\n\n"
        "Kelib to'lovni amalga oshirganingizdan so'ng, adminimiz tizimda tasdiqlaydi va siz guruhga qo'shilasiz.",
        parse_mode="HTML"
    )
    await state.clear()

# --- 6. CHEK RASMI (YOKI FAYL) KELGANDA ---
@courses_router.message(OrderCourse.receipt, F.photo | F.document)
async def process_receipt(message: types.Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    course_info = f"{data['selected_lang']} ({data['selected_pack']})"
    
    # media/receipts papkasi yo'q bo'lsa, kod uni o'zi avtomatik yaratadi
    os.makedirs("media/receipts", exist_ok=True)
    
    # Fayl haqida ma'lumot olish
    if message.photo:
        file_id = message.photo[-1].file_id # Eng tiniq sifatdagisini olamiz
        ext = ".jpg"
    else:
        file_id = message.document.file_id
        ext = f".{message.document.file_name.split('.')[-1]}"
    
    # Faylni serverga (noutbukingizga) yuklab olish
    file = await bot.get_file(file_id)
    # Rasm nomi noyob bo'lishi uchun UserID va FileID aralashtiriladi
    file_path = f"media/receipts/{message.from_user.id}_{file_id[:10]}{ext}"
    await bot.download_file(file.file_path, file_path)
    
    # Bazaga yozish
    payment_id = await add_payment(message.from_user.id, course_info, 'card', file_path)
    user_data = await get_user(message.from_user.id)
    
    # Adminga rasm bilan birga yuborish qismi (process_receipt ichida)
    admin_id = os.getenv("ADMIN_ID")
    if admin_id:
        admin_text = (
            f"💳 <b>Karta orqali yangi to'lov!</b>\n\n"
            f"🆔 So'rov ID: {payment_id}\n"
            f"👤 O'quvchi: {user_data['full_name']}\n"
            f"📞 Telefon: {user_data['phone']}\n"
            f"📚 Kurs: {course_info}"
        )
        
        # Tugmalarni yozamiz
        admin_builder = InlineKeyboardBuilder()
        admin_builder.button(text="✅ Tasdiqlash", callback_data=AdminApproveCB(payment_id=payment_id))
        admin_builder.button(text="❌ Rad etish", callback_data=AdminRejectCB(payment_id=payment_id))
        admin_builder.adjust(2)

        photo_file = FSInputFile(file_path)
        await bot.send_photo(
            chat_id=admin_id, 
            photo=photo_file, 
            caption=admin_text, 
            parse_mode="HTML",
            reply_markup=admin_builder.as_markup()
        )
    
    await message.answer(
        "✅ <b>Chek qabul qilindi va bazaga saqlandi!</b>\n\n"
        "Adminlarimiz to'lovni tekshirib, tez orada sizga guruh havolasini yuborishadi. Iltimos, kuting.",
        parse_mode="HTML"
    )
    await state.clear()