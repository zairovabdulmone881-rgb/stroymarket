#!/usr/bin/env python3
"""Сборка final_video_3.mp4 «Зомби-апокалипсис начался, пока ты в метро»: 1080x1920, 30 fps, H.264 + AAC.
Основано на video2/build.py (final_video_2_final.mp4). Картинка на весь экран, поверх — только субтитры.
Без музыки: голос + звуковые эффекты (Freesound CC0, см. sfx_real/CREDITS.txt).
Движение: медленный наезд 1.00 → 1.10 за сцену + резкие наезды на ключевых словах (пауза без наезда ≤ 2.5 с),
на склейках белый блик 0.1 с и «вуш».
Запуск: python3 video3/tts.py --force && python3 video3/build.py [--frames DIR]"""
import json, os, re, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from script import SCENES
import sfx

ROOT = os.path.dirname(HERE)
W, H, FPS, SR = 1080, 1920, 30, 48000
FONT = os.path.join(ROOT, "fonts", "Montserrat_900Black.ttf")
FS, STROKE = 92, 12
SUB_CX, SUB_CY = 540, 1250
SUB_MAXW = 760          # центр 540 и пустые правые 160 px → блок не шире 2·(920−540)
YELLOW, RED, WHITE = (255, 210, 26), (255, 43, 28), (255, 255, 255)
GAP, LAST_TAIL, PRE15 = 0.3, 1.5, 0.8
IMG_DIR = "imgs3"
OUT = os.path.join(ROOT, sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "final_video_3.mp4")
N = len(SCENES)


def ease(x):
    x = min(1.0, max(0.0, x)); return x * x * (3 - 2 * x)


# ---------------- тайминг ----------------
voices = [json.load(open(os.path.join(HERE, "voice", f"{n:02d}.json"))) for n in range(1, N + 1)]
durs = []
for i, v in enumerate(voices):
    d = v["dur"] + GAP
    if i == 13: d = v["dur"] + PRE15          # 0.8 с тишины перед сценой 15
    if i == N - 1: d += LAST_TAIL
    durs.append(d)
starts = np.concatenate([[0], np.cumsum(durs)[:-1]])
TOTAL = float(sum(durs))
NF = int(round(TOTAL * FPS))


def word_t(i, prefix):
    return [w for w in voices[i]["words"] if w["w"].lower().strip("«»").startswith(prefix)][0]["t0"]


# ---------------- слова → фразы субтитров ----------------
def tokens(text):
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
    items = [{"w": tok.upper(), "t0": w["t0"], "t1": w["t1"], "brk": brk, "key": tok.lower() in keys}
             for (tok, brk), w in zip(toks, words)]
    groups, cur = [], []
    for k, it in enumerate(items):
        cur.append(it)
        nxt = items[k + 1] if k + 1 < len(items) else None
        if it["brk"] or len(cur) == 3 or nxt is None or nxt["t0"] - it["t1"] > 0.3:
            groups.append(cur); cur = []
    for k in range(len(groups) - 1):                      # короткий предлог в конце блока — к следующему слову
        g = groups[k]
        if len(g) > 1 and len(g[-1]["w"]) <= 2 and not g[-1]["brk"] and len(groups[k + 1]) < 3:
            groups[k + 1].insert(0, g.pop())
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
    sh = Image.new("L", im.size, 0)
    ImageDraw.Draw(sh).text((pad - l, pad - t), text, font=f, fill=255, stroke_width=STROKE + 4)
    sh = sh.filter(ImageFilter.GaussianBlur(9)).point(lambda v: int(v * 0.75))
    im.putalpha(sh)
    ImageDraw.Draw(im).text((pad - l, pad - t), text, font=f, fill=color, stroke_width=STROKE, stroke_fill=(0, 0, 0))
    return im


GAP_K, LINE_K = 0.18, 1.12
def text_w(spr):
    return spr.width - 36


def layout(group, accent, sz=FS):
    """слова целиком (без переносов), центр (540, 1250), ≤ 2 строк, строка ≤ SUB_MAXW"""
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
    res, stack = [], list(groups)
    while stack:
        g = stack.pop(0)
        lay = layout(g, accent)
        if lay is None:
            if len(g) > 1:                                   # сначала делим фразу (не оставляя предлог в конце)
                m = (len(g) + 1) // 2
                if len(g[m - 1]["w"]) <= 2 and m > 1 and layout(g[m - 1:], accent) is not None:
                    m -= 1
                stack = [g[:m], g[m:]] + stack
                continue
            for sz in range(FS - 2, 40, -2):                 # одно слово шире строки — уменьшаем шрифт
                lay = layout(g, accent, sz)
                if lay is not None: break
        res.append((g, lay))
    return res


