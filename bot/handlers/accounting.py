# handlers/accounting.py
import os
from html import escape

from aiogram import Router, types, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import BaseFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.db import (
    get_user_role,
    get_user_interface_lang,
    get_accounting_payment_stats,
    get_accounting_payments,
    get_accounting_payment_detail,
    get_active_groups,
    get_group_link,
    add_student_to_group_if_capacity,
    approve_payment_with_actor,
    reject_payment_with_actor,
    log_admin_action,
)
from utils.i18n import all_texts
from utils.states import (
    AccountingListCB,
    AccountingPaymentCB,
    AccountingAssignGroupCB,
    AccountingRejectState,
    AdminApproveCB,
    AdminRejectCB,
)

accounting_router = Router()


# ==========================================
# LOCAL TEXTS
# ==========================================

LOCAL_TEXTS = {
    "no_access": {
        "uz": "⛔ Bu bo‘lim faqat buxgalteriya/admin/superadmin uchun.",
        "ru": "⛔ Этот раздел только для бухгалтерии/admin/superadmin.",
        "en": "⛔ This section is only for accountant/admin/superadmin.",
    },
    "panel_title": {
        "uz": "💰 <b>Buxgalteriya paneli</b>\n\nTo‘lovlar bilan ishlash bo‘limi.",
        "ru": "💰 <b>Бухгалтерия</b>\n\nРаздел для работы с оплатами.",
        "en": "💰 <b>Accounting panel</b>\n\nPayment management section.",
    },
    "stats": {
        "uz": "📊 <b>Statistika:</b>\nJami: <b>{total}</b>\nKutilmoqda: <b>{pending}</b>\nTasdiqlangan: <b>{approved}</b>\nRad etilgan: <b>{rejected}</b>\n\n💵 Naqd kutilmoqda: <b>{cash_pending}</b>\n💳 Karta kutilmoqda: <b>{card_pending}</b>",
        "ru": "📊 <b>Статистика:</b>\nВсего: <b>{total}</b>\nОжидает: <b>{pending}</b>\nПодтверждено: <b>{approved}</b>\nОтклонено: <b>{rejected}</b>\n\n💵 Наличные ожидают: <b>{cash_pending}</b>\n💳 Карта ожидает: <b>{card_pending}</b>",
        "en": "📊 <b>Statistics:</b>\nTotal: <b>{total}</b>\nPending: <b>{pending}</b>\nApproved: <b>{approved}</b>\nRejected: <b>{rejected}</b>\n\n💵 Cash pending: <b>{cash_pending}</b>\n💳 Card pending: <b>{card_pending}</b>",
    },
    "pending_all": {
        "uz": "⏳ Kutilayotgan to‘lovlar",
        "ru": "⏳ Ожидающие оплаты",
        "en": "⏳ Pending payments",
    },
    "pending_cash": {
        "uz": "💵 Naqd kutilmoqda",
        "ru": "💵 Наличные ожидают",
        "en": "💵 Cash pending",
    },
    "pending_card": {
        "uz": "💳 Karta kutilmoqda",
        "ru": "💳 Карта ожидает",
        "en": "💳 Card pending",
    },
    "approved": {
        "uz": "✅ Tasdiqlangan",
        "ru": "✅ Подтверждено",
        "en": "✅ Approved",
    },
    "rejected": {
        "uz": "❌ Rad etilgan",
        "ru": "❌ Отклонено",
        "en": "❌ Rejected",
    },
    "back_panel": {
        "uz": "🔙 Buxgalteriya paneli",
        "ru": "🔙 Бухгалтерия",
        "en": "🔙 Accounting panel",
    },
    "list_title": {
        "uz": "💰 <b>To‘lovlar ro‘yxati</b>\n\nStatus: <b>{status}</b>\nTo‘lov turi: <b>{method}</b>\nSahifa: <b>{page}</b>\n\nTo‘lov detailini ko‘rish uchun tanlang:",
        "ru": "💰 <b>Список оплат</b>\n\nСтатус: <b>{status}</b>\nМетод: <b>{method}</b>\nСтраница: <b>{page}</b>\n\nВыберите оплату для просмотра:",
        "en": "💰 <b>Payment list</b>\n\nStatus: <b>{status}</b>\nMethod: <b>{method}</b>\nPage: <b>{page}</b>\n\nChoose a payment to view details:",
    },
    "empty_list": {
        "uz": "Bu bo‘yicha to‘lovlar topilmadi.",
        "ru": "Оплаты по этому фильтру не найдены.",
        "en": "No payments found for this filter.",
    },
    "prev": {
        "uz": "⬅️ Oldingi",
        "ru": "⬅️ Назад",
        "en": "⬅️ Previous",
    },
    "next": {
        "uz": "Keyingi ➡️",
        "ru": "Далее ➡️",
        "en": "Next ➡️",
    },
    "payment_not_found": {
        "uz": "To‘lov topilmadi.",
        "ru": "Оплата не найдена.",
        "en": "Payment not found.",
    },
    "detail_title": {
        "uz": "💰 <b>To‘lov ma’lumotlari</b>",
        "ru": "💰 <b>Детали оплаты</b>",
        "en": "💰 <b>Payment detail</b>",
    },
    "approve": {
        "uz": "✅ Tasdiqlash",
        "ru": "✅ Подтвердить",
        "en": "✅ Approve",
    },
    "reject": {
        "uz": "❌ Rad etish",
        "ru": "❌ Отклонить",
        "en": "❌ Reject",
    },
    "receipt": {
        "uz": "📎 Chekni ko‘rish",
        "ru": "📎 Посмотреть чек",
        "en": "📎 View receipt",
    },
    "already_processed": {
        "uz": "Bu to‘lov allaqachon ko‘rib chiqilgan.",
        "ru": "Эта оплата уже обработана.",
        "en": "This payment has already been processed.",
    },
    "choose_group": {
        "uz": "✅ To‘lovni tasdiqlash uchun o‘quvchini qaysi guruhga qo‘shamiz?",
        "ru": "✅ Для подтверждения оплаты выберите группу для студента.",
        "en": "✅ To approve payment, choose the group for the student.",
    },
    "no_groups": {
        "uz": "Faol guruhlar topilmadi. Avval guruh yarating.",
        "ru": "Активные группы не найдены. Сначала создайте группу.",
        "en": "No active groups found. Please create a group first.",
    },
    "approved_done": {
        "uz": "✅ To‘lov tasdiqlandi.\n\nPayment ID: <code>{payment_id}</code>\nO‘quvchi: <b>{student_name}</b>\nGuruh: <b>{group_name}</b>",
        "ru": "✅ Оплата подтверждена.\n\nPayment ID: <code>{payment_id}</code>\nСтудент: <b>{student_name}</b>\nГруппа: <b>{group_name}</b>",
        "en": "✅ Payment approved.\n\nPayment ID: <code>{payment_id}</code>\nStudent: <b>{student_name}</b>\nGroup: <b>{group_name}</b>",
    },
    "student_approved": {
        "uz": "🎉 <b>Tabriklaymiz! Sizning to‘lovingiz tasdiqlandi.</b>\n\nSiz <b>{group_name}</b> guruhiga biriktirildingiz.\n\nGuruhga qo‘shilish havolasi 👇\n{group_link}",
        "ru": "🎉 <b>Поздравляем! Ваша оплата подтверждена.</b>\n\nВы добавлены в группу <b>{group_name}</b>.\n\nСсылка для вступления 👇\n{group_link}",
        "en": "🎉 <b>Congratulations! Your payment has been approved.</b>\n\nYou have been assigned to <b>{group_name}</b>.\n\nGroup invitation link 👇\n{group_link}",
    },
    "reject_reason": {
        "uz": "❌ Rad etish sababini yozing.\n\nMasalan: chek noaniq, summa tushmagan, noto‘g‘ri chek.",
        "ru": "❌ Напишите причину отказа.\n\nНапример: чек неясный, сумма не поступила, неверный чек.",
        "en": "❌ Write the rejection reason.\n\nExample: unclear receipt, payment not received, wrong receipt.",
    },
    "rejected_done": {
        "uz": "❌ To‘lov rad etildi.\n\nPayment ID: <code>{payment_id}</code>\nSabab: {reason}",
        "ru": "❌ Оплата отклонена.\n\nPayment ID: <code>{payment_id}</code>\nПричина: {reason}",
        "en": "❌ Payment rejected.\n\nPayment ID: <code>{payment_id}</code>\nReason: {reason}",
    },
    "student_rejected": {
        "uz": "❌ Sizning to‘lovingiz tasdiqlanmadi.\n\nSabab: {reason}\n\nQaytadan to‘lov qilish uchun 📚 Kurslar bo‘limidan foydalaning.",
        "ru": "❌ Ваша оплата не подтверждена.\n\nПричина: {reason}\n\nЧтобы повторить оплату, используйте раздел 📚 Курсы.",
        "en": "❌ Your payment was not approved.\n\nReason: {reason}\n\nTo pay again, please use the 📚 Courses section.",
    },
    "receipt_not_found": {
        "uz": "Chek fayli topilmadi yoki bu naqd to‘lov.",
        "ru": "Файл чека не найден или это оплата наличными.",
        "en": "Receipt file was not found or this is a cash payment.",
    },
}


