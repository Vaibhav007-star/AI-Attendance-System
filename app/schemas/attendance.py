from datetime import datetime, date
from typing import Optional
from pydantic import BaseModel
from app.schemas.user import UserOut

class AttendanceCreate(BaseModel):
    user_id: int
    verification_method: Optional[str] = "Face-AI"
    match_confidence: Optional[float] = 1.0
    liveness_score: Optional[float] = 1.0
    notes: Optional[str] = None

class AttendanceOut(BaseModel):
    id: int
    user_id: int
    log_date: date
    check_in: datetime
    check_out: Optional[datetime] = None
    status: str
    match_confidence: float
    liveness_score: float
    verification_method: str
    snapshot_path: Optional[str] = None
    notes: Optional[str] = None
    user: Optional[UserOut] = None

    class Config:
        from_attributes = True

class AttendanceFilter(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    department_id: Optional[int] = None
    status: Optional[str] = None
    user_id: Optional[int] = None
