"""
VisionAttend AI - Enterprise Realistic Data Generator (Expanded Edition)
Populates 25 employees across 6 departments with 600+ historical & today's
attendance records spanning the past 30 days for LinkedIn showcase demos.
"""

import os
import random
from datetime import datetime, date, time, timedelta
from pathlib import Path
import numpy as np
import cv2

from app.core.database import SessionLocal, init_db
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User
from app.models.biometric import BiometricProfile
from app.models.attendance import AttendanceLog
from app.services.face_engine import face_engine
from app.config import settings

DEPARTMENTS = [
    {"name": "AI & Computer Vision Lab", "code": "AICV", "manager": "Dr. Aris Thorne"},
    {"name": "Cloud Infrastructure & SRE", "code": "CLD", "manager": "Marcus Sterling"},
    {"name": "Product Design & UX", "code": "UXD", "manager": "Elena Rostova"},
    {"name": "Cybersecurity & Zero Trust", "code": "SEC", "manager": "Dante Vance"},
    {"name": "People Operations & HR", "code": "HR", "manager": "Sarah Connor"},
    {"name": "Enterprise Strategic Sales", "code": "SALES", "manager": "Devon Blake"}
]

EMPLOYEES = [
    # AICV
    {"name": "Dr. Aris Thorne", "emp_id": "VA-101", "role": "admin", "dept": 0, "designation": "VP of Artificial Intelligence", "gender": "m"},
    {"name": "Dr. Sophia Chen", "emp_id": "VA-102", "role": "employee", "dept": 0, "designation": "Principal Computer Vision Scientist", "gender": "f"},
    {"name": "Lucas Meyer", "emp_id": "VA-103", "role": "employee", "dept": 0, "designation": "Senior Deep Learning Engineer", "gender": "m"},
    {"name": "Aria Montgomery", "emp_id": "VA-104", "role": "employee", "dept": 0, "designation": "Neural Network Optimization Lead", "gender": "f"},
    {"name": "Rohan Deshmukh", "emp_id": "VA-105", "role": "employee", "dept": 0, "designation": "Edge AI Systems Architect", "gender": "m"},

    # Cloud & SRE
    {"name": "Marcus Sterling", "emp_id": "VA-106", "role": "employee", "dept": 1, "designation": "Director of Cloud Infrastructure", "gender": "m"},
    {"name": "Freja Lindqvist", "emp_id": "VA-107", "role": "employee", "dept": 1, "designation": "Principal SRE & DevOps Lead", "gender": "f"},
    {"name": "Alexander Vance", "emp_id": "VA-108", "role": "employee", "dept": 1, "designation": "Distributed Systems Engineer", "gender": "m"},
    {"name": "Chloe Dupont", "emp_id": "VA-109", "role": "employee", "dept": 1, "designation": "Kubernetes Platform Specialist", "gender": "f"},

    # Product Design & UX
    {"name": "Elena Rostova", "emp_id": "VA-110", "role": "employee", "dept": 2, "designation": "Chief Design Officer", "gender": "f"},
    {"name": "Julian Vega", "emp_id": "VA-111", "role": "employee", "dept": 2, "designation": "Lead Glassmorphism UX Architect", "gender": "m"},
    {"name": "Maya Patel", "emp_id": "VA-112", "role": "employee", "dept": 2, "designation": "Senior Motion & Interaction Designer", "gender": "f"},
    {"name": "Oliver Quinn", "emp_id": "VA-113", "role": "employee", "dept": 2, "designation": "Product Strategy Lead", "gender": "m"},

    # Cybersecurity & Zero Trust
    {"name": "Dante Vance", "emp_id": "VA-114", "role": "employee", "dept": 3, "designation": "Head of Biometric Security & CISO", "gender": "m"},
    {"name": "Katarina Volkova", "emp_id": "VA-115", "role": "employee", "dept": 3, "designation": "Zero Trust Threat Intelligence Lead", "gender": "f"},
    {"name": "Nathaniel Drake", "emp_id": "VA-116", "role": "employee", "dept": 3, "designation": "Senior Cryptographic Security Analyst", "gender": "m"},

    # HR & People Ops
    {"name": "Sarah Connor", "emp_id": "VA-117", "role": "employee", "dept": 4, "designation": "VP of People Operations", "gender": "f"},
    {"name": "Ethan Caldwell", "emp_id": "VA-118", "role": "employee", "dept": 4, "designation": "Global Talent Acquisition Lead", "gender": "m"},
    {"name": "Zoe Kravitz", "emp_id": "VA-119", "role": "employee", "dept": 4, "designation": "Workforce Experience Specialist", "gender": "f"},

    # Sales & Enterprise
    {"name": "Devon Blake", "emp_id": "VA-120", "role": "employee", "dept": 5, "designation": "VP of Enterprise Partnerships", "gender": "m"},
    {"name": "Samantha Reed", "emp_id": "VA-121", "role": "employee", "dept": 5, "designation": "Global Accounts Director", "gender": "f"},
    {"name": "Leo Takahashi", "emp_id": "VA-122", "role": "employee", "dept": 5, "designation": "Strategic Enterprise Solutions Lead", "gender": "m"},
    {"name": "Isabella Morales", "emp_id": "VA-123", "role": "employee", "dept": 5, "designation": "Client Success Executive", "gender": "f"},
    {"name": "Gavin MacLeod", "emp_id": "VA-124", "role": "employee", "dept": 5, "designation": "Enterprise Sales Representative", "gender": "m"}
]

