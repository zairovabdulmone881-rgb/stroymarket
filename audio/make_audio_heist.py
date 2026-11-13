"""Звук для ролика «Ограбление века» (12 c). Запуск: python3 make_audio_heist.py"""
import os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_audio import *   # noqa

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

def heist():
    b = buf(12)
    # --- сцена 1 (0–3): тиканье часов, тёмный гул, пульс-бит, который затихает на глитче
    t = .1
    while t < 3.0:
        put(b, t, clock_tick(int(t*2) % 2 == 0), .9); t += .5
    put(b, 0, fft_filter(tone(55, 3.0, attack=.8, decay=0, wave_='saw'), hi=220), .35)
    put(b, .3, pad([midi(n) for n in (50, 57, 62)], 3.0, .14), 1.0)
    for bt in np.arange(.9, 3.0, .6): put(b, bt, kick(.3, 100, 42), .55)
    put(b, .7, riser(.35, 300, 1800), .3)
    put(b, 1.0, shimmer(), .6); put(b, 1.0, hit(), .55)                    # золотая вспышка
    typing(b, 'СНАРУЖИ: Ограбление века', 1.0, 20, .38)
    typing(b, '5 минут до приезда полиции', 2.2, 34, .25)
    # --- глитч-переход 3.0–3.3: резкий звук, бит обрывается
    put(b, 2.99, glitch(.3), .75); put(b, 3.0, scratch(.3), .55)
    # --- сцена 2 (3.3–8.0): грустное пианино (Am – F – C – G) + струнный пэд
    prog = [((57, 60, 64), 76), ((53, 57, 60), 72), ((48, 52, 55), 72), ((55, 59, 62), 74)]
    for k, (ch, mel) in enumerate(prog):
        ct = 3.3 + k*1.2
        for j, n in enumerate(ch): put(b, ct + j*.18, piano(midi(n-12 if j == 0 else n), 2.0, .45))
        put(b, ct + .6, piano(midi(mel), 1.8, .5))
        put(b, ct, piano(midi(ch[0]-24), 2.4, .5))
    put(b, 3.3, strings([midi(n) for n in (45, 52, 57)], 4.7, .22), 1.0)
    typing(b, 'ВНУТРИ: Это не ограбление', 3.5, 12, .0)
    put(b, 4.0, whoosh(.5, True), .25)                                      # конверт
    put(b, 5.1, tone(220, .3, decay=12), .3)                                # кассир принимает
    put(b, 5.35, timpani(), .55)
    put(b, 5.4, ding(1319), .4); put(b, 5.55, ding(1760), .3)               # уведомление телефона
    # --- сцена 3 (8–12): музыка нарастает, обрыв на слове «комментах»
    put(b, 7.9, hit(), .5)
    put(b, 8.3, strings([midi(n) for n in (45, 52, 57, 60)], 3.2, .3), 1.0)
    put(b, 8.4, riser(3.0, 180, 2600), .45)
    for k, bt in enumerate(np.arange(8.9, 11.4, 1.0)):
        for j in range(4): put(b, bt + j*.25*(1-k*.12), kick(.25, 100, 45), .35 + k*.12)
    for k, (ch, mel) in enumerate(prog[:3]):
        put(b, 8.7 + k*.9, piano(midi(mel+5), 1.0, .4))
    typing(b, 'Он преступник или единственный честный человек в этом городе?', 9.0, 34, .30)
    typing(b, 'Пиши в комментах', 10.75, 22, .32)
    # обработка + реверберация + ЖЁСТКИЙ обрыв музыки
    n = len(b); b = b.copy()
    b[:int(.15*SR)] *= np.linspace(0, 1, int(.15*SR))
    b = np.tanh(b*1.2)/np.tanh(1.2)
    wet = np.zeros_like(b)
    for dly, g in ((.043, .28), (.071, .2), (.113, .14), (.167, .09)):
        k = int(dly*SR); wet[k:] += b[:-k]*g
    b = b + wet*.6
    cut = int(11.45*SR); b[cut:] = 0; b[cut-int(.01*SR):cut] *= np.linspace(1, 0, int(.01*SR))
    # после обрыва — только тихие щелчки печати подписи
    tail = buf(12); typing(tail, 'Продолжение — завтра.', 11.5, 40, .1)
    b = b/np.max(np.abs(b))*.85 + tail
    b[-int(.25*SR):] *= np.linspace(1, 0, int(.25*SR))
    with wave.open(os.path.join(HERE, 'heist.wav'), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(b, -1, 1)*32767).astype(np.int16).tobytes())

if __name__ == '__main__': heist(); print('ok')
