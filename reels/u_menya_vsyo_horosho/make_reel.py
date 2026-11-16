#!/usr/bin/env python3
"""Reels «У меня всё хорошо» — всё рисуется кодом (Pillow + numpy + ffmpeg).

Запуск:
  python3 make_reel.py preview   # превью-кадры 1, 5, 12, 21, 26 с + cover.png
  python3 make_reel.py render    # финальный MP4
"""
import math
import os
import subprocess
import sys
from functools import lru_cache
from multiprocessing import Pool

import numpy as np
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.dirname(os.path.abspath(__file__))
W, H, FPS = 1080, 1920, 30
DUR = 27.0
NFRAMES = int(DUR * FPS)
SR = 48000

# ---------- шрифты ----------
FONT_DIR = "/usr/share/fonts/opentype/inter/"


def find_font():
    try:
        out = subprocess.run(["fc-list"], capture_output=True, text=True).stdout
        for line in out.splitlines():
            if "Montserrat" in line and "ExtraBold" in line:
                return line.split(":")[0]
    except Exception:
        pass
    if os.path.exists(FONT_DIR + "Inter-ExtraBold.otf"):
        return FONT_DIR + "Inter-ExtraBold.otf"
    return "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


BOLD = find_font()
ITALIC = FONT_DIR + "Inter-SemiBoldItalic.otf"
if not os.path.exists(ITALIC):
    ITALIC = BOLD


@lru_cache(None)
def font(size, italic=False):
    return ImageFont.truetype(ITALIC if italic else BOLD, size)


# ---------- палитра ----------
def hx(c):
    c = c.lstrip("#")
    return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))


BG = hx("#0E0F13")
WHITE = hx("#F2F2F2")
TOP_GRAD = hx("#2A1F14")
BOT_GRAD = hx("#0F1A2E")
ACC_WARM = hx("#FFB547")
ACC_COLD = hx("#4DA3FF")
LABEL = hx("#9AA0AA")
YELLOW = hx("#FFD23F")
THOUGHT = hx("#CFE3FF")
INK = hx("#111111")
GREEN = hx("#34C759")

# ---------- раскладка ----------
TOP_Y0, TOP_Y1 = 280, 920
STRIP_Y0, STRIP_Y1 = 920, 1000
BOT_Y0, BOT_Y1 = 1000, 1640
MARGIN = 80
SAFE_TOP, SAFE_BOT = 250, 1570


# ---------- easing ----------
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def appear(t, t0, dur=0.25):
    """(scale, alpha) для появления элемента: 0.85→1, 0→1, ease-out."""
    if t < t0:
        return None
    k = ease_out((t - t0) / dur)
    return 0.85 + 0.15 * k, k


def ramp(t, t0, dur):
    return ease_out((t - t0) / dur) if dur > 0 else float(t >= t0)


# ---------- примитивы ----------
SS = 2  # суперсэмплинг спрайтов


def seg(d, p1, p2, w, fill):
    d.line([p1, p2], fill=fill, width=w)
    r = w / 2
    for (x, y) in (p1, p2):
        d.ellipse([x - r, y - r, x + r, y + r], fill=fill)


def poly(d, pts, w, fill):
    for a, b in zip(pts, pts[1:]):
        seg(d, a, b, w, fill)


def paste_sprite(canvas, sprite, cx, cy, scale=1.0, alpha=1.0):
    """Кладёт RGBA-спрайт центром в (cx, cy) с масштабом и прозрачностью."""
    if alpha <= 0.001:
        return
    if abs(scale - 1) > 1e-3:
        sw = max(1, int(round(sprite.width * scale)))
        sh = max(1, int(round(sprite.height * scale)))
        sprite = sprite.resize((sw, sh), Image.BICUBIC)
    if alpha < 0.999:
        a = sprite.getchannel("A").point(lambda v: int(v * alpha))
        sprite = sprite.copy()
        sprite.putalpha(a)
    x = int(round(cx - sprite.width / 2))
    y = int(round(cy - sprite.height / 2))
    canvas.alpha_composite(sprite, (x, y)) if x >= 0 and y >= 0 else canvas.paste(sprite, (x, y), sprite)


def text_w(s, f):
    return f.getlength(s)


def wrap(text, f, maxw):
    words, lines, cur = text.split(" "), [], ""
    for w_ in words:
        tst = (cur + " " + w_).strip()
        if text_w(tst, f) <= maxw:
            cur = tst
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


# ---------- человечек ----------
HEAD_D = 140
LW = 10


