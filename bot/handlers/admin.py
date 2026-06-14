# handlers/admin.py
from aiogram import Router, types, F
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import get_payment, update_payment_status, get_active_groups, get_group_link
from utils.states import AdminApproveCB, AdminRejectCB, AdminGroupCB

admin_router = Router()

# --- 1. ADMIN RAD ETGANDA ---
@admin_router.callback_query(AdminRejectCB.filter())
async def admin_reject(callback: types.CallbackQuery, callback_data: AdminRejectCB):
    payment_id = callback_data.payment_id
    payment_data = await get_payment(payment_id)
    
    if payment_data['status'] != 'pending':
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    # Bazada statusni o'zgartirish
    await update_payment_status(payment_id, 'rejected')
    
    # Admindagi tugmalarni olib tashlash va xabarni tahrirlash
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n❌ <b>Holat: RAD ETILDI</b>", 
        parse_mode="HTML"
    )
    
    # O'quvchiga xabar berish
    await callback.bot.send_message(
        chat_id=payment_data['user_id'],
        text="❌ Kechirasiz, sizning to'lov chekingiz ma'muriyat tomonidan tasdiqlanmadi. Iltimos, qaytadan urinib ko'ring yoki ofis bilan bog'laning."
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
        btn_text = f"{grp['name']} ({grp['language']})"
        builder.button(text=btn_text, callback_data=AdminGroupCB(payment_id=payment_id, group_id=grp['id']))
    
    builder.adjust(1)
    
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ O'quvchini qaysi guruhga qo'shamiz?", 
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )

# --- 3. ADMIN GURUHNI TANLAGANDA (O'QUVCHIGA SSILKA BORADI) ---
@admin_router.callback_query(AdminGroupCB.filter())
async def admin_assign_group(callback: types.CallbackQuery, callback_data: AdminGroupCB):
    payment_id = callback_data.payment_id
    group_id = callback_data.group_id
    
    payment_data = await get_payment(payment_id)
    group_data = await get_group_link(group_id)
    
    # Bazada statusni 'approved' ga o'zgartiramiz
    await update_payment_status(payment_id, 'approved')
    
    # Admindagi xabarni yakuniy holatga keltiramiz
    await callback.message.edit_caption(
        caption=f"{callback.message.caption}\n\n✅ <b>Holat: TASDIQLANDI</b>\n"
                f"Biriktirildi: {group_data['name']}",
        parse_mode="HTML"
    )
    
    # Eng zo'r qismi: O'quvchiga Guruh ssilkasini yuboramiz!
    await callback.bot.send_message(
        chat_id=payment_data['user_id'],
        text=f"🎉 <b>Tabriklaymiz! Sizning to'lovingiz tasdiqlandi!</b>\n\n"
             f"Siz <b>{group_data['name']}</b> guruhiga biriktirildingiz.\n\n"
             f"Guruhga qo'shilish havolasi (ssilka) 👇\n"
             f"{group_data['telegram_link']}",
        parse_mode="HTML"
    )