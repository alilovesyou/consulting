# api/routes_student.py
from fastapi import APIRouter, Depends, HTTPException, Request

from api.security import require_roles
from database.db import (
    get_api_student_groups,
    get_api_group_lessons,
    get_api_student_results,
    api_user_has_group
)

router = APIRouter(prefix="/api/student", tags=["Student"])


@router.get("/groups")
async def get_my_groups(
    current_user: dict = Depends(require_roles("student"))
):
    telegram_id = current_user["telegram_id"]

    groups = await get_api_student_groups(telegram_id)

    return {
        "telegram_id": telegram_id,
        "groups": [dict(group) for group in groups]
    }


@router.get("/groups/{group_id}/lessons")
async def get_my_group_lessons(
    group_id: int,
    request: Request,
    current_user: dict = Depends(require_roles("student"))
):
    telegram_id = current_user["telegram_id"]

    has_access = await api_user_has_group(telegram_id, group_id)

    if not has_access:
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruh darslarini ko'ra olmaysiz."
        )

    lessons = await get_api_group_lessons(telegram_id, group_id)

    result = []
    base_url = str(request.base_url).rstrip("/")

    for lesson in lessons:
        item = dict(lesson)

        if item.get("material_url"):
            item["material_url"] = base_url + item["material_url"]

        result.append(item)

    return {
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
        "telegram_id": telegram_id,
        "results": [dict(result) for result in results]
    }