def at(key: str, lang: str = "uz", **kwargs) -> str:
    item = LOCAL_TEXTS.get(key, {})
    text = item.get(lang) or item.get("uz") or key
    return text.format(**kwargs)


def h(value):
    if value is None:
        return "-"
    return escape(str(value))


def rv(record, key: str, default=None):
    if not record:
        return default
    try:
        if key in record.keys():
            return record[key]
    except Exception:
        pass
    return default


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


async def safe_edit_text(message: types.Message, text: str, **kwargs):
    """
    Text message bo'lsa edit_text qiladi.
    Photo/document captionli message bo'lsa edit_caption qiladi.
    Agar edit qilib bo'lmasa, yangi message yuboradi.
    """
    try:
        await message.edit_text(text, **kwargs)
        return
    except TelegramBadRequest as e:
        error_text = str(e).lower()

        if "message is not modified" in error_text:
            return

        if "there is no text in the message to edit" in error_text:
            try:
                await message.edit_caption(caption=text, **kwargs)
                return
            except TelegramBadRequest as caption_error:
                caption_error_text = str(caption_error).lower()

                if "message is not modified" in caption_error_text:
                    return

                await message.answer(text, **kwargs)
                return

        raise


def status_to_db(status: str):
    return None if status == "all" else status


def method_to_db(method: str):
    return None if method == "all" else method


