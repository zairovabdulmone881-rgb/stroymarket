"""Синтез звуковых эффектов (без музыки, без внешних сэмплов). Всё — моно float32, 48 кГц."""
import numpy as np
from scipy import signal

SR = 48000
rng = np.random.default_rng(7)


def t_(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR)).astype(np.float32)


def pink(d):
    n = int(d * SR)
    f = np.fft.rfftfreq(n, 1 / SR); f[0] = 1
    x = np.fft.irfft(np.fft.rfft(rng.standard_normal(n)) / np.sqrt(f), n)
    return (x / (np.abs(x).max() + 1e-9)).astype(np.float32)


def bp(x, lo, hi, order=2):
    sos = signal.butter(order, [lo, hi], "bandpass", fs=SR, output="sos")
    return signal.sosfilt(sos, x).astype(np.float32)


def lp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "lowpass", fs=SR, output="sos"), x).astype(np.float32)


def hp(x, f, order=2):
    return signal.sosfilt(signal.butter(order, f, "highpass", fs=SR, output="sos"), x).astype(np.float32)


def env_ad(n, a, d):
    """атака a c, экспоненциальный спад d c"""
    t = np.arange(n) / SR
    e = np.minimum(1, t / max(a, 1e-4)) * np.exp(-np.maximum(0, t - a) / d)
    return e.astype(np.float32)


def fade(x, fi=0.05, fo=0.1):
    x = x.copy(); n = len(x)
    a, b = min(n, int(fi * SR)), min(n, int(fo * SR))
    if a: x[:a] *= np.linspace(0, 1, a)
    if b: x[-b:] *= np.linspace(1, 0, b)
    return x


def slow_mod(d, rate, depth=1.0):
    """плавная случайная огибающая 0..1"""
    n = int(d * SR); k = max(4, int(d * rate) + 4)
    pts = rng.random(k)
    m = np.interp(np.linspace(0, k - 1, n), np.arange(k), pts)
    return (1 - depth + depth * m).astype(np.float32)


def reverb(x, d=0.8, mix=0.3):
    ir = noise(d) * np.exp(-np.arange(int(d * SR)) / SR / (d / 5))
    ir = lp(ir, 5000)
    w = signal.fftconvolve(x, ir)[: len(x) + len(ir)]
    w = w / (np.abs(w).max() + 1e-9) * np.abs(x).max()
    out = np.zeros(len(w), np.float32); out[: len(x)] += x * (1 - mix)
    return (out + w * mix).astype(np.float32)


def place(dst, src, at):
    i = int(at * SR)
    if i >= len(dst): return
    if i < 0: src, i = src[-i:], 0
    n = min(len(src), len(dst) - i)
    dst[i:i + n] += src[:n]


# ---------- эффекты ----------
def vibration(d=1.6):
    """вибрация телефона: два «бзз» по 0.45 с"""
    out = np.zeros(int(d * SR), np.float32)
    for k, st in enumerate((0.0, 0.75)):
        t = t_(0.45)
        f0 = 165
        buzz = np.sign(np.sin(2 * np.pi * f0 * t)) * 0.6 + np.sin(2 * np.pi * 2 * f0 * t) * 0.3
        rattle = bp(noise(0.45), 180, 1400) * (0.5 + 0.5 * np.sin(2 * np.pi * f0 * t))
        x = lp((buzz + rattle * 0.8).astype(np.float32), 2500)
        place(out, fade(x, 0.02, 0.04), st)
    return out


def crowd(d, bright=1.0):
    out = np.zeros(int(d * SR), np.float32)
    for _ in range(14):
        f = rng.uniform(350, 1100)
        v = bp(noise(d), f * 0.7, f * 1.9) * slow_mod(d, rng.uniform(3, 7), 0.9) ** 2
        out += v * rng.uniform(0.4, 1)
    out += lp(pink(d), 300) * 0.6 * bright
    return fade(out / (np.abs(out).max() + 1e-9), 0.4, 0.4)


def helicopter(d):
    t = t_(d)
    rot = 11.5
    pulse = np.maximum(0, np.sin(2 * np.pi * rot * t)) ** 6
    x = lp(noise(d), 500) * (0.25 + pulse) + np.sin(2 * np.pi * 46 * t) * 0.2 * pulse
    pas = np.exp(-((t - d * 0.55) / (d * 0.35)) ** 2)  # пролёт
    return fade(lp(x.astype(np.float32), 1200) * pas.astype(np.float32), 0.3, 0.5)


