# handlers/admin.py
from aiogram import Router, types, F
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder



from database.db import (
    get_payment, update_payment_status, get_active_groups, 
    get_group_link, add_student_to_group, update_teacher_status, 
    get_all_teachers, create_new_group, 
    get_bot_statistics, get_all_groups, change_group_teacher, delete_group,
    get_kick_request, update_kick_request_status, remove_student_from_group,
    get_user_role, add_student_to_group_if_capacity
)
from utils.states import (
    AdminApproveCB, AdminRejectCB, AdminGroupCB,
    AdminTeacherApproveCB, AdminTeacherRejectCB,
    CreateGroup, AssignTeacherCB, KickApproveCB, KickRejectCB
)

admin_router = Router()

class AdminOnly(BaseFilter):
    async def __call__(self, event) -> bool:
        if not getattr(event, "from_user", None):
            return False

        role = await get_user_role(event.from_user.id)
        return role in ["admin", "superadmin"]


admin_router.message.filter(AdminOnly())
admin_router.callback_query.filter(AdminOnly())

# --- 1. ADMIN RAD ETGANDA (KURS TO'LOVI) ---
@admin_router.callback_query(AdminRejectCB.filter())
async def admin_reject(callback: types.CallbackQuery, callback_data: AdminRejectCB):
    payment_id = callback_data.payment_id
    payment_data = await get_payment(payment_id)
    
    if payment_data['status'] != 'pending':
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Bazada statusni o'zgartirish
    await update_payment_status(payment_id, 'rejected')
    
    # Rasm/Fayl yoki Oddiy text ekanligini tekshirib tahrirlaymiz
    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n❌ <b>Holat: RAD ETILDI</b>", 
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n❌ <b>Holat: RAD ETILDI</b>", 
            parse_mode="HTML"
        )
    
    # O'quvchiga xabar berish
    await callback.bot.send_message(
        chat_id=payment_data['user_id'],
        text="❌ Kechirasiz, sizning to'lov chekingiz ma'muriyat tomonidan tasdiqlanmadi (Chek xato yoki noaniq bo'lishi mumkin).\n\n"
             "<b>Qaytadan urinib ko'rish yoki boshqa chek yuborish uchun pastdagi 📚 Kurslar menyusidan qaytadan to'lov qiling.</b>",
        parse_mode="HTML"
    )

# --- 2. ADMIN TASDIQLAGANDA (GURUHLARNI CHIQARISH) ---
@admin_router.callback_query(AdminApproveCB.filter())
async def admin_approve(callback: types.CallbackQuery, callback_data: AdminApproveCB):
    payment_id = callback_data.payment_id
    payment_data = await get_payment(payment_id)
    
    if payment_data['status'] != 'pending':
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Bazadan mavjud guruhlarni olamiz
    groups = await get_active_groups()
    if not groups:
        await callback.answer("Bazada hech qanday faol guruh yo'q! Avval guruh qo'shing.", show_alert=True)
        return

    # Guruhlar ro'yxatini tugma qilib chiqaramiz
    builder = InlineKeyboardBuilder()
    for grp in groups:
        btn_text = f"{grp['name']} ({grp['language']}) — {grp['current_count']}/{grp['max_capacity']}"
        builder.button(
            text=btn_text,
            callback_data=AdminGroupCB(payment_id=payment_id, group_id=grp['id'])
        )
    
    builder.adjust(1)
    
    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n✅ O'quvchini qaysi guruhga qo'shamiz?", 
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n✅ O'quvchini qaysi guruhga qo'shamiz?", 
            parse_mode="HTML",
            reply_markup=builder.as_markup()
        )