def status_label(status: str, lang: str = "uz") -> str:
    labels = {
        "pending": {
            "uz": "kutilmoqda",
            "ru": "ожидает",
            "en": "pending",
        },
        "approved": {
            "uz": "tasdiqlangan",
            "ru": "подтверждено",
            "en": "approved",
        },
        "rejected": {
            "uz": "rad etilgan",
            "ru": "отклонено",
            "en": "rejected",
        },
        "all": {
            "uz": "hammasi",
            "ru": "все",
            "en": "all",
        },
    }
    return labels.get(status, {}).get(lang) or labels.get(status, {}).get("uz") or status


def method_label(method: str, lang: str = "uz") -> str:
    labels = {
        "cash": {
            "uz": "naqd",
            "ru": "наличные",
            "en": "cash",
        },
        "card": {
            "uz": "karta",
            "ru": "карта",
            "en": "card",
        },
        "all": {
            "uz": "hammasi",
            "ru": "все",
            "en": "all",
        },
    }
    return labels.get(method, {}).get(lang) or labels.get(method, {}).get("uz") or method


# ==========================================
# ACCESS FILTER
# ==========================================

class AccountingOnly(BaseFilter):
    async def __call__(self, event) -> bool:
        if not getattr(event, "from_user", None):
            return False

        role = await get_user_role(event.from_user.id)
        return role in ["accountant", "admin", "superadmin"]