def beep(f, d, sq=False):
    t = t_(d)
    w = np.sign(np.sin(2 * np.pi * f * t)) * 0.5 if sq else np.sin(2 * np.pi * f * t)
    return fade(w.astype(np.float32), 0.005, 0.01)


def store(d):
    out = crowd(d) * 0.8
    for st in np.arange(0.6, d - 0.3, rng.uniform(1.1, 1.7)):
        place(out, beep(2350, 0.09) * 0.35, st + rng.uniform(-0.2, 0.2))
    # тележка
    for st in (d * 0.3, d * 0.7):
        rat = bp(noise(0.7), 900, 4000) * (rng.random(int(0.7 * SR)) > 0.92) * 3
        place(out, fade(rat.astype(np.float32), 0.05, 0.2) * 0.4, st)
    return out


def shout(d=0.75):
    """крик «Эй!» — пила с формантами"""
    t = t_(d)
    f0 = np.interp(t, [0, 0.12, 0.45, d], [230, 330, 300, 220]) * (1 + 0.02 * np.sin(2 * np.pi * 6 * t))
    ph = 2 * np.pi * np.cumsum(f0) / SR
    saw = (2 * ((ph / (2 * np.pi)) % 1) - 1).astype(np.float32)
    v = sum(bp(saw, F * 0.85, F * 1.15) * g for F, g in ((600, 1), (1750, 0.7), (2600, 0.4)))
    v += bp(noise(d), 1500, 4000) * 0.15
    v = np.tanh(v * 3) * env_ad(len(v), 0.03, 0.5)
    return reverb(fade(v.astype(np.float32), 0.01, 0.15), 0.9, 0.35)


def terminal(d=2.2):
    """отказ терминала: пик-пик … пиииу"""
    out = np.zeros(int(d * SR), np.float32)
    for st in (0.0, 0.22):
        place(out, beep(1850, 0.12, True) * 0.6, st)
    place(out, beep(1200, 0.25, True) * 0.6, 0.6)
    place(out, beep(800, 0.45, True) * 0.6, 0.88)
    return lp(out, 6000)


def horn(f, d):
    t = t_(d)
    w = np.sign(np.sin(2 * np.pi * f * t)) + np.sign(np.sin(2 * np.pi * f * 1.26 * t))
    return fade(lp(w.astype(np.float32), 2200), 0.02, 0.06)


def traffic(d, n_horns=6):
    out = lp(pink(d), 250) * 0.5 + lp(noise(d), 120) * 0.2
    out = out.astype(np.float32)
    for _ in range(n_horns):
        hd = rng.uniform(0.25, 0.8)
        g = rng.uniform(0.15, 0.4)
        place(out, horn(rng.uniform(330, 470), hd) * g, rng.uniform(0, max(0.1, d - hd)))
    return fade(out, 0.3, 0.4)


def hammer_hit():
    n = int(0.35 * SR); t = np.arange(n) / SR
    thump = np.sin(2 * np.pi * 95 * t) * np.exp(-t / 0.05)
    crack = bp(noise(0.35), 300, 3500) * np.exp(-t / 0.018)
    wood = np.sin(2 * np.pi * 420 * t) * np.exp(-t / 0.04) * 0.4
    return (thump + crack * 1.6 + wood).astype(np.float32)


def hammering(d):
    out = np.zeros(int(d * SR), np.float32)
    st = 0.05
    while st < d - 0.4:
        for k in range(rng.integers(2, 4)):
            place(out, hammer_hit() * rng.uniform(0.7, 1), st); st += rng.uniform(0.3, 0.42)
        st += rng.uniform(0.5, 0.9)
    return reverb(out, 0.5, 0.2)[: len(out)]


def knock():
    n = int(0.3 * SR); t = np.arange(n) / SR
    x = np.sin(2 * np.pi * 105 * t) * np.exp(-t / 0.045) + bp(noise(0.3), 150, 1200) * np.exp(-t / 0.02) * 1.2
    x += np.sin(2 * np.pi * 240 * t) * np.exp(-t / 0.03) * 0.5
    return x.astype(np.float32)


def three_knocks():
    out = np.zeros(int(1.6 * SR), np.float32)
    for st in (0.0, 0.34, 0.68):
        place(out, knock(), st)
    return reverb(out, 0.6, 0.25)[: len(out)]


