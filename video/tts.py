#!/usr/bin/env python3
"""Озвучка сцен голосом ru-RU-DmitryNeural (edge-tts) -> voice/NN.mp3.
edge-tts жёстко берёт CA из certifi; в песочнице HTTPS идёт через прокси,
поэтому указываем ему CA-бандл прокси (если он есть)."""
import asyncio, os, ssl, sys
import edge_tts, edge_tts.communicate as comm
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build import SCENES, ROOT

CA = "/root/.ccr/ca-bundle.crt"
if os.path.exists(CA):
    comm._SSL_CTX = ssl.create_default_context(cafile=CA)

async def main(only=None):
    os.makedirs(os.path.join(ROOT, "voice"), exist_ok=True)
    for i, (text, _, _) in enumerate(SCENES):
        if only and i + 1 not in only: continue
        out = os.path.join(ROOT, "voice", f"{i+1:02d}.mp3")
        for attempt in range(8):  # сервис иногда отвечает без аудио — повторяем
            try:
                c = edge_tts.Communicate(text, "ru-RU-DmitryNeural", rate="-8%", pitch="-4Hz")
                await c.save(out)
                if os.path.getsize(out) > 1000: break
            except edge_tts.exceptions.NoAudioReceived as e:
                print("  повтор", i + 1, attempt + 1, e)
            await asyncio.sleep(1.5 * (attempt + 1))
        else:
            sys.exit(f"Не удалось озвучить сцену {i+1}")
        print(out, os.path.getsize(out))

asyncio.run(main([int(a) for a in sys.argv[1:]] or None))
