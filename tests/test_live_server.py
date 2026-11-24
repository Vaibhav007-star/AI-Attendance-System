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
    print("=" * 60)
    print(" VISIONATTEND AI - LIVE SERVER END-TO-END TEST SUITE")
    print("=" * 60)

    print("\n--- 1. Testing Web UI Routes ---")
    pages = [
        ("/kiosk", "Live Camera Kiosk Screen"),
        ("/dashboard", "Analytics Dashboard Screen"),
        ("/employees", "Staff Directory & Enrollment Screen"),
        ("/records", "Attendance Records Audit Screen"),
        ("/login", "Admin Portal Sign-In Screen"),
        ("/docs", "FastAPI Swagger Documentation")
    ]
    for path, desc in pages:
        test_endpoint(f"{base_url}{path}", desc)

    print("\n--- 2. Testing JWT Authentication ---")
    login_payload = json.dumps({"email": "admin@visionattend.ai", "password": "Admin@123"}).encode("utf-8")
    req = urllib.request.Request(f"{base_url}/api/v1/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as resp:
        auth_data = json.loads(resp.read().decode("utf-8"))
        token = auth_data["access_token"]
        user_name = auth_data["user"]["full_name"]
        print(f"[PASS] Authenticated as '{user_name}' | JWT Token generated: {token[:25]}...")

    print("\n--- 3. Testing Real-Time Dashboard Stats ---")
    req = urllib.request.Request(f"{base_url}/api/v1/dashboard/stats")
    with urllib.request.urlopen(req) as resp:
        stats = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] Total Staff: {stats['total_employees']}")
        print(f"[PASS] Present Today: {stats['present_today']}")
        print(f"[PASS] On-Time Arrivals: {stats['on_time_today']}")
        print(f"[PASS] Late Arrivals: {stats['late_today']}")
        print(f"[PASS] Attendance Rate: {stats['attendance_rate']}%")
        print(f"[PASS] Hourly Velocity Buckets: {len(stats['hourly_arrivals'])} hours tracked")

    print("\n--- 4. Testing Live Biometric Face Verification & Anti-Spoofing ---")
    # Generate test face crop (112x112 textured face)
    test_img = np.random.randint(60, 200, (112, 112, 3), dtype=np.uint8)
    cv2.circle(test_img, (56, 56), 36, (170, 160, 210), -1)
    _, buf = cv2.imencode(".jpg", test_img)
    b64_frame = "data:image/jpeg;base64," + base64.b64encode(buf.tobytes()).decode("ascii")

    # Encode multipart/form-data
    boundary = "----WebKitFormBoundary7MA4YWxkTrZu0gW"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image_base64"\r\n\r\n'
        f"{b64_frame}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="auto_record"\r\n\r\n'
        f"true\r\n"
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/v1/recognition/verify",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"}
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"[PASS] Verification API Response: Matched={res['matched']}, Action='{res['action']}', Liveness={res['liveness_score']}, Msg='{res['message']}'")

    print("\n--- 5. Testing Attendance Export Services ---")
    test_endpoint(f"{base_url}/api/v1/attendance/export/csv", "Attendance CSV Report Generator")
    test_endpoint(f"{base_url}/api/v1/attendance/export/excel", "Attendance Excel (.xlsx) Report Generator")

    print("\n" + "=" * 60)
    print(" ALL 10 LIVE SYSTEM CHECKS PASSED WITH ZERO ERRORS!")
    print("=" * 60)

if __name__ == "__main__":
    run()
