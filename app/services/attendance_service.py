import os
import cv2
import uuid
from datetime import datetime, date, time
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.attendance import AttendanceLog

class AttendanceService:
    """
    Intelligent Attendance State Machine:
    - Auto Check-In & Check-Out
    - Anti-Passback & Cooldown Prevention
    - Punctuality & Late Detection against office hours
    - Biometric Evidence Snapshot Archiving
    """

    @staticmethod
    def get_office_hours():
        try:
            start_parts = [int(p) for p in settings.OFFICE_START_TIME.split(":")]
            late_parts = [int(p) for p in settings.OFFICE_LATE_THRESHOLD.split(":")]
            start_t = time(start_parts[0], start_parts[1], start_parts[2] if len(start_parts) > 2 else 0)
            late_t = time(late_parts[0], late_parts[1], late_parts[2] if len(late_parts) > 2 else 0)
            return start_t, late_t
        except Exception:
            return time(9, 0), time(9, 30)

    @classmethod
    def save_snapshot(cls, frame_crop: Optional[Any]) -> Optional[str]:
        if frame_crop is None or frame_crop.size == 0:
            return None
        try:
            snapshots_dir = settings.FACES_DIR / "snapshots"
            snapshots_dir.mkdir(parents=True, exist_ok=True)
            filename = f"att_{date.today().isoformat()}_{uuid.uuid4().hex[:8]}.jpg"
            filepath = snapshots_dir / filename
            cv2.imwrite(str(filepath), frame_crop)
            return f"/static/faces/snapshots/{filename}"
        except Exception:
            return None

    @classmethod
    def record_attendance(
        cls,
        db: Session,
        user_id: int,
        confidence: float = 1.0,
        liveness_score: float = 1.0,
        verification_method: str = "Face-AI",
        face_crop: Optional[Any] = None,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
        if not user:
            return {"success": False, "action": "rejected", "message": "User not found or inactive"}

        today = date.today()
        now = datetime.utcnow()
        now_time = now.time()

        # Check existing log for today
        existing_log = db.query(AttendanceLog).filter(
            AttendanceLog.user_id == user_id,
            AttendanceLog.log_date == today
        ).first()

        snapshot_url = cls.save_snapshot(face_crop) if face_crop is not None else None

        if existing_log is None:
            # First scan of the day -> Check-In!
            _, late_thresh = cls.get_office_hours()
            status_label = "Late" if now_time > late_thresh else "On-Time"

            new_log = AttendanceLog(
                user_id=user_id,
                log_date=today,
                check_in=now,
                status=status_label,
                match_confidence=confidence,
                liveness_score=liveness_score,
                verification_method=verification_method,
                snapshot_path=snapshot_url,
                notes=notes
            )
            db.add(new_log)
            db.commit()
            db.refresh(new_log)

            return {
                "success": True,
                "action": "checked_in",
                "status": status_label,
                "time": now.strftime("%H:%M:%S"),
                "user_name": user.full_name,
                "message": f"Welcome, {user.full_name}! Check-in recorded ({status_label})."
            }

        # User has already checked in today. Check cooldown.
        last_action_time = existing_log.check_out if existing_log.check_out else existing_log.check_in
        time_diff = (now - last_action_time).total_seconds() / 60.0

        if time_diff < settings.ATTENDANCE_COOLDOWN_MINUTES:
            return {
                "success": True,
                "action": "cooldown",
                "status": existing_log.status,
                "time": last_action_time.strftime("%H:%M:%S"),
                "user_name": user.full_name,
                "message": f"Scan acknowledged, {user.full_name}. Cooldown active ({int(settings.ATTENDANCE_COOLDOWN_MINUTES - time_diff)}m remaining)."
            }

        # Cooldown passed -> Record Check-Out!
        existing_log.check_out = now
        if snapshot_url:
            existing_log.snapshot_path = snapshot_url
        if notes:
            existing_log.notes = f"{existing_log.notes or ''}; {notes}".strip("; ")

        db.commit()
        db.refresh(existing_log)

        return {
            "success": True,
            "action": "checked_out",
            "status": existing_log.status,
            "time": now.strftime("%H:%M:%S"),
            "user_name": user.full_name,
            "message": f"Goodbye, {user.full_name}! Check-out recorded at {now.strftime('%H:%M:%S')}."
        }

attendance_service = AttendanceService()