SUBS, LAYOUT_LOG = [], []
for i in range(N):
    accent = RED if SCENES[i]["red"] else YELLOW
    gs = fit_groups(chunks_for(i), accent)
    for gi, (g, lay) in enumerate(gs):
        t_on = starts[i] + g[0]["t0"]
        if gi + 1 < len(gs):
            t_off = starts[i] + min(gs[gi + 1][0][0]["t0"], g[-1]["t1"] + 0.6)
        else:
            t_off = starts[i] + min(durs[i], g[-1]["t1"] + (LAST_TAIL if i == N - 1 else 0.6))
        SUBS.append((t_on, t_off, lay))
        LAYOUT_LOG.append((i + 1, " ".join(it["w"] for it in g), lay))


# ---------------- картинки и движение ----------------
BASE = 1.25          # запас разрешения под наезды
def prep_image(i):
    src = Image.open(os.path.join(ROOT, IMG_DIR, f"{i + 1:02d}.png")).convert("RGB")
    assert abs(src.width / src.height - 9 / 16) < 0.01, src.size
    return src.resize((int(W * BASE), int(H * BASE)), Image.LANCZOS)


def punches_for(i):
    """резкие наезды на ключевых словах; ни один отрезок без наезда/склейки не длиннее 2.5 с"""
    d, words = durs[i], voices[i]["words"]
    keys = [k.lower() for k in SCENES[i]["keys"]]
    toks = tokens(SCENES[i]["text"])
    kp = sorted(w["t0"] for (tok, _), w in zip(toks, words) if tok.lower() in keys and w["t0"] > 0.7)
    pts = []
    for p in kp:                                          # не чаще раза в 0.8 с
        if not pts or p - pts[-1] > 0.8: pts.append(p)
    changed = True
    while changed:                                        # заполняем паузы > 2.5 с
        changed = False
        ev = [0.0] + pts + [d]
        for a, b in zip(ev, ev[1:]):
            if b - a > 2.5:
                mid = (a + b) / 2
                cand = [w["t0"] for w in words if a + 0.8 < w["t0"] < b - 0.8] or [mid]
                pts.append(min(cand, key=lambda t: abs(t - mid))); pts.sort(); changed = True
                break
    res = pts
    ok = lambda ps: all(b - a <= 2.5 for a, b in zip([0.0] + ps, ps + [d]))
    assert ok(res), (i, res, d)
    return res


T16 = word_t(15, "поворачива")        # сцена 16: резкий наезд + удар на «поворачиваются»
SCN = []
for i in range(N):
    p = punches_for(i)
    if i == 15:
        p = sorted([x for x in p if abs(x - T16) > 0.8] + [T16])
    SCN.append({"img": prep_image(i), "punch": p})
    print("scene", i + 1, "dur %.2f" % durs[i], "punches", [round(x, 2) for x in p], flush=True)


def zoom_at(i, t):
    z = 1.0 + 0.10 * ease(t / durs[i])                     # медленный наезд 1.00 → 1.10
    pk, amp = 0.0, 0.08
    for p in SCN[i]["punch"]:
        if t >= p:
            pk = ease((t - p) / 0.12) * (1 - 0.7 * ease((t - p - 0.12) / 1.6))
            amp = 0.16 if (i == 15 and abs(p - T16) < 1e-6) else 0.08
    return z * (1 + amp * pk)


def render_bg(i, t):
    img = SCN[i]["img"]
    z = zoom_at(i, t)
    bw, bh = img.width / z, img.height / z
    x0, y0 = (img.width - bw) / 2, (img.height - bh) / 2
    return img.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + bw, y0 + bh))


