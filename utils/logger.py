from datetime import datetime
import os

def log(message):
    os.makedirs("logs", exist_ok=True)

    with open("logs/system.log", "a") as f:
        f.write(f"{datetime.now()} - {message}\n")