accounting_router.message.filter(AccountingOnly())
accounting_router.callback_query.filter(AccountingOnly())


# ==========================================
# KEYBOARDS
# ==========================================

def accounting_panel_keyboard(lang: str = "uz"):
    builder = InlineKeyboardBuilder()

    builder.button(
        text=at("pending_all", lang),
        callback_data=AccountingListCB(status="pending", method="all", page=1)
    )
    builder.button(
        text=at("pending_cash", lang),
        callback_data=AccountingListCB(status="pending", method="cash", page=1)
    )
    builder.button(
        text=at("pending_card", lang),
        callback_data=AccountingListCB(status="pending", method="card", page=1)
    )
    builder.button(
        text=at("approved", lang),
        callback_data=AccountingListCB(status="approved", method="all", page=1)
    )
    builder.button(
        text=at("rejected", lang),
        callback_data=AccountingListCB(status="rejected", method="all", page=1)
    )

    builder.adjust(1)
    return builder.as_markup()


async def render_accounting_panel(message: types.Message, user_id: int):
    lang = await user_lang(user_id)

    stats = await get_accounting_payment_stats()

    text = (
        f"{at('panel_title', lang)}\n\n"
        f"{at('stats', lang, **dict(stats))}"
    )

    await safe_edit_text(
        message,
        text,
        parse_mode="HTML",
        reply_markup=accounting_panel_keyboard(lang)
    )


def back_to_panel_keyboard(lang: str = "uz"):
    builder = InlineKeyboardBuilder()
    builder.button(
        text=at("back_panel", lang),
        callback_data="acc_panel"
    )
    builder.adjust(1)
    return builder.as_markup()


def payment_detail_keyboard(payment, lang: str = "uz"):
    builder = InlineKeyboardBuilder()

    payment_id = payment["id"]
    status = payment["status"]
    receipt_path = payment["receipt_path"]

    if receipt_path:
        builder.button(
            text=at("receipt", lang),
            callback_data=AccountingPaymentCB(payment_id=payment_id, action="receipt")
        )

    if status == "pending":
        builder.button(
            text=at("approve", lang),
            callback_data=AccountingPaymentCB(payment_id=payment_id, action="approve")
        )
        builder.button(
            text=at("reject", lang),
            callback_data=AccountingPaymentCB(payment_id=payment_id, action="reject")
        )

    builder.button(
        text=at("back_panel", lang),
        callback_data="acc_panel"
    )

    builder.adjust(1, 2, 1)
    return builder.as_markup()


def group_select_keyboard(payment_id: int, groups, lang: str = "uz"):
    builder = InlineKeyboardBuilder()

    for group in groups:
        current_count = rv(group, "current_count", 0)
        max_capacity = rv(group, "max_capacity", "-")

        text = f"{group['name']} — {current_count}/{max_capacity}"
        builder.button(
            text=text,
            callback_data=AccountingAssignGroupCB(
                payment_id=payment_id,
                group_id=group["id"]
            )
        )

    builder.button(
        text=at("back_panel", lang),
        callback_data="acc_panel"
    )

    builder.adjust(1)
    return builder.as_markup()


# ==========================================
# FORMATTERS
# ==========================================

