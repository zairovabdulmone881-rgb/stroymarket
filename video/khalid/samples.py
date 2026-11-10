"""Образцы озвучки первого кадра разными голосами — для выбора."""
import asyncio, json, pathlib, sys
import edge_tts

HERE = pathlib.Path(__file__).parent
VARIANTS = {
    "1-dmitry-torzhestvenny": dict(voice="ru-RU-DmitryNeural", rate="-12%", pitch="-8Hz"),
    "2-andrew": dict(voice="en-US-AndrewMultilingualNeural", rate="-5%"),
    "3-brian": dict(voice="en-US-BrianMultilingualNeural", rate="-5%"),
    "4-florian": dict(voice="de-DE-FlorianMultilingualNeural", rate="-5%"),
}


async def say(text, **kw):
    for attempt in range(12):
        try:
            data = b""
            async for chunk in edge_tts.Communicate(text, **kw).stream():
                if chunk["type"] == "audio":
                    data += chunk["data"]
            if data:
                return data
        except Exception as e:
            print(f"   попытка {attempt + 1}: {e}", flush=True)
        await asyncio.sleep(min(4 * (attempt + 1), 15))
    return None


async def main():
    text = json.loads((HERE / "lines.json").read_text(encoding="utf8"))[0]
    out = HERE / "samples"
    out.mkdir(exist_ok=True)
    failed = []
    for name, kw in VARIANTS.items():
        if (out / f"{name}.mp3").exists():
            continue
        data = await say(text, **kw)
        if data:
            (out / f"{name}.mp3").write_bytes(data)
            print(f"{name}: готово", flush=True)
        else:
            failed.append(name)
    for name in failed:
        print(f"НЕ ЗАПИСАНО: {name}")
    sys.exit(1 if failed else 0)


asyncio.run(main())
