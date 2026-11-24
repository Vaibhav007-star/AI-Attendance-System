import os
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.config import settings
from app.models.user import User
from app.models.biometric import BiometricProfile

BASE_DIR = Path(__file__).resolve().parent.parent.parent
YUNET_PATH = BASE_DIR / "data" / "face_detection_yunet.onnx"
SFACE_PATH = BASE_DIR / "data" / "face_recognition_sface.onnx"

class FaceEngine:
    """
    Enterprise Deep Learning Face Recognition Engine (OpenCV 5 YuNet + SFace).
    - YuNet: High-accuracy CNN face detector with 5-point landmark localization.
    - SFace: Deep representation model extracting 128-D L2-normalized feature embeddings.
    - Cosine similarity matching in spherical hyperspace.
    """

    def __init__(self):
        self.detector = None
        self.recognizer = None
        self._init_models()

        # In-memory fast cache of user embeddings: {user_id: [np.ndarray, ...]}
        self.enrolled_cache: Dict[int, List[np.ndarray]] = {}
        self.user_info_cache: Dict[int, Dict[str, Any]] = {}

    def _init_models(self):
        try:
            if YUNET_PATH.exists() and hasattr(cv2, "FaceDetectorYN_create"):
                self.detector = cv2.FaceDetectorYN_create(
                    str(YUNET_PATH), "", (320, 320),
                    score_threshold=settings.FACE_DETECTION_CONFIDENCE,
                    nms_threshold=0.3,
                    top_k=5000
                )
        except Exception as e:
            print(f"[FaceEngine] YuNet detector init warning: {e}")

        try:
            if SFACE_PATH.exists() and hasattr(cv2, "FaceRecognizerSF_create"):
                self.recognizer = cv2.FaceRecognizerSF_create(str(SFACE_PATH), "")
        except Exception as e:
            print(f"[FaceEngine] SFace recognizer init warning: {e}")

    def detect_faces(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Detects faces in BGR image.
        Returns list of bounding boxes: [(x, y, w, h), ...]
        """
        if image is None or image.size == 0:
            return []

        h, w = image.shape[:2]

        if self.detector is not None:
            try:
                self.detector.setInputSize((w, h))
                _, faces = self.detector.detect(image)
                if faces is not None:
                    results = []
                    for face in faces:
                        fx = max(0, int(face[0]))
                        fy = max(0, int(face[1]))
                        fw = min(w - fx, int(face[2]))
                        fh = min(h - fy, int(face[3]))
                        if fw > 20 and fh > 20:
                            results.append((fx, fy, fw, fh))
                    return results
            except Exception as e:
                print(f"[FaceEngine] Detection error: {e}")

        # Fallback: simple center crop if image is already a face crop
        return [(0, 0, w, h)]

    def extract_embedding(self, face_crop: np.ndarray) -> np.ndarray:
        """
        Extracts 128-dimensional deep feature representation vector.
        L2 normalized to unit sphere.
        """
        if face_crop is None or face_crop.size == 0:
            return np.zeros(128, dtype=np.float32)

        # Ensure 3-channel BGR
        if len(face_crop.shape) == 2:
            face_crop = cv2.cvtColor(face_crop, cv2.COLOR_GRAY2BGR)

        if self.recognizer is not None:
            try:
                # Resize to standard 112x112 for deep network
                aligned = cv2.resize(face_crop, (112, 112))
                feature = self.recognizer.feature(aligned)
                if feature is not None:
                    vec = feature.flatten().astype(np.float32)
                    norm = np.linalg.norm(vec)
                    if norm > 0:
                        vec = vec / norm
                    return vec
            except Exception as e:
                print(f"[FaceEngine] SFace feature extraction error: {e}")

        # Algorithmic fallback: Gradient & spatial descriptor (128-D)
        gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
        resized = cv2.resize(gray, (96, 96))
        gx = cv2.Sobel(resized, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(resized, cv2.CV_32F, 0, 1, ksize=3)
        mag, angle = cv2.cartToPolar(gx, gy, angleInDegrees=True)

        features = []
        for r in range(4):
            for c in range(4):
                sub_mag = mag[r*24:(r+1)*24, c*24:(c+1)*24]
                sub_ang = angle[r*24:(r+1)*24, c*24:(c+1)*24]
                hist, _ = np.histogram(sub_ang, bins=8, range=(0, 360), weights=sub_mag)
                features.extend(hist.tolist())

        vec = np.array(features, dtype=np.float32)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    @staticmethod
    def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
        """Calculates cosine similarity between two unit vectors."""
        dot = float(np.dot(v1, v2))
        return max(-1.0, min(1.0, dot))

    def reload_cache(self, db: Session):
        """Loads enrolled user embeddings into RAM for instant lookup."""
        self.enrolled_cache.clear()
        self.user_info_cache.clear()

        profiles = db.query(BiometricProfile).all()
        for prof in profiles:
            user = prof.user
            if user and user.is_active:
                raw_embeddings = prof.get_embeddings()
                np_embeddings = [np.array(e, dtype=np.float32) for e in raw_embeddings if len(e) == 128]
                if np_embeddings:
                    self.enrolled_cache[user.id] = np_embeddings
                    self.user_info_cache[user.id] = {
                        "user_id": user.id,
                        "employee_id": user.employee_id,
                        "full_name": user.full_name,
                        "department": user.department.name if user.department else "General",
                        "avatar": user.avatar_path
                    }

    def match_face(self, probe_vector: np.ndarray, threshold: Optional[float] = None) -> Optional[dict]:
        """
        Finds the closest enrolled identity in Euclidean / Cosine hyperspace.
        """
        if threshold is None:
            threshold = settings.FACE_RECOGNITION_THRESHOLD

        best_score = -1.0
        best_user_id = None

        for user_id, gallery_vectors in self.enrolled_cache.items():
            for g_vec in gallery_vectors:
                sim = self.cosine_similarity(probe_vector, g_vec)
                if sim > best_score:
                    best_score = sim
                    best_user_id = user_id

        if best_user_id is not None and best_score >= threshold:
            info = self.user_info_cache.get(best_user_id, {})
            return {
                "user_id": best_user_id,
                "employee_id": info.get("employee_id"),
                "full_name": info.get("full_name"),
                "department": info.get("department"),
                "confidence": round(best_score, 4),
                "matched": True
            }

        return {
            "user_id": None,
            "confidence": round(max(0.0, best_score), 4) if best_score > 0 else 0.0,
            "matched": False
        }

face_engine = FaceEngine()
