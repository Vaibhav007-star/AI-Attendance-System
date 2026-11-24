from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.attendance import router as attendance_router
from app.api.v1.recognition import router as recognition_router
from app.api.v1.dashboard import router as dashboard_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
api_v1_router.include_router(attendance_router)
api_v1_router.include_router(recognition_router)
api_v1_router.include_router(dashboard_router)