def format_payment_detail(payment, lang: str = "uz"):
    created_at = payment["created_at"].strftime("%d.%m.%Y %H:%M") if payment["created_at"] else "-"
    approved_at = payment["approved_at"].strftime("%d.%m.%Y %H:%M") if payment["approved_at"] else "-"
    rejected_at = payment["rejected_at"].strftime("%d.%m.%Y %H:%M") if payment["rejected_at"] else "-"

    return (
        f"{at('detail_title', lang)}\n\n"
        f"🆔 Payment ID: <code>{payment['id']}</code>\n"
        f"👤 O‘quvchi: <b>{h(payment['student_name'])}</b>\n"
        f"🆔 Student ID: <code>{payment['user_id']}</code>\n"
        f"📞 Telefon: {h(payment['student_phone'])}\n"
        f"📍 Hudud: {h(payment['student_region'])}\n"
        f"📚 Kurs: {h(payment['course_info'])}\n"
        f"💳 To‘lov turi: <b>{h(method_label(payment['payment_method'], lang))}</b>\n"
        f"📌 Status: <b>{h(status_label(payment['status'], lang))}</b>\n"
        f"💰 Summa: {h(payment['amount'])}\n"
        f"📎 Chek: {h(payment['receipt_path'])}\n"
        f"🕒 Yaratilgan: {created_at}\n\n"
        f"✅ Tasdiqlagan: {h(payment['approved_by_name'])}\n"
        f"✅ Tasdiqlangan vaqt: {approved_at}\n"
        f"❌ Rad etgan: {h(payment['rejected_by_name'])}\n"
        f"❌ Rad etilgan vaqt: {rejected_at}\n"
        f"📝 Rad etish sababi: {h(payment['reject_reason'])}"
    )


# ==========================================
# 1. ACCOUNTING PANEL
# ==========================================

@accounting_router.message(F.text.in_(all_texts("accounting_panel")))
async def show_accounting_panel(message: types.Message):
    lang = await user_lang(message.from_user.id)

    stats = await get_accounting_payment_stats()

    text = (
        f"{at('panel_title', lang)}\n\n"
        f"{at('stats', lang, **dict(stats))}"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=accounting_panel_keyboard(lang)
    )


@accounting_router.callback_query(F.data == "acc_panel")
async def back_to_accounting_panel(callback: types.CallbackQuery):
    await render_accounting_panel(callback.message, callback.from_user.id)
    await callback.answer()


# ==========================================
# 2. PAYMENT LIST
# ==========================================

@accounting_router.callback_query(AccountingListCB.filter())
async def show_payment_list(callback: types.CallbackQuery, callback_data: AccountingListCB):
    lang = await user_lang(callback.from_user.id)

    page = max(callback_data.page, 1)
    limit = 10
    offset = (page - 1) * limit

    status = callback_data.status
    method = callback_data.method

    payments = await get_accounting_payments(
        status=status_to_db(status),
        payment_method=method_to_db(method),
        limit=limit,
        offset=offset
    )

    if not payments:
        await safe_edit_text(
            callback.message,
            at("empty_list", lang),
            parse_mode="HTML",
            reply_markup=back_to_panel_keyboard(lang)
        )
        await callback.answer()
        return

    text = at(
        "list_title",
        lang,
        status=status_label(status, lang),
        method=method_label(method, lang),
        page=page
    )

    builder = InlineKeyboardBuilder()

    for payment in payments:
        student_name = payment["student_name"] or str(payment["user_id"])
        method_icon = "💵" if payment["payment_method"] == "cash" else "💳"
        status_icon = {
            "pending": "⏳",
            "approved": "✅",
            "rejected": "❌",
        }.get(payment["status"], "📌")

        button_text = (
            f"{status_icon} #{payment['id']} {method_icon} "
            f"{student_name[:22]}"
        )

        builder.button(
            text=button_text,
            callback_data=AccountingPaymentCB(
                payment_id=payment["id"],
                action="detail"
            )
        )

    if page > 1:
        builder.button(
            text=at("prev", lang),
            callback_data=AccountingListCB(status=status, method=method, page=page - 1)
        )

    if len(payments) == limit:
        builder.button(
            text=at("next", lang),
            callback_data=AccountingListCB(status=status, method=method, page=page + 1)
        )

    builder.button(
        text=at("back_panel", lang),
        callback_data="acc_panel"
    )

    builder.adjust(1)

    await safe_edit_text(
        callback.message,
        text,
        parse_mode="HTML",
        reply_markup=builder.as_markup()
    )
    await callback.answer()


# ==========================================
# 3. PAYMENT DETAIL
# ==========================================

