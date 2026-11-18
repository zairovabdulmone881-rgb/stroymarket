#!/usr/bin/env python3
"""Поиск и сверка хадисов по открытой базе fawazahmed0/hadith-api.
  python3 tools/hadith.py fetch                 — скачать сборники в video/.cache/hadith
  python3 tools/hadith.py find bukhari "سيف من سيوف الله" [--eng word]
  python3 tools/hadith.py show bukhari 4262
  python3 tools/hadith.py verify episodes/001-abu-bakr/episode.js   — сверка всех ссылок выпуска
Номера: Бухари — нумерация Фатх аль-Бари; Муслим — нумерация Абд аль-Баки
(arabicnumber), как принято цитировать; Тирмизи — с оценками аль-Альбани."""
import json, os, re, sys, urllib.request
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CACHE = os.environ.get("HADITH_CACHE", os.path.join(ROOT, ".cache", "hadith"))
BOOKS = ["bukhari", "muslim", "tirmidhi", "abudawud", "nasai", "ibnmajah"]
BASE = "https://cdn.jsdelivr.net/gh/fawazahmed0/hadith-api@1/editions/{}.min.json"
QURAN = "https://api.alquran.cloud/v1/ayah/{}/quran-simple-clean"

HARAKAT = re.compile(r"[ؐ-ًؚ-ٰٟۖ-ۭـ]")
def norm(s):
    s = HARAKAT.sub("", s)
    s = re.sub("[إأآٱ]", "ا", s).replace("ى", "ي").replace("ة", "ه").replace("ؤ", "و").replace("ئ", "ي")
    s = re.sub(r"[^ء-ي ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()

_db = {}
def load(lang, book):
    k = f"{lang}-{book}"
    if k not in _db:
        p = os.path.join(CACHE, k + ".json")
        if not os.path.exists(p):
            os.makedirs(CACHE, exist_ok=True)
            urllib.request.urlretrieve(BASE.format(k), p)
        _db[k] = json.load(open(p, encoding="utf-8"))["hadiths"]
    return _db[k]

def num_of(book, h):
    # Муслим цитируется по Абд аль-Баки (arabicnumber), остальные — по hadithnumber
    return int(float(h["arabicnumber"])) if book == "muslim" and h.get("arabicnumber") else h["hadithnumber"]

def get(book, n):
    ar = [h for h in load("ara", book) if num_of(book, h) == n]
    en = {h["hadithnumber"]: h for h in load("eng", book)}
    return [(h, en.get(h["hadithnumber"])) for h in ar]

def find(book, q, eng=None, limit=15):
    nq = norm(q); out = []
    en = {h["hadithnumber"]: h for h in load("eng", book)}
    for h in load("ara", book):
        if nq in norm(h["text"]):
            e = en.get(h["hadithnumber"])
            if eng and (not e or eng.lower() not in e["text"].lower()): continue
            out.append((h, e))
    for h, e in out[:limit]:
        g = "; ".join(f'{x["name"]}: {x["grade"]}' for x in (e or h).get("grades", []))
        print(f"== {book} {num_of(book, h)} (seq {h['hadithnumber']}) {g}\n{(e or {}).get('text','')[:700]}\n")
    print(f"всего: {len(out)}")

def verify_quote(ref, ar):
    book, n = ref.split(":"); n = int(n)
    if book == "quran":
        raise ValueError
    hs = get(book, n)
    if not hs: return False, "номер не найден"
    na = norm(ar)
    for h, e in hs:
        if na in norm(h["text"]):
            grades = (e or h).get("grades", [])
            g = "; ".join(f'{x["name"]}: {x["grade"]}' for x in grades)
            alb = [x["grade"].lower() for x in grades if "albani" in x["name"].lower()]
            if book not in ("bukhari", "muslim") and not (alb and any(w in alb[0] for w in ("sahih", "hasan"))):
                return False, "нет оценки «достоверный/хороший» у аль-Альбани: " + g
            return True, g
    return False, "текст не найден в этом хадисе"

def verify_quran(key, ar):
    # key: "сура:аят" или "сура:аят1-аят2"
    sura, ayat = key.split(":")
    a, b = (ayat.split("-") + [ayat])[:2]
    txt = ""
    for n in range(int(a), int(b) + 1):
        req = urllib.request.Request(QURAN.format(f"{sura}:{n}"), headers={"User-Agent": "Mozilla/5.0"})
        txt += " " + json.load(urllib.request.urlopen(req))["data"]["text"]
    return norm(ar) in norm(txt), ""

def verify(path):
    src = open(path, encoding="utf-8").read()
    js = src[src.index("{"): src.rindex("}") + 1]
    data = json.loads(subprocess_node(js))
    ok = True
    for i, f in enumerate(data["frames"], 1):
        ref = f.get("ref")
        if not ref:
            if f["type"] == "quote": print(f"  кадр {i}: НЕТ ref у цитаты"); ok = False
            continue
        if f["type"] == "quote" and not f.get("ar"):
            print(f"  кадр {i}: у цитаты нет арабского текста"); ok = False; continue
        refs = ref if isinstance(ref, list) else [ref]
        for r in refs:
            ar = f.get("ar") if f["type"] == "quote" else f.get("check")
            if not ar:
                print(f"  кадр {i}: {r} — нет текста для сверки (поле check)"); ok = False; continue
            if r.startswith("quran:"):
                good, note = verify_quran(r[6:], ar)
            else:
                good, note = verify_quote(r, ar)
            print(f"  кадр {i}: {r:16} {'OK ' if good else 'ОШИБКА'} {note}")
            ok &= good
    return ok

def subprocess_node(js):
    import subprocess
    return subprocess.check_output(["node", "-e", f"process.stdout.write(JSON.stringify({js}))"], text=True)

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "fetch":
        for b in BOOKS:
            for l in ("ara", "eng"): load(l, b)
        print("ok")
    elif a[0] == "find":
        eng = a[a.index("--eng") + 1] if "--eng" in a else None
        find(a[1], a[2], eng)
    elif a[0] == "show":
        for h, e in get(a[1], int(a[2])):
            g = "; ".join(f'{x["name"]}: {x["grade"]}' for x in (e or h).get("grades", []))
            print(f"== {a[1]} {a[2]} (seq {h['hadithnumber']}) {g}\n{h['text']}\n--\n{(e or {}).get('text','')}\n")
    elif a[0] == "snip":
        # snip bukhari 3653 "начало" "конец" — точная цитата из текста (с огласовками)
        book, n, a1, a2 = a[1], int(a[2]), norm(a[3]), norm(a[4])
        for h, e in get(book, n):
            t = h["text"]; idx = []  # соответствие позиций нормализованного текста исходному
            nt = ""
            for k, ch in enumerate(t):
                c = norm(ch) if ch.strip() else " "
                if c == "" : continue
                if c == " " and nt.endswith(" "): continue
                nt += c; idx.extend([k] * len(c))
            i = nt.find(a1); j = nt.find(a2, i)
            if i < 0 or j < 0: print("не найдено в seq", h["hadithnumber"]); continue
            end = idx[j + len(a2) - 1] + 1
            while end < len(t) and HARAKAT.match(t[end]): end += 1
            print(t[idx[i]:end].strip())
    elif a[0] == "verify":
        allok = True
        for p in a[1:]:
            print(p); allok &= verify(p)
        sys.exit(0 if allok else 1)
