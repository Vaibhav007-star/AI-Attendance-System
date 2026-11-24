from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class DashboardStats(BaseModel):
    total_employees: int
    present_today: int
    on_time_today: int
    late_today: int
    absent_today: int
    attendance_rate: float
    recent_logs: List[Any]
    department_distribution: Dict[str, int]
    hourly_arrivals: Dict[str, int]

class VerificationResponse(BaseModel):
    matched: bool
    user_id: Optional[int] = None
    employee_id: Optional[str] = None
    full_name: Optional[str] = None
    department: Optional[str] = None
    confidence: float
    liveness_score: float
    is_live: bool
    action: Optional[str] = None  # "checked_in", "checked_out", "cooldown", "rejected"
    message: str
