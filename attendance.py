import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
import pygame

# -------------------- SOUND --------------------
pygame.mixer.init()

def play_beep():
    try:
        pygame.mixer.music.load("beep.mp3")
        pygame.mixer.music.play()
    except:
        pass

# -------------------- DATASET --------------------
dataset_path = "dataset"

known_labels = []   # integer label per image
known_names  = []   # name_reg string per label index
label_map    = {}   # folder name -> integer label

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

train_images = []
train_labels = []

print("Loading dataset...")

for idx, person in enumerate(sorted(os.listdir(dataset_path))):
    person_path = os.path.join(dataset_path, person)
    if not os.path.isdir(person_path):
        continue

    label_map[idx] = person  # idx -> "Name_RegNo"

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)

        if img is None:
            continue

        img = cv2.resize(img, (200, 200))
        train_images.append(img)
        train_labels.append(idx)

if len(train_images) == 0:
    print("⚠️  No dataset found! Run capture_faces.py first.")
    exit()

# -------------------- TRAIN LBPH --------------------
print(f"Training on {len(train_images)} images for {len(label_map)} person(s)...")
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(train_images, np.array(train_labels))
print("✅ Training done!")

# -------------------- RECOGNITION --------------------
CONFIDENCE_THRESHOLD = 37  # lower = stricter (LBPH: lower distance = better)

def recognize_face(gray_face):
    gray_face = cv2.resize(gray_face, (200, 200))
    label, distance = recognizer.predict(gray_face)

    # Convert distance to a 0-100 confidence score
    confidence = max(0, int(100 - distance))

    if distance < CONFIDENCE_THRESHOLD:
        name_reg = label_map.get(label, "Unknown")
        return name_reg, confidence
    else:
        return "Unknown", confidence

# -------------------- ATTENDANCE --------------------
attendance_file = "attendance.csv"

if not os.path.exists(attendance_file):
    df = pd.DataFrame(columns=["Name", "RegNo", "Date", "Time"])
    df.to_csv(attendance_file, index=False)

# -------------------- CAMERA --------------------
cap = cv2.VideoCapture(0)
marked = set()

print("📷 Camera started. Press Q or ESC to exit, S for screenshot.")

# -------------------- MAIN LOOP --------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    now      = datetime.now()
    date     = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face_gray    = gray[y:y+h, x:x+w]
        name_reg, confidence = recognize_face(face_gray)

        if name_reg != "Unknown":
            parts  = name_reg.split("_", 1)
            name   = parts[0]
            reg_no = parts[1] if len(parts) > 1 else ""
            color  = (0, 255, 0)
        else:
            name, reg_no = "Unknown", ""
            color = (0, 0, 255)

        # -------------------- MARK ATTENDANCE --------------------
        if name_reg != "Unknown" and name_reg not in marked:
            df = pd.read_csv(attendance_file)

            if not ((df["Name"] == name) & (df["Date"] == date)).any():
                new_row = {"Name": name, "RegNo": reg_no,
                           "Date": date, "Time": time_now}
                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(attendance_file, index=False)
                print(f"✅ Marked: {name} ({reg_no}) at {time_now}")
                play_beep()

            marked.add(name_reg)

        # -------------------- DRAW --------------------
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)
        label_text = f"{name} ({confidence}%)" if name != "Unknown" else "Unknown"
        cv2.putText(frame, label_text, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

    # -------------------- HUD --------------------
    cv2.putText(frame, "AI Attendance System", (150, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)
    cv2.putText(frame, f"{date}  {time_now}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    cv2.putText(frame, f"Marked: {len(marked)}", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)
    cv2.putText(frame, "Q: Exit | S: Screenshot", (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)

    cv2.imshow("AI Attendance System", frame)

    key = cv2.waitKey(1) & 0xFF
    if key in (27, ord('q')):
        break
    if key == ord('s'):
        cv2.imwrite("screenshot.jpg", frame)
        print("📸 Screenshot saved.")
    if cv2.getWindowProperty("AI Attendance System", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()
print("👋 Exited.")