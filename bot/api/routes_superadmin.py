# api/routes_superadmin.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.security import require_roles
from database.db import (
    count_api_superadmin_users,
    count_superadmins,
    get_admin_action_detail,
    get_api_superadmin_admin_actions,
    get_api_superadmin_admins,
    get_api_superadmin_all_results,
    get_api_superadmin_group_students,
    get_api_superadmin_groups_overview,
    get_api_superadmin_statistics,
    get_api_superadmin_student_profile,
    get_api_superadmin_student_results,
    get_api_superadmin_students_overview,
    get_api_superadmin_teacher_groups,
    get_api_superadmin_teachers_by_language,
    get_api_superadmin_teachers_overview,
    get_api_superadmin_user,
    get_api_superadmin_users,
    get_recent_users_for_role_assignment,
    get_staff_users,
    log_admin_action,
    set_user_role,
    update_user_role,
)

router = APIRouter(prefix="/api/superadmin", tags=["Superadmin"])

ALLOWED_ROLES = [
    "user",
    "student",
    "teacher",
    "pending_teacher",
    "rejected_teacher",
    "admin",
    "accountant",
    "superadmin",
]

STAFF_ROLES = [
    "user",
    "admin",
    "accountant",
    "superadmin",
]


class ChangeRolePayload(BaseModel):
    role: str


class SetStaffRolePayload(BaseModel):
    telegram_id: int
    role: str
    full_name: Optional[str] = None


def validate_role(role: str):
    if role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role noto'g'ri.")


def validate_staff_role(role: str):
    if role not in STAFF_ROLES:
        raise HTTPException(
            status_code=400,
            detail="Staff management orqali faqat user/admin/accountant/superadmin role beriladi."
        )


async def protect_superadmin_demote(
    target_telegram_id: int,
    current_superadmin_id: int,
    old_role: Optional[str],
    new_role: str
):
    if target_telegram_id == current_superadmin_id and new_role != "superadmin":
        raise HTTPException(
            status_code=400,
            detail="O'zingizning superadmin rolingizni o'zgartira olmaysiz."
        )

    if old_role == "superadmin" and new_role != "superadmin":
        superadmin_count = await count_superadmins()

        if superadmin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Oxirgi superadminni boshqa rolga o'tkazib bo'lmaydi."
            )


# ==========================================
# STATISTICS
# ==========================================

@router.get("/statistics")
async def superadmin_statistics(
    current_user: dict = Depends(require_roles("superadmin"))
):
    stats = await get_api_superadmin_statistics()

    return {
        "ok": True,
        "superadmin_id": current_user["telegram_id"],
        "statistics": stats
    }


# ==========================================
# ALL USERS
# ==========================================

