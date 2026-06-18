# handlers/admin.py
from html import escape

from aiogram import Router, types, F
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    get_payment,
    update_payment_status,
    get_active_groups,
    get_group_link,
    update_teacher_status,
    get_all_teachers,
    create_new_group,
    get_bot_statistics,
    get_all_groups,
    change_group_teacher,
    delete_group,
    get_kick_request,
    update_kick_request_status,
    remove_student_from_group,
    get_user_role,
    add_student_to_group_if_capacity,
    log_admin_action,
    get_superadmin_ids,
    upsert_admin_user,
    remove_admin_role,
    get_api_superadmin_admins,
    get_api_superadmin_admin_actions,
    get_api_superadmin_teachers_overview,
    get_api_superadmin_teacher_groups,
    get_api_superadmin_group_students,
    get_api_superadmin_students_overview,
    get_api_superadmin_student_results,
    get_api_superadmin_all_results,
)
from utils.states import (
    AdminApproveCB,
    AdminRejectCB,
    AdminGroupCB,
    AdminTeacherApproveCB,
    AdminTeacherRejectCB,
    CreateGroup,
    AssignTeacherCB,
    KickApproveCB,
    KickRejectCB,
    AddAdminState,
    RemoveAdminCB,
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


async def is_superadmin(user_id: int) -> bool:
    role = await get_user_role(user_id)
    return role == "superadmin"


async def require_superadmin_message(message: types.Message, state: FSMContext | None = None) -> bool:
    if not await is_superadmin(message.from_user.id):
        if state:
            await state.clear()

        await message.answer("⛔ Bu bo'lim faqat Superadmin uchun.")
        return False

    return True


async def require_superadmin_callback(callback: types.CallbackQuery) -> bool:
    if not await is_superadmin(callback.from_user.id):
        await callback.answer("Bu bo'lim faqat Superadmin uchun.", show_alert=True)
        return False

    return True


async def notify_superadmins(bot, actor_id: int, text: str):
    superadmin_ids = await get_superadmin_ids()

    for superadmin_id in superadmin_ids:
        if superadmin_id == actor_id:
            continue

        try:
            await bot.send_message(
                chat_id=superadmin_id,
                text=text,
                parse_mode="HTML",
            )
        except Exception:
            pass


def h(value):
    """HTML parse_mode uchun xavfsiz text."""
    if value is None:
        return "-"
    return escape(str(value))


def superadmin_menu_keyboard():
    kb = [
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
        [types.KeyboardButton(text="📊 Statistika")],
    ]

    return types.ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)


# ==========================================
# 1. ADMIN PAYMENT REJECT
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(AdminRejectCB.filter())
async def admin_reject(callback: types.CallbackQuery, callback_data: AdminRejectCB):
    payment_id = callback_data.payment_id
    payment_data = await get_payment(payment_id)

    if not payment_data:
        await callback.answer("To'lov so'rovi topilmadi.", show_alert=True)
        return

    if payment_data["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    await update_payment_status(payment_id, "rejected")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="payment_rejected_from_bot",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment_data["user_id"],
        },
    )

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n❌ <b>Holat: RAD ETILDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n❌ <b>Holat: RAD ETILDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    await callback.bot.send_message(
        chat_id=payment_data["user_id"],
        text=(
            "❌ Kechirasiz, sizning to'lov chekingiz ma'muriyat tomonidan tasdiqlanmadi "
            "(Chek xato yoki noaniq bo'lishi mumkin).\n\n"
            "<b>Qaytadan urinib ko'rish yoki boshqa chek yuborish uchun pastdagi 📚 Kurslar "
            "menyusidan qaytadan to'lov qiling.</b>"
        ),
        parse_mode="HTML",
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>payment rejected</b>\n"
            f"Payment ID: <code>{payment_id}</code>\n"
            f"Student ID: <code>{payment_data['user_id']}</code>"
        ),
    )


