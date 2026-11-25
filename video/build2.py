#!/usr/bin/env python3
"""Ролик №2 «24 часа до прихода» — на том же движке, что и ролик про лифт (video/build.py, video/tts.py).

  python3 video/build2.py --tts            # озвучка -> voice2/NN.wav (+ радио-фрагменты)
  python3 video/build2.py                  # сборка -> final_video_2.mp4 (нужны imgs2/01..18.png)
  python3 video/build2.py --draft          # черновик с заглушками вместо отсутствующих картинок
Апскейл маленьких картинок (необязательно):  python3 video/upscale.py <model.onnx> imgs2 imgs2_hd
"""
import argparse, asyncio, json, math, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build as B
from build import (W, H, FPS, SR, ROOT, filt, env_ad, fade, reverb, stereo, randwalk, growl, metal_hit,
                   thump, wind, scrape, smooth, font, text_w, render_sub, render_fact, render_bar, loudnorm)

IMGDIR, HDDIR, VDIR = "imgs2", "imgs2_hd", "voice2"

# ------------------------------------------------------------------ сценарий
SCENES = [
    ("Ночью тебе приходит сообщение. Заражённые в двухстах километрах. У вас двадцать четыре часа.", "У ТЕБЯ 24 ЧАСА", "24"),
    ("Что ты сделаешь первым?", "ЧТО ПЕРВЫМ?", "ПЕРВЫМ?"),
    ("Утром магазины пустеют за час. Ты успеваешь взять только воду.", "МАГАЗИНЫ ПУСТЫ", "ПУСТЫ"),
    ("Банкоматы не работают. Карты — просто пластик.", "КАРТЫ НЕ РАБОТАЮТ", "НЕ РАБОТАЮТ"),
    ("Дома ты собираешь рюкзак: вода, спички, аптечка, радио, документы.", "ТОЛЬКО САМОЕ НУЖНОЕ", "НУЖНОЕ"),
    ("Весь город бежит. Трасса стоит намертво.", "ТРАССА СТОИТ", "СТОИТ"),
    ("И ты решаешь остаться. Заколачиваешь окна.", "ТЫ ОСТАЁШЬСЯ", "ОСТАЁШЬСЯ"),
    ("Двенадцать часов до прихода. В дверь стучит сосед с дочкой.", "СОСЕД С ДОЧКОЙ", "ДОЧКОЙ"),
    ("Ты бы пустил?", "ТЫ БЫ ПУСТИЛ?", "ПУСТИЛ?"),
    ("Ты открываешь. Теперь вас трое. А воды — на двоих.", "ВОДЫ — НА ДВОИХ", "ДВОИХ"),
    ("Три часа до прихода. Связь пропадает. По радио — одна фраза: не выходите на улицу.", "НЕ ВЫХОДИТЕ", "НЕ ВЫХОДИТЕ"),
    ("Полночь. Город гаснет. И становится очень тихо.", "ТИШИНА", "ТИШИНА"),
    ("А потом во дворе появляется первый.", "ПЕРВЫЙ", "ПЕРВЫЙ"),
    ("За ним — сотни.", "ЗА НИМ — СОТНИ", "СОТНИ"),
    ("Вы сидите без света и почти не дышите.", "НИ ЗВУКА", "ЗВУКА"),
    ("Кто-то скребётся в дверь.", "КТО-ТО ЗА ДВЕРЬЮ", "ДВЕРЬЮ"),
    ("Но утро наступает. Вы пережили первую ночь.", "ПЕРВАЯ НОЧЬ ПОЗАДИ", "ПОЗАДИ"),
    ("А что бы ты взял в рюкзак? Пиши в комментариях.", "ЧТО ТЫ БЫ ВЗЯЛ?", "ВЗЯЛ?"),
]
# озвучка по фрагментам: (текст, rate %, pitch Hz, пауза после). База -8% / -4Hz, как в ролике №1.
SCRIPT = [
    [("Ночью тебе приходит сообщение.", -8, -4, 0.35), ("Заражённые в двухстах километрах.", -12, -6, 0.35), ("У вас двадцать четыре часа.", -16, -8, 0)],
    [("Что ты сделаешь первым?", -14, -4, 0)],
    [("Утром магазины пустеют за час.", -2, -3, 0.30), ("Ты успеваешь взять только воду.", -8, -5, 0)],
    [("Банкоматы не работают.", -6, -4, 0.35), ("Карты — просто пластик.", -14, -7, 0)],
    [("Дома ты собираешь рюкзак:", -6, -4, 0.25), ("вода, спички, аптечка, радио, документы.", -10, -4, 0)],
    [("Весь город бежит.", 0, -3, 0.35), ("Трасса стоит намертво.", -14, -7, 0)],
    [("И ты решаешь остаться.", -14, -6, 0.35), ("Заколачиваешь окна.", -4, -4, 0)],
    [("Двенадцать часов до прихода.", -10, -6, 0.40), ("В дверь стучит сосед с дочкой.", -8, -4, 0)],
    [("Ты бы пустил?", -16, -4, 0)],
    [("Ты открываешь.", -10, -4, 0.30), ("Теперь вас трое.", -10, -4, 0.40), ("А воды — на двоих.", -16, -8, 0)],
    [("Три часа до прихода.", -10, -6, 0.30), ("Связь пропадает.", -12, -6, 0.35), ("По радио — одна фраза:", -10, -5, 0.30), ("не выходите на улицу.", -18, -9, 0)],
    [("Полночь.", -18, -10, 0.40), ("Город гаснет.", -14, -8, 0.45), ("И становится очень тихо.", -20, -10, 0)],
    [("А потом во дворе появляется первый.", -14, -8, 0)],
    [("За ним — сотни.", -12, -8, 0)],
    [("Вы сидите без света", -16, -8, 0.20), ("и почти не дышите.", -20, -10, 0)],
    [("Кто-то скребётся в дверь.", -16, -9, 0)],
    [("Но утро наступает.", -10, -2, 0.40), ("Вы пережили первую ночь.", -10, -3, 0)],
    [("А что бы ты взял в рюкзак?", -6, 0, 0.35), ("Пиши в комментариях.", -2, -2, 0)],
]
RADIO = ["Внимание. Говорит штаб гражданской обороны.", "Оставайтесь дома.", "Не выходите на улицу."]

