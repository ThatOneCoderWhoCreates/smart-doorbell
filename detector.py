from ultralytics import YOLO
import time
import cv2

# Load YOLO model
model = YOLO("yolov8n.pt")

PERSON_CLASS_ID = 0   # COCO class 0 = person
CONF_THRESHOLD = 0.5
SUSPICIOUS_TIME = 10  # seconds

# Timer variable
person_start_time = None


def detect_person(frame):
    """
    Returns:
        person_detected (bool)
        annotated_frame (frame with bounding boxes + label)
    """

    global person_start_time

    results = model(frame, classes=[PERSON_CLASS_ID], verbose=False)

    person_detected = False

    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])

                if cls == PERSON_CLASS_ID and conf >= CONF_THRESHOLD:
                    person_detected = True

    annotated_frame = results[0].plot()

    # -----------------------------
    # TIMER LOGIC
    # -----------------------------
    label = ""
    color = (0, 255, 0)

    if person_detected:
        if person_start_time is None:
            person_start_time = time.time()

        duration = time.time() - person_start_time

        if duration >= SUSPICIOUS_TIME:
            label = "SUSPICIOUS PERSON"
            color = (0, 0, 255)
        else:
            label = "NORMAL VISITOR"
            color = (0, 255, 0)

        # Display timer
        cv2.putText(
            annotated_frame,
            f"Time: {int(duration)}s",
            (30, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            2
        )

    else:
        person_start_time = None

    # Display label
    if label:
        cv2.putText(
            annotated_frame,
            label,
            (30, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            color,
            3
        )

    return person_detected, annotated_frame
