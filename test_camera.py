<<<<<<< HEAD
from camera.capture import capture_image

print("Testing camera...")
img = capture_image()

if img:
    print("SUCCESS:", img)
else:
    print("FAILED")
=======
import cv2

for i in range(5):
    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
    print(f"Index {i}: {cap.isOpened()}")
    cap.release()
>>>>>>> bae2011394891f3509e14bf25e50836c364789e0
