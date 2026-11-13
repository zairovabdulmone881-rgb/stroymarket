"""Синтез звука для роликов (только numpy). Запуск: python3 make_audio.py"""
import numpy as np, wave, os
SR = 44100
rng = np.random.default_rng(7)
HERE = os.path.dirname(os.path.abspath(__file__))

def buf(d): return np.zeros(int(d*SR))
def put(b, t, x, g=1.0):
    i = int(t*SR)
    if i >= len(b): return
    n = min(len(x), len(b)-i); b[i:i+n] += x[:n]*g
def tt(d): return np.arange(int(d*SR))/SR
def fft_filter(x, lo=None, hi=None):
    X = np.fft.rfft(x); f = np.fft.rfftfreq(len(x), 1/SR)
    if lo: X[f < lo] = 0
    if hi: X[f > hi] = 0
    return np.fft.irfft(X, len(x))
def tone(freq, d, attack=.005, decay=6, wave_='sine', vib=0):
    t = tt(d); ph = 2*np.pi*freq*t + (vib*np.sin(2*np.pi*5*t) if vib else 0)
    if wave_ == 'sine': s = np.sin(ph)
    elif wave_ == 'tri': s = 2/np.pi*np.arcsin(np.sin(ph))
    elif wave_ == 'saw': s = 2*((freq*t) % 1) - 1
    else: s = np.sign(np.sin(ph))
    env = np.minimum(1, t/attack) * np.exp(-decay*t)
    return s*env
def midi(n): return 440*2**((n-69)/12)
def noise(d): return rng.uniform(-1, 1, int(d*SR))

# ---- эффекты ----
def tick(): return fft_filter(noise(.02), lo=2500, hi=9000)*np.exp(-tt(.02)*220)*.9
def ding(f=1318): return tone(f, .7, decay=7, wave_='tri')*.8 + tone(f*2, .7, decay=10)*.25
def coin():
    out = buf(.4); put(out, 0, tone(1568, .12, decay=25, wave_='sq'), .4); put(out, .08, tone(2093, .32, decay=9, wave_='sq'), .35); return out
def kick(d=.35, f0=140, f1=42):
    t = tt(d); fr = f1 + (f0-f1)*np.exp(-t*28); ph = 2*np.pi*np.cumsum(fr)/SR
    return np.sin(ph)*np.exp(-t*9)
def hit():  # низкий удар + «хвост»
    return kick(1.2, 110, 36)*1.0 + fft_filter(noise(1.2), hi=600)*np.exp(-tt(1.2)*4)*.4
def scratch(d=.28):  # обрыв музыки: падающий «рекорд-скретч»
    t = tt(d); fr = 1800*np.exp(-t*9)+120; ph = 2*np.pi*np.cumsum(fr)/SR
    return (np.sign(np.sin(ph))*.35 + fft_filter(noise(d), lo=800)*.5)*np.exp(-t*7)
def sigh(d=1.4):  # вздох: шум с формантой, вдох→выдох
    t = tt(d); n = fft_filter(noise(d), lo=300, hi=2600)
    env = np.sin(np.pi*np.clip(t/d, 0, 1))**2 * np.exp(-t*1.2)
    n = n*env; v = tone(190, d, attack=.25, decay=3.2)*.18*np.exp(-t*.5)
    return n*1.1 + v
def glitch(d):
    out = buf(d); t = 0
    while t < d:
        L = rng.uniform(.012, .05)
        seg = np.sign(np.sin(2*np.pi*rng.uniform(80, 2500)*tt(L)))*.5 if rng.random() > .4 else noise(L)*.7
        put(out, t, seg*np.hanning(len(seg)), 1); t += L*rng.uniform(.6, 1.6)
    return out
def whoosh(d=.45, up=True):
    t = tt(d); n = fft_filter(noise(d), lo=400, hi=5000)
    env = (t/d)**1.5*np.exp(-((t/d)*3)) if up else np.exp(-t*7)
    return n*env*5 if up else n*env