# ==========================================
# 2. ADMIN PAYMENT APPROVE START
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(AdminApproveCB.filter())
async def admin_approve(callback: types.CallbackQuery, callback_data: AdminApproveCB):
    payment_id = callback_data.payment_id
    payment_data = await get_payment(payment_id)

    if not payment_data:
        await callback.answer("To'lov so'rovi topilmadi.", show_alert=True)
        return

    if payment_data["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    groups = await get_active_groups()

    if not groups:
        await callback.answer("Bazada hech qanday faol guruh yo'q! Avval guruh qo'shing.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    for grp in groups:
        btn_text = f"{grp['name']} ({grp['language']}) — {grp['current_count']}/{grp['max_capacity']}"
        builder.button(
            text=btn_text,
            callback_data=AdminGroupCB(payment_id=payment_id, group_id=grp["id"]),
        )

    builder.adjust(1)

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n✅ O'quvchini qaysi guruhga qo'shamiz?",
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n✅ O'quvchini qaysi guruhga qo'shamiz?",
            parse_mode="HTML",
            reply_markup=builder.as_markup(),
        )


# ==========================================
# 3. ADMIN PAYMENT APPROVE FINAL
# Admin + Superadmin
# ==========================================

@admin_router.callback_query(AdminGroupCB.filter(F.payment_id != 0))
async def admin_assign_group(callback: types.CallbackQuery, callback_data: AdminGroupCB):
    payment_id = callback_data.payment_id
    group_id = callback_data.group_id

    payment_data = await get_payment(payment_id)

    if not payment_data:
        await callback.answer("To'lov so'rovi topilmadi.", show_alert=True)
        return

    if payment_data["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan!", show_alert=True)
        return

    group_data = await get_group_link(group_id)

    if not group_data:
        await callback.answer("Guruh topilmadi.", show_alert=True)
        return

    capacity_result = await add_student_to_group_if_capacity(payment_data["user_id"], group_id)

    if not capacity_result["ok"]:
        await callback.answer(capacity_result["message"], show_alert=True)
        return

    await update_payment_status(payment_id, "approved")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="payment_approved_from_bot",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment_data["user_id"],
            "group_id": group_id,
            "group_name": group_data["name"],
            "capacity": capacity_result,
        },
    )

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=(
                f"{callback.message.html_text}\n\n"
                f"✅ <b>Holat: TASDIQLANDI</b>\n"
                f"Biriktirildi: {group_data['name']}"
            ),
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n"
            f"✅ <b>Holat: TASDIQLANDI</b>\n"
            f"Biriktirildi: {group_data['name']}",
            parse_mode="HTML",
            reply_markup=None,
        )

    await callback.bot.send_message(
        chat_id=payment_data["user_id"],
        text=(
            "🎉 <b>Tabriklaymiz! Sizning to'lovingiz tasdiqlandi!</b>\n\n"
            f"Siz <b>{group_data['name']}</b> guruhiga biriktirildingiz.\n\n"
            f"Guruhga qo'shilish havolasi (ssilka) 👇\n"
            f"{group_data['telegram_link']}"
        ),
        parse_mode="HTML",
    )

    await notify_superadmins(
        bot=callback.bot,
        actor_id=callback.from_user.id,
        text=(
            "📌 <b>Admin harakati</b>\n\n"
            f"Admin ID: <code>{callback.from_user.id}</code>\n"
            f"Action: <b>payment approved</b>\n"
            f"Payment ID: <code>{payment_id}</code>\n"
            f"Student ID: <code>{payment_data['user_id']}</code>\n"
            f"Group: <b>{h(group_data['name'])}</b>"
        ),
    )


# ==========================================
# 4. TEACHER APPLICATION REJECT
# Superadmin only
# ==========================================

@admin_router.callback_query(AdminTeacherRejectCB.filter())
async def admin_reject_teacher(callback: types.CallbackQuery, callback_data: AdminTeacherRejectCB):
    if not await require_superadmin_callback(callback):
        return

    teacher_id = callback_data.teacher_id

    await update_teacher_status(teacher_id, "rejected_teacher")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="teacher_application_rejected_from_bot",
        entity_type="user",
        entity_id=teacher_id,
        details={
            "teacher_id": teacher_id,
            "new_status": "rejected_teacher",
        },
    )

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n❌ <b>QAROR: RAD ETILDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n❌ <b>QAROR: RAD ETILDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    await callback.bot.send_message(
        chat_id=teacher_id,
        text="❌ Kechirasiz, sizning ustozlik arizangiz ma'muriyat tomonidan tasdiqlanmadi.",
    )


