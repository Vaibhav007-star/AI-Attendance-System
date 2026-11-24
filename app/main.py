import os
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, RedirectResponse

from app.config import settings
from app.core.database import init_db, SessionLocal
from app.core.security import get_password_hash
from app.models.department import Department
from app.models.user import User
from app.models.attendance import AttendanceLog
from app.services.face_engine import face_engine
from app.api.v1 import api_v1_router

templates_dir = Path(__file__).resolve().parent / "templates"
static_dir = Path(__file__).resolve().parent / "static"
templates = Jinja2Templates(directory=str(templates_dir))

def seed_initial_data():
    db = SessionLocal()
    try:
        # Create default departments
        if db.query(Department).count() == 0:
            depts = [
                Department(name="Artificial Intelligence", code="AI", manager_name="Dr. Alan Turing"),
                Department(name="Software Engineering", code="SWE", manager_name="Ada Lovelace"),
                Department(name="Human Resources", code="HR", manager_name="Sarah Connor"),
                Department(name="Product & Design", code="PRD", manager_name="Steve Wozniak")
            ]
            db.add_all(depts)
            db.commit()

        # Create default Admin
        admin = db.query(User).filter(User.email == "admin@visionattend.ai").first()
        if not admin:
            admin = User(
                employee_id="VA-001",
                full_name="VisionAttend Administrator",
                email="admin@visionattend.ai",
                hashed_password=get_password_hash("Admin@123"),
                phone="+1-555-0199",
                designation="System Admin",
                role="admin",
                department_id=1,
                is_active=True
            )
            db.add(admin)
            db.commit()

        # Seed sample demo staff if user table has only admin
        if db.query(User).count() == 1:
            demo_users = [
                User(employee_id="VA-101", full_name="Johnathan Vance", email="johnathan@visionattend.ai", hashed_password=get_password_hash("Welcome@123"), designation="Senior AI Researcher", role="employee", department_id=1),
                User(employee_id="VA-102", full_name="Elena Rostova", email="elena@visionattend.ai", hashed_password=get_password_hash("Welcome@123"), designation="Lead FullStack Architect", role="employee", department_id=2),
                User(employee_id="VA-103", full_name="Marcus Aurelius", email="marcus@visionattend.ai", hashed_password=get_password_hash("Welcome@123"), designation="HR Operations Lead", role="employee", department_id=3)
            ]
            db.add_all(demo_users)
            db.commit()

        # Reload Face Cache
        face_engine.reload_cache(db)
        print("[VisionAttend AI] Database initialized & Biometric cache loaded into RAM.")
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    seed_initial_data()
    yield
    # Shutdown
    print("[VisionAttend AI] Service shut down.")

app = FastAPI(
    title=settings.APP_NAME,
    description="Next-Generation Enterprise AI Face Recognition Attendance System with Anti-Spoofing and Liveness Verification",
    version="2.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Face Storage first so /static/faces resolves to storage/faces
faces_dir = settings.FACES_DIR
faces_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static/faces", StaticFiles(directory=str(faces_dir)), name="face_storage")

# Mount General Static Files (CSS, JS)
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Include API v1 routes
app.include_router(api_v1_router)

# Frontend UI Routes
@app.get("/", response_class=HTMLResponse)
def landing_page(request: Request):
    return templates.TemplateResponse(request=request, name="landing.html", context={"app_name": settings.APP_NAME})

@app.get("/kiosk", response_class=HTMLResponse)
def kiosk_page(request: Request):
    return templates.TemplateResponse(request=request, name="kiosk.html", context={"app_name": settings.APP_NAME})

@app.get("/dashboard", response_class=HTMLResponse)
def dashboard_page(request: Request):
    return templates.TemplateResponse(request=request, name="dashboard.html", context={"app_name": settings.APP_NAME})

@app.get("/employees", response_class=HTMLResponse)
def employees_page(request: Request):
    return templates.TemplateResponse(request=request, name="employees.html", context={"app_name": settings.APP_NAME})

@app.get("/records", response_class=HTMLResponse)
def records_page(request: Request):
    return templates.TemplateResponse(request=request, name="records.html", context={"app_name": settings.APP_NAME})

@app.get("/settings", response_class=HTMLResponse)
def settings_page(request: Request):
    return templates.TemplateResponse(request=request, name="settings.html", context={"app_name": settings.APP_NAME})

@app.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request):
    return templates.TemplateResponse(request=request, name="admin.html", context={"app_name": settings.APP_NAME})

@app.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html", context={"app_name": settings.APP_NAME})
