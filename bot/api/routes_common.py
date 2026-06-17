# api/routes_common.py
from fastapi import APIRouter, Depends

from api.security import get_current_profile

router = APIRouter(prefix="/api", tags=["Common"])


@router.get("/health")
async def health_check():
    return {
        "ok": True,
        "service": "Visa Consulting Mini App API"
    }


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_profile)):
    return {
        "telegram_id": current_user["telegram_id"],
        "telegram_user": current_user["telegram_user"],
        "profile": current_user["profile"],
        "role": current_user["role"]
    }