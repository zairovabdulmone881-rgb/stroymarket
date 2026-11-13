"""Звук для ролика «Ограбление века» (25 c). Запуск: python3 make_audio_heist.py"""
import os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_audio import *   # noqa

DUR = 25
def piano(freq, d=2.4, g=1.0):
    t = tt(d); s = (np.sin(2*np.pi*freq*t) + .45*np.sin(4*np.pi*freq*t)*np.exp(-t*3) + .2*np.sin(6*np.pi*freq*t)*np.exp(-t*5))
    return s*np.minimum(1, t/.004)*np.exp(-t*2.1)*g
def riser(d, f0=200, f1=2400):
    t = tt(d); fr = f0*(f1/f0)**(t/d); ph = 2*np.pi*np.cumsum(fr)/SR
    n = fft_filter(noise(d), lo=800)
    return (np.sin(ph)*.35 + n*.5)*(t/d)**2
def strings(freqs, d, g=.2):
    out = sum(tone(f, d, attack=1.2, decay=.35, wave_='saw', vib=.5) for f in freqs)/len(freqs)
    return fft_filter(out, hi=1800)*g
def timpani(): return kick(1.4, 95, 48)*1.0 + np.sin(2*np.pi*70*tt(1.4))*np.exp(-tt(1.4)*3)*.4
def shimmer(d=1.2):
    out = buf(d)
    for k in range(10): put(out, k*.04, tone(2000+k*330, .5, decay=9)*.2)
    return out
def step(g=1.0):
    out = buf(.16); put(out, 0, kick(.16, 95, 52), .8); put(out, 0, fft_filter(noise(.07), hi=700)*np.exp(-tt(.07)*60), .5)
    return out*g
def siren(d):
    t = tt(d); f = 700 + 320*np.sin(2*np.pi*.8*t); ph = 2*np.pi*np.cumsum(f)/SR
    s = 2/np.pi*np.arcsin(np.sin(ph)) + .3*np.sin(2*ph)
    env = np.minimum(1, t/.6)*np.minimum(1, (d-t)/.35)
    return fft_filter(s, hi=3500)*env
def dip(d=.8):   # затемнение между сценами: «вдох» и низкий провал
    out = buf(d); put(out, 0, whoosh(d*.6, False), .8); put(out, 0, tone(58, d, attack=.02, decay=4), .5); return out

