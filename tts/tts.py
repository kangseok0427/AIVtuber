# tts/tts.py
import asyncio
import os
import re
import subprocess
import edge_tts

VOICE      = "ko-KR-SunHiNeural"
OUTPUT_DIR = "assets/output"

os.makedirs(OUTPUT_DIR, exist_ok=True)

def clean_text(text: str) -> str:
    # 한글, 영문, 숫자, 기본 문장부호만 남기고 전부 제거
    text = re.sub(r'[^\uAC00-\uD7A3\u3131-\u318Ea-zA-Z0-9\s,.!?~]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

_current_player = None

async def text_to_speech(text: str) -> str:
    global _current_player
    clean = clean_text(text)
    if not clean:
        return ""
    out_path = f"{OUTPUT_DIR}/gaon.wav"
    communicate = edge_tts.Communicate(clean, VOICE)
    await communicate.save(out_path)
    
    # 이전 재생 중이면 종료
    if _current_player and _current_player.poll() is None:
        _current_player.terminate()
    
    _current_player = subprocess.Popen(["afplay", out_path])
    return out_path