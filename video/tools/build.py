#!/usr/bin/env python3
"""Собирает страницу выпуска: шаблон + episode.js (+ длительности озвучки).

    python3 video/tools/build.py video/episodes/044-khalid

Пишет в папку выпуска index.html (плеер) и lines.json (текст диктора для озвучки).
"""
import json, math, pathlib, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
ep = pathlib.Path(sys.argv[1]).resolve()
code = (ep / "episode.js").read_text(encoding="utf8")

# имя, тексты диктора и минимальные длительности берём из самого episode.js
probe = code + "\n;JSON.stringify({name:EPISODE.name,say:FRAMES.map(f=>f.say||''),t:FRAMES.map(f=>f.t)})"
info = json.loads(subprocess.check_output(
    ["node", "-e", "process.stdout.write(require('vm').runInNewContext(require('fs').readFileSync(0,'utf8')))"],
    input=probe.encode()))
(ep / "lines.json").write_text(json.dumps(info["say"], ensure_ascii=False, indent=1) + "\n", encoding="utf8")

voice = [ep / "voice" / f"{i:02d}.mp3" for i in range(1, len(info["t"]) + 1)]
has_voice = all(v.exists() for v in voice)
dur = list(info["t"])
if has_voice:
    for i, v in enumerate(voice):
        a = float(subprocess.check_output(
            ["ffprobe", "-v", "0", "-show_entries", "format=duration", "-of", "csv=p=0", str(v)]))
        dur[i] = max(dur[i], math.ceil((a + 2.2) * 2) / 2)  # секунда до голоса, секунда с запасом после

page = (ROOT / "template" / "template.html").read_text(encoding="utf8")
page = (page.replace("{{NAME}}", info["name"]).replace("{{EPISODE_JS}}", code.strip())
            .replace("{{DUR}}", json.dumps(dur)).replace("{{HAS_VOICE}}", "true" if has_voice else "false"))
(ep / "index.html").write_text(page, encoding="utf8")
print(f"{ep.name}: {len(dur)} кадров, {sum(dur):.1f} с, озвучка: {'есть' if has_voice else 'нет'}")
