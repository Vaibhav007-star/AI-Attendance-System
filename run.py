#!/usr/bin/env python3
"""
VisionAttend AI - Primary Application Launcher
Starts the FastAPI Web Service, Dashboard & Autonomous Kiosk.
"""

import sys
import argparse
import uvicorn
from app.config import settings
from app.core.database import init_db
from app.main import seed_initial_data

def main():
    parser = argparse.ArgumentParser(description="VisionAttend AI Application Runner")
    parser.add_argument("--host", default=settings.HOST, help="Bind socket host")
    parser.add_argument("--port", type=int, default=settings.PORT, help="Bind socket port")
    parser.add_argument("--reload", action="store_true", help="Enable code auto-reloading")
    parser.add_argument("--init-db", action="store_true", help="Initialize database schema and seed data only")
    parser.add_argument("--seed", action="store_true", help="Seed full enterprise workforce dataset for demo showcases")
    parser.add_argument("--desktop", action="store_true", help="Launch native OpenCV desktop camera kiosk")
    parser.add_argument("--camera", type=int, default=0, help="Webcam device index for desktop kiosk")
    args = parser.parse_args()

    if args.seed:
        from seed_demo_data import seed_enterprise_data
        seed_enterprise_data()
        return

    if args.init_db:
        print("[VisionAttend AI] Initializing database...")
        init_db()
        seed_initial_data()
        print("[VisionAttend AI] Database successfully initialized.")
        return

    if args.desktop:
        from desktop_kiosk import run_desktop_kiosk
        run_desktop_kiosk(args.camera)
        return

    print("=" * 65)
    print("  🚀 VisionAttend AI - Enterprise Facial Biometric Platform")
    print(f"  🌐 Web Kiosk:   http://localhost:{args.port}/kiosk")
    print(f"  📊 Dashboard:   http://localhost:{args.port}/dashboard")
    print(f"  👥 Employees:   http://localhost:{args.port}/employees")
    print(f"  📑 Records:     http://localhost:{args.port}/records")
    print(f"  📡 API Docs:    http://localhost:{args.port}/docs")
    print("=" * 65)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )

if __name__ == "__main__":
    main()