@accounting_router.callback_query(AccountingPaymentCB.filter(F.action == "detail"))
async def show_payment_detail(callback: types.CallbackQuery, callback_data: AccountingPaymentCB):
    lang = await user_lang(callback.from_user.id)

    payment = await get_accounting_payment_detail(callback_data.payment_id)

    if not payment:
        await callback.answer(at("payment_not_found", lang), show_alert=True)
        return

    await safe_edit_text(
        callback.message,
        format_payment_detail(payment, lang),
        parse_mode="HTML",
        reply_markup=payment_detail_keyboard(payment, lang)
    )
    await callback.answer()


# ==========================================
# 4. RECEIPT VIEW
# ==========================================

@accounting_router.callback_query(AccountingPaymentCB.filter(F.action == "receipt"))
async def show_payment_receipt(callback: types.CallbackQuery, callback_data: AccountingPaymentCB, bot: Bot):
    lang = await user_lang(callback.from_user.id)

    payment = await get_accounting_payment_detail(callback_data.payment_id)

    if not payment:
        await callback.answer(at("payment_not_found", lang), show_alert=True)
        return

    receipt_path = payment["receipt_path"]

    if not receipt_path or not os.path.exists(receipt_path):
        await callback.answer(at("receipt_not_found", lang), show_alert=True)
        return

    ext = os.path.splitext(receipt_path)[1].lower()
    file = FSInputFile(receipt_path)

    caption = (
        f"📎 <b>To‘lov cheki</b>\n\n"
        f"🆔 Payment ID: <code>{payment['id']}</code>\n"
        f"👤 O‘quvchi: <b>{h(payment['student_name'])}</b>\n"
        f"📚 Kurs: {h(payment['course_info'])}"
    )

    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=file,
            caption=caption,
            parse_mode="HTML"
        )
    else:
        await bot.send_document(
            chat_id=callback.message.chat.id,
            document=file,
            caption=caption,
            parse_mode="HTML"
        )

    await callback.answer()


# ==========================================
# 5. APPROVE START -> GROUP SELECT
# ==========================================

@accounting_router.callback_query(AccountingPaymentCB.filter(F.action == "approve"))
async def approve_payment_start(callback: types.CallbackQuery, callback_data: AccountingPaymentCB):
    lang = await user_lang(callback.from_user.id)

    payment = await get_accounting_payment_detail(callback_data.payment_id)

    if not payment:
        await callback.answer(at("payment_not_found", lang), show_alert=True)
        return

    if payment["status"] != "pending":
        await callback.answer(at("already_processed", lang), show_alert=True)
        return

    groups = await get_active_groups()

    if not groups:
        await callback.answer(at("no_groups", lang), show_alert=True)
        return

    await safe_edit_text(
        callback.message,
        at("choose_group", lang),
        parse_mode="HTML",
        reply_markup=group_select_keyboard(callback_data.payment_id, groups, lang)
    )
    await callback.answer()


# ==========================================
# 6. APPROVE FINAL
# ==========================================

