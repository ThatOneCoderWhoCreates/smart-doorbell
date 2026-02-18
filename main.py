import cv2
import time
import os
import threading
from collections import deque
from datetime import datetime

from detector import detect_person

BUFFER_SECONDS = 5
FPS = 20
VIDEO_FOLDER = "storage/local"

os.makedirs(VIDEO_FOLDER, exist_ok=True)

cap = None
running = False
recording = False
writer = None

buffer = deque(maxlen=BUFFER_SECONDS * FPS)
latest_frame = None


def get_latest_frame():
    return latest_frame


def start_system():
    global cap, running, recording, writer, latest_frame

    if running:
        return

    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)

    if not cap.isOpened():
        print("Camera failed to open")
        return

    running = True
    print("System Started")

    while running:
        ret, frame = cap.read()
        if not ret:
            continue

        person_detected, annotated = detect_person(frame)

        latest_frame = annotated.copy()

        buffer.append(frame.copy())

        # -----------------------------
        # START RECORDING IF PERSON
        # -----------------------------
        if person_detected and not recording:

            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"{VIDEO_FOLDER}/event_{timestamp}.mp4"

            height, width, _ = frame.shape

            writer = cv2.VideoWriter(
                filename,
                cv2.VideoWriter_fourcc(*"mp4v"),
                FPS,
                (width, height)
            )

            # Write buffered frames
            for f in buffer:
                writer.write(f)

            recording = True
            print("Recording started")

        # -----------------------------
        # WRITE FRAME IF RECORDING
        # -----------------------------
        if recording:
            writer.write(frame)

            # STOP RECORDING IF PERSON GONE
            if not person_detected:
                writer.release()
                writer = None
                recording = False
                print("Recording stopped (no person detected)")

        time.sleep(1 / FPS)


def stop_system():
    global running, cap, recording, writer

    running = False

    if recording and writer:
        writer.release()

    if cap:
        cap.release()

    print("System Stopped")
