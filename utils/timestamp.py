import cv2
from datetime import datetime

def add_timestamp(frame):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cv2.putText(
        frame,
        timestamp,
        (10, frame.shape[0] - 10),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.6,
        (0, 255, 0),   # Green text
        2,
        cv2.LINE_AA
    )

#<<<<<<< HEAD
    return frame
#=======
    return frame
#>>>>>>> bae2011394891f3509e14bf25e50836c364789e0
