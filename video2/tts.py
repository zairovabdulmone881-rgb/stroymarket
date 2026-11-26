#!/usr/bin/env python3
"""Озвучка сцен: edge-tts ru-RU-DmitryNeural, «доработанный» — чтобы звучал живее:
  1) каждое предложение синтезируется отдельно со своей скоростью/высотой (режиссура интонации),
     плюс небольшой случайный разброс, чтобы не было монотонности;
  2) паузы только между предложениями, разной длины (без разрезов внутри фраз);
  3) обработка: тёплый низ, убран «металл» ~3 кГц и шипение, мягкая компрессия, лёгкая комната.
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
VOICE = "ru-RU-DmitryNeural"
BASE_RATE, BASE_PITCH = -3, -2          # базовый тон рассказчика: чуть спокойнее и ниже стандартного
rng = np.random.default_rng(24)

# режиссура: (номер сцены, начало фразы) → (сдвиг скорости %, сдвиг высоты Гц, пауза ПЕРЕД фразой, с)
DIRECT = {
    (1, "Три часа"): (-10, -4, 0), (1, "«У вас"): (-6, -3, 0.2),
    (2, "Из-за"): (-6, -3, 0.35), (2, "Ты узнаешь"): (-8, -4, 0.4),
    (3, "Утро"): (-12, -3, 0), (3, "А воды"): (-6, -3, 0.3),
    (4, "«Это моё"): (8, 8, 0.12),
    (5, "Банкоматы"): (-6, -2, 0), (5, "Твои деньги"): (0, 0, 0.35),
    (6, "Ты тоже"): (-8, -2, 0.3),
    (7, "Она стоит"): (-4, -3, 0.3),
    (8, "Заколачиваешь"): (4, 0, 0.25), (8, "Двенадцать"): (-10, -5, 0.4),
    (9, "Сосед"): (-6, -2, 0.35), (9, "С дочкой"): (-10, -3, 0.25), (9, "«Пусти"): (-4, 6, 0.4),
    (10, "Ты открываешь"): (-14, -5, 0.45),
    (11, "Радио"): (2, 0, 0.35),
    (12, "Вот она"): (-10, -5, 0), (12, "Бежать"): (-4, -2, 0.4),
    (13, "Ты выдыхаешь"): (-10, -1, 0), (13, "Ещё шесть"): (-2, 1, 0.45),
    (14, "И тут"): (-6, -2, 0), (14, "На время"): (-10, -4, 0.3),
    (15, "Его"): (-16, -7, 0),
    (16, "Двадцать"): (-6, -4, 0.4), (16, "давно"): (-22, -9, 0.75),
    (17, "А ты бы"): (-4, 2, 0), (17, "Пиши"): (2, 0, 0.35),
}

async def synth(text, path, rate="+0%", pitch="+0Hz"):
    for attempt in range(12):
        try:
            return await _synth(text, path, rate, pitch)
        except Exception as e:
            print("retry", attempt, repr(text), e, flush=True); await asyncio.sleep(3 + attempt * 3)
    raise RuntimeError(text)

async def _synth(text, path, rate="+0%", pitch="+0Hz"):
    c = edge_tts.Communicate(text, VOICE, rate=rate, pitch=pitch, boundary="WordBoundary")
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

def pieces(n, text):
    """фразы: режем после . ! ? … и перед цитатой «…»; к каждой — скорость, высота, пауза перед ней"""
    text = re.sub(r"^\s*(?:…|\.\.\.)\s*", "", text.strip())
    parts = [p for p in re.split(r"(?<=[.!?…»])\s+|(?<=:)\s+(?=«)", text) if p.strip()]
    # «истекли… давно» — отдельная драматичная пауза
    out = []
    for p in parts:
        out += [q for q in re.split(r"(?<=…)\s+", p) if q.strip()]
    res = []
    for k, p in enumerate(out):
        dr, dp, pause = 0, 0, (0.28 if k else 0.0)
        if len(p.split()) <= 2 and k: pause = 0.22
        for (sn, start), v in DIRECT.items():
            if sn == n and p.startswith(start):
                dr, dp, pause = v; break
        if p.startswith("«"): dp = max(dp, 4)
        if p.endswith("?"): dp += 2
        r = BASE_RATE + dr + int(rng.integers(-2, 3))
        h = BASE_PITCH + dp + int(rng.integers(-1, 2))
        res.append((p, f"{r:+d}%", f"{h:+d}Hz", pause))
    return res


VOICE_FX = ("highpass=f=75,equalizer=f=170:t=q:w=0.9:g=2.5,equalizer=f=3100:t=q:w=1.2:g=-3,"
            "equalizer=f=6500:t=q:w=1.5:g=-1.5,highshelf=f=10000:g=-3,"
            "acompressor=threshold=-20dB:ratio=2.2:attack=8:release=150:makeup=1.5")


def room(a, mix=0.07):
    """очень лёгкая комната: снимает «сухость» синтеза, не размазывая слова"""
    n = int(0.28 * SR); t = np.arange(n) / SR
    ir = np.random.default_rng(3).standard_normal(n) * np.exp(-t / 0.06)
    ir[: int(0.012 * SR)] = 0                                         # ранние отражения чуть позже прямого звука
    w = np.convolve(a, ir)[: len(a)]
    w *= np.abs(a).max() / (np.abs(w).max() + 1e-9)
    return (a + w * mix).astype(np.float32)


async def main():
    for n, sc in enumerate(SCENES, 1):
        if os.path.exists(os.path.join(OUT, f"{n:02d}.json")) and "--force" not in sys.argv: continue
        audio, words, t = [], [], 0.0
        for k, (p, rate, pitch, pause) in enumerate(pieces(n, sc["text"])):
            if pause:
                audio.append(np.zeros(int(pause * SR), np.float32)); t += pause
            mp3 = os.path.join(OUT, f"{n:02d}_{k}.mp3")
            ws = await synth(p, mp3, rate, pitch)
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