def pop():
    out = buf(.18); put(out, 0, tone(520, .18, decay=22), .7); put(out, 0, fft_filter(noise(.05), lo=1200)*np.exp(-tt(.05)*80), .5); return out
def alarm_ring(d):
    out = buf(d); t = 0
    while t < d:
        for k in range(4): put(out, t+k*.07, tone(2100, .05, attack=.002, decay=30, wave_='sq')*.5)
        t += .5
    return out
def clock_tick(accent=False): return fft_filter(noise(.03), lo=1500, hi=6000)*np.exp(-tt(.03)*160)*(1.1 if accent else .7)

def pad(freqs, d, gain=.12):
    out = sum(tone(f, d, attack=.6, decay=.25, wave_='tri', vib=.4) for f in freqs)/len(freqs)
    return out*gain

def typing(b, text, start, cps, g=.35):
    for i, ch in enumerate(text):
        if ch != ' ': put(b, start + i/cps, tick(), g*rng.uniform(.7, 1.1))

def finalize(b, path, fade_in=.15, fade_out=.6):
    n = len(b); b = b.copy()
    b[:int(fade_in*SR)] *= np.linspace(0, 1, int(fade_in*SR))
    b[-int(fade_out*SR):] *= np.linspace(1, 0, int(fade_out*SR))
    b = np.tanh(b*1.2)/np.tanh(1.2); b = b/np.max(np.abs(b))*.85
    # лёгкая «комнатная» реверберация (несколько эхо)
    wet = np.zeros_like(b)
    for dly, g in ((.043, .28), (.071, .2), (.113, .14), (.167, .09)):
        k = int(dly*SR); wet[k:] += b[:-k]*g
    b = b + wet*.6; b = b/np.max(np.abs(b))*.85
    with wave.open(path, 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((b*32767).astype(np.int16).tobytes())

# ============ «ПЕРВАЯ ЗАРПЛАТА» (15 c) ============
def first_salary():
    b = buf(15)
    # 0–2.8 — бодрая музыка (пентатоника, 150 bpm) + монетки
    step = 60/150/2; scale = [0, 4, 7, 9, 12, 9, 7, 4]; root = 60
    t = .0; i = 0
    while t < 2.8:
        n = root + scale[i % 8] + (12 if (i//8) % 2 else 0)
        put(b, t, tone(midi(n), .22, decay=12, wave_='tri'), .38)
        if i % 2 == 0: put(b, t, tone(midi(root-12 + (0 if (i//8)%2==0 else 5)), .3, decay=7), .35)
        if i % 4 == 0: put(b, t, kick(.2, 120, 50), .6)
        if i % 4 == 2: put(b, t, fft_filter(noise(.08), lo=4000)*np.exp(-tt(.08)*45), .5)
        t += step; i += 1
    for ct in (.5, 1.1, 1.7, 2.3): put(b, ct, coin(), .5)
    put(b, 2.72, scratch(), .8)                  # обрыв музыки
    put(b, 2.72, glitch(.33), .45)               # глитч-переход
    # 3.0–3.5 — тишина (чёрный экран)
    put(b, 3.45, glitch(.2), .4)
    put(b, 3.5, hit(), .75)                      # удар в начале «реальности»
    put(b, 3.6, sigh(1.5), .9)                   # вздох
    # 3.5–12.2 — грустный тягучий бит: Am – F – C – G, пэд + медленный кик
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    for k, ct in enumerate(np.arange(3.5, 12.2, 2.2)):
        put(b, ct, pad([midi(n) for n in chords[k % 4]], 2.6), 1.0)
        put(b, ct, tone(midi(chords[k % 4][0]-12), 2.2, attack=.05, decay=1.6), .35)
    for bt in np.arange(3.9, 12.0, 1.1):
        put(b, bt, kick(.4, 90, 38), .55)
        put(b, bt+.55, fft_filter(noise(.1), lo=3500, hi=9000)*np.exp(-tt(.1)*40), .22)
    # уведомления телефона
    for nt in (4.0, 4.7, 5.4): put(b, nt, ding(1175), .55)
    put(b, 7.0, tone(90, 1.2, attack=.2, decay=1.5), .45)     # руки к лицу
    put(b, 8.0, ding(392), .25)                                 # «0 ₽»
    # печать текста
    typing(b, 'Ожидание: я получу первую зарплату и куплю ВСЁ!', .15, 22, .0)
    typing(b, 'Реальность:', 3.7, 14, .3)
    typing(b, 'Ты работаешь, чтобы жить, или живёшь, чтобы работать?', 6.4, 20, .35)
    typing(b, 'На что ушла твоя первая зарплата? Напиши в комментариях', 12.6, 18, .35)
    # финал
    put(b, 12.4, hit(), .6)
    put(b, 12.4, pad([midi(n) for n in (45, 52, 57)], 2.8), 1.1)
    finalize(b, os.path.join(HERE, 'first-salary.wav'), fade_out=.9)

# ============ «ДЕДЛАЙН» (18 c) ============
def deadline():
    b = buf(18)
    D0, DL, OUT = .8, 2.0, 14.8
    # фоновый лоу-фай луп: напряжение растёт к концу
    prog = lambda t: np.clip((t-D0)/(OUT-D0), 0, 1)
    chords = [(60, 64, 67), (57, 60, 64), (53, 57, 60), (55, 59, 62)]
    for k, ct in enumerate(np.arange(0, 14.8, 2.0)):
        p = prog(ct); sh = int(p*3)                  # транспонируем вверх к концу
        put(b, ct, pad([midi(n+sh) for n in chords[k % 4]], 2.3, .16), 1.0)
        put(b, ct, tone(midi(chords[k % 4][0]-12+sh), 1.9, attack=.02, decay=2), .3)
    for bt in np.arange(.8, 14.8, .5):
        p = prog(bt)
        put(b, bt, kick(.3, 110, 45), .35+.3*p)
        if int((bt-.8)/.5) % 2: put(b, bt, fft_filter(noise(.07), lo=4500)*np.exp(-tt(.07)*50), .22+.2*p)
    # тиканье часов — всё чаще
    t = .8
    while t < 15:
        put(b, t, clock_tick(int(t*2) % 2 == 0), .4)
        t += 0.5 - 0.3*prog(t)
    # смена дня: поп + свуш
    for i in range(7):
        ts = D0 + i*DL
        put(b, ts-.02, pop(), .5); put(b, ts, whoosh(.4, False), .35)
        put(b, ts+.9, ding(880 + 60*i), .12)
    # печать реплик по дням
    lines = [['По плану', 'День 2. По плану', 'Всё по графику', 'Уже половина', 'Почти готово', 'Проверяю', 'Сдано'],
             ['Начну завтра', 'Время есть', 'Завтра точно', 'Сначала отдых', 'Ещё чуть-чуть', 'Начинаю', 'Только кофе'],
             ['Z z z', 'Z z z', 'Не успею', 'Всё пропало', 'Сколько осталось', 'ААААА', 'Я не спал']]
    for col in lines:
        for i, s in enumerate(col): typing(b, s, D0 + i*DL + .05, 26, .18)
    # Паникёр просыпается — «ой!»
    put(b, D0 + 2*DL - .05, tone(300, .35, decay=6, vib=12), .3)
    put(b, D0 + 2*DL - .05, whoosh(.3, True), .3)
    # будильник звонит с 5-го дня
    put(b, D0 + 4*DL, alarm_ring(OUT-(D0+4*DL)), .28)
    # финал: удар, пэд, печать CTA
    put(b, OUT, hit(), .9)
    put(b, OUT, scratch(.3), .35)
    put(b, OUT+.3, pad([midi(n) for n in (45, 52, 57, 60)], 3.0, .2), 1.0)
    typing(b, 'Ты кто из них?', OUT+1.2, 20, .4)
    typing(b, 'Контролёр, Прокрастинатор или Паникёр? Напиши в комментариях', OUT+2.4, 24, .35)
    finalize(b, os.path.join(HERE, 'deadline-gold.wav'), fade_out=.8)

if __name__ == '__main__':
    first_salary(); deadline(); print('ok')
