"""
AI Attendance System - Full Featured GUI
Features:
  - Face Recognition (LBPH)
  - Anti-Spoofing / Liveness Detection
  - Live Attendance Table
  - Attendance Statistics Dashboard
  - Absentee Alert + Export
  - Register New Student via GUI
"""

import cv2
import os
import numpy as np
import pandas as pd
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from PIL import Image, ImageTk
import threading
import pygame

# ─────────────────────────────────────────────
# SOUND
# ─────────────────────────────────────────────
pygame.mixer.init()
def play_beep():
    try:
        pygame.mixer.music.load("beep.mp3")
        pygame.mixer.music.play()
    except:
        pass

# ─────────────────────────────────────────────
# PATHS & CONSTANTS
# ─────────────────────────────────────────────
DATASET_PATH      = "dataset"
ATTENDANCE_FILE   = "attendance.csv"
CONFIDENCE_THRESH = 75
CAM_W, CAM_H      = 640, 400   # fixed camera display pixel size

os.makedirs(DATASET_PATH, exist_ok=True)
if not os.path.exists(ATTENDANCE_FILE):
    pd.DataFrame(columns=["Name","RegNo","Date","Time"]).to_csv(ATTENDANCE_FILE, index=False)

# ─────────────────────────────────────────────
# FACE CASCADES
# ─────────────────────────────────────────────
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
eye_cascade  = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_eye.xml")

# ─────────────────────────────────────────────
# LBPH RECOGNIZER
# ─────────────────────────────────────────────
recognizer  = cv2.face.LBPHFaceRecognizer_create()
label_map   = {}
model_ready = False

def train_model():
    global recognizer, label_map, model_ready
    images, labels, label_map = [], [], {}
    idx = 0
    for person in sorted(os.listdir(DATASET_PATH)):
        person_path = os.path.join(DATASET_PATH, person)
        if not os.path.isdir(person_path):
            continue
        added = 0
        for img_name in os.listdir(person_path):
            img = cv2.imread(os.path.join(person_path, img_name),
                             cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            images.append(cv2.resize(img, (200, 200)))
            labels.append(idx)
            added += 1
        if added > 0:
            label_map[idx] = person
            idx += 1
    if not images:
        model_ready = False
        return 0
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.train(images, np.array(labels))
    model_ready = True
    return len(label_map)

def recognize_face(gray_face):
    if not model_ready:
        return "Unknown", 0
    label, distance = recognizer.predict(cv2.resize(gray_face, (200, 200)))
    confidence = max(0, int(100 - distance))
    if distance < CONFIDENCE_THRESH:
        return label_map.get(label, "Unknown"), confidence
    return "Unknown", confidence

# ─────────────────────────────────────────────
# LIVENESS
# ─────────────────────────────────────────────
def check_liveness(face_bgr, face_gray):
    if cv2.Laplacian(face_gray, cv2.CV_64F).var() < 80:
        return False, "SPOOF? Low texture"
    if len(eye_cascade.detectMultiScale(face_gray, 1.1, 5,
                                         minSize=(20,20))) == 0:
        return False, "No eyes detected"
    if np.std(cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)[:,:,1]) < 15:
        return False, "SPOOF? Flat color"
    return True, "Live"

# ─────────────────────────────────────────────
# ATTENDANCE CSV
# ─────────────────────────────────────────────
def mark_attendance(name, reg_no):
    now  = datetime.now()
    date = now.strftime("%Y-%m-%d")
    time = now.strftime("%H:%M:%S")
    df   = pd.read_csv(ATTENDANCE_FILE)
    if ((df["Name"] == name) & (df["Date"] == date)).any():
        return False
    df = pd.concat([df, pd.DataFrame([{
        "Name": name, "RegNo": reg_no, "Date": date, "Time": time
    }])], ignore_index=True)
    df.to_csv(ATTENDANCE_FILE, index=False)
    play_beep()
    return True

# ─────────────────────────────────────────────
# COLORS
# ─────────────────────────────────────────────
BG, PANEL, ACCENT = "#0d1117", "#161b22", "#238636"
RED, BLUE         = "#da3633", "#1f6feb"
TEXT, MUTED       = "#c9d1d9", "#8b949e"

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def make_scrollable(parent):
    canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
    vsb    = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
    canvas.configure(yscrollcommand=vsb.set)
    vsb.pack(side="right", fill="y")
    canvas.pack(side="left", fill="both", expand=True)
    inner = tk.Frame(canvas, bg=BG)
    win   = canvas.create_window((0,0), window=inner, anchor="nw")
    canvas.bind("<Configure>",
                lambda e: canvas.itemconfig(win, width=e.width))
    inner.bind("<Configure>",
               lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.bind_all("<MouseWheel>",
        lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))
    return inner

