"""Озвучка выпусков голосом Дмитрий (ru-RU-DmitryNeural). Запускается на GitHub Actions.

Проходит по всем папкам video/episodes/*/ и для каждой строки lines.json,
у которой ещё нет voice/NN.mp3, записывает её. Готовые файлы не перезаписывает:
чтобы переозвучить кадр, удалите его mp3.
"""
import asyncio, json, pathlib, re, sys
import edge_tts

EPISODES = pathlib.Path(__file__).resolve().parent.parent / "episodes"
VOICE = "ru-RU-DmitryNeural"


async def say(text):
    """Кусок текста -> mp3-байты. Сервис часто молчит, поэтому повторяем."""
    for attempt in range(12):
        try:
            data = b""
            async for chunk in edge_tts.Communicate(text, VOICE).stream():
                if chunk["type"] == "audio":
                    data += chunk["data"]
            if data:
                return data
        except Exception as e:
            print(f"   попытка {attempt + 1}: {e}", flush=True)
        await asyncio.sleep(min(4 * (attempt + 1), 15))
    return None


async def main():
    failed = []
    for lines_file in sorted(EPISODES.glob("*/lines.json")):
        ep = lines_file.parent
        out = ep / "voice"
        out.mkdir(exist_ok=True)
        for i, text in enumerate(json.loads(lines_file.read_text(encoding="utf8")), 1):
            target = out / f"{i:02d}.mp3"
            if target.exists() or not text.strip():
                continue
            data = await say(text)
            if data is None:  # целиком не вышло — читаем по предложениям
                data = b""
                for part in re.findall(r"[^.!?]+[.!?]*", text):
                    piece = await say(part.strip())
                    if piece is None:
                        failed.append(f"{ep.name}, кадр {i}: {part.strip()}")
                        data = None
                        break
                    data += piece
                    await asyncio.sleep(1)
            if data:
                target.write_bytes(data)
                print(f"{ep.name}, кадр {i}: готово", flush=True)
            await asyncio.sleep(2)
    for f in failed:
        print("НЕ ОЗВУЧЕНО:", f)
    sys.exit(1 if failed else 0)


asyncio.run(main())
