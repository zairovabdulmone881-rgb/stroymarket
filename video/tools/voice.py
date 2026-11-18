#!/usr/bin/env python3
"""Озвучка выпуска: каждый кадр голосом ru-RU-DmitryNeural, затем сведение.
  python3 tools/voice.py episodes/001-abu-bakr-as-siddiq
Кладёт в папку выпуска: voice/NN.mp3 (каждый кадр), voice.mp3 (весь выпуск)
и timing.js (длительность кадров по длине озвучки).
Диктор вступает через LEAD секунд после смены кадра.
VOICE_DUMMY=1 — вместо голоса тишина расчётной длины (для проверки без сети)."""
import json, os, subprocess, sys, asyncio
LEAD, TAIL, MIN = 1.0, 1.2, 5.0
VOICE, RATE = "ru-RU-DmitryNeural", os.environ.get("VOICE_RATE", "-5%")

def episode(dirp):
    js = open(os.path.join(dirp, "episode.js"), encoding="utf-8").read()
    js = js[js.index("{"): js.rindex("}") + 1]
    return json.loads(subprocess.check_output(["node", "-e", f"process.stdout.write(JSON.stringify({js}))"], text=True))

def dur(p):
    return float(subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", p], text=True))

async def _say(text):
    """Текст -> mp3-байты. Сервис часто молчит, поэтому повторяем."""
    import edge_tts
    for attempt in range(12):
        try:
            data = b""
            async for ch in edge_tts.Communicate(text, VOICE, rate=RATE).stream():
                if ch["type"] == "audio": data += ch["data"]
            if data: return data
        except Exception as e:
            print(f"   попытка {attempt + 1}: {e}", flush=True)
        await asyncio.sleep(min(4 * (attempt + 1), 15))
    return None

async def _tts(text):
    data = await _say(text)
    if data is None:  # целиком не вышло — по предложениям
        import re
        data = b""
        for part in re.findall(r"[^.!?]+[.!?]*", text):
            piece = await _say(part.strip())
            if piece is None: return None
            data += piece; await asyncio.sleep(1)
    return data

def tts(text, out):
    data = asyncio.run(_tts(text))
    if not data: raise RuntimeError("озвучка не получена")
    open(out, "wb").write(data)

def main(dirp):
    ep = episode(dirp); vdir = os.path.join(dirp, "voice"); os.makedirs(vdir, exist_ok=True)
    timing, parts = [], []
    idx_path = os.path.join(vdir, "index.json")
    idx = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    new_idx, failed = {}, []
    fresh = not os.path.exists(os.path.join(dirp, "timing.js"))
    for i, f in enumerate(ep["frames"], 1):
        p = os.path.join(vdir, f"{i:02d}.mp3")
        key = f"{VOICE}|{RATE}|{f['voice']}"
        new_idx[f"{i:02d}"] = key
        if os.path.exists(p) and idx.get(f"{i:02d}") == key and not os.environ.get("VOICE_DUMMY"):
            pass  # текст кадра не менялся — озвучка уже есть
        elif os.environ.get("VOICE_DUMMY"):
            est = max(1.0, len(f["voice"]) / 14.0)
            subprocess.check_call(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi", "-i", "anullsrc=r=24000:cl=mono", "-t", f"{est:.2f}", p])
        else:
            try:
                tts(f["voice"], p); fresh = True
            except Exception as e:
                failed.append(i); new_idx.pop(f"{i:02d}", None); print(f"кадр {i:02d}: НЕ ОЗВУЧЕН ({e})"); continue
        d = round(max(MIN, LEAD + dur(p) + TAIL), 2)
        timing.append(d); parts.append((p, d))
        print(f"кадр {i:02d}: {d:5.2f} c")
    for extra in os.listdir(vdir):  # лишние кадры после сокращения выпуска
        if extra.endswith(".mp3") and int(extra[:2]) > len(ep["frames"]): os.remove(os.path.join(vdir, extra))
    if not os.environ.get("VOICE_DUMMY"):
        json.dump(new_idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    if failed:
        print("не озвучены кадры:", failed, "— запустите ещё раз, готовые кадры не перезаписываются")
        sys.exit(1)
    # Сведение: кадр = тишина LEAD + голос + тишина до конца кадра
    args, flt = ["ffmpeg", "-y", "-loglevel", "error"], []
    for k, (p, d) in enumerate(parts):
        args += ["-i", p]
        flt.append(f"[{k}:a]aresample=48000,aformat=channel_layouts=stereo,adelay={int(LEAD*1000)}|{int(LEAD*1000)},apad,atrim=0:{d}[a{k}]")
    flt.append("".join(f"[a{k}]" for k in range(len(parts))) + f"concat=n={len(parts)}:v=0:a=1[out]")
    subprocess.check_call(args + ["-filter_complex", ";".join(flt), "-map", "[out]", "-c:a", "libmp3lame", "-b:a", "160k", os.path.join(dirp, "voice.mp3")])
    with open(os.path.join(dirp, "timing.js"), "w", encoding="utf-8") as fh:
        fh.write("// Создано tools/voice.py — длительность кадров по озвучке\nwindow.TIMING = " + json.dumps(timing) + ";\n")
    print(f"итого: {sum(timing):.1f} c")
    if fresh and os.environ.get("UPDATED_LIST"):
        with open(os.environ["UPDATED_LIST"], "a") as fh: fh.write(os.path.basename(dirp) + "\n")

if __name__ == "__main__":
    for d in sys.argv[1:]: main(d.rstrip("/"))
