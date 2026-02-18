import time
from ultralytics import YOLO

model = YOLO("yolov8n.pt")

person_present_since = None
SUSPICIOUS_TIME = 10  # seconds


def detect_person(frame):
    global person_present_since

    results = model(frame, classes=[0], verbose=False)  # person class only

    detected = False

    for r in results:
        if len(r.boxes) > 0:
            detected = True

            for box in r.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                conf = float(box.conf[0])

                label = f"Person {conf:.2f}"
                color = (0, 255, 0)

                frame = r.plot()  # draw bounding boxes

    if detected:
        if person_present_since is None:
            person_present_since = time.time()

        duration = time.time() - person_present_since

        if duration > SUSPICIOUS_TIME:
            return frame, True  # suspicious detected
        else:
            return frame, False
    else:
        person_present_since = None
        return frame, False