TIMER = ["24:00", "23:58", "18:00", "16:30", "14:00", "13:00", "12:30", "12:00", "11:59", "09:00", "03:00", "00:00",
         "НОЧЬ 1", "НОЧЬ 1", "НОЧЬ 1", "НОЧЬ 1", "УТРО", "УТРО"]
PLACE = ["ДОМ", "ДОМ", "МАГАЗИН", "БАНК", "ДОМ", "ТРАССА", "ДОМ", "ДОМ", "ДОМ", "ДОМ", "КУХНЯ", "ГОРОД",
         "ДВОР", "УЛИЦА", "КВАРТИРА", "КВАРТИРА", "КВАРТИРА", None]
THREAT = [round(15 + 85 * k / 13) for k in range(14)] + [90, 80, 70, 70]
FACTS = {2: "Спасатели советуют держать запас около 4 литров воды на человека в сутки",
         3: "Без электричества не работают банкоматы и терминалы — держи наличные",
         10: "Радиоприёмник на батарейках работает без интернета и сотовой связи"}
# центр интереса (x, y в долях картинки), начало -> конец; уточняется по реальным картинкам
FOCUS = [((0.5, 0.45), (0.5, 0.43)), ((0.5, 0.48), (0.5, 0.46)), ((0.5, 0.52), (0.52, 0.5)), ((0.5, 0.45), (0.48, 0.45)),
         ((0.5, 0.58), (0.5, 0.56)), ((0.5, 0.62), (0.5, 0.38)), ((0.5, 0.45), (0.5, 0.43)), ((0.5, 0.45), (0.5, 0.45)),
         ((0.5, 0.5), (0.5, 0.48)), ((0.5, 0.55), (0.5, 0.53)), ((0.5, 0.55), (0.5, 0.52)), ((0.5, 0.6), (0.5, 0.38)),
         ((0.5, 0.45), (0.5, 0.42)), ((0.5, 0.5), (0.5, 0.48)), ((0.5, 0.5), (0.5, 0.48)), ((0.5, 0.55), (0.5, 0.52)),
         ((0.5, 0.45), (0.5, 0.42)), ((0.5, 0.42), (0.5, 0.42))]
PAN_UP = {5, 11}
RED_VIG = {13}
SHAKE = {0, 6, 13, 15}
VIBRO = [(0.15, 0.55), (0.75, 1.15), (1.35, 1.75)]      # 01: вибрация телефона
SCRATCH = [(0.15, 0.85), (1.2, 1.9), (2.25, 2.95)]       # 16: скрежет ногтей
DARK_STEPS = [0.15, 0.75, 1.3, 1.9, 2.5, 3.1]            # 12: окна гаснут рывками


def hammer_times(du):
    return [t for t in np.arange(0.25, du - 0.3, 0.62)]


