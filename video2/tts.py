#!/usr/bin/env python3
"""Озвучка сцен: edge-tts ru-RU-DmitryNeural, каждая сцена целиком (естественные паузы самого голоса).
Выход: voice/NN.wav (48 кГц моно) + voice/NN.json (слова с таймингами)."""
import asyncio, json, os, re, subprocess, sys
import numpy as np
import ssl
import edge_tts, edge_tts.communicate
edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
sys.path.insert(0, os.path.dirname(__file__))
from script import SCENES

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "video2", "voice"); os.makedirs(OUT, exist_ok=True)
SR = 48000
VOICE, RATE, PITCH = "ru-RU-DmitryNeural", "-8%", "-4Hz"

async def synth(text, path):
    for attempt in range(12):
        try:
            return await _synth(text, path)
        except Exception as e:
            print("retry", attempt, repr(text), e, flush=True); await asyncio.sleep(3 + attempt * 3)
    raise RuntimeError(text)

async def _synth(text, path):
    c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
    words = []
    with open(path, "wb") as f:
        async for ch in c.stream():
            if ch["type"] == "audio": f.write(ch["data"])
            elif ch["type"] == "WordBoundary":
                words.append({"w": ch["text"], "t0": ch["offset"] / 1e7, "t1": (ch["offset"] + ch["duration"]) / 1e7})
    return words

def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()

def pieces(text):
    # сцена читается целиком, без нарезки и вставных пауз; ведущее «…» убираем
    return [re.sub(r"^\s*(?:…|\.\.\.)\s*", "", text.strip())]


async def main():
    for n, sc in enumerate(SCENES, 1):
        if os.path.exists(os.path.join(OUT, f"{n:02d}.json")) and "--force" not in sys.argv: continue
        audio, words, t = [], [], 0.0
        for k, p in enumerate(pieces(sc["text"])):
            if k:
                audio.append(np.zeros(int(0.5 * SR), np.float32)); t += 0.5
            mp3 = os.path.join(OUT, f"{n:02d}_{k}.mp3")
            ws = await synth(p, mp3)
            a = decode(mp3)
            env = np.abs(a) > 0.01
            i0 = max(0, int(np.argmax(env)) - int(0.03 * SR))
            i1 = min(len(a), len(a) - int(np.argmax(env[::-1])) + int(0.06 * SR))
            a = a[i0:i1]; sh = i0 / SR
            for w in ws:
                words.append({"w": w["w"], "t0": round(t + max(0, w["t0"] - sh), 3), "t1": round(t + min(len(a) / SR, w["t1"] - sh), 3)})
            audio.append(a); t += len(a) / SR
            os.remove(mp3)
        a = np.concatenate(audio)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        os.path.join(OUT, f"{n:02d}.wav")], input=a.tobytes(), check=True)
        json.dump({"dur": round(len(a) / SR, 3), "words": words}, open(os.path.join(OUT, f"{n:02d}.json"), "w"), ensure_ascii=False, indent=1)
        print(n, round(len(a) / SR, 2), " ".join(w["w"] for w in words), flush=True)

asyncio.run(main())