# ==========================================
# 5. TEACHER APPLICATION APPROVE
# Superadmin only
# ==========================================

@admin_router.callback_query(AdminTeacherApproveCB.filter())
async def admin_approve_teacher(callback: types.CallbackQuery, callback_data: AdminTeacherApproveCB):
    if not await require_superadmin_callback(callback):
        return

    teacher_id = callback_data.teacher_id

    await update_teacher_status(teacher_id, "teacher")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="teacher_application_approved_from_bot",
        entity_type="user",
        entity_id=teacher_id,
        details={
            "teacher_id": teacher_id,
            "new_status": "teacher",
        },
    )

    if callback.message.photo or callback.message.document:
        await callback.message.edit_caption(
            caption=f"{callback.message.html_text}\n\n✅ <b>QAROR: QABUL QILINDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )
    else:
        await callback.message.edit_text(
            f"{callback.message.html_text}\n\n✅ <b>QAROR: QABUL QILINDI</b>",
            parse_mode="HTML",
            reply_markup=None,
        )

    await callback.bot.send_message(
        chat_id=teacher_id,
        text=(
            "🎉 <b>Tabriklaymiz! Siz ishga qabul qilindingiz.</b>\n\n"
            "Sizga Ustoz maqomi berildi. Iltimos, /start buyrug'ini bosib o'z ish panelingizga kiring."
        ),
        parse_mode="HTML",
    )


# ==========================================
# 6. STATISTICS
# Admin + Superadmin
# ==========================================

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


# ==========================================
# 7. CREATE GROUP
# Superadmin only
# ==========================================

@admin_router.message(F.text == "➕ Guruh yaratish")
async def start_create_group(message: types.Message, state: FSMContext):
    if not await require_superadmin_message(message, state):
        return

    await message.answer(
        "📝 Yangi guruh nomini kiriting:\n<i>(Masalan: IELTS - N1 yoki Dasturlash - 1)</i>",
        parse_mode="HTML",
        reply_markup=types.ReplyKeyboardRemove(),
    )

    await state.set_state(CreateGroup.name)


@admin_router.message(CreateGroup.name)
async def cg_name(message: types.Message, state: FSMContext):
    if not await require_superadmin_message(message, state):
        return

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
    if not await require_superadmin_callback(callback):
        await state.clear()
        return

    lang = callback.data.split("_", 1)[1]
    await state.update_data(language=lang)

    await callback.message.edit_text(f"Til tanlandi: {h(lang)} ✅")
    await callback.message.answer(
        "👥 Guruh sig'imi (Limit) qancha bo'ladi? Faqat raqam yozing:\n<i>(Masalan: 15)</i>",
        parse_mode="HTML",
    )

    await state.set_state(CreateGroup.capacity)


@admin_router.message(CreateGroup.capacity)
async def cg_capacity(message: types.Message, state: FSMContext):
    if not await require_superadmin_message(message, state):
        return

    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam kiriting!")
        return

    await state.update_data(capacity=int(message.text))

    await message.answer(
        "🔗 Telegram guruh/kanal havolasini (ssilkasini) yuboring:\n"
        "<i>(Masalan: https://t.me/+AbCdEf...)</i>",
        parse_mode="HTML",
    )

    await state.set_state(CreateGroup.link)


@admin_router.message(CreateGroup.link)
async def cg_link(message: types.Message, state: FSMContext):
    if not await require_superadmin_message(message, state):
        return

    await state.update_data(link=message.text)

    teachers = await get_all_teachers()

    if not teachers:
        await message.answer(
            "⚠️ Bazada tasdiqlangan ustozlar yo'q! Guruh ochish uchun avval ustoz ishga qabul qiling.",
            reply_markup=superadmin_menu_keyboard(),
        )
        await state.clear()
        return

    builder = InlineKeyboardBuilder()

    for t in teachers:
        builder.button(
            text=f"{t['full_name']} ({t['teach_lang']})",
            callback_data=AssignTeacherCB(teacher_id=t["telegram_id"]),
        )

    builder.adjust(1)

    await message.answer("👨‍🏫 Bu guruhga qaysi ustozni biriktiramiz?", reply_markup=builder.as_markup())
    await state.set_state(CreateGroup.teacher)


@admin_router.callback_query(CreateGroup.teacher, AssignTeacherCB.filter())
async def cg_teacher(callback: types.CallbackQuery, callback_data: AssignTeacherCB, state: FSMContext):
    if not await require_superadmin_callback(callback):
        await state.clear()
        return

    data = await state.get_data()
    teacher_id = callback_data.teacher_id

    await create_new_group(
        data["name"],
        data["language"],
        data["capacity"],
        data["link"],
        teacher_id,
    )

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="group_created_from_bot",
        entity_type="group",
        entity_id=None,
        details={
            "name": data["name"],
            "language": data["language"],
            "capacity": data["capacity"],
            "link": data["link"],
            "teacher_id": teacher_id,
        },
    )

    await callback.message.delete()
    await callback.message.answer(
        f"✅ <b>{h(data['name'])}</b> guruhi muvaffaqiyatli yaratildi va ustozga biriktirildi!",
        parse_mode="HTML",
        reply_markup=superadmin_menu_keyboard(),
    )

    await state.clear()


