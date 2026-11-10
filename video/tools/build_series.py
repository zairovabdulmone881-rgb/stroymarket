#!/usr/bin/env python3
"""Собирает страницу серии (список 100 выпусков + шаблон и дизайн) из video/series.json.

    python3 video/tools/build_series.py   ->  video/series/index.html
"""
import html, json, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
data = json.loads((ROOT / "series.json").read_text(encoding="utf8"))
items = data["items"]
done = [it for it in items if it["status"] == "готов"]


def cell(it):
    num = f'<span class="k">{it["num"]:03d}</span>'
    name = f'<span class="nm">{html.escape(it["name"])}</span>'
    if it["status"] == "готов" and it.get("artifact"):
        return f'<li class="done"><a href="{it["artifact"]}" target="_blank" rel="noopener">{num}{name}<span class="chip">готов</span></a></li>'
    return f'<li>{num}{name}</li>'


page = (ROOT / "series" / "series.template.html").read_text(encoding="utf8")
page = (page.replace("{{DONE}}", str(len(done))).replace("{{TOTAL}}", str(data["total"]))
            .replace("{{PCT}}", f'{len(done) / data["total"] * 100:.0f}')
            .replace("{{NOTE}}", html.escape(data["note"]))
            .replace("{{TEN}}", "\n".join(cell(it) for it in items[:10]))
            .replace("{{REST}}", "\n".join(cell(it) for it in items[10:])))
(ROOT / "series" / "index.html").write_text(page, encoding="utf8")
print(f"Серия: готово {len(done)} из {data['total']}")
