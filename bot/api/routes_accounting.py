# api/routes_accounting.py
import os
from html import escape
from typing import Optional

from aiogram import Bot
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from api.security import require_roles
from database.db import (
    add_student_to_group_if_capacity,
    approve_payment_with_actor,
    get_accounting_payment_detail,
    get_accounting_payment_stats,
    get_accounting_payments,
    get_active_groups,
    get_group_link,
    get_user_interface_lang,
    log_admin_action,
    reject_payment_with_actor,
)

router = APIRouter(prefix="/api/accounting", tags=["Accounting"])

ALLOWED_STATUSES = {"pending", "approved", "rejected", "all"}
ALLOWED_METHODS = {"cash", "card", "all"}


class ApprovePaymentPayload(BaseModel):
    group_id: int


class RejectPaymentPayload(BaseModel):
    reason: Optional[str] = None


def normalize_filter(value: Optional[str]):
    if value is None or value == "all":
        return None
    return value


def make_media_url(request: Request, path: Optional[str]):
    if not path:
        return None

    normalized = str(path).replace("\\", "/")

    if normalized.startswith("media/"):
        base_url = str(request.base_url).rstrip("/")
        return f"{base_url}/{normalized}"

    return None


def payment_to_dict(payment, request: Request):
    item = dict(payment)
    item["receipt_url"] = make_media_url(request, item.get("receipt_path"))
    return item


async def user_lang(user_id: int) -> str:
    lang = await get_user_interface_lang(user_id)
    return lang or "uz"


def payment_approved_text(lang: str, group_name: str, group_link: str) -> str:
    texts = {
        "uz": (
            "🎉 <b>Tabriklaymiz! Sizning to‘lovingiz tasdiqlandi.</b>\n\n"
            f"Siz <b>{escape(group_name)}</b> guruhiga biriktirildingiz.\n\n"
            "Guruhga qo‘shilish havolasi 👇\n"
            f"{escape(group_link)}"
        ),
        "ru": (
            "🎉 <b>Поздравляем! Ваша оплата подтверждена.</b>\n\n"
            f"Вы добавлены в группу <b>{escape(group_name)}</b>.\n\n"
            "Ссылка для вступления 👇\n"
            f"{escape(group_link)}"
        ),
        "en": (
            "🎉 <b>Congratulations! Your payment has been approved.</b>\n\n"
            f"You have been assigned to <b>{escape(group_name)}</b>.\n\n"
            "Group invitation link 👇\n"
            f"{escape(group_link)}"
        ),
    }
    return texts.get(lang) or texts["uz"]


def payment_rejected_text(lang: str, reason: str) -> str:
    reason_text = escape(reason or "-")

    texts = {
        "uz": (
            "❌ Sizning to‘lovingiz tasdiqlanmadi.\n\n"
            f"Sabab: {reason_text}\n\n"
            "Qaytadan to‘lov qilish uchun 📚 Kurslar bo‘limidan foydalaning."
        ),
        "ru": (
            "❌ Ваша оплата не подтверждена.\n\n"
            f"Причина: {reason_text}\n\n"
            "Чтобы повторить оплату, используйте раздел 📚 Курсы."
        ),
        "en": (
            "❌ Your payment was not approved.\n\n"
            f"Reason: {reason_text}\n\n"
            "To pay again, please use the 📚 Courses section."
        ),
    }
    return texts.get(lang) or texts["uz"]


async def send_telegram_message(chat_id: int, text: str):
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        return

    bot = Bot(token=bot_token)

    try:
        await bot.send_message(
            chat_id=chat_id,
            text=text,
            parse_mode="HTML"
        )
    except Exception:
        pass
    finally:
        await bot.session.close()


@router.get("/stats")
async def accounting_stats(
    current_user: dict = Depends(require_roles("admin", "accountant", "superadmin"))
):
    stats = await get_accounting_payment_stats()

    return {
        "ok": True,
        "viewer_id": current_user["telegram_id"],
        "statistics": dict(stats)
    }


@router.get("/payments")
async def accounting_payments(
    request: Request,
    status: Optional[str] = Query(default="pending"),
    payment_method: Optional[str] = Query(default="all"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("admin", "accountant", "superadmin"))
):
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Payment status noto'g'ri.")

    if payment_method not in ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail="Payment method noto'g'ri.")

    payments = await get_accounting_payments(
        status=normalize_filter(status),
        payment_method=normalize_filter(payment_method),
        limit=limit,
        offset=offset
    )

    return {
        "ok": True,
        "status": status,
        "payment_method": payment_method,
        "limit": limit,
        "offset": offset,
        "payments": [payment_to_dict(payment, request) for payment in payments]
    }


