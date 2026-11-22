# 📷 AI Attendance System — Face Recognition & Real-Time Tracking

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-5C3EE8.svg?logo=opencv&logoColor=white)](https://opencv.org/)
[![MediaPipe](https://img.shields.io/badge/MediaPipe-Face%20Mesh-00A9E0.svg)](https://developers.google.com/mediapipe)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter-green.svg)](https://docs.python.org/3/library/tkinter.html)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **Real-time automated face recognition and contactless attendance management platform powered by OpenCV, Google MediaPipe Face Mesh, deep metric embeddings (Cosine Similarity), audio confirmation cues, and an interactive Tkinter desktop GUI with automated CSV logging.**

---

## 📑 Table of Contents
- [Architecture Overview](#-architecture-overview)
- [Key Features](#-key-features)
- [Tech Stack](#-tech-stack)
- [Repository Structure](#-repository-structure)
- [Installation & Setup](#-installation--setup)
- [Workflow & How It Works](#-workflow--how-it-works)
  - [Step 1: Face Registration & Capture](#step-1-face-registration--capture)
  - [Step 2: Vector Embedding Generation](#step-2-vector-embedding-generation)
  - [Step 3: Real-Time Attendance Recognition](#step-3-real-time-attendance-recognition)
  - [Step 4: Interactive Desktop GUI](#step-4-interactive-desktop-gui)
- [Attendance Log Output](#-attendance-log-output)
- [Future Enhancements](#-future-enhancements)
- [Author & License](#-author--license)

---

## 🏗️ Architecture Overview

```text
  [ Webcam Video Stream ]
            │
            ▼
  [ Face Detection ] ────────► MediaPipe Face Detection / Haar Cascades
            │
            ▼
  [ Facial Landmark Embedding ] ──► 468 Dense Landmarks (MediaPipe FaceMesh)
            │
            ▼
  [ Metric Matching ] ───────► Cosine Similarity against Known Registered Vectors
            │
      Score >= 0.90?
     ┌──────┴──────┐
    YES            NO
     │              │
     ▼              ▼
[ Identity ]   [ "Unknown" ]
     │
     ├─► Play Audio Cue (beep.mp3)
     ├─► Prevent Duplicate Logging in Same Session
     └─► Append Record to attendance.csv (Name, RegNo, Date, Time)
```

---

## ✨ Key Features

- 👤 **Dual Facial Recognition Pipelines:**
  - **MediaPipe Face Mesh:** Generates high-fidelity landmark coordinate embeddings matched via Cosine Similarity metric spaces ($>90\%$ threshold).
  - **Dlib / Deep Face Encodings:** Supports 128-dimensional Euclidean face encodings saved to serialized pickle vectors (`encodings.pkl`).
- 🖥️ **Interactive Desktop GUI (`gui_attendance.py`):** User-friendly Tkinter interface showing live webcam preview, student/employee details input, and real-time attendance registration.
- ⚡ **Real-Time Video Inference:** High-FPS tracking with OpenCV bounding boxes, confidence score overlays, and responsive escape controls.
- 🔊 **Audio Confirmation (`beep.mp3`):** Instant auditory feedback upon successful identity verification and check-in.
- 📝 **Automated Session Logging:** Deduplicated, timestamped recording to `attendance.csv` (Name, RegNo, Date, Time) ready for payroll or academic LMS import.

---

## 🧰 Tech Stack

- **Computer Vision:** OpenCV (`cv2`), MediaPipe (`face_detection`, `face_mesh`), Haar Cascades
- **Feature Extraction & Deep Embeddings:** Scikit-Learn (`cosine_similarity`), NumPy, Pickle
- **Data Engineering:** Pandas
- **Desktop Application:** Python Tkinter, Pillow (`PIL`)
- **Audio Processing:** Playsound

---

## 📂 Repository Structure

```text
AI-Attendance-System/
├── attendance.py        # Core automated recognition pipeline with MediaPipe & audio feedback
├── gui_attendance.py    # Desktop GUI application built with Tkinter & OpenCV
├── capture_faces.py     # Web-cam data collector for registering new faces
├── encode_faces.py      # Batch feature extractor producing serialized encodings
├── main.py              # Lightweight real-time face detection visualizer
├── attendance.csv       # Persistent attendance log database (CSV)
├── beep.mp3             # Audio verification sound effect
├── screenshot.jpg       # System UI preview
└── README.md            # Comprehensive project documentation
```

---

## 🚀 Installation & Setup

### 1. Clone the Repository
```bash
git clone https://github.com/Vaibhav007-star/AI-Attendance-System.git
cd AI-Attendance-System
```

### 2. Create and Activate Virtual Environment
```bash
# Windows
python -m venv .venv
.\.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install opencv-python mediapipe numpy pandas scikit-learn pillow playsound
```

---

## 🎯 Workflow & How It Works

### Step 1: Face Registration & Capture
Capture reference images of each person under various angles and lighting:
```bash
python capture_faces.py
```
Images will be saved into the `dataset/<Person_Name>/` folder.

### Step 2: Vector Embedding Generation
Extract and serialize facial feature vectors:
```bash
python encode_faces.py
```
This generates `encodings.pkl` containing normalized facial feature vectors.

### Step 3: Real-Time Attendance Recognition
Launch the autonomous live camera scanner:
```bash
python attendance.py
```
- Recognizes faces in real time.
- Plays `beep.mp3` upon detection.
- Writes a new entry into `attendance.csv` only once per day/session per person.
- Press `Q` or `ESC` to stop.

### Step 4: Interactive Desktop GUI
Alternatively, run the desktop dashboard:
```bash
python gui_attendance.py
```

---

## 📊 Attendance Log Output (`attendance.csv`)

| Name | RegNo | Date | Time | Status |
|---|---|---|---|---|
| Vaibhav | REG-2024-001 | 2026-11-22 | 09:15:32 | Present |
| John Doe | REG-2024-042 | 2026-11-22 | 09:17:04 | Present |
| Jane Smith | REG-2024-089 | 2026-11-22 | 09:18:22 | Present |

---

## 👤 Author
**Vaibhav**
- GitHub: [@Vaibhav007-star](https://github.com/Vaibhav007-star)
- Specialization: AI & Data Science Engineering • Computer Vision • Multi-Agent Systems
