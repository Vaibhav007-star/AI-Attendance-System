from datetime import date, datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.models.attendance import AttendanceLog
from app.models.user import User
from app.schemas.attendance import AttendanceOut, AttendanceCreate
from app.services.attendance_service import attendance_service
from app.services.export_service import export_service

router = APIRouter(prefix="/attendance", tags=["Attendance Management"])

@router.get("/logs", response_model=List[AttendanceOut])
def list_attendance_logs(
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
    department_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    limit: int = 200,
    skip: int = 0,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceLog).join(User)

    if start_date:
        query = query.filter(AttendanceLog.log_date >= start_date)
    if end_date:
        query = query.filter(AttendanceLog.log_date <= end_date)
    if department_id:
        query = query.filter(User.department_id == department_id)
    if status:
        query = query.filter(AttendanceLog.status == status)
    if user_id:
        query = query.filter(AttendanceLog.user_id == user_id)

    logs = query.order_by(AttendanceLog.check_in.desc()).offset(skip).limit(limit).all()
    return logs

@router.post("/record", response_model=AttendanceOut)
def record_manual_attendance(
    payload: AttendanceCreate,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == payload.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    res = attendance_service.record_attendance(
        db=db,
        user_id=payload.user_id,
        confidence=payload.match_confidence or 1.0,
        liveness_score=payload.liveness_score or 1.0,
        verification_method=payload.verification_method or "Manual-Admin",
        notes=payload.notes
    )

    log = db.query(AttendanceLog).filter(
        AttendanceLog.user_id == payload.user_id,
        AttendanceLog.log_date == date.today()
    ).first()

    return log

@router.get("/export/csv")
def export_csv(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceLog).join(User)
    if start_date:
        query = query.filter(AttendanceLog.log_date >= start_date)
    if end_date:
        query = query.filter(AttendanceLog.log_date <= end_date)

    logs = query.order_by(AttendanceLog.check_in.desc()).all()
    csv_data = export_service.generate_csv(logs)

    filename = f"attendance_report_{date.today().isoformat()}.csv"
    return Response(
        content=csv_data,
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/export/excel")
def export_excel(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    db: Session = Depends(get_db)
):
    query = db.query(AttendanceLog).join(User)
    if start_date:
        query = query.filter(AttendanceLog.log_date >= start_date)
    if end_date:
        query = query.filter(AttendanceLog.log_date <= end_date)

    logs = query.order_by(AttendanceLog.check_in.desc()).all()
    stream = export_service.generate_excel(logs)

    filename = f"attendance_report_{date.today().isoformat()}.xlsx"
    return Response(
        content=stream.getvalue(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
