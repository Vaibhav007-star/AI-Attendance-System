import urllib.request
import json
import base64
import numpy as np
import cv2

base_url = "http://127.0.0.1:8000"

def test_endpoint(url, desc):
    req = urllib.request.Request(url, headers={"User-Agent": "TestClient/1.0"})
    with urllib.request.urlopen(req) as resp:
        code = resp.getcode()
        length = len(resp.read())
        print(f"[PASS] {desc}: HTTP {code} ({length} bytes)")

def run():
    print("=" * 65)
    print(" VISIONATTEND AI - LIVE WEBSITE & SUBSYSTEM TEST SUITE")
    print("=" * 65)

    print("\n--- 1. Testing Web UI Pages ---")
    pages = [
        ("/", "Flagship Landing Page"),
        ("/kiosk", "Live Autonomous Camera Kiosk Screen"),
        ("/dashboard", "Analytics & Punctuality Dashboard Screen"),
        ("/employees", "Staff Directory & Face AI Enrollment Screen"),
        ("/records", "Attendance Records & Audit Screen"),
        ("/settings", "System Policy & Shift Settings Screen"),
        ("/admin", "Executive Admin Management Portal"),
        ("/login", "Admin Portal Sign-In Screen"),
        ("/docs", "FastAPI Swagger API Documentation")
    ]
    for path, desc in pages:
        test_endpoint(f"{base_url}{path}", desc)

    print("\n--- 2. Testing System Settings API ---")
    req = urllib.request.Request(f"{base_url}/api/v1/settings")
    with urllib.request.urlopen(req) as resp:
        cfg = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] Settings API Loaded: Shift Start={cfg['office_start_time']}, Late Mark={cfg['office_late_threshold']}, Cooldown={cfg['attendance_cooldown_minutes']}m")

    # Test updating settings
    cfg["attendance_cooldown_minutes"] = 5
    update_data = json.dumps(cfg).encode("utf-8")
    req_update = urllib.request.Request(f"{base_url}/api/v1/settings", data=update_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req_update) as resp:
        updated = json.loads(resp.read().decode("utf-8"))
        assert updated["attendance_cooldown_minutes"] == 5
        print("[PASS] Settings API Update: Successfully saved and validated policy changes")

    print("\n--- 3. Testing JWT Authentication ---")
    login_payload = json.dumps({"email": "admin@visionattend.ai", "password": "Admin@123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/api/v1/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        auth_data = json.loads(resp.read().decode("utf-8"))
        token = auth_data["access_token"]
        print(f"[PASS] JWT Authentication: Generated bearer token ({token[:25]}...)")

    print("\n--- 4. Testing Real-Time Dashboard Analytics ---")
    req = urllib.request.Request(f"{base_url}/api/v1/dashboard/stats")
    with urllib.request.urlopen(req) as resp:
        stats = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] Dashboard KPIs: Staff={stats['total_employees']}, Present={stats['present_today']}, On-Time={stats['on_time_today']}, Late={stats['late_today']}")

    print("\n--- 5. Testing Export Capabilities ---")
    test_endpoint(f"{base_url}/api/v1/attendance/export/csv", "CSV Attendance Report Generator")
    test_endpoint(f"{base_url}/api/v1/attendance/export/excel", "Excel (.xlsx) Attendance Report Generator")

    print("\n" + "=" * 65)
    print(" ALL WEBSITE PAGES & SUBSYSTEM CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 65)

if __name__ == "__main__":
    run()
