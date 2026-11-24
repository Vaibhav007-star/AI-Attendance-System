from datetime import datetime, date
from sqlalchemy import Column, Integer, String, Float, DateTime, Date, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

class AttendanceLog(Base):
    __tablename__ = "attendance_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    log_date = Column(Date, default=date.today, index=True)
    check_in = Column(DateTime, default=datetime.utcnow)
    check_out = Column(DateTime, nullable=True)
    # Status: 'On-Time', 'Late', 'Half-Day', 'Overtime', 'Early-Departure'
    status = Column(String(50), default="On-Time")
    match_confidence = Column(Float, default=1.0)
    liveness_score = Column(Float, default=1.0)
    verification_method = Column(String(50), default="Face-AI")  # Face-AI, Kiosk, Manual-Admin
    snapshot_path = Column(String(255), nullable=True)
    ip_address = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)

    user = relationship("User", back_populates="attendance_logs")
