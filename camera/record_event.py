import cv2
import os
from datetime import datetime


def record_event(pre_frames, cap, duration=10, fps=10):
    if not pre_frames:
        print("No pre-buffer frames available")
        return None

    project_root = os.getcwd()
    
    # Hierarchical storage: storage/local/YYYY/MM/DD
    now = datetime.now()
    date_path = os.path.join(str(now.year), f"{now.month:02d}", f"{now.day:02d}")
    save_dir = os.path.join(project_root, "storage", "local", date_path)
    os.makedirs(save_dir, exist_ok=True)

    filename = os.path.join(
        save_dir,
        f"event_{now.strftime('%H-%M-%S')}.mp4"
    )

    # Save raw frames temporarily, then convert to web-safe mp4 via ffmpeg
    import subprocess
    
    height, width, _ = pre_frames[0].shape
    
    # We will pipe the raw BGR frames directly to ffmpeg
    process = subprocess.Popen([
        'ffmpeg',
        '-y', # Overwrite if exists
        '-f', 'rawvideo',
        '-vcodec', 'rawvideo',
        '-s', f'{width}x{height}',
        '-pix_fmt', 'bgr24',
        '-r', str(fps),
        '-i', '-', # Read from stdin
        '-c:v', 'libx264',
        '-pix_fmt', 'yuv420p', # Web safe color space
        '-preset', 'ultrafast',
        '-movflags', '+faststart', # Essential for web/mobile streaming
        filename
    ], stdin=subprocess.PIPE, stderr=subprocess.DEVNULL)

    # Write pre-event frames
    for frame in pre_frames:
        process.stdin.write(frame.tobytes())

    # Write post-event frames (Slow Motion)
    frame_count = duration * fps
    for _ in range(frame_count):
        ret, frame = cap.read()
        if not ret:
            break
        process.stdin.write(frame.tobytes())
        process.stdin.write(frame.tobytes()) # Duplicate for slow mo

    # Close stdin to signal end of stream and wait for finish
    process.stdin.close()
    process.wait()

    return filename
