"""Озвучка ролика «Халид ибн аль-Валид» голосом Дмитрий (ru-RU-DmitryNeural)."""
import asyncio, json, pathlib
import edge_tts

HERE = pathlib.Path(__file__).parent
VOICE = "ru-RU-DmitryNeural"


async def main():
    lines = json.loads((HERE / "lines.json").read_text(encoding="utf8"))
    out = HERE / "voice"
    out.mkdir(exist_ok=True)
    for i, text in enumerate(lines, 1):
        for attempt in range(4):
            try:
                await edge_tts.Communicate(text, VOICE).save(str(out / f"{i:02d}.mp3"))
                break
            except Exception as e:  # сервис иногда рвёт соединение
                print(f"кадр {i}: попытка {attempt + 1} не удалась: {e}")
                if attempt == 3:
                    raise
                await asyncio.sleep(3 * (attempt + 1))
        print(f"кадр {i}: готово")


asyncio.run(main())