def radio(d):
    x = bp(noise(d), 600, 3800) * (0.5 + 0.5 * slow_mod(d, 9, 1))
    crack = (rng.random(int(d * SR)) > 0.9993).astype(np.float32)
    crack = bp(signal.lfilter([1], [1, -0.97], crack).astype(np.float32), 800, 5000) * 6
    t = t_(d)
    whistle = np.sin(2 * np.pi * np.cumsum(1400 + 600 * np.sin(2 * np.pi * 0.4 * t)) / SR) * 0.08
    x = x + crack + whistle.astype(np.float32)
    return fade(np.tanh(x * 1.5).astype(np.float32), 0.15, 0.4)


def growl(d):
    t = t_(d)
    fr = 28 + 8 * np.sin(2 * np.pi * 0.7 * t)
    pulses = np.maximum(0, np.sin(2 * np.pi * np.cumsum(fr) / SR)) ** 4
    x = lp(noise(d), 700) * (0.3 + pulses)
    x = bp(x.astype(np.float32), 80, 900) + bp(x.astype(np.float32), 350, 650) * 0.8
    e = np.sin(np.pi * np.clip(t / d, 0, 1)) ** 0.7
    return reverb(fade((np.tanh(x * 2) * e).astype(np.float32), 0.2, 0.4), 1.2, 0.45)


def breathing(d):
    out = np.zeros(int(d * SR), np.float32)
    st = 0.0
    while st < d - 1.0:
        for ln, (lo, hi) in ((1.1, (700, 2600)), (1.5, (400, 1800))):
            n = int(ln * SR)
            e = np.sin(np.pi * np.arange(n) / n) ** 2
            place(out, bp(noise(ln), lo, hi) * e.astype(np.float32), st); st += ln + 0.15
        st += 0.4
    return out


def ringing(d):
    t = t_(d)
    tone = np.sin(2 * np.pi * (4300 + 15 * np.sin(2 * np.pi * 5 * t)) * t) * 0.35
    rumble = lp(noise(d), 80) * 2
    e = np.clip(t / (d * 0.7), 0, 1) ** 1.5
    return fade(((tone + rumble) * e).astype(np.float32), 0.05, 0.3)


def hit(d=2.0):
    n = int(d * SR); t = np.arange(n) / SR
    f = 110 * np.exp(-t / 0.25) + 38
    boom = np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.55)
    click = lp(noise(d), 3000) * np.exp(-t / 0.03) * 1.2
    x = np.tanh((boom * 1.4 + click) * 1.5)
    return reverb(x.astype(np.float32), 1.5, 0.3)


def scratch(d):
    out = np.zeros(int(d * SR), np.float32)
    st = 0.0
    while st < d - 0.5:
        ln = rng.uniform(0.45, 0.8); n = int(ln * SR); t = np.arange(n) / SR
        e = np.sin(np.pi * t / ln) ** 0.8 * (0.6 + 0.4 * (rng.random(n) > 0.5))
        sq_f = rng.uniform(2300, 3400) + 300 * np.sin(2 * np.pi * rng.uniform(3, 7) * t)
        squeal = np.sin(2 * np.pi * np.cumsum(sq_f) / SR) * 0.25 * (np.sin(2 * np.pi * 37 * t) > 0)
        grit = bp(noise(ln), 1800, 7000) * (np.sin(2 * np.pi * rng.uniform(25, 45) * t) > 0.2)
        place(out, ((grit + squeal) * e).astype(np.float32), st)
        st += ln + rng.uniform(0.1, 0.4)
    return reverb(out, 0.7, 0.3)[: len(out)]


def whoosh(d=0.45):
    n = int(d * SR); x = noise(d)
    # бегущий полосовой фильтр через STFT
    f, tt, Z = signal.stft(x, SR, nperseg=1024)
    pos = np.linspace(0, 1, Z.shape[1])
    fc = 300 * (14 ** np.sin(np.pi * pos))           # 300 → 4 кГц → 300
    g = np.exp(-((np.log(f[:, None] + 1) - np.log(fc[None, :])) ** 2) / 0.5)
    _, y = signal.istft(Z * g * np.sin(np.pi * pos)[None, :] ** 2, SR, nperseg=1024)
    return fade(y[:n].astype(np.float32), 0.02, 0.05)