# --- 3. ADMIN GURUHNI TANLAGANDA (O'QUVCHIGA SSILKA BORADI) ---
@admin_router.callback_query(AdminGroupCB.filter(F.payment_id != 0))
async def admin_assign_group(callback: types.CallbackQuery, callback_data: AdminGroupCB):
    payment_id = callback_data.payment_id
    group_id = callback_data.group_id
    
    payment_data = await get_payment(payment_id)
    group_data = await get_group_link(group_id)
    
    capacity_result = await add_student_to_group_if_capacity(payment_data['user_id'], group_id)

    if not capacity_result["ok"]:
        await callback.answer(capacity_result["message"], show_alert=True)
        return
    
    await update_payment_status(payment_id, 'approved')
    
    # Admindagi xabarni yakuniy holatga keltiramiz
    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n✅ <b>Holat: TASDIQLANDI</b>\n"
                    f"Biriktirildi: {group_data['name']}",
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n✅ <b>Holat: TASDIQLANDI</b>\n"
                    f"Biriktirildi: {group_data['name']}",
            parse_mode="HTML"
        )
    
    # O'quvchiga Guruh ssilkasini yuboramiz!
    await callback.bot.send_message(
        chat_id=payment_data['user_id'],
        text=f"🎉 <b>Tabriklaymiz! Sizning to'lovingiz tasdiqlandi!</b>\n\n"
             f"Siz <b>{group_data['name']}</b> guruhiga biriktirildingiz.\n\n"
             f"Guruhga qo'shilish havolasi (ssilka) 👇\n"
             f"{group_data['telegram_link']}",
        parse_mode="HTML"
    )

# --- 5. USTOZ ARIZASINI RAD ETISH ---
@admin_router.callback_query(AdminTeacherRejectCB.filter())
async def admin_reject_teacher(callback: types.CallbackQuery, callback_data: AdminTeacherRejectCB):
    teacher_id = callback_data.teacher_id
    await update_teacher_status(teacher_id, 'rejected_teacher')
    
    # Rasm/Fayl yoki Oddiy text ekanligini tekshirib tahrirlaymiz
    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n❌ <b>QAROR: RAD ETILDI</b>", 
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n❌ <b>QAROR: RAD ETILDI</b>", 
            parse_mode="HTML"
        )
        
    await callback.bot.send_message(
        chat_id=teacher_id, 
        text="❌ Kechirasiz, sizning ustozlik arizangiz ma'muriyat tomonidan tasdiqlanmadi."
    )

# --- 6. USTOZ ARIZASINI QABUL QILISH ---
@admin_router.callback_query(AdminTeacherApproveCB.filter())
async def admin_approve_teacher(callback: types.CallbackQuery, callback_data: AdminTeacherApproveCB):
    teacher_id = callback_data.teacher_id
    
    # Bazada rolini 'teacher' ga o'zgartiramiz
    await update_teacher_status(teacher_id, 'teacher')
    
    # Rasm/Fayl yoki Oddiy text ekanligini tekshirib tahrirlaymiz
    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n✅ <b>QAROR: QABUL QILINDI</b>", 
            parse_mode="HTML"
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n✅ <b>QAROR: QABUL QILINDI</b>", 
            parse_mode="HTML"
        )
    
    # Yangi ustozga xabar yuboramiz
    await callback.bot.send_message(
        chat_id=teacher_id, 
        text="🎉 <b>Tabriklaymiz! Siz ishga qabul qilindingiz.</b>\n\n"
             "Sizga Ustoz maqomi berildi. Iltimos, /start buyrug'ini bosib o'z ish panelingizga kiring.",
        parse_mode="HTML"
    )

# --- 7. STATISTIKA ---
@admin_router.message(F.text == "📊 Statistika")
async def show_statistics(message: types.Message):
    stats = await get_bot_statistics()
    text = (
        "📊 <b>Platforma Statistikasi:</b>\n\n"
        f"👨‍🎓 Jami O'quvchilar: <b>{stats['students']}</b> ta\n"
        f"👨‍🏫 Jami Ustozlar: <b>{stats['teachers']}</b> ta\n"
        f"📚 Faol Guruhlar: <b>{stats['groups']}</b> ta\n"
    )
    await message.answer(text, parse_mode="HTML")

