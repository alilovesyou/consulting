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

INIT_DATA_MAX_AGE_SECONDS = 60 * 60 * 24 * 7  # 7 kun


def verify_telegram_init_data(init_data: str) -> dict:
    """
    Telegram Mini App initData ni tekshiradi.

    Frontend header orqali yuboradi:
    X-Telegram-Init-Data: window.Telegram.WebApp.initData
    """
    bot_token = os.getenv("BOT_TOKEN")

    if not bot_token:
        raise HTTPException(status_code=500, detail="BOT_TOKEN topilmadi.")

    if not init_data:
        raise HTTPException(status_code=401, detail="Telegram initData yuborilmagan.")

    parsed_data = dict(parse_qsl(init_data, keep_blank_values=True))
    received_hash = parsed_data.pop("hash", None)

    if not received_hash:
        raise HTTPException(status_code=401, detail="Telegram initData hash topilmadi.")

    data_check_string = "\n".join(
        f"{key}={value}" for key, value in sorted(parsed_data.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        bot_token.encode(),
        hashlib.sha256
    ).digest()

    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        raise HTTPException(status_code=401, detail="Telegram initData noto'g'ri.")

    auth_date_raw = parsed_data.get("auth_date")

    if auth_date_raw:
        try:
            auth_date = int(auth_date_raw)
        except ValueError:
            raise HTTPException(status_code=401, detail="auth_date noto'g'ri.")

        if time.time() - auth_date > INIT_DATA_MAX_AGE_SECONDS:
            raise HTTPException(status_code=401, detail="Telegram initData eskirgan.")

    user_raw = parsed_data.get("user")

    if not user_raw:
        raise HTTPException(status_code=401, detail="Telegram user ma'lumoti yo'q.")

    try:
        user = json.loads(user_raw)
    except json.JSONDecodeError:
        raise HTTPException(status_code=401, detail="Telegram user JSON noto'g'ri.")

    if "id" not in user:
        raise HTTPException(status_code=401, detail="Telegram user ID topilmadi.")

    return {
        "telegram_id": int(user["id"]),
        "telegram_user": user,
        "raw": parsed_data
    }


async def get_current_telegram_user(
    x_telegram_init_data: Optional[str] = Header(default=None)
) -> dict:
    """
    Faqat Telegram initData ni tekshiradi.
    Database role tekshirmaydi.
    """
    return verify_telegram_init_data(x_telegram_init_data)


async def get_current_profile(
    current_user: dict = Depends(get_current_telegram_user)
) -> dict:
    """
    Telegram initData tekshirilgandan keyin userni database'dan oladi.
    """
    telegram_id = current_user["telegram_id"]
    profile = await get_api_user_profile(telegram_id)

    if not profile:
        raise HTTPException(status_code=404, detail="Foydalanuvchi bazada topilmadi.")

    return {
        "telegram_id": telegram_id,
        "telegram_user": current_user["telegram_user"],
        "profile": dict(profile),
        "role": profile["role"] or "user"
    }


def require_roles(*allowed_roles: str):
    """
    API endpointlarni role bo'yicha himoya qiladi.

    Misol:
    current_user: dict = Depends(require_roles("admin", "superadmin"))
    """
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