@accounting_router.callback_query(AccountingAssignGroupCB.filter())
async def approve_payment_final(callback: types.CallbackQuery, callback_data: AccountingAssignGroupCB):
    lang = await user_lang(callback.from_user.id)

    payment = await get_accounting_payment_detail(callback_data.payment_id)

    if not payment:
        await callback.answer(at("payment_not_found", lang), show_alert=True)
        return

    if payment["status"] != "pending":
        await callback.answer(at("already_processed", lang), show_alert=True)
        return

    group = await get_group_link(callback_data.group_id)

    if not group:
        await callback.answer(at("no_groups", lang), show_alert=True)
        return

    capacity_result = await add_student_to_group_if_capacity(
        payment["user_id"],
        callback_data.group_id
    )

    if not capacity_result["ok"]:
        await callback.answer(capacity_result["message"], show_alert=True)
        return

    await approve_payment_with_actor(
        payment_id=callback_data.payment_id,
        actor_id=callback.from_user.id
    )

    await log_admin_action(
        admin_id=callback.from_user.id,
        action="payment_approved_from_accounting_panel",
        entity_type="payment",
        entity_id=callback_data.payment_id,
        details={
            "student_id": payment["user_id"],
            "group_id": callback_data.group_id,
            "group_name": group["name"],
            "capacity": capacity_result,
        }
    )

    await safe_edit_text(
        callback.message,
        at(
            "approved_done",
            lang,
            payment_id=callback_data.payment_id,
            student_name=h(payment["student_name"]),
            group_name=h(group["name"])
        ),
        parse_mode="HTML"
    )

    student_lang = await user_lang(payment["user_id"])

    try:
        await callback.bot.send_message(
            chat_id=payment["user_id"],
            text=at(
                "student_approved",
                student_lang,
                group_name=h(group["name"]),
                group_link=group["telegram_link"]
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await callback.answer()


# ==========================================
# 7. REJECT START
# ==========================================

@accounting_router.callback_query(AccountingPaymentCB.filter(F.action == "reject"))
async def reject_payment_start(callback: types.CallbackQuery, callback_data: AccountingPaymentCB, state: FSMContext):
    lang = await user_lang(callback.from_user.id)

    payment = await get_accounting_payment_detail(callback_data.payment_id)

    if not payment:
        await callback.answer(at("payment_not_found", lang), show_alert=True)
        return

    if payment["status"] != "pending":
        await callback.answer(at("already_processed", lang), show_alert=True)
        return

    await state.update_data(payment_id=callback_data.payment_id)

    await safe_edit_text(
        callback.message,
        at("reject_reason", lang),
        parse_mode="HTML"
    )

    await state.set_state(AccountingRejectState.reason)
    await callback.answer()


# ==========================================
# 8. REJECT FINAL
# ==========================================

@accounting_router.message(AccountingRejectState.reason)
async def reject_payment_final(message: types.Message, state: FSMContext):
    lang = await user_lang(message.from_user.id)

    data = await state.get_data()
    payment_id = data.get("payment_id")
    reason = message.text.strip()

    if not payment_id:
        await message.answer(at("payment_not_found", lang))
        await state.clear()
        return

    payment = await get_accounting_payment_detail(payment_id)

    if not payment:
        await message.answer(at("payment_not_found", lang))
        await state.clear()
        return

    if payment["status"] != "pending":
        await message.answer(at("already_processed", lang))
        await state.clear()
        return

    await reject_payment_with_actor(
        payment_id=payment_id,
        actor_id=message.from_user.id,
        reason=reason
    )

    await log_admin_action(
        admin_id=message.from_user.id,
        action="payment_rejected_from_accounting_panel",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment["user_id"],
            "reason": reason,
        }
    )

    await message.answer(
        at("rejected_done", lang, payment_id=payment_id, reason=h(reason)),
        parse_mode="HTML"
    )

    student_lang = await user_lang(payment["user_id"])

    try:
        await message.bot.send_message(
            chat_id=payment["user_id"],
            text=at("student_rejected", student_lang, reason=h(reason)),
            parse_mode="HTML"
        )
    except Exception:
        pass

    await state.clear()

# ==========================================
# LEGACY PAYMENT NOTIFICATION CALLBACKS
# Eski notificationlarda qolgan AdminApproveCB/AdminRejectCB tugmalarini
# yangi accounting flowga yo'naltiramiz.
# ==========================================

@accounting_router.callback_query(AdminApproveCB.filter())
async def legacy_admin_approve_payment(
    callback: types.CallbackQuery,
    callback_data: AdminApproveCB
):
    await approve_payment_start(
        callback,
        AccountingPaymentCB(
            payment_id=callback_data.payment_id,
            action="approve"
        )
    )


@accounting_router.callback_query(AdminRejectCB.filter())
async def legacy_admin_reject_payment(
    callback: types.CallbackQuery,
    callback_data: AdminRejectCB,
    state: FSMContext
):
    await reject_payment_start(
        callback,
        AccountingPaymentCB(
            payment_id=callback_data.payment_id,
            action="reject"
        ),
        state
    )