# ==========================================
# 8. GROUP MANAGEMENT
# Superadmin only
# ==========================================

@admin_router.message(F.text == "📚 Guruhlar ro'yxati")
async def list_groups_for_admin(message: types.Message):
    if not await require_superadmin_message(message):
        return

    groups = await get_all_groups()

    if not groups:
        await message.answer("Guruhlar mavjud emas.")
        return

    builder = InlineKeyboardBuilder()

    for g in groups:
        builder.button(
            text=g["name"],
            callback_data=AdminGroupCB(payment_id=0, group_id=g["id"]),
        )

    builder.adjust(1)

    await message.answer("Tahrirlamoqchi bo'lgan guruhni tanlang:", reply_markup=builder.as_markup())


@admin_router.callback_query(AdminGroupCB.filter(F.payment_id == 0))
async def manage_group_options(callback: types.CallbackQuery, callback_data: AdminGroupCB):
    if not await require_superadmin_callback(callback):
        return

    group_id = callback_data.group_id

    builder = InlineKeyboardBuilder()
    builder.button(text="👥 O'quvchilarni ko‘rish", callback_data=f"sa_gs_{group_id}")
    builder.button(text="🔄 Ustozni almashtirish", callback_data=f"ch_tch_{group_id}")
    builder.button(text="❌ Guruhni o'chirish", callback_data=f"del_grp_{group_id}")
    builder.adjust(1)

    await callback.message.edit_text("Guruh bilan nima qilamiz?", reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith("ch_tch_"))
async def change_teacher_start(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    group_id = int(callback.data.split("_")[2])
    teachers = await get_all_teachers()

    if not teachers:
        await callback.answer("Bazada tasdiqlangan ustozlar yo'q.", show_alert=True)
        return

    builder = InlineKeyboardBuilder()

    for t in teachers:
        builder.button(
            text=t["full_name"],
            callback_data=f"set_new_t_{group_id}_{t['telegram_id']}",
        )

    builder.adjust(1)

    await callback.message.edit_text("Yangi ustozni tanlang:", reply_markup=builder.as_markup())


@admin_router.callback_query(F.data.startswith("set_new_t_"))
async def set_new_teacher(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    parts = callback.data.split("_")
    group_id = int(parts[3])
    teacher_id = int(parts[4])

    await change_group_teacher(group_id, teacher_id)

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="group_teacher_changed_from_bot",
        entity_type="group",
        entity_id=group_id,
        details={
            "group_id": group_id,
            "new_teacher_id": teacher_id,
        },
    )

    await callback.message.edit_text("✅ Ustoz muvaffaqiyatli almashtirildi!")


@admin_router.callback_query(F.data.startswith("del_grp_"))
async def delete_group_handler(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    group_id = int(callback.data.split("_")[2])

    await delete_group(group_id)

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="group_deleted_from_bot",
        entity_type="group",
        entity_id=group_id,
        details={
            "group_id": group_id,
        },
    )

    await callback.message.edit_text("✅ Guruh muvaffaqiyatli o‘chirildi.")


# ==========================================
# 9. KICK REQUEST APPROVE
# Superadmin only
# ==========================================

@admin_router.callback_query(KickApproveCB.filter())
async def approve_kick_request(callback: types.CallbackQuery, callback_data: KickApproveCB):
    if not await require_superadmin_callback(callback):
        return

    request_id = callback_data.request_id
    request = await get_kick_request(request_id)

    if not request:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    if request["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await remove_student_from_group(request["user_id"], request["group_id"])
    await update_kick_request_status(request_id, "approved")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="kick_request_approved_from_bot",
        entity_type="kick_request",
        entity_id=request_id,
        details={
            "request_id": request_id,
            "student_id": request["user_id"],
            "group_id": request["group_id"],
            "teacher_id": request["teacher_id"],
        },
    )

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n"
        f"✅ <b>QAROR: CHETLATISH TASDIQLANDI</b>",
        parse_mode="HTML",
        reply_markup=None,
    )

    await callback.bot.send_message(
        chat_id=request["teacher_id"],
        text=(
            f"✅ Siz yuborgan chetlatish so'rovi tasdiqlandi.\n\n"
            f"👤 O'quvchi: {request['student_name']}\n"
            f"📚 Guruh: {request['group_name']}"
        ),
    )

    await callback.bot.send_message(
        chat_id=request["user_id"],
        text=(
            f"❌ Siz <b>{h(request['group_name'])}</b> guruhidan chetlatildingiz.\n\n"
            f"Sabab va batafsil ma'lumot uchun ma'muriyat bilan bog'laning."
        ),
        parse_mode="HTML",
    )


