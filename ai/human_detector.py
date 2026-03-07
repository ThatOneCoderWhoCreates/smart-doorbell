from ultralytics import YOLO
import time
import cv2

class HumanDetector:
    def __init__(self):
        self.model = YOLO("models/yolov8n.pt")

        # Face detector for mask / helmet suspicion
        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
        )

        self.first_detected_time = None
        self.last_seen_time = None
        self.suspicious_triggered = False

    def analyze_frame(self, frame):
        results = self.model(frame, verbose=False)
        boxes = results[0].boxes

        best_box = None
        best_conf = 0

        if boxes is not None and len(boxes) > 0:
            for box in boxes:
                conf = float(box.conf[0])
                if conf > best_conf:
                    best_conf = conf
                    best_box = box

        current_time = time.time()
        suspicious = False
        label = None

        # ----------------------------
        # WEAPON EDGE CASE DETECTION
        # ----------------------------
        if boxes is not None:
            for box in boxes:
                class_id = int(box.cls[0])
                class_name = self.model.names[class_id].lower()

                if class_name in ["knife", "gun", "weapon"]:
                    suspicious = True
                    label = f"SUSPICIOUS {class_name.upper()} DETECTED"
                    break

        # ----------------------------
        # MAIN OBJECT LOGIC (UNCHANGED)
        # ----------------------------
        if best_box is not None and not suspicious:
            class_id = int(best_box.cls[0])
            class_name = self.model.names[class_id]

            if self.first_detected_time is None:
                self.first_detected_time = current_time

            self.last_seen_time = current_time
            duration = current_time - self.first_detected_time

            # ----------------------------
            # RECORD ANY PERSON
            # trigger an event for ANY person detected
            # ----------------------------
            if class_name.lower() == "person":
                suspicious = True # This will trigger record_event in main.py
                label = f"PERSON DETECTED"
            else:
                label = f"REGULAR {class_name.upper()}"
                
            # Keep loitering label logic
            if duration > 10 and class_name.lower() == "person" and not self.suspicious_triggered:
                label = f"SUSPICIOUS LOITERING"
                self.suspicious_triggered = True

            # ----------------------------
            # MASK / HELMET EDGE CASE
            # Only if person detected
            # ----------------------------
            if class_name.lower() == "person":
                x1, y1, x2, y2 = map(int, best_box.xyxy[0])
                person_crop = frame[y1:y2, x1:x2]

                if person_crop.size > 0:
                    gray = cv2.cvtColor(person_crop, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.3,
                        minNeighbors=5
                    )

                    if len(faces) == 0 and duration > 5:
                        suspicious = True
                        label = "SUSPICIOUS FACE COVERED / HELMET"

        else:
            # Reset after grace period (UNCHANGED)
            if self.last_seen_time and (current_time - self.last_seen_time > 2):
                self.first_detected_time = None
                self.suspicious_triggered = False

        annotated = results[0].plot()
        return annotated, label, suspicious