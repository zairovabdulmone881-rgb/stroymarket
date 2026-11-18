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

async def tts(text, out):
    import edge_tts
    await edge_tts.Communicate(text, VOICE, rate=RATE).save(out)

def main(dirp):
    ep = episode(dirp); vdir = os.path.join(dirp, "voice"); os.makedirs(vdir, exist_ok=True)
    timing, parts = [], []
    idx_path = os.path.join(vdir, "index.json")
    idx = json.load(open(idx_path, encoding="utf-8")) if os.path.exists(idx_path) else {}
    new_idx = {}
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
            for attempt in range(4):
                try: asyncio.run(tts(f["voice"], p)); break
                except Exception as e:
                    if attempt == 3: raise
                    print("повтор:", e)
        d = round(max(MIN, LEAD + dur(p) + TAIL), 2)
        timing.append(d); parts.append((p, d))
        print(f"кадр {i:02d}: {d:5.2f} c")
    for extra in os.listdir(vdir):  # лишние кадры после сокращения выпуска
        if extra.endswith(".mp3") and int(extra[:2]) > len(ep["frames"]): os.remove(os.path.join(vdir, extra))
    if not os.environ.get("VOICE_DUMMY"):
        json.dump(new_idx, open(idx_path, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
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

if __name__ == "__main__":
    for d in sys.argv[1:]: main(d.rstrip("/"))
