import cv2
import os

name = input("Enter Name: ")
reg_no = input("Enter Reg No: ")

folder = f"dataset/{name}_{reg_no}"
os.makedirs(folder, exist_ok=True)

cap = cv2.VideoCapture(0)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

count = 0

while True:
    ret, frame = cap.read()
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        face = frame[y:y+h, x:x+w]

        # Save only face
        face = cv2.resize(face, (200, 200))
        cv2.imwrite(f"{folder}/{count}.jpg", face)
        count += 1

        cv2.rectangle(frame, (x, y), (x+w, y+h), (0,255,0), 2)

    cv2.putText(frame, f"Images: {count}/20", (20,40),
                cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)

    cv2.imshow("Capture Faces", frame)

    if cv2.waitKey(1) & 0xFF == 27 or count >= 20:
        break

cap.release()
cv2.destroyAllWindows()