import os
import platform
os.environ["OPENCV_AVFOUNDATION_SKIP_AUTH"] = "1"

import cv2
import time
import threading
import shutil
from collections import deque
from datetime import datetime
from detector import detect_person

BUFFER_SECONDS = 10
FPS = 10
POST_EVENT_SECONDS = 10
VIDEO_FOLDER = "storage/local"

os.makedirs(VIDEO_FOLDER, exist_ok=True)

cap = None
buffer = deque(maxlen=BUFFER_SECONDS * FPS)
running = False
recording = False
latest_frame = None
lock = threading.Lock()


def add_timestamp(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, timestamp,
                (10, frame.shape[0] - 10),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2)
    return frame


def start_system():
    global cap, running, latest_frame

    if running:
        return

    system = platform.system()

    if system == "Darwin":
        cap = cv2.VideoCapture(0, cv2.CAP_AVFOUNDATION)
    elif system == "Windows":
        cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera failed to open")
        return

    running = True
    print("Camera started")

    while running:
        ret, frame = cap.read()
        if not ret:
            continue

        frame = add_timestamp(frame)

        # Run AI detection
        frame, suspicious = detect_person(frame)

        latest_frame = frame.copy()

        with lock:
            buffer.append(frame.copy())

        # Trigger recording only if suspicious
        if suspicious and not recording:
            print("Suspicious activity detected!")
            handle_event()

        time.sleep(1 / FPS)


def stop_system():
    global running, cap
    running = False

    if cap:
        cap.release()
        cap = None

    print("System stopped")


def get_latest_frame():
    return latest_frame


def handle_event():
    global recording

    if recording:
        return

    if len(buffer) < FPS:
        return

    recording = True
    print("Recording event...")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    temp_folder = f"{VIDEO_FOLDER}/temp_{timestamp}"
    os.makedirs(temp_folder, exist_ok=True)

    frame_index = 0

    # Save pre-event frames
    with lock:
        for frame in buffer:
            cv2.imwrite(f"{temp_folder}/frame_{frame_index:04d}.jpg", frame)
            frame_index += 1

    # Save post-event frames
    start = time.time()
    while time.time() - start < POST_EVENT_SECONDS:
        ret, frame = cap.read()
        if ret:
            frame = add_timestamp(frame)
            cv2.imwrite(f"{temp_folder}/frame_{frame_index:04d}.jpg", frame)
            frame_index += 1

    output_file = f"{VIDEO_FOLDER}/event_{timestamp}.mp4"

    os.system(
        f"ffmpeg -y -framerate {FPS} "
        f"-i {temp_folder}/frame_%04d.jpg "
        f"-c:v libx264 -pix_fmt yuv420p {output_file}"
    )

    shutil.rmtree(temp_folder)

    print(f"Saved: {output_file}")

    recording = False
