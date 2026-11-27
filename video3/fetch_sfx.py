#!/usr/bin/env python3
"""Поиск реальных звуков на Freesound (только лицензия CC0) и скачивание превью HQ.
python3 fetch_sfx.py search "<запрос>"   — показать кандидатов
python3 fetch_sfx.py get <id> <имя>       — скачать в video2/sfx_real/<имя>.wav
Список использованных звуков с авторами — video2/sfx_real/CREDITS.txt"""
import html, os, re, subprocess, sys, urllib.parse, urllib.request

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sfx_real")
UA = {"User-Agent": "Mozilla/5.0"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40).read()


def search(q, n=12):
    url = "https://freesound.org/search/?" + urllib.parse.urlencode(
        {"q": q, "f": 'license:"Creative Commons 0"', "s": "Downloads (most first)"})
    s = fetch(url).decode("utf-8", "replace")
    res = []
    for m in re.finditer(r'data-sound-id="(\d+)"\s+data-username="([^"]*)".*?data-mp3="([^"]+)".*?data-title="([^"]*)"\s+data-duration="([\d.]+)"', s, re.S):
        res.append({"id": m.group(1), "user": m.group(2), "mp3": m.group(3).replace("-lq.mp3", "-hq.mp3"),
                    "title": html.unescape(m.group(4)), "dur": float(m.group(5))})
    return res[:n]


def get(sid, name, q=None):
    os.makedirs(OUT, exist_ok=True)
    page = fetch(f"https://freesound.org/s/{sid}/").decode("utf-8", "replace")
    mp3 = re.search(r'data-mp3="([^"]+)"', page).group(1).replace("-lq.mp3", "-hq.mp3")
    title = html.unescape(re.search(r'data-title="([^"]*)"', page).group(1))
    user = re.search(r'data-username="([^"]*)"', page).group(1)
    lic = "CC0" if ("publicdomain/zero" in page or "Creative Commons 0" in page) else "CHECK"
    tmp = os.path.join(OUT, name + ".mp3")
    open(tmp, "wb").write(fetch(mp3))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", tmp, "-ac", "1", "-ar", "48000", os.path.join(OUT, name + ".wav")], check=True)
    os.remove(tmp)
    with open(os.path.join(OUT, "CREDITS.txt"), "a") as f:
        f.write(f"{name}.wav  —  «{title}» by {user}, https://freesound.org/s/{sid}/  [{lic}]\n")
    print("ok", name, title, user, lic)


if __name__ == "__main__":
    if sys.argv[1] == "search":
        for r in search(sys.argv[2]):
            print(r["id"], "%.1fs" % r["dur"], r["user"], "|", r["title"])
    else:
        get(sys.argv[2], sys.argv[3])
