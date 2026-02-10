from camera.capture import capture_image

print("Testing camera...")
img = capture_image()

if img:
    print("SUCCESS:", img)
else:
    print("FAILED")