def generate_avatar_image(emp_id: str, name: str, dept_name: str, gender: str) -> str:
    size = (160, 160)
    img = np.zeros((size[1], size[0], 3), dtype=np.uint8)

    h_val = abs(hash(emp_id)) % 360
    c1 = (int((h_val * 0.7) % 180 + 30), 40, int((h_val * 1.2) % 100 + 40))
    c2 = (15, 23, 42)

    for y in range(size[1]):
        ratio = y / size[1]
        b = int(c1[0] * (1 - ratio) + c2[0] * ratio)
        g = int(c1[1] * (1 - ratio) + c2[1] * ratio)
        r = int(c1[2] * (1 - ratio) + c2[2] * ratio)
        img[y, :] = (b, g, r)

    center = (size[0] // 2, size[1] // 2 - 6)
    cv2.circle(img, center, 44, (0, 242, 254), 1)
    cv2.circle(img, center, 40, (25, 35, 60), -1)

    initials = "".join([part[0] for part in name.replace("Dr. ", "").split()[:2]]).upper()
    font = cv2.FONT_HERSHEY_DUPLEX
    text_size = cv2.getTextSize(initials, font, 1.0, 2)[0]
    tx = (size[0] - text_size[0]) // 2
    ty = (size[1] + text_size[1]) // 2 - 6
    cv2.putText(img, initials, (tx, ty), font, 1.0, (0, 242, 254), 2, cv2.LINE_AA)

    cv2.rectangle(img, (0, size[1] - 26), (size[0], size[1]), (10, 15, 28), -1)
    sub_font = cv2.FONT_HERSHEY_SIMPLEX
    sub_size = cv2.getTextSize(emp_id, sub_font, 0.38, 1)[0]
    cv2.putText(img, emp_id, ((size[0] - sub_size[0]) // 2, size[1] - 8), sub_font, 0.38, (180, 200, 220), 1, cv2.LINE_AA)

    avatar_path = settings.FACES_DIR / f"{emp_id}.jpg"
    cv2.imwrite(str(avatar_path), img)
    return f"/static/faces/{emp_id}.jpg"

def generate_random_biometric_vector(seed_str: str) -> np.ndarray:
    seed = abs(hash(seed_str)) % (2**31 - 1)
    rng = np.random.RandomState(seed)
    vec = rng.randn(128).astype(np.float32)
    norm = np.linalg.norm(vec)
    if norm > 0:
        vec = vec / norm
    return vec

def seed_enterprise_data(days_history: int = 35):
    print("=" * 65)
    print(f" 🚀 Seeding VisionAttend AI Expanded Dataset ({days_history} Days History)")
    print("=" * 65)

    init_db()
    db = SessionLocal()

    try:
        # Clear existing logs for fresh generation
        db.query(AttendanceLog).delete()
        db.query(BiometricProfile).delete()
        db.query(User).delete()
        db.query(Department).delete()
        db.commit()

        # 1. Create Departments
        dept_objects = []
        for d in DEPARTMENTS:
            dept = Department(name=d["name"], code=d["code"], manager_name=d["manager"])
            db.add(dept)
            dept_objects.append(dept)
        db.commit()
        for d in dept_objects:
            db.refresh(d)
        print(f"[OK] Created {len(dept_objects)} departments.")

        # 2. Create Administrator Account
        admin_avatar = generate_avatar_image("VA-001", "VisionAttend Admin", "AICV", "m")
        admin = User(
            employee_id="VA-001",
            full_name="VisionAttend Administrator",
            email="admin@visionattend.ai",
            hashed_password=get_password_hash("Admin@123"),
            phone="+1-555-0199",
            designation="Chief System Administrator",
            role="admin",
            department_id=dept_objects[0].id,
            avatar_path=admin_avatar,
            is_active=True
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

        admin_vec = generate_random_biometric_vector("admin-001")
        bio_admin = BiometricProfile(
            user_id=admin.id,
            embeddings_json="",
            sample_count=4,
            quality_score=0.985,
            encoding_version="sface_v1"
        )
        bio_admin.set_embeddings([admin_vec.tolist()])
        db.add(bio_admin)

        # 3. Create Employees
        user_objects = [admin]
        for emp in EMPLOYEES:
            first_name = emp["name"].replace("Dr. ", "").split()[0].lower()
            last_name = emp["name"].split()[-1].lower()
            email = f"{first_name}.{last_name}@visionattend.ai"

            avatar_url = generate_avatar_image(emp["emp_id"], emp["name"], DEPARTMENTS[emp["dept"]]["name"], emp["gender"])

            user = User(
                employee_id=emp["emp_id"],
                full_name=emp["name"],
                email=email,
                hashed_password=get_password_hash("Welcome@123"),
                phone=f"+1-555-{random.randint(1000, 9999)}",
                designation=emp["designation"],
                role=emp["role"],
                department_id=dept_objects[emp["dept"]].id,
                avatar_path=avatar_url,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            user_objects.append(user)

            u_vec = generate_random_biometric_vector(emp["emp_id"])
            bio = BiometricProfile(
                user_id=user.id,
                embeddings_json="",
                sample_count=random.randint(3, 5),
                quality_score=round(random.uniform(0.93, 0.99), 3),
                encoding_version="sface_v1"
            )
            bio.set_embeddings([u_vec.tolist(), (u_vec * 0.99 + 0.01).tolist()])
            db.add(bio)

        db.commit()
        print(f"[OK] Enrolled {len(user_objects)} staff members with biometric profiles.")

        # 4. Generate Comprehensive Multi-Week Attendance History (35 Days)
        today = date.today()
        total_historical = 0

        verification_methods = ["Face-AI Kiosk-01", "Face-AI Kiosk-02", "Mobile Gateway", "Face-AI Edge-Entry"]

        for days_back in range(days_history, 0, -1):
            cur_date = today - timedelta(days=days_back)
            if cur_date.weekday() >= 5:  # Skip weekends
                continue

            for user in user_objects:
                # 92% attendance likelihood on working days
                if random.random() > 0.92:
                    continue

                # Realistic distribution:
                # 78% On-Time, 16% Late, 6% Half-Day or Overtime
                rand_status = random.random()
                if rand_status < 0.78:
                    in_h = random.choice([8, 9])
                    in_m = random.randint(32, 59) if in_h == 8 else random.randint(0, 28)
                    status_lbl = "On-Time"
                    duration = random.uniform(8.1, 9.2)
                elif rand_status < 0.94:
                    in_h = random.choice([9, 10])
                    in_m = random.randint(31, 59) if in_h == 9 else random.randint(0, 22)
                    status_lbl = "Late"
                    duration = random.uniform(8.0, 9.0)
                else:
                    in_h = 8
                    in_m = random.randint(40, 55)
                    status_lbl = random.choice(["Overtime", "On-Time"])
                    duration = random.uniform(9.5, 11.2) if status_lbl == "Overtime" else 8.5

                check_in_dt = datetime.combine(cur_date, time(in_h, in_m, random.randint(0, 59)))
                check_out_dt = check_in_dt + timedelta(hours=duration)

                conf = round(random.uniform(0.950, 0.998), 4)
                liveness = round(random.uniform(0.90, 0.99), 3)
                v_method = random.choice(verification_methods)

                log = AttendanceLog(
                    user_id=user.id,
                    log_date=cur_date,
                    check_in=check_in_dt,
                    check_out=check_out_dt,
                    status=status_lbl,
                    match_confidence=conf,
                    liveness_score=liveness,
                    verification_method=v_method,
                    notes=f"Autonomous scan verified ({status_lbl})"
                )
                db.add(log)
                total_historical += 1

        db.commit()
        print(f"[OK] Generated {total_historical} historical attendance audit logs.")

        # 5. Generate Today's Live Active Turnout
        # 22 out of 25 present today (~88% turnout)
        random.seed(1337)
        today_present_users = random.sample(user_objects, k=min(22, len(user_objects)))
        today_logs_count = 0

        # Arrivals distributed from 08:35 AM to 10:25 AM
        arrival_minutes = sorted([random.randint(515, 625) for _ in range(len(today_present_users))])

        for idx, user in enumerate(today_present_users):
            arr_min = arrival_minutes[idx]
            in_h = arr_min // 60
            in_m = arr_min % 60
            check_in_dt = datetime.combine(today, time(in_h, in_m, random.randint(5, 55)))

            status_lbl = "Late" if (in_h > 9 or (in_h == 9 and in_m > 30)) else "On-Time"
            conf = round(random.uniform(0.955, 0.998), 4)
            liveness = round(random.uniform(0.92, 0.99), 3)

            # Some early arrivers already checked out for lunch/shift
            check_out_dt = None
            if in_h <= 8 and random.random() < 0.3:
                check_out_dt = check_in_dt + timedelta(hours=8, minutes=random.randint(15, 45))

            log = AttendanceLog(
                user_id=user.id,
                log_date=today,
                check_in=check_in_dt,
                check_out=check_out_dt,
                status=status_lbl,
                match_confidence=conf,
                liveness_score=liveness,
                verification_method="Face-AI Kiosk-01",
                notes=f"Kiosk live terminal match ({status_lbl})"
            )
            db.add(log)
            today_logs_count += 1

        db.commit()
        print(f"[OK] Generated {today_logs_count} live attendance check-ins for today.")

        # Reload RAM cache
        face_engine.reload_cache(db)
        print("[OK] Enrolled biometric cache reloaded into RAM.")

        total_all = total_historical + today_logs_count
        print("=" * 65)
        print(f" ✨ COMPLETED: {len(user_objects)} employees enrolled | {total_all} total attendance records!")
        print("=" * 65)

    finally:
        db.close()

if __name__ == "__main__":
    seed_enterprise_data(35)
