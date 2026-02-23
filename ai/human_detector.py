from ultralytics import YOLO
import time

class HumanDetector:
    def __init__(self):
        self.model = YOLO("models/yolov8n.pt")
        self.first_detected_time = None
        self.last_seen_time = None
        self.suspicious_triggered = False

    def analyze_frame(self, frame):
        # Remove class filtering to detect anything
        results = self.model(frame, verbose=False)

        boxes = results[0].boxes
        
        # Determine the most prominent object in the frame (highest confidence)
        best_box = None
        best_conf = 0
        if len(boxes) > 0:
             for box in boxes:
                 conf = float(box.conf[0])
                 if conf > best_conf:
                     best_conf = conf
                     best_box = box

        current_time = time.time()
        suspicious = False
        label = None

        if best_box is not None:
            class_id = int(best_box.cls[0])
            class_name = self.model.names[class_id]
            
            if self.first_detected_time is None:
                self.first_detected_time = current_time

            self.last_seen_time = current_time
            duration = current_time - self.first_detected_time

            if duration > 10 and not self.suspicious_triggered:
                suspicious = True
                label = f"SUSPICIOUS {class_name.upper()}"
                self.suspicious_triggered = True
            else:
                label = f"REGULAR {class_name.upper()}"

        else:
            # Allow 2 second grace period before reset
            if self.last_seen_time and (current_time - self.last_seen_time > 2):
                self.first_detected_time = None
                self.suspicious_triggered = False

        annotated = results[0].plot()
        return annotated, label, suspicious
