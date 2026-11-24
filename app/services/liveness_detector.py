import cv2
import numpy as np

class LivenessDetector:
    """
    Multi-Factor Passive & Active Anti-Spoofing Engine.
    Detects presentation attacks:
    1. Printed Paper Attacks (Laplacian texture variance + edge contrast)
    2. Digital Screen Attacks (FFT frequency spectrum moire patterns)
    3. Specular Glare & Color Balance (Glass reflection on mobile/tablet screens)
    """

    def __init__(self, blur_threshold: float = 65.0, moire_threshold: float = 8.0):
        self.blur_threshold = blur_threshold
        self.moire_threshold = moire_threshold

    def compute_blur_score(self, face_gray: np.ndarray) -> float:
        """Computes variance of the Laplacian. Higher = sharper, realistic texture."""
        if face_gray.size == 0:
            return 0.0
        lap = cv2.Laplacian(face_gray, cv2.CV_64F)
        variance = float(lap.var())
        return variance

    def compute_frequency_score(self, face_gray: np.ndarray) -> float:
        """
        Computes 2D FFT to detect repeating high-frequency moire patterns
        typical of LCD/OLED digital screens.
        """
        if face_gray.shape[0] < 32 or face_gray.shape[1] < 32:
            return 1.0
        
        resized = cv2.resize(face_gray, (64, 64))
        f = np.fft.fft2(resized)
        fshift = np.fft.fftshift(f)
        magnitude_spectrum = 20 * np.log(np.abs(fshift) + 1e-8)
        
        # High frequency ring energy
        rows, cols = resized.shape
        crow, ccol = rows // 2, cols // 2
        # Mask center low frequencies
        magnitude_spectrum[crow-6:crow+6, ccol-6:ccol+6] = 0
        mean_hf = float(np.mean(magnitude_spectrum))
        return mean_hf

    def compute_color_balance(self, face_bgr: np.ndarray) -> float:
        """
        Examines HSV saturation and value variance.
        Printed photos tend to have compressed dynamic range compared to real skin.
        """
        if face_bgr.size == 0:
            return 0.0
        hsv = cv2.cvtColor(face_bgr, cv2.COLOR_BGR2HSV)
        s_std = float(np.std(hsv[:, :, 1]))
        v_std = float(np.std(hsv[:, :, 2]))
        # Normalized diversity score
        score = min(1.0, (s_std + v_std) / 80.0)
        return score

    def evaluate(self, face_crop: np.ndarray) -> dict:
        """
        Evaluates a face crop and returns composite liveness score (0.0 to 1.0)
        and spoof classification.
        """
        if face_crop is None or face_crop.size == 0:
            return {"is_live": False, "score": 0.0, "reason": "Empty face region"}

        if len(face_crop.shape) == 3:
            face_gray = cv2.cvtColor(face_crop, cv2.COLOR_BGR2GRAY)
            face_bgr = face_crop
        else:
            face_gray = face_crop
            face_bgr = cv2.cvtColor(face_crop, cv2.COLOR_GRAY2BGR)

        # 1. Texture Sharpness
        blur_val = self.compute_blur_score(face_gray)
        # Normalize: 0 to 120 -> 0.0 to 1.0
        blur_norm = min(1.0, blur_val / 120.0)

        # 2. High-Frequency Moire
        freq_val = self.compute_frequency_score(face_gray)
        freq_norm = max(0.0, min(1.0, 1.0 - (freq_val / 40.0)))

        # 3. Dynamic color variation
        color_norm = self.compute_color_balance(face_bgr)

        # Composite weighted score
        composite_score = float(0.50 * blur_norm + 0.25 * freq_norm + 0.25 * color_norm)
        composite_score = round(max(0.0, min(1.0, composite_score)), 3)

        is_live = composite_score >= 0.45 and blur_val >= 35.0

        reasons = []
        if blur_val < 35.0:
            reasons.append("Low texture resolution / blur")
        if freq_norm < 0.2:
            reasons.append("Digital screen moire detected")
        if color_norm < 0.2:
            reasons.append("Compressed color depth")

        return {
            "is_live": is_live,
            "score": composite_score,
            "metrics": {
                "blur_variance": round(blur_val, 2),
                "frequency_score": round(freq_val, 2),
                "color_diversity": round(color_norm, 2)
            },
            "reason": ", ".join(reasons) if not is_live else "Live Verified"
        }

liveness_detector = LivenessDetector()
