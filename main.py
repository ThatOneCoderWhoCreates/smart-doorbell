from camera.live_buffer import LiveCameraBuffer
from camera.record_event import record_event
from utils.logger import log
import time
import threading

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
