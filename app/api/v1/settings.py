from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.config import settings
from app.api.deps import require_admin
from app.services.face_engine import face_engine
from app.services.liveness_detector import liveness_detector

router = APIRouter(prefix="/settings", tags=["System Settings"])

class SystemSettingsSchema(BaseModel):
    office_start_time: str = Field(default="09:00:00", description="Expected arrival time (HH:MM:SS)")
    office_late_threshold: str = Field(default="09:30:00", description="Late mark threshold (HH:MM:SS)")
    office_end_time: str = Field(default="18:00:00", description="Shift end time (HH:MM:SS)")
    attendance_cooldown_minutes: int = Field(default=5, ge=1, le=60, description="Cooldown before allowing re-scan")
    face_recognition_threshold: float = Field(default=0.58, ge=0.40, le=0.90, description="Cosine similarity threshold")
    face_detection_confidence: float = Field(default=0.70, ge=0.40, le=0.95, description="Detector confidence threshold")
    liveness_detection_enabled: bool = Field(default=True, description="Enable anti-spoofing defense")
    liveness_threshold: float = Field(default=0.60, ge=0.30, le=0.90, description="Minimum liveness score")
    auto_checkout_enabled: bool = Field(default=True, description="Allow auto check-out on subsequent scans")
    kiosk_sound_enabled: bool = Field(default=True, description="Enable Web Audio feedback on kiosk")

@router.get("", response_model=SystemSettingsSchema)
def get_current_settings():
    return SystemSettingsSchema(
        office_start_time=settings.OFFICE_START_TIME,
        office_late_threshold=settings.OFFICE_LATE_THRESHOLD,
        office_end_time=settings.OFFICE_END_TIME,
        attendance_cooldown_minutes=settings.ATTENDANCE_COOLDOWN_MINUTES,
        face_recognition_threshold=settings.FACE_RECOGNITION_THRESHOLD,
        face_detection_confidence=settings.FACE_DETECTION_CONFIDENCE,
        liveness_detection_enabled=settings.LIVENESS_DETECTION_ENABLED,
        liveness_threshold=settings.LIVENESS_THRESHOLD,
        auto_checkout_enabled=settings.AUTO_CHECKOUT_ENABLED,
        kiosk_sound_enabled=True
    )

@router.post("", response_model=SystemSettingsSchema)
def update_settings(payload: SystemSettingsSchema):
    settings.OFFICE_START_TIME = payload.office_start_time
    settings.OFFICE_LATE_THRESHOLD = payload.office_late_threshold
    settings.OFFICE_END_TIME = payload.office_end_time
    settings.ATTENDANCE_COOLDOWN_MINUTES = payload.attendance_cooldown_minutes
    settings.FACE_RECOGNITION_THRESHOLD = payload.face_recognition_threshold
    settings.FACE_DETECTION_CONFIDENCE = payload.face_detection_confidence
    settings.LIVENESS_DETECTION_ENABLED = payload.liveness_detection_enabled
    settings.LIVENESS_THRESHOLD = payload.liveness_threshold
    settings.AUTO_CHECKOUT_ENABLED = payload.auto_checkout_enabled

    # Sync with runtime detectors
    if face_engine.detector is not None:
        try:
            face_engine.detector.setScoreThreshold(payload.face_detection_confidence)
        except Exception:
            pass

    return payload
