# api/app.py
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes_common import router as common_router
from api.routes_student import router as student_router
from api.routes_teacher import router as teacher_router
from api.routes_admin import router as admin_router
from api.routes_superadmin import router as superadmin_router
from api.routes_accounting import router as accounting_router

BASE_DIR = Path(__file__).resolve().parent.parent
MEDIA_DIR = BASE_DIR / "media"
LESSONS_DIR = MEDIA_DIR / "lessons"
RECEIPTS_DIR = MEDIA_DIR / "receipts"

LESSONS_DIR.mkdir(parents=True, exist_ok=True)
RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def get_cors_origins():
    """
    .env ichida API_CORS_ORIGINS bo'lsa:
    API_CORS_ORIGINS=https://example.com,https://another.com

    Developmentda bo'lmasa hammasiga ruxsat beradi.
    """
    raw = os.getenv("API_CORS_ORIGINS", "").strip()

    if not raw:
        return ["*"]

    return [item.strip() for item in raw.split(",") if item.strip()]


app = FastAPI(
    title="Visa Consulting Mini App API",
    version="1.1.0"
)

cors_origins = get_cors_origins()

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dars materiallari Mini App ichida ko'rinishi uchun.
app.mount(
    "/media/lessons",
    StaticFiles(directory=str(LESSONS_DIR)),
    name="lesson_media"
)

# Cheklar accounting dashboardda ko'rinishi uchun.
# Keyin xohlasak buni protected endpointga o'tkazamiz.
app.mount(
    "/media/receipts",
    StaticFiles(directory=str(RECEIPTS_DIR)),
    name="receipt_media"
)

app.include_router(common_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(admin_router)
app.include_router(accounting_router)
app.include_router(superadmin_router)