@lru_cache(None)
def stickman_sprite(mood="smile", arms="down", bun=False, breath=0, talk=False):
    """Спрайт человечка. Якорь: центр спрайта по X, ноги на y = GROUND."""
    S = SS
    SW, SH = 520, 620
    GROUND = 560
    im = Image.new("RGBA", (SW * S, SH * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    cx = SW / 2

    def P(x, y):  # локальные координаты (0,0)=ноги-центр
        return ((cx + x) * S, (GROUND + y) * S)

    w = LW * S
    col = WHITE + (255,)
    b = -breath  # вверх
    hip = P(0, -120)
    neck = P(0, -255 + b)
    seg(d, P(-42, 0), hip, w, col)
    seg(d, P(42, 0), hip, w, col)
    seg(d, hip, neck, w, col)
    sh = (0, -235 + b)
    # руки
    if arms == "down":
        poly(d, [P(*sh), P(-38, -170 + b), P(-52, -108 + b * 0.5)], w, col)
        poly(d, [P(*sh), P(38, -170 + b), P(52, -108 + b * 0.5)], w, col)
    elif arms == "ear":  # правая рука держит телефон у уха
        poly(d, [P(*sh), P(-38, -170 + b), P(-52, -108 + b * 0.5)], w, col)
        poly(d, [P(*sh), P(92, -205 + b), P(86, -300 + b)], w, col)
    elif arms == "chest":  # обе руки держат телефон у груди
        poly(d, [P(*sh), P(-45, -175 + b), P(-12, -165 + b)], w, col)
        poly(d, [P(*sh), P(45, -175 + b), P(12, -165 + b)], w, col)
    elif arms == "front":  # правая рука вытянута к большому телефону
        poly(d, [P(*sh), P(-38, -170 + b), P(-52, -108 + b * 0.5)], w, col)
        poly(d, [P(*sh), P(95, -215 + b), P(175, -250 + b)], w, col)
    elif arms == "table":  # руки на столе справа
        poly(d, [P(*sh), P(-38, -170 + b), P(-52, -108 + b * 0.5)], w, col)
        poly(d, [P(*sh), P(70, -175 + b), P(140, -150)], w, col)
    # голова
    hc = (0, -255 - 8 - HEAD_D / 2 + b)
    r = HEAD_D / 2
    hx_, hy_ = P(*hc)
    rr = r * S
    d.ellipse([hx_ - rr, hy_ - rr, hx_ + rr, hy_ + rr], outline=col, width=w, fill=BG + (255,))
    if bun:
        bx, by = P(hc[0], hc[1] - r - 22)
        br = 30 * S
        d.ellipse([bx - br, by - br, bx + br, by + br], outline=col, width=w, fill=BG + (255,))
        # перевязь пучка
        seg(d, P(hc[0] - 18, hc[1] - r + 2), P(hc[0] + 18, hc[1] - r + 2), w, col)
        # чёлка
        d.arc([hx_ - rr * 0.78, hy_ - rr * 0.95, hx_ + rr * 0.15, hy_ - rr * 0.05],
              start=180, end=290, fill=col, width=int(w * 0.7))
    # лицо
    ex, ey = 26, hc[1] - 8
    er = 8 * S
    for sx in (-1, 1):
        x0, y0 = P(hc[0] + sx * ex, ey)
        if mood == "tired":
            # полуприкрытые глаза: нижняя половина + веко
            d.chord([x0 - er * 1.2, y0 - er * 1.2, x0 + er * 1.2, y0 + er * 1.2], 0, 180, fill=col)
            seg(d, (x0 - er * 1.6, y0 - 1 * S), (x0 + er * 1.6, y0 - 1 * S), int(4 * S), col)
        else:
            d.ellipse([x0 - er, y0 - er, x0 + er, y0 + er], fill=col)
    mx, my = P(hc[0], hc[1] + 28)
    if mood == "smile":
        if talk:
            d.chord([mx - 24 * S, my - 16 * S, mx + 24 * S, my + 20 * S], 0, 180, fill=col)
        else:
            d.arc([mx - 30 * S, my - 26 * S, mx + 30 * S, my + 10 * S], 25, 155, fill=col, width=int(7 * S))
    elif mood == "sad":
        d.arc([mx - 26 * S, my - 2 * S, mx + 26 * S, my + 30 * S], 205, 335, fill=col, width=int(7 * S))
    elif mood == "tired":
        seg(d, (mx - 22 * S, my + 4 * S), (mx + 22 * S, my + 4 * S), int(7 * S), col)
    # маленький телефон у уха
    if arms == "ear":
        px, py = P(80, -318 + b)
        pw, ph = 30 * S, 64 * S
        d.rounded_rectangle([px - pw / 2, py - ph / 2, px + pw / 2, py + ph / 2], radius=8 * S,
                            fill=(40, 40, 46, 255), outline=col, width=int(5 * S))
    if arms == "chest":
        px, py = P(0, -168 + b)
        pw, ph = 56 * S, 92 * S
        d.rounded_rectangle([px - pw / 2, py - ph / 2, px + pw / 2, py + ph / 2], radius=10 * S,
                            fill=(30, 34, 44, 255), outline=col, width=int(5 * S))
        d.rounded_rectangle([px - pw / 2 + 9 * S, py - ph / 2 + 10 * S, px + pw / 2 - 9 * S, py + ph / 2 - 10 * S],
                            radius=4 * S, fill=ACC_COLD + (255,))
    im = im.resize((SW, SH), Image.LANCZOS)
    return im, GROUND


def breath_px(t, phase=0.0):
    # ±2 px (размах 4 px), период 2 с
    return int(round(2 + 2 * math.sin(2 * math.pi * (t / 2.0) + phase)))


def draw_stickman(canvas, x, ground_y, t, phase=0.0, **kw):
    spr, gy = stickman_sprite(breath=breath_px(t, phase), **kw)
    canvas.alpha_composite(spr, (int(x - spr.width / 2), int(ground_y - gy)))


# ---------- облачко ----------
@lru_cache(None)
def bubble_sprite(text, maxw=520, tail="left"):
    S = SS
    f = font(46 * S)
    lines = wrap(text, f, maxw * S)
    lh = int(58 * S)
    tw = max(text_w(l, f) for l in lines)
    padx, pady = 34 * S, 26 * S
    bw = int(tw + 2 * padx)
    bh = int(lh * len(lines) + 2 * pady - 6 * S)
    tail_w = 34 * S
    im = Image.new("RGBA", (bw + 2 * tail_w, bh + 2 * tail_w), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    ox, oy = tail_w, tail_w
    d.rounded_rectangle([ox, oy, ox + bw, oy + bh], radius=28 * S, fill=(255, 255, 255, 255))
    ty = oy + bh * 0.62
    if tail == "left":
        d.polygon([(ox + 6 * S, ty - 24 * S), (ox - tail_w + 4 * S, ty + 22 * S), (ox + 14 * S, ty + 18 * S)],
                  fill=(255, 255, 255, 255))
    for i, l in enumerate(lines):
        d.text((ox + padx, oy + pady + i * lh - 4 * S), l, font=f, fill=INK)
    im = im.resize((im.width // S, im.height // S), Image.LANCZOS)
    return im


# ---------- текст с выделением ----------
def draw_rich_lines(canvas, lines, size, cy, line_h=None, shadow=True):
    """lines: [[(text,color),...], ...]; центрировано по X, блок по центру cy."""
    f = font(size)
    line_h = line_h or int(size * 1.18)
    total = line_h * len(lines)
    y = cy - total / 2
    d = ImageDraw.Draw(canvas)
    for segs in lines:
        lw_ = sum(text_w(s, f) for s, _ in segs)
        x = W / 2 - lw_ / 2
        for s, c in segs:
            if shadow:
                d.text((x + 3, y + 4), s, font=f, fill=(0, 0, 0, 150))
            d.text((x, y), s, font=f, fill=c + (255,))
            x += text_w(s, f)
        y += line_h
    return y


@lru_cache(None)
def rich_sprite(lines_key, size, line_h=None):
    lines = [list(l) for l in lines_key]
    f = font(size)
    line_h = line_h or int(size * 1.18)
    wmax = max(sum(text_w(s, f) for s, _ in l) for l in lines)
    im = Image.new("RGBA", (int(wmax) + 40, line_h * len(lines) + 40), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    y = 20
    for segs in lines:
        lw_ = sum(text_w(s, f) for s, _ in segs)
        x = im.width / 2 - lw_ / 2
        for s, c in segs:
            d.text((x + 3, y + 4), s, font=f, fill=(0, 0, 0, 160))
            d.text((x, y), s, font=f, fill=c + (255,))
            x += text_w(s, f)
        y += line_h
    return im


HOOK1 = ((("Мама спрашивает:", WHITE),), (("КАК ТЫ?", YELLOW),))
HOOK2 = ((("А она говорит", WHITE),), (("ТО ЖЕ САМОЕ", YELLOW),))
HOOK_CY = 392


# ---------- мысли (машинка) ----------
CPS = 25


def draw_thought(canvas, text, t, t0, x, y, maxw=W - 2 * MARGIN):
    if t < t0:
        return
    f = font(44, italic=True)
    lines = wrap(text, f, maxw)
    n = int((t - t0) * CPS)
    total = len(text)
    d = ImageDraw.Draw(canvas)
    lh = 56
    shown = 0
    cur_pos = (x, y)
    for i, l in enumerate(lines):
        take = clamp(n - shown, 0, len(l))
        part = l[:int(take)]
        if part:
            d.text((x, y + i * lh), part, font=f, fill=THOUGHT + (255,))
        if take > 0 or i == 0:
            cur_pos = (x + text_w(part, f) + 4, y + i * lh)
        shown += len(l) + 1
    # курсор мигает во время печати и 1,2 с после
    done_t = t0 + total / CPS
    if t < done_t + 1.2 and (t < done_t or int(t * 3) % 2 == 0):
        cx, cy = cur_pos
        d.rectangle([cx, cy + 8, cx + 4, cy + 50], fill=THOUGHT + (220,))


# ---------- иконки ----------
@lru_cache(None)
def icon_sprite(kind, caption):
    S = SS
    f = font(38 * S)
    cw = int(text_w(caption, f)) if caption else 0
    iw = 96 * S
    Wd = iw + (24 * S + cw if caption else 0) + 20 * S
    Ht = 110 * S
    im = Image.new("RGBA", (Wd, Ht), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = WHITE + (255,)
    acc = ACC_COLD + (255,)
    lw = 6 * S
    cx, cy = 10 * S + iw / 2, Ht / 2
    if kind == "bill":
        d.rounded_rectangle([cx - 34 * S, cy - 44 * S, cx + 34 * S, cy + 44 * S], radius=8 * S, outline=col, width=lw)
        for i, yy in enumerate((-22, -4, 14)):
            d.line([cx - 20 * S, cy + yy * S, cx + (20 if i < 2 else 2) * S, cy + yy * S], fill=col, width=int(5 * S))
        d.ellipse([cx + 8 * S, cy + 22 * S, cx + 30 * S, cy + 44 * S], fill=hx("#FF5A5A") + (255,))
        d.text((cx + 19 * S, cy + 33 * S), "!", font=font(18 * S), fill=(255, 255, 255, 255), anchor="mm")
    elif kind == "mail":
        d.rounded_rectangle([cx - 44 * S, cy - 30 * S, cx + 44 * S, cy + 30 * S], radius=6 * S, outline=col, width=lw)
        d.line([cx - 40 * S, cy - 26 * S, cx, cy + 6 * S, cx + 40 * S, cy - 26 * S], fill=col, width=lw, joint="curve")
        d.ellipse([cx + 22 * S, cy - 48 * S, cx + 50 * S, cy - 20 * S], fill=acc)
    elif kind == "plate":
        d.ellipse([cx - 46 * S, cy - 22 * S, cx + 46 * S, cy + 30 * S], outline=col, width=lw)
        d.ellipse([cx - 26 * S, cy - 8 * S, cx + 26 * S, cy + 16 * S], outline=(242, 242, 242, 120), width=int(4 * S))
    if caption:
        d.text((10 * S + iw + 24 * S, cy), caption, font=f, fill=col, anchor="lm")
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


@lru_cache(None)
def pills_sprite():
    S = SS
    im = Image.new("RGBA", (120 * S, 150 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = WHITE + (255,)
    d.rounded_rectangle([20 * S, 10 * S, 76 * S, 38 * S], radius=6 * S, fill=ACC_COLD + (255,))
    d.rounded_rectangle([14 * S, 38 * S, 82 * S, 140 * S], radius=10 * S, outline=col, width=6 * S, fill=(20, 28, 44, 255))
    d.rectangle([24 * S, 66 * S, 72 * S, 104 * S], fill=(242, 242, 242, 200))
    d.line([30 * S, 78 * S, 66 * S, 78 * S], fill=(30, 30, 30, 255), width=4 * S)
    d.line([30 * S, 92 * S, 56 * S, 92 * S], fill=(30, 30, 30, 255), width=4 * S)
    # таблетки рядом
    d.ellipse([88 * S, 120 * S, 112 * S, 140 * S], fill=col)
    d.ellipse([92 * S, 100 * S, 114 * S, 118 * S], fill=(242, 242, 242, 200))
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


@lru_cache(None)
def mug_sprite():
    S = SS
    im = Image.new("RGBA", (110 * S, 100 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    col = WHITE + (255,)
    d.rounded_rectangle([10 * S, 20 * S, 70 * S, 92 * S], radius=10 * S, outline=col, width=6 * S)
    d.arc([54 * S, 34 * S, 94 * S, 74 * S], 270, 90, fill=col, width=6 * S)
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


# ---------- большой телефон (сцена 1) ----------
@lru_cache(None)
def big_phone_sprite():
    S = SS
    pw, ph = 250, 470
    im = Image.new("RGBA", ((pw + 40) * S, (ph + 40) * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    o = 20 * S
    d.rounded_rectangle([o, o, o + pw * S, o + ph * S], radius=38 * S, fill=(26, 27, 32, 255),
                        outline=WHITE + (255,), width=8 * S)
    d.rounded_rectangle([o + 16 * S, o + 16 * S, o + (pw - 16) * S, o + (ph - 16) * S], radius=26 * S,
                        fill=(22, 30, 40, 255))
    cx = o + pw * S / 2
    # аватар
    d.ellipse([cx - 44 * S, o + 70 * S, cx + 44 * S, o + 158 * S], fill=(60, 70, 86, 255))
    d.ellipse([cx - 16 * S, o + 86 * S, cx + 16 * S, o + 118 * S], fill=(200, 210, 225, 255))
    d.chord([cx - 32 * S, o + 120 * S, cx + 32 * S, o + 176 * S], 180, 360, fill=(200, 210, 225, 255))
    d.text((cx, o + 205 * S), "Мама", font=font(50 * S), fill=(255, 255, 255, 255), anchor="mm")
    d.text((cx, o + 250 * S), "входящий вызов", font=font(20 * S), fill=(170, 180, 195, 255), anchor="mm")
    # кнопки
    gy = o + 380 * S
    d.ellipse([cx + 22 * S, gy - 36 * S, cx + 94 * S, gy + 36 * S], fill=GREEN + (255,))
    d.ellipse([cx - 94 * S, gy - 36 * S, cx - 22 * S, gy + 36 * S], fill=(255, 69, 58, 255))
    # трубки
    for bx, rot in ((cx + 58 * S, 0), (cx - 58 * S, 1)):
        if rot == 0:
            d.arc([bx - 18 * S, gy - 18 * S, bx + 18 * S, gy + 18 * S], 110, 340, fill=(255, 255, 255, 255), width=7 * S)
        else:
            d.line([bx - 18 * S, gy, bx + 18 * S, gy], fill=(255, 255, 255, 255), width=9 * S)
    return im.resize((im.width // S, im.height // S), Image.LANCZOS)


# ---------- фоны ----------
def radial(cx, cy, r, col, strength):
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    dd = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2) / r
    m = np.clip(1 - dd, 0, 1) ** 2 * strength
    return m[..., None] * np.array(col, np.float32)[None, None, :]


def vgrad(y0, y1, c0, c1):
    k = np.linspace(0, 1, y1 - y0, dtype=np.float32)[:, None, None]
    return (np.array(c0, np.float32) * (1 - k) + np.array(c1, np.float32) * k) * np.ones((1, W, 1), np.float32)


@lru_cache(None)
def vignette():
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    nx, ny = (xx - W / 2) / (W / 2), (yy - H / 2) / (H / 2)
    dd = np.sqrt(nx ** 2 * 1.0 + ny ** 2 * 0.9)
    v = 1 - 0.38 * np.clip((dd - 0.55) / 0.85, 0, 1) ** 1.6
    return v[..., None].astype(np.float32)


@lru_cache(None)
def bg_full():
    a = np.ones((H, W, 3), np.float32) * np.array(BG, np.float32)
    a += radial(W / 2, 1050, 760, ACC_WARM, 0.07)
    return Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")


@lru_cache(None)
def bg_split():
    a = np.ones((H, W, 3), np.float32) * np.array(BG, np.float32)
    a[TOP_Y0:TOP_Y1] = vgrad(TOP_Y0, TOP_Y1, TOP_GRAD, BG)
    a[BOT_Y0:BOT_Y1] = vgrad(BOT_Y0, BOT_Y1, BOT_GRAD, BG)
    # тёплый свет лампы сверху, холодный «лунный» свет снизу
    warm = radial(800, 330, 520, ACC_WARM, 0.16)
    cold = radial(860, 1080, 560, ACC_COLD, 0.10)
    a[TOP_Y0:TOP_Y1] += warm[TOP_Y0:TOP_Y1]
    a[BOT_Y0:BOT_Y1] += cold[BOT_Y0:BOT_Y1]
    a[STRIP_Y0:STRIP_Y1] = np.array((18, 19, 24), np.float32)
    img = Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # тонкие линии-разделители
    d.line([0, STRIP_Y0, W, STRIP_Y0], fill=(40, 42, 50, 255), width=2)
    d.line([0, STRIP_Y1 - 1, W, STRIP_Y1 - 1], fill=(40, 42, 50, 255), width=2)
    # лампа в верхней панели
    lx = 800
    d.line([lx, TOP_Y0, lx, TOP_Y0 + 40], fill=(90, 80, 66, 255), width=4)
    d.polygon([(lx - 50, TOP_Y0 + 90), (lx + 50, TOP_Y0 + 90), (lx + 24, TOP_Y0 + 40), (lx - 24, TOP_Y0 + 40)],
              fill=ACC_WARM + (255,))
    # окно в нижней панели
    wx0, wy0 = 760, BOT_Y0 + 40
    return img


def spaced_text(d, x, y, s, f, spacing, fill, anchor_right=False):
    widths = [text_w(c, f) for c in s]
    total = sum(widths) + spacing * (len(s) - 1)
    if anchor_right:
        x = x - total
    for c, wd in zip(s, widths):
        d.text((x, y), c, font=f, fill=fill, anchor="lm")
        x += wd + spacing
    return total


def draw_labels(canvas):
    d = ImageDraw.Draw(canvas)
    f = font(40)
    cy = (STRIP_Y0 + STRIP_Y1) / 2
    # ▲ СНАРУЖИ (слева), ВНУТРИ ▼ (справа)
    x = MARGIN
    d.polygon([(x, cy + 10), (x + 22, cy + 10), (x + 11, cy - 10)], fill=ACC_WARM + (255,))
    spaced_text(d, x + 38, cy, "СНАРУЖИ", f, 8, LABEL + (255,))
    xr = W - MARGIN
    d.polygon([(xr, cy - 10), (xr - 22, cy - 10), (xr - 11, cy + 10)], fill=ACC_COLD + (255,))
    spaced_text(d, xr - 38, cy, "ВНУТРИ", f, 8, LABEL + (255,), anchor_right=True)


def draw_watermark(canvas):
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    d.text((1000, 1530), "@mister_maskaaa", font=font(30), fill=(255, 255, 255, int(255 * 0.6)), anchor="rm")
    canvas.alpha_composite(layer)


def dim_region(arr, y0, y1, factor):
    if factor < 0.999:
        arr[y0:y1] *= factor


# ---------- сцены ----------
VIB_PULSES = [(0.0, 0.38), (0.55, 0.93), (1.10, 1.48), (1.65, 2.0)]


def vib_on(t):
    return any(a <= t < b for a, b in VIB_PULSES)


def scene1(t):
    img = bg_full().copy()
    ground = 1440
    draw_stickman(img, 380, ground, t, mood="smile", arms="front")
    # телефон дрожит ±6 px во время импульсов
    dx = dy = 0
    if vib_on(t):
        fr = int(round(t * FPS))
        seq = [(-6, 2), (6, -3), (-4, -6), (5, 4), (-6, -2), (3, 6)]
        dx, dy = seq[fr % len(seq)]
    ph = big_phone_sprite()
    paste_sprite(img, ph, 690 + dx, 1100 + dy)
    if vib_on(t):
        d = ImageDraw.Draw(img)
        for side in (-1, 1):
            x = 690 + side * 160 + dx
            for k in range(2):
                off = side * k * 22
                d.arc([x + off - 20, 1040 + dy, x + off + 20, 1160 + dy], 300 if side > 0 else 120,
                      60 if side > 0 else 240, fill=(255, 255, 255, 140), width=5)
    spr = rich_sprite(HOOK1, 76)
    paste_sprite(img, spr, W / 2, HOOK_CY)
    arr = np.asarray(img.convert("RGB"), np.float32)
    arr *= vignette()
    return arr


SON_BUBBLE = "Да всё нормально, мам, не переживай"
MOM_BUBBLE = "У меня всё хорошо, сынок"
SON_THOUGHT = "У неё и так давление. Не хочу её грузить."
MOM_THOUGHT = "Только бы он не волновался"

TOP_GROUND = 900
BOT_GROUND = 1600
FIG_X = 230
TOP_FIG_X = 190
THOUGHT_Y = BOT_Y0 + 34


def talking(t, t0, t1):
    return t0 <= t < t1 and int(t * 7) % 2 == 0


def draw_top_son(img, t):
    draw_stickman(img, TOP_FIG_X, TOP_GROUND, t, mood="smile", arms="ear", talk=talking(t, 2.35, 4.8))
    a = appear(t, 2.3)
    if a:
        spr = bubble_sprite(SON_BUBBLE, 480)
        paste_sprite(img, spr, 355 + spr.width / 2, 640, *a)


def draw_bot_son(img, t, active):
    draw_stickman(img, FIG_X, BOT_GROUND, t, phase=1.3, mood="tired", arms="chest")
    if not active:
        return
    items = [("bill", "Долг: 23 000", 8.4, 1195), ("mail", "47 непрочитанных", 10.0, 1315),
             ("plate", "пусто", 11.6, 1435)]
    for kind, cap, t0, cy in items:
        a = appear(t, t0)
        if a:
            spr = icon_sprite(kind, cap)
            paste_sprite(img, spr, 470 + spr.width / 2, cy, *a)
    draw_thought(img, SON_THOUGHT, t, 13.0, MARGIN, THOUGHT_Y)


def draw_top_mom(img, t):
    draw_stickman(img, TOP_FIG_X, TOP_GROUND, t, mood="smile", arms="ear", bun=True, talk=talking(t, 18.45, 20.2))
    a = appear(t, 18.4)
    if a:
        spr = bubble_sprite(MOM_BUBBLE, 480)
        paste_sprite(img, spr, 355 + spr.width / 2, 640, *a)


def draw_bot_mom(img, t):
    d = ImageDraw.Draw(img)
    # кухонный стол
    ty = 1470
    d.rounded_rectangle([330, ty, 720, ty + 14], radius=7, fill=WHITE + (255,))
    d.line([380, ty + 10, 380, 1600], fill=WHITE + (255,), width=10)
    d.line([670, ty + 10, 670, 1600], fill=WHITE + (255,), width=10)
    draw_stickman(img, FIG_X, BOT_GROUND, t, phase=1.3, mood="tired", arms="table", bun=True)
    m = mug_sprite()
    img.alpha_composite(m, (580, ty - m.height + 6))
    p = pills_sprite()
    img.alpha_composite(p, (440, ty - p.height + 8))
    draw_thought(img, MOM_THOUGHT, t, 19.2, MARGIN, THOUGHT_Y)


def scene_split(t, which):
    img = bg_split().copy()
    if which == "son":
        draw_top_son(img, t)
        draw_bot_son(img, t, active=t >= 8.0)
    else:
        draw_top_mom(img, t)
        draw_bot_mom(img, t)
    draw_labels(img)

    # затемнение панелей
    if which == "son":
        if t < 8.0:
            top_f, bot_f = 1.0, 0.3
        else:
            k = ramp(t, 8.0, 0.25)
            top_f, bot_f = 1 - 0.7 * k, 0.3 + 0.7 * k
    else:
        top_f = bot_f = 1.0
    final_k = ramp(t, 24.0, 0.25) if which == "mom" else 0.0
    if which == "mom" and t >= 21.0:
        # подложка под хук-оверлей
        k = ramp(t, 21.0, 0.25) * (1 - ramp(t, 24.0, 0.2))
        if k > 0:
            layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
            ld = ImageDraw.Draw(layer)
            for i in range(60):
                yy0 = 262 + i * 4
                edge = min(i, 59 - i) / 12
                al = int(235 * k * clamp(edge))
                ld.rectangle([0, yy0, W, yy0 + 4], fill=(10, 11, 14, al))
            img.alpha_composite(layer)
            a = appear(t, 21.0)
            spr = rich_sprite(HOOK2, 76)
            sc, al = a
            paste_sprite(img, spr, W / 2, HOOK_CY, sc, al * (1 - ramp(t, 24.0, 0.2)))

    arr = np.asarray(img.convert("RGB"), np.float32)
    dim_region(arr, TOP_Y0, TOP_Y1, top_f)
    dim_region(arr, BOT_Y0, BOT_Y1, bot_f)
    arr *= vignette()
    if final_k > 0:
        arr *= (1 - 0.75 * final_k)
        # мягкая тёмная подложка под призыв, чтобы ничего не просвечивало
        yy = np.arange(H, dtype=np.float32)
        band = np.clip((1 - np.abs(yy - 940) / 250) * 2.2, 0, 1)
        arr *= (1 - 0.88 * final_k * band)[:, None, None]
        img2 = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
        a = appear(t, 24.15)
        if a:
            spr = rich_sprite(((("Отправь тому, кто тоже", WHITE),), (("никогда не жалуется", WHITE),)), 64)
            paste_sprite(img2, spr, W / 2, 850, *a)
        a = appear(t, 24.6)
        if a:
            spr = rich_sprite(((("Завтра: что внутри у друга,", LABEL),), (("который всегда шутит →", LABEL),)), 38)
            paste_sprite(img2, spr, W / 2, 1030, *a)
        arr = np.asarray(img2.convert("RGB"), np.float32)
    return arr


def scene_at(t):
    if t < 2.0:
        return scene1(t)
    if t < 18.0:
        return scene_split(t, "son")
    return scene_split(t, "mom")


def render_frame(i):
    t = i / FPS
    arr = None
    for tb in (2.0, 18.0):
        if abs(t - tb) < 0.1:  # быстрый fade 0,2 с
            k = (t - (tb - 0.1)) / 0.2
            a_prev = scene_at(min(t, tb - 0.0334))
            a_next = scene_at(max(t, tb))
            arr = a_prev * (1 - k) + a_next * k
    if arr is None:
        arr = scene_at(t)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).convert("RGBA")
    draw_watermark(img)
    return np.asarray(img.convert("RGB"), np.uint8)


# ---------- звук ----------
def bandnoise(n, f0, q, rng):
    """Шум в полосе вокруг f0 через FFT-фильтр."""
    x = rng.standard_normal(n)
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(n, 1 / SR)
    bw = f0 / q
    X *= np.exp(-0.5 * ((fr - f0) / bw) ** 2)
    y = np.fft.irfft(X, n)
    return y / (np.abs(y).max() + 1e-9)


def fft_lowpass(x, fc):
    X = np.fft.rfft(x)
    fr = np.fft.rfftfreq(len(x), 1 / SR)
    X *= 1 / (1 + (fr / fc) ** 4)
    return np.fft.irfft(X, len(x))


def note(n):  # MIDI → Гц
    return 440 * 2 ** ((n - 69) / 12)


def make_audio(path):
    N = int(DUR * SR)
    t = np.arange(N) / SR
    rng = np.random.default_rng(7)
    # аккорды Am–F–C–G
    chords = [[45, 57, 60, 64, 69], [41, 53, 57, 60, 65], [48, 55, 60, 64, 67], [43, 55, 59, 62, 67]]
    clen = 3.375
    pad = np.zeros((N, 2))
    for ci in range(8):
        t0 = ci * clen
        s0 = int(max(0, t0 - 0.3) * SR)
        s1 = int(min(DUR, t0 + clen + 1.6) * SR)
        tt = t[s0:s1] - t0
        env = np.clip((tt + 0.3) / 1.2, 0, 1) ** 2  # мягкая атака
        rel = np.clip(1 - (tt - clen) / 1.6, 0, 1)
        env = env * np.where(tt > clen, rel, 1.0)
        for n in chords[ci % 4]:
            f = note(n)
            for ch, det in ((0, -0.0018), (1, 0.0021)):
                ff = f * (1 + det)
                vib = 0.002 * np.sin(2 * np.pi * 0.23 * tt + n)
                ph = 2 * np.pi * ff * tt * (1 + vib)
                v = np.sin(ph) + 0.30 * np.sin(2 * ph + 0.3) + 0.12 * np.sin(3 * ph + 0.7)
                amp = 0.55 if n < 50 else 0.32
                pad[s0:s1, ch] += v * env * amp
    for ch in range(2):
        pad[:, ch] = fft_lowpass(pad[:, ch], 1400)
    # медленное «дыхание» громкости
    pad *= (0.9 + 0.1 * np.sin(2 * np.pi * t / 6.75))[:, None]
    pad /= np.abs(pad).max()

    sfx = np.zeros((N, 2))

    def add(sig, at, gain, pan=0.0):
        s = int(at * SR)
        e = min(N, s + len(sig))
        L = math.cos((pan + 1) * math.pi / 4)
        R = math.sin((pan + 1) * math.pi / 4)
        sfx[s:e, 0] += sig[:e - s] * gain * L * 1.41
        sfx[s:e, 1] += sig[:e - s] * gain * R * 1.41

    # вибрация телефона: импульсы шума 150 Гц + гул
    for a, b in VIB_PULSES:
        n = int((b - a) * SR)
        tt = np.arange(n) / SR
        buzz = 0.6 * bandnoise(n, 150, 2.5, rng) + 0.5 * np.sign(np.sin(2 * np.pi * 150 * tt)) * 0.5 \
            + 0.4 * np.sin(2 * np.pi * 150 * tt)
        buzz = fft_lowpass(buzz, 900)
        env = np.clip(tt / 0.01, 0, 1) * np.clip((b - a - tt) / 0.02, 0, 1)
        env *= 0.8 + 0.2 * np.sin(2 * np.pi * 30 * tt)
        add(buzz * env, a, 0.32, 0.15)

    def pop(f0=880, dur=0.18):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        fsw = f0 * (1 + 0.6 * np.exp(-tt * 40))
        ph = 2 * np.pi * np.cumsum(fsw) / SR
        return np.sin(ph) * np.exp(-tt * 28) * np.clip(tt / 0.003, 0, 1)

    def whoosh(dur=0.35):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        x = bandnoise(n, 1800, 1.2, rng)
        env = np.sin(np.pi * tt / dur) ** 2
        return x * env

    def click():
        n = int(0.025 * SR)
        tt = np.arange(n) / SR
        return bandnoise(n, 3200, 2.0, rng) * np.exp(-tt * 260)

    def boom(dur=1.4):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        f = 55 * (1 + 0.8 * np.exp(-tt * 10))
        ph = 2 * np.pi * np.cumsum(f) / SR
        return (np.sin(ph) + 0.3 * np.sin(2 * ph)) * np.exp(-tt * 2.6) * np.clip(tt / 0.005, 0, 1)

    def chime(f0=880, dur=2.2):
        n = int(dur * SR)
        tt = np.arange(n) / SR
        s = np.zeros(n)
        for k, (m, g) in enumerate(((1, 1), (2.01, 0.35), (3.0, 0.15))):
            s += g * np.sin(2 * np.pi * f0 * m * tt) * np.exp(-tt * (2.2 + k))
        return s * np.clip(tt / 0.004, 0, 1)

    for at in (1.92, 7.92, 17.92, 23.92):
        add(whoosh(), at, 0.10)
    add(pop(740), 2.3, 0.12, 0.2)
    for at, f in ((8.4, 520), (10.0, 600), (11.6, 680)):
        add(pop(f), at, 0.11, 0.3)
    add(pop(880), 18.4, 0.12, 0.2)
    for text_, t0 in ((SON_THOUGHT, 13.0), (MOM_THOUGHT, 19.2)):
        for i, c in enumerate(text_):
            if c != " ":
                add(click(), t0 + i / CPS, 0.06 * (0.8 + 0.4 * rng.random()), -0.2 + 0.4 * rng.random())
    add(boom(), 21.0, 0.30)
    add(chime(note(69)), 24.15, 0.07, -0.2)
    add(chime(note(76)), 24.6, 0.05, 0.2)

    write_wav(path + ".pad.wav", pad * 0.5)
    # нормализация пэда к −24 LUFS
    lufs = measure_lufs(path + ".pad.wav")
    gain_db = -24.0 - lufs
    pad *= 0.5 * 10 ** (gain_db / 20)
    print(f"pad: {lufs:.1f} LUFS → gain {gain_db:+.1f} dB")
    mix = pad + sfx
    # фейд последних 0,5 с
    fade = np.clip((DUR - t) / 0.5, 0, 1)
    mix *= (fade ** 2)[:, None]
    mix *= np.clip(t / 0.02, 0, 1)[:, None]
    peak = np.abs(mix).max()
    if peak > 0.89:
        mix *= 0.89 / peak
    write_wav(path, mix)
    os.remove(path + ".pad.wav")
    print(f"mix: {measure_lufs(path):.1f} LUFS integrated, peak {20*np.log10(np.abs(mix).max()):.1f} dBFS")


def write_wav(path, x):
    import wave
    x16 = (np.clip(x, -1, 1) * 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(2)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes(x16.tobytes())


def measure_lufs(path):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-nostats", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                       capture_output=True, text=True)
    lines = [l for l in r.stderr.splitlines() if l.strip().startswith("I:")]
    return float(lines[-1].split()[1])


# ---------- main ----------
def preview():
    pdir = os.path.join(OUT, "preview")
    os.makedirs(pdir, exist_ok=True)
    for s in (1, 5, 12, 21, 26):
        # на 21-й секунде берём кадр, где хук уже проявился
        tt = s + (0.3 if s == 21 else 0)
        Image.fromarray(render_frame(int(round(tt * FPS)))).save(os.path.join(pdir, f"frame_{s:02d}s.png"))
    Image.fromarray(render_frame(int(1.0 * FPS))).save(os.path.join(OUT, "cover.png"))
    # контрольный лист с безопасными зонами
    print("preview saved to", pdir)


def render():
    wav = os.path.join(OUT, "audio.wav")
    make_audio(wav)
    mp4 = os.path.join(OUT, "u_menya_vsyo_horosho.mp4")
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
           "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
           "-i", wav,
           "-c:v", "libx264", "-preset", "slow", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR),
           "-t", f"{DUR}", "-movflags", "+faststart", mp4]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    with Pool(os.cpu_count()) as pool:
        for i, fr in enumerate(pool.imap(render_frame, range(NFRAMES), chunksize=4)):
            p.stdin.write(fr.tobytes())
            if i % 90 == 0:
                print(f"frame {i}/{NFRAMES}", flush=True)
    p.stdin.close()
    p.wait()
    os.remove(wav)
    print("done:", mp4)


if __name__ == "__main__":
    print("font:", BOLD)
    {"preview": preview, "render": render}[sys.argv[1] if len(sys.argv) > 1 else "preview"]()
