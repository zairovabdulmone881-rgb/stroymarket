#!/usr/bin/env python3
"""Сборка вертикального ролика «Ты застрял в лифте. Снаружи — зомби».

Использование:
  python3 video/build.py --voice voice --out final_video.mp4
Если папки voice/ нет (или --draft), длительности сцен оцениваются по длине текста,
голоса нет, и результат — только черновик.
Всё детерминировано от номера кадра / номера сцены.
"""
import argparse, json, math, os, subprocess, sys, wave
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from scipy import signal
from scipy.io import wavfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H, FPS, SR = 1080, 1920, 30, 48000

# ---------------------------------------------------------------- сценарий
SCENES = [
    # текст диктора, субтитр, выделение, HUD-время, локация, плашка, угроза, фокус(от, до)
    ("Ты едешь в лифте домой. Девятый этаж…", "ТЫ ЕДЕШЬ ДОМОЙ", "ДОМОЙ"),
    ("…и тут кабина резко встаёт. Свет гаснет. Кнопка диспетчера молчит.", "ЛИФТ ВСТАЛ", "ВСТАЛ"),
    ("А потом ты слышишь это… Скрежет. Сверху. Снизу. Отовсюду.", "СКРЕЖЕТ. ОТОВСЮДУ", "СКРЕЖЕТ."),
    ("Кто-то пытается раскрыть двери.", "КТО-ТО ЛОМИТ ДВЕРИ", "ДВЕРИ"),
    ("Ты лезешь в люк на крыше кабины.", "ЛЮК В ПОТОЛКЕ", "ЛЮК"),
    ("Шахта. Темнота. Только трос и твой фонарик.", "ТОЛЬКО ТРОС И ФОНАРИК", "ФОНАРИК"),
    ("Десятый этаж. На лестнице — они.", "НА ЛЕСТНИЦЕ — ОНИ", "ОНИ"),
    ("Ты забегаешь в первую открытую квартиру и закрываешь дверь шкафом.", "ДВЕРЬ — ШКАФОМ", "ШКАФОМ"),
    ("В окне — весь город. Он горит.", "ГОРОД ГОРИТ", "ГОРИТ"),
    ("Воды — три бутылки. Еды — на неделю.", "3 БУТЫЛКИ ВОДЫ", "ВОДЫ"),
    ("Ночью в дверь начинают стучать.", "НОЧЬЮ СТУЧАТ", "СТУЧАТ"),
    ("Утром ты выбираешься на крышу…", "УТРО. КРЫША", "КРЫША"),
    ("…и видишь свет. Ты не один.", "ТЫ НЕ ОДИН", "НЕ ОДИН"),
    ("А ты бы выбрался из этого лифта? Пиши в комментариях.", "А ТЫ БЫ ВЫБРАЛСЯ?", "ВЫБРАЛСЯ?"),
]
HOUR = ["ЧАС 1"] * 6 + ["ЧАС 3"] * 4 + ["ЧАС 9"] + ["ДЕНЬ 2"] * 3
CLOCK = ["21:40"] * 6 + ["23:15"] * 4 + ["03:20"] + ["06:45"] * 3
PLACE = ["ЛИФТ"] * 6 + ["ПОДЪЕЗД", "КВАРТИРА", "КВАРТИРА", "КВАРТИРА", "КВАРТИРА", "КРЫША", "КРЫША", "КРЫША"]
THREAT = [10, 22, 35, 48, 55, 60, 72, 78, 82, 86, 95, 80, 68, 60]
# центр интереса (x, y в долях картинки): (начало, конец сцены)
FOCUS = [
    ((0.40, 0.62), (0.42, 0.38)),  # 01 сдвиг вверх
    ((0.55, 0.52), (0.58, 0.50)),
    ((0.48, 0.60), (0.50, 0.58)),
    ((0.58, 0.32), (0.58, 0.30)),
    ((0.45, 0.38), (0.48, 0.36)),
    ((0.50, 0.68), (0.50, 0.28)),  # 06 сдвиг вверх
    ((0.62, 0.36), (0.66, 0.32)),
    ((0.42, 0.55), (0.42, 0.52)),
    ((0.58, 0.40), (0.60, 0.36)),
    ((0.50, 0.60), (0.50, 0.62)),
    ((0.62, 0.48), (0.64, 0.46)),
    ((0.45, 0.62), (0.45, 0.58)),
    ((0.52, 0.62), (0.56, 0.36)),  # 13 сдвиг вверх
    ((0.55, 0.45), (0.55, 0.42)),
]
FACTS = {1: "Застрял в лифте — нажми кнопку вызова диспетчера и не разжимай двери сам",
         9: "Без воды человек выживает около 3 суток"}
