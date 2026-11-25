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

IMGDIR, CARDDIR, HDDIR, VDIR = "imgs2", "imgs2_card", "imgs2_hd", "voice2"
# В PDF каждая страница 720x1280: по центру резкая карточка-кадр, вокруг — размытая копия,
# сверху у части страниц осколок предыдущей карточки, в углу — номер сцены.
# Верх карточки по группам страниц (найден по чёрной полосе-разделителю), низ/бока общие.
CARD_BOX = ([(312, 966)] * 3 + [(362, 955)] * 3 + [(367, 921)] * 3 + [(365, 938)] * 3 +
            [(392, 921)] * 3 + [(458, 846)] * 2)          # (верх, низ) карточки по группам страниц
CARD_L, CARD_R = 16, 701
CARD_CX, CARD_CY, CARD_MAXH, CARD_MAXW = 460, 850, 480, 860   # карточка между HUD и субтитрами, в безопасной зоне

# ------------------------------------------------------------------ сценарий
SCENES = [
    ("Ночью тебе приходит сообщение. Заражённые в двухстах километрах. У вас двадцать четыре часа.", "У ТЕБЯ 24 ЧАСА", "24"),
    ("Что ты сделаешь первым?", "ЧТО ПЕРВЫМ?", "ПЕРВЫМ?"),
    ("Утром магазины пустеют за час. Ты успеваешь взять только воду.", "МАГАЗИНЫ ПУСТЫ", "ПУСТЫ"),
    ("И за эту воду тебя уже готовы бить.", "ЗА ВОДУ ДЕРУТСЯ", "ДЕРУТСЯ"),
    ("Банкоматы не работают. Карты — просто пластик.", "КАРТЫ НЕ РАБОТАЮТ", "НЕ РАБОТАЮТ"),
    ("Соседи набивают машины вещами. Весь город бежит.", "ГОРОД БЕЖИТ", "БЕЖИТ"),
    ("Но трасса стоит намертво.", "ТРАССА СТОИТ", "СТОИТ"),
    ("И ты решаешь остаться. Заколачиваешь окна.", "ТЫ ОСТАЁШЬСЯ", "ОСТАЁШЬСЯ"),
    ("Двенадцать часов до прихода. В дверь стучит сосед с дочкой.", "СОСЕД С ДОЧКОЙ", "ДОЧКОЙ"),
    ("Ты бы пустил? У тебя одна бутылка воды.", "ТЫ БЫ ПУСТИЛ?", "ПУСТИЛ?"),
    ("Три часа до прихода. Связь пропадает. По радио — одна фраза: не выходите на улицу.", "НЕ ВЫХОДИТЕ", "НЕ ВЫХОДИТЕ"),
    ("Полночь. На трассе, где все стояли в пробке, — теперь они. Сотни.", "ИХ СОТНИ", "СОТНИ"),
    ("Вы сидите без света. И ты сам не замечаешь, как засыпаешь.", "НИ ЗВУКА", "ЗВУКА"),
    ("Утром тебя будит телефон.", "НОВОЕ СООБЩЕНИЕ", "СООБЩЕНИЕ"),
    ("Вирус распространён по всей стране. Оставайтесь дома.", "ПО ВСЕЙ СТРАНЕ", "ВСЕЙ СТРАНЕ"),
    ("Ты смотришь в глазок. Подъезд забит ими.", "ОНИ В ПОДЪЕЗДЕ", "В ПОДЪЕЗДЕ"),
    ("А что бы ты взял в рюкзак? Пиши в комментариях.", "ЧТО ТЫ БЫ ВЗЯЛ?", "ВЗЯЛ?"),
]
# Озвучка. База -8% / -4Hz (как задано). Чтобы звучало по-человечески:
# целые предложения читаются одним запросом (естественная интонация), фрагменты —
# только там, где нужна драматическая пауза; отклонения высоты небольшие (-2…-6 Hz).
SCRIPT = [
    [("Ночью тебе приходит сообщение.", -6, -4, 0.45), ("Заражённые в двухстах километрах.", -8, -4, 0.40), ("У вас двадцать четыре часа.", -12, -6, 0)],
    [("Что ты сделаешь первым?", -10, -3, 0)],
    [("Утром магазины пустеют за час. Ты успеваешь взять только воду.", -4, -4, 0)],
    [("И за эту воду тебя уже готовы бить.", -4, -4, 0)],
    [("Банкоматы не работают.", -6, -4, 0.35), ("Карты — просто пластик.", -10, -5, 0)],
    [("Соседи набивают машины вещами.", -4, -4, 0.35), ("Весь город бежит.", -2, -3, 0)],
    [("Но трасса стоит намертво.", -10, -5, 0)],
    [("И ты решаешь остаться.", -10, -5, 0.35), ("Заколачиваешь окна.", -4, -4, 0)],
    [("Двенадцать часов до прихода.", -8, -5, 0.40), ("В дверь стучит сосед с дочкой.", -6, -4, 0)],
    [("Ты бы пустил?", -12, -3, 0.50), ("У тебя одна бутылка воды.", -10, -5, 0)],
    [("Три часа до прихода. Связь пропадает.", -8, -5, 0.35), ("По радио — одна фраза:", -8, -4, 0.30), ("не выходите на улицу.", -14, -6, 0)],
    [("Полночь.", -12, -6, 0.45), ("На трассе, где все стояли в пробке, — теперь они.", -8, -5, 0.35), ("Сотни.", -14, -6, 0)],
    [("Вы сидите без света.", -12, -6, 0.40), ("И ты сам не замечаешь, как засыпаешь.", -14, -6, 0)],
    [("Утром тебя будит телефон.", -8, -3, 0)],
    [("Вирус распространён по всей стране.", -10, -5, 0.35), ("Оставайтесь дома.", -14, -6, 0)],
    [("Ты смотришь в глазок.", -10, -5, 0.45), ("Подъезд забит ими.", -14, -6, 0)],
    [("А что бы ты взял в рюкзак?", -4, -2, 0.35), ("Пиши в комментариях.", -2, -2, 0)],
]
RADIO = ["Внимание. Говорит штаб гражданской обороны.", "Оставайтесь дома.", "Не выходите на улицу."]
VOICE_GAIN = {13: -2.0, 16: -1.0}   # тихие сцены (засыпает, глазок) чуть тише
PREROLL = 0.35          # сцена 01: голос вступает после удара-зацепа
HUD_K = 1.7             # HUD и карточка «ФАКТ» — в 1.7 раза крупнее
SUB_Y = 1250            # центр субтитров
SUB_MAXW = 860          # ширина строки субтитров
SUB_X = 460             # центр колонки = центр безопасной зоны (0…920): строка 860 px -> x 30…890
SAFE_R, SAFE_B = 160, 380   # безопасные зоны Shorts: справа и снизу — ничего важного
FACT_X, FACT_W = 40, 860    # «ФАКТ» целиком в безопасной зоне (x 40…900)
# Резкие наезды (+8% за 0.15 с) в сценах длиннее 4 с — на ключевых словах (начало слова, по WordBoundary)
PUNCH_WORDS = {1: ["сообщение", "двухстах", "двадцать"], 3: ["пустеют", "воду"], 4: ["бить"], 5: ["работают", "пластик"],
               6: ["машины", "бежит"], 8: ["остаться", "окна"], 9: ["двенадцать", "сосед", "дочкой"],
               10: ["пустил", "одна"], 11: ["пропадает", "радио", "улицу"], 12: ["полночь", "пробке", "сотни"],
               13: ["света", "засыпаешь"], 15: ["вирус", "стране", "дома"], 16: ["глазок", "забит"],
               17: ["рюкзак", "комментариях"]}
