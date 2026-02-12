import os
import platform
from datetime import datetime
import yaml
from utils.logger import log

IS_WINDOWS = platform.system() == "Windows"

with open("config.yaml") as f:
    config = yaml.safe_load(f)

STORAGE_PATH = config["storage"]["path"]

def capture_image():
    os.makedirs(STORAGE_PATH, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{STORAGE_PATH}/visitor_{timestamp}.jpg"

    if IS_WINDOWS:
        return capture_with_webcam(filename)
    else:
        return capture_with_libcamera(filename)


def capture_with_webcam(filename):
    try:
        import cv2
        import time

        # Force DirectShow backend
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

        if not cap.isOpened():
            raise RuntimeError("Webcam not accessible")

        # Warm-up camera (VERY IMPORTANT on Windows)
        time.sleep(1)

        ret, frame = cap.read()
        cap.release()

        if not ret or frame is None:
            raise RuntimeError("Failed to capture frame")

        cv2.imwrite(filename, frame)
        log(f"Webcam image captured: {filename}")
        return filename

    except Exception as e:
        log(f"Webcam error: {e}")
        return None



def capture_with_libcamera(filename):
    import subprocess
    try:
        subprocess.run(
            ["libcamera-still", "-o", filename, "--nopreview"],
            check=True
        )
        log(f"Pi camera image captured: {filename}")
        return filename

    except Exception as e:
        log(f"Pi camera error: {e}")
        return None
