#!/usr/bin/env python3
"""Делает готовый mp4 выпуска: сборка страницы, съёмка кадров, сведение с озвучкой.

    python3 video/tools/make_video.py video/episodes/044-khalid [куда положить mp4]

Нужны node с playwright, ffmpeg и озвучка в папке выпуска voice/01.mp3 … NN.mp3.
"""
import json, os, pathlib, re, shutil, subprocess, sys, tempfile

TOOLS = pathlib.Path(__file__).resolve().parent
ep = pathlib.Path(sys.argv[1]).resolve()
out = pathlib.Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else ep.parent.parent / "out" / f"{ep.name}.mp4"
out.parent.mkdir(parents=True, exist_ok=True)
FPS, LEAD = 30, 1.0

subprocess.check_call([sys.executable, str(TOOLS / "build.py"), str(ep)])
page = (ep / "index.html").read_text(encoding="utf8")
dur = json.loads(re.search(r"const DUR=(\[[^\]]*\])", page).group(1))
if "const HAS_VOICE=true" not in page:
    sys.exit("Нет озвучки: в папке voice должны лежать mp3 для всех кадров.")

frames = pathlib.Path(tempfile.mkdtemp(prefix="frames-"))
n = min(4, os.cpu_count() or 1)
jobs = [subprocess.Popen(["node", str(TOOLS / "render.js"), str(ep), str(frames), str(w), str(n), str(FPS)])
        for w in range(n)]
if any(j.wait() for j in jobs):
    sys.exit("Съёмка кадров не удалась.")

cmd = ["ffmpeg", "-y", "-v", "error", "-framerate", str(FPS), "-i", str(frames / "%06d.jpg")]
flt, t = [], 0.0
for i, d in enumerate(dur, 1):
    cmd += ["-i", str(ep / "voice" / f"{i:02d}.mp3")]
    flt.append(f"[{i}:a]aresample=48000,adelay={int((t + LEAD) * 1000)}:all=1[a{i}]")
    t += d
flt.append("".join(f"[a{i}]" for i in range(1, len(dur) + 1))
           + f"amix=inputs={len(dur)}:normalize=0,apad,atrim=0:{t}[a]")
cmd += ["-filter_complex", ";".join(flt), "-map", "0:v", "-map", "[a]",
        "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-t", str(t), str(out)]
subprocess.check_call(cmd)
shutil.rmtree(frames)
print(f"Готово: {out} ({t:.0f} с)")