TIMER = ["24:00", "23:58", "18:00", "17:40", "16:30", "14:00", "13:00", "12:30", "12:00", "11:59", "03:00", "00:00",
         "НОЧЬ 1", "УТРО", "УТРО", "УТРО", "УТРО"]
PLACE = ["ДОМ", "УЛИЦА", "МАГАЗИН", "МАГАЗИН", "БАНК", "ДВОР", "ТРАССА", "ДОМ", "ДОМ", "ДОМ", "КУХНЯ", "ТРАССА",
         "КВАРТИРА", "КВАРТИРА", "КВАРТИРА", "ПОДЪЕЗД", None]
# 15% -> 100% к орде на трассе (сцена 12), ночью спадает, утром снова 100%
THREAT = [round(15 + 85 * k / 11) for k in range(12)] + [85, 75, 90, 100, 100]
FACTS = {2: "Спасатели советуют держать запас около 4 литров воды на человека в сутки",
         4: "Без электричества не работают банкоматы и терминалы — держи наличные",
         10: "Радиоприёмник на батарейках работает без интернета и сотовой связи"}
# центр интереса (доли карточки), начало -> конец
FOCUS = [((0.45, 0.5), (0.42, 0.5)), ((0.5, 0.5), (0.5, 0.48)), ((0.5, 0.5), (0.62, 0.35)), ((0.45, 0.45), (0.55, 0.45)),
         ((0.55, 0.45), (0.62, 0.4)), ((0.5, 0.5), (0.55, 0.5)), ((0.5, 0.6), (0.5, 0.45)), ((0.5, 0.5), (0.55, 0.5)),
         ((0.5, 0.5), (0.4, 0.55)), ((0.5, 0.5), (0.45, 0.55)), ((0.45, 0.55), (0.6, 0.6)), ((0.5, 0.55), (0.5, 0.45)),
         ((0.45, 0.5), (0.45, 0.48)), ((0.5, 0.5), (0.55, 0.55)), ((0.5, 0.45), (0.5, 0.45)), ((0.5, 0.5), (0.5, 0.5)),
         ((0.5, 0.45), (0.5, 0.42))]