# --- 8. GURUH YARATISH JARAYONI ---
@admin_router.message(F.text == "➕ Guruh yaratish")
async def start_create_group(message: types.Message, state: FSMContext):
    await message.answer(
        "📝 Yangi guruh nomini kiriting:\n<i>(Masalan: IELTS - N1 yoki Dasturlash - 1)</i>", 
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(CreateGroup.name)

@admin_router.message(CreateGroup.name)
async def cg_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    
    from utils.data import LANGUAGES
    builder = InlineKeyboardBuilder()
    for code, name in LANGUAGES.items():
        builder.button(text=name, callback_data=f"cglang_{name}")
    builder.adjust(2)
    
    await message.answer("Qaysi til/fan o'qitiladi?", reply_markup=builder.as_markup())
    await state.set_state(CreateGroup.language)

@admin_router.callback_query(CreateGroup.language, F.data.startswith("cglang_"))
async def cg_lang(callback: types.CallbackQuery, state: FSMContext):
    lang = callback.data.split("_")[1]
    await state.update_data(language=lang)
    
    await callback.message.edit_text(f"Til tanlandi: {lang} ✅")
    await callback.message.answer("👥 Guruh sig'imi (Limit) qancha bo'ladi? Faqat raqam yozing:\n<i>(Masalan: 15)</i>", parse_mode="HTML")
    await state.set_state(CreateGroup.capacity)

@admin_router.message(CreateGroup.capacity)
async def cg_capacity(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return
        
    await state.update_data(capacity=int(message.text))
    await message.answer("🔗 Telegram guruh/kanal havolasini (ssilkasini) yuboring:\n<i>(Masalan: https://t.me/+AbCdEf...)</i>", parse_mode="HTML")
    await state.set_state(CreateGroup.link)

@admin_router.message(CreateGroup.link)
async def cg_link(message: types.Message, state: FSMContext):
    await state.update_data(link=message.text)
    
    # Bazadagi hamma "teacher" rolli odamlarni tortamiz
    teachers = await get_all_teachers()
    
    if not teachers:
        # Menyu tugmalarini joyiga qaytarib qo'yamiz
        kb = [[types.KeyboardButton(text="➕ Guruh yaratish"), types.KeyboardButton(text="📊 Statistika")]]
        keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
        await message.answer("⚠️ Bazada tasdiqlangan ustozlar yo'q! Guruh ochish uchun avval ustoz ishga qabul qiling.", reply_markup=keyboard)
        await state.clear()
        return
        
    builder = InlineKeyboardBuilder()
    for t in teachers:
        builder.button(text=f"{t['full_name']} ({t['teach_lang']})", callback_data=AssignTeacherCB(teacher_id=t['telegram_id']))
    builder.adjust(1)
    
    await message.answer("👨‍🏫 Bu guruhga qaysi ustozni biriktiramiz?", reply_markup=builder.as_markup())
    await state.set_state(CreateGroup.teacher)

@admin_router.callback_query(CreateGroup.teacher, AssignTeacherCB.filter())
async def cg_teacher(callback: types.CallbackQuery, callback_data: AssignTeacherCB, state: FSMContext):
    data = await state.get_data()
    teacher_id = callback_data.teacher_id
    
    # Bazaga yozamiz
    await create_new_group(data['name'], data['language'], data['capacity'], data['link'], teacher_id)
    
    # Menyu tugmalarini joyiga qaytarish
    kb = [[types.KeyboardButton(text="➕ Guruh yaratish"), types.KeyboardButton(text="📊 Statistika")]]
    keyboard = types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
    
    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>{data['name']}</b> guruhi muvaffaqiyatli yaratildi va ustozga biriktirildi!",
        parse_mode="HTML",
        reply_markup=keyboard
    )
    await state.clear()

# --- 9. GURUHLARNI BOSHQARISH ---
@admin_router.message(F.text == "📚 Guruhlar ro'yxati")
async def list_groups_for_admin(message: types.Message):
    groups = await get_all_groups()
    if not groups:
        await message.answer("Guruhlar mavjud emas.")
        return
        
    builder = InlineKeyboardBuilder()
    for g in groups:
        builder.button(text=g['name'], callback_data=AdminGroupCB(payment_id=0, group_id=g['id']))
    builder.adjust(1)
    await message.answer("Tahrirlamoqchi bo'lgan guruhni tanlang:", reply_markup=builder.as_markup())

# --- Guruh tanlanganda tahrirlash menyusi ---
@admin_router.callback_query(AdminGroupCB.filter(F.payment_id == 0))
async def manage_group_options(callback: types.CallbackQuery, callback_data: AdminGroupCB):
    group_id = callback_data.group_id
    builder = InlineKeyboardBuilder()
    builder.button(text="🔄 Ustozni almashtirish", callback_data=f"ch_tch_{group_id}")
    builder.button(text="❌ Guruhni o'chirish", callback_data=f"del_grp_{group_id}")
    builder.adjust(1)
    await callback.message.edit_text("Guruh bilan nima qilamiz?", reply_markup=builder.as_markup())

# --- Ustozni almashtirish logikasi ---
@admin_router.callback_query(F.data.startswith("ch_tch_"))
async def change_teacher_start(callback: types.CallbackQuery):
    group_id = int(callback.data.split("_")[2])
    teachers = await get_all_teachers()
    
    builder = InlineKeyboardBuilder()
    for t in teachers:
        builder.button(text=t['full_name'], callback_data=f"set_new_t_{group_id}_{t['telegram_id']}")
    builder.adjust(1)
    await callback.message.edit_text("Yangi ustozni tanlang:", reply_markup=builder.as_markup())

@admin_router.callback_query(F.data.startswith("set_new_t_"))
async def set_new_teacher(callback: types.CallbackQuery):
    parts = callback.data.split("_")
    group_id, teacher_id = int(parts[3]), int(parts[4])
    await change_group_teacher(group_id, teacher_id)
    await callback.message.edit_text("✅ Ustoz muvaffaqiyatli almashtirildi!")

@admin_router.callback_query(F.data.startswith("del_grp_"))
async def delete_group_handler(callback: types.CallbackQuery):
    group_id = int(callback.data.split("_")[2])
    await delete_group(group_id)
    await callback.message.edit_text("✅ Guruh muvaffaqiyatli o‘chirildi.")

# --- 10. CHETLATISH SO'ROVINI TASDIQLASH ---
@admin_router.callback_query(KickApproveCB.filter())
async def approve_kick_request(callback: types.CallbackQuery, callback_data: KickApproveCB):
    request_id = callback_data.request_id
    request = await get_kick_request(request_id)

    if not request:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    if request['status'] != 'pending':
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await remove_student_from_group(request['user_id'], request['group_id'])
    await update_kick_request_status(request_id, 'approved')

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n"
        f"✅ <b>QAROR: CHETLATISH TASDIQLANDI</b>",
        parse_mode="HTML"
    )

    await callback.bot.send_message(
        chat_id=request['teacher_id'],
        text=(
            f"✅ Siz yuborgan chetlatish so'rovi tasdiqlandi.\n\n"
            f"👤 O'quvchi: {request['student_name']}\n"
            f"📚 Guruh: {request['group_name']}"
        )
    )

    await callback.bot.send_message(
        chat_id=request['user_id'],
        text=(
            f"❌ Siz <b>{request['group_name']}</b> guruhidan chetlatildingiz.\n\n"
            f"Sabab va batafsil ma'lumot uchun ma'muriyat bilan bog'laning."
        ),
        parse_mode="HTML"
    )


# --- 11. CHETLATISH SO'ROVINI RAD ETISH ---
@admin_router.callback_query(KickRejectCB.filter())
async def reject_kick_request(callback: types.CallbackQuery, callback_data: KickRejectCB):
    request_id = callback_data.request_id
    request = await get_kick_request(request_id)

    if not request:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    if request['status'] != 'pending':
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await update_kick_request_status(request_id, 'rejected')

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n"
        f"❌ <b>QAROR: RAD ETILDI</b>",
        parse_mode="HTML"
    )

    await callback.bot.send_message(
        chat_id=request['teacher_id'],
        text=(
            f"❌ Siz yuborgan chetlatish so'rovi admin tomonidan rad etildi.\n\n"
            f"👤 O'quvchi: {request['student_name']}\n"
            f"📚 Guruh: {request['group_name']}"
        )
    )