import tkinter as tk
import threading
from PIL import Image, ImageTk
import cv2
from main import start_system, stop_system, get_latest_frame


class SmartDoorbellUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Doorbell System")
        self.root.geometry("500x500")

        self.system_thread = None
        self.status = tk.StringVar(value="Status: Idle")

        tk.Label(root, text="SMART DOORBELL",
                 font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(root, textvariable=self.status,
                 font=("Arial", 12)).pack(pady=5)

        self.video_label = tk.Label(root)
        self.video_label.pack()

        self.start_btn = tk.Button(
            root,
            text="Start Camera System",
            width=25,
            command=self.start_system
        )
        self.start_btn.pack(pady=5)

        self.stop_btn = tk.Button(
            root,
            text="Stop System",
            width=25,
            command=self.stop_system,
            state=tk.DISABLED
        )
        self.stop_btn.pack(pady=5)

        tk.Button(
            root,
            text="Exit",
            width=25,
            command=self.exit_app
        ).pack(pady=20)

        self.update_video()

    def start_system(self):
        self.status.set("Status: Running (AI Detection Active)")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)

        self.system_thread = threading.Thread(
            target=start_system,
            daemon=True
        )
        self.system_thread.start()

    def stop_system(self):
        stop_system()
        self.status.set("Status: Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)

    def exit_app(self):
        stop_system()
        self.root.destroy()

    def update_video(self):
        frame = get_latest_frame()

        if frame is not None:
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((450, 300))
            imgtk = ImageTk.PhotoImage(image=img)

            self.video_label.imgtk = imgtk
            self.video_label.configure(image=imgtk)

        self.root.after(30, self.update_video)


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartDoorbellUI(root)
    root.mainloop()