def draw_subs(frame, t):
    for t_on, t_off, lay in SUBS:
        if not (t_on <= t < t_off): continue
        k = min(1.0, (t - t_on) / 0.12)
        s = 0.7 + 0.3 * (1 - (1 - k) ** 3)
        for _, spr, (cx, cy) in lay:
            if s < 0.999:
                spr = spr.resize((max(1, int(spr.width * s)), max(1, int(spr.height * s))), Image.BICUBIC)
                cx, cy = SUB_CX + (cx - SUB_CX) * s, SUB_CY + (cy - SUB_CY) * s
            frame.alpha_composite(spr, (int(round(cx - spr.width / 2)), int(round(cy - spr.height / 2))))
    return frame


def frame_at(fi):
    t = fi / FPS
    i = int(np.searchsorted(starts, t, side="right") - 1)
    lt = t - starts[i]
    fr = render_bg(i, lt).convert("RGBA")
    if i > 0 and lt < 0.1:                                 # белый блик 0.1 с на склейке
        a = int(255 * 0.25 * (1 - lt / 0.1))
        fr = Image.alpha_composite(fr, Image.new("RGBA", (W, H), (255, 255, 255, a)))
    return draw_subs(fr, t).convert("RGB")


# ---------------- звук ----------------
def build_audio():
    n = int(TOTAL * SR) + SR
    voice = np.zeros(n, np.float32); fx = np.zeros(n, np.float32)
    for i in range(N):
        sfx.place(voice, sfx.load_from(os.path.join(HERE, "voice", f"{i+1:02d}.wav")), starts[i])
    act = np.abs(voice) > 0.02
    tgt = float(np.sqrt(np.mean(voice[act] ** 2))) * 10 ** (-10 / 20)   # эффекты на −10 дБ под голосом

    def add(x, at, rel_db=0.0):
        a = np.abs(x) > np.abs(x).max() * 0.05
        r = float(np.sqrt(np.mean(x[a] ** 2))) + 1e-9
        sfx.place(fx, x * (tgt / r) * 10 ** (rel_db / 20), at)

    S, D = starts, durs
    Wd = lambda i, w: S[i] + word_t(i, w)
    VE = lambda i: S[i] + voices[i]["dur"]                  # конец голоса сцены

    def R(name, t0=0.0, t1=None, fi=0.03, fo=0.15, lp=None, hp=None, rate=1.0):
        x = sfx.load_from(os.path.join(HERE, "sfx_real", name + ".wav"))
        x = x[int(t0 * SR): int(t1 * SR) if t1 else None]
        if rate != 1.0:
            x = np.interp(np.arange(0, len(x) - 1, rate), np.arange(len(x)), x).astype(np.float32)
        if lp: x = sfx.lp(x, lp)
        if hp: x = sfx.hp(x, hp)
        return sfx.fade(x, fi, fo)

    def bed(name, t0, d, at, rel=-10, **kw):              # фон: −20 дБ под голосом
        add(R(name, t0, t0 + d, fi=0.25, fo=0.4, **kw), at, rel)

    # 01 — скрежет тормозов, щелчок света
    add(R("brakes", 96.0, 96.0 + Wd(0, "гаснет") - S[0] + 0.3, fi=0.05, fo=0.35, hp=300), S[0], 0)
    add(R("light_off", fi=0.002, fo=0.05), Wd(0, "гаснет") - 0.05, 0)
    # 03 — гул вагона, кашель
    bed("train_hum", 140.0, D[2], S[2])
    add(R("cough1", 0.0, 1.2, fi=0.005, fo=0.2, lp=6000), Wd(2, "кашляет") + 0.55, -4)
    # 04 — кашель (сильнее), затем тишина
    bed("train_hum", 140.0 + D[2], Wd(3, "замолкает") - S[3], S[3], -12)
    add(R("cough2", 1.9, 3.4, fi=0.005, fo=0.2, lp=6000), S[3] + 0.05, -6)
    add(R("cough1", 0.0, 2.4, fi=0.005, fo=0.3, lp=6000), Wd(3, "сильнее") - 0.2, -2)
    # 05 — писк приборов
    for k, dt in enumerate((0.15, 0.9, 1.35, 2.6, 3.2, 4.4)):
        if S[4] + dt < VE(4):
            add(R("beep", fi=0.003, fo=0.03, lp=5000, rate=(1.0, 1.12, 1.0, 0.9, 1.12, 1.0)[k]), S[4] + dt, -6)
    # 06 — крик
    add(R("scream", 0.0, 2.2, fi=0.01, fo=0.4), Wd(5, "раздаётся"), -1)
    # 07 — рычание
    add(R("zombie_growl", 0.2, 3.0, lp=5000), Wd(6, "встаёт"), -2)
    bed("monster_growl", 1.5, D[6], S[6], -10, lp=4000)
    # 08 — лязг дверей, прыжок
    add(R("train_door", 0.6, 2.6, fi=0.01, fo=0.3), Wd(7, "ручку") - 0.1, 0)
    add(R("jump_gravel", fi=0.005, fo=0.3), Wd(7, "прыгаешь") + 0.35, 0)
    # 09 — треск электричества
    bed("elec_arc", 1.0, D[8], S[8], -10, lp=7000)
    add(R("elec_crackle", fi=0.005, fo=0.2), Wd(8, "напряжением"), -3)
    add(R("elec_crackle", fi=0.005, fo=0.2, rate=0.85), Wd(8, "конец") - 0.05, -1)
    # 11 — шаги, капли, мигание фонаря
    bed("steps_tunnel", 0.5, D[10], S[10], -8)
    bed("drips", 66.0, D[10], S[10], -10)
    for k, dt in enumerate((0.0, 0.18, 0.5)):
        add(R("flash_click", fi=0.002, fo=0.05), Wd(10, "фонарик") + 0.2 + dt, -5 - 2 * k)
    add(R("flicker", 0.0, 1.6, fi=0.01, fo=0.3, lp=6000), Wd(10, "садится"), -6)
    # 12 — топот множества ног, рычание
    bed("many_run", 3.0, D[11] + 0.3, S[11], -6)
    add(R("horde", 0.0, 3.5, fo=0.6, lp=5000), Wd(11, "много") - 0.3, -3)
    # 13 — эхо станции
    bed("station", 20.0, D[12] + 0.3, S[12], -8)
    # 14 — гул ламп, затем тишина (0.8 с перед сценой 15)
    bed("lamp_hum", 2.0, VE(13) - S[13], S[13], -10)
    # 15 — почти тишина: еле слышный гул ламп
    bed("lamp_hum", 12.0, D[14], S[14], -20)
    # 16 — шорох, рычание, удар на «поворачиваются»
    add(R("rustle", fi=0.01, fo=0.3), Wd(15, "шепчет"), -6)
    add(R("rustle", fi=0.01, fo=0.3, rate=0.9), Wd(15, "поворачива") - 0.6, -4)
    add(R("zombie_growl", 0.2, 3.0, lp=5000), Wd(15, "поворачива") + 0.15, -2)
    add(R("boom", 0, 4.0, fi=0.002, fo=1.0), Wd(15, "поворачива") - 0.02, 3)
    # 17 — удар-акцент
    add(R("boom", 0, 3.0, fi=0.002, fo=0.8), S[16], 0)
    # склейки: «вуш» (перед сценой 15 — тишина)
    for i in range(1, N):
        if i == 14: continue
        add(R("whoosh", fi=0.005, fo=0.1), S[i] - 0.25, -5)

    mix = (voice + fx)[: int(TOTAL * SR)]
    pre = os.path.join(HERE, "mix_pre.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", pre],
                   input=mix.astype(np.float32).tobytes(), check=True)
    comp = os.path.join(HERE, "mix_comp.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", pre, "-af",
                    "acompressor=threshold=-18dB:ratio=2.5:attack=5:release=120:makeup=1,alimiter=limit=0.7:level=false", comp], check=True)
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", comp, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True).stderr
    m = json.loads(r[r.rindex("{"):r.rindex("}") + 1])
    af = ("loudnorm=I=-14:TP=-1.5:LRA=11:linear=true:measured_I={input_i}:measured_TP={input_tp}:"
          "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}").format(**m)
    fin = os.path.join(HERE, "mix.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", comp, "-af", af + ",aresample=48000", "-ac", "2", fin], check=True)
    return fin


if __name__ == "__main__":
    for sc, txt, lay in LAYOUT_LOG:
        xs = [(c[0] - text_w(s) / 2, c[0] + text_w(s) / 2) for _, s, c in lay]
        print("sub", sc, txt, "| x %d..%d" % (min(a for a, b in xs), max(b for a, b in xs)), "lines", len({round(c[1]) for _, _, c in lay}))
    if "--frames" in sys.argv:
        od = sys.argv[sys.argv.index("--frames") + 1]; os.makedirs(od, exist_ok=True)
        for i in range(N):
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
