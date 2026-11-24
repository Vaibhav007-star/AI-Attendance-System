"""
VisionAttend AI - Standalone Desktop OpenCV Attendance Kiosk
Runs high-throughput local computer vision pipeline with native HUD and audio feedback.
"""

import sys
import time
import cv2
import numpy as np
from datetime import datetime

# Windows sound support
try:
    import winsound
    def play_beep(freq=1200, duration=150):
        winsound.Beep(freq, duration)
except ImportError:
    def play_beep(freq=1200, duration=150):
        pass

from app.core.database import SessionLocal, init_db
from app.services.face_engine import face_engine
from app.services.liveness_detector import liveness_detector
from app.services.attendance_service import attendance_service
from app.main import seed_initial_data

def run_desktop_kiosk(camera_index: int = 0):
    print("=" * 60)
    print(" VisionAttend AI - Standalone Desktop Camera Kiosk")
    print(" Press 'q' or 'ESC' to exit | Press 's' to manually scan")
    print("=" * 60)

    # Initialize DB & Biometric RAM Cache
    init_db()
    seed_initial_data()
    db = SessionLocal()

    cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print(f"[ERROR] Could not open video capture device index {camera_index}")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    prev_time = time.time()
    last_recognition_time = 0
    hud_message = "Position face within scanning reticle"
    hud_color = (0, 242, 254)  # BGR Cyan

    while True:
        ret, frame = cap.read()
        if not ret:
            print("[WARN] Failed to read frame from webcam.")
            break

        # Flip horizontally for natural mirror feel
        frame = cv2.flip(frame, 1)
        h, w, _ = frame.shape

        current_time = time.time()
        fps = 1.0 / max(0.001, (current_time - prev_time))
        prev_time = current_time

        # Detect faces
        faces = face_engine.detect_faces(frame)

        # Process recognition every 350ms to maintain smooth 60 FPS video
        if faces and (current_time - last_recognition_time > 0.35):
            last_recognition_time = current_time
            # Sort by area, take largest
            faces.sort(key=lambda b: b[2] * b[3], reverse=True)
            x, y, fw, fh = faces[0]
            face_crop = frame[y:y+fh, x:x+fw]

            # 1. Anti-Spoofing & Liveness
            liveness_res = liveness_detector.evaluate(face_crop)

            if not liveness_res["is_live"]:
                hud_message = f"SPOOF ALERT: {liveness_res['reason']}"
                hud_color = (0, 0, 255)  # Red
                play_beep(400, 200)
            else:
                # 2. Extract Embedding & Match
                probe_vec = face_engine.extract_embedding(face_crop)
                match_res = face_engine.match_face(probe_vec)

                if match_res and match_res["matched"]:
                    # Record Attendance
                    user_id = match_res["user_id"]
                    att_res = attendance_service.record_attendance(
                        db=db,
                        user_id=user_id,
                        confidence=match_res["confidence"],
                        liveness_score=liveness_res["score"],
                        verification_method="Desktop-Kiosk",
                        face_crop=face_crop
                    )
                    action = att_res.get("action")
                    if action in ["checked_in", "checked_out"]:
                        play_beep(1400, 150)
                        hud_message = att_res.get("message")
                        hud_color = (0, 255, 128)  # Emerald
                    elif action == "cooldown":
                        hud_message = att_res.get("message")
                        hud_color = (255, 200, 0)
                else:
                    hud_message = "Face detected: Not enrolled in system"
                    hud_color = (180, 180, 180)

        # Draw HUD Bounding Boxes
        for (x, y, fw, fh) in faces:
            # Reticle Box
            cv2.rectangle(frame, (x, y), (x + fw, y + fh), hud_color, 2)
            # Corner accents
            d = 16
            cv2.line(frame, (x, y), (x + d, y), hud_color, 4)
            cv2.line(frame, (x, y), (x, y + d), hud_color, 4)
            cv2.line(frame, (x + fw, y), (x + fw - d, y), hud_color, 4)
            cv2.line(frame, (x + fw, y), (x + fw, y + d), hud_color, 4)
            cv2.line(frame, (x, y + fh), (x + d, y + fh), hud_color, 4)
            cv2.line(frame, (x, y + fh), (x, y + fh - d), hud_color, 4)
            cv2.line(frame, (x + fw, y + fh), (x + fw - d, y + fh), hud_color, 4)
            cv2.line(frame, (x + fw, y + fh), (x + fw, y + fh - d), hud_color, 4)

        # Header Glass Banner
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (w, 65), (15, 20, 35), -1)
        cv2.rectangle(overlay, (0, h - 50), (w, h), (15, 20, 35), -1)
        cv2.addWeighted(overlay, 0.75, frame, 0.25, 0, frame)

        # Header Text
        cv2.putText(frame, "VisionAttend AI  |  Biometric Kiosk", (20, 40), cv2.FONT_HERSHEY_DUPLEX, 0.8, (0, 242, 254), 2)
        cv2.putText(frame, f"FPS: {int(fps)}", (w - 140, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180, 180, 180), 1)

        # Footer Status Banner
        now_str = datetime.now().strftime("%Y-%m-%d  %H:%M:%S")
        cv2.putText(frame, now_str, (20, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (160, 160, 160), 1)
        cv2.putText(frame, hud_message, (280, h - 18), cv2.FONT_HERSHEY_SIMPLEX, 0.55, hud_color, 2)

        cv2.imshow("VisionAttend AI - Biometric Kiosk", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q') or key == 27:
            break
        elif key == ord('s'):
            last_recognition_time = 0

    cap.release()
    cv2.destroyAllWindows()
    db.close()
    print("[VisionAttend AI] Desktop Kiosk closed.")

if __name__ == "__main__":
    idx = int(sys.argv[1]) if len(sys.argv) > 1 and sys.argv[1].isdigit() else 0
    run_desktop_kiosk(idx)
