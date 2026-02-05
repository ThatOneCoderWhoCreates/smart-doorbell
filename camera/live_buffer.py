import cv2
import time
from collections import deque

class LiveCameraBuffer:
    def __init__(self, buffer_seconds=15, fps=10):
        self.fps = fps
        self.buffer_size = buffer_seconds * fps
        self.buffer = deque(maxlen=self.buffer_size)

        self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
        if not self.cap.isOpened():
            raise RuntimeError("Camera not accessible")

        # Set resolution (optional)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    def read_frame(self):
        ret, frame = self.cap.read()
        if ret:
            self.buffer.append(frame)
        return ret, frame

    def get_buffer_frames(self):
        return list(self.buffer)

    def release(self):
        self.cap.release()