def heist():
    b = buf(DUR)
    # ---------- шаги ----------
    k = 0
    while .5 + k/2.6 < 2.45: put(b, .5 + k/2.6, step(.25 + .5*(k/5)), 1.0); k += 1
    k = 0
    while 3.3 + k/3.2 < 4.35: put(b, 3.3 + k/3.2, step(.5), 1.0); k += 1
    # ---------- СЦЕНА 1 (0–3): тиканье, гул, бит ----------
    t = .1
    while t < 3.0: put(b, t, clock_tick(int(t*2) % 2 == 0), .9); t += .5
    put(b, 0, fft_filter(tone(55, 3.0, attack=.8, decay=0, wave_='saw'), hi=220), .35)
    put(b, .3, pad([midi(n) for n in (50, 57, 62)], 3.0, .14), 1.0)
    for bt in np.arange(.9, 3.0, .6): put(b, bt, kick(.3, 100, 42), .55)
    put(b, .7, riser(.35, 300, 1800), .3)
    put(b, 1.0, shimmer(), .6); put(b, 1.0, hit(), .55)
    typing(b, 'СНАРУЖИ: Ограбление века', 1.0, 20, .38)
    typing(b, '5 минут до приезда полиции', 2.2, 34, .25)
    put(b, 2.99, glitch(.3), .75); put(b, 3.0, scratch(.3), .55)       # глитч, бит обрывается
    # ---------- СЦЕНА 2 (3.3–8): грустное пианино ----------
    prog = [((57, 60, 64), 76), ((53, 57, 60), 72), ((48, 52, 55), 72), ((55, 59, 62), 74)]
    for k, (ch, mel) in enumerate(prog):
        ct = 3.3 + k*1.4
        for j, n in enumerate(ch): put(b, ct + j*.2, piano(midi(n-12 if j == 0 else n), 2.2, .45))
        put(b, ct + .7, piano(midi(mel), 2.0, .5)); put(b, ct, piano(midi(ch[0]-24), 2.6, .5))
    put(b, 3.3, strings([midi(n) for n in (45, 52, 57)], 5.0, .22), 1.0)
    put(b, 4.0, whoosh(.5, True), .25)
    put(b, 5.1, tone(220, .3, decay=12), .3)
    put(b, 5.35, timpani(), .55); put(b, 5.4, ding(1319), .4); put(b, 5.55, ding(1760), .3)
    put(b, 7.95, dip(), .8)
    # ---------- «ВЫПИСКА» (8.8–12.6): холодный пульс, печать, баланс ----------
    put(b, 8.8, pad([midi(n) for n in (45, 52, 55)], 4.2, .2), 1.0)
    for bt in np.arange(8.9, 12.5, .6): put(b, bt, kick(.3, 95, 40), .45)
    for i, rt in enumerate((9.4, 9.9, 10.4)): put(b, rt, ding(784 + i*60), .28); put(b, rt, tick(), .6)
    put(b, 10.95, fft_filter(tone(233, .6, wave_='sq', decay=4), hi=1400), .35)
    put(b, 10.95, tick(), .6)
    put(b, 11.5, hit(), 1.0); put(b, 11.5, scratch(.3), .5); put(b, 11.5, glitch(.12), .35)
    for i, tk in enumerate(np.arange(11.55, 12.45, 1/22)): put(b, tk, tick(), .45 - .2*(i/20))
    put(b, 12.55, dip(), .8)
    # ---------- «ПОЛИЦИЯ» (13.4–17): сирена, пульс, тишина после слов ----------
    put(b, 13.4, siren(3.6), .32)
    put(b, 13.4, fft_filter(tone(55, 3.6, attack=.5, decay=0, wave_='saw'), hi=220), .35)
    bt, gap = 13.5, .8
    while bt < 16.9: put(b, bt, kick(.35, 90, 38), .5); put(b, bt+.2, kick(.3, 80, 36), .3); bt += gap
    typing(b, 'ПОЛИЦИЯ ПРИЕХАЛА', 13.6, 14, .35)
    put(b, 15.3, piano(midi(57), 2.4, .5), 1.0); put(b, 16.1, piano(midi(64), 2.4, .5), 1.0)
    put(b, 16.95, dip(), .8)
    # ---------- ФИНАЛ (17.4–25): музыка нарастает, обрыв на «комментах» ----------
    put(b, 17.35, hit(), .5)
    put(b, 17.5, strings([midi(n) for n in (45, 52, 57, 60)], 5.4, .3), 1.0)
    put(b, 17.6, riser(4.8, 180, 2600), .45)
    for k, bt in enumerate(np.arange(18.4, 22.8, 1.1)):
        for j in range(4): put(b, bt + j*.25*(1-k*.1), kick(.25, 100, 45), .3 + k*.1)
    for k, (ch, mel) in enumerate(prog):
        put(b, 18.1 + k*1.1, piano(midi(mel+5), 1.2, .4))
    typing(b, 'Он преступник или единственный честный человек в этом городе?', 17.9, 30, .30)
    typing(b, 'Пиши в комментах', 21.6, 15, .32)
    # ---------- обработка, реверберация, жёсткий обрыв ----------
    b = b.copy()
    b[:int(.15*SR)] *= np.linspace(0, 1, int(.15*SR))
    b = np.tanh(b*1.2)/np.tanh(1.2)
    wet = np.zeros_like(b)
    for dly, g in ((.043, .28), (.071, .2), (.113, .14), (.167, .09)):
        k = int(dly*SR); wet[k:] += b[:-k]*g
    b = b + wet*.6
    cut = int(22.8*SR); b[cut:] = 0; b[cut-int(.01*SR):cut] *= np.linspace(1, 0, int(.01*SR))
    tail = buf(DUR); typing(tail, 'Продолжение — завтра.', 23.3, 40, .1)
    b = b/np.max(np.abs(b))*.85 + tail
    b[-int(.25*SR):] *= np.linspace(1, 0, int(.25*SR))
    with wave.open(os.path.join(HERE, 'heist.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(b, -1, 1)*32767).astype(np.int16).tobytes())

if __name__ == '__main__': heist(); print('ok')
