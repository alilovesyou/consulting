# api/routes_common.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.security import get_current_profile
from database.db import set_user_interface_lang

router = APIRouter(prefix="/api", tags=["Common"])

ALLOWED_LANGS = {"uz", "ru", "en"}


class LanguagePayload(BaseModel):
    lang: str


def build_permissions(role: str) -> dict:
    """
    Frontend qaysi panel/bo'limlarni ko'rsatishini bilishi uchun.
    Bu security emas, faqat UI helper.
    Real himoya backend endpointlarda require_roles orqali qilinadi.
    """
    return {
        "can_view_student": role == "student",
        "can_view_teacher": role == "teacher",
        "can_view_admin": role in ["admin", "superadmin"],
        "can_view_accounting": role in ["admin", "accountant", "superadmin"],
        "can_manage_payments": role in ["accountant", "superadmin"],
        "can_manage_staff": role == "superadmin",
        "can_view_superadmin": role == "superadmin",
    }


@router.get("/health")
async def health_check():
    return {
        "ok": True,
        "service": "Visa Consulting Mini App API",
        "version": "1.1.0"
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_profile)):
    profile = current_user["profile"]
    role = current_user["role"]

    return {
        "ok": True,
        "telegram_id": current_user["telegram_id"],
        "telegram_user": current_user["telegram_user"],
        "profile": profile,
        "role": role,
        "permissions": build_permissions(role)
    }


@router.get("/permissions")
async def get_permissions(current_user: dict = Depends(get_current_profile)):
    role = current_user["role"]

    return {
        "ok": True,
        "role": role,
        "permissions": build_permissions(role)
    }


@router.patch("/language")
async def update_language(
    payload: LanguagePayload,
    current_user: dict = Depends(get_current_profile)
):
    lang = payload.lang.strip().lower()

    if lang not in ALLOWED_LANGS:
        raise HTTPException(
            status_code=400,
            detail="Til noto'g'ri. Faqat uz, ru, en mumkin."
        )

    telegram_id = current_user["telegram_id"]

    await set_user_interface_lang(telegram_id, lang)

    return {
        "ok": True,
        "telegram_id": telegram_id,
        "interface_lang": lang
    }