import face_recognition
import os
import pickle
import cv2

dataset_path = "dataset"

known_encodings = []
known_names = []

for person in os.listdir(dataset_path):
    person_path = os.path.join(dataset_path, person)

    for img_name in os.listdir(person_path):
        img_path = os.path.join(person_path, img_name)

        image = cv2.imread(img_path)
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        encodings = face_recognition.face_encodings(rgb)

        if encodings:
            known_encodings.append(encodings[0])
            known_names.append(person)

print("Encoding Done ✅")

data = {"encodings": known_encodings, "names": known_names}

with open("encodings.pkl", "wb") as f:
    pickle.dump(data, f)

print("Saved encodings.pkl 🎯")