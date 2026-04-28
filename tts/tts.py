# tts/tts.py
import asyncio
import os
import re
import subprocess
import sounddevice as sd
import soundfile as sf
import edge_tts

VOICE      = "ko-KR-SunHiNeural"
OUTPUT_DIR = "assets/output"
VBCABLE_DEVICE = 2  # VB-Cable

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text: str) -> str:
    text = re.sub(r'[^\uAC00-\uD7A3\u3131-\u318Ea-zA-Z0-9\s,.!?~]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

async def text_to_speech(text: str) -> str:
    clean = clean_text(text)
    if not clean:
        return ""
    
    out_path = f"{OUTPUT_DIR}/gaon.wav"
    communicate = edge_tts.Communicate(clean, VOICE)
    await communicate.save(out_path)
    
    # VB-Cable로 출력
    data, samplerate = sf.read(out_path)
    sd.play(data, samplerate, device=VBCABLE_DEVICE)
    sd.wait()
    
    return out_path