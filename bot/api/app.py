# api/app.py
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes_common import router as common_router
from api.routes_student import router as student_router
from api.routes_teacher import router as teacher_router
from api.routes_admin import router as admin_router
from api.routes_superadmin import router as superadmin_router

app = FastAPI(
    title="Visa Consulting Mini App API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("media/lessons", exist_ok=True)

app.mount(
    "/media/lessons",
    StaticFiles(directory="media/lessons"),
    name="lesson_media"
)

app.include_router(common_router)
app.include_router(student_router)
app.include_router(teacher_router)
app.include_router(admin_router)
app.include_router(superadmin_router)