PAN_UP = {6, 11}
RED_VIG = {11, 15}
SHAKE = {0, 3, 7, 11, 13, 15}
VIBRO = [(0.45, 0.85), (1.05, 1.45), (1.65, 2.05)]      # 01: вибрация телефона (после удара-зацепа)
VIBRO14 = [(0.1, 0.5), (0.7, 1.1), (1.3, 1.7)]          # 14: телефон будит
SCRATCH = [(0.4, 1.0), (1.5, 2.1), (2.6, 3.2)]          # 16: скребутся в подъезде
FIGHT = [0.2, 0.9, 1.6]                                  # 04: рывки за воду


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
    R = lambda i: np.random.default_rng(3000 + i)

    def vibro(t0, pattern, g=0.22):
        for a, b in pattern:
            m = int((b - a) * SR); tt = np.arange(m) / SR
            bz = np.sign(np.sin(2 * np.pi * 165 * tt)) * (0.6 + 0.4 * np.sin(2 * np.pi * 330 * tt))
            bz = filt(bz, "bandpass", [120, 2500], 2) * np.minimum(1, np.minimum(tt, tt[-1] - tt) / 0.02)
            put(bz * g, t0 + a)

    def hit(rng, t0, g=0.5, f0=70):
        n = int(2.4 * SR); t2 = np.arange(n) / SR
        sub = np.sin(2 * np.pi * (f0 * np.exp(-t2 * 1.6) + 34) * t2) * np.exp(-t2 / 0.6)
        crack = filt(rng.standard_normal(n), "bandpass", [300, 6000], 2) * np.exp(-t2 / 0.025)
        put(reverb(sub * 1.3 + crack + metal_hit(rng, n, 130, 0.8) * 0.4, rng, 1.6, 0.32) * g, t0)

    def horde(rng, n, voices=16):
        crowd = np.zeros((n, 2))
        for k in range(voices):
            crowd += stereo(growl(rng, n, rng.uniform(55, 120), rng.uniform(14, 32), rng.uniform(600, 1300)), rng.uniform(-0.9, 0.9)) * rng.uniform(0.5, 1)
        crowd += stereo(filt(rng.standard_normal(n), "lowpass", 120, 3)) * 2
        crowd = np.stack([reverb(crowd[:, c], rng, 1.8, 0.4)[:n, c] for c in range(2)], 1)
        return crowd / np.abs(crowd).max()

    # 01 удар-зацеп + вибрация + сигнал тревоги
    rng = R(1)
    hit(rng, st[0], 0.62, 85)
    vibro(st[0], VIBRO)
    m = int(min(du[0], 3.0) * SR); tt = np.arange(m) / SR
    gate = filt(((tt % 0.75) < 0.5).astype(float), "lowpass", 60, 2)
    alarm = (np.sin(2 * np.pi * 853 * tt) + np.sin(2 * np.pi * 960 * tt)) * gate
    put(reverb(fade(alarm, 0.02, 0.6), rng, 0.8, 0.25) * 0.10, st[0] + 0.4)
    # 02 улица в панике: гул толпы + тиканье часов
    rng = R(2); n = int((du[1] + 0.2) * SR)
    put(fade2(reverb(babble(rng, n, 14, angry=True)[:, 0], rng, 1.6, 0.45)[:n], 0.2, 0.3) * 0.22, st[1])
    for k, t0 in enumerate(np.arange(0.2, du[1], 0.5)):
        m = int(0.06 * SR); tt = np.arange(m) / SR
        tk = filt(rng.standard_normal(m), "bandpass", [1800, 5000], 2) * np.exp(-tt / 0.003) + 0.5 * np.sin(2 * np.pi * (3400 if k % 2 == 0 else 2900) * tt) * np.exp(-tt / 0.012)
        put(reverb(tk, rng, 0.4, 0.2) * 0.35, st[1] + t0)
    # 03 магазин: гул толпы + тележки
    rng = R(3); n = int((du[2] + 0.2) * SR)
    put(fade2(reverb(babble(rng, n, 18)[:, 0], rng, 1.4, 0.4)[:n], 0.3, 0.3) * 0.32, st[2])
    for _ in range(int(du[2] * 2)):
        m = int(rng.uniform(0.4, 0.9) * SR); tt = np.arange(m) / SR
        clicks = (rng.random(m) < 0.004).astype(float)
        rat = filt(clicks, "bandpass", [1500, 5000], 2) * 6 + filt(rng.standard_normal(m), "lowpass", 200, 2) * 0.5
        put(stereo(rat * np.sin(np.pi * tt / tt[-1]), rng.uniform(-0.7, 0.7)) * 0.12, st[2] + rng.uniform(0, du[2] - 0.5))
    # 04 драка за воду: злой гул + рывки (глухие удары, хруст пластика)
    rng = R(4); n = int((du[3] + 0.2) * SR)
    put(fade2(reverb(babble(rng, n, 12, (90, 170), angry=True)[:, 1], rng, 1.0, 0.35)[:n], 0.2, 0.3) * 0.30, st[3])
    for t0 in FIGHT:
        put(thump(rng, int(0.5 * SR), 90, 0.12) * 0.35, st[3] + t0)
        m = int(0.25 * SR); tt = np.arange(m) / SR
        cr = filt((rng.random(m) < 0.02).astype(float), "bandpass", [1500, 6000], 2) * np.exp(-tt / 0.08) * 3
        put(cr * 0.5, st[3] + t0 + 0.03)
    # 05 банкомат: писк ошибки + ропот
    rng = R(5); n = int((du[4] + 0.2) * SR)
    put(fade2(reverb(babble(rng, n, 12, (90, 160), angry=True)[:, 1], rng, 1.0, 0.35)[:n], 0.3, 0.3) * 0.24, st[4])
    for t0 in (0.3, 0.3 + du[4] * 0.5):
        for k in range(3):
            m = int(0.11 * SR); tt = np.arange(m) / SR
            bp = filt(np.sign(np.sin(2 * np.pi * 1250 * tt)), "lowpass", 3000, 2) * np.minimum(1, np.minimum(tt, tt[-1] - tt) / 0.005)
            put(bp * 0.09, st[4] + t0 + k * 0.18)
    # 06 двор: двигатели, хлопки багажников, суета
    rng = R(6); n = int((du[5] + 0.2) * SR)
    eng = filt(np.sign(np.sin(2 * np.pi * np.cumsum(32 + 4 * np.sin(2 * np.pi * 0.7 * np.arange(n) / SR)) / SR)), "lowpass", 220, 3)
    put(fade(eng, 0.3, 0.3) * 0.10, st[5])
    put(fade2(reverb(babble(rng, n, 10)[:, 0], rng, 1.2, 0.4)[:n], 0.3, 0.3) * 0.16, st[5])
    for t0 in (0.5, du[5] * 0.55, du[5] * 0.8):
        put(reverb(thump(rng, int(0.6 * SR), 75, 0.15) * 0.8 + metal_hit(rng, int(0.6 * SR), 210, 0.25) * 0.25, rng, 0.9, 0.3) * 0.38, st[5] + t0)
    # 07 трасса: гудки машин + далёкая сирена
    rng = R(7); n = int((du[6] + 0.2) * SR); tt = np.arange(n) / SR
    put(fade(filt(rng.standard_normal(n), "lowpass", 150, 3), 0.3, 0.3) * 0.25, st[6])
    siren = np.sin(2 * np.pi * np.cumsum(1000 + 350 * np.sin(2 * np.pi * tt / 3.2)) / SR)
    put(fade2(reverb(filt(siren, "lowpass", 2000, 2), rng, 2.5, 0.7)[:n], 0.6, 0.4) * 0.05, st[6])
    for _ in range(6):
        L = rng.uniform(0.2, 0.8); m = int(L * SR); t2 = np.arange(m) / SR; f = rng.uniform(340, 470)
        hn = np.sign(np.sin(2 * np.pi * f * t2)) + 0.7 * np.sign(np.sin(2 * np.pi * f * 1.26 * t2))
        hn = reverb(filt(hn, "lowpass", 1800, 2) * np.minimum(1, np.minimum(t2, t2[-1] - t2) / 0.02), rng, 1.2, 0.45)
        put(hn * rng.uniform(0.05, 0.12), st[6] + rng.uniform(0, max(0.1, du[6] - 0.6)))
    # 08 удары молотка
    rng = R(8)
    for t0 in hammer_times(du[7]):
        m = int(0.5 * SR); t2 = np.arange(m) / SR
        h = filt(rng.standard_normal(m), "bandpass", [800, 6000], 2) * np.exp(-t2 / 0.006) * 1.5 \
            + np.sin(2 * np.pi * 2650 * t2) * np.exp(-t2 / 0.06) * 0.25 + thump(rng, m, 95, 0.12) * 0.5
        put(reverb(h, rng, 0.6, 0.25)[:m] * 0.42, st[7] + t0)
    # 09 три стука в дверь
    rng = R(9)
    for t0 in knock_times(lens[8]):
        put(reverb(thump(rng, int(0.9 * SR)), rng, 0.7, 0.3) * 0.5, st[8] + t0)
    # 10 стук сердца + треск свечи
    rng = R(10)
    for k, t0 in enumerate(heart_times(du[9])):
        m = int(0.4 * SR); t2 = np.arange(m) / SR
        hb = np.sin(2 * np.pi * (58 if k % 2 == 0 else 50) * t2) * np.exp(-t2 / 0.09) * (1 if k % 2 == 0 else 0.7)
        put(filt(hb, "lowpass", 160, 2) * 0.9, st[9] + t0)
    n = int(du[9] * SR); cr = np.zeros(n)
    for _ in range(int(du[9] * 4)):
        s0 = rng.integers(0, n - 300); cr[s0:s0 + 200] += rng.standard_normal(200) * np.exp(-np.arange(200) / 30) * rng.uniform(0.3, 1)
    put(filt(cr, "bandpass", [900, 4500], 2) * 0.3, st[9])
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
    # 12 орда на трассе: рёв толпы
    rng = R(12); n = int((du[11] + 0.3) * SR)
    put(fade2(horde(rng, n), 0.25, 0.3) * 0.42, st[11])
    # 13 засыпает: приглушённое дыхание, всё тише
    rng = R(13); t0 = 0.1; k = 0
    while t0 < du[12] - 0.5:
        for L, band, g in ((0.9, (600, 2400), 1.0), (1.2, (300, 1700), 0.8)):
            m = int(L * SR); t2 = np.arange(m) / SR
            br = filt(rng.standard_normal(m), "bandpass", list(band), 2) * np.sin(np.pi * t2 / L) ** 1.5
            put(filt(br, "lowpass", 1800, 2) * g * 0.2 * (0.65 ** k), st[12] + t0)
            t0 += L + 0.15
        k += 1
    # 14 будит телефон: вибрация
    vibro(st[13], VIBRO14, 0.28)
    # 15 сообщение: низкий гул + удар-акцент
    rng = R(15); n = int((du[14] + 0.2) * SR); tt = np.arange(n) / SR
    drone = (np.sin(2 * np.pi * 41 * tt) + 0.5 * np.sin(2 * np.pi * 61.5 * tt)) * (0.7 + 0.3 * np.sin(2 * np.pi * 0.4 * tt))
    put(fade(drone, 0.6, 0.4) * 0.12, st[14])
    hit(rng, st[14] + 0.02, 0.35, 60)
    # 16 глазок: орда за дверью (глухо) + скрежет
    rng = R(16); n = int((du[15] + 0.3) * SR)
    hd = horde(rng, n, 12); hd = np.stack([filt(hd[:, c], "lowpass", 700, 3) for c in range(2)], 1)
    put(fade2(hd, 0.3, 0.3) * 0.45, st[15])
    for a, b in SCRATCH:
        if a >= du[15]: continue
        m = int((min(b, du[15]) - a) * SR); t2 = np.arange(m) / SR
        sc = scrape(rng, m); sq = np.sin(2 * np.pi * np.cumsum(2900 * (1 + 0.08 * np.tanh(randwalk(rng, m, 0.01, 3)))) / SR) * 0.3
        x = filt(sc + sq, "bandpass", [1500, 6500], 2) * np.sin(np.pi * t2 / t2[-1]) ** 0.6
        put(reverb(filt(x, "lowpass", 5000, 2), rng, 0.6, 0.3)[:m] * 0.4, st[15] + a)
    # 17 удар-акцент на вопросе
    hit(R(17), st[16] + 0.02, 0.5, 70)
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


