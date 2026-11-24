from datetime import date
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.api.deps import get_db
from app.models.user import User
from app.models.department import Department
from app.models.attendance import AttendanceLog
from app.schemas.dashboard import DashboardStats

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Analytics"])

@router.get("/stats", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    today = date.today()

    total_employees = db.query(User).filter(User.is_active == True).count()
    today_logs = db.query(AttendanceLog).filter(AttendanceLog.log_date == today).all()

    present_today = len(today_logs)
    on_time_today = sum(1 for log in today_logs if log.status == "On-Time")
    late_today = sum(1 for log in today_logs if log.status == "Late")
    absent_today = max(0, total_employees - present_today)

    attendance_rate = round((present_today / total_employees * 100.0), 1) if total_employees > 0 else 0.0

    # Hourly arrivals curve
    hourly_arrivals = defaultdict(int)
    for h in range(7, 20):
        hourly_arrivals[f"{h:02d}:00"] = 0

    for log in today_logs:
        if log.check_in:
            hour_str = f"{log.check_in.hour:02d}:00"
            hourly_arrivals[hour_str] += 1

    # Department distribution of present users
    dept_distribution = defaultdict(int)
    for log in today_logs:
        dept_name = log.user.department.name if log.user and log.user.department else "General"
        dept_distribution[dept_name] += 1

    # Recent 10 logs with employee name
    recent_logs = []
    for log in sorted(today_logs, key=lambda l: l.check_in or datetime.min, reverse=True)[:10]:
        recent_logs.append({
            "id": log.id,
            "employee_id": log.user.employee_id if log.user else "N/A",
            "full_name": log.user.full_name if log.user else "Unknown",
            "department": log.user.department.name if log.user and log.user.department else "General",
            "avatar_path": log.user.avatar_path if log.user else None,
            "check_in": log.check_in.strftime("%H:%M:%S") if log.check_in else "-",
            "check_out": log.check_out.strftime("%H:%M:%S") if log.check_out else "-",
            "status": log.status,
            "confidence": round(log.match_confidence * 100, 1),
            "snapshot_path": log.snapshot_path
        })

    return DashboardStats(
        total_employees=total_employees,
        present_today=present_today,
        on_time_today=on_time_today,
        late_today=late_today,
        absent_today=absent_today,
        attendance_rate=attendance_rate,
        recent_logs=recent_logs,
        department_distribution=dict(dept_distribution),
        hourly_arrivals=dict(sorted(hourly_arrivals.items()))
    )
