from fastapi import FastAPI, UploadFile, File, Form
import shutil
import os
import time
from gradio_client import Client, handle_file

app = FastAPI(title="Faceless VTuber API", version="1.0")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    rvc_client = Client("ardha27/rvc-models")
except Exception as e:
    rvc_client = None
    print("Warning: Could not connect to RVC Public API.", e)

from app.services.audio_cleaning import clean_voice

@app.post("/process-audio/")
async def process_audio(character: str = Form("itachi"), audio: UploadFile = File(...)):
    input_path = os.path.join(UPLOAD_DIR, f"input_{int(time.time())}_{audio.filename}")
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(audio.file, buffer)
    
    # Render Free Tier 0.1 vCPU is too slow for noisereduce (takes > 100s timeout)
    # So we just return the raw user voice directly for instant processing!
    output_path = os.path.join(OUTPUT_DIR, f"output_{int(time.time())}.wav")
    print(f"Received character request: '{character}'")
    shutil.copy(input_path, output_path)
    
    # Return absolute path so Unity can load it easily
    abs_output_path = os.path.abspath(output_path)
    
    # 4. Return the response directly as a file
    from fastapi.responses import FileResponse
    return FileResponse(abs_output_path, media_type="audio/wav")

from fastapi.responses import FileResponse
import zipfile
import subprocess
import imageio_ffmpeg

@app.post("/render-video/")
async def render_video(zip_file: UploadFile = File(...)):
    print("Received ZIP for video rendering...")
    render_id = int(time.time())
    render_dir = os.path.join(OUTPUT_DIR, f"render_{render_id}")
    os.makedirs(render_dir, exist_ok=True)
    
    zip_path = os.path.join(render_dir, "upload.zip")
    with open(zip_path, "wb") as buffer:
        shutil.copyfileobj(zip_file.file, buffer)
        
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(render_dir)
        
    print(f"Extracted frames to {render_dir}")
    output_mp4 = os.path.join(render_dir, "final_video.mp4")
    ffmpeg_exe = imageio_ffmpeg.get_ffmpeg_exe()
    
    ffmpeg_cmd = [
        ffmpeg_exe, "-y",
        "-framerate", "30",
        "-i", os.path.join(render_dir, "frame_%04d.jpg"),
        "-i", os.path.join(render_dir, "audio.wav"),
        "-c:v", "libx264",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-shortest",
        output_mp4
    ]
    
    try:
        subprocess.run(ffmpeg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return FileResponse(output_mp4, media_type="video/mp4", filename="vtuber_export.mp4")
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": e.stderr.decode()}
