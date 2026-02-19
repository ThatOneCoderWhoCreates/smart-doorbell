from ultralytics import YOLO

model = YOLO("yolov8n.pt")

PERSON_CLASS_ID = 0   # COCO class id for person
CONF_THRESHOLD = 0.5


def detect_person(frame):
    """
    Returns:
        person_detected (bool)
        annotated_frame (with normal YOLO labels)
    """

    results = model(frame, verbose=False)

    person_detected = False

    for result in results:
        if result.boxes is not None:
            for box in result.boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])

                if cls == PERSON_CLASS_ID and conf >= CONF_THRESHOLD:
                    person_detected = True

    annotated_frame = results[0].plot()

    return person_detected, annotated_frame
