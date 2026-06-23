# api/security.py
import hashlib
import hmac
import json
import os
import time
from typing import Optional
from urllib.parse import parse_qsl

from dotenv import load_dotenv
from fastapi import Depends, Header, HTTPException

from database.db import get_api_user_profile

load_dotenv()

# Telegram initData 7 kungacha yaroqli.
# Xohlasang keyin 1 kunga tushiramiz.
INIT_DATA_MAX_AGE_SECONDS = 60 * 60 * 24 * 7

# Local development uchun.
# Productionda API_DEV_AUTH=0 yoki umuman yozilmasin.
API_DEV_AUTH = os.getenv("API_DEV_AUTH", "0") == "1"

ROLE_USER = "user"
ROLE_STUDENT = "student"
ROLE_TEACHER = "teacher"
ROLE_PENDING_TEACHER = "pending_teacher"
ROLE_REJECTED_TEACHER = "rejected_teacher"
ROLE_ADMIN = "admin"
ROLE_ACCOUNTANT = "accountant"
ROLE_SUPERADMIN = "superadmin"

ALL_ROLES = {
    ROLE_USER,
    ROLE_STUDENT,
    ROLE_TEACHER,
    ROLE_PENDING_TEACHER,
    ROLE_REJECTED_TEACHER,
    ROLE_ADMIN,
    ROLE_ACCOUNTANT,
    ROLE_SUPERADMIN,
}

STAFF_ROLES = {
    ROLE_ADMIN,
    ROLE_ACCOUNTANT,
    ROLE_SUPERADMIN,
}

MANAGEMENT_ROLES = {
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
}

ACCOUNTING_ROLES = {
    ROLE_ACCOUNTANT,
    ROLE_ADMIN,
    ROLE_SUPERADMIN,
}


def _get_bot_token() -> str:
    bot_token = os.getenv("BOT_TOKEN", "").strip()

    if not bot_token:
        raise HTTPException(
            status_code=500,
            detail="BOT_TOKEN server konfiguratsiyasida topilmadi."
        )

    return bot_token


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Telegram Mini App initData ni tekshiradi.

    Frontend quyidagi header orqali yuboradi:
    X-Telegram-Init-Data: window.Telegram.WebApp.initData
    """
    bot_token = _get_bot_token()

    if not init_data:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData yuborilmagan."
        )

    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed_data.pop("hash", None)

    if not received_hash:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData hash topilmadi."
        )

    data_check_string = "\n".join(
        f"{key}={value}"
        for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode("utf-8"),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(
            status_code=401,
            detail="Telegram initData noto'g'ri."
        )

    auth_date_raw = parsed_data.get("auth_date")

    if not auth_date_raw:
        raise HTTPException(
            status_code=401,
            detail="Telegram auth_date topilmadi."
        )

    try:
        auth_date = int(auth_date_raw)
    except ValueError:
        raise HTTPException(
            status_code=401,
            detail="Telegram auth_date noto'g'ri."
        )

    now = int(time.time())

    if auth_date > now + 300:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData vaqti noto'g'ri."
        )

    if now - auth_date > INIT_DATA_MAX_AGE_SECONDS:
        raise HTTPException(
            status_code=401,
            detail="Telegram initData eskirgan."
        )

    user_raw = parsed_data.get("user")

    if not user_raw:
        raise HTTPException(
            status_code=401,
            detail="Telegram user ma'lumoti yo'q."
        )

    try:
        telegram_user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=401,
            detail="Telegram user JSON noto'g'ri."
        )

    telegram_id = telegram_user.get("id")

    if not telegram_id:
        raise HTTPException(
            status_code=401,
            detail="Telegram user ID topilmadi."
        )

    try:
        telegram_id = int(telegram_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=401,
            detail="Telegram user ID noto'g'ri."
        )

    return {
        "telegram_id": telegram_id,
        "telegram_user": telegram_user,
        "raw": parsed_data,
    }


async def get_current_telegram_user(
    x_telegram_init_data: Optional[str] = Header(default=None),
    x_dev_telegram_id: Optional[str] = Header(default=None),
) -> dict:
    """
    Faqat Telegram initData ni tekshiradi.
    Database role tekshirmaydi.

    Local test uchun:
    API_DEV_AUTH=1 bo'lsa, X-Dev-Telegram-Id header ishlaydi.
    Productionda buni yoqmaslik kerak.
    """
    if API_DEV_AUTH and x_dev_telegram_id:
        try:
            telegram_id = int(x_dev_telegram_id)
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="X-Dev-Telegram-Id noto'g'ri."
            )

        return {
            "telegram_id": telegram_id,
            "telegram_user": {
                "id": telegram_id,
                "is_dev_auth": True,
            },
            "raw": {},
        }

    return verify_telegram_init_data(x_telegram_init_data or "")


async def get_current_profile(
    current_user: dict = Depends(get_current_telegram_user)
) -> dict:
    """
    Telegram initData tekshirilgandan keyin userni database'dan oladi.
    """
    telegram_id = current_user["telegram_id"]
    profile = await get_api_user_profile(telegram_id)

    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Foydalanuvchi bazada topilmadi. Avval Telegram bot orqali /start bosing."
        )

    profile_dict = dict(profile)
    role = profile_dict.get("role") or ROLE_USER

    if role not in ALL_ROLES:
        raise HTTPException(
            status_code=403,
            detail=f"Foydalanuvchi roli noto'g'ri: {role}"
        )

    return {
        "telegram_id": telegram_id,
        "telegram_user": current_user["telegram_user"],
        "profile": profile_dict,
        "role": role,
    }


def require_roles(*allowed_roles: str):
    """
    API endpointlarni role bo'yicha himoya qiladi.

    Misol:
    current_user: dict = Depends(require_roles("admin", "superadmin"))
    """
    if not allowed_roles:
        raise RuntimeError("require_roles kamida bitta role qabul qilishi kerak.")

    unknown_roles = set(allowed_roles) - ALL_ROLES

    if unknown_roles:
        raise RuntimeError(f"Noto'g'ri role berilgan: {', '.join(sorted(unknown_roles))}")

    async def checker(
        current_profile: dict = Depends(get_current_profile)
    ) -> dict:
        role = current_profile["role"]

        if role not in allowed_roles:
            raise HTTPException(
                status_code=403,
                detail="Bu bo'limga kirish uchun ruxsat yo'q."
            )

        return current_profile

    return checker


# Qulay dependency aliaslar.
# Xohlasang endpointlarda require_roles(...) o'rniga shularni ham ishlatamiz.

def require_user():
    return require_roles(
        ROLE_USER,
        ROLE_STUDENT,
        ROLE_TEACHER,
        ROLE_PENDING_TEACHER,
        ROLE_REJECTED_TEACHER,
        ROLE_ADMIN,
        ROLE_ACCOUNTANT,
        ROLE_SUPERADMIN,
    )


def require_student():
    return require_roles(ROLE_STUDENT)


def require_teacher():
    return require_roles(ROLE_TEACHER)


def require_admin():
    return require_roles(ROLE_ADMIN, ROLE_SUPERADMIN)


def require_superadmin():
    return require_roles(ROLE_SUPERADMIN)


def require_accountant():
    return require_roles(ROLE_ACCOUNTANT, ROLE_SUPERADMIN)


def require_accounting_access():
    return require_roles(ROLE_ACCOUNTANT, ROLE_ADMIN, ROLE_SUPERADMIN)


def require_management_access():
    return require_roles(ROLE_ADMIN, ROLE_SUPERADMIN)