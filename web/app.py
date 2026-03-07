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

import aiofiles

# We will handle /storage/ manually to support iOS Range Requests, so comment out the StaticFiles mount
# app.mount("/storage", StaticFiles(directory="storage/local"), name="storage")

@app.get("/storage/{video_path:path}")
async def stream_video(video_path: str, request: Request):
    file_path = os.path.join("storage/local", video_path)
    if not os.path.exists(file_path):
        return HTMLResponse(status_code=404)

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("Range", 0)

    if range_header:
        byte1, byte2 = range_header.replace("bytes=", "").split("-")
        start = int(byte1)
        end = int(byte2) if byte2 else file_size - 1
    else:
        start = 0
        end = file_size - 1

    chunk_size = (end - start) + 1

    async def file_iterator(file_path, start, chunk_size):
        async with aiofiles.open(file_path, "rb") as video:
            await video.seek(start)
            chunk = await video.read(chunk_size)
            yield chunk

    headers = {
        "Content-Range": f"bytes {start}-{end}/{file_size}",
        "Accept-Ranges": "bytes",
        "Content-Length": str(chunk_size),
        "Content-Type": "video/mp4",
    }
    
    return StreamingResponse(
        file_iterator(file_path, start, chunk_size),
        headers=headers,
        status_code=206 if range_header else 200
    )

# -------------------------
# PUSH NOTIFICATION SENDER

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
    print("Starting Doorbell System... (Waiting for manual start)")


is_shutting_down = False

@app.on_event("shutdown")
async def shutdown_event():
    global is_shutting_down
    is_shutting_down = True
    print("Stopping Doorbell System...")
    system.stop()
    for pc in pcs:
        await pc.close()
    pcs.clear()
    
    # Force close any lingering WebSockets so Uvicorn can terminate instantly
    for ws in list(active_audio_sockets):
        try:
            await ws.close()
        except:
            pass


# -------------------------
# UI ROUTE
# -------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/recordings_page", response_class=HTMLResponse)
async def recordings_page(request: Request):
    return templates.TemplateResponse("recordings.html", {"request": request})


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
    global current_alert
    current_alert = {"id": 0, "message": None}
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
    system.request_event() # Force a recording event
    return JSONResponse({"status": "motion_simulated_and_recording_started"})


@app.post("/api/subscribe")
async def subscribe(request: Request):
    sub = await request.json()
    if sub not in subscriptions:
        subscriptions.append(sub)
    print(f"Registered new Push Subscription. Total: {len(subscriptions)}")
    return JSONResponse({"status": "subscribed"})


@app.get("/api/recordings")
async def get_recordings(sort: str = "newest", filter_date: str = None):
    try:
        base_dir = "storage/local"
        videos = []
        
        for root, _, files in os.walk(base_dir):
            for file in files:
                if file.endswith((".mp4", ".webm", ".avi")):
                    filepath = os.path.join(root, file)
                    
                    # Ignore corrupted or empty video files
                    if os.path.getsize(filepath) == 0:
                        continue
                        
                    rel_path = os.path.relpath(filepath, base_dir).replace("\\", "/")
                    
                    if filter_date:
                        date_parts = filter_date.split("-")
                        if len(date_parts) == 3:
                            y, m, d = date_parts
                            if f"{y}/{m}/{d}" not in rel_path:
                                continue
                                
                    videos.append({
                        "path": rel_path,
                        "time": os.path.getmtime(filepath)
                    })
                    
        # Sort based on timestamp to fix "Oldest/Newest" bug
        if sort == "oldest":
            videos.sort(key=lambda x: x["time"], reverse=False)
        else: # newest
            videos.sort(key=lambda x: x["time"], reverse=True)
            
        return JSONResponse({"recordings": [v["path"] for v in videos]})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.delete("/api/recordings/{video_path:path}")
async def delete_recording(video_path: str):
    try:
        # Prevent directory traversal
        if ".." in video_path:
            return JSONResponse({"error": "Invalid path"}, status_code=400)
            
        file_path = os.path.join("storage/local", video_path)
        if os.path.exists(file_path):
            os.remove(file_path)
            return JSONResponse({"status": "deleted"})
        else:
            return JSONResponse({"error": "File not found"}, status_code=404)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


# -------------------------
# PUSH NOTIFICATION SENDER
# -------------------------

from pywebpush import webpush, WebPushException
import json
import time

current_alert = {"id": 0, "message": None}

@app.get("/api/latest_alert")
async def get_latest_alert():
    return JSONResponse(current_alert)

def send_push_notification(message_text: str):
    global current_alert
    current_alert["id"] = time.time()
    current_alert["message"] = message_text
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

    while not is_shutting_down:
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

active_audio_sockets = set()

@app.websocket("/ws/audio")
async def websocket_audio_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_audio_sockets.add(websocket)
    try:
        while True:
            # Receive audio packet from one connected client
            data = await websocket.receive_bytes()
            
            # Broadcast the packet to all OUTBOUND clients (e.g., Phone -> PC, PC -> Phone)
            for client in list(active_audio_sockets):
                if client != websocket:
                    try:
                        await client.send_bytes(data)
                    except Exception as e:
                        active_audio_sockets.discard(client)
    except WebSocketDisconnect:
        active_audio_sockets.discard(websocket)
    finally:
        pass