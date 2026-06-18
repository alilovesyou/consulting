# api/routes_superadmin.py
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from api.security import require_roles
from database.db import (
    count_api_superadmin_users,
    count_superadmins,
    get_api_superadmin_admins,
    get_api_superadmin_statistics,
    get_api_superadmin_user,
    get_api_superadmin_users,
    update_user_role,
    get_api_superadmin_admin_actions,
    upsert_admin_user,
    remove_admin_role,
    get_api_superadmin_teachers_overview,
    get_api_superadmin_teacher_groups,
    get_api_superadmin_groups_overview,
    get_api_superadmin_group_students,
    get_api_superadmin_students_overview,
    get_api_superadmin_student_results,
    get_api_superadmin_all_results,
    log_admin_action
)

router = APIRouter(prefix="/api/superadmin", tags=["Superadmin"])

ALLOWED_ROLES = [
    "user",
    "student",
    "teacher",
    "pending_teacher",
    "rejected_teacher",
    "admin",
    "superadmin"
]


class ChangeRolePayload(BaseModel):
    role: str


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


@router.get("/users")
async def superadmin_users(
    role: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    if role is not None and role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role noto'g'ri.")

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

    if new_role not in ALLOWED_ROLES:
        raise HTTPException(status_code=400, detail="Role noto'g'ri.")

    target_user = await get_api_superadmin_user(telegram_id)

    if not target_user:
        raise HTTPException(status_code=404, detail="Foydalanuvchi topilmadi.")

    old_role = target_user["role"]

    # O'zini o'zi superadminlikdan tushirib yubormasin
    if telegram_id == current_superadmin_id and new_role != "superadmin":
        raise HTTPException(
            status_code=400,
            detail="O'zingizning superadmin rolingizni o'zgartira olmaysiz."
        )

    # Oxirgi superadminni demote qilib yubormaslik
    if old_role == "superadmin" and new_role != "superadmin":
        superadmin_count = await count_superadmins()

        if superadmin_count <= 1:
            raise HTTPException(
                status_code=400,
                detail="Oxirgi superadminni boshqa rolga o'tkazib bo'lmaydi."
            )

    await update_user_role(telegram_id, new_role)

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "old_role": old_role,
        "new_role": new_role
    }


@router.get("/admins")
async def superadmin_admins(
    current_user: dict = Depends(require_roles("superadmin"))
):
    admins = await get_api_superadmin_admins()

    return {
        "ok": True,
        "admins": [dict(admin) for admin in admins]
    }

class AddAdminPayload(BaseModel):
    telegram_id: int
    full_name: Optional[str] = None


@router.get("/admin-actions")
async def superadmin_admin_actions(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    actions = await get_api_superadmin_admin_actions(limit=limit, offset=offset)

    return {
        "ok": True,
        "actions": [dict(action) for action in actions]
    }


@router.post("/admins")
async def superadmin_add_admin(
    payload: AddAdminPayload,
    current_user: dict = Depends(require_roles("superadmin"))
):
    await upsert_admin_user(payload.telegram_id, payload.full_name)

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="superadmin_add_admin",
        entity_type="user",
        entity_id=payload.telegram_id,
        details={
            "new_admin_id": payload.telegram_id,
            "full_name": payload.full_name
        }
    )

    return {
        "ok": True,
        "message": "Admin qo'shildi.",
        "telegram_id": payload.telegram_id
    }


@router.delete("/admins/{telegram_id}")
async def superadmin_remove_admin(
    telegram_id: int,
    current_user: dict = Depends(require_roles("superadmin"))
):
    if telegram_id == current_user["telegram_id"]:
        raise HTTPException(
            status_code=400,
            detail="O'zingizni adminlardan olib tashlay olmaysiz."
        )

    await remove_admin_role(telegram_id)

    await log_admin_action(
        admin_id=current_user["telegram_id"],
        action="superadmin_remove_admin",
        entity_type="user",
        entity_id=telegram_id,
        details={
            "removed_admin_id": telegram_id
        }
    )

    return {
        "ok": True,
        "message": "Admin roli olib tashlandi.",
        "telegram_id": telegram_id
    }


@router.get("/teachers")
async def superadmin_teachers_overview(
    current_user: dict = Depends(require_roles("superadmin"))
):
    teachers = await get_api_superadmin_teachers_overview()

    return {
        "ok": True,
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


@router.get("/students")
async def superadmin_students_overview(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    students = await get_api_superadmin_students_overview(limit=limit, offset=offset)

    return {
        "ok": True,
        "students": [dict(student) for student in students]
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


@router.get("/results")
async def superadmin_all_results(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    current_user: dict = Depends(require_roles("superadmin"))
):
    results = await get_api_superadmin_all_results(limit=limit, offset=offset)

    return {
        "ok": True,
        "results": [dict(result) for result in results]
    }