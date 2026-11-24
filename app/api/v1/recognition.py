import io
import cv2
import base64
import numpy as np
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.orm import Session
from app.api.deps import get_db, require_admin
from app.config import settings
from app.models.user import User
from app.models.biometric import BiometricProfile
from app.schemas.dashboard import VerificationResponse
from app.services.face_engine import face_engine
from app.services.liveness_detector import liveness_detector
from app.services.attendance_service import attendance_service

router = APIRouter(prefix="/recognition", tags=["Biometrics & Face Recognition"])

def decode_image_bytes(image_bytes: bytes) -> np.ndarray:
    nparr = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if img is None:
        raise HTTPException(status_code=400, detail="Failed to decode image data")
    return img

def decode_base64_image(b64_str: str) -> np.ndarray:
    if "," in b64_str:
        b64_str = b64_str.split(",", 1)[1]
    img_bytes = base64.b64decode(b64_str)
    return decode_image_bytes(img_bytes)

@router.post("/enroll")
async def enroll_face(
    user_id: int = Form(...),
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Enrolls a user's face into the biometric profile database.
    Extracts high-dimensional embeddings and stores them for real-time matching.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if image is not None:
        content = await image.read()
        frame = decode_image_bytes(content)
    elif image_base64:
        frame = decode_base64_image(image_base64)
    else:
        raise HTTPException(status_code=400, detail="Image must be provided as file upload or base64")

    # Detect face
    faces = face_engine.detect_faces(frame)
    if not faces:
        raise HTTPException(status_code=400, detail="No face detected. Please ensure good lighting and look directly at camera.")
    
    # Take largest face
    faces.sort(key=lambda b: b[2] * b[3], reverse=True)
    x, y, w, h = faces[0]
    face_crop = frame[y:y+h, x:x+w]

    # Check liveness/quality
    liveness_res = liveness_detector.evaluate(face_crop)
    if not liveness_res["is_live"]:
        raise HTTPException(status_code=400, detail=f"Image quality insufficient: {liveness_res['reason']}")

    # Extract 128-D vector
    embedding = face_engine.extract_embedding(face_crop)

    # Save avatar image
    avatar_rel_path = f"/static/faces/{user.employee_id}.jpg"
    avatar_full_path = settings.FACES_DIR / f"{user.employee_id}.jpg"
    cv2.imwrite(str(avatar_full_path), face_crop)
    user.avatar_path = avatar_rel_path

    # Save/update biometric profile
    bio_profile = db.query(BiometricProfile).filter(BiometricProfile.user_id == user.id).first()
    if bio_profile:
        existing_list = bio_profile.get_embeddings()
        existing_list.append(embedding.tolist())
        # Keep maximum 5 samples per user
        if len(existing_list) > 5:
            existing_list = existing_list[-5:]
        bio_profile.set_embeddings(existing_list)
        bio_profile.sample_count = len(existing_list)
        bio_profile.quality_score = liveness_res["score"]
    else:
        bio_profile = BiometricProfile(
            user_id=user.id,
            embeddings_json="",
            sample_count=1,
            quality_score=liveness_res["score"]
        )
        bio_profile.set_embeddings([embedding.tolist()])
        db.add(bio_profile)

    db.commit()
    # Refresh in-memory cache
    face_engine.reload_cache(db)

    return {
        "success": True,
        "message": f"Biometric enrollment completed for {user.full_name} ({user.employee_id})",
        "sample_count": bio_profile.sample_count,
        "quality_score": liveness_res["score"],
        "avatar_url": user.avatar_path
    }

@router.post("/verify", response_model=VerificationResponse)
async def verify_face_frame(
    image: Optional[UploadFile] = File(None),
    image_base64: Optional[str] = Form(None),
    auto_record: bool = Form(True),
    db: Session = Depends(get_db)
):
    """
    Real-time face verification and liveness evaluation from camera frame.
    Automatically logs or updates attendance when a verified match is recognized!
    """
    if image is not None:
        content = await image.read()
        frame = decode_image_bytes(content)
    elif image_base64:
        frame = decode_base64_image(image_base64)
    else:
        raise HTTPException(status_code=400, detail="No frame payload provided")

    faces = face_engine.detect_faces(frame)
    if not faces:
        return VerificationResponse(
            matched=False,
            confidence=0.0,
            liveness_score=0.0,
            is_live=False,
            action="none",
            message="No face detected in frame"
        )

    # Pick largest face
    faces.sort(key=lambda b: b[2] * b[3], reverse=True)
    x, y, w, h = faces[0]
    face_crop = frame[y:y+h, x:x+w]

    # Evaluate Liveness / Anti-Spoofing
    liveness_res = liveness_detector.evaluate(face_crop)
    if not liveness_res["is_live"]:
        return VerificationResponse(
            matched=False,
            confidence=0.0,
            liveness_score=liveness_res["score"],
            is_live=False,
            action="spoof_rejected",
            message=f"Presentation attack detected: {liveness_res['reason']}"
        )

    # Extract embedding & match against enrolled database
    probe_vec = face_engine.extract_embedding(face_crop)
    match_res = face_engine.match_face(probe_vec)

    if not match_res or not match_res["matched"]:
        return VerificationResponse(
            matched=False,
            confidence=match_res.get("confidence", 0.0) if match_res else 0.0,
            liveness_score=liveness_res["score"],
            is_live=True,
            action="unrecognized",
            message="Face detected but not enrolled in database"
        )

    user_id = match_res["user_id"]
    confidence = match_res["confidence"]

    action = "recognized"
    att_message = f"Welcome, {match_res['full_name']}!"

    # Auto Record Attendance
    if auto_record:
        att_res = attendance_service.record_attendance(
            db=db,
            user_id=user_id,
            confidence=confidence,
            liveness_score=liveness_res["score"],
            verification_method="Face-AI",
            face_crop=face_crop
        )
        action = att_res.get("action", "recorded")
        att_message = att_res.get("message", att_message)

    return VerificationResponse(
        matched=True,
        user_id=user_id,
        employee_id=match_res["employee_id"],
        full_name=match_res["full_name"],
        department=match_res["department"],
        confidence=confidence,
        liveness_score=liveness_res["score"],
        is_live=True,
        action=action,
        message=att_message
    )
