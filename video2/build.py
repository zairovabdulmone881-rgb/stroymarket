#!/usr/bin/env python3
"""Сборка final_video_2.mp4: 1080x1920, 30 fps, H.264 + AAC.
Картинка на весь экран, поверх только субтитры. Без музыки: голос + звуковые эффекты.
Запуск: python3 video2/tts.py && python3 video2/build.py [--preview]"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from script import SCENES
import sfx

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
V2 = os.path.join(ROOT, "video2")
W, H, FPS, SR = 1080, 1920, 30, 48000
BASE = 1.2                      # запас разрешения подготовленного кадра под наезды
FONT = os.path.join(ROOT, "fonts", "Montserrat_900Black.ttf")
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FS, STROKE = 92, 12
CARD_CY = 760        # центр иллюстрации по вертикали
SUB_BELOW = 1400     # субтитры — на фоне под иллюстрацией (не на лицах), выше нижних 380 px
SUB_CX, SUB_CY, SUB_MAXW = 540, 1250, 860   # ВСЕГДА: центр по горизонтали, центр текста на 1250 px, ширина ≤ 860 px
YELLOW, RED, WHITE = (255, 210, 26), (255, 43, 28), (255, 255, 255)
GAP, LAST_TAIL, PRE15 = 0.3, 1.5, 0.6
OUT = os.path.join(ROOT, sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "final_video_2.mp4")


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ---------------- тайминг ----------------
voices = [json.load(open(os.path.join(V2, "voice", f"{n:02d}.json"))) for n in range(1, 18)]
durs = []
for i, v in enumerate(voices):
    d = v["dur"] + GAP
    if i == 13: d = v["dur"] + PRE15          # 0.6 с тишины перед сценой 15
    if i == 16: d += LAST_TAIL
    durs.append(d)
starts = np.concatenate([[0], np.cumsum(durs)[:-1]])
TOTAL = float(sum(durs))
NF = int(round(TOTAL * FPS))


# ---------------- слова → фразы субтитров ----------------
def tokens(text):
    """слова исходного текста + знак препинания после них"""
    out = []
    for m in re.finditer(r"[\w][\w\-]*", text):
        tail = text[m.end():m.end() + 3]
        out.append((m.group(0), bool(re.match(r"\s*[.,:!?…—»]", tail))))
    return out


def chunks_for(i):
    sc, words = SCENES[i], voices[i]["words"]
    toks = tokens(sc["text"])
    assert len(toks) == len(words), (i, toks, [w["w"] for w in words])
    keys = [k.lower() for k in sc["keys"]]
    items = []
    for (tok, brk), w in zip(toks, words):
        items.append({"w": tok.upper(), "t0": w["t0"], "t1": w["t1"], "brk": brk, "key": tok.lower() in keys})
    groups, cur = [], []
    for k, it in enumerate(items):
        cur.append(it)
        nxt = items[k + 1] if k + 1 < len(items) else None
        if it["brk"] or len(cur) == 3 or nxt is None or nxt["t0"] - it["t1"] > 0.3:
            groups.append(cur); cur = []
    return groups


font_cache = {}
def font(sz):
    if sz not in font_cache: font_cache[sz] = ImageFont.truetype(FONT, sz)
    return font_cache[sz]


def word_sprite(text, color, sz):
    f = font(sz)
    l, t, r, b = f.getbbox(text, stroke_width=STROKE)
    pad = 18
    im = Image.new("RGBA", (r - l + 2 * pad, b - t + 2 * pad), (0, 0, 0, 0))
    # мягкая тень под обводкой — для читаемости на светлом фоне (не плашка)
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).text((pad - l, pad - t), text, font=f, fill=255, stroke_width=STROKE + 4)
    sh = sh.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.75))
    im.putalpha(sh)
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=color, stroke_width=STROKE, stroke_fill=(0, 0, 0))
    return im


GAP_K, LINE_K = 0.18, 1.12


def text_w(spr):
    return spr.width - 36          # видимая ширина (без полей под тень)


def layout(group, accent, sz=FS):
    """раскладка фразы: слова целиком (никаких переносов с дефисом), центр по горизонтали (540),
    центр блока на 1250 px, не больше 2 строк, строка ≤ 860 px. None — если не помещается при этом размере."""
    spr = [word_sprite(it["w"], accent if it["key"] else WHITE, sz) for it in group]
    gap, lh = int(sz * GAP_K), int(sz * LINE_K)
    if max(text_w(x) for x in spr) > SUB_MAXW:
        return None
    lines = [[0]]
    for j in range(1, len(spr)):
        lw = sum(text_w(spr[q]) for q in lines[-1]) + gap * len(lines[-1]) + text_w(spr[j])
        if lw > SUB_MAXW: lines.append([j])
        else: lines[-1].append(j)
    if len(lines) > 2:
        return None
    widths = [sum(text_w(spr[q]) for q in ln) + gap * (len(ln) - 1) for ln in lines]
    y0 = SUB_CY - lh * len(lines) / 2
    out = []
    for li, ln in enumerate(lines):
        x = SUB_CX - widths[li] / 2
        for j in ln:
            out.append((j, spr[j], (x + text_w(spr[j]) / 2, y0 + li * lh + lh / 2)))
            x += text_w(spr[j]) + gap
    return out


def fit_groups(groups, accent):
    """92 px, если влезает в 2 строки по 860 px. Слово шире 860 px — уменьшаем шрифт для этой фразы
    (слово остаётся целым на своей строке). Больше 2 строк — делим фразу."""
    res = []
    stack = list(groups)
    while stack:
        g = stack.pop(0)
        lay = layout(g, accent)
        if lay is None:
            too_wide = any(text_w(word_sprite(it["w"], WHITE, FS)) > SUB_MAXW for it in g)
            if too_wide:
                for sz in range(FS - 2, 40, -2):
                    lay = layout(g, accent, sz)
                    if lay is not None: break
            if lay is None and len(g) > 1:
                m = (len(g) + 1) // 2
                stack = [g[:m], g[m:]] + stack
                continue
        res.append((g, lay))
    return res


SUBS = []   # (t_on, t_off, [(t_word, sprite, center)])
LAYOUT_LOG = []
for i in range(17):
    if i == 14: continue                          # сцена 15: без субтитров — текст СМС уже на картинке
    accent = YELLOW
    gs = fit_groups(chunks_for(i), accent)
    for gi, (g, lay) in enumerate(gs):
        t_on = starts[i] + g[0]["t0"]
        if gi + 1 < len(gs):
            t_off = starts[i] + min(gs[gi + 1][0][0]["t0"], g[-1]["t1"] + 0.6)
        else:
            t_off = starts[i] + min(durs[i], g[-1]["t1"] + (LAST_TAIL if i == 16 else 0.6))
        # фраза появляется целиком (в начале первого слова) — текст всегда в одном месте, по центру 540×1250
        SUBS.append((t_on, t_off, [(t_on, sp, c) for k, sp, c in lay]))
        LAYOUT_LOG.append((i + 1, " ".join(it["w"] for it in g), lay))


# ---------------- картинки и движение ----------------
def card_box(a):
    """границы чёткой иллюстрации внутри оригинала (вокруг — размытые поля)"""
    g = np.asarray(a.convert("L"), np.float32)
    rows = np.abs(np.diff(g, axis=0)).mean(1); cols = np.abs(np.diff(g, axis=1)).mean(0)
    r = np.where(rows > np.percentile(rows, 60))[0]; c = np.where(cols > np.percentile(cols, 40))[0]
    return c.min() / a.width, r.min() / a.height, c.max() / a.width, r.max() / a.height


# горизонтальная панорама по иллюстрации (доля ширины — центр окна 9:16): старт → конец; без зума
PAN = {1: (0.35, 0.65), 2: (0.35, 0.65), 3: (0.30, 0.75), 4: (0.30, 0.65), 5: (0.30, 0.70), 6: (0.35, 0.70),
       7: (0.30, 0.70), 8: (0.40, 0.60), 9: (0.30, 0.55), 10: (0.25, 0.70), 11: (0.30, 0.65), 12: (0.35, 0.65),
       13: (0.30, 0.70), 14: (0.40, 0.65), 15: (0.40, 0.50), 16: (0.35, 0.65), 17: (0.45, 0.55)}


SCALE17 = None     # сцена 17: картинка целиком во всю ширину (лицо+шапка занимают ~6–97% ширины, 25% мало)


def prep_image(i):
    """ОРИГИНАЛ imgs2/NN.png без изменений: 720×1280 (9:16) → 1080×1920, без обрезки, зума и панорамы"""
    src = Image.open(os.path.join(ROOT, "imgs2", f"{i + 1:02d}.png")).convert("RGB")
    return src.resize((W, H), Image.LANCZOS), (0.5, 0.5)


def punches_for(i):
    """резкие наезды +8% за 0.12 с на ключевых словах; ни один отрезок без изменения не длиннее 2.5 с"""
    d = durs[i]
    words = voices[i]["words"]
    keys = [k.lower() for k in SCENES[i]["keys"]]
    toks = tokens(SCENES[i]["text"])
    kt = [w["t0"] for (tok, _), w in zip(toks, words) if tok.lower() in keys and w["t0"] > 0.9]
    if i == 14: return []                                   # у сцены 15 свой наезд
    pts = sorted(kt)
    # заполняем пробелы > 2.5 с наездом на ближайшее к середине слово
    changed = True
    while changed:
        changed = False
        ev = [0.0] + pts + [d]
        for a, b in zip(ev, ev[1:]):
            if b - a > 2.5:
                mid = (a + b) / 2
                cand = [w["t0"] for w in words if a + 0.6 < w["t0"] < b - 0.6] or [mid]
                pts.append(min(cand, key=lambda t: abs(t - mid))); pts.sort(); changed = True
                break
    # не чаще раза в 0.8 с
    res = []
    for p in pts:
        if not res or p - res[-1] > 0.8: res.append(p)
    # убираем лишние наезды, если без них правило 2.5 с всё равно выполняется
    ok = lambda ps: all(b - a <= 2.5 for a, b in zip([0.0] + ps, ps + [d]))
    k = 0
    while k < len(res):
        trial = res[:k] + res[k + 1:]
        if ok(trial): res = trial
        else: k += 1
    return res


SCN = []
for i in range(17):
    img, anchor = prep_image(i)
    SCN.append({"img": img, "anchor": anchor, "punch": punches_for(i)})
    print("scene", i + 1, "dur %.2f" % durs[i], "punches", [round(p, 2) for p in SCN[-1]["punch"]], flush=True)

# сцена 15: резкий наезд на «ВЧЕРА» в момент слова
V15 = [w for w in voices[14]["words"] if w["w"].lower().startswith("вчера")][0]["t0"]
ANCHOR15 = (0.46, 0.20)   # надпись «ВЧЕРА» в кадре сцены 15


def zoom_at(i, t):
    d = durs[i]
    z = 1.0 + 0.10 * ease(t / d)
    # резкий наезд +8% за 0.12 с, затем плавный отход — наезды не копятся
    pk = 0.0
    for p in SCN[i]["punch"]:
        if t >= p:
            pk = ease((t - p) / 0.12) * (1 - 0.7 * ease((t - p - 0.12) / 1.6))
    z *= 1 + 0.08 * pk
    anchor = SCN[i]["anchor"]
    if i == 14:
        k = ease((t - (V15 - 0.05)) / 0.14)
        z *= 1 + 0.55 * k
        anchor = tuple(a + (b - a) * k for a, b in zip(anchor, ANCHOR15))
    return z, anchor


def render_bg(i, t):
    """медленный проезд камеры слева направо (с плавным стартом и остановкой), масштаб 1:1"""
    img = SCN[i]["img"]
    if img.size == (W, H):
        return img
    p0, p1 = SCN[i]["anchor"]
    c = p0 + (p1 - p0) * ease(t / durs[i])
    x = min(max(0.0, c * img.width - W / 2), img.width - W)
    return img.resize((W, H), Image.BILINEAR, box=(x, 0, x + W, H))


def draw_subs(frame, t):
    """«поп» 0.12 с: вся фраза растёт 0.7 → 1 вокруг центра блока (540, 1250), положение не меняется"""
    for t_on, t_off, ws in SUBS:
        if not (t_on <= t < t_off): continue
        k = min(1.0, (t - t_on) / 0.12)
        s = 0.7 + 0.3 * (1 - (1 - k) ** 3)
        for tw, spr, (cx, cy) in ws:
            if s < 0.999:
                spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.BICUBIC)
                cx, cy = SUB_CX + (cx - SUB_CX) * s, SUB_CY + (cy - SUB_CY) * s
            frame.alpha_composite(spr, (int(round(cx - spr.width / 2)), int(round(cy - spr.height / 2))))
    return frame


def rounded_card():
    """карточка СМС: тёмно-красный фон, белая скруглённая рамка, красная плашка «ВЧЕРА 03:00» (80 px),
    ниже белый текст (50 px). Возвращает слой 1080×1920 и центр слова «ВЧЕРА» для наезда."""
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cw, x0 = 900, (W - 900) // 2
    f80, f50 = font(80), font(50)
    body = ["Вирус распространён", "по всей стране.", "Оставайтесь дома."]
    bar_h, pad, lh = 130, 50, 68
    ch = pad + bar_h + 45 + lh * len(body) + pad
    y0 = (H - ch) // 2 - 80
    sh = Image.new("L", (W, H), 0)                                   # мягкая тень под карточкой
    ImageDraw.Draw(sh).rounded_rectangle([x0 + 10, y0 + 24, x0 + cw + 10, y0 + ch + 24], 56, fill=170)
    layer.putalpha(sh.filter(ImageFilter.GaussianBlur(28)))
    layer = Image.composite(Image.new("RGBA", (W, H), (0, 0, 0, 255)), Image.new("RGBA", (W, H), (0, 0, 0, 0)), layer.getchannel("A"))
    d = ImageDraw.Draw(layer)
    d.rounded_rectangle([x0, y0, x0 + cw, y0 + ch], 56, fill=(92, 8, 12, 255), outline=(255, 255, 255, 255), width=10)
    bx0, by0 = x0 + pad, y0 + pad
    d.rounded_rectangle([bx0, by0, x0 + cw - pad, by0 + bar_h], 22, fill=(228, 24, 28, 255))
    title = "ВЧЕРА 03:00"
    l, t, r, b = f80.getbbox(title)
    tx = (W - (r - l)) / 2 - l; ty = by0 + (bar_h - (b - t)) / 2 - t
    d.text((tx, ty), title, font=f80, fill=(255, 255, 255, 255))
    lw, _, rw, _ = f80.getbbox("ВЧЕРА")
    vchera = (tx + (lw + rw) / 2, by0 + bar_h / 2)
    y = by0 + bar_h + 45
    for line in body:
        l, t, r, b = f50.getbbox(line)
        d.text(((W - (r - l)) / 2 - l, y - t), line, font=f50, fill=(255, 255, 255, 255))
        y += lh
    return layer, vchera


SMS_CARD, SMS_VCHERA = rounded_card()
SMS_OVERLAY = False   # оригиналы без изменений: на картинке 15 СМС уже нарисована


def scene15(lt, bg):
    """карточка плавно появляется за 0.3 с, затем резкий наезд на «ВЧЕРА» (в момент слова, вместе с ударом).
    Фон под карточкой одновременно размывается и темнеет, чтобы карточка читалась."""
    a = ease(lt / 0.3)
    soft = bg.convert("RGB").resize((W // 6, H // 6), Image.BILINEAR).filter(ImageFilter.GaussianBlur(4)).resize((W, H), Image.BICUBIC)
    soft = Image.eval(soft, lambda v: int(v * 0.4)).convert("RGBA")
    bg = Image.blend(bg, soft, a)
    card = SMS_CARD.copy()
    card.putalpha(card.getchannel("A").point(lambda v: int(v * a)))
    fr = Image.alpha_composite(bg, card)
    k = ease((lt - max(0.35, V15 - 0.05)) / 0.14)
    z = 1 + 0.9 * k
    if z > 1.001:
        ax, ay = SMS_VCHERA
        x0, y0 = ax * (1 - 1 / z), ay * (1 - 1 / z)
        fr = fr.resize((W, H), Image.BICUBIC, box=(x0, y0, x0 + W / z, y0 + H / z))
    return fr


def frame_at(fi):
    t = fi / FPS
    i = int(np.searchsorted(starts, t, side="right") - 1)
    lt = t - starts[i]
    fr = render_bg(i, lt).convert("RGBA")
    if i == 14 and SMS_OVERLAY:
        fr = scene15(lt, fr)
    if i > 0 and lt < 0.1:                     # белый блик 0.1 с, 25%
        a = int(255 * 0.25 * (1 - lt / 0.1))
        fr = Image.alpha_composite(fr, Image.new("RGBA", (W, H), (255, 255, 255, a)))
    return draw_subs(fr, t).convert("RGB")


# ---------------- звук ----------------
def build_audio():
    n = int(TOTAL * SR) + SR
    voice = np.zeros(n, np.float32); fx = np.zeros(n, np.float32)
    for i in range(17):
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", os.path.join(V2, "voice", f"{i+1:02d}.wav"),
                              "-f", "f32le", "-ac", "1", "-ar", str(SR), "-"], capture_output=True, check=True).stdout
        sfx.place(voice, np.frombuffer(raw, np.float32), starts[i])
    act = np.abs(voice) > 0.02
    vr = float(np.sqrt(np.mean(voice[act] ** 2)))
    tgt = vr * 10 ** (-10 / 20)                # эффекты на −10 дБ под голосом

    def add(x, at, rel_db=0.0):
        a = np.abs(x) > np.abs(x).max() * 0.05
        r = float(np.sqrt(np.mean(x[a] ** 2))) + 1e-9
        sfx.place(fx, x * (tgt / r) * 10 ** (rel_db / 20), at)

    W_ = lambda i, word: starts[i] + [w for w in voices[i]["words"] if w["w"].lower().startswith(word)][0]["t0"]
    S, D = starts, durs
    REAL = os.path.join(V2, "sfx_real")

    def R(name, t0=0.0, t1=None, fi=0.03, fo=0.15, lp=None, rate=1.0):
        """кусок реальной записи (Freesound, CC0) с короткими фейдами"""
        x = sfx.load_from(os.path.join(REAL, name + ".wav"))
        x = x[int(t0 * SR): int(t1 * SR) if t1 else None]
        if rate != 1.0:
            x = np.interp(np.arange(0, len(x) - 1, rate), np.arange(len(x)), x).astype(np.float32)
        if lp: x = sfx.lp(x, lp)
        return sfx.fade(x, fi, fo)

    def bed(name, t0, d, at, rel, **kw):
        add(R(name, t0, t0 + d, fi=0.25, fo=0.4, **kw), at, rel)

    BED = -10                                   # фоны: итого −20 дБ под голосом; отдельные звуки: −10 дБ
    add(R("vibrate"), S[0] + 0.05, -2)
    add(R("vibrate"), S[0] + 1.25, -2)
    add(R("vibrate"), W_(0, "приходит") - 0.3, -2)
    bed("crowd_panic", 1.0, D[1], S[1], BED + 2)
    bed("helicopter", 4.0, D[1], S[1], BED + 1, lp=3000)
    bed("supermarket", 0.5, D[2] + D[3], S[2], BED + 3)
    add(sfx.shout_voice(), W_(3, "сзади") - 0.05, -4)
    add(sfx.terminal(), S[4] + 0.05)
    add(sfx.terminal(), W_(4, "цифры") - 0.1, -3)
    bed("traffic_horns", 122.0, D[5] + D[6], S[5], BED + 4)
    bed("hammer", 2.2, D[7], S[7], -3)
    add(R("knock", 0.2, 0.95, fi=0.005, fo=0.08), S[8] + 0.0, 2)
    bed("radio", 1.0, D[10], S[10], BED + 2, lp=5000)
    bed("monster_growl", 1.5, D[11], S[11], BED + 2, lp=4000)
    bed("breathing", 4.0, D[12], S[12], BED + 2, lp=5000)
    bed("tinnitus", 2.0, D[13] - 0.1, S[13], BED - 2)
    add(R("boom", 0, 4.0, fi=0.002, fo=1.0), S[14] + V15 - 0.02, 3)   # 15: тишина, затем удар на «вчера»
    for k, r in enumerate((1.0, 0.85, 1.1, 0.92)):
        add(R("metal_scrape", rate=r, lp=6000), S[15] + 0.1 + k * 1.5, -6)
    add(R("zombie_growl", 0.2, 2.7, lp=5000), W_(15, "давно") - 0.3, -4)
    bed("monster_growl", 9.0, D[15], S[15], BED + 1, lp=4000)
    add(R("boom", 0, 3.0, fi=0.002, fo=0.8), S[16], 0)               # 17: удар-акцент
    for i in range(1, 17):
        if i == 14: continue                                          # перед 15 — тишина
        add(R("whoosh", fi=0.005, fo=0.1), S[i] - 0.25, -5)
    mix = voice + fx
    mix = mix[: int(TOTAL * SR)]
    pre = os.path.join(V2, "mix_pre.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", pre],
                   input=mix.astype(np.float32).tobytes(), check=True)
    # громкость: два прохода loudnorm → −14 LUFS
    comp = os.path.join(V2, "mix_comp.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af",
                    "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=120:makeup=1,alimiter=limit=0.7:level=false", comp], check=True)
    pre = comp
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", pre, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:"
          "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}").format(**m)
    fin = os.path.join(V2, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af", af + ",aresample=48000", "-ac", "2", fin], check=True)
    return fin


if __name__ == "__main__":
    if "--frames" in sys.argv:                 # кадры из середины каждой сцены для проверки
        od = sys.argv[sys.argv.index("--frames") + 1]; os.makedirs(od, exist_ok=True)
        for i in range(17):
            frame_at(int((starts[i] + durs[i] / 2) * FPS)).save(os.path.join(od, f"mid_{i+1:02d}.png"))
        sys.exit()
    wav = build_audio(); print("audio ok", flush=True)
    ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                           "-r", str(FPS), "-i", "-", "-i", wav, "-map", "0:v", "-map", "1:a",
                           "-c:v", "libx264", "-preset", "medium", "-crf", "19", "-pix_fmt", "yuv420p", "-profile:v", "high",
                           "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest", "-movflags", "+faststart", OUT],
                          stdin=subprocess.PIPE)
    for fi in range(NF):
        ff.stdin.write(frame_at(fi).tobytes())
        if fi % 300 == 0: print("frame", fi, "/", NF, flush=True)
    ff.stdin.close(); ff.wait()
    print("done", OUT, "%.2f s" % TOTAL)