# ==========================================
# 10. KICK REQUEST REJECT
# Superadmin only
# ==========================================

@admin_router.callback_query(KickRejectCB.filter())
async def reject_kick_request(callback: types.CallbackQuery, callback_data: KickRejectCB):
    if not await require_superadmin_callback(callback):
        return

    request_id = callback_data.request_id
    request = await get_kick_request(request_id)

    if not request:
        await callback.answer("So'rov topilmadi.", show_alert=True)
        return

    if request["status"] != "pending":
        await callback.answer("Bu so'rov allaqachon ko'rib chiqilgan.", show_alert=True)
        return

    await update_kick_request_status(request_id, "rejected")

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="kick_request_rejected_from_bot",
        entity_type="kick_request",
        entity_id=request_id,
        details={
            "request_id": request_id,
            "student_id": request["user_id"],
            "group_id": request["group_id"],
            "teacher_id": request["teacher_id"],
        },
    )

    await callback.message.edit_text(
        f"{callback.message.html_text}\n\n"
        f"❌ <b>QAROR: RAD ETILDI</b>",
        parse_mode="HTML",
        reply_markup=None,
    )

    await callback.bot.send_message(
        chat_id=request["teacher_id"],
        text=(
            f"❌ Siz yuborgan chetlatish so'rovi admin tomonidan rad etildi.\n\n"
            f"👤 O'quvchi: {request['student_name']}\n"
            f"📚 Guruh: {request['group_name']}"
        ),
    )


# ==========================================
# 11. ADMIN MANAGEMENT
# Superadmin only
# ==========================================

