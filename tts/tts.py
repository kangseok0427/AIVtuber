# tts/tts.py
import asyncio
import os
import re
import shutil
import pyaudio
import edge_tts
import soundfile as sf
import numpy as np
from gradio_client import Client
from dotenv import load_dotenv

load_dotenv()

VOICE      = os.getenv("TTS_VOICE", "ko-KR-SunHiNeural")
OUTPUT_DIR = "assets/output"
MODEL_NAME = os.getenv("TTS_MODEL_NAME", "Gaon_200e_2200s.pth")
INDEX_NAME = os.getenv("TTS_INDEX_NAME", "Gaon.index")
APPLIO_URL = os.getenv("APPLIO_URL", "http://127.0.0.1:6969")

os.makedirs(OUTPUT_DIR, exist_ok=True)

try:
    client = Client(APPLIO_URL)
    print("[TTS] Applio 연결 완료!")
except Exception:
    raise RuntimeError("Applio가 켜져있지 않아요! 먼저 Applio를 실행해주세요.")

def clean_text(text: str) -> str:
    text = re.sub(r'[^\uAC00-\uD7A3\u3131-\u318Ea-zA-Z0-9\s,.!?~]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def find_device(name: str) -> int | None:
    p = pyaudio.PyAudio()
    for i in range(p.get_device_count()):
        d = p.get_device_info_by_index(i)
        if name in d['name'] and d['maxOutputChannels'] > 0:
            p.terminate()
            return i
    p.terminate()
    return None

def play_audio(path: str):
    import sounddevice as sd
    device_index = find_device("VB-Cable")
    if device_index is None:
        print("[TTS] VB-Cable 디바이스 없음!")
        return

    data, samplerate = sf.read(path, dtype='float32')

    if data.ndim == 1:
        data = np.stack([data, data], axis=1)

    # 끝에 묵음 추가
    silence = np.zeros((int(samplerate * 0.8), 2), dtype=np.float32)
    data = np.concatenate([data, silence], axis=0)

    sd.play(data, samplerate, device=device_index)
    sd.wait()

async def text_to_speech(text: str) -> str:
    clean = clean_text(text)
    if not clean:
        return ""

    raw_path = f"{OUTPUT_DIR}/gaon_raw.wav"
    out_path = f"{OUTPUT_DIR}/gaon.wav"

    # 1. Edge TTS
    communicate = edge_tts.Communicate(clean, VOICE)
    await communicate.save(raw_path)

    # Applio 입출력 경로
    applio_input  = os.path.expanduser("~/Applio/assets/audios/gaon_raw.wav")
    applio_output = os.path.expanduser("~/Applio/assets/audios/gaon_out.wav")
    shutil.copy(os.path.abspath(raw_path), applio_input)

    # 2. Applio RVC 변환
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: client.predict(
            True,                            # terms_accepted
            0,                               # param_1:  pitch
            0.5,                             # param_2:  index_rate
            1.0,                             # param_3:  volume_envelope
            0.5,                             # param_4:  protect
            "fcpe",                          # param_5:  f0_method
            applio_input,                    # param_6:  input_path
            applio_output,                   # param_7:  output_path
            f"logs/models/{MODEL_NAME}",     # param_8:  pth_path
            f"logs/{INDEX_NAME}",            # param_9:  index_path
            False,                           # param_10: split_audio
            False,                           # param_11: f0_autotune
            1.0,                             # param_12: f0_autotune_strength
            False,                           # param_13: proposed_pitch
            155.0,                           # param_14: proposed_pitch_threshold
            False,                           # param_15: clean_audio
            0.5,                             # param_16: clean_strength
            "WAV",                           # param_17: export_format
            "contentvec",                    # param_18: embedder_model
            "",                              # param_19: embedder_model_custom
            False,                           # param_20: formant_shifting
            1.0,                             # param_21: formant_qfrency
            1.0,                             # param_22: formant_timbre
            False,                           # param_23: post_process
            False,                           # param_24: reverb
            False,                           # param_25: pitch_shift
            False,                           # param_26: limiter
            False,                           # param_27: gain
            False,                           # param_28: distortion
            False,                           # param_29: chorus
            False,                           # param_30: bitcrush
            False,                           # param_31: clipping
            False,                           # param_32: compressor
            False,                           # param_33: delay
            0.5,                             # param_34: reverb_room_size
            0.5,                             # param_35: reverb_damping
            0.33,                            # param_36: reverb_wet_gain
            0.4,                             # param_37: reverb_dry_gain
            1.0,                             # param_38: reverb_width
            0.0,                             # param_39: reverb_freeze_mode
            0.0,                             # param_40: pitch_shift_semitones
            -6.0,                            # param_41: limiter_threshold
            0.05,                            # param_42: limiter_release_time
            0.0,                             # param_43: gain_db
            25.0,                            # param_44: distortion_gain
            1.0,                             # param_45: chorus_rate
            0.25,                            # param_46: chorus_depth
            7.0,                             # param_47: chorus_center_delay
            0.0,                             # param_48: chorus_feedback
            0.5,                             # param_49: chorus_mix
            8.0,                             # param_50: bitcrush_bit_depth
            -6.0,                            # param_51: clipping_threshold
            0.0,                             # param_52: compressor_threshold
            1.0,                             # param_53: compressor_ratio
            1.0,                             # param_54: compressor_attack
            100.0,                           # param_55: compressor_release
            0.5,                             # param_56: delay_seconds
            0.0,                             # param_57: delay_feedback
            0.5,                             # param_58: delay_mix
            0,                               # param_59: sid
            api_name="/enforce_terms"
        ))

        if result and len(result) > 1 and result[1]:
            shutil.copy(result[1], out_path)
            play_audio(out_path)
        else:
            print("[TTS] 변환 실패, Edge TTS로 재생")
            play_audio(raw_path)

    except Exception:
        import traceback
        print(f"[TTS] Applio 오류:\n{traceback.format_exc()}")
        play_audio(raw_path)

    return out_path