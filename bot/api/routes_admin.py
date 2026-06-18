# api/routes_admin.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.security import require_roles
from database.db import (
    add_student_to_group_if_capacity,
    change_group_teacher,
    create_new_group,
    delete_group,
    get_api_admin_groups,
    get_api_admin_kick_requests,
    get_api_admin_payments,
    get_api_admin_statistics,
    get_api_admin_teachers,
    get_api_teacher_applications,
    get_group_link,
    get_kick_request,
    get_payment,
    log_admin_action,
    remove_student_from_group,
    update_kick_request_status,
    update_payment_status,
    update_teacher_status,
)


router = APIRouter(prefix="/api/admin", tags=["Admin"])


class ApprovePaymentPayload(BaseModel):
    group_id: int


class CreateGroupPayload(BaseModel):
    name: str
    language: str
    max_capacity: int = 10
    telegram_link: str
    teacher_id: int


class ChangeTeacherPayload(BaseModel):
    teacher_id: int


class RejectPayload(BaseModel):
    reason: Optional[str] = None


# ==========================================
# ADMIN + SUPERADMIN
# Oddiy admin faqat statistika va payment checklarni ko'radi/tasdiqlaydi.
# ==========================================

@router.get("/statistics")
async def admin_statistics(
    current_user: dict = Depends(require_roles("admin", "superadmin"))
):
    stats = await get_api_admin_statistics()

    return {
        "ok": True,
        "admin_id": current_user["telegram_id"],
        "statistics": stats
    }


@router.get("/payments")
async def admin_payments(
    status: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_roles("admin", "superadmin"))
):
    allowed_statuses = [None, "pending", "approved", "rejected"]

    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Payment status noto'g'ri.")

    payments = await get_api_admin_payments(status=status)

    return {
        "ok": True,
        "status": status,
        "payments": [dict(payment) for payment in payments]
    }


@router.post("/payments/{payment_id}/approve")
async def approve_payment(
    payment_id: int,
    payload: ApprovePaymentPayload,
    current_user: dict = Depends(require_roles("admin", "superadmin"))
):
    payment = await get_payment(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")

    if payment["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bu to'lov allaqachon ko'rib chiqilgan.")

    group = await get_group_link(payload.group_id)

    if not group:
        raise HTTPException(status_code=404, detail="Guruh topilmadi.")

    capacity_result = await add_student_to_group_if_capacity(
        payment["user_id"],
        payload.group_id
    )

    if not capacity_result["ok"]:
        raise HTTPException(status_code=400, detail=capacity_result["message"])

    await update_payment_status(payment_id, "approved")

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="payment_approved",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment["user_id"],
            "group_id": payload.group_id,
            "group_name": group["name"],
            "capacity": capacity_result
        }
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
async def reject_payment(
    payment_id: int,
    payload: RejectPayload = RejectPayload(),
    current_user: dict = Depends(require_roles("admin", "superadmin"))
):
    payment = await get_payment(payment_id)

    if not payment:
        raise HTTPException(status_code=404, detail="To'lov topilmadi.")

    if payment["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bu to'lov allaqachon ko'rib chiqilgan.")

    await update_payment_status(payment_id, "rejected")

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="payment_rejected",
        entity_type="payment",
        entity_id=payment_id,
        details={
            "student_id": payment["user_id"],
            "reason": payload.reason
        }
    )

    return {
        "ok": True,
        "payment_id": payment_id,
        "status": "rejected",
        "reason": payload.reason
    }


# ==========================================
# SUPERADMIN ONLY
# Guruh, ustoz, teacher application va kick-request boshqaruvi.
# ==========================================

@router.get("/groups")
async def admin_groups(
    current_user: dict = Depends(require_roles("superadmin"))
):
    groups = await get_api_admin_groups()

    return {
        "ok": True,
        "groups": [dict(group) for group in groups]
    }


@router.post("/groups")
async def create_group(
    payload: CreateGroupPayload,
    current_user: dict = Depends(require_roles("superadmin"))
):
    if payload.max_capacity <= 0:
        raise HTTPException(status_code=400, detail="Guruh sig'imi 0 dan katta bo'lishi kerak.")

    await create_new_group(
        name=payload.name,
        language=payload.language,
        max_capacity=payload.max_capacity,
        telegram_link=payload.telegram_link,
        teacher_id=payload.teacher_id
    )

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="group_created",
        entity_type="group",
        entity_id=None,
        details={
            "name": payload.name,
            "language": payload.language,
            "max_capacity": payload.max_capacity,
            "telegram_link": payload.telegram_link,
            "teacher_id": payload.teacher_id
        }
    )

    return {
        "ok": True,
        "message": "Guruh yaratildi.",
        "group": payload.model_dump()
    }


