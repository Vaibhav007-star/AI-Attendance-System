"""
Comprehensive Automated Test Suite for VisionAttend AI
Validates database, face engine, anti-spoofing, attendance rules, and API endpoints.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import cv2
import numpy as np
from datetime import date, datetime
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import SessionLocal
from app.models.user import User
from app.models.department import Department
from app.models.attendance import AttendanceLog
from app.services.face_engine import face_engine
from app.services.liveness_detector import liveness_detector
from app.services.attendance_service import attendance_service
from app.services.export_service import export_service

client = TestClient(app)

def test_health_and_index():
    res = client.get("/")
    assert res.status_code in [200, 307]

def test_api_departments():
    res = client.get("/api/v1/users/departments")
    assert res.status_code == 200
    depts = res.json()
    assert len(depts) >= 4
    names = [d["name"] for d in depts]
    assert "Artificial Intelligence" in names

def test_api_users():
    res = client.get("/api/v1/users")
    assert res.status_code == 200
    users = res.json()
    assert len(users) >= 1
    admin = next(u for u in users if u["email"] == "admin@visionattend.ai")
    assert admin["role"] == "admin"

def test_liveness_engine():
    # Test real-like synthetic textured face image
    real_crop = np.random.randint(50, 220, (112, 112, 3), dtype=np.uint8)
    cv2.circle(real_crop, (56, 56), 40, (150, 150, 180), -1)
    res_real = liveness_detector.evaluate(real_crop)
    assert "score" in res_real
    assert "metrics" in res_real

    # Test blank/zero-texture attack image (flat gray / blank paper)
    blank_crop = np.full((112, 112, 3), 128, dtype=np.uint8)
    res_blank = liveness_detector.evaluate(blank_crop)
    assert res_blank["is_live"] is False

def test_face_engine_embeddings():
    dummy_face = np.random.randint(0, 255, (112, 112, 3), dtype=np.uint8)
    vec = face_engine.extract_embedding(dummy_face)
    assert len(vec) == 128
    norm = np.linalg.norm(vec)
    assert 0.98 <= norm <= 1.02  # Unit length vector

    sim_self = face_engine.cosine_similarity(vec, vec)
    assert round(sim_self, 2) == 1.00

def test_attendance_state_machine():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.employee_id == "VA-101").first()
        assert user is not None

        # Clean existing log for today to test cleanly
        db.query(AttendanceLog).filter(
            AttendanceLog.user_id == user.id,
            AttendanceLog.log_date == date.today()
        ).delete()
        db.commit()

        # 1. First scan -> Check-In
        res1 = attendance_service.record_attendance(db, user.id, confidence=0.95)
        assert res1["success"] is True
        assert res1["action"] == "checked_in"

        # 2. Immediate second scan -> Cooldown active
        res2 = attendance_service.record_attendance(db, user.id, confidence=0.96)
        assert res2["success"] is True
        assert res2["action"] == "cooldown"

    finally:
        db.close()

def test_export_service():
    db = SessionLocal()
    try:
        logs = db.query(AttendanceLog).all()
        csv_out = export_service.generate_csv(logs)
        assert "Employee ID" in csv_out
        assert "Status" in csv_out

        excel_stream = export_service.generate_excel(logs)
        assert excel_stream.getbuffer().nbytes > 1000
    finally:
        db.close()

def test_dashboard_stats_endpoint():
    res = client.get("/api/v1/dashboard/stats")
    assert res.status_code == 200
    stats = res.json()
    assert "total_employees" in stats
    assert "present_today" in stats
    assert "hourly_arrivals" in stats
    assert "department_distribution" in stats
    assert stats["total_employees"] >= 4

if __name__ == "__main__":
    print("[*] Running VisionAttend AI automated tests...")
    test_health_and_index()
    print(" -> Health & Index: PASS")
    test_api_departments()
    print(" -> Departments API: PASS")
    test_api_users()
    print(" -> Users API: PASS")
    test_liveness_engine()
    print(" -> Anti-Spoofing & Liveness: PASS")
    test_face_engine_embeddings()
    print(" -> Face Embeddings & Cosine Similarity: PASS")
    test_attendance_state_machine()
    print(" -> Attendance State Machine & Cooldown: PASS")
    test_export_service()
    print(" -> CSV & Excel Export Generator: PASS")
    test_dashboard_stats_endpoint()
    print(" -> Dashboard Stats Analytics: PASS")
    print("\n[SUCCESS] All 8 test suites passed with 100% success!")