@router.get("/payments/history")
async def accounting_payment_history(
    request: Request,
    status: Optional[str] = Query(default="all"),
    payment_method: Optional[str] = Query(default="all"),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("admin", "accountant", "superadmin"))
):
    if status not in ALLOWED_STATUSES:
        raise HTTPException(status_code=400, detail="Payment status noto'g'ri.")

    if payment_method not in ALLOWED_METHODS:
        raise HTTPException(status_code=400, detail="Payment method noto'g'ri.")

    payments = await get_accounting_payments(
        status=normalize_filter(status),
        payment_method=normalize_filter(payment_method),
        limit=limit,
        offset=offset
    )

    return {
        "ok": True,
        "status": status,
        "payment_method": payment_method,
        "limit": limit,
        "offset": offset,
        "payments": [payment_to_dict(payment, request) for payment in payments]
    }


@router.get("/payments/{payment_id}")
async def accounting_payment_detail(
    payment_id: int,
    request: Request,
    current_user: dict = Depends(require_roles("admin", "accountant", "superadmin"))
):
    payment = await get_accounting_payment_detail(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")

    return {
        "ok": True,
        "payment": payment_to_dict(payment, request)
    }


@router.get("/groups")
async def accounting_active_groups(
    current_user: dict = Depends(require_roles("accountant", "superadmin"))
):
    groups = await get_active_groups()

    return {
        "ok": True,
        "groups": [dict(group) for group in groups]
    }


@router.post("/payments/{payment_id}/approve")
async def accounting_approve_payment(
    payment_id: int,
    payload: ApprovePaymentPayload,
    current_user: dict = Depends(require_roles("accountant", "superadmin"))
):
    actor_id = current_user["telegram_id"]

    payment = await get_accounting_payment_detail(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")

    if payment["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail="Bu to'lov allaqachon ko'rib chiqilgan."
        )

    group = await get_group_link(payload.group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi.")

    capacity_result = await add_student_to_group_if_capacity(
        payment["user_id"],
        payload.group_id
    )

    if not capacity_result["ok"]:
        raise HTTPException(status_code=400, detail=capacity_result["message"])

    await approve_payment_with_actor(
        payment_id=payment_id,
        actor_id=actor_id
    )

    await log_admin_action(
        admin_id=actor_id,
        action="payment_approved_from_miniapp",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment["user_id"],
            "group_id": payload.group_id,
            "group_name": group["name"],
            "capacity": capacity_result,
        }
    )

    student_lang = await user_lang(payment["user_id"])

    await send_telegram_message(
        chat_id=payment["user_id"],
        text=payment_approved_text(
            student_lang,
            group_name=group["name"],
            group_link=group["telegram_link"]
        )
    )

    return {
        "ok": True,
        "payment_id": payment_id,
        "status": "approved",
        "student_id": payment["user_id"],
        "group_id": payload.group_id,
        "group_name": group["name"],
        "capacity": capacity_result
    }


@router.post("/payments/{payment_id}/reject")
async def accounting_reject_payment(
    payment_id: int,
    payload: RejectPaymentPayload,
    current_user: dict = Depends(require_roles("accountant", "superadmin"))
):
    actor_id = current_user["telegram_id"]
    reason = (payload.reason or "").strip() or "-"

    payment = await get_accounting_payment_detail(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")

    if payment["status"] != "pending":
        raise HTTPException(
            status_code=400,
            detail="Bu to'lov allaqachon ko'rib chiqilgan."
        )

    await reject_payment_with_actor(
        payment_id=payment_id,
        actor_id=actor_id,
        reason=reason
    )

    await log_admin_action(
        admin_id=actor_id,
        action="payment_rejected_from_miniapp",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment["user_id"],
            "reason": reason,
        }
    )

    student_lang = await user_lang(payment["user_id"])

    await send_telegram_message(
        chat_id=payment["user_id"],
        text=payment_rejected_text(student_lang, reason)
    )

    return {
        "ok": True,
        "payment_id": payment_id,
        "status": "rejected",
        "reason": reason
    }