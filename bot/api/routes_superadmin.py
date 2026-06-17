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