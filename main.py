import cv2
import time
import os
import threading
from datetime import datetime
from detector import detect_person

VIDEO_FOLDER = "storage/local"
os.makedirs(VIDEO_FOLDER, exist_ok=True)

FPS = 10
STOP_DELAY = 5   # seconds to wait before stopping recording

cap = None
running = False
recording = False
video_writer = None
last_person_time = None
latest_frame = None
lock = threading.Lock()


def start_system():
    global cap, running

    if running:
        return

    cap = cv2.VideoCapture(0)

    if not cap.isOpened():
        print("Camera failed to open")
        return

    running = True
    print("Camera started successfully")

    while running:
        ret, frame = cap.read()
        if not ret:
            continue

        person_detected, annotated = detect_person(frame)

        # Save frame for UI live feed
        with lock:
            global latest_frame
            latest_frame = annotated.copy()

        handle_recording(annotated, person_detected)

        time.sleep(1 / FPS)


def stop_system():
    global running, cap, video_writer, recording

    running = False

    if video_writer:
        video_writer.release()
        video_writer = None

    if cap:
        cap.release()
        cap = None

    recording = False
    print("System stopped")


def handle_recording(frame, person_detected):
    global recording, video_writer, last_person_time

    current_time = time.time()

    # Person detected
    if person_detected:
        last_person_time = current_time

        if not recording:
            start_new_recording(frame)

    # If currently recording
    if recording:
        if person_detected:
            video_writer.write(frame)
        else:
            if current_time - last_person_time <= STOP_DELAY:
                video_writer.write(frame)
            else:
                stop_recording()


def start_new_recording(frame):
    global video_writer, recording

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{VIDEO_FOLDER}/visit_{timestamp}.mp4"

    height, width, _ = frame.shape

    video_writer = cv2.VideoWriter(
        filename,
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS,
        (width, height)
    )

    recording = True
    print(f"Started recording: {filename}")


def stop_recording():
    global video_writer, recording

    if video_writer:
        video_writer.release()
        video_writer = None

    recording = False
    print("Recording stopped")


def get_latest_frame():
    with lock:
        return latest_frame
