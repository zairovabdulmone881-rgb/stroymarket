#!/usr/bin/env python3
"""Reels «У меня всё хорошо» — версия в формате «СВИДАНИЕ»
(чёрный фон, золотой лайн-арт со свечением, две карточки + счётчик между ними).

  python3 make_reel.py preview   # превью-кадры + cover.png
  python3 make_reel.py render    # финальный MP4
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 27.0
NFRAMES = int(DUR * FPS)
SR = 48000
SS = 2

FD = "/usr/share/fonts/opentype/inter/"


def _font_path(kind):
    names = {"x": "ExtraBold", "b": "Bold", "s": "SemiBold", "i": "SemiBoldItalic"}
    try:
        out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "Montserrat" in line and f"Montserrat-{names[kind]}." in line:
                return line.split(":")[0]
    except Exception:
        pass
    p = FD + f"Inter-{names[kind]}.otf"
    return p if os.path.exists(p) else "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


@lru_cache(None)
def font(size, kind="x"):
    return ImageFont.truetype(_font_path(kind), int(size))


def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


BG = hx("#050505")
GOLD = hx("#D9A441")
GOLD_L = hx("#EDCB82")
GOLD_D = hx("#8A6A2E")
CREAM = hx("#F6E6BE")
BUBBLE = hx("#FFF2D6")
INK = hx("#16110A")
RED = hx("#FF4A36")
WIN = hx("#F2B544")
HEART = hx("#F0503C")

# ---------- раскладка (как в референсе) ----------
CARD_A = (35, 125, 1045, 828)
CARD_B = (35, 975, 1045, 1672)
GROUND_A = 690
GROUND_B = 1535
TITLE_Y = 70
MID_LABEL_Y = 849
TIMER_Y = 918
WM_Y = 1735
CTA_Y = 1835


def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ramp(t, t0, d):
    return ease_out((t - t0) / d)


def appear(t, t0, dur=0.25):
    if t < t0:
        return None
    k = ease_out((t - t0) / dur)
    return 0.85 + 0.15 * k, k


def life(t, t0, t1, fin=0.25, fout=0.15):
    """(scale, alpha) для элемента, который появляется в t0 и исчезает в t1."""
    if t < t0 or t >= t1 + fout:
        return None
    k = ease_out((t - t0) / fin)
    out = 1 - clamp((t - t1) / fout) if t >= t1 else 1.0
    return 0.85 + 0.15 * k, k * out


def paste(canvas, spr, cx, cy, scale=1.0, alpha=1.0):
    if alpha <= 0.003:
        return
    if abs(scale - 1) > 1e-3:
        spr = spr.resize((max(1, round(spr.width * scale)), max(1, round(spr.height * scale))), Image.BICUBIC)
    if alpha < 0.997:
        spr = spr.copy()
        spr.putalpha(spr.getchannel("A").point(lambda v: int(v * alpha)))
    canvas.alpha_composite(spr, (int(round(cx - spr.width / 2)), int(round(cy - spr.height / 2))))


def spaced(d, cx, cy, s, f, sp, fill):
    ws = [f.getlength(c) for c in s]
    total = sum(ws) + sp * (len(s) - 1)
    x = cx - total / 2
    for c, w_ in zip(s, ws):
        d.text((x, cy), c, font=f, fill=fill, anchor="lm")
        x += w_ + sp


def wrap(text, f, maxw):
    lines, cur = [], ""
    for w_ in text.split(" "):
        tst = (cur + " " + w_).strip()
        if f.getlength(tst) <= maxw:
            cur = tst
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------- линии в стиле «полая трубка» ----------
def tube(d, pts, S, outer=CREAM, inner=(8, 7, 6), w_out=11, w_in=4):
    for wd, col in ((w_out, outer), (w_in, inner)):
        w = wd * S
        for a, b in zip(pts, pts[1:]):
            d.line([a, b], fill=col + (255,), width=int(w))
        for (x, y) in pts:
            r = w / 2
            d.ellipse([x - r, y - r, x + r, y + r], fill=col + (255,))


# ---------- человечек ----------
HEAD_R = 44


@lru_cache(None)
def person(who="son", mood="smile", arms="ear", breath=0, talk=False, phone_on=True):
    S = SS
    SW, SH, GY = 300, 470, 440
    im = Image.new("RGBA", (SW * S, SH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)

    def P(x, y):
        return ((SW / 2 + x) * S, (GY + y) * S)

    b = -breath
    hip = (0, -150)
    neck = (0, -268 + b)
    sh = (0, -252 + b)
    # ноги и тело
    tube(d, [P(-20, 0), P(-6, -75), P(*hip)], S)
    tube(d, [P(20, 0), P(8, -75), P(*hip)], S)
    tube(d, [P(*hip), P(*neck)], S)
    # руки
    left = [P(*sh), P(-30, -200 + b), P(-38, -140 + b / 2)]
    if arms == "ear":
        right = [P(*sh), P(52, -228 + b), P(44, -312 + b)]
    elif arms == "low":
        right = [P(*sh), P(34, -200 + b), P(46, -150 + b / 2)]
    else:
        right = [P(*sh), P(30, -200 + b), P(38, -140 + b / 2)]
    tube(d, left, S)
    tube(d, right, S)
    # голова
    hc = (0, -268 - 4 - HEAD_R + b)
    cx, cy = P(*hc)
    r = HEAD_R * S
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(6, 5, 4, 255), outline=CREAM + (255,), width=int(5 * S))
    gold = GOLD + (255,)
    if who == "son":
        # шапка волос + лучики
        d.chord([cx - r, cy - r, cx + r, cy + r], 195, 345, fill=gold)
        for ang in range(200, 345, 18):
            a = math.radians(ang)
            x1, y1 = cx + math.cos(a) * r * 0.95, cy + math.sin(a) * r * 0.95
            x2, y2 = cx + math.cos(a) * r * 1.42, cy + math.sin(a) * r * 1.42
            nx, ny = -math.sin(a) * 5 * S, math.cos(a) * 5 * S
            d.polygon([(x1 - nx, y1 - ny), (x2, y2), (x1 + nx, y1 + ny)], fill=gold)
    else:
        # мама: пучок + пряди
        bx, by = cx - 10 * S, cy - r - 14 * S
        br = 20 * S
        d.ellipse([bx - br, by - br, bx + br, by + br], fill=gold, outline=GOLD_L + (255,), width=int(3 * S))
        d.chord([cx - r, cy - r, cx + r, cy + r], 180, 360, fill=gold)
        d.chord([cx - r * 1.08, cy - r * 0.6, cx - r * 0.55, cy + r * 0.9], 90, 270, fill=gold)
        d.chord([cx + r * 0.55, cy - r * 0.6, cx + r * 1.08, cy + r * 0.9], 270, 90, fill=gold)
    # лицо
    fc = CREAM + (255,)
    ey = cy + 2 * S
    for sx in (-1, 1):
        ex = cx + sx * 15 * S
        er = 4.5 * S
        if mood in ("tired", "sad"):
            d.chord([ex - er * 1.4, ey - er * 1.2, ex + er * 1.4, ey + er * 1.6], 0, 180, fill=fc)
            d.line([ex - er * 1.8, ey - er * 0.3, ex + er * 1.8, ey - er * 0.3], fill=fc, width=int(3 * S))
        else:
            d.ellipse([ex - er, ey - er, ex + er, ey + er], fill=fc)
    my = cy + 20 * S
    if mood == "smile":
        if talk:
            d.chord([cx - 13 * S, my - 8 * S, cx + 13 * S, my + 12 * S], 0, 180, fill=fc)
        else:
            d.arc([cx - 17 * S, my - 16 * S, cx + 17 * S, my + 8 * S], 25, 155, fill=fc, width=int(4 * S))
    elif mood == "sad":
        d.arc([cx - 14 * S, my + 2 * S, cx + 14 * S, my + 20 * S], 205, 335, fill=fc, width=int(4 * S))
    else:
        if talk:
            d.ellipse([cx - 8 * S, my, cx + 8 * S, my + 10 * S], fill=fc)
        else:
            d.line([cx - 12 * S, my + 6 * S, cx + 12 * S, my + 6 * S], fill=fc, width=int(4 * S))
    # телефон
    if arms in ("ear", "low"):
        px, py = P(48, -326 + b) if arms == "ear" else P(52, -160 + b / 2)
        pw, ph = 22 * S, 44 * S
        fill = BUBBLE + (255,) if phone_on else (10, 9, 8, 255)
        d.rounded_rectangle([px - pw / 2, py - ph / 2, px + pw / 2, py + ph / 2], radius=6 * S, fill=fill,
                            outline=CREAM + (255,), width=int(3 * S))
    k = 0.9  # фигуры чуть компактнее, чтобы облачка не налезали на заголовки
    im = im.resize((int(SW * k), int(SH * k)), Image.LANCZOS)
    return im, GY * k


def breath(t, ph=0.0):
    return int(round(2 + 2 * math.sin(2 * math.pi * t / 2.0 + ph)))


def draw_person(canvas, x, gy, t, ph=0.0, **kw):
    spr, g = person(breath=breath(t, ph), **kw)
    canvas.alpha_composite(spr, (int(x - spr.width / 2), int(gy - g)))


# ---------- облачка ----------
@lru_cache(None)
def bubble(text, thought=False, tail=0.0):
    """Речь: кремовая «таблетка» с хвостиком вниз. Мысль: тёмная, золотой контур, курсив + кружочки."""
    S = SS
    f = font(40 * S, "i" if thought else "s")
    tw = f.getlength(text)
    padx, h = 32 * S, 74 * S
    bw = int(tw + 2 * padx)
    extra = 46 * S
    im = Image.new("RGBA", (bw + 8 * S, h + extra + 8 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x0, y0 = 4 * S, 4 * S
    tx = x0 + bw / 2 + tail * S
    if thought:
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + h], radius=h / 2, fill=(20, 15, 8, 245),
                            outline=GOLD + (255,), width=int(3 * S))
        for k, (dy, rr) in enumerate(((14, 9), (34, 6))):
            cx_, cy_ = tx - k * 10 * S, y0 + h + dy * S
            d.ellipse([cx_ - rr * S, cy_ - rr * S, cx_ + rr * S, cy_ + rr * S], fill=(20, 15, 8, 245),
                      outline=GOLD + (255,), width=int(3 * S))
        col = CREAM
    else:
        d.polygon([(tx - 14 * S, y0 + h - 4 * S), (tx + 14 * S, y0 + h - 4 * S), (tx, y0 + h + 18 * S)],
                  fill=GOLD + (255,))
        d.rounded_rectangle([x0, y0, x0 + bw, y0 + h], radius=h / 2, fill=BUBBLE + (255,),
                            outline=GOLD + (255,), width=int(3 * S))
        d.polygon([(tx - 11 * S, y0 + h - 6 * S), (tx + 11 * S, y0 + h - 6 * S), (tx, y0 + h + 12 * S)],
                  fill=BUBBLE + (255,))
        col = INK
    d.text((x0 + bw / 2, y0 + h / 2), text, font=f, fill=col + (255,), anchor="mm")
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    return im


def bubble_at(canvas, text, t, t0, t1, cx, bottom_y, thought=False, tail=0.0, typing=False):
    lf = life(t, t0, t1)
    if not lf:
        return
    shown = text
    if typing:
        n = int((t - t0 - 0.15) * 25)
        shown_n = clamp(n, 0, len(text))
        spr_full = bubble(text, thought, tail)
        # фиксированная ширина облачка, текст печатается машинкой
        spr = spr_full.copy()
        S = 1
        d = ImageDraw.Draw(spr)
        f = font(40, "i")
        h = 74
        x0, y0 = 2, 2
        bw = spr.width - 4
        # перекрываем текст фоном и печатаем часть
        d.rounded_rectangle([x0 + 20, y0 + 6, x0 + bw - 20, y0 + h - 6], radius=20, fill=(20, 15, 8, 255))
        part = text[:int(shown_n)]
        tw = f.getlength(text)
        tx0 = x0 + bw / 2 - tw / 2
        d.text((tx0, y0 + h / 2), part, font=f, fill=CREAM + (255,), anchor="lm")
        if t < t0 + 0.15 + len(text) / 25 + 0.8 and int(t * 3) % 2 == 0:
            cxp = tx0 + f.getlength(part) + 3
            d.rectangle([cxp, y0 + 20, cxp + 3, y0 + h - 20], fill=CREAM + (230,))
    else:
        spr = bubble(shown, thought, tail)
    sc, al = lf
    tip = (4 + 74 + (34 + 6 if thought else 18))  # низ хвостика/кружков в спрайте
    paste(canvas, spr, cx, bottom_y - tip + spr.height / 2, sc, al)


# ---------- предметы ----------
@lru_cache(None)
def icon(kind, caption=""):
    S = SS
    f = font(32 * S, "s")
    cw = f.getlength(caption) if caption else 0
    iw = 76 * S
    im = Image.new("RGBA", (int(iw + (22 * S + cw if caption else 0) + 10 * S), 90 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx, cy = 5 * S + iw / 2, 45 * S
    c = CREAM + (255,)
    g = GOLD + (255,)
    lw = int(5 * S)
    if kind == "bill":
        d.rounded_rectangle([cx - 26 * S, cy - 34 * S, cx + 26 * S, cy + 34 * S], radius=6 * S, outline=c, width=lw,
                            fill=(12, 10, 7, 255))
        for i, yy in enumerate((-16, -2, 12)):
            d.line([cx - 14 * S, cy + yy * S, cx + (14 if i < 2 else 0) * S, cy + yy * S], fill=g, width=int(4 * S))
        d.ellipse([cx + 8 * S, cy + 16 * S, cx + 30 * S, cy + 38 * S], fill=RED + (255,))
        d.text((cx + 19 * S, cy + 27 * S), "!", font=font(17 * S), fill=(255, 255, 255, 255), anchor="mm")
    elif kind == "mail":
        d.rounded_rectangle([cx - 34 * S, cy - 23 * S, cx + 34 * S, cy + 23 * S], radius=5 * S, outline=c, width=lw,
                            fill=(12, 10, 7, 255))
        d.line([cx - 30 * S, cy - 19 * S, cx, cy + 4 * S, cx + 30 * S, cy - 19 * S], fill=c, width=lw, joint="curve")
        d.ellipse([cx + 18 * S, cy - 38 * S, cx + 40 * S, cy - 16 * S], fill=RED + (255,))
    elif kind == "plate":
        d.ellipse([cx - 36 * S, cy - 17 * S, cx + 36 * S, cy + 23 * S], outline=c, width=lw, fill=(12, 10, 7, 255))
        d.ellipse([cx - 20 * S, cy - 6 * S, cx + 20 * S, cy + 12 * S], outline=g, width=int(3 * S))
    if caption:
        d.text((5 * S + iw + 22 * S, cy), caption, font=f, fill=CREAM + (255,), anchor="lm")
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


@lru_cache(None)
def tonometer():
    S = SS
    im = Image.new("RGBA", (170 * S, 120 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = CREAM + (255,)
    d.rounded_rectangle([6 * S, 20 * S, 120 * S, 112 * S], radius=12 * S, outline=c, width=int(5 * S), fill=(14, 11, 7, 255))
    d.rounded_rectangle([20 * S, 32 * S, 106 * S, 74 * S], radius=6 * S, fill=(30, 10, 8, 255))
    d.text((63 * S, 53 * S), "160/95", font=font(24 * S, "b"), fill=RED + (255,), anchor="mm")
    d.ellipse([52 * S, 82 * S, 74 * S, 104 * S], outline=GOLD + (255,), width=int(4 * S))
    # трубка манжеты
    d.arc([96 * S, 4 * S, 168 * S, 96 * S], 270, 80, fill=GOLD + (255,), width=int(5 * S))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


@lru_cache(None)
def pills():
    S = SS
    im = Image.new("RGBA", (110 * S, 120 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = CREAM + (255,)
    d.rounded_rectangle([14 * S, 6 * S, 64 * S, 30 * S], radius=5 * S, fill=GOLD + (255,))
    d.rounded_rectangle([8 * S, 28 * S, 70 * S, 114 * S], radius=10 * S, outline=c, width=int(5 * S), fill=(14, 11, 7, 255))
    d.rectangle([18 * S, 52 * S, 60 * S, 88 * S], fill=CREAM + (220,))
    d.line([24 * S, 63 * S, 54 * S, 63 * S], fill=INK + (255,), width=int(4 * S))
    d.line([24 * S, 76 * S, 46 * S, 76 * S], fill=INK + (255,), width=int(4 * S))
    d.ellipse([78 * S, 96 * S, 100 * S, 114 * S], fill=c)
    d.ellipse([84 * S, 78 * S, 104 * S, 94 * S], fill=CREAM + (190,))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


@lru_cache(None)
def mug():
    S = SS
    im = Image.new("RGBA", (90 * S, 80 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    c = CREAM + (255,)
    d.rounded_rectangle([8 * S, 14 * S, 56 * S, 74 * S], radius=8 * S, outline=c, width=int(5 * S), fill=(14, 11, 7, 255))
    d.arc([42 * S, 26 * S, 76 * S, 60 * S], 270, 90, fill=c, width=int(5 * S))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


# ---------- фоны карточек ----------
def _radial(cx, cy, r, strength, x0, y0, x1, y1):
    yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
    dd = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    return np.clip(1 - dd, 0, 1) ** 2 * strength


def window(d, box, rng, lit=0.45):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=12, fill=(8, 7, 5, 255), outline=GOLD + (255,), width=4)
    # городские огни в окне
    for _ in range(26):
        x = rng.uniform(x0 + 18, x1 - 22)
        y = rng.uniform(y0 + (y1 - y0) * 0.45, y1 - 18)
        if rng.random() < lit:
            d.rectangle([x, y, x + 6, y + 6], fill=WIN + (255,))
        else:
            d.rectangle([x, y, x + 6, y + 6], fill=(70, 52, 20, 255))


@lru_cache(None)
def background():
    rng = np.random.default_rng(3)
    a = np.zeros((H, W, 3), np.float32) + np.array(BG, np.float32)
    for (x0, y0, x1, y1), glow_c in ((CARD_A, (290, 470)), (CARD_B, (330, 1330))):
        k = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
        grad = np.array((24, 19, 10), np.float32) * (1 - k) + np.array((8, 7, 5), np.float32) * k
        a[y0:y1, x0:x1] = grad
        g = _radial(glow_c[0], glow_c[1], 520, 1.0, x0, y0, x1, y1)[..., None]
        a[y0:y1, x0:x1] += g * np.array((60, 44, 18), np.float32)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    # закругляем углы карточек
    mask = Image.new("L", (W, H), 0)
    md = ImageDraw.Draw(mask)
    for c in (CARD_A, CARD_B):
        md.rounded_rectangle(c, radius=46, fill=255)
    base = Image.new("RGBA", (W, H), BG + (255,))
    base.paste(img, (0, 0), mask)
    d = ImageDraw.Draw(base)
    # сетка в карточке мамы (кухонная плитка)
    x0, y0, x1, y1 = CARD_B
    for x in range(x0 + 50, x1, 48):
        d.line([x, y0 + 8, x, GROUND_B], fill=(30, 25, 15, 255), width=1)
    for y in range(y0 + 30, GROUND_B, 48):
        d.line([x0 + 8, y, x1 - 8, y], fill=(30, 25, 15, 255), width=1)
    # звёздная пыль в карточке сына
    x0, y0, x1, y1 = CARD_A
    for _ in range(70):
        x, y = rng.uniform(x0 + 20, x1 - 20), rng.uniform(y0 + 20, y1 - 20)
        r = rng.uniform(1, 2.4)
        v = int(rng.uniform(60, 130))
        d.ellipse([x - r, y - r, x + r, y + r], fill=(v, v, v, 255))
    # полы
    d.line([66, GROUND_A, 1014, GROUND_A], fill=GOLD_L + (255,), width=3)
    d.line([66, GROUND_B, 1014, GROUND_B], fill=GOLD_L + (255,), width=3)
    # окна
    window(d, (800, 205, 990, 330), rng)
    window(d, (800, 1055, 990, 1180), rng, 0.3)
    # стол на кухне
    d.rounded_rectangle([560, 1428, 990, 1442], radius=7, fill=CREAM + (255,))
    for lx in (600, 950):
        d.line([lx, 1440, lx, GROUND_B], fill=CREAM + (255,), width=8)
    # стол сына (табурет с тарелкой не нужен — иконки висят над полом)
    return base


def card_borders(canvas, a_col, b_col):
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle(CARD_A, radius=46, outline=a_col + (255,), width=3)
    d.rounded_rectangle(CARD_B, radius=46, outline=b_col + (255,), width=3)


def lerp_col(a, b, k):
    return tuple(int(a[i] + (b[i] - a[i]) * k) for i in range(3))


# ---------- тайминг ----------
CALL_END = 19.6
BANNER_T = 21.0
CTA_T = 22.2
RATE = 7.0  # секунд звонка за секунду ролика

SON = [  # (текст, t0, t1, мысль?)
    ("Да всё нормально, мам", 2.0, 5.4, False),
    ("Не переживай", 5.6, 7.6, False),
    ("Не хочу её грузить", 7.8, 16.6, True),
    ("Ладно, мам, целую", 16.8, CALL_END, False),
]
MOM = [
    ("Сынок, как ты?", 0.0, 9.6, False),
    ("У меня всё хорошо, сынок", 9.8, 13.6, False),
    ("Только бы он не волновался", 13.8, 17.6, True),
    ("Береги себя", 17.8, CALL_END, False),
]
SON_ICONS = [("bill", "Долг: 23 000", 4.4, 420), ("mail", "47 непрочитанных", 5.6, 515), ("plate", "пусто", 6.8, 610)]
MOM_ITEMS = [("tono", 11.4), ("pills", 12.4)]


def speaking(lines, t):
    for txt, t0, t1, th in lines:
        if t0 <= t < min(t1, t0 + 1.4) and not th:
            return True
    return False


def thinking(lines, t):
    return any(t0 <= t < t1 and th for _, t0, t1, th in lines)


def compose(t):
    img = background().copy()
    d = ImageDraw.Draw(img)
    on_call = t < CALL_END
    end_k = ramp(t, CALL_END, 0.3)

    # мерцание окон: случайные огоньки
    rng = np.random.default_rng(int(t * 2))
    for (x0, y0, x1, y1) in ((800, 205, 990, 330), (800, 1055, 990, 1180)):
        for _ in range(3):
            x, y = rng.uniform(x0 + 18, x1 - 22), rng.uniform(y0 + (y1 - y0) * 0.45, y1 - 18)
            d.rectangle([x, y, x + 6, y + 6], fill=WIN + (255,))

    # --- СЫН ---
    son_mood = "tired" if (thinking(SON, t) or 4.4 <= t < 5.6 and False) else "smile"
    if not on_call:
        son_mood = "sad"
    draw_person(img, 300, GROUND_A, t, mood=son_mood, arms="ear" if on_call else "low",
                talk=speaking(SON, t) and int(t * 7) % 2 == 0, phone_on=on_call, who="son")
    for kind, cap, t0, cy in SON_ICONS:
        a = appear(t, t0)
        if a:
            spr = icon(kind, cap)
            paste(img, spr, 560 + spr.width / 2, cy, *a)
    for txt, t0, t1, th in SON:
        bubble_at(img, txt, t, t0, t1, 330 if not th else 340, 338, thought=th, tail=-30, typing=th)

    # --- МАМА ---
    mom_mood = "tired" if thinking(MOM, t) else "smile"
    if not on_call:
        mom_mood = "sad"
    draw_person(img, 300, GROUND_B, t, ph=1.3, mood=mom_mood, arms="ear" if on_call else "low",
                talk=speaking(MOM, t) and int(t * 7) % 2 == 0, phone_on=on_call, who="mom")
    m = mug()
    img.alpha_composite(m, (860, 1428 - m.height + 4))
    for kind, t0 in MOM_ITEMS:
        a = appear(t, t0)
        if a:
            spr = tonometer() if kind == "tono" else pills()
            x = 690 if kind == "tono" else 800
            paste(img, spr, x, 1430 - spr.height / 2 + 2, *a)
    for txt, t0, t1, th in MOM:
        bubble_at(img, txt, t, t0, t1, 400 if not th else 420, 1172, thought=th, tail=-75, typing=th)

    # --- рамки, заголовки ---
    a_col = GOLD
    b_col = GOLD
    card_borders(img, a_col, b_col)
    spaced(d, W / 2, TITLE_Y, "У МЕНЯ ВСЁ ХОРОШО", font(32), 14, GOLD_L + (255,))
    spaced(d, W / 2, 163, "СЫН", font(46), 16, GOLD_L + (255,))
    spaced(d, W / 2, 1013, "МАМА", font(46), 16, GOLD_L + (255,))
    spaced(d, W / 2, WM_Y, "MISTER_MASKAAA", font(30, "s"), 18, GOLD_D + (255,))

    # --- счётчик звонка ---
    banner_k = ramp(t, BANNER_T, 0.25)
    if banner_k < 1:
        tc = min(t, CALL_END) * RATE
        txt = f"{int(tc) // 60:02d}:{int(tc) % 60:02d}"
        col = lerp_col(BUBBLE, RED, end_k)
        lab = "ЗВОНОК ЗАВЕРШЁН" if not on_call else "ИДЁТ ЗВОНОК"
        lay = Image.new("RGBA", (W, 180), (0, 0, 0, 0))
        ld = ImageDraw.Draw(lay)
        spaced(ld, W / 2, MID_LABEL_Y - 818, lab, font(28), 12, CREAM + (255,))
        ld.text((W / 2, TIMER_Y - 818), txt, font=font(108), fill=col + (255,), anchor="mm")
        # линии с точками: точки сходятся к таймеру, пока идёт звонок
        p = clamp(min(t, CALL_END) / CALL_END)
        lc = lerp_col(GOLD, RED, end_k)
        y = TIMER_Y + 6 - 818
        ld.line([60, y, 330, y], fill=lc + (255,), width=3)
        ld.line([750, y, 1020, y], fill=lc + (255,), width=3)
        for x in (85 + 220 * p, 995 - 220 * p):
            ld.ellipse([x - 9, y - 9, x + 9, y + 9], fill=lc + (255,))
        if not on_call and int(t * 2.5) % 2 == 1:  # мигание после завершения
            lay.putalpha(lay.getchannel("A").point(lambda v: int(v * 0.55)))
        lay.putalpha(lay.getchannel("A").point(lambda v: int(v * (1 - banner_k))))
        img.alpha_composite(lay, (0, 818))

    arr = np.asarray(img.convert("RGB"), np.float32)
    # затемнение карточек в финале
    if t >= BANNER_T:
        k = ramp(t, BANNER_T, 0.3)
        f_ = 1 - 0.55 * k
        arr[CARD_A[1] - 10:CARD_A[3] + 10] *= f_
        arr[CARD_B[1] - 10:CARD_B[3] + 10] *= f_
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")

    # плашка-панчлайн
    a = appear(t, BANNER_T)
    if a:
        paste(img, banner_sprite(), W / 2, 912, *a)
    a = appear(t, CTA_T)
    if a:
        paste(img, cta_sprite(), W / 2, CTA_Y, *a)
    return img


@lru_cache(None)
def heart(size):
    S = 4
    s = size * S
    im = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = s * 0.27
    d.ellipse([s * 0.05, s * 0.08, s * 0.05 + 2 * r, s * 0.08 + 2 * r], fill=HEART + (255,))
    d.ellipse([s * 0.95 - 2 * r, s * 0.08, s * 0.95, s * 0.08 + 2 * r], fill=HEART + (255,))
    d.polygon([(s * 0.07, s * 0.40), (s * 0.93, s * 0.40), (s * 0.5, s * 0.92)], fill=HEART + (255,))
    return im.resize((size, size), Image.LANCZOS)


@lru_cache(None)
def banner_sprite():
    S = SS
    bw, bh = 940, 140
    im = Image.new("RGBA", (bw * S, bh * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, bw * S - 1, bh * S - 1], radius=40 * S, fill=hx("#F4D894") + (255,))
    d.text((bw * S / 2, bh * S / 2), "Оба сказали: «всё хорошо»", font=font(56 * S), fill=INK + (255,), anchor="mm")
    return im.resize((bw, bh), Image.LANCZOS)


@lru_cache(None)
def cta_sprite():
    f = font(40, "b")
    txt = "Отправь тому, кто никогда не жалуется"
    tw = f.getlength(txt)
    hs = 40
    im = Image.new("RGBA", (int(tw + hs + 30), 70), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.text((5, 35), txt, font=f, fill=CREAM + (255,), anchor="lm")
    im.alpha_composite(heart(hs), (int(tw + 18), 35 - hs // 2 + 2))
    return im


def glow(arr):
    """Мягкое свечение ярких элементов (как в референсе)."""
    lum = arr.max(axis=2, keepdims=True)
    bright = arr * np.clip((lum - 165) / 90, 0, 1)
    small = Image.fromarray(np.clip(bright, 0, 255).astype(np.uint8)).resize((W // 4, H // 4), Image.BILINEAR)
    g1 = small.filter(ImageFilter.GaussianBlur(4))
    g2 = small.filter(ImageFilter.GaussianBlur(12))
    g = (np.asarray(g1.resize((W, H), Image.BILINEAR), np.float32) * 0.55
         + np.asarray(g2.resize((W, H), Image.BILINEAR), np.float32) * 0.45)
    return arr + 0.6 * g * np.array((1.0, 0.85, 0.55), np.float32)


def render_frame(i):
    t = i / FPS
    img = compose(t)
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr = glow(arr)
    return np.clip(arr, 0, 255).astype(np.uint8)


# ---------- звук ----------
def note(n):
    return 440 * 2 ** ((n - 69) / 12)


def bandnoise(n, f0, q, rng):
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    X *= np.exp(-0.5 * ((fr - f0) / (f0 / q)) ** 2)
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def fft_lowpass(x, fc):
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (fr / fc) ** 4)
    return np.fft.irfft(X, len(x))


def measure_lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    lines = [l for l in r.stderr.splitlines() if l.strip().startswith("I:")]
    return float(lines[-1].split()[1])


def write_wav(path, x):
    import wave
    x16 = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x16.tobytes())


def make_audio(path):
    N = int(DUR * SR)
    t = np.arange(N) / SR
    rng = np.random.default_rng(11)
    chords = [[45, 57, 60, 64, 69], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67]]
    clen = 3.375
    pad = np.zeros((N, 2))
    for ci in range(8):
        t0 = ci * clen
        s0, s1 = int(max(0, t0 - 0.3) * SR), int(min(DUR, t0 + clen + 1.6) * SR)
        tt = t[s0:s1] - t0
        env = np.clip((tt + 0.3) / 1.2, 0, 1) ** 2
        env = env * np.where(tt > clen, np.clip(1 - (tt - clen) / 1.6, 0, 1), 1.0)
        for n in chords[ci % 4]:
            for ch, det in ((0, -0.0018), (1, 0.0021)):
                ph = 2 * np.pi * note(n) * (1 + det) * tt * (1 + 0.002 * np.sin(2 * np.pi * 0.23 * tt + n))
                v = np.sin(ph) + 0.3 * np.sin(2 * ph + 0.3) + 0.12 * np.sin(3 * ph + 0.7)
                pad[s0:s1, ch] += v * env * (0.55 if n < 50 else 0.32)
    for ch in range(2):
        pad[:, ch] = fft_lowpass(pad[:, ch], 1400)
    # после завершения звонка пэд становится тише и темнее
    pad *= (0.9 + 0.1 * np.sin(2 * np.pi * t / 6.75))[:, None]
    pad /= np.abs(pad).max()

    sfx = np.zeros((N, 2))

    def add(sig, at, gain, pan=0.0):
        s = int(at * SR)
        e = min(N, s + len(sig))
        if e <= s:
            return
        L, R = math.cos((pan + 1) * math.pi / 4), math.sin((pan + 1) * math.pi / 4)
        sfx[s:e, 0] += sig[:e - s] * gain * L * 1.41
        sfx[s:e, 1] += sig[:e - s] * gain * R * 1.41

    def tone(f, dur, att=0.005, dec=None):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        env = np.clip(tt / att, 0, 1) * np.clip((dur - tt) / 0.01, 0, 1)
        if dec:
            env *= np.exp(-tt * dec)
        return np.sin(2 * np.pi * f * tt) * env

    def pop(f0=880, dur=0.18):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        ph = 2 * np.pi * np.cumsum(f0 * (1 + 0.6 * np.exp(-tt * 40))) / SR
        return np.sin(ph) * np.exp(-tt * 28) * np.clip(tt / 0.003, 0, 1)

    def click():
        n = int(0.025 * SR)
        return bandnoise(n, 3200, 2.0, rng) * np.exp(-np.arange(n) / SR * 260)

    def chime(f0, dur=2.2):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        s = sum(g * np.sin(2 * np.pi * f0 * m * tt) * np.exp(-tt * (2.2 + k))
                for k, (m, g) in enumerate(((1, 1), (2.01, 0.35), (3.0, 0.15))))
        return s * np.clip(tt / 0.004, 0, 1)

    # соединение звонка: два коротких сигнала
    add(tone(880, 0.09) + 0.4 * tone(1320, 0.09), 0.05, 0.08)
    add(tone(1175, 0.12) + 0.4 * tone(1760, 0.12), 0.2, 0.08)
    # реплики — мягкие «попы», мысли — машинка
    for lines, pan in ((SON, -0.25), (MOM, 0.25)):
        for txt, t0, t1, th in lines:
            if th:
                for i, c in enumerate(txt):
                    if c != " ":
                        add(click(), t0 + 0.15 + i / 25, 0.05 * (0.8 + 0.4 * rng.random()), pan)
            elif t0 > 0.1:
                add(pop(760 if pan < 0 else 620), t0, 0.11, pan)
    for _, _, t0, _ in SON_ICONS:
        add(pop(520), t0, 0.09, -0.3)
    for _, t0 in MOM_ITEMS:
        add(pop(480), t0, 0.09, 0.3)
    # конец звонка: короткие гудки 425 Гц
    for k in range(4):
        add(tone(425, 0.32), CALL_END + 0.1 + k * 0.6, 0.10)
    add(chime(note(69)), BANNER_T, 0.07, -0.2)
    add(chime(note(76)), CTA_T, 0.05, 0.2)

    write_wav(path + ".pad.wav", pad * 0.5)
    lufs = measure_lufs(path + ".pad.wav")
    pad *= 0.5 * 10 ** ((-24.0 - lufs) / 20)
    # после конца звонка пэд чуть проседает
    duck = 1 - 0.35 * np.clip((t - CALL_END) / 0.5, 0, 1) * np.clip((BANNER_T - t) / 0.6 + 1, 0, 1)
    pad *= duck[:, None]
    mix = pad + sfx
    mix *= (np.clip((DUR - t) / 0.5, 0, 1) ** 2 * np.clip(t / 0.02, 0, 1))[:, None]
    pk = np.abs(mix).max()
    if pk > 0.89:
        mix *= 0.89 / pk
    write_wav(path, mix)
    os.remove(path + ".pad.wav")
    print(f"pad −24 LUFS; mix {measure_lufs(path):.1f} LUFS, peak {20 * np.log10(np.abs(mix).max()):.1f} dBFS")


# ---------- main ----------
PREVIEW_T = (1, 5, 12, 21, 26)
COVER_T = 2.6


def preview():
    pdir = os.path.join(OUT, "preview")
    os.makedirs(pdir, exist_ok=True)
    for s in PREVIEW_T:
        tt = s + (0.4 if s == 21 else 0)
        Image.fromarray(render_frame(int(round(tt * FPS)))).save(os.path.join(pdir, f"frame_{s:02d}s.png"))
    Image.fromarray(render_frame(int(COVER_T * FPS))).save(os.path.join(OUT, "cover.png"))
    print("preview ok")


def render():
    wav = os.path.join(OUT, "audio.wav")
    make_audio(wav)
    mp4 = os.path.join(OUT, "u_menya_vsyo_horosho.mp4")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-t", f"{DUR}", "-movflags", "+faststart", mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for fr in pool.imap(render_frame, range(NFRAMES), chunksize=4):
            p.stdin.write(fr.tobytes())
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("done:", mp4)


if __name__ == "__main__":
    print("font:", _font_path("x"))
    {"preview": preview, "render": render}[sys.argv[1] if len(sys.argv) > 1 else "preview"]()
