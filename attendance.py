import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
from playsound import playsound
import mediapipe as mp
from sklearn.metrics.pairwise import cosine_similarity

# -------------------- DATASET --------------------
dataset_path = "dataset"

known_encodings = []
known_names = []

# -------------------- MEDIAPIPE --------------------
mp_face = mp.solutions.face_mesh
face_mesh = mp_face.FaceMesh(static_image_mode=True)

# 🔥 Get face embedding
def get_face_embedding(image):
    img_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(img_rgb)

    if results.multi_face_landmarks:
        landmarks = results.multi_face_landmarks[0]
        embedding = []

        for lm in landmarks.landmark:
            embedding.append(lm.x)
            embedding.append(lm.y)

        return np.array(embedding)
    return None


# -------------------- LOAD DATASET --------------------
for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)
        img = cv2.imread(img_path)

        if img is None:
            continue

        embedding = get_face_embedding(img)

        if embedding is not None:
            known_encodings.append(embedding)
            known_names.append(person)

known_encodings = np.array(known_encodings)

# -------------------- RECOGNITION --------------------
def recognize_face(face):
    embedding = get_face_embedding(face)

    if embedding is None:
        return "Unknown", 0

    similarities = cosine_similarity([embedding], known_encodings)[0]
    max_index = np.argmax(similarities)
    score = similarities[max_index]

    print("Similarity:", score)

    if score > 0.90:   # 🔥 adjust if needed
        confidence = int(score * 100)
        return known_names[max_index], confidence
    else:
        return "Unknown", 0


# -------------------- ATTENDANCE --------------------
attendance_file = "attendance.csv"

if not os.path.exists(attendance_file):
    df = pd.DataFrame(columns=["Name", "RegNo", "Date", "Time"])
    df.to_csv(attendance_file, index=False)

# -------------------- CAMERA --------------------
cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

marked = set()

# -------------------- MAIN LOOP --------------------
while True:
    ret, frame = cap.read()
    if not ret:
        break

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time_now = now.strftime("%H:%M:%S")

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face = frame[y:y+h, x:x+w]

        name_reg, confidence = recognize_face(face)

        if name_reg != "Unknown":
            name, reg_no = name_reg.split("_")
            color = (0, 255, 0)
        else:
            name, reg_no = "Unknown", ""
            color = (0, 0, 255)

        # -------------------- ATTENDANCE MARK --------------------
        if name_reg not in marked and name_reg != "Unknown":
            df = pd.read_csv(attendance_file)

            if not ((df["Name"] == name) & (df["Date"] == date)).any():
                new_row = {
                    "Name": name,
                    "RegNo": reg_no,
                    "Date": date,
                    "Time": time_now
                }

                df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
                df.to_csv(attendance_file, index=False)

                # 🔊 Play sound
                try:
                    playsound("beep.mp3")
                except:
                    pass

            marked.add(name_reg)

        # -------------------- DRAW --------------------
        cv2.rectangle(frame, (x, y), (x+w, y+h), color, 2)

        label = f"{name} ({confidence}%)" if name != "Unknown" else "Unknown"
        cv2.putText(frame, label, (x, y-10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)

        cv2.putText(frame, f"{confidence}%", (x, y+h+25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,255), 2)

    # -------------------- UI --------------------
    cv2.putText(frame, "AI Attendance System", (150, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (255,255,255), 3)

    cv2.putText(frame, f"{date} {time_now}", (20, 70),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 2)

    cv2.putText(frame, f"Marked: {len(marked)}", (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,0), 2)

    cv2.putText(frame, "Q: Exit | S: Screenshot", (20, 150),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200,200,200), 2)

    # -------------------- DISPLAY --------------------
    cv2.imshow("AI Attendance System", frame)

    key = cv2.waitKey(1) & 0xFF

    if key == 27 or key == ord('q'):
        break

    if key == ord('s'):
        cv2.imwrite("screenshot.jpg", frame)

    if cv2.getWindowProperty("AI Attendance System", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()