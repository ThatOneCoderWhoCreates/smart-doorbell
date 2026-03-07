from camera.live_buffer import LiveCameraBuffer
from camera.record_event import record_event
from ai.human_detector import HumanDetector
from utils.logger import log
from utils.hardware import HardwareInterface
import cv2
import time
import threading


class DoorbellSystem:
    def __init__(self, show_window=False):
        self.event_requested = False
        self.running = False
        self.show_window = show_window
        self.idle = True  # Starts idle, waits for motion
        
        self.push_callback = None
        self.push_sent_for_event = False

        self.hardware = HardwareInterface()
        self.hardware.set_pir_callback(self._on_motion)

        self.camera = None
        self.detector = None
        self.current_frame = None

    def set_push_callback(self, callback):
        self.push_callback = callback

    def request_event(self):
        self.event_requested = True

    def unlock(self):
        log("API Command Received: UNLOCK DOOR")
        self.hardware.unlock_door()

    def lock(self):
        log("API Command Received: LOCK DOOR")
        self.hardware.lock_door()

    def mock_motion(self):
        """API hook to simulate motion"""
        self.hardware.mock_pir_trigger()

    def _on_motion(self):
        if self.idle:
            log("System Waking up from Motion...")
            self.idle = False
            self.push_sent_for_event = False

    def start(self):
        if self.running:
            return

        self.running = True
        self.camera = LiveCameraBuffer(buffer_seconds=15, fps=10)
        self.detector = HumanDetector()

        threading.Thread(target=self._run, daemon=True).start()
        log("System started (Idle mode). Waiting for motion.")

    def stop(self):
        self.running = False
        self.idle = True
        if self.camera:
            self.camera.release()
            self.camera = None
        if self.show_window:
            cv2.destroyAllWindows()
        self.hardware.cleanup()
        self.current_frame = None
        log("System stopped")

    def _run(self):
        last_active_time = time.time()
        try:
            while self.running:
                frame = self.camera.read_frame()
                if frame is None:
                    continue

                if self.idle:
                    self.current_frame = frame
                    time.sleep(0.03)
                    continue

                annotated, label, suspicious = self.detector.analyze_frame(frame)
                self.current_frame = annotated
                
                # If we see anything, stay awake. Otherwise, go back to sleep after 30s.
                if label:
                    last_active_time = time.time()
                    if suspicious and not self.push_sent_for_event and self.push_callback:
                        self.push_callback(f"ALERT: {label} Detected!")
                        self.push_sent_for_event = True
                elif time.time() - last_active_time > 30:
                    log("No activity for 30s. Returning to Idle state.")
                    self.idle = True
                    # Don't set current_frame to None so live feed persists

                if label:
                    color = (0, 0, 255) if label.startswith("SUSPICIOUS") else (0, 255, 0)
                    cv2.putText(
                        annotated,
                        label,
                        (50, 50),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        color,
                        3
                    )

                # Recording is now strictly Manual / Motion Triggered.
                # AI threats only send push notifications / alerts, they DO NOT auto-record anymore.

                if self.event_requested:
                    self.event_requested = False
                    pre_frames = self.camera.get_buffer_frames()
                    video = record_event(
                        pre_frames,
                        self.camera.cap,
                        duration=10,
                        fps=10
                    )
                    log(f"Saved video: {video}")

                time.sleep(0.03)

        except Exception as e:
            log(f"System error: {e}")

    def get_frame(self):
        return self.current_frame