@admin_router.message(F.text == "👨‍💻 Adminlarni boshqarish")
async def manage_admins_menu(message: types.Message):
    if not await require_superadmin_message(message):
        return

    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Admin qo‘shish", callback_data="sa_add_admin")
    builder.button(text="📋 Adminlar ro‘yxati", callback_data="sa_admin_list")
    builder.adjust(1)

    await message.answer(
        "👨‍💻 <b>Adminlarni boshqarish</b>\n\n"
        "Bu bo‘limda yangi admin qo‘shish yoki mavjud adminni olib tashlash mumkin.",
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(F.data == "sa_add_admin")
async def start_add_admin(callback: types.CallbackQuery, state: FSMContext):
    if not await require_superadmin_callback(callback):
        return

    await callback.message.edit_text(
        "➕ <b>Yangi admin qo‘shish</b>\n\n"
        "Admin qilmoqchi bo‘lgan odamning Telegram ID raqamini yuboring.\n\n"
        "Masalan:\n"
        "<code>123456789</code>",
        parse_mode="HTML"
    )

    await state.set_state(AddAdminState.telegram_id)


@admin_router.message(AddAdminState.telegram_id)
async def process_admin_telegram_id(message: types.Message, state: FSMContext):
    if not await require_superadmin_message(message, state):
        return

    if not message.text.isdigit():
        await message.answer("Iltimos, faqat raqam yuboring. Masalan: 123456789")
        return

    await state.update_data(telegram_id=int(message.text))

    await message.answer(
        "Adminning ismini kiriting.\n\n"
        "Agar ismini bilmasangiz, `-` yuboring."
    )

    await state.set_state(AddAdminState.full_name)


@admin_router.message(AddAdminState.full_name)
async def process_admin_full_name(message: types.Message, state: FSMContext):
    if not await require_superadmin_message(message, state):
        return

    data = await state.get_data()
    telegram_id = data["telegram_id"]

    full_name = message.text.strip()
    if full_name == "-":
        full_name = None

    await upsert_admin_user(telegram_id, full_name)

    await log_admin_action(
        admin_id=message.from_user.id,
        action="admin_added_from_bot",
        entity_type="user",
        entity_id=telegram_id,
        details={
            "new_admin_id": telegram_id,
            "full_name": full_name
        },
    )

    try:
        await message.bot.send_message(
            chat_id=telegram_id,
            text=(
                "🎉 <b>Sizga Admin huquqi berildi.</b>\n\n"
                "Iltimos, /start bosib admin panelga kiring."
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await message.answer(
        "✅ Admin muvaffaqiyatli qo‘shildi.\n\n"
        f"Telegram ID: <code>{telegram_id}</code>",
        parse_mode="HTML",
        reply_markup=superadmin_menu_keyboard()
    )

    await state.clear()


@admin_router.callback_query(F.data == "sa_admin_list")
async def show_admins_list(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    admins = await get_api_superadmin_admins()

    if not admins:
        await callback.message.edit_text("Adminlar topilmadi.")
        return

    text = "📋 <b>Adminlar ro‘yxati:</b>\n\n"
    builder = InlineKeyboardBuilder()

    for admin in admins:
        telegram_id = admin["telegram_id"]
        full_name = admin["full_name"] or "Ism yo‘q"
        role = admin["role"]

        text += (
            f"👤 <b>{h(full_name)}</b>\n"
            f"🆔 <code>{telegram_id}</code>\n"
            f"🔐 Role: <b>{h(role)}</b>\n\n"
        )

        if role == "admin":
            builder.button(
                text=f"❌ {full_name} adminlikdan olish",
                callback_data=RemoveAdminCB(telegram_id=telegram_id)
            )

    builder.adjust(1)

    await callback.message.edit_text(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(RemoveAdminCB.filter())
async def remove_admin_handler(callback: types.CallbackQuery, callback_data: RemoveAdminCB):
    if not await require_superadmin_callback(callback):
        return

    telegram_id = callback_data.telegram_id

    if telegram_id == callback.from_user.id:
        await callback.answer("O‘zingizni adminlikdan olib tashlay olmaysiz.", show_alert=True)
        return

    role = await get_user_role(telegram_id)

    if role == "superadmin":
        await callback.answer("Superadminni bu yerdan olib tashlab bo‘lmaydi.", show_alert=True)
        return

    if role != "admin":
        await callback.answer("Bu foydalanuvchi admin emas.", show_alert=True)
        return

    await remove_admin_role(telegram_id)

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="admin_removed_from_bot",
        entity_type="user",
        entity_id=telegram_id,
        details={
            "removed_admin_id": telegram_id
        },
    )

    try:
        await callback.bot.send_message(
            chat_id=telegram_id,
            text=(
                "⚠️ <b>Sizning Admin huquqingiz olib tashlandi.</b>\n\n"
                "Endi siz oddiy foydalanuvchi sifatida ko‘rinasiz."
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.message.edit_text(
        "✅ Admin huquqi olib tashlandi.\n\n"
        f"Telegram ID: <code>{telegram_id}</code>",
        parse_mode="HTML"
    )


# ==========================================
# 12. SUPERADMIN VIEW: ADMIN ACTIONS
# Superadmin only
# ==========================================

@admin_router.message(F.text == "📌 Admin harakatlari")
async def show_admin_actions(message: types.Message):
    if not await require_superadmin_message(message):
        return

    actions = await get_api_superadmin_admin_actions(limit=30, offset=0)

    if not actions:
        await message.answer("📌 Hali admin harakatlari mavjud emas.")
        return

    text = "📌 <b>Oxirgi admin harakatlari:</b>\n\n"

    for item in actions:
        admin_name = item["admin_name"] or "Noma'lum admin"
        created_at = item["created_at"].strftime("%d.%m.%Y %H:%M") if item["created_at"] else "-"

        text += (
            f"🆔 <b>Action ID:</b> {item['id']}\n"
            f"👤 <b>Admin:</b> {h(admin_name)}\n"
            f"🔐 <b>Admin ID:</b> <code>{item['admin_id']}</code>\n"
            f"⚙️ <b>Action:</b> <code>{h(item['action'])}</code>\n"
            f"📦 <b>Entity:</b> {h(item['entity_type'])} / {h(item['entity_id'])}\n"
            f"🕒 <b>Vaqt:</b> {created_at}\n\n"
        )

    await message.answer(text[:3900], parse_mode="HTML")


# ==========================================
# 13. SUPERADMIN VIEW: TEACHERS
# Superadmin only
# ==========================================

@admin_router.message(F.text == "👨‍🏫 Ustozlarni ko‘rish")
async def show_teachers_overview(message: types.Message):
    if not await require_superadmin_message(message):
        return

    teachers = await get_api_superadmin_teachers_overview()

    if not teachers:
        await message.answer("👨‍🏫 Hali tasdiqlangan ustozlar yo‘q.")
        return

    text = "👨‍🏫 <b>Ustozlar ro‘yxati:</b>\n\n"
    builder = InlineKeyboardBuilder()

    for teacher in teachers:
        teacher_id = teacher["telegram_id"]
        full_name = teacher["full_name"] or "Ism yo‘q"

        text += (
            f"👤 <b>{h(full_name)}</b>\n"
            f"🆔 <code>{teacher_id}</code>\n"
            f"📞 {h(teacher['phone'])}\n"
            f"📚 Fan: {h(teacher['teach_lang'])}\n"
            f"👥 Guruhlar: <b>{teacher['groups_count']}</b>\n"
            f"👨‍🎓 O‘quvchilar: <b>{teacher['students_count']}</b>\n\n"
        )

        builder.button(
            text=f"📚 {full_name} guruhlari",
            callback_data=f"sa_tg_{teacher_id}"
        )

    builder.adjust(1)

    await message.answer(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(F.data.startswith("sa_tg_"))
async def show_teacher_groups(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    teacher_id = int(callback.data.split("_")[2])
    groups = await get_api_superadmin_teacher_groups(teacher_id)

    if not groups:
        await callback.message.edit_text("Bu ustozga hali faol guruh biriktirilmagan.")
        return

    text = f"📚 <b>Ustoz guruhlari</b>\n🆔 Teacher ID: <code>{teacher_id}</code>\n\n"
    builder = InlineKeyboardBuilder()

    for group in groups:
        text += (
            f"📚 <b>{h(group['name'])}</b>\n"
            f"Til/Fan: {h(group['language'])}\n"
            f"Sig‘im: <b>{group['current_count']}/{group['max_capacity']}</b>\n"
            f"Link: {h(group['telegram_link'])}\n\n"
        )

        builder.button(
            text=f"👥 {group['name']} o‘quvchilari",
            callback_data=f"sa_gs_{group['id']}"
        )

    builder.adjust(1)

    await callback.message.edit_text(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 14. SUPERADMIN VIEW: GROUP STUDENTS
# Superadmin only
# ==========================================

@admin_router.callback_query(F.data.startswith("sa_gs_"))
async def show_group_students(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    group_id = int(callback.data.split("_")[2])
    students = await get_api_superadmin_group_students(group_id)

    if not students:
        await callback.message.edit_text("Bu guruhda hozircha o‘quvchilar yo‘q.")
        return

    text = f"👥 <b>Guruh o‘quvchilari</b>\n🆔 Group ID: <code>{group_id}</code>\n\n"
    builder = InlineKeyboardBuilder()

    for student in students:
        student_id = student["telegram_id"]
        full_name = student["full_name"] or "Ism yo‘q"
        joined_at = student["joined_at"].strftime("%d.%m.%Y") if student["joined_at"] else "-"

        text += (
            f"👤 <b>{h(full_name)}</b>\n"
            f"🆔 <code>{student_id}</code>\n"
            f"📞 {h(student['phone'])}\n"
            f"📍 {h(student['region'])}\n"
            f"📅 Yosh: {h(student['age'])}\n"
            f"➕ Qo‘shilgan: {joined_at}\n\n"
        )

        builder.button(
            text=f"📊 {full_name} baholari",
            callback_data=f"sa_sr_{student_id}"
        )

    builder.adjust(1)

    await callback.message.edit_text(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


# ==========================================
# 15. SUPERADMIN VIEW: STUDENTS
# Superadmin only
# ==========================================

@admin_router.message(F.text == "👨‍🎓 O‘quvchilarni ko‘rish")
async def show_students_overview(message: types.Message):
    if not await require_superadmin_message(message):
        return

    students = await get_api_superadmin_students_overview(limit=30, offset=0)

    if not students:
        await message.answer("👨‍🎓 Hali o‘quvchilar yo‘q.")
        return

    text = "👨‍🎓 <b>Oxirgi o‘quvchilar:</b>\n\n"
    builder = InlineKeyboardBuilder()

    for student in students:
        student_id = student["telegram_id"]
        full_name = student["full_name"] or "Ism yo‘q"

        text += (
            f"👤 <b>{h(full_name)}</b>\n"
            f"🆔 <code>{student_id}</code>\n"
            f"📞 {h(student['phone'])}\n"
            f"📍 {h(student['region'])}\n"
            f"👥 Guruhlar: <b>{student['groups_count']}</b>\n"
            f"📊 Baholar: <b>{student['results_count']}</b>\n\n"
        )

        builder.button(
            text=f"📊 {full_name} baholari",
            callback_data=f"sa_sr_{student_id}"
        )

    builder.adjust(1)

    await message.answer(
        text[:3900],
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )


@admin_router.callback_query(F.data.startswith("sa_sr_"))
async def show_student_results(callback: types.CallbackQuery):
    if not await require_superadmin_callback(callback):
        return

    student_id = int(callback.data.split("_")[2])
    results = await get_api_superadmin_student_results(student_id)

    if not results:
        await callback.message.edit_text("Bu o‘quvchiga hali baho/natija kiritilmagan.")
        return

    text = f"📊 <b>O‘quvchi baholari</b>\n🆔 Student ID: <code>{student_id}</code>\n\n"

    for result in results:
        created_at = result["created_at"].strftime("%d.%m.%Y") if result["created_at"] else "-"

        text += (
            f"📝 <b>{h(result['result_title'])}</b>\n"
            f"📊 Ball: <b>{h(result['score'])}</b>\n"
            f"📚 Guruh: {h(result['group_name'])}\n"
            f"👨‍🏫 Ustoz: {h(result['teacher_name'])}\n"
            f"💬 Izoh: {h(result['comment'])}\n"
            f"🕒 Sana: {created_at}\n\n"
        )

    await callback.message.edit_text(text[:3900], parse_mode="HTML")


# ==========================================
# 16. SUPERADMIN VIEW: ALL RESULTS
# Superadmin only
# ==========================================

@admin_router.message(F.text == "📊 Barcha natijalar")
async def show_all_results(message: types.Message):
    if not await require_superadmin_message(message):
        return

    results = await get_api_superadmin_all_results(limit=40, offset=0)

    if not results:
        await message.answer("📊 Hali hech qanday natija kiritilmagan.")
        return

    text = "📊 <b>Oxirgi barcha natijalar:</b>\n\n"

    for result in results:
        created_at = result["created_at"].strftime("%d.%m.%Y") if result["created_at"] else "-"

        text += (
            f"👨‍🎓 <b>{h(result['student_name'])}</b>\n"
            f"📝 {h(result['result_title'])}: <b>{h(result['score'])}</b>\n"
            f"📚 Guruh: {h(result['group_name'])}\n"
            f"👨‍🏫 Ustoz: {h(result['teacher_name'])}\n"
            f"🕒 Sana: {created_at}\n\n"
        )

    await message.answer(text[:3900], parse_mode="HTML")