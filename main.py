import cv2
import mediapipe as mp

# Initialize MediaPipe Face Detection
mp_face = mp.solutions.face_detection
face_detection = mp_face.FaceDetection(model_selection=0, min_detection_confidence=0.5)

# Initialize drawing
mp_draw = mp.solutions.drawing_utils

# Start webcam
cap = cv2.VideoCapture(0)

while True:
    success, img = cap.read()
    if not success:
        break

    # Convert image to RGB
    img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Detect faces
    results = face_detection.process(img_rgb)

    if results.detections:
        for detection in results.detections:
            mp_draw.draw_detection(img, detection)

    # ✅ Add text on screen
    cv2.putText(img, "Press Q or ESC to Exit", (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

    # Show output
    cv2.imshow("Face Detection", img)

    key = cv2.waitKey(1) & 0xFF

    # ✅ Exit with ESC or Q
    if key == 27 or key == ord('q'):
        break

    # ✅ Exit if window closed
    if cv2.getWindowProperty("Face Detection", cv2.WND_PROP_VISIBLE) < 1:
        break

cap.release()
cv2.destroyAllWindows()