def extract_cards():
    """imgs2/NN.png -> imgs2_card/NN.png: вырезать карточку и стереть номер сцены в углу."""
    import cv2
    os.makedirs(os.path.join(ROOT, CARDDIR), exist_ok=True)
    for i in range(len(SCENES)):
        im = Image.open(os.path.join(ROOT, IMGDIR, f"{i+1:02d}.png")).convert("RGB")
        c = np.asarray(im.crop((CARD_L, CARD_BOX[i][0] + 3, CARD_R, CARD_BOX[i][1] - 3)))
        g = c[:90, :120].astype(np.int16)
        # номер сцены в этом PDF полупрозрачный — закрываем фиксированную область угла карточки
        bw_, bh_ = (90, 60) if CARD_BOX[i][1] - CARD_BOX[i][0] < 450 else (140, 90)
        ys, xs = np.array([0, bh_ - 18]), np.array([0, bw_ - 18])
        out = c.copy(); npx = 0
        if len(ys):
            # прямоугольник номера (с обводкой и тенью): заполнить inpaint'ом и мягко размыть,
            # края маски растушёваны — остаётся спокойное пятно «вне фокуса», без следов цифр
            y1, x1 = ys.max() + 18, xs.max() + 18
            m = np.zeros(c.shape[:2], np.uint8); m[:y1, :x1] = 255
            fill = cv2.inpaint(c, m, 15, cv2.INPAINT_TELEA)
            fill = cv2.GaussianBlur(fill, (0, 0), 14)
            mm = np.zeros(c.shape[:2], np.float32); mm[:y1 + 6, :x1 + 6] = 1
            wgt = cv2.GaussianBlur(mm, (0, 0), 14)[..., None]
            wgt = np.clip(wgt / max(wgt[y1 // 2, x1 // 2, 0], 1e-3), 0, 1)
            out = (c * (1 - wgt) + fill * wgt).astype(np.uint8)
            npx = y1 * x1
        Image.fromarray(out).save(os.path.join(ROOT, CARDDIR, f"{i+1:02d}.png"))
        print(i + 1, c.shape[1::-1], "закрыто пикселей:", npx)


def card_canvas(i, draft):
    """Кадр 9:16: размытая затемнённая подложка + карточка по центру. Возвращает (canvas, K, rect)."""
    K = 1.25
    hd = os.path.join(ROOT, HDDIR, f"{i+1:02d}.png"); cp = os.path.join(ROOT, CARDDIR, f"{i+1:02d}.png")
    if os.path.exists(hd): card = Image.open(hd).convert("RGB")
    elif os.path.exists(cp): card = Image.open(cp).convert("RGB")
    elif draft: card = placeholder(i).crop((0, 400, 900, 1200))
    else: sys.exit(f"Нет карточки {cp}: запустите --cards")
    CW, CH = int(W * K), int(H * K)
    # подложка
    s = max(CW / card.width, CH / card.height)
    bg = card.resize((max(1, int(card.width * s / 12)), max(1, int(card.height * s / 12))), Image.BILINEAR)
    bg = bg.filter(ImageFilter.GaussianBlur(4)).resize((int(card.width * s), int(card.height * s)), Image.BICUBIC)
    bg = bg.crop(((bg.width - CW) // 2, (bg.height - CH) // 2, (bg.width - CW) // 2 + CW, (bg.height - CH) // 2 + CH))
    bg = Image.eval(bg, lambda v: int(v * 0.42))
    # карточка
    sc = min(CARD_MAXW * K / card.width, CARD_MAXH * K / card.height)
    cw, ch = int(card.width * sc), int(card.height * sc)
    cimg = card.resize((cw, ch), Image.LANCZOS).filter(ImageFilter.UnsharpMask(radius=1.0, percent=30, threshold=3))
    # мягкая виньетка углов карточки
    yy, xx = np.mgrid[0:ch, 0:cw].astype(np.float32)
    rr = np.sqrt(((xx - cw / 2) / (cw / 2)) ** 2 + ((yy - ch / 2) / (ch / 2)) ** 2)
    cv = 1 - 0.5 * np.clip((rr - 0.95) / 0.45, 0, 1) ** 1.5
    cimg = Image.fromarray((np.asarray(cimg, np.float32) * cv[..., None]).astype(np.uint8))
    if cw > CW:   # шире кадра — обрезать бока поровну
        cimg = cimg.crop(((cw - CW) // 2, 0, (cw - CW) // 2 + CW, ch)); cw = CW
    x0, y0 = int(CARD_CX * K - cw / 2), int(CARD_CY * K - ch / 2)
    sh = Image.new("L", (CW, CH), 0); ImageDraw.Draw(sh).rectangle([x0 - 6, y0 + 4, x0 + cw + 6, y0 + ch + 18], fill=200)
    bg.paste(Image.new("RGB", (CW, CH), (0, 0, 0)), (0, 0), sh.filter(ImageFilter.GaussianBlur(22)))
    bg.paste(cimg, (x0, y0))
    return bg, K, (x0, y0, cw, ch)


def tmin(s):
    h, m = s.split(":"); return int(h) * 60 + int(m)


def render_hud(i, t, f, starts_f, threat=None):
    q = lambda v: int(round(v * HUD_K)); HH = 600
    im = Image.new("RGBA", (W, HH), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    grad = Image.new("L", (1, HH))
    for y in range(HH): grad.putpixel((0, y), int(170 * (1 - y / HH) ** 1.4))
    im.paste(Image.new("RGBA", (W, HH), (0, 0, 0, 255)), (0, 0), grad.resize((W, HH)))
    x0, y0 = 44, 96
    val = TIMER[i]; numeric = ":" in val
    if numeric:
        d.text((x0 + 4, y0), "ДО ПРИХОДА", font=font("extra", q(32)), fill=(255, 255, 255, 235), stroke_width=q(3), stroke_fill=(0, 0, 0, 255))
        shown = val
        if i > 0 and ":" in TIMER[i - 1] and t < 0.4:   # «прокрутка» таймера от прошлого значения
            a, b = tmin(TIMER[i - 1]), tmin(val); k = smooth(t / 0.4); v = round(a + (b - a) * k)
            shown = f"{v // 60:02d}:{v % 60:02d}"
        col = (255, 255, 255)
        s12 = starts_f[TIMER.index("00:00")]
        if s12 - 5 * FPS <= f < s12:               # последние 5 с до 00:00 — мигает красным
            col = (255, 43, 28) if (f // 8) % 2 == 0 else (255, 255, 255)
        if val == "00:00": col = (255, 43, 28)
        fm = B.ImageFont.truetype(os.path.join(ROOT, "fonts", "JetBrainsMono_800ExtraBold.ttf"), q(118))
        d.text((x0 - 6, y0 + q(36)), shown, font=fm, fill=col + (255,), stroke_width=q(6), stroke_fill=(0, 0, 0, 255))
        py = y0 + q(36) + q(140)
    else:
        col = (255, 43, 28) if val.startswith("НОЧЬ") else (255, 210, 26)
        d.text((x0, y0 + q(10)), val, font=font("black", q(112)), fill=col + (255,), stroke_width=q(6), stroke_fill=(0, 0, 0, 255))
        py = y0 + q(10) + q(140)
    if PLACE[i]:
        f2 = font("extra", q(34)); tw = text_w(d, PLACE[i], f2); ph = q(54)
        d.rounded_rectangle([x0, py, x0 + tw + q(44), py + ph], q(8), fill=(0, 0, 0, 170))
        d.rectangle([x0, py, x0 + q(8), py + ph], fill=(255, 210, 26, 255))
        d.text((x0 + q(26), py + ph // 2), PLACE[i], font=f2, fill=(255, 255, 255, 255), anchor="lm")
    if threat is not None:   # шкала «УГРОЗА»: под таймером и плашкой, горизонтальная, 300 px
        by = py + (q(54) if PLACE[i] else 0) + 22
        fl = font("black", q(30)); lw = text_w(d, "УГРОЗА", fl, q(4))
        d.text((x0, by + 26), "УГРОЗА", font=fl, fill=(255, 255, 255, 255), stroke_width=q(4), stroke_fill=(0, 0, 0, 255), anchor="lm")
        bx = x0 + lw + 18; bw, bh = 300, 40
        d.rounded_rectangle([bx - 5, by + 6 - 5, bx + bw + 5, by + 6 + bh + 5], 12, fill=(0, 0, 0, 170), outline=(255, 255, 255, 220), width=4)
        fw = int(bw * threat / 100); col = B.threat_col(threat)
        if fw > 0: d.rounded_rectangle([bx, by + 6, bx + fw, by + 6 + bh], 9, fill=col + (255,))
        for k in range(1, 10):
            xx = bx + bw * k // 10; d.line([xx, by + 6 + bh - 12, xx, by + 6 + bh], fill=(0, 0, 0, 120), width=3)
        d.text((bx + bw + 22, by + 26), f"{int(round(threat))}%", font=font("black", q(40)), fill=col + (255,),
               stroke_width=q(4), stroke_fill=(0, 0, 0, 255), anchor="lm")
    return im


def render_bar_top(v):
    """Шкала «УГРОЗА» в правом верхнем углу (над карточкой, ничего не закрывает); x1.7."""
    q = lambda x: int(round(x * HUD_K))
    bw, bh = q(30), 400
    im = Image.new("RGBA", (440, bh + 24), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    bx, by = 440 - bw - 14, 10
    d.rounded_rectangle([bx - 6, by - 6, bx + bw + 6, by + bh + 6], 14, fill=(0, 0, 0, 170), outline=(255, 255, 255, 220), width=4)
    fh = int(bh * v / 100); col = B.threat_col(v)
    if fh > 0: d.rounded_rectangle([bx, by + bh - fh, bx + bw, by + bh], 10, fill=col + (255,))
    for k in range(1, 10):
        yy = by + bh * k // 10; d.line([bx, yy, bx + 14, yy], fill=(0, 0, 0, 120), width=3)
    d.text((bx - 18, by + bh - q(52) - 14), "УГРОЗА", font=font("black", q(30)), fill=(255, 255, 255, 255), stroke_width=q(4), stroke_fill=(0, 0, 0, 255), anchor="rd")
    d.text((bx - 18, by + bh), f"{int(round(v))}%", font=font("black", q(52)), fill=col + (255,), stroke_width=q(5), stroke_fill=(0, 0, 0, 255), anchor="rd")
    return im


def scene_words(i):
    p = os.path.join(ROOT, VDIR, f"{i+1:02d}.words.json")
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else []


def punch_times(i, du):
    if du <= 4.0: return []
    keys = PUNCH_WORDS.get(i + 1, []); out = []
    for w in scene_words(i):
        ww = w["word"].lower().strip(".,:;!?—…«»")
        if any(ww.startswith(k) for k in keys) and all(abs(w["t"] - o) > 0.6 for o in out):
            out.append(max(0.08, w["t"]))
    return out[:3]


def punch_zoom(t, times):
    """+8% за 0.15 с, удержание 0.35 с, мягкий возврат за 0.5 с."""
    z = 0.0
    for p in times:
        if t < p: continue
        u = t - p
        if u < 0.15: z = max(z, 0.08 * (1 - (1 - u / 0.15) ** 3))
        elif u < 0.5: z = max(z, 0.08)
        else: z = max(z, 0.08 * (1 - smooth((u - 0.5) / 0.5)))
    return z


def intro_zoom(t):
    """Сцена 01: быстрый наезд за первые 0.35 с (+15%), затем плавно до +5%."""
    return 0.15 * (1 - (1 - min(t / 0.35, 1)) ** 3) - 0.10 * smooth((t - 0.5) / 1.0)


def shake_offset(i, t, du):
    def jit(seed, t, amp, f):
        r = np.random.default_rng(seed); ph = r.uniform(0, 6.3, 6); fr = f * r.uniform(0.6, 1.6, 6)
        return (amp * sum(math.sin(2 * math.pi * fr[k] * t + ph[k]) for k in range(3)) / 2.2,
                amp * sum(math.sin(2 * math.pi * fr[k] * t + ph[k]) for k in range(3, 6)) / 2.2)
    if i == 0:
        on = any(a <= t <= b for a, b in VIBRO)
        hx, hy = jit(102, t, 22 * math.exp(-t / 0.12), 14)      # удар-зацеп в первые доли секунды
        vx, vy = jit(101, t, 5 if on else 0, 28)
        return hx + vx, hy + vy
    if i == 3:                                                # рывки в драке за воду
        dx = dy = 0.0
        for k in FIGHT:
            if t >= k:
                e = math.exp(-(t - k) / 0.13) * 18
                dx += e * math.sin(2 * math.pi * 11 * (t - k) + 0.4); dy += e * math.sin(2 * math.pi * 14 * (t - k))
        return dx, dy
    if i == 13:                                               # вибрация телефона
        on = any(a <= t <= b for a, b in VIBRO14)
        return jit(131, t, 5 if on else 0, 28)
    if i == 7:
        dx = dy = 0.0
        for k in hammer_times(du):
            if t >= k:
                e = math.exp(-(t - k) / 0.1) * 16
                dx += e * math.sin(2 * math.pi * 15 * (t - k) + 0.7); dy += e * math.sin(2 * math.pi * 19 * (t - k))
        return dx, dy
    if i == 11:
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
    canv = [card_canvas(i, draft) for i in range(len(SCENES))]
    ends0 = starts_f[1:] + [total_f]
    punches = [punch_times(i, (ends0[i] - starts_f[i]) / FPS) for i in range(len(SCENES))]
    print("наезды:", {i + 1: p for i, p in enumerate(punches) if p})
    imgs = [(c, K) for c, K, _ in canv]
    subs = [render_sub(i, SCENES, SUB_MAXW) for i in range(len(SCENES))]
    facts = {k: render_fact(v, HUD_K, FACT_W) for k, v in FACTS.items()}
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
        zmax = 0.18 if i == 9 else 0.10                       # 10: «Ты бы пустил?» — медленный глубокий наезд
        z = (1.0 + zmax * u) * (1.06 if i in SHAKE else 1.0)
        z *= 1 + punch_zoom(t, punches[i])
        if i == 0:
            z *= 1 + intro_zoom(t)
        if i == 9:                                             # пульс в такт сердцу
            z *= 1 + sum(0.008 * math.exp(-(t - h) / 0.12) for h in heart_times(du) if t >= h)
        (fx0, fy0), (fx1, fy1) = FOCUS[i]
        e = smooth(u) if i in PAN_UP else u
        fx = fx0 + (fx1 - fx0) * e; fy = fy0 + (fy1 - fy0) * e
        rx, ry, rw, rh = canv[i][2]
        fx = (rx + fx * rw) / base.width; fy = (ry + fy * rh) / base.height
        cw, ch = W * K / z, H * K / z
        sx, sy = shake_offset(i, t, du); scale = cw / W
        Fx, Fy = fx * base.width, fy * base.height; C0x, C0y = base.width / 2, base.height / 2
        zt = (W * K) / cw
        cx = min(max(Fx + (C0x - Fx) / zt + sx * scale, cw / 2), base.width - cw / 2)
        cy = min(max(Fy + (C0y - Fy) / zt + sy * scale, ch / 2), base.height - ch / 2)
        a = np.asarray(base.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)), dtype=np.float32)
        if i == 12:
            a *= 1 - 0.35 * smooth(u)                          # засыпает: всё темнее
        if i == 14:                                            # сообщение: краснее к концу
            k = 0.12 * smooth(u); a = a * (1 - k) + red * k
        if i in RED_VIG:
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 1.6 * t - 1.2); al = redm * (0.35 + 0.4 * pulse)
            a = a * (1 - al) + red * al
        a *= vig
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        v0 = THREAT[i - 1] if i > 0 else 0
        ov.alpha_composite(render_hud(i, t, f, starts_f, v0 + (THREAT[i] - v0) * smooth(t / 0.6)), (0, 0))
        if i in facts:
            fa0 = max(0.3, du - 0.45 - 3.4)                    # «ФАКТ» — последние ~3.4 с сцены, сначала видна картинка
            fc = facts[i]; k = smooth((t - fa0) / 0.3) * (1 - smooth((t - (du - 0.45)) / 0.3))
            if k > 0:
                c2 = fc.copy(); c2.putalpha(c2.getchannel("A").point(lambda q: int(q * k)))
                ov.alpha_composite(c2, (int(-fc.width + (FACT_X + fc.width) * k), 600))
        sb = subs[i]; k = min(t / 0.15, 1.0); sc = 0.7 + 0.3 * (1 - (1 - k) ** 3)
        sbi = sb if sc >= 0.999 else sb.resize((max(1, int(sb.width * sc)), max(1, int(sb.height * sc))), Image.BICUBIC)
        ov.alpha_composite(sbi, (int(SUB_X - sbi.width / 2), int(SUB_Y - sbi.height / 2)))
        o = np.asarray(ov, dtype=np.float32); oa = o[:, :, 3:4] / 255.0
        a = a * (1 - oa) + o[:, :, :3] * oa
        if fl < 4 and (i > 0 or True):                      # вспышка на склейке и на самом первом кадре
            fa = (0.45 if i == 0 else 0.3) * (1 - fl / 4); a = a * (1 - fa) + 255 * fa
        p.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
        if f % 300 == 0: print(f"  кадр {f}/{total_f}", flush=True)
    p.stdin.close(); p.wait()
    if p.returncode: sys.exit("ffmpeg failed")


# ------------------------------------------------------------------ main
def run_tts():
    import tts
    asyncio.run(tts.main(None, SCRIPT, os.path.join(ROOT, VDIR), fx=tts.VOICE_FX_HUMAN, gains=VOICE_GAIN,
                         pad=0.06, fade_ms=25, words=True, preroll={1: PREROLL}))
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
    ap.add_argument("--cards", action="store_true", help="вырезать карточки из imgs2 -> imgs2_card")
    ap.add_argument("--draft", action="store_true")
    ap.add_argument("--out", default=os.path.join(ROOT, "final_video_2.mp4"))
    ap.add_argument("--work", default="/tmp/zombie_build2")
    a = ap.parse_args()
    if a.tts:
        run_tts(); return
    if a.cards:
        extract_cards(); return
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
