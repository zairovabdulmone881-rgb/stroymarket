"""Озвучка ролика «Халид ибн аль-Валид» голосом Дмитрий (ru-RU-DmitryNeural)."""
import asyncio, json, pathlib, re, sys
import edge_tts

HERE = pathlib.Path(__file__).parent
VOICE = "ru-RU-DmitryNeural"


async def say(text):
    """Один кусок текста -> mp3-байты; сервис иногда молчит, поэтому повторяем."""
    for attempt in range(6):
        try:
            data = b""
            async for chunk in edge_tts.Communicate(text, VOICE).stream():
                if chunk["type"] == "audio":
                    data += chunk["data"]
            if data:
                return data
        except Exception as e:
            print(f"   попытка {attempt + 1}: {e}", flush=True)
        await asyncio.sleep(4 * (attempt + 1))
    return None


async def main():
    lines = json.loads((HERE / "lines.json").read_text(encoding="utf8"))
    out = HERE / "voice"
    out.mkdir(exist_ok=True)
    failed = []
    for i, text in enumerate(lines, 1):
        data = await say(text)
        if data is None:  # целиком не вышло — читаем по предложениям
            data = b""
            for part in re.findall(r"[^.!?]+[.!?]*", text):
                piece = await say(part.strip())
                if piece is None:
                    failed.append((i, part.strip()))
                    data = None
                    break
                data += piece
                await asyncio.sleep(1)
        if data:
            (out / f"{i:02d}.mp3").write_bytes(data)
            print(f"кадр {i}: готово", flush=True)
        await asyncio.sleep(2)
    for i, part in failed:
        print(f"НЕ ОЗВУЧЕНО, кадр {i}: {part}")
    sys.exit(1 if failed else 0)


asyncio.run(main())
