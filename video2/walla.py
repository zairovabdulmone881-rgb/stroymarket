#!/usr/bin/env python3
"""Исходники для «живых» эффектов из голосов edge-tts: гул толпы (walla) и крик.
Выход: video2/sfx_src/*.wav (48 кГц моно)."""
import asyncio, os, ssl, subprocess
import edge_tts, edge_tts.communicate
edge_tts.communicate._SSL_CTX = ssl.create_default_context(cafile="/root/.ccr/ca-bundle.crt")

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx_src")
os.makedirs(OUT, exist_ok=True)

LINES = [
    "Где вода? Тут же была вода!", "Не толкайтесь, тут дети!", "Мама, мама, ты где?",
    "Пропустите, пожалуйста, мне надо пройти", "Касса не работает, вы слышите?", "Это моё, отойди!",
    "Сколько можно стоять, давайте быстрее", "Хлеба больше нет, всё разобрали", "Позвони отцу, срочно!",
    "Что вообще происходит, кто-нибудь знает?", "Связи нет, ничего не грузится", "Отойдите от двери!",
    "Берите что есть и уходим", "Не кричите, все слышат", "Да куда вы лезете?", "Девушка, вы последняя?",
]
VOICES = ["ru-RU-DmitryNeural", "ru-RU-SvetlanaNeural", "uk-UA-OstapNeural", "uk-UA-PolinaNeural"]


async def say(text, voice, rate, pitch, path):
    for k in range(10):
        try:
            c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch)
            with open(path + ".mp3", "wb") as f:
                async for ch in c.stream():
                    if ch["type"] == "audio": f.write(ch["data"])
            break
        except Exception as e:
            print("retry", text, e); await asyncio.sleep(3 + 2 * k)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", path + ".mp3", "-ac", "1", "-ar", "48000", path], check=True)
    os.remove(path + ".mp3")


async def main():
    jobs = []
    for i, line in enumerate(LINES):
        v = VOICES[i % len(VOICES)]
        rate = f"{(-10 + (i * 7) % 30):+d}%"
        pitch = f"{(-12 + (i * 5) % 24):+d}Hz"
        p = os.path.join(OUT, f"walla_{i:02d}.wav")
        if not os.path.exists(p): jobs.append(say(line, v, rate, pitch, p))
    p = os.path.join(OUT, "shout.wav")
    if not os.path.exists(p): jobs.append(say("Эй! Отдай!", "uk-UA-OstapNeural", "+25%", "+25Hz", p))
    for j in jobs: await j
    print("ok", len(os.listdir(OUT)))

asyncio.run(main())
