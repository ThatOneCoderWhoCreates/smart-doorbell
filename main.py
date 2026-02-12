import cv2
import time
import threading
import os
from collections import deque
from datetime import datetime
import tkinter as tk
from PIL import Image, ImageTk

# -------- SETTINGS --------
BUFFER_SECONDS = 10
FPS = 10
POST_EVENT_SECONDS = 10
VIDEO_FOLDER = "storage/local"

os.makedirs(VIDEO_FOLDER, exist_ok=True)

# -------- CAMERA --------
cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

buffer = deque(maxlen=BUFFER_SECONDS * FPS)
recording = False

# -------- GUI --------
root = tk.Tk()
root.title("Smart Doorbell")

video_label = tk.Label(root)
video_label.pack()

status_label = tk.Label(root, text="Status: Idle", font=("Arial", 12))
status_label.pack()

# -------- FUNCTIONS --------

def add_timestamp(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cv2.putText(frame, timestamp, (10, 460),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6,
                (0, 255, 0), 2)
    return frame


def update_frame():
    ret, frame = cap.read()
    if ret:
        frame = add_timestamp(frame)
        buffer.append(frame.copy())

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb)
        imgtk = ImageTk.PhotoImage(image=img)

        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)

    root.after(int(1000/FPS), update_frame)


def record_event():
    global recording
    if recording:
        return

    recording = True
    status_label.config(text="Status: Recording Event")

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    filename = f"{VIDEO_FOLDER}/event_{timestamp}.avi"

    height, width, _ = buffer[0].shape
    writer = cv2.VideoWriter(
        filename,
        cv2.VideoWriter_fourcc(*"XVID"),
        FPS,
        (width, height)
    )

    # Write pre-event frames
    for frame in buffer:
        writer.write(frame)

    # Write post-event frames
    start = time.time()
    while time.time() - start < POST_EVENT_SECONDS:
        ret, frame = cap.read()
        if ret:
            frame = add_timestamp(frame)
            writer.write(frame)

    writer.release()
    status_label.config(text=f"Saved: {filename}")
    recording = False


trigger_button = tk.Button(root, text="Trigger Event", command=lambda: threading.Thread(target=record_event).start())
trigger_button.pack(pady=10)

# -------- START --------
update_frame()
root.mainloop()

cap.release()
cv2.destroyAllWindows()
