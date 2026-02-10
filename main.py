from camera.live_buffer import LiveCameraBuffer
from camera.record_event import record_event
from utils.logger import log
import time
import threading

<<<<<<< HEAD
# =====================
# SHARED CONTROL FLAGS
# =====================
event_requested = False
system_running = False


def request_event():
    global event_requested
    event_requested = True


def start_system():
    global system_running, event_requested
    system_running = True
    event_requested = False

    log("Smart Doorbell System Started")
    print("Live camera feed running (continuous)")
    print("Maintaining 10–15s rolling buffer\n")

    camera = LiveCameraBuffer(buffer_seconds=15, fps=10)

    try:
        while system_running:
            # Always read frames
            camera.read_frame()
            time.sleep(0.05)

            if event_requested:
                event_requested = False
                log("Motion event detected")

                print("Saving pre-event + live video...")
                pre_frames = camera.get_buffer_frames()

                video = record_event(
                    pre_frames,
                    camera.cap,
                    duration=10,
                    fps=10
                )

                log(f"Event video saved: {video}")
                print(f"Saved video: {video}\n")

    except Exception as e:
        log(f"System error: {e}")

    finally:
        camera.release()
        log("System stopped safely")
        print("Camera released")


def stop_system():
    global system_running
    system_running = False


# CLI fallback (still works)
if __name__ == "__main__":
    start_system()
=======
# Shared trigger flag
event_requested = False

def wait_for_trigger():
    global event_requested
    while True:
        input(">> Press ENTER to simulate motion\n")
        event_requested = True

print("Smart Doorbell System Started")
print("Live camera feed running (continuous)")
print("Maintaining 10–15s rolling buffer\n")

# Start trigger listener in a separate thread
trigger_thread = threading.Thread(target=wait_for_trigger, daemon=True)
trigger_thread.start()

camera = LiveCameraBuffer(buffer_seconds=15, fps=10)

try:
    while True:
        # ALWAYS read frames (this is the key fix)
        camera.read_frame()
        time.sleep(0.05)  # control CPU usage

        if event_requested:
            event_requested = False
            log("Motion event detected")

            print("Saving pre-event + live video...")
            pre_frames = camera.get_buffer_frames()

            video = record_event(
                pre_frames,
                camera.cap,
                duration=10,
                fps=10
            )

            log(f"Event video saved: {video}")
            print(f"Saved video: {video}\n")

except KeyboardInterrupt:
    log("System shutdown by user")
    camera.release()
    print("\nSystem stopped safely")
>>>>>>> bae2011394891f3509e14bf25e50836c364789e0
