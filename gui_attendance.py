import cv2
import pandas as pd
from datetime import datetime
from tkinter import *
from PIL import Image, ImageTk

# CSV file
attendance_file = "attendance.csv"

# Create CSV if not exists
try:
    pd.read_csv(attendance_file)
except:
    df = pd.DataFrame(columns=["Name", "RegNo", "Date", "Time"])
    df.to_csv(attendance_file, index=False)

# GUI
root = Tk()
root.title("Light Attendance System")
root.geometry("900x600")

video_label = Label(root)
video_label.pack()

cap = None
running = False

# Face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

# Entry fields
name_var = StringVar()
reg_var = StringVar()

Label(root, text="Name").pack()
Entry(root, textvariable=name_var).pack()

Label(root, text="Reg No").pack()
Entry(root, textvariable=reg_var).pack()

# Start camera
def start_camera():
    global cap, running
    cap = cv2.VideoCapture(0)
    running = True
    update_frame()

# Stop camera
def stop_camera():
    global running
    running = False
    if cap:
        cap.release()
    cv2.destroyAllWindows()

# Update frame
def update_frame():
    global running

    if not running:
        return

    ret, frame = cap.read()
    if not ret:
        return

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    # Draw rectangle
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x,y), (x+w, y+h), (0,255,0), 2)

    # Convert for GUI
    img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    imgtk = ImageTk.PhotoImage(image=img)

    video_label.imgtk = imgtk
    video_label.configure(image=imgtk)

    root.after(10, update_frame)

# Mark attendance
def mark_attendance():
    name = name_var.get()
    reg = reg_var.get()

    if name == "" or reg == "":
        print("Enter details")
        return

    now = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")

    df = pd.read_csv(attendance_file)

    new_row = {
        "Name": name,
        "RegNo": reg,
        "Date": date,
        "Time": time
    }

    df = pd.concat([df, pd.DataFrame([new_row])], ignore_index=True)
    df.to_csv(attendance_file, index=False)

    print("✅ Attendance Marked")

# Buttons
Button(root, text="Start Camera", command=start_camera, bg="green", fg="white").pack(pady=10)
Button(root, text="Stop Camera", command=stop_camera, bg="red", fg="white").pack(pady=10)
Button(root, text="Mark Attendance", command=mark_attendance, bg="blue", fg="white").pack(pady=10)
Button(root, text="Exit", command=root.quit, bg="black", fg="white").pack(pady=10)

root.mainloop()