#!/usr/bin/env python3
"""Озвучка сцен: edge-tts ru-RU-DmitryNeural, rate -8%, pitch -4Hz — каждая сцена отдельным синтезом.
Внутри сцены текст режется ТОЛЬКО на «…» и «—»: там вставляется пауза 0.5 с.
Обработка голоса как в video2 (тёплый низ, минус «металл», мягкая компрессия, лёгкая комната).
Выход: voice/NN.wav (48 кГц моно) + voice/NN.json (слова с таймингами)."""
import asyncio, json, os, re, ssl, subprocess, sys
import numpy as np
import edge_tts, edge_tts.communicate
if os.path.exists('/root/.ccr/ca-bundle.crt'):
    edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile='/root/.ccr/ca-bundle.crt')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import SCENES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "voice"); os.makedirs(OUT, exist_ok=True)
SR, VOICE, RATE, PITCH, DASH_PAUSE = 48000, "ru-RU-DmitryNeural", "-8%", "-4Hz", 0.5


async def synth(text, path):
    for attempt in range(12):
        try:
            c = edge_tts.Communicate(text, VOICE, rate=RATE, pitch=PITCH, boundary="WordBoundary")
            words = []
            with open(path, "wb") as f:
                async for ch in c.stream():
                    if ch["type"] == "audio": f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        words.append({"w": ch["text"], "t0": ch["offset"] / 1e7, "t1": (ch["offset"] + ch["duration"]) / 1e7})
            return words
        except Exception as e:
            print("retry", attempt, repr(text), e, flush=True); await asyncio.sleep(3 + attempt * 3)
    raise RuntimeError(text)


def decode(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.float32).copy()


def pieces(text):
    """режем только по «…» и «—» (пауза 0.5 с); знак остаётся у предыдущего куска"""
    parts = re.split(r"(?<=…)\s+|\s+—\s+", text.strip())
    return [p.strip() for p in parts if p.strip()]


VOICE_FX = ("highpass=f=75,equalizer=f=170:t=q:w=0.9:g=2.5,equalizer=f=3100:t=q:w=1.2:g=-3,"
            "equalizer=f=6500:t=q:w=1.5:g=-1.5,highshelf=f=10000:g=-3,"
            "acompressor=threshold=-20dB:ratio=2.2:attack=8:release=150:makeup=1.5")


def room(a, mix=0.07):
    n = int(0.28 * SR); t = np.arange(n) / SR
    ir = np.random.default_rng(3).standard_normal(n) * np.exp(-t / 0.06)
    ir[: int(0.012 * SR)] = 0
    w = np.convolve(a, ir)[: len(a)]
    w *= np.abs(a).max() / (np.abs(w).max() + 1e-9)
    return (a + w * mix).astype(np.float32)


async def main():
    for n, sc in enumerate(SCENES, 1):
        if os.path.exists(os.path.join(OUT, f"{n:02d}.json")) and "--force" not in sys.argv: continue
        audio, words, t = [], [], 0.0
        for k, p in enumerate(pieces(sc["text"])):
            if k:
                audio.append(np.zeros(int(DASH_PAUSE * SR), np.float32)); t += DASH_PAUSE
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
        a = room(np.concatenate(audio))
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-",
                        "-af", VOICE_FX, os.path.join(OUT, f"{n:02d}.wav")], input=a.tobytes(), check=True)
        json.dump({"dur": round(len(a) / SR, 3), "words": words}, open(os.path.join(OUT, f"{n:02d}.json"), "w"), ensure_ascii=False, indent=1)
        print(n, round(len(a) / SR, 2), " ".join(w["w"] for w in words), flush=True)

asyncio.run(main())