def knock_times(L):
    a = 0.45 * L
    return [a, a + 0.42, a + 0.84]


def heart_times(du):
    out, t = [], 0.1
    while t < du:
        out += [t, t + 0.27]; t += 0.82
    return out


# ------------------------------------------------------------------ звук
def babble(rng, n, voices=16, f0=(100, 220), rate=(0.12, 0.3), angry=False):
    V = [(700, 1200), (500, 900), (350, 800), (500, 1800), (300, 2200), (600, 1500)]
    out = np.zeros((n, 2))
    for v in range(voices):
        x = np.zeros(n); t = rng.uniform(0, 0.5); base = rng.uniform(*f0)
        while t < n / SR:
            L = rng.uniform(*rate); m = int(L * SR); s = int(t * SR)
            if s + m >= n: break
            if rng.random() < 0.8:
                tt = np.arange(m) / SR; f = base * (1 + 0.15 * rng.standard_normal()) * (1 - 0.1 * tt / L)
                ph = 2 * np.pi * np.cumsum(np.full(m, f)) / SR
                src = 2 * ((ph / (2 * np.pi)) % 1) - 1 + 0.3 * rng.standard_normal(m)
                f1, f2 = V[rng.integers(len(V))]
                seg = filt(src, "bandpass", [f1 * 0.8, f1 * 1.2], 2) + 0.6 * filt(src, "bandpass", [f2 * 0.85, f2 * 1.15], 2)
                seg *= np.sin(np.pi * tt / L) ** 0.7
                x[s:s + m] += seg * (1.6 if angry else 1)
            t += L + rng.uniform(0, 0.12 if rng.random() < 0.8 else 0.6)
        out += stereo(x, rng.uniform(-0.9, 0.9)) * rng.uniform(0.4, 1)
    out = np.stack([filt(out[:, c], "lowpass", 3200, 2) for c in range(2)], 1)
    return out / (np.abs(out).max() + 1e-9)