RED_VIG = {2, 3, 6, 10}
SHAKE = {1, 3, 10}
KNOCKS = [0.35, 0.95, 1.55]          # сцена 11: удары (сек от начала сцены)
YELLOW, RED = (255, 210, 26), (255, 43, 28)


def font(weight, size):
    p = os.path.join(ROOT, "fonts", "Montserrat_900Black.ttf" if weight == "black" else "Montserrat_800ExtraBold.ttf")
    if not os.path.exists(p):
        p = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    return ImageFont.truetype(p, size)


def ffprobe_dur(path):
    out = subprocess.check_output(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                                   "-of", "default=nw=1:nk=1", path])
    return float(out)


def smooth(t):
    t = min(max(t, 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- тайминг
def timeline(voice_dir):
    voices, lens = [], []
    for i, (txt, _, _) in enumerate(SCENES):
        p = os.path.join(voice_dir, f"{i+1:02d}.mp3") if voice_dir else None
        if p and os.path.exists(p):
            voices.append(p); lens.append(ffprobe_dur(p))
        else:
            voices.append(None); lens.append(0.55 + len(txt) / 14.5)  # оценка для черновика
    durs = [l + 0.3 for l in lens]
    durs[-1] = lens[-1] + 1.5
    starts_f, f = [], 0
    for d in durs:
        starts_f.append(f); f += int(round(d * FPS))
    return voices, lens, starts_f, f


# ---------------------------------------------------------------- аудио-утилиты
def sos(kind, f, order=4):
    return signal.butter(order, f, btype=kind, fs=SR, output="sos")


def filt(x, kind, f, order=4):
    return signal.sosfilt(sos(kind, f, order), x)


def env_ad(n, a, d):
    t = np.arange(n) / SR
    return np.minimum(t / max(a, 1e-4), 1.0) * np.exp(-np.maximum(t - a, 0) / d)


def fade(x, fi=0.15, fo=0.25):
    n = len(x); a = int(fi * SR); b = int(fo * SR)
    g = np.ones(n)
    if a: g[:a] = np.linspace(0, 1, a)
    if b: g[-b:] *= np.linspace(1, 0, b)
    return x * g


def reverb(x, rng, t60=1.2, mix=0.35):
    n = int(t60 * SR)
    t = np.arange(n) / SR
    out = []
    for ch in range(2):
        ir = rng.standard_normal(n) * np.exp(-6.9 * t / t60)
        ir = filt(ir, "lowpass", 5000, 2); ir /= np.sqrt(np.sum(ir ** 2))
        out.append(np.pad(signal.fftconvolve(x, ir), (0, 1))[: len(x) + n])
    dry = np.pad(x, (0, n))
    return np.stack([dry * (1 - mix) + out[0] * mix, dry * (1 - mix) + out[1] * mix], 1)


def stereo(x, pan=0.0):
    l = math.cos((pan + 1) * math.pi / 4); r = math.sin((pan + 1) * math.pi / 4)
    return np.stack([x * l, x * r], 1) * 1.414


def randwalk(rng, n, rate, smooth_hz):
    w = np.cumsum(rng.standard_normal(n)) * rate
    w = filt(w, "lowpass", smooth_hz, 2)
    return w - w.mean()


def growl(rng, n, f0=80, rough=24, bright=700):
    t = np.arange(n) / SR
    f = f0 * (1 + 0.12 * np.tanh(randwalk(rng, n, 0.01, 3))) * (1 + 0.04 * np.sin(2 * np.pi * rough * t))
    ph = 2 * np.pi * np.cumsum(f) / SR
    saw = 2 * ((ph / (2 * np.pi)) % 1) - 1
    x = saw + 0.6 * rng.standard_normal(n) * (0.5 + 0.5 * np.sin(ph))
    x = filt(x, "bandpass", [60, bright], 2)
    am = 0.6 + 0.4 * np.abs(np.sin(2 * np.pi * rough * 0.5 * t + rng.uniform(0, 6)))
    sw = 0.5 + 0.5 * np.clip(filt(rng.standard_normal(n), "lowpass", 1.5, 2) * 20, -1, 1)
    return x * am * sw


def metal_hit(rng, n, base=180, dec=1.2):
    t = np.arange(n) / SR
    x = np.zeros(n)
    for k, r in enumerate([1, 2.41, 3.95, 6.07, 9.17, 13.2]):
        x += rng.uniform(0.4, 1) / (k + 1) ** 0.6 * np.sin(2 * np.pi * base * r * t + rng.uniform(0, 6)) * np.exp(-t / (dec / (1 + 0.5 * k)))
    burst = filt(rng.standard_normal(n), "bandpass", [200, 4000], 2) * np.exp(-t / 0.04)
    thump = np.sin(2 * np.pi * 52 * t) * np.exp(-t / 0.25)
    return 0.45 * x + 0.8 * burst + 1.0 * thump


def thump(rng, n, f=68, dec=0.28):
    t = np.arange(n) / SR
    body = np.sin(2 * np.pi * (f - 18 * t / (t[-1] + 1e-9)) * t) * np.exp(-t / dec)
    nb = filt(rng.standard_normal(n), "lowpass", 600, 2) * np.exp(-t / 0.06)
    wood = filt(rng.standard_normal(n), "bandpass", [140, 380], 2) * np.exp(-t / 0.12)
    return 1.2 * body + 1.0 * nb + 2.0 * wood


def wind(rng, n, lo=300, hi=1400, gust_hz=0.3):
    out = []
    for ch in range(2):
        x = rng.standard_normal(n)
        g = 0.55 + 0.45 * np.sin(2 * np.pi * gust_hz * np.arange(n) / SR + rng.uniform(0, 6)) \
            + 0.25 * np.clip(randwalk(rng, n, 0.002, 1), -1, 1)
        a = filt(x, "bandpass", [lo, hi], 2)
        b = filt(x, "bandpass", [lo * 2.2, lo * 2.6], 2) * 1.5  # свист
        out.append((a + b) * np.clip(g, 0.1, 1.5))
    return np.stack(out, 1)


def scrape(rng, n):
    t = np.arange(n) / SR
    x = rng.standard_normal(n)
    a = filt(x, "bandpass", [700, 3200], 4)
    stick = (np.sin(2 * np.pi * np.cumsum(25 + 15 * np.tanh(randwalk(rng, n, 0.01, 2))) / SR) > 0.3).astype(float)
    stick = filt(stick, "lowpass", 300, 2)
    fsq = 1400 * (1 + 0.15 * np.tanh(randwalk(rng, n, 0.01, 2)))
    sq = np.sin(2 * np.pi * np.cumsum(fsq) / SR) * 0.25
    sw = np.clip(0.4 + filt(rng.standard_normal(n), "lowpass", 2, 2) * 25, 0, 1)
    return (a * (0.4 + stick) + sq) * sw


# ---------------------------------------------------------------- звуковые эффекты
def build_sfx(starts_f, total_f, lens):
    N = int(round(total_f / FPS * SR)) + SR
    mix = np.zeros((N, 2))

    def put(x, t0, gain=1.0):
        if x.ndim == 1: x = stereo(x)
        s = int(round(t0 * SR)); e = min(N, s + len(x))
        if s < N: mix[s:e] += x[: e - s] * gain

    st = [s / FPS for s in starts_f]
    du = [(starts_f[i + 1] if i + 1 < len(starts_f) else total_f) / FPS - st[i] for i in range(len(st))]
    R = lambda i: np.random.default_rng(1000 + i)

    # 01 гул мотора лифта
    rng = R(1); n = int((du[0] + 0.2) * SR); t = np.arange(n) / SR
    hum = sum(a * np.sin(2 * np.pi * f * t * (1 + 0.003 * np.sin(2 * np.pi * 0.7 * t))) for f, a in [(48, 1), (96, .6), (144, .3), (390, .06)])
    hum += 0.8 * filt(rng.standard_normal(n), "lowpass", 220, 2)
    put(fade(hum, 0.3, 0.12) * 0.22, st[0])
    # 02 удар-остановка + щелчок света + гудение мигающей лампы
    rng = R(2); n = int(2.5 * SR)
    put(reverb(metal_hit(rng, n, 165, 1.4), rng, 0.8, 0.3) * 0.55, st[1] + 0.02)
    t_click = st[1] + 0.42 * lens[1]
    click = filt(rng.standard_normal(int(0.02 * SR)), "highpass", 2500, 2) * env_ad(int(0.02 * SR), 0.0005, 0.004)
    put(click * 0.9, t_click); put(click * 0.5, t_click + 0.09)
    n = int(du[1] * SR); t = np.arange(n) / SR
    buzz = filt(np.sign(np.sin(2 * np.pi * 100 * t)), "bandpass", [100, 1500], 2) * 0.05
    put(fade(buzz, 0.4, 0.2), st[1])
    # 03–04 скрежет + рычание
    for i, sg, gg in [(2, 0.30, 0.18), (3, 0.22, 0.32)]:
        rng = R(i + 1); n = int((du[i] + 0.1) * SR)
        sc = reverb(scrape(rng, n), rng, 1.0, 0.35)[:n]
        gr = reverb(growl(rng, n, 72 if i == 2 else 85), rng, 0.9, 0.25)[:n]
        put(fade(sc[:, 0], 0.1, 0.15) * sg, st[i]); put(stereo(fade(gr[:, 1], 0.2, 0.15), 0.2) * gg, st[i])
    # 04 удары по створкам
    rng = R(40)
    for k, dt in enumerate([0.15, 0.7, 1.3]):
        if dt < du[3]: put(metal_hit(rng, int(0.8 * SR), 240, 0.4) * 0.18, st[3] + dt)
    # 05 лязг люка (тихо)
    rng = R(5); put(reverb(metal_hit(rng, int(1.2 * SR), 300, 0.5), rng, 1.5, 0.4) * 0.16, st[4] + 0.4 * du[4])
    # 06 капли с эхом + скрип троса
    rng = R(6); n = int((du[5] + 0.3) * SR); drops = np.zeros(n); t = 0.2
    while t < du[5]:
        m = int(0.08 * SR); tt = np.arange(m) / SR
        f0 = rng.uniform(900, 1700)
        d = np.sin(2 * np.pi * f0 * (1 - 0.6 * tt / 0.08) * tt) * np.exp(-tt / 0.018)
        s = int(t * SR); drops[s:s + m] += d[: n - s] * rng.uniform(0.5, 1)
        t += rng.uniform(0.35, 0.8)
    echo = drops.copy()
    for k, dl in enumerate([0.21, 0.43, 0.66, 0.9]):
        s = int(dl * SR); echo[s:] += drops[:-s] * 0.55 ** (k + 1)
    put(reverb(echo, rng, 2.4, 0.5)[:n] * 0.28, st[5])
    for t0 in [0.5, 0.5 + du[5] * 0.45]:
        m = int(0.9 * SR); tt = np.arange(m) / SR
        rate = 18 + 30 * np.sin(np.pi * tt / 0.9)
        pulses = (np.sin(2 * np.pi * np.cumsum(rate) / SR) > 0.92).astype(float)
        cr = filt(pulses + 0.1 * rng.standard_normal(m), "bandpass", [350, 1300], 2) * np.sin(np.pi * tt / 0.9)
        put(reverb(cr, rng, 1.5, 0.4)[:m] * 0.5, st[5] + t0)
    # 07 рычание толпы
    rng = R(7); n = int((du[6] + 0.2) * SR); crowd = np.zeros((n, 2))
    for k in range(10):
        g = growl(rng, n, rng.uniform(58, 115), rng.uniform(15, 30), rng.uniform(500, 1100))
        crowd += stereo(g, rng.uniform(-0.8, 0.8)) * rng.uniform(0.5, 1)
    crowd = np.stack([reverb(crowd[:, c], rng, 1.6, 0.4)[:n, c] for c in range(2)], 1)
    put(np.stack([fade(crowd[:, c], 0.25, 0.2) for c in range(2)], 1) * 0.11, st[6])
    # 08 тяжёлое скольжение шкафа + глухой стук в конце
    rng = R(8); a, b = 0.42 * du[7], 0.86 * du[7]; n = int((b - a) * SR); tt = np.arange(n) / SR
    grain = np.clip(filt(rng.standard_normal(n), "lowpass", 45, 2) * 8, 0, 1)
    slide = (filt(rng.standard_normal(n), "lowpass", 260, 3) * 1.5 + filt(rng.standard_normal(n), "bandpass", [180, 900], 2) * grain)
    put(reverb(fade(slide, 0.08, 0.05), rng, 0.6, 0.25) * 0.45, st[7] + a)
    put(thump(rng, int(0.8 * SR), 60, 0.3) * 0.5, st[7] + b)
    # 09 далёкий гул пожара + ветер
    rng = R(9); n = int((du[8] + 0.2) * SR)
    roar = filt(np.cumsum(rng.standard_normal(n)) * 0.02, "bandpass", [40, 450], 2)
    roar = roar / (np.abs(roar).max() + 1e-9)
    crack = np.zeros(n)
    for _ in range(int(du[8] * 18)):
        s = rng.integers(0, n - 400); crack[s:s + 300] += rng.standard_normal(300) * np.exp(-np.arange(300) / 40) * rng.uniform(0.2, 1)
    crack = filt(crack, "bandpass", [1200, 6000], 2)
    fire = reverb(roar * 0.8 + crack * 0.25, rng, 2.0, 0.55)[:n]
    w = wind(rng, n, 250, 900, 0.25)
    sfx9 = fire * 0.5 + w * 0.12
    put(np.stack([fade(sfx9[:, c], 0.3, 0.3) for c in range(2)], 1) * 0.6, st[8])
    # 10 тихая комната: еле слышный фон
    rng = R(10); n = int(du[9] * SR)
    put(fade(filt(rng.standard_normal(n), "lowpass", 180, 2), 0.3, 0.3) * 0.05, st[9])
    # 11 три тяжёлых удара в дверь
    rng = R(11)
    for k in KNOCKS:
        put(reverb(thump(rng, int(0.9 * SR)), rng, 0.7, 0.3) * 0.55, st[10] + k)
    # 12–13 ветер на крыше
    rng = R(12); n = int((du[11] + du[12] + 0.2) * SR)
    w = wind(rng, n, 350, 1600, 0.35)
    put(np.stack([fade(w[:, c], 0.4, 0.4) for c in range(2)], 1) * 0.16, st[11])
    # 14 удар-акцент на вопросе
    rng = R(14); n = int(2.6 * SR); tt = np.arange(n) / SR
    sub = np.sin(2 * np.pi * (70 * np.exp(-tt * 1.3) + 32) * tt) * np.exp(-tt / 0.7)
    hit = sub * 1.3 + metal_hit(rng, n, 120, 0.9) * 0.5
    put(reverb(hit, rng, 1.8, 0.35) * 0.5, st[13] + 0.02)
    tail = wind(rng, int(du[13] * SR), 350, 1400, 0.3)
    put(np.stack([fade(tail[:, c], 0.5, 1.0) for c in range(2)], 1) * 0.07, st[13])
    return mix


def load_wav48(path):
    tmp = path + ".48k.wav"
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", path, "-ar", str(SR), "-ac", "2", tmp], check=True)
    sr, x = wavfile.read(tmp); os.remove(tmp)
    return x.astype(np.float64) / 32768.0


def build_audio(voices, starts_f, total_f, lens, out_wav):
    N = int(round(total_f / FPS * SR))
    sfx = build_sfx(starts_f, total_f, lens)[:N]
    voice = np.zeros((N, 2))
    for i, p in enumerate(voices):
        if p is None: continue
        v = load_wav48(p); s = int(round(starts_f[i] / FPS * SR)); e = min(N, s + len(v))
        voice[s:e] += v[: e - s]
    # ducking: огибающая голоса -> -10 дБ на эффектах
    env = np.abs(voice).max(1)
    hop = 480; fr = np.array([env[k:k + hop].max() if k < N else 0 for k in range(0, N, hop)])
    active = (fr > 0.01).astype(float)
    # атака 30 мс, отпускание 300 мс
    g = np.zeros_like(active); cur = 0.0
    for k, a in enumerate(active):
        cur = cur + (a - cur) * (0.3 if a > cur else 0.035); g[k] = cur
    gain_db = -10.0 * g
    gain = np.interp(np.arange(N), np.arange(len(g)) * hop, 10 ** (gain_db / 20))
    mix = voice * 1.0 + sfx * gain[:, None] * 0.8
    pk = np.abs(mix).max()
    if pk > 0.98: mix *= 0.98 / pk
    wavfile.write(out_wav, SR, (mix * 32767).astype(np.int16))


# ---------------------------------------------------------------- графика
def text_w(d, s, f, stroke=0):
    b = d.textbbox((0, 0), s, font=f, stroke_width=stroke)
    return b[2] - b[0]


def render_sub(i):
    """Субтитр сцены i: RGBA, центр по горизонтали."""
    text, hl = SCENES[i][1], SCENES[i][2]
    words = text.split(" "); hw = hl.split(" ")
    flags = [False] * len(words)
    for k in range(len(words) - len(hw) + 1):
        if words[k:k + len(hw)] == hw:
            for j in range(len(hw)): flags[k + j] = True
    last = i == len(SCENES) - 1
    size = 96
    stroke = 12
    tmp = ImageDraw.Draw(Image.new("RGBA", (10, 10)))

    def fnt(f):
        return font("black", int(size * 1.25) if (last and f) else size)

    def line_w(idx):
        sp = text_w(tmp, " ", fnt(False))
        return sum(text_w(tmp, words[k], fnt(flags[k]), stroke) - 2 * stroke for k in idx) + sp * (len(idx) - 1) + 2 * stroke

    lines = [list(range(len(words)))]
    if line_w(lines[0]) > 980 and len(words) > 1:
        best = None
        for c in range(1, len(words)):
            m = max(line_w(list(range(c))), line_w(list(range(c, len(words)))))
            if best is None or m < best[0]: best = (m, c)
        c = best[1]; lines = [list(range(c)), list(range(c, len(words)))]
    while max(line_w(l) for l in lines) > 1010:
        size -= 4
    asc = fnt(True).getmetrics()[0] if last else fnt(False).getmetrics()[0]
    lh = int(asc * 1.12)
    Wd = max(line_w(l) for l in lines) + 20
    Hd = lh * len(lines) + 2 * stroke + 30
    im = Image.new("RGBA", (Wd, Hd), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sp = text_w(tmp, " ", fnt(False))
    for li, idx in enumerate(lines):
        x = (Wd - line_w(idx)) / 2 + 10 - 10
        base_y = 10 + stroke + li * lh + asc
        for k in idx:
            f = fnt(flags[k])
            col = (RED if last else YELLOW) if flags[k] else (255, 255, 255)
            d.text((x + stroke, base_y), words[k], font=f, fill=col + (255,), stroke_width=stroke,
                   stroke_fill=(0, 0, 0, 255), anchor="ls")
            x += text_w(d, words[k], f, stroke) - 2 * stroke + sp
    # мягкая тень
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0))
    sh.putalpha(im.getchannel("A").filter(ImageFilter.GaussianBlur(10)).point(lambda v: v * 0.6))
    out = Image.new("RGBA", (Wd, Hd + 8), (0, 0, 0, 0))
    out.alpha_composite(sh, (0, 8)); out.alpha_composite(im, (0, 0))
    return out


def render_static(i):
    """HUD (час, плашка, время) — RGBA на весь кадр."""
    im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    x0, y0 = 48, 120
    # верхняя тёмная подложка для читаемости
    grad = Image.new("L", (1, 360))
    for y in range(360): grad.putpixel((0, y), int(150 * (1 - y / 360) ** 1.6))
    im.paste(Image.new("RGBA", (W, 360), (0, 0, 0, 255)), (0, 0), grad.resize((W, 360)))
    f1 = font("black", 70)
    d.text((x0, y0), HOUR[i], font=f1, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0, 255))
    f2 = font("extra", 34)
    tw = text_w(d, PLACE[i], f2)
    d.rounded_rectangle([x0, y0 + 92, x0 + tw + 44, y0 + 92 + 54], 8, fill=(0, 0, 0, 170))
    d.rectangle([x0, y0 + 92, x0 + 8, y0 + 92 + 54], fill=YELLOW + (255,))
    d.text((x0 + 26, y0 + 92 + 27), PLACE[i], font=f2, fill=(255, 255, 255, 255), anchor="lm")
    f3 = font("black", 70)
    d.text((W - 48, y0), CLOCK[i], font=f3, fill=(255, 255, 255, 255), stroke_width=5, stroke_fill=(0, 0, 0, 255), anchor="ra")
    return im


