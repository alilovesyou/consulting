# api/routes_teacher.py
import os
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel

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

BASE_DIR = Path(__file__).resolve().parent.parent
LESSONS_DIR = BASE_DIR / "media" / "lessons"

MAX_LESSON_FILE_SIZE_MB = int(os.getenv("MAX_LESSON_FILE_SIZE_MB", "200"))
MAX_LESSON_FILE_SIZE_BYTES = MAX_LESSON_FILE_SIZE_MB * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".mp4", ".mov", ".mkv", ".webm",
    ".pdf", ".doc", ".docx", ".ppt", ".pptx",
    ".jpg", ".jpeg", ".png", ".webp"
}


class CreateResultPayload(BaseModel):
    student_id: int
    result_title: str
    score: str
    comment: Optional[str] = ""


class CreateKickRequestPayload(BaseModel):
    student_id: int
    reason: str


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


def validate_upload_file(original_filename: str):
    ext = Path(original_filename).suffix.lower()

    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Bu fayl turi ruxsat etilmagan."
        )

    return ext


def make_material_url(request: Request, material_path: str | None):
    if not material_path:
        return None

    normalized = str(material_path).replace("\\", "/")
    base_url = str(request.base_url).rstrip("/")

    if normalized.startswith("media/lessons/"):
        return f"{base_url}/{normalized}"

    if "/media/lessons/" in normalized:
        relative = normalized.split("/media/lessons/", 1)[1]
        return f"{base_url}/media/lessons/{relative}"

    return None


async def save_upload_file(file: UploadFile, local_path: Path) -> int:
    file_size = 0
    local_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with open(local_path, "wb") as output:
            while True:
                chunk = await file.read(1024 * 1024)

                if not chunk:
                    break

                file_size += len(chunk)

                if file_size > MAX_LESSON_FILE_SIZE_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Fayl juda katta. Maksimum: {MAX_LESSON_FILE_SIZE_MB} MB."
                    )

                output.write(chunk)

    except HTTPException:
        if local_path.exists():
            local_path.unlink(missing_ok=True)
        raise

    except Exception:
        if local_path.exists():
            local_path.unlink(missing_ok=True)
        raise HTTPException(
            status_code=500,
            detail="Faylni saqlashda xatolik yuz berdi."
        )

    return file_size


@router.get("/groups")
async def teacher_groups(
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]
    groups = await get_api_teacher_groups(teacher_id)

    return {
        "ok": True,
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
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruhni boshqara olmaysiz."
        )

    students = await get_teacher_group_students(teacher_id, group_id)

    return {
        "ok": True,
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
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruhni boshqara olmaysiz."
        )

    lessons = await get_api_teacher_group_lessons(teacher_id, group_id)

    result = []

    for lesson in lessons:
        item = dict(lesson)
        item["material_url"] = make_material_url(request, item.get("video_path"))
        result.append(item)

    return {
        "ok": True,
        "teacher_id": teacher_id,
        "group_id": group_id,
        "lessons": result
    }


@router.post("/groups/{group_id}/lessons")
async def upload_teacher_lesson(
    group_id: int,
    request: Request,
    title: str = Form(...),
    file: UploadFile = File(...),
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruhga dars yuklay olmaysiz."
        )

    clean_title = title.strip()

    if not clean_title:
        raise HTTPException(
            status_code=400,
            detail="Dars nomi bo'sh bo'lmasligi kerak."
        )

    original_filename = file.filename or "lesson_file"
    ext = validate_upload_file(original_filename)

    material_type = detect_material_type(original_filename, file.content_type)

    unique_name = f"lesson_{uuid.uuid4().hex}{ext}"
    relative_path = f"media/lessons/group_{group_id}/{unique_name}"
    local_path = BASE_DIR / relative_path

    file_size = await save_upload_file(file, local_path)

    lesson_id = await add_lesson(
        group_id=group_id,
        title=clean_title,
        material_path=relative_path,
        material_type=material_type,
        original_filename=original_filename,
        file_size=file_size
    )

    return {
        "ok": True,
        "lesson_id": lesson_id,
        "group_id": group_id,
        "title": clean_title,
        "material_type": material_type,
        "original_filename": original_filename,
        "file_size": file_size,
        "path": relative_path,
        "material_url": make_material_url(request, relative_path)
    }


@router.get("/results")
async def teacher_results(
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]
    results = await get_api_teacher_results(teacher_id)

    return {
        "ok": True,
        "teacher_id": teacher_id,
        "results": [dict(result) for result in results]
    }


@router.post("/groups/{group_id}/results")
async def create_teacher_result(
    group_id: int,
    payload: CreateResultPayload,
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruhga natija kirita olmaysiz."
        )

    if payload.student_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Student ID noto'g'ri."
        )

    result_title = payload.result_title.strip()
    score = payload.score.strip()
    comment = (payload.comment or "").strip()

    if not result_title:
        raise HTTPException(
            status_code=400,
            detail="Natija nomi bo'sh bo'lmasligi kerak."
        )

    if not score:
        raise HTTPException(
            status_code=400,
            detail="Ball/natija bo'sh bo'lmasligi kerak."
        )

    if not await api_student_is_in_teacher_group(teacher_id, group_id, payload.student_id):
        raise HTTPException(
            status_code=403,
            detail="Bu o'quvchi sizning guruhingizda emas."
        )

    result_id = await add_student_result(
        user_id=payload.student_id,
        group_id=group_id,
        teacher_id=teacher_id,
        result_title=result_title,
        score=score,
        comment=comment
    )

    student = await get_full_profile(payload.student_id)
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
        "ok": True,
        "teacher_id": teacher_id,
        "kick_requests": [dict(item) for item in requests]
    }


@router.post("/groups/{group_id}/kick-requests")
async def create_teacher_kick_request(
    group_id: int,
    payload: CreateKickRequestPayload,
    current_user: dict = Depends(require_roles("teacher"))
):
    teacher_id = current_user["telegram_id"]

    if not await teacher_owns_group(teacher_id, group_id):
        raise HTTPException(
            status_code=403,
            detail="Siz bu guruh bo'yicha so'rov yubora olmaysiz."
        )

    if payload.student_id <= 0:
        raise HTTPException(
            status_code=400,
            detail="Student ID noto'g'ri."
        )

    reason = payload.reason.strip()

    if not reason:
        raise HTTPException(
            status_code=400,
            detail="Chetlatish sababi bo'sh bo'lmasligi kerak."
        )

    if not await api_student_is_in_teacher_group(teacher_id, group_id, payload.student_id):
        raise HTTPException(
            status_code=403,
            detail="Bu o'quvchi sizning guruhingizda emas."
        )

    request_id = await add_kick_request(
        user_id=payload.student_id,
        group_id=group_id,
        teacher_id=teacher_id,
        reason=reason
    )

    student = await get_full_profile(payload.student_id)
    group = await get_group_info(group_id)

    return {
        "ok": True,
        "request_id": request_id,
        "student": dict(student) if student else None,
        "group": dict(group) if group else None,
        "reason": reason,
        "status": "pending"
    }