def build_sfx(starts_f, total_f, lens):
    N = int(round(total_f / FPS * SR)) + SR
    mix = np.zeros((N, 2))

    def put(x, t0, gain=1.0):
        if x.ndim == 1: x = stereo(x)
        s = int(round(t0 * SR)); e = min(N, s + len(x))
        if s < N: mix[s:e] += x[: e - s] * gain

    def fade2(x, a, b):
        return np.stack([fade(x[:, c], a, b) for c in range(2)], 1) if x.ndim == 2 else fade(x, a, b)

    st = [s / FPS for s in starts_f]
    du = [(starts_f[i + 1] if i + 1 < len(starts_f) else total_f) / FPS - st[i] for i in range(len(st))]
    R = lambda i: np.random.default_rng(2000 + i)

    # 01 вибрация телефона + сигнал тревоги (двухтональный, как у систем оповещения)
    rng = R(1)
    for a, b in VIBRO:
        m = int((b - a) * SR); tt = np.arange(m) / SR
        bz = np.sign(np.sin(2 * np.pi * 165 * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * 330 * tt))
        bz = filt(bz, "bandpass", [120, 2500], 2) * np.minimum(1, np.minimum(tt, tt[-1] - tt) / 0.02)
        put(bz * 0.22, st[0] + a)
    m = int(min(du[0], 3.0) * SR); tt = np.arange(m) / SR
    gate = ((tt % 0.75) < 0.5).astype(float); gate = filt(gate, "lowpass", 60, 2)
    alarm = (np.sin(2 * np.pi * 853 * tt) + np.sin(2 * np.pi * 960 * tt)) * gate
    put(reverb(fade(alarm, 0.02, 0.6), rng, 0.8, 0.25) * 0.10, st[0] + 0.1)
    # 02 тишина + тиканье часов
    rng = R(2)
    for k, t0 in enumerate(np.arange(0.2, du[1], 1.0)):
        m = int(0.06 * SR); tt = np.arange(m) / SR
        f = 3400 if k % 2 == 0 else 2900
        tk = filt(rng.standard_normal(m), "bandpass", [1800, 5000], 2) * np.exp(-tt / 0.003) + 0.5 * np.sin(2 * np.pi * f * tt) * np.exp(-tt / 0.012)
        put(reverb(tk, rng, 0.4, 0.2) * 0.35, st[1] + t0)
    # 03 гул толпы + тележки
    rng = R(3); n = int((du[2] + 0.2) * SR)
    put(fade2(reverb(babble(rng, n, 18)[:, 0], rng, 1.4, 0.4)[:n], 0.3, 0.3) * 0.32, st[2])
    for _ in range(int(du[2] * 2)):
        m = int(rng.uniform(0.4, 0.9) * SR); tt = np.arange(m) / SR
        clicks = (rng.random(m) < 0.004).astype(float)
        rat = filt(clicks, "bandpass", [1500, 5000], 2) * 6 + filt(rng.standard_normal(m), "lowpass", 200, 2) * 0.5
        put(stereo(rat * np.sin(np.pi * tt / tt[-1]), rng.uniform(-0.7, 0.7)) * 0.12, st[2] + rng.uniform(0, du[2] - 0.5))
    # 04 писк терминала (ошибка) + ропот
    rng = R(4); n = int((du[3] + 0.2) * SR)
    put(fade2(reverb(babble(rng, n, 12, (90, 160), angry=True)[:, 1], rng, 1.0, 0.35)[:n], 0.3, 0.3) * 0.26, st[3])
    for t0 in (0.3, 0.3 + du[3] * 0.5):
        for k in range(3):
            m = int(0.11 * SR); tt = np.arange(m) / SR
            bp = filt(np.sign(np.sin(2 * np.pi * 1250 * tt)), "lowpass", 3000, 2) * np.minimum(1, np.minimum(tt, tt[-1] - tt) / 0.005)
            put(bp * 0.09, st[3] + t0 + k * 0.18)
    # 05 шорох рюкзака + молния
    rng = R(5); n = int(du[4] * SR)
    cr = np.clip(filt(rng.standard_normal(n), "lowpass", 25, 2) * 18, 0, 1) ** 2
    rus = filt(rng.standard_normal(n), "bandpass", [800, 6000], 2) * cr
    put(fade(rus, 0.1, 0.3) * 0.35, st[4])
    m = int(0.6 * SR); tt = np.arange(m) / SR
    rate = 60 + 110 * tt / 0.6
    zp = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > 0.95).astype(float)
    zp = filt(zp + 0.05 * rng.standard_normal(m), "bandpass", [1500, 7000], 2) * np.sin(np.pi * tt / 0.6) ** 0.5
    put(zp * 1.0, st[4] + du[4] * 0.62)
    # 06 гудки машин + далёкая сирена
    rng = R(6); n = int((du[5] + 0.2) * SR); tt = np.arange(n) / SR
    rumble = filt(rng.standard_normal(n), "lowpass", 150, 3)
    put(fade(rumble, 0.3, 0.3) * 0.25, st[5])
    sir_f = 1000 + 350 * np.sin(2 * np.pi * tt / 3.2)
    siren = np.sin(2 * np.pi * np.cumsum(sir_f) / SR)
    put(fade2(reverb(filt(siren, "lowpass", 2000, 2), rng, 2.5, 0.7)[:n], 0.6, 0.4) * 0.05, st[5])
    for _ in range(7):
        L = rng.uniform(0.2, 0.8); m = int(L * SR); t2 = np.arange(m) / SR; f = rng.uniform(340, 470)
        hn = np.sign(np.sin(2 * np.pi * f * t2)) + 0.7 * np.sign(np.sin(2 * np.pi * f * 1.26 * t2))
        hn = filt(hn, "lowpass", 1800, 2) * np.minimum(1, np.minimum(t2, t2[-1] - t2) / 0.02)
        hn = reverb(hn, rng, 1.2, 0.45)
        put(np.stack([hn[:, 0] * (1 + p) / 2 for p in (rng.uniform(-1, 1),)] * 2, 1) * rng.uniform(0.05, 0.12), st[5] + rng.uniform(0, du[5] - 0.6))
    # 07 удары молотка
    rng = R(7)
    for t0 in hammer_times(du[6]):
        m = int(0.5 * SR); t2 = np.arange(m) / SR
        h = filt(rng.standard_normal(m), "bandpass", [800, 6000], 2) * np.exp(-t2 / 0.006) * 1.5 \
            + np.sin(2 * np.pi * 2650 * t2) * np.exp(-t2 / 0.06) * 0.25 + thump(rng, m, 95, 0.12) * 0.5
        put(reverb(h, rng, 0.6, 0.25)[:m] * 0.42, st[6] + t0)
    # 08 три стука в дверь
    rng = R(8)
    for t0 in knock_times(lens[7]):
        put(reverb(thump(rng, int(0.9 * SR)), rng, 0.7, 0.3) * 0.5, st[7] + t0)
    # 09 стук сердца
    rng = R(9)
    for k, t0 in enumerate(heart_times(du[8])):
        m = int(0.4 * SR); t2 = np.arange(m) / SR
        hb = np.sin(2 * np.pi * (58 if k % 2 == 0 else 50) * t2) * np.exp(-t2 / 0.09) * (1 if k % 2 == 0 else 0.7)
        put(filt(hb, "lowpass", 160, 2) * 0.9, st[8] + t0)
    # 10 треск свечи
    rng = R(10); n = int(du[9] * SR); cr = np.zeros(n)
    for _ in range(int(du[9] * 5)):
        s = rng.integers(0, n - 300); cr[s:s + 200] += rng.standard_normal(200) * np.exp(-np.arange(200) / 30) * rng.uniform(0.3, 1)
    put(filt(cr, "bandpass", [900, 4500], 2) * 0.35, st[9])
    # 11 радиошум + обрывки голоса
    rng = R(11); n = int((du[10] + 0.2) * SR)
    stat = filt(rng.standard_normal(n), "bandpass", [400, 4000], 2) * (0.5 + 0.5 * np.clip(randwalk(rng, n, 0.003, 4), -1, 1))
    put(fade(stat, 0.2, 0.3) * 0.07, st[10])
    rp = os.path.join(ROOT, VDIR, "radio.wav")
    if os.path.exists(rp):
        sr, rv = B.wavfile.read(rp); rv = rv.astype(np.float64) / 32768
        if rv.ndim == 2: rv = rv.mean(1)
        rv = np.tanh(filt(rv, "bandpass", [450, 2800], 4) * 3) * 0.6
        gate = (filt(rng.standard_normal(len(rv)), "lowpass", 3, 2) > -0.02).astype(float)
        rv *= filt(gate, "lowpass", 40, 2)
        put(fade(rv[: int(du[10] * SR)], 0.05, 0.3) * 0.22, st[10] + 0.1)
    # 12 щелчок, тишина 1 с, затем ветер
    rng = R(12)
    click = filt(rng.standard_normal(int(0.03 * SR)), "highpass", 1500, 2) * env_ad(int(0.03 * SR), 0.0005, 0.005) \
        + 0.6 * filt(rng.standard_normal(int(0.03 * SR)), "lowpass", 400, 2) * env_ad(int(0.03 * SR), 0.0005, 0.01)
    put(click * 0.9, st[11] + DARK_STEPS[0])
    n = int((du[11] - 1.15 + du[12] * 0) * SR)
    if n > 0: put(fade2(wind(rng, n, 280, 1000, 0.25), 0.8, 0.3) * 0.12, st[11] + 1.15)
    # 13 одинокое рычание
    rng = R(13); n = int((du[12] + 0.2) * SR)
    put(fade2(reverb(growl(rng, n, 70, 18, 800), rng, 2.0, 0.45)[:n], 0.3, 0.3) * 0.33, st[12])
    put(fade2(wind(rng, n, 280, 1000, 0.25), 0.1, 0.3) * 0.08, st[12])
    # 14 рёв толпы
    rng = R(14); n = int((du[13] + 0.3) * SR); crowd = np.zeros((n, 2))
    for k in range(16):
        crowd += stereo(growl(rng, n, rng.uniform(55, 120), rng.uniform(14, 32), rng.uniform(600, 1300)), rng.uniform(-0.9, 0.9)) * rng.uniform(0.5, 1)
    crowd += stereo(filt(rng.standard_normal(n), "lowpass", 120, 3)) * 2
    crowd = np.stack([reverb(crowd[:, c], rng, 1.8, 0.4)[:n, c] for c in range(2)], 1)
    put(fade2(crowd / np.abs(crowd).max(), 0.15, 0.3) * 0.45, st[13])
    # 15 приглушённое дыхание, всё тише
    rng = R(15); t0 = 0.1; k = 0
    while t0 < du[14] - 0.5:
        for L, band, g in ((0.9, (600, 2400), 1.0), (1.2, (300, 1700), 0.8)):
            m = int(L * SR); t2 = np.arange(m) / SR
            br = filt(rng.standard_normal(m), "bandpass", list(band), 2) * np.sin(np.pi * t2 / L) ** 1.5
            put(filt(br, "lowpass", 1800, 2) * g * 0.22 * (0.65 ** k), st[14] + t0)
            t0 += L + 0.15
        k += 1
    # 16 скрежет ногтей по металлу
    rng = R(16)
    for a, b in SCRATCH:
        m = int((b - a) * SR); t2 = np.arange(m) / SR
        sc = scrape(rng, m); sq = np.sin(2 * np.pi * np.cumsum(2900 * (1 + 0.08 * np.tanh(randwalk(rng, m, 0.01, 3)))) / SR) * 0.3
        x = filt(sc + sq, "bandpass", [1500, 6500], 2) * np.sin(np.pi * t2 / t2[-1]) ** 0.6
        put(reverb(filt(x, "lowpass", 5000, 2), rng, 0.6, 0.3)[:m] * 0.5, st[15] + a)
    # 17 птицы вдалеке
    rng = R(17); n = int((du[16] + 0.3) * SR); birds = np.zeros(n); t0 = 0.3
    while t0 < du[16] - 0.3:
        for c in range(rng.integers(3, 7)):
            L = rng.uniform(0.05, 0.11); m = int(L * SR); t2 = np.arange(m) / SR
            f = rng.uniform(2800, 4800) * (1 + rng.uniform(-0.3, 0.3) * t2 / L)
            ch = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.sin(np.pi * t2 / L) ** 2
            s = int((t0 + c * rng.uniform(0.08, 0.14)) * SR)
            if s + m < n: birds[s:s + m] += ch
        t0 += rng.uniform(0.6, 1.3)
    put(fade2(reverb(birds, rng, 1.8, 0.55)[:n], 0.4, 0.4) * 0.10, st[16])
    # 18 удар-акцент
    rng = R(18); n = int(2.6 * SR); t2 = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (70 * np.exp(-t2 * 1.3) + 32) * t2) * np.exp(-t2 / 0.7)
    put(reverb(sub * 1.3 + metal_hit(rng, n, 120, 0.9) * 0.5, rng, 1.8, 0.35) * 0.5, st[17] + 0.02)
    mix = np.stack([filt(filt(mix[:, c], "lowpass", 9000, 6), "highpass", 30, 2) for c in range(2)], 1)
    return mix


