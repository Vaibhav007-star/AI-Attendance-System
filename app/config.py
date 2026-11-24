import os
from pathlib import Path
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    APP_NAME: str = "VisionAttend AI - Enterprise Face Attendance System"
    APP_ENV: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    SECRET_KEY: str = "super-secret-visionattend-key-change-in-production-2026-xyz"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    DATABASE_URL: str = f"sqlite:///{BASE_DIR / 'data' / 'attendance.db'}"

    FACE_DETECTION_CONFIDENCE: float = 0.70
    FACE_RECOGNITION_THRESHOLD: float = 0.58
    LIVENESS_DETECTION_ENABLED: bool = True
    LIVENESS_THRESHOLD: float = 0.60
    ANTI_SPOOF_METHOD: str = "frequency_and_motion"

    ATTENDANCE_COOLDOWN_MINUTES: int = 5
    OFFICE_START_TIME: str = "09:00:00"
    OFFICE_LATE_THRESHOLD: str = "09:30:00"
    OFFICE_END_TIME: str = "18:00:00"
    AUTO_CHECKOUT_ENABLED: bool = True

    DATA_DIR: Path = BASE_DIR / "data"
    FACES_DIR: Path = BASE_DIR / "storage" / "faces"
    EXPORTS_DIR: Path = BASE_DIR / "storage" / "exports"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

# Ensure directories exist
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
settings.FACES_DIR.mkdir(parents=True, exist_ok=True)
settings.EXPORTS_DIR.mkdir(parents=True, exist_ok=True)
