import threading
import time
import yaml

from camera.live_buffer import LiveCameraBuffer
from camera.record_event import record_event
from utils.logger import log

# Load configuration
with open("config.yaml") as f:
    config = yaml.safe_load(f)

buffer_seconds = config["camera"]["buffer_seconds"]
fps = config["camera"]["fps"]
event_duration = config["camera"]["event_duration"]

# Global objects
live_buffer = None
system_running = False


def start_system():
    global live_buffer, system_running

    if system_running:
        return

    print("Starting Smart Doorbell system...")
    log("System started")

    live_buffer = LiveCameraBuffer(buffer_seconds=buffer_seconds, fps=fps)
    system_running = True

    # Start background thread
    threading.Thread(target=run_camera_loop, daemon=True).start()


def run_camera_loop():
    global system_running

    print("Live camera feed running (continuous)")
    print(f"Maintaining {buffer_seconds}s rolling buffer")

    while system_running:
        ret, frame = live_buffer.read_frame()
        if not ret:
            print("Camera frame read failed")
            break
        time.sleep(1 / fps)


def trigger_motion():
    global live_buffer

    if not live_buffer:
        print("System not started")
        return

    print("Motion event detected")
    print("Saving pre-event + live video...")
    log("Motion detected")

    filename = record_event(
        live_buffer.get_buffer_frames(),
        live_buffer.cap,
        duration=event_duration,
        fps=fps
    )

    print(f"Saved video: {filename}")
    log(f"Event saved: {filename}")


def stop_system():
    global system_running, live_buffer

    system_running = False

    if live_buffer:
        live_buffer.release()

    print("System stopped")
    log("System stopped")
