import cv2
from collections import deque

class LiveCameraBuffer:
    def __init__(self, buffer_seconds=15, fps=10):
        self.cap = cv2.VideoCapture(0)
        self.fps = fps
        self.buffer_size = buffer_seconds * fps
        self.buffer = deque(maxlen=self.buffer_size)

    def read_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return None

        self.buffer.append(frame)
        return frame

    def get_buffer_frames(self):
        return list(self.buffer)

    def release(self):
        self.cap.release()
