import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import cv2
import asyncio
from aiortc import RTCPeerConnection, RTCSessionDescription
from main import DoorbellSystem
from web.audio import MicrophoneTrack

app = FastAPI()

# Mount static files
app.mount("/static", StaticFiles(directory="web/static"), name="static")

# Mount storage directory to serve videos
os.makedirs("storage/local", exist_ok=True)
app.mount("/storage", StaticFiles(directory="storage/local"), name="storage")

# Templates
templates = Jinja2Templates(directory="web/templates")

# Ngrok Bypass Middleware
@app.middleware("http")
async def add_ngrok_bypass_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["ngrok-skip-browser-warning"] = "true"
    return response

# Doorbell system instance
system = DoorbellSystem(show_window=False)

# Store push subscriptions
subscriptions = []

# Store active peer connections
pcs = set()


# -------------------------
# Startup / Shutdown Events
# -------------------------

@app.on_event("startup")
async def startup_event():
    print("Starting Doorbell System...")
    system.start()


@app.on_event("shutdown")
async def shutdown_event():
    print("Stopping Doorbell System...")
    system.stop()
    for pc in pcs:
        await pc.close()
    pcs.clear()


# -------------------------
# UI ROUTE
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# -------------------------
# SYSTEM CONTROL ROUTES
# -------------------------

@app.get("/start")
async def start():
    system.start()
    return JSONResponse({"status": "started"})


@app.get("/api/status")
async def get_status():
    return JSONResponse({"status": "started" if system.running else "stopped"})


@app.get("/stop")
async def stop():
    system.stop()
    return JSONResponse({"status": "stopped"})


@app.get("/trigger")
async def trigger():
    system.request_event()
    return JSONResponse({"status": "triggered"})


@app.post("/api/unlock")
async def unlock_door():
    system.unlock()
    return JSONResponse({"status": "door_unlocked"})

@app.post("/api/lock")
async def lock():
    system.lock()
    return JSONResponse({"status": "door_locked"})


@app.post("/api/pir-trigger")
async def trigger_pir():
    system.mock_motion()
    return JSONResponse({"status": "motion_simulated"})


@app.post("/api/subscribe")
async def subscribe(request: Request):
    sub = await request.json()
    if sub not in subscriptions:
        subscriptions.append(sub)
    print(f"Registered new Push Subscription. Total: {len(subscriptions)}")
    return JSONResponse({"status": "subscribed"})


@app.get("/api/recordings")
async def get_recordings():
    try:
        files = os.listdir("storage/local")
        videos = [f for f in files if f.endswith(".avi")]
        videos.sort(reverse=True) # newest first
        return JSONResponse({"recordings": videos})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -------------------------
# PUSH NOTIFICATION SENDER
# -------------------------

from pywebpush import webpush, WebPushException
import json

def send_push_notification(message_text: str):
    print(f"Sending Push Notification to {len(subscriptions)} devices: {message_text}")
    for sub in subscriptions.copy():
        try:
            webpush(
                subscription_info=sub,
                data=message_text,
                vapid_private_key="private_key.pem",
                vapid_claims={
                    "sub": "mailto:admin@smartdoorbell.local"
                }
            )
        except WebPushException as ex:
            print("WebPush Error:", repr(ex))
            if ex.response and ex.response.status_code in [404, 410]:
                print(f"Removing inactive subscription")
                subscriptions.remove(sub)
        except Exception as e:
            print("Failed to send push:", str(e))

system.set_push_callback(send_push_notification)


# -------------------------
# MJPEG VIDEO STREAM
# -------------------------

async def generate_frames():
    def get_idle_frame():
        import numpy as np
        # Create a black image
        img = np.zeros((480, 640, 3), dtype=np.uint8)
        img[:] = (30, 30, 30)
        cv2.putText(img, "SYSTEM IDLE - WAITING FOR MOTION", (50, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        _, buffer = cv2.imencode(".jpg", img)
        return buffer.tobytes()

    idle_bytes = get_idle_frame()

    while True:
        frame = system.get_frame()
        if frame is not None:
            _, buffer = cv2.imencode(".jpg", frame)
            frame_bytes = buffer.tobytes()
        else:
            frame_bytes = idle_bytes

        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame_bytes
            + b"\r\n"
        )
        await asyncio.sleep(0.1 if frame is None else 0.03)


@app.get("/video_feed")
async def video_feed():
    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# -------------------------
# WEBSOCKET AUDIO CHANNEL
# -------------------------
from fastapi import WebSocket, WebSocketDisconnect
from utils.audio import AudioHandler

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    audio = AudioHandler(rate=16000, chunk=1024)
    audio.start_input_stream()
    audio.start_output_stream()
    
    # Task to read from WebSocket (phone mic) and play on PC speaker
    async def receive_from_phone():
        try:
            while True:
                data = await websocket.receive_bytes()
                await asyncio.to_thread(audio.write_audio, data)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Error receiving audio from phone: {e}")

    # Task to read from PC mic and send to WebSocket (phone speaker)
    async def send_to_phone():
        try:
            while True:
                data = await asyncio.to_thread(audio.read_audio)
                if data:
                    await websocket.send_bytes(data)
                else:
                    await asyncio.sleep(0.01)
        except WebSocketDisconnect:
            pass
        except Exception as e:
            print(f"Error sending audio to phone: {e}")

    try:
        # Run both tasks concurrently
        await asyncio.gather(
            receive_from_phone(),
            send_to_phone()
        )
    except WebSocketDisconnect:
        print("Audio WebSocket disconnected.")
    finally:
        audio.close()