@router.patch("/groups/{group_id}/teacher")
async def change_teacher(
    group_id: int,
    payload: ChangeTeacherPayload,
    current_user: dict = Depends(require_roles("superadmin"))
):
    await change_group_teacher(group_id, payload.teacher_id)

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="group_teacher_changed",
        entity_type="group",
        entity_id=group_id,
        details={
            "group_id": group_id,
            "new_teacher_id": payload.teacher_id
        }
    )

    return {
        "ok": True,
        "message": "Ustoz almashtirildi.",
        "group_id": group_id,
        "teacher_id": payload.teacher_id
    }


@router.delete("/groups/{group_id}")
async def remove_group(
    group_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    await delete_group(group_id)

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="group_deleted",
        entity_type="group",
        entity_id=group_id,
        details={
            "group_id": group_id
        }
    )

    return {
        "ok": True,
        "message": "Guruh o'chirildi.",
        "group_id": group_id
    }


@router.get("/teachers")
async def admin_teachers(
    current_user: dict = Depends(require_roles("superadmin"))
):
    teachers = await get_api_admin_teachers()

    return {
        "ok": True,
        "teachers": [dict(teacher) for teacher in teachers]
    }


@router.get("/teacher-applications")
async def teacher_applications(
    status: str = Query(default="pending_teacher"),
    current_user: dict = Depends(require_roles("superadmin"))
):
    allowed_statuses = ["pending_teacher", "rejected_teacher", "teacher"]

    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Teacher application status noto'g'ri.")

    applications = await get_api_teacher_applications(status=status)

    return {
        "ok": True,
        "status": status,
        "applications": [dict(application) for application in applications]
    }


@router.post("/teacher-applications/{teacher_id}/approve")
async def approve_teacher_application(
    teacher_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    await update_teacher_status(teacher_id, "teacher")

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="teacher_application_approved",
        entity_type="user",
        entity_id=teacher_id,
        details={
            "teacher_id": teacher_id,
            "new_status": "teacher"
        }
    )

    return {
        "ok": True,
        "teacher_id": teacher_id,
        "status": "teacher"
    }


@router.post("/teacher-applications/{teacher_id}/reject")
async def reject_teacher_application(
    teacher_id: int,
    payload: RejectPayload = RejectPayload(),
    current_user: dict = Depends(require_roles("superadmin"))
):
    await update_teacher_status(teacher_id, "rejected_teacher")

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="teacher_application_rejected",
        entity_type="user",
        entity_id=teacher_id,
        details={
            "teacher_id": teacher_id,
            "new_status": "rejected_teacher",
            "reason": payload.reason
        }
    )

    return {
        "ok": True,
        "teacher_id": teacher_id,
        "status": "rejected_teacher",
        "reason": payload.reason
    }


@router.get("/kick-requests")
async def admin_kick_requests(
    status: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_roles("superadmin"))
):
    allowed_statuses = [None, "pending", "approved", "rejected"]

    if status not in allowed_statuses:
        raise HTTPException(status_code=400, detail="Kick request status noto'g'ri.")

    requests = await get_api_admin_kick_requests(status=status)

    return {
        "ok": True,
        "status": status,
        "kick_requests": [dict(item) for item in requests]
    }


@router.post("/kick-requests/{request_id}/approve")
async def approve_kick_request(
    request_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    request = await get_kick_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="So'rov topilmadi.")

    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bu so'rov allaqachon ko'rib chiqilgan.")

    await remove_student_from_group(request["user_id"], request["group_id"])
    await update_kick_request_status(request_id, "approved")

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="kick_request_approved",
        entity_type="kick_request",
        entity_id=request_id,
        details={
            "request_id": request_id,
            "student_id": request["user_id"],
            "group_id": request["group_id"],
            "teacher_id": request["teacher_id"]
        }
    )

    return {
        "ok": True,
        "request_id": request_id,
        "status": "approved",
        "student_id": request["user_id"],
        "group_id": request["group_id"]
    }


@router.post("/kick-requests/{request_id}/reject")
async def reject_kick_request(
    request_id: int,
    payload: RejectPayload = RejectPayload(),
    current_user: dict = Depends(require_roles("superadmin"))
):
    request = await get_kick_request(request_id)

    if not request:
        raise HTTPException(status_code=404, detail="So'rov topilmadi.")

    if request["status"] != "pending":
        raise HTTPException(status_code=400, detail="Bu so'rov allaqachon ko'rib chiqilgan.")

    await update_kick_request_status(request_id, "rejected")

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="kick_request_rejected",
        entity_type="kick_request",
        entity_id=request_id,
        details={
            "request_id": request_id,
            "student_id": request["user_id"],
            "group_id": request["group_id"],
            "teacher_id": request["teacher_id"],
            "reason": payload.reason
        }
    )

    return {
        "ok": True,
        "request_id": request_id,
        "status": "rejected",
        "reason": payload.reason
    }