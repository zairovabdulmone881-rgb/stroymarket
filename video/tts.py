#!/usr/bin/env python3
"""Озвучка сцен голосом ru-RU-DmitryNeural (edge-tts) -> voice/NN.wav (48 кГц, обработанный).

Каждая фраза собирается из фрагментов со своим темпом/высотой и паузами — живая
драматичная подача вместо ровного чтения. База: rate -8%, pitch -4Hz.
Затем голосовая обработка: EQ, эксайтер, компрессия, де-эссер, выравнивание громкости.
edge-tts жёстко берёт CA из certifi; в песочнице HTTPS идёт через прокси,
поэтому указываем ему CA-бандл прокси (если он есть)."""
import asyncio, os, ssl, subprocess, sys
import numpy as np
from scipy.io import wavfile
import edge_tts, edge_tts.communicate as comm

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SR = 48000
CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    comm._SSL_CTX = ssl.create_default_context(cafile=CA)

# (текст, rate %, pitch Hz, пауза после, сек)
SCRIPT = [
    [("Ты едешь в лифте домой.", -8, -4, 0.30), ("Девятый этаж…", -16, -7, 0)],
    [("…и тут кабина резко встаёт!", 0, -2, 0.40), ("Свет гаснет.", -14, -6, 0.35), ("Кнопка диспетчера молчит.", -14, -8, 0)],
    [("А потом ты слышишь это…", -16, -8, 0.50), ("Скрежет.", -20, -10, 0.35), ("Сверху.", -8, -5, 0.22),
     ("Снизу.", -8, -5, 0.22), ("Отовсюду.", -18, -9, 0)],
    [("Кто-то пытается раскрыть двери!", 2, -2, 0)],
    [("Ты лезешь в люк на крыше кабины.", 0, -4, 0)],
    [("Шахта.", -18, -9, 0.35), ("Темнота.", -18, -9, 0.40), ("Только трос и твой фонарик.", -10, -6, 0)],
    [("Десятый этаж.", -8, -4, 0.45), ("На лестнице — они.", -18, -10, 0)],
    [("Ты забегаешь в первую открытую квартиру", 4, -2, 0.12), ("и закрываешь дверь шкафом.", 0, -4, 0)],
    [("В окне — весь город.", -10, -4, 0.40), ("Он горит.", -18, -9, 0)],
    [("Воды — три бутылки.", -10, -4, 0.30), ("Еды — на неделю.", -10, -5, 0)],
    [("Ночью в дверь начинают стучать.", -16, -9, 0)],
    [("Утром ты выбираешься на крышу…", -6, -2, 0)],
    [("…и видишь свет.", -10, -2, 0.45), ("Ты не один.", -16, -4, 0)],
    [("А ты бы выбрался из этого лифта?", -6, 0, 0.35), ("Пиши в комментариях.", -2, -2, 0)],
]

VOICE_FX = ",".join([
    "highpass=f=75:poles=2",
    "equalizer=f=140:t=q:w=1.0:g=2.5",     # тело/низ голоса
    "equalizer=f=380:t=q:w=1.2:g=-3",      # убрать «бочку»
    "equalizer=f=3200:t=q:w=1.0:g=3.5",    # разборчивость
    "highshelf=f=7500:g=3",                # яркость
    "aexciter=amount=1.2:drive=6:blend=0:freq=6000:ceil=16000",  # воздух выше 12 кГц
    "deesser=i=0.35:m=0.5:f=0.5",
    "acompressor=threshold=-22dB:ratio=3:attack=5:release=90:makeup=4",
])


def dec(path):
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-af", "aresample=resampler=soxr:precision=28",
                        "-ar", str(SR), "-ac", "1", "-f", "f32le", "-"], capture_output=True, check=True)
    return np.frombuffer(r.stdout, np.float32).astype(np.float64)


def trim(x, thr_db=-45, pad=0.03):
    fr = 240; n = len(x) // fr
    db = 20 * np.log10(np.sqrt(np.mean(x[: n * fr].reshape(n, fr) ** 2, 1)) + 1e-9)
    on = np.where(db > thr_db)[0]
    if not len(on): return x
    a = max(0, on[0] * fr - int(pad * SR)); b = min(len(x), (on[-1] + 1) * fr + int(pad * SR * 2))
    return x[a:b]


async def synth(text, rate, pitch, out, voice="ru-RU-DmitryNeural"):
    for attempt in range(8):  # сервис иногда отвечает без аудио — повторяем
        try:
            c = edge_tts.Communicate(text, voice, rate=f"{rate:+d}%", pitch=f"{pitch:+d}Hz")
            await c.save(out)
            if os.path.getsize(out) > 1000: return
        except edge_tts.exceptions.NoAudioReceived as e:
            print("  повтор", text, attempt + 1, e)
        await asyncio.sleep(1.5 * (attempt + 1))
    sys.exit(f"Не удалось озвучить: {text}")


def process(x, out_wav):
    tmp = out_wav + ".raw.wav"
    wavfile.write(tmp, SR, x.astype(np.float32))
    r = subprocess.run(["ffmpeg", "-v", "error", "-i", tmp, "-af", VOICE_FX, "-ar", str(SR), "-ac", "1",
                        "-f", "f32le", "-"], capture_output=True, check=True)
    os.remove(tmp)
    y = np.frombuffer(r.stdout, np.float32).astype(np.float64)
    # выровнять громкость по активной речи до -17 dBFS RMS, мягкий потолок -1.5 dBFS
    fr = 480; n = len(y) // fr
    rms = np.sqrt(np.mean(y[: n * fr].reshape(n, fr) ** 2, 1))
    act = rms[rms > rms.max() * 0.1]
    y *= 10 ** (-17 / 20) / np.sqrt(np.mean(act ** 2))
    lim = 10 ** (-1.5 / 20)
    y = np.where(np.abs(y) > lim * 0.8, np.sign(y) * (lim * 0.8 + (lim * 0.2) * np.tanh((np.abs(y) - lim * 0.8) / (lim * 0.2))), y)
    wavfile.write(out_wav, SR, (y * 32767).astype(np.int16))


async def main(only=None, script=SCRIPT, vdir=os.path.join(ROOT, "voice")):
    cdir = os.path.join(vdir, "chunks")
    os.makedirs(cdir, exist_ok=True)
    for i, chunks in enumerate(script):
        if only and i + 1 not in only: continue
        parts = []
        for k, (text, rate, pitch, pause) in enumerate(chunks):
            mp3 = os.path.join(cdir, f"{i+1:02d}_{k}.mp3")
            await synth(text, rate, pitch, mp3)
            parts.append(trim(dec(mp3)))
            if pause: parts.append(np.zeros(int(pause * SR)))
        x = np.concatenate([np.zeros(int(0.04 * SR))] + parts + [np.zeros(int(0.08 * SR))])
        out = os.path.join(vdir, f"{i+1:02d}.wav")
        process(x, out)
        print(out, round(len(x) / SR, 2), "с", flush=True)


if __name__ == "__main__":
    asyncio.run(main([int(a) for a in sys.argv[1:]] or None))
