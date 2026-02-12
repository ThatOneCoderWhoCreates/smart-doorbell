import tkinter as tk
import threading
import main

class SmartDoorbellUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Doorbell System")
        self.root.geometry("420x320")

        self.system_thread = None
        self.status = tk.StringVar(value="Status: Idle")

        # Title
        tk.Label(
            root,
            text="SMART DOORBELL",
            font=("Arial", 16, "bold")
        ).pack(pady=10)

        # Status
        tk.Label(
            root,
            textvariable=self.status,
            font=("Arial", 12)
        ).pack(pady=10)

        # Start Button
        self.start_btn = tk.Button(
            root,
            text="Start Camera System",
            width=25,
            command=self.start_system
        )
        self.start_btn.pack(pady=5)

        # Trigger Button
        self.trigger_btn = tk.Button(
            root,
            text="Simulate Motion Event",
            width=25,
            command=self.trigger_event,
            state=tk.DISABLED
        )
        self.trigger_btn.pack(pady=5)

        # Stop Button
        self.stop_btn = tk.Button(
            root,
            text="Stop System",
            width=25,
            command=self.stop_system,
            state=tk.DISABLED
        )
        self.stop_btn.pack(pady=5)

        # Exit
        tk.Button(
            root,
            text="Exit",
            width=25,
            command=self.exit_app
        ).pack(pady=20)

    def start_system(self):
        self.status.set("Status: Running")
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.trigger_btn.config(state=tk.NORMAL)

        self.system_thread = threading.Thread(
            target=main.start_system,
            daemon=True
        )
        self.system_thread.start()

    def trigger_event(self):
        main.request_event()
        self.status.set("Status: Motion Event Triggered")

    def stop_system(self):
        main.stop_system()
        self.status.set("Status: Stopped")
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.trigger_btn.config(state=tk.DISABLED)

    def exit_app(self):
        main.stop_system()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartDoorbellUI(root)
    root.mainloop()
