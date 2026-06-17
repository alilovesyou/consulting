# api/routes_teacher.py
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile

from api.security import require_roles
from database.db import (
    add_kick_request,
    add_lesson,
    add_student_result,
    api_student_is_in_teacher_group,
    get_api_teacher_group_lessons,
    get_api_teacher_groups,
    get_api_teacher_kick_requests,
    get_api_teacher_results,
    get_full_profile,
    get_group_info,
    get_teacher_group_students,
    teacher_owns_group,
)

router = APIRouter(prefix="/api/teacher", tags=["Teacher"])

ALLOWED_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".webm",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".webp"
}


def detect_material_type(filename: str, content_type: str | None = None) -> str:
    ext = Path(filename).suffix.lower()

    if ext in [".mp4", ".mov", ".mkv", ".webm"]:
        return "video"

    if ext in [".jpg", ".jpeg", ".png", ".webp"]:
        return "photo"

    if content_type and content_type.startswith("image/"):
        return "photo"

    if content_type and content_type.startswith("video/"):
        return "video"

    return "document"


@router.get("/groups")
async def teacher_groups(
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    groups = await get_api_teacher_groups(teacher_id)

    return {
        "teacher_id": teacher_id,
        "groups": [dict(group) for group in groups]
    }


@router.get("/groups/{group_id}/students")
async def teacher_group_students(
    group_id: int,
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(status_code=403, detail="Siz bu guruhni boshqara olmaysiz.")

    students = await get_teacher_group_students(teacher_id, group_id)

    return {
        "teacher_id": teacher_id,
        "group_id": group_id,
        "students": [dict(student) for student in students]
    }


@router.get("/groups/{group_id}/lessons")
async def teacher_group_lessons(
    group_id: int,
    request: Request,
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(status_code=403, detail="Siz bu guruhni boshqara olmaysiz.")

    lessons = await get_api_teacher_group_lessons(teacher_id, group_id)

    result = []
    base_url = str(request.base_url).rstrip("/")

    for lesson in lessons:
        item = dict(lesson)

        material_path = item.get("video_path")
        if material_path and material_path.startswith("media/lessons/"):
            item["material_url"] = base_url + "/" + material_path.replace("\\", "/")
        else:
            item["material_url"] = None

        result.append(item)

    return {
        "teacher_id": teacher_id,
        "group_id": group_id,
        "lessons": result
    }


@router.post("/groups/{group_id}/lessons")
async def upload_teacher_lesson(
    group_id: int,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(status_code=403, detail="Siz bu guruhga dars yuklay olmaysiz.")

    original_filename = file.filename or "lesson_file"
    ext = Path(original_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Bu fayl turi ruxsat etilmagan."
        )

    folder_path = Path(f"media/lessons/group_{group_id}")
    folder_path.mkdir(parents=True, exist_ok=True)

    unique_name = f"lesson_{uuid.uuid4().hex}{ext}"
    local_path = folder_path / unique_name

    file_size = 0

    with open(local_path, "wb") as output:
        while True:
            chunk = await file.read(1024 * 1024)
            if not chunk:
                break

            file_size += len(chunk)
            output.write(chunk)

    material_type = detect_material_type(original_filename, file.content_type)

    lesson_id = await add_lesson(
        group_id=group_id,
        title=title,
        material_path=str(local_path).replace("\\", "/"),
        material_type=material_type,
        original_filename=original_filename,
        file_size=file_size
    )

    return {
        "ok": True,
        "lesson_id": lesson_id,
        "group_id": group_id,
        "title": title,
        "material_type": material_type,
        "original_filename": original_filename,
        "file_size": file_size,
        "path": str(local_path).replace("\\", "/")
    }


@router.get("/results")
async def teacher_results(
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    results = await get_api_teacher_results(teacher_id)

    return {
        "teacher_id": teacher_id,
        "results": [dict(result) for result in results]
    }


@router.post("/groups/{group_id}/results")
async def create_teacher_result(
    group_id: int,
    student_id: int = Form(...),
    result_title: str = Form(...),
    score: str = Form(...),
    comment: str = Form(""),
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(status_code=403, detail="Siz bu guruhga natija kirita olmaysiz.")

    if not await api_student_is_in_teacher_group(teacher_id, group_id, student_id):
        raise HTTPException(status_code=403, detail="Bu o'quvchi sizning guruhingizda emas.")

    result_id = await add_student_result(
        user_id=student_id,
        group_id=group_id,
        teacher_id=teacher_id,
        result_title=result_title,
        score=score,
        comment=comment
    )

    student = await get_full_profile(student_id)
    group = await get_group_info(group_id)

    return {
        "ok": True,
        "result_id": result_id,
        "student": dict(student) if student else None,
        "group": dict(group) if group else None,
        "result_title": result_title,
        "score": score,
        "comment": comment
    }


@router.get("/kick-requests")
async def teacher_kick_requests(
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    requests = await get_api_teacher_kick_requests(teacher_id)

    return {
        "teacher_id": teacher_id,
        "kick_requests": [dict(item) for item in requests]
    }


@router.post("/groups/{group_id}/kick-requests")
async def create_teacher_kick_request(
    group_id: int,
    student_id: int = Form(...),
    reason: str = Form(...),
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(status_code=403, detail="Siz bu guruh bo'yicha so'rov yubora olmaysiz.")

    if not await api_student_is_in_teacher_group(teacher_id, group_id, student_id):
        raise HTTPException(status_code=403, detail="Bu o'quvchi sizning guruhingizda emas.")

    request_id = await add_kick_request(
        user_id=student_id,
        group_id=group_id,
        teacher_id=teacher_id,
        reason=reason
    )

    student = await get_full_profile(student_id)
    group = await get_group_info(group_id)

    return {
        "ok": True,
        "request_id": request_id,
        "student": dict(student) if student else None,
        "group": dict(group) if group else None,
        "reason": reason,
        "status": "pending"
    }