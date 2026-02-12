import cv2
import time
from datetime import datetime
from utils.timestamp import add_timestamp

def record_event(pre_buffer, cap, duration=10, fps=10):
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"storage/local/event_{timestamp}.avi"

    height, width, _ = pre_buffer[0].shape

    writer = cv2.VideoWriter(
        filename,
        cv2.VideoWriter_fourcc(*"XVID"),
        fps,
        (width, height)
    )

    # Write PRE-event frames
    for frame in pre_buffer:
        frame = add_timestamp(frame)
        writer.write(frame)

    # Write LIVE frames
    start = time.time()
    while time.time() - start < duration:
        ret, frame = cap.read()
        if ret:
            frame = add_timestamp(frame)
            writer.write(frame)

    writer.release()
    return filename