def wrap(d, text, f, maxw):
    lines, cur = [], ""
    for w in text.split():
        t = (cur + " " + w).strip()
        if text_w(d, t, f) <= maxw: cur = t
        else: lines.append(cur); cur = w
    lines.append(cur)
    return lines


def render_fact(text):
    cw = 620; f = font("extra", 34); tmp = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
    lines = wrap(tmp, text, f, cw - 56)
    lh = 44; chh = 70 + len(lines) * lh + 28
    im = Image.new("RGBA", (cw + 20, chh + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    sh = Image.new("RGBA", im.size, (0, 0, 0, 0)); ImageDraw.Draw(sh).rounded_rectangle([6, 10, cw + 6, chh + 10], 18, fill=(0, 0, 0, 140))
    im.alpha_composite(sh.filter(ImageFilter.GaussianBlur(8)))
    d.rounded_rectangle([0, 0, cw, chh], 18, fill=(255, 255, 255, 245))
    fb = font("black", 30)
    d.rounded_rectangle([24, 22, 24 + text_w(d, "ФАКТ", fb) + 36, 22 + 46], 10, fill=RED + (255,))
    d.text((24 + 18, 22 + 23), "ФАКТ", font=fb, fill=(255, 255, 255, 255), anchor="lm")
    for k, l in enumerate(lines):
        d.text((28, 86 + k * lh), l, font=f, fill=(20, 20, 20, 255))
    return im


def threat_col(v):
    v = v / 100
    g, y, r = np.array([40, 200, 70]), np.array(YELLOW), np.array(RED)
    c = g + (y - g) * (v / 0.5) if v < 0.5 else y + (r - y) * ((v - 0.5) / 0.5)
    return tuple(int(a) for a in c)


def render_bar(v, pulse):
    bw, bh = 38, 420
    im = Image.new("RGBA", (170, bh + 140), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
    fl = font("black", 26)
    d.text((158, 22), "УГРОЗА", font=fl, fill=(255, 255, 255, 255), stroke_width=4, stroke_fill=(0, 0, 0, 255), anchor="rm")
    bx = 170 - 12 - bw; by = 50
    d.rounded_rectangle([bx - 5, by - 5, bx + bw + 5, by + bh + 5], 12, fill=(0, 0, 0, 170), outline=(255, 255, 255, 220), width=3)
    fh = int(bh * v / 100); col = threat_col(v)
    if fh > 0:
        d.rounded_rectangle([bx, by + bh - fh, bx + bw, by + bh], 8, fill=col + (255,))
    for k in range(1, 10):
        yy = by + bh * k // 10; d.line([bx, yy, bx + 10, yy], fill=(0, 0, 0, 120), width=2)
    fp = font("black", 36)
    d.text((158, by + bh + 42), f"{int(round(v))}%", font=fp, fill=col + (255,), stroke_width=5, stroke_fill=(0, 0, 0, 255), anchor="rm")
    return im


def prep_image(i):
    im = Image.open(os.path.join(ROOT, "imgs", f"{i+1:02d}.png")).convert("RGB")
    K = 1.25  # запас разрешения под наезд
    s = max(W * K / im.width, H * K / im.height)
    im = im.resize((int(round(im.width * s)), int(round(im.height * s))), Image.LANCZOS)
    im = im.filter(ImageFilter.UnsharpMask(radius=2.2, percent=70, threshold=2))
    return im, K


def shake_offset(i, t, dur):
    """смещение камеры в пикселях кадра"""
    def jit(seed, t, amp, f):
        r = np.random.default_rng(seed)
        ph = r.uniform(0, 6.3, 6); fr = f * r.uniform(0.6, 1.6, 6)
        return amp * sum(math.sin(2 * math.pi * fr[k] * t + ph[k]) for k in range(3)) / 2.2, \
            amp * sum(math.sin(2 * math.pi * fr[k] * t + ph[k]) for k in range(3, 6)) / 2.2
    if i == 1:   # удар-остановка: сильная затухающая + лёгкая постоянная
        a = 28 * math.exp(-t / 0.35) + 3
        return jit(21, t, a, 11)
    if i == 3:
        return jit(41, t, 9 + 4 * math.sin(2 * math.pi * 0.9 * t), 9)
    if i == 10:
        dx = dy = 0.0
        for k in KNOCKS:
            if t >= k:
                e = math.exp(-(t - k) / 0.14) * 30
                dx += e * math.sin(2 * math.pi * 13 * (t - k) + 1.0)
                dy += e * math.sin(2 * math.pi * 16 * (t - k))
        return dx, dy
    return 0.0, 0.0


def flicker(f_local):
    blk = f_local // 3
    r = np.random.default_rng(5000 + blk)
    v = r.random()
    if v < 0.45: return 0.0
    if v < 0.7: return 0.6
    return r.uniform(0.15, 0.5)


def render_video(starts_f, total_f, lens, out_path, audio_wav, draft_note=False):
    xs = (np.arange(W) - W / 2) / (W / 2); ys = (np.arange(H) - H / 2) / (H / 2)
    rr = np.sqrt(xs[None, :] ** 2 * 0.9 + ys[:, None] ** 2 * 0.75)
    ss = lambda a, b, x: np.clip((x - a) / (b - a), 0, 1) ** 2 * (3 - 2 * np.clip((x - a) / (b - a), 0, 1))
    vig = (1 - 0.42 * ss(0.45, 1.3, rr)).astype(np.float32)[:, :, None]
    redm = ss(0.35, 1.25, rr).astype(np.float32)[:, :, None]
    red = np.array([150, 0, 0], np.float32)
    gr = np.random.default_rng(77)
    grains = [gr.standard_normal((H // 2, W // 2)).astype(np.float32) for _ in range(8)]
    grains = [np.repeat(np.repeat(g, 2, 0), 2, 1)[:, :, None] * 7.0 for g in grains]

    imgs = [prep_image(i) for i in range(len(SCENES))]
    statics = [render_static(i) for i in range(len(SCENES))]
    subs = [render_sub(i) for i in range(len(SCENES))]
    facts = {k: render_fact(v) for k, v in FACTS.items()}

    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
           "-i", "-", "-i", audio_wav, "-map", "0:v", "-map", "1:a",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p", "-profile:v", "high",
           "-r", str(FPS), "-c:a", "aac", "-b:a", "192k", "-ar", str(SR), "-ac", "2",
           "-movflags", "+faststart", "-shortest", out_path]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    ends = starts_f[1:] + [total_f]
    for f in range(total_f):
        i = max(k for k in range(len(starts_f)) if starts_f[k] <= f)
        fl = f - starts_f[i]; nf = ends[i] - starts_f[i]
        t = fl / FPS; u = fl / max(nf - 1, 1)
        base, K = imgs[i]
        z = (1.0 + 0.12 * u) * (1.06 if i in SHAKE else 1.0)
        (fx0, fy0), (fx1, fy1) = FOCUS[i]
        e = smooth(u) if i in (0, 5, 12) else u
        fx = fx0 + (fx1 - fx0) * e; fy = fy0 + (fy1 - fy0) * e
        cw, ch = W * K / z, H * K / z
        sx, sy = shake_offset(i, t, nf / FPS)
        scale = cw / W
        cx = fx * base.width + sx * scale; cy = fy * base.height + sy * scale
        cx = min(max(cx, cw / 2), base.width - cw / 2); cy = min(max(cy, ch / 2), base.height - ch / 2)
        frame = base.resize((W, H), Image.BICUBIC, box=(cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2))
        a = np.asarray(frame, dtype=np.float32)
        if i == 1:
            a *= (1 - flicker(fl))
        if i in RED_VIG:
            pulse = 0.5 + 0.5 * math.sin(2 * math.pi * 1.3 * t - 1.2)
            al = redm * (0.35 + 0.35 * pulse)
            a = a * (1 - al) + red * al
        a *= vig
        # оверлеи
        ov = statics[i].copy()
        # шкала угрозы: плавно от предыдущего значения за 0.6 с
        v0 = THREAT[i - 1] if i > 0 else 0
        v = v0 + (THREAT[i] - v0) * smooth(t / 0.6)
        ov.alpha_composite(render_bar(v, 0), (W - 170 - 22, 640))
        if i in facts:
            fc = facts[i]; k = smooth((t - 0.35) / 0.3)
            if k > 0:
                tmpc = fc.copy(); tmpc.putalpha(tmpc.getchannel("A").point(lambda q: int(q * k)))
                ov.alpha_composite(tmpc, (int(-fc.width + (40 + fc.width) * k), 330))
        sb = subs[i]; k = min(t / 0.15, 1.0)
        sc = 0.7 + 0.3 * (1 - (1 - k) ** 3) + 0.06 * math.sin(math.pi * k) * (1 - k) * 0
        sbi = sb if sc >= 0.999 else sb.resize((max(1, int(sb.width * sc)), max(1, int(sb.height * sc))), Image.BICUBIC)
        ov.alpha_composite(sbi, (int(W / 2 - sbi.width / 2), int(1470 - sbi.height / 2)))
        o = np.asarray(ov, dtype=np.float32)
        oa = o[:, :, 3:4] / 255.0
        a = a * (1 - oa) + o[:, :, :3] * oa
        a += grains[f % 8]
        # белая вспышка на склейке
        if i > 0 and fl < 4:
            fa = 0.3 * (1 - fl / 4)
            a = a * (1 - fa) + 255 * fa
        p.stdin.write(np.clip(a, 0, 255).astype(np.uint8).tobytes())
        if f % 150 == 0: print(f"  кадр {f}/{total_f}", flush=True)
    p.stdin.close(); p.wait()
    if p.returncode: sys.exit("ffmpeg failed")


def loudnorm(in_wav, out_wav):
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", in_wav, "-af", "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json",
                        "-f", "null", "-"], capture_output=True, text=True)
    js = json.loads(r.stderr[r.stderr.rindex("{"):r.stderr.rindex("}") + 1])
    af = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={js['input_i']}:measured_TP={js['input_tp']}:"
          f"measured_LRA={js['input_lra']}:measured_thresh={js['input_thresh']}:offset={js['target_offset']}:linear=true")
    subprocess.run(["ffmpeg", "-y", "-v", "error", "-i", in_wav, "-af", af, "-ar", str(SR), "-ac", "2", out_wav], check=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--voice", default=os.path.join(ROOT, "voice"))
    ap.add_argument("--out", default=os.path.join(ROOT, "final_video.mp4"))
    ap.add_argument("--work", default="/tmp/zombie_build")
    ap.add_argument("--draft", action="store_true", help="без голоса, длительности по оценке")
    a = ap.parse_args()
    os.makedirs(a.work, exist_ok=True)
    voices, lens, starts_f, total_f = timeline(None if a.draft else a.voice)
    if not a.draft and any(v is None for v in voices):
        sys.exit("Нет файлов озвучки в " + a.voice + " — используйте --draft для черновика")
    print("сцены (старт, сек):", [round(s / FPS, 2) for s in starts_f], "итого", round(total_f / FPS, 2), "с")
    json.dump({"starts_f": starts_f, "total_f": total_f, "voice_len": lens}, open(os.path.join(a.work, "timeline.json"), "w"), indent=1)
    raw = os.path.join(a.work, "mix_raw.wav"); fin = os.path.join(a.work, "mix.wav")
    build_audio(voices, starts_f, total_f, lens, raw)
    loudnorm(raw, fin)
    render_video(starts_f, total_f, lens, a.out, fin)
    print("готово:", a.out)


if __name__ == "__main__":
    main()