# ------------------------------------------------------------------ графика
def placeholder(i):
    im = Image.new("RGB", (900, 1600), (28, 30, 38)); d = ImageDraw.Draw(im)
    d.text((450, 700), f"СЦЕНА {i+1:02d}", font=font("black", 90), fill=(230, 230, 230), anchor="mm")
    d.text((450, 820), f"нет картинки {IMGDIR}/{i+1:02d}.png", font=font("extra", 40), fill=(255, 120, 100), anchor="mm")
    return im


def prep(i, draft):
    p = os.path.join(ROOT, IMGDIR, f"{i+1:02d}.png")
    if not os.path.exists(p):
        if not draft: sys.exit(f"Нет картинки {p}")
        im = placeholder(i); K = 1.25
        s = max(W * K / im.width, H * K / im.height)
        return im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS), K
    return B.prep_image(i, IMGDIR, HDDIR)


def tmin(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)


def render_hud(i, t, f, starts_f):
    im = Image.new("RGBA", (W, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    grad = Image.new("L", (1, 400))
    for y in range(400): grad.putpixel((0, y), int(160 * (1 - y / 400) ** 1.6))
    im.paste(Image.new("RGBA", (W, 400), (0, 0, 0, 255)), (0, 0), grad.resize((W, 400)))
    x0, y0 = 48, 104
    val = TIMER[i]; numeric = ":" in val
    if numeric:
        d.text((x0 + 2, y0), "ДО ПРИХОДА", font=font("extra", 32), fill=(255, 255, 255, 230), stroke_width=3, stroke_fill=(0, 0, 0, 255))
        shown = val
        if i > 0 and ":" in TIMER[i - 1] and t < 0.4:   # «прокрутка» таймера от прошлого значения
            a, b = tmin(TIMER[i - 1]), tmin(val); k = smooth(t / 0.4); v = round(a + (b - a) * k)
            shown = f"{v // 60:02d}:{v % 60:02d}"
        col = (255, 255, 255)
        s12 = starts_f[TIMER.index("00:00")]
        if s12 - 5 * FPS <= f < s12:               # последние 5 с до 00:00 — мигает красным
            col = (255, 43, 28) if (f // 8) % 2 == 0 else (255, 255, 255)
        if val == "00:00": col = (255, 43, 28)
        fm = B.ImageFont.truetype(os.path.join(ROOT, "fonts", "JetBrainsMono_800ExtraBold.ttf"), 118)
        d.text((x0 - 4, y0 + 36), shown, font=fm, fill=col + (255,), stroke_width=6, stroke_fill=(0, 0, 0, 255))
        py = y0 + 36 + 140
    else:
        col = (255, 43, 28) if val.startswith("НОЧЬ") else (255, 210, 26)
        d.text((x0, y0 + 22), val, font=font("black", 112), fill=col + (255,), stroke_width=6, stroke_fill=(0, 0, 0, 255))
        py = y0 + 22 + 140
    if PLACE[i]:
        f2 = font("extra", 34); tw = text_w(d, PLACE[i], f2)
        d.rounded_rectangle([x0, py, x0 + tw + 44, py + 54], 8, fill=(0, 0, 0, 170))
        d.rectangle([x0, py, x0 + 8, py + 54], fill=(255, 210, 26, 255))
        d.text((x0 + 26, py + 27), PLACE[i], font=f2, fill=(255, 255, 255, 255), anchor="lm")
    return im


def shake_offset(i, t, du):
    def jit(seed, t, amp, f):
        r = np.random.default_rng(seed); ph = r.uniform(0, 6.3, 6); fr = f * r.uniform(0.6, 1.6, 6)
        return (amp * sum(math.sin(2 * math.pi * fr[k] * t + ph[k]) for k in range(3)) / 2.2,
                amp * sum(math.sin(2 * math.pi * fr[k] * t + ph[k]) for k in range(3, 6)) / 2.2)
    if i == 0:
        on = any(a <= t <= b for a, b in VIBRO)
        return jit(101, t, 5 if on else 0, 28)
    if i == 6:
        dx = dy = 0.0
        for k in hammer_times(du):
            if t >= k:
                e = math.exp(-(t - k) / 0.1) * 16
                dx += e * math.sin(2 * math.pi * 15 * (t - k) + 0.7); dy += e * math.sin(2 * math.pi * 19 * (t - k))
        return dx, dy
    if i == 13:
        return jit(141, t, 12, 9)
    if i == 15:
        on = any(a <= t <= b for a, b in SCRATCH)
        return jit(161, t, 7 if on else 1.5, 12)
    return 0.0, 0.0


def flicker(fl, seed, lo):
    r = np.random.default_rng(seed + fl // 3); v = r.random()
    if v < 0.55: return 0.0
    if v < 0.75: return lo
    return r.uniform(0.1, lo)


def render_video(starts_f, total_f, lens, out_path, audio_wav, draft):
    xs = (np.arange(W) - W / 2) / (W / 2); ys = (np.arange(H) - H / 2) / (H / 2)
    rr = np.sqrt(xs[None, :] ** 2 * 0.9 + ys[:, None] ** 2 * 0.75)
    ss = lambda a, b, x: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
    vig = (1 - 0.42 * ss(0.45, 1.3, rr)).astype(np.float32)[:, :, None]
    redm = ss(0.35, 1.25, rr).astype(np.float32)[:, :, None]
    red = np.array([150, 0, 0], np.float32); warm = np.array([255, 178, 105], np.float32)
    imgs = [prep(i, draft) for i in range(len(SCENES))]
    subs = [render_sub(i, SCENES) for i in range(len(SCENES))]
    facts = {k: render_fact(v) for k, v in FACTS.items()}
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", audio_wav, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "slow", "-crf", "15", "-tune", "animation", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-r", str(FPS), "-c:a", "aac", "-b:a", "256k", "-ar", str(SR), "-ac", "2", "-movflags", "+faststart", "-shortest", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ends = starts_f[1:] + [total_f]
    for f in range(total_f):
        i = max(k for k in range(len(starts_f)) if starts_f[k] <= f)
        fl = f - starts_f[i]; nf = ends[i] - starts_f[i]; t = fl / FPS; u = fl / max(nf - 1, 1); du = nf / FPS
        base, K = imgs[i]
        zmax = 0.20 if i == 8 else 0.12                       # 09: медленный глубокий наезд
        z = (1.0 + zmax * u) * (1.06 if i in SHAKE else 1.0)
        if i == 8:                                             # пульс в такт сердцу
            z *= 1 + sum(0.008 * math.exp(-(t - h) / 0.12) for h in heart_times(du) if t >= h)
        (fx0, fy0), (fx1, fy1) = FOCUS[i]
        e = smooth(u) if i in PAN_UP else u
        fx = fx0 + (fx1 - fx0) * e; fy = fy0 + (fy1 - fy0) * e
        cw, ch = W * K / z, H * K / z
        sx, sy = shake_offset(i, t, du); scale = cw / W
        cx = min(max(fx * base.width + sx * scale, cw / 2), base.width - cw / 2)
        cy = min(max(fy * base.height + sy * scale, ch / 2), base.height - ch / 2)
        a = np.asarray(base.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)), dtype=np.float32)
        if i == 11:                                            # окна гаснут рывками
            n = sum(1 for s in DARK_STEPS if t >= s)
            dip = 0.25 if any(0 <= t - s < 0.07 for s in DARK_STEPS) else 0
            a *= 1 - min(0.6, 0.1 * n + dip)
        if i == 12:
            a *= 1 - flicker(fl, 7000, 0.45)                   # мигание фонаря
        if i == 14:
            a *= 1 - 0.25 * u                                  # всё тише и темнее
        if i == 16:                                            # мягкий тёплый свет
            k = 0.08 + 0.22 * smooth(u)
            a = a * (1 - k) + np.minimum(255, a * 1.15 + 20) * k * 0.5 + warm * k * 0.5
        if i in RED_VIG:
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 1.6 * t - 1.2); al = redm * (0.35 + 0.4 * pulse)
            a = a * (1 - al) + red * al
        a *= vig
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ov.alpha_composite(render_hud(i, t, f, starts_f), (0, 0))
        v0 = THREAT[i - 1] if i > 0 else 0
        ov.alpha_composite(render_bar(v0 + (THREAT[i] - v0) * smooth(t / 0.6), 0), (W - 170 - 22, 640))
        if i in facts:
            fc = facts[i]; k = smooth((t - 0.35) / 0.3)
            if k > 0:
                c2 = fc.copy(); c2.putalpha(c2.getchannel("A").point(lambda q: int(q * k)))
                ov.alpha_composite(c2, (int(-fc.width + (40 + fc.width) * k), 410))
        sb = subs[i]; k = min(t / 0.15, 1.0); sc = 0.7 + 0.3 * (1 - (1 - k) ** 3)
        sbi = sb if sc >= 0.999 else sb.resize((max(1, int(sb.width * sc)), max(1, int(sb.height * sc))), Image.BICUBIC)
        ov.alpha_composite(sbi, (int(W / 2 - sbi.width / 2), int(1470 - sbi.height / 2)))
        o = np.asarray(ov, dtype=np.float32); oa = o[:, :, 3:4] / 255.0
        a = a * (1 - oa) + o[:, :, :3] * oa
        if i > 0 and fl < 4:
            fa = 0.3 * (1 - fl / 4); a = a * (1 - fa) + 255 * fa
        p.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
        if f % 300 == 0: print(f"  кадр {f}/{total_f}", flush=True)
    p.stdin.close(); p.wait()
    if p.returncode: sys.exit("ffmpeg failed")


# ------------------------------------------------------------------ main
def run_tts():
    import tts
    asyncio.run(tts.main(None, SCRIPT, os.path.join(ROOT, VDIR)))
    # радио-фрагменты другим голосом (диктор гражданской обороны), без нашей голосовой обработки
    async def radio():
        parts = []
        for k, txt in enumerate(RADIO):
            mp3 = os.path.join(ROOT, VDIR, "chunks", f"radio_{k}.mp3")
            await tts.synth(txt, 0, 0, mp3, voice="ru-RU-SvetlanaNeural")
            parts.append(tts.trim(tts.dec(mp3))); parts.append(np.zeros(int(0.5 * SR)))
        B.wavfile.write(os.path.join(ROOT, VDIR, "radio.wav"), SR, (np.concatenate(parts) * 32767 * 0.9).astype(np.int16))
    asyncio.run(radio())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tts", action="store_true")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "final_video_2.mp4"))
    ap.add_argument("--work", default="/tmp/zombie_build2")
    a = ap.parse_args()
    if a.tts:
        run_tts(); return
    os.makedirs(a.work, exist_ok=True)
    voices, lens, starts_f, total_f = B.timeline(os.path.join(ROOT, VDIR), SCENES, tail=1.5)
    if any(v is None for v in voices): sys.exit("Нет озвучки: запустите с --tts")
    print("сцены (старт, сек):", [round(s / FPS, 2) for s in starts_f], "итого", round(total_f / FPS, 2), "с")
    json.dump({"starts_f": starts_f, "total_f": total_f, "voice_len": lens}, open(os.path.join(a.work, "timeline.json"), "w"), indent=1)
    raw = os.path.join(a.work, "mix_raw.wav"); fin = os.path.join(a.work, "mix.wav")
    B.build_audio(voices, starts_f, total_f, lens, raw, sfx_fn=build_sfx, duck_db=-10.0, sfx_gain=0.55)
    loudnorm(raw, fin)
    render_video(starts_f, total_f, lens, a.out, fin, a.draft)
    print("готово:", a.out)


if __name__ == "__main__":
    main()
