from ultralytics import YOLO

model = YOLO("yolov8n.pt")

def detect_person(frame):
    results = model(frame, verbose=False)

    for result in results:
        for box in result.boxes:
            cls = int(box.cls[0])
            label = model.names[cls]

            if label == "person":
                return True

    return False
