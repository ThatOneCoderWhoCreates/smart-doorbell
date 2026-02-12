import tkinter as tk
import threading
import main


class SmartDoorbellUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Smart Doorbell System")
        self.root.geometry("400x300")

        # Title
        tk.Label(
            root,
            text="SMART DOORBELL",
            font=("Arial", 16, "bold")
        ).pack(pady=15)

        # Status label
        self.status = tk.StringVar(value="Status: Idle")
        tk.Label(
            root,
            textvariable=self.status,
            font=("Arial", 12)
        ).pack(pady=10)

        # Start button
        tk.Button(
            root,
            text="Start System",
            width=20,
            command=self.start_system,
            bg="green",
            fg="white"
        ).pack(pady=5)

        # Simulate motion button
        tk.Button(
            root,
            text="Simulate Motion",
            width=20,
            command=self.trigger_motion,
            bg="red",
            fg="white"
        ).pack(pady=5)

        # Stop button
        tk.Button(
            root,
            text="Stop System",
            width=20,
            command=self.stop_system,
            bg="gray",
            fg="white"
        ).pack(pady=5)

    def start_system(self):
        self.status.set("Status: Running")
        threading.Thread(target=main.start_system, daemon=True).start()

    def trigger_motion(self):
        self.status.set("Status: Recording Event")
        threading.Thread(target=main.trigger_motion, daemon=True).start()

    def stop_system(self):
        self.status.set("Status: Stopped")
        main.stop_system()


if __name__ == "__main__":
    root = tk.Tk()
    app = SmartDoorbellUI(root)
    root.mainloop()
