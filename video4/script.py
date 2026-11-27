"""Сцены читаются из scenario4.txt: номер | текст | ключевые слова | звук."""
import os
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCENES = []
for line in open(os.path.join(ROOT, "scenario4.txt"), encoding="utf-8"):
    p = [x.strip() for x in line.split("|")]
    if len(p) == 4 and p[0].isdigit():
        SCENES.append({"text": p[1], "keys": [k.strip() for k in p[2].split(",")], "sfx": p[3],
                       "red": int(p[0]) in (16, 17)})
assert len(SCENES) == 17, len(SCENES)