def mk_btn(parent, text, cmd, color, px=14, py=6):
    return tk.Button(parent, text=text, command=cmd,
                     bg=color, fg="white", relief="flat",
                     font=("Courier New", 10, "bold"),
                     padx=px, pady=py, cursor="hand2",
                     activebackground=color, activeforeground="white")

# ─────────────────────────────────────────────
# APP
# ─────────────────────────────────────────────
class AttendanceApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AI Attendance System")
        self.geometry("1100x700")
        self.minsize(1000, 650)
        self.configure(bg=BG)
        self.resizable(True, True)
        self.cap     = None
        self.running = False
        self.marked  = set()
        self._styles()
        self._header()
        self._tabs()
        self._load_model_async()
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── STYLES ───────────────────────────────
    def _styles(self):
        s = ttk.Style(self)
        s.theme_use("clam")
        s.configure("TNotebook",       background=BG,   borderwidth=0)
        s.configure("TNotebook.Tab",   background=PANEL, foreground=MUTED,
                    font=("Courier New",11,"bold"), padding=[16,8])
        s.map("TNotebook.Tab",
              background=[("selected", ACCENT)],
              foreground=[("selected", "white")])
        s.configure("TFrame",          background=BG)
        s.configure("Treeview",        background=PANEL, foreground=TEXT,
                    fieldbackground=PANEL, rowheight=26,
                    font=("Courier New",10))
        s.configure("Treeview.Heading", background="#21262d",
                    foreground="#58a6ff", font=("Courier New",10,"bold"))
        s.map("Treeview", background=[("selected", BLUE)])

    # ── HEADER ───────────────────────────────
    def _header(self):
        hdr = tk.Frame(self, bg=PANEL, height=52)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="🎓  AI Attendance System",
                 font=("Courier New",17,"bold"),
                 bg=PANEL, fg="#58a6ff").pack(side="left", padx=20)
        self.status_lbl = tk.Label(hdr, text="● Loading...",
                                   font=("Courier New",11),
                                   bg=PANEL, fg="#f0883e")
        self.status_lbl.pack(side="right", padx=20)

    # ── TABS ─────────────────────────────────
    def _tabs(self):
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=8, pady=6)
        for text, builder in [
            ("📷  Live Camera",    self._tab_camera),
            ("📊  Statistics",     self._tab_stats),
            ("🔔  Absentee Alert", self._tab_absent),
            ("➕  Register Student", self._tab_register),
        ]:
            f = ttk.Frame(nb)
            nb.add(f, text=text)
            builder(f)

    # ────────────────────────────────────────
    # TAB 1 — CAMERA
    # Pack order: button_bar (bottom) → live_bar (bottom) → main_row (top/expand)
    # main_row: cam_container (fixed 640×400, no expand) | right_panel (fixed 300w)
    # ────────────────────────────────────────
    def _tab_camera(self, p):
        # 1. Button bar — packed first so it always claims space at bottom
        btn_bar = tk.Frame(p, bg="#1c2128", height=52)
        btn_bar.pack(side="bottom", fill="x")
        btn_bar.pack_propagate(False)
        for txt, cmd, col in [
            ("▶  Start Camera",  self._start_camera,     ACCENT),
            ("■  Stop Camera",   self._stop_camera,      RED),
            ("📸  Screenshot",   self._screenshot,       BLUE),
            ("🔄  Reload Model", self._load_model_async, "#6e7681"),
        ]:
            mk_btn(btn_bar, txt, cmd, col).pack(side="left", padx=(10,4), pady=10)

        # 2. Liveness status bar — just above buttons
        live_bar = tk.Frame(p, bg=BG, height=26)
        live_bar.pack(side="bottom", fill="x")
        live_bar.pack_propagate(False)
        self.live_lbl = tk.Label(live_bar, text="", bg=BG,
                                 font=("Courier New",11,"bold"))
        self.live_lbl.pack(side="left", padx=12)

        # 3. Main row — fills remaining space
        row = tk.Frame(p, bg=BG)
        row.pack(side="top", fill="both", expand=True, padx=8, pady=(8,4))

        # Camera feed — FIXED size, pack_propagate(False) prevents expansion
        cam_wrap = tk.Frame(row, bg="#000000", width=CAM_W, height=CAM_H)
        cam_wrap.pack(side="left")
        cam_wrap.pack_propagate(False)

        self.cam_label = tk.Label(cam_wrap, bg="#000000",
                                  text="Camera Off", fg=MUTED,
                                  font=("Courier New",13))
        self.cam_label.pack(fill="both", expand=True)

        # Right panel — fixed 300 px wide, fills height
        right = tk.Frame(row, bg=PANEL, width=300)
        right.pack(side="left", fill="y", padx=(10,0))
        right.pack_propagate(False)

        tk.Label(right, text="Today's Attendance",
                 font=("Courier New",12,"bold"),
                 bg=PANEL, fg="#58a6ff").pack(pady=(14,4))
        self.today_count = tk.Label(right, text="",
                                    font=("Courier New",9),
                                    bg=PANEL, fg=MUTED)
        self.today_count.pack()

        tf = tk.Frame(right, bg=PANEL)
        tf.pack(fill="both", expand=True, padx=8, pady=6)
        cols = ("Name","Reg","Time")
        self.live_tree = ttk.Treeview(tf, columns=cols, show="headings")
        for c, w in zip(cols, (110,100,70)):
            self.live_tree.heading(c, text=c)
            self.live_tree.column(c, width=w, anchor="center")
        vsb = ttk.Scrollbar(tf, orient="vertical",
                             command=self.live_tree.yview)
        self.live_tree.configure(yscrollcommand=vsb.set)
        self.live_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        mk_btn(right, "Export CSV", self._export_csv, "#21262d").pack(pady=8)
        self._refresh_live_table()

    # ────────────────────────────────────────
    # TAB 2 — STATISTICS
    # ────────────────────────────────────────
    def _tab_stats(self, p):
        inner = make_scrollable(p)
        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", padx=14, pady=10)
        tk.Label(hdr, text="Attendance Statistics",
                 font=("Courier New",15,"bold"),
                 bg=BG, fg="#58a6ff").pack(side="left")
        mk_btn(hdr, "🔄 Refresh", self._refresh_stats,
               ACCENT, px=10, py=4).pack(side="right")

        self.cards_frame = tk.Frame(inner, bg=BG)
        self.cards_frame.pack(fill="x", padx=14, pady=6)

        tk.Label(inner, text="Per Student Summary",
                 font=("Courier New",12,"bold"),
                 bg=BG, fg="#e3b341").pack(anchor="w", padx=14, pady=(10,4))

        tf = tk.Frame(inner, bg=BG)
        tf.pack(fill="both", expand=True, padx=14, pady=6)
        cols = ("Name","RegNo","Days Present","Last Seen","Attendance %")
        self.stats_tree = ttk.Treeview(tf, columns=cols,
                                       show="headings", height=14)
        for c in cols:
            self.stats_tree.heading(c, text=c)
            self.stats_tree.column(c, width=160, anchor="center")
        vsb = ttk.Scrollbar(tf, orient="vertical",
                             command=self.stats_tree.yview)
        self.stats_tree.configure(yscrollcommand=vsb.set)
        self.stats_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._refresh_stats()

    # ────────────────────────────────────────
    # TAB 3 — ABSENTEE
    # ────────────────────────────────────────
    def _tab_absent(self, p):
        inner = make_scrollable(p)
        hdr = tk.Frame(inner, bg=BG)
        hdr.pack(fill="x", padx=14, pady=10)
        tk.Label(hdr, text="Absentee Alert",
                 font=("Courier New",15,"bold"),
                 bg=BG, fg=RED).pack(side="left")
        mk_btn(hdr, "📧 Export", self._export_absent,
               "#21262d", px=10, py=4).pack(side="right", padx=4)
        mk_btn(hdr, "🔄 Refresh", self._refresh_absent,
               RED, px=10, py=4).pack(side="right", padx=4)

        mid = tk.Frame(inner, bg=BG)
        mid.pack(fill="x", padx=14, pady=4)
        tk.Label(mid, text="Date:", bg=BG, fg=MUTED,
                 font=("Courier New",11)).pack(side="left")
        self.absent_date = tk.Entry(mid, font=("Courier New",11),
                                    bg=PANEL, fg="white",
                                    insertbackground="white",
                                    relief="flat", width=14)
        self.absent_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.absent_date.pack(side="left", padx=8, ipady=4)

        self.absent_summary = tk.Label(inner, text="",
                                       font=("Courier New",11),
                                       bg=BG, fg=RED)
        self.absent_summary.pack(anchor="w", padx=14, pady=4)

        tf = tk.Frame(inner, bg=BG)
        tf.pack(fill="both", expand=True, padx=14, pady=6)
        cols = ("Name","RegNo","Status")
        self.absent_tree = ttk.Treeview(tf, columns=cols,
                                        show="headings", height=16)
        for c, w in zip(cols, (220,200,160)):
            self.absent_tree.heading(c, text=c)
            self.absent_tree.column(c, width=w, anchor="center")
        vsb = ttk.Scrollbar(tf, orient="vertical",
                             command=self.absent_tree.yview)
        self.absent_tree.configure(yscrollcommand=vsb.set)
        self.absent_tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        self._refresh_absent()

    # ────────────────────────────────────────
    # TAB 4 — REGISTER
    # ────────────────────────────────────────
    def _tab_register(self, p):
        inner = make_scrollable(p)
        tk.Label(inner, text="Register New Student",
                 font=("Courier New",16,"bold"),
                 bg=BG, fg="#58a6ff").pack(pady=(24,16))

        form = tk.Frame(inner, bg=BG)
        form.pack()
        self.reg_name = tk.StringVar()
        self.reg_no   = tk.StringVar()
        self.reg_imgs = tk.IntVar(value=30)
        for i, (lbl, var) in enumerate([
            ("Full Name:",          self.reg_name),
            ("Register No:",        self.reg_no),
            ("Images to Capture:",  self.reg_imgs),
        ]):
            tk.Label(form, text=lbl, width=22, anchor="e",
                     font=("Courier New",12), bg=BG,
                     fg=MUTED).grid(row=i, column=0, pady=8, padx=8)
            tk.Entry(form, textvariable=var, width=26,
                     font=("Courier New",12), bg=PANEL,
                     fg="white", insertbackground="white",
                     relief="flat").grid(row=i, column=1,
                                         pady=8, padx=8, ipady=6)

        self.reg_progress = tk.Label(inner, text="",
                                     font=("Courier New",11),
                                     bg=BG, fg=ACCENT)
        self.reg_progress.pack(pady=6)

        pv = tk.Frame(inner, bg="#000000", width=480, height=300)
        pv.pack(pady=8)
        pv.pack_propagate(False)
        self.reg_cam_label = tk.Label(pv, bg="#000000",
                                      text="Preview will appear here",
                                      fg=MUTED, font=("Courier New",10))
        self.reg_cam_label.pack(fill="both", expand=True)

        mk_btn(inner, "📷  Start Capture", self._start_register,
               ACCENT, px=24, py=10).pack(pady=16)

    # ────────────────────────────────────────
    # MODEL
    # ────────────────────────────────────────
    def _load_model_async(self):
        self.status_lbl.config(text="● Training...", fg="#f0883e")
        def _train():
            n = train_model()
            if n > 0:
                self.status_lbl.config(
                    text=f"● Model ready  ({n} student{'s' if n!=1 else ''})",
                    fg="#3fb950")
            else:
                self.status_lbl.config(
                    text="● No dataset — register students first", fg=RED)
        threading.Thread(target=_train, daemon=True).start()

    # ────────────────────────────────────────
    # CAMERA LOGIC
    # ────────────────────────────────────────
    def _start_camera(self):
        if self.running:
            return
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            messagebox.showerror("Error", "Cannot open webcam.")
            return
        self.running = True
        self._next_frame()

    def _stop_camera(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None
        self.cam_label.config(image="", text="Camera Off")
        self.live_lbl.config(text="")

    def _next_frame(self):
        if not self.running or self.cap is None:
            return
        ret, frame = self.cap.read()
        if not ret:
            self.after(30, self._next_frame)
            return

        date     = datetime.now().strftime("%Y-%m-%d")
        time_now = datetime.now().strftime("%H:%M:%S")
        gray     = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces    = face_cascade.detectMultiScale(gray, 1.3, 5)
        live_txt = ""

        for (x, y, w, h) in faces:
            face_bgr  = frame[y:y+h, x:x+w]
            face_gray = gray[y:y+h, x:x+w]
            is_live, reason = check_liveness(face_bgr, face_gray)
            live_txt = "✅ LIVE" if is_live else f"❌ {reason}"

            if not is_live:
                cv2.rectangle(frame, (x,y),(x+w,y+h),(0,60,220),3)
                cv2.putText(frame, reason, (x,y-8),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.65,(0,60,220),2)
                continue

            name_reg, conf = recognize_face(face_gray)
            if name_reg != "Unknown":
                parts  = name_reg.split("_", 1)
                name   = parts[0]
                reg_no = parts[1] if len(parts) > 1 else ""
                col    = (0,220,60)
                if name_reg not in self.marked:
                    self.marked.add(name_reg)
                    if mark_attendance(name, reg_no):
                        self.after(0, self._refresh_live_table)
            else:
                name, reg_no, col = "Unknown", "", (0,60,220)

            cv2.rectangle(frame, (x,y),(x+w,y+h), col, 2)
            cv2.putText(frame,
                        f"{name} {conf}%" if name != "Unknown" else "Unknown",
                        (x,y-8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, col, 2)

        cv2.putText(frame, f"{date} {time_now}", (8,24),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (180,180,180), 1)
        cv2.putText(frame, f"Marked: {len(self.marked)}", (8,48),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0,220,255), 2)

        # Always resize to exact CAM_W x CAM_H — no dynamic sizing
        pil   = Image.fromarray(
                    cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                ).resize((CAM_W, CAM_H), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=pil)
        self.cam_label.imgtk = imgtk
        self.cam_label.config(image=imgtk, text="")

        fg = "#3fb950" if live_txt == "✅ LIVE" else (
             RED if live_txt else "")
        self.live_lbl.config(text=live_txt, fg=fg)
        self.after(30, self._next_frame)

    def _screenshot(self):
        if self.cap and self.running:
            ret, frame = self.cap.read()
            if ret:
                fname = f"screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
                cv2.imwrite(fname, frame)
                messagebox.showinfo("Screenshot", f"Saved: {fname}")

    # ────────────────────────────────────────
    # LIVE TABLE
    # ────────────────────────────────────────
    def _refresh_live_table(self):
        for r in self.live_tree.get_children():
            self.live_tree.delete(r)
        try:
            df    = pd.read_csv(ATTENDANCE_FILE)
            date  = datetime.now().strftime("%Y-%m-%d")
            today = df[df["Date"]==date].sort_values("Time", ascending=False)
            for _, r in today.iterrows():
                self.live_tree.insert("", "end",
                    values=(r["Name"], r["RegNo"], r["Time"]))
            self.today_count.config(
                text=f"{len(today)} total today  ({len(self.marked)} this session)")
        except:
            pass

    def _export_csv(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV","*.csv")],
            initialfile=f"attendance_{datetime.now().strftime('%Y%m%d')}.csv")
        if path:
            try:
                import shutil; shutil.copy(ATTENDANCE_FILE, path)
                messagebox.showinfo("Exported", f"Saved to {path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ────────────────────────────────────────
    # STATISTICS
    # ────────────────────────────────────────
    def _refresh_stats(self):
        for w in self.cards_frame.winfo_children():
            w.destroy()
        for r in self.stats_tree.get_children():
            self.stats_tree.delete(r)
        try:
            df = pd.read_csv(ATTENDANCE_FILE)
        except:
            return
        if df.empty:
            return
        total_days = df["Date"].nunique()
        today      = datetime.now().strftime("%Y-%m-%d")
        for title, val, col in [
            ("📅 Total Days", str(total_days),              BLUE),
            ("👥 Students",   str(df["Name"].nunique()),    ACCENT),
            ("✅ Today",      str(len(df[df["Date"]==today])), "#e3b341"),
            ("📝 Records",    str(len(df)),                 "#6e7681"),
        ]:
            c = tk.Frame(self.cards_frame, bg=col, padx=18, pady=12)
            c.pack(side="left", padx=8, pady=4)
            tk.Label(c, text=val,   font=("Courier New",22,"bold"),
                     bg=col, fg="white").pack()
            tk.Label(c, text=title, font=("Courier New",9),
                     bg=col, fg="white").pack()
        for name, grp in df.groupby("Name"):
            days = grp["Date"].nunique()
            pct  = round(days/total_days*100, 1) if total_days else 0
            self.stats_tree.insert("", "end",
                values=(name, grp["RegNo"].iloc[0],
                        days, grp["Date"].max(), f"{pct}%"),
                tags=("low" if pct < 75 else "ok",))
        self.stats_tree.tag_configure("low", foreground=RED)
        self.stats_tree.tag_configure("ok",  foreground="#3fb950")

    # ────────────────────────────────────────
    # ABSENTEE
    # ────────────────────────────────────────
    def _all_students(self):
        out = []
        for p in os.listdir(DATASET_PATH):
            if os.path.isdir(os.path.join(DATASET_PATH, p)):
                pts = p.split("_", 1)
                out.append({"Name": pts[0],
                             "RegNo": pts[1] if len(pts)>1 else ""})
        return out

    def _refresh_absent(self):
        for r in self.absent_tree.get_children():
            self.absent_tree.delete(r)
        date = self.absent_date.get().strip()
        try:    df = pd.read_csv(ATTENDANCE_FILE)
        except: return
        present = set(df[df["Date"]==date]["Name"].tolist())
        np_, na_ = 0, 0
        for s in self._all_students():
            if s["Name"] in present:
                self.absent_tree.insert("","end",
                    values=(s["Name"],s["RegNo"],"✅ Present"), tags=("p",))
                np_ += 1
            else:
                self.absent_tree.insert("","end",
                    values=(s["Name"],s["RegNo"],"❌ Absent"), tags=("a",))
                na_ += 1
        self.absent_tree.tag_configure("p", foreground="#3fb950")
        self.absent_tree.tag_configure("a", foreground=RED)
        self.absent_summary.config(
            text=(f"Date: {date}  |  Total: {np_+na_}"
                  f"  |  Present: {np_}  |  Absent: {na_}"))

    def _export_absent(self):
        date = self.absent_date.get().strip()
        try:    df = pd.read_csv(ATTENDANCE_FILE)
        except: return
        present = set(df[df["Date"]==date]["Name"].tolist())
        rows = [{"Name":s["Name"],"RegNo":s["RegNo"],"Date":date,
                 "Status":"Present" if s["Name"] in present else "Absent"}
                for s in self._all_students()]
        path = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV","*.csv")],
            initialfile=f"absentees_{date}.csv")
        if path:
            pd.DataFrame(rows).to_csv(path, index=False)
            messagebox.showinfo("Exported", f"Saved to {path}")

    # ────────────────────────────────────────
    # REGISTER
    # ────────────────────────────────────────
    def _start_register(self):
        name   = self.reg_name.get().strip()
        reg_no = self.reg_no.get().strip()
        n_imgs = self.reg_imgs.get()
        if not name or not reg_no:
            messagebox.showwarning("Missing", "Enter Name and Register No.")
            return
        folder = os.path.join(DATASET_PATH, f"{name}_{reg_no}")
        os.makedirs(folder, exist_ok=True)

        def _capture():
            cap2  = cv2.VideoCapture(0)
            count = 0
            while count < n_imgs:
                ret, frame = cap2.read()
                if not ret:
                    break
                gray  = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                for (x,y,w,h) in face_cascade.detectMultiScale(gray,1.3,5):
                    cv2.imwrite(f"{folder}/{count}.jpg",
                                cv2.resize(gray[y:y+h,x:x+w],(200,200)))
                    count += 1
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,220,60),2)
                    if count >= n_imgs:
                        break
                cv2.putText(frame, f"Capturing: {count}/{n_imgs}",
                            (10,35), cv2.FONT_HERSHEY_SIMPLEX,
                            1, (0,220,60), 2)
                pil   = Image.fromarray(
                            cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                        ).resize((480,300),Image.LANCZOS)
                imgtk = ImageTk.PhotoImage(image=pil)
                self.reg_cam_label.imgtk = imgtk
                self.reg_cam_label.config(image=imgtk, text="")
                self.reg_progress.config(text=f"Capturing {count}/{n_imgs}...")
                if cv2.waitKey(1) & 0xFF == 27:
                    break
            cap2.release()
            self.reg_cam_label.config(image="", text="Done!")
            self.reg_progress.config(
                text=f"✅ {count} images captured. Retraining...")
            self._load_model_async()
            messagebox.showinfo("Done",
                f"Registered {name} ({reg_no}) with {count} images.")
        threading.Thread(target=_capture, daemon=True).start()

    # ────────────────────────────────────────
    # CLEANUP
    # ────────────────────────────────────────
    def _on_close(self):
        self._stop_camera()
        self.destroy()


if __name__ == "__main__":
    app = AttendanceApp()
    app.mainloop()