@router.get("/users")
async def superadmin_users(
    role: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    if role is not None:
        validate_role(role)

    users = await get_api_superadmin_users(
        role=role,
        search=search,
        limit=limit,
        offset=offset
    )

    total = await count_api_superadmin_users(
        role=role,
        search=search
    )

    return {
        "ok": True,
        "total": total,
        "limit": limit,
        "offset": offset,
        "role": role,
        "search": search,
        "users": [dict(user) for user in users]
    }


@router.get("/users/{telegram_id}")
async def superadmin_user_detail(
    telegram_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    user = await get_api_superadmin_user(telegram_id)

    if not user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")

    return {
        "ok": True,
        "user": dict(user)
    }


@router.patch("/users/{telegram_id}/role")
async def superadmin_change_user_role(
    telegram_id: int,
    payload: ChangeRolePayload,
    current_user: dict = Depends(require_roles("superadmin"))
):
    new_role = payload.role
    current_superadmin_id = current_user["telegram_id"]

    validate_role(new_role)

    target_user = await get_api_superadmin_user(telegram_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")

    old_role = target_user["role"]

    await protect_superadmin_demote(
        target_telegram_id=telegram_id,
        current_superadmin_id=current_superadmin_id,
        old_role=old_role,
        new_role=new_role
    )

    await update_user_role(telegram_id, new_role)

    await log_admin_action(
        admin_id=current_superadmin_id,
        action="user_role_changed_from_miniapp",
        entity_type="user",
        entity_id=telegram_id,
        details={
            "target_user_id": telegram_id,
            "old_role": old_role,
            "new_role": new_role
        }
    )

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "old_role": old_role,
        "new_role": new_role
    }


# ==========================================
# STAFF MANAGEMENT
# superadmin only
# ==========================================

@router.get("/staff")
async def superadmin_staff(
    role: Optional[str] = Query(default=None),
    current_user: dict = Depends(require_roles("superadmin"))
):
    if role is not None and role not in ["admin", "accountant", "superadmin"]:
        raise HTTPException(
            status_code=400,
            detail="Staff role faqat admin/accountant/superadmin bo'lishi mumkin."
        )

    staff = await get_staff_users(role=role)

    return {
        "ok": True,
        "role": role,
        "staff": [dict(item) for item in staff]
    }


@router.get("/staff/recent-users")
async def superadmin_recent_users_for_role_assignment(
    limit: int = Query(default=10, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    users = await get_recent_users_for_role_assignment(
        limit=limit,
        offset=offset
    )

    return {
        "ok": True,
        "limit": limit,
        "offset": offset,
        "users": [dict(user) for user in users]
    }


@router.post("/staff/role")
async def superadmin_set_staff_role(
    payload: SetStaffRolePayload,
    current_user: dict = Depends(require_roles("superadmin"))
):
    current_superadmin_id = current_user["telegram_id"]

    validate_staff_role(payload.role)

    old_role = await get_api_superadmin_user(payload.telegram_id)
    old_role_value = old_role["role"] if old_role else "user"

    await protect_superadmin_demote(
        target_telegram_id=payload.telegram_id,
        current_superadmin_id=current_superadmin_id,
        old_role=old_role_value,
        new_role=payload.role
    )

    await set_user_role(
        telegram_id=payload.telegram_id,
        role=payload.role,
        full_name=payload.full_name
    )

    await log_admin_action(
        admin_id=current_superadmin_id,
        action="staff_role_changed_from_miniapp",
        entity_type="user",
        entity_id=payload.telegram_id,
        details={
            "target_user_id": payload.telegram_id,
            "full_name": payload.full_name,
            "old_role": old_role_value,
            "new_role": payload.role
        }
    )

    return {
        "ok": True,
        "telegram_id": payload.telegram_id,
        "old_role": old_role_value,
        "new_role": payload.role
    }


# Legacy endpoint. Frontend hozir /api/superadmin/admins ishlatyapti.
# Keyin frontendni /staff ga o'tkazamiz.
@router.get("/admins")
async def superadmin_admins(
    current_user: dict = Depends(require_roles("superadmin"))
):
    admins = await get_api_superadmin_admins()

    return {
        "ok": True,
        "admins": [dict(admin) for admin in admins]
    }


# ==========================================
# ADMIN / STAFF ACTIONS
# ==========================================

@router.get("/admin-actions")
async def superadmin_admin_actions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    actions = await get_api_superadmin_admin_actions(
        limit=limit,
        offset=offset
    )

    return {
        "ok": True,
        "limit": limit,
        "offset": offset,
        "actions": [dict(action) for action in actions]
    }


@router.get("/admin-actions/{action_id}")
async def superadmin_admin_action_detail(
    action_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    action = await get_admin_action_detail(action_id)

    if not action:
        raise HTTPException(status_code=404, detail="Action topilmadi.")

    return {
        "ok": True,
        "action": dict(action)
    }


# ==========================================
# TEACHERS
# ==========================================

@router.get("/teachers")
async def superadmin_teachers_overview(
    current_user: dict = Depends(require_roles("superadmin"))
):
    teachers = await get_api_superadmin_teachers_overview()

    return {
        "ok": True,
        "teachers": [dict(teacher) for teacher in teachers]
    }


@router.get("/teachers/by-language/{language}")
async def superadmin_teachers_by_language(
    language: str,
    current_user: dict = Depends(require_roles("superadmin"))
):
    teachers = await get_api_superadmin_teachers_by_language(language)

    return {
        "ok": True,
        "language": language,
        "teachers": [dict(teacher) for teacher in teachers]
    }


@router.get("/teachers/{teacher_id}/groups")
async def superadmin_teacher_groups(
    teacher_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    groups = await get_api_superadmin_teacher_groups(teacher_id)

    return {
        "ok": True,
        "teacher_id": teacher_id,
        "groups": [dict(group) for group in groups]
    }


# ==========================================
# GROUPS
# ==========================================

@router.get("/groups")
async def superadmin_groups_overview(
    current_user: dict = Depends(require_roles("superadmin"))
):
    groups = await get_api_superadmin_groups_overview()

    return {
        "ok": True,
        "groups": [dict(group) for group in groups]
    }


@router.get("/groups/{group_id}/students")
async def superadmin_group_students(
    group_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    students = await get_api_superadmin_group_students(group_id)

    return {
        "ok": True,
        "group_id": group_id,
        "students": [dict(student) for student in students]
    }


# ==========================================
# STUDENTS
# ==========================================

@router.get("/students")
async def superadmin_students_overview(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    students = await get_api_superadmin_students_overview(
        limit=limit,
        offset=offset
    )

    return {
        "ok": True,
        "limit": limit,
        "offset": offset,
        "students": [dict(student) for student in students]
    }


@router.get("/students/{student_id}")
async def superadmin_student_profile(
    student_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    student = await get_api_superadmin_student_profile(student_id)

    if not student:
        raise HTTPException(status_code=404, detail="O'quvchi topilmadi.")

    return {
        "ok": True,
        "student": dict(student)
    }


@router.get("/students/{student_id}/results")
async def superadmin_student_results(
    student_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    results = await get_api_superadmin_student_results(student_id)

    return {
        "ok": True,
        "student_id": student_id,
        "results": [dict(result) for result in results]
    }


# ==========================================
# RESULTS
# ==========================================

@router.get("/results")
async def superadmin_all_results(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    results = await get_api_superadmin_all_results(
        limit=limit,
        offset=offset
    )

    return {
        "ok": True,
        "limit": limit,
        "offset": offset,
        "results": [dict(result) for result in results]
    }