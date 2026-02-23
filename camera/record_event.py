import cv2
import os
from datetime import datetime


def record_event(pre_frames, cap, duration=10, fps=10):
    if not pre_frames:
        print("No pre-buffer frames available")
        return None

    project_root = os.getcwd()
    save_dir = os.path.join(project_root, "storage", "local")
    os.makedirs(save_dir, exist_ok=True)

    filename = os.path.join(
        save_dir,
        f"event_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.avi"
    )

    height, width, _ = pre_frames[0].shape

    fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # Windows-safe codec
    out = cv2.VideoWriter(filename, fourcc, fps, (width, height))

    if not out.isOpened():
        print("VideoWriter failed to open")
        return None

    # Write pre-event frames
    for frame in pre_frames:
        out.write(frame)

    # Write post-event frames
    frame_count = duration * fps
    for _ in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        out.write(frame)

    out.release()

    return filename
