# api/routes_student.py
from fastapi import APIRouter, Depends, HTTPException, Request

from api.security import require_roles
from database.db import (
    api_user_has_group,
    get_api_group_lessons,
    get_api_student_groups,
    get_api_student_results,
)

router = APIRouter(prefix="/api/student", tags=["Student"])


def make_material_url(request: Request, material_url: str | None):
    """
    DBdan kelgan material_url:
    - "/media/lessons/..." bo'lsa base_url bilan to'liq URL qiladi.
    - "media/lessons/..." bo'lsa ham to'g'rilaydi.
    - already http bo'lsa o'zini qaytaradi.
    """
    if not material_url:
        return None

    value = str(material_url).replace("\\", "/")

    if value.startswith("http://") or value.startswith("https://"):
        return value

    base_url = str(request.base_url).rstrip("/")

    if value.startswith("/media/"):
        return f"{base_url}{value}"

    if value.startswith("media/"):
        return f"{base_url}/{value}"

    return None


async def ensure_student_has_group(telegram_id: int, group_id: int):
    has_access = await api_user_has_group(telegram_id, group_id)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruh ma'lumotlarini ko'ra olmaysiz."
        )


@router.get("/profile")
async def student_profile(
    current_user: dict = Depends(require_roles("student"))
):
    profile = current_user["profile"]

    return {
        "ok": True,
        "telegram_id": current_user["telegram_id"],
        "profile": profile
    }


@router.get("/groups")
async def get_my_groups(
    current_user: dict = Depends(require_roles("student"))
):
    telegram_id = current_user["telegram_id"]

    groups = await get_api_student_groups(telegram_id)

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "groups": [dict(group) for group in groups]
    }


@router.get("/groups/{group_id}")
async def get_my_group_detail(
    group_id: int,
    current_user: dict = Depends(require_roles("student"))
):
    telegram_id = current_user["telegram_id"]

    await ensure_student_has_group(telegram_id, group_id)

    groups = await get_api_student_groups(telegram_id)
    group = None

    for item in groups:
        if item["id"] == group_id:
            group = dict(item)
            break

    if not group:
        raise HTTPException(
            status_code=404,
            detail="Guruh topilmadi."
        )

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "group": group
    }


@router.get("/groups/{group_id}/lessons")
async def get_my_group_lessons(
    group_id: int,
    request: Request,
    current_user: dict = Depends(require_roles("student"))
):
    telegram_id = current_user["telegram_id"]

    await ensure_student_has_group(telegram_id, group_id)

    lessons = await get_api_group_lessons(telegram_id, group_id)

    result = []

    for lesson in lessons:
        item = dict(lesson)
        item["material_url"] = make_material_url(
            request,
            item.get("material_url")
        )
        result.append(item)

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "group_id": group_id,
        "lessons": result
    }


@router.get("/results")
async def get_my_results(
    current_user: dict = Depends(require_roles("student"))
):
    telegram_id = current_user["telegram_id"]

    results = await get_api_student_results(telegram_id)

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "results": [dict(result) for result in results]
    }