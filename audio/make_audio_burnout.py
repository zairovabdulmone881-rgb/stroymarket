"""Звук для ролика «Выгорание» (15 c). Запуск: python3 make_audio_burnout.py"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_audio import *   # noqa: общие синтезаторы

def power_down(d=.7, f0=900, f1=120):
    t = tt(d); fr = f1 + (f0-f1)*np.exp(-t*5); ph = 2*np.pi*np.cumsum(fr)/SR
    return (np.sin(ph)*.6 + np.sign(np.sin(ph))*.15)*np.exp(-t*3.2)
def heartbeat():
    out = buf(.5); put(out, 0, kick(.25, 100, 40), .9); put(out, .17, kick(.25, 85, 38), .6); return out
def beep(d=.14, f=1000):
    return tone(f, d, attack=.003, decay=14, wave_='sq')*.35

def burnout():
    b = buf(15)
    # 0–3: бодрая музыка
    step = 60/145/2; scale = [0, 4, 7, 9, 12, 9, 7, 4]; root = 62; t = 0.; i = 0
    while t < 3.0:
        slow = 1 + max(0, t-2.4)*.5                      # к концу чуть «садится» темп
        put(b, t, tone(midi(root + scale[i % 8] - (1 if t > 2.7 else 0)), .22, decay=12, wave_='tri'), .38)
        if i % 4 == 0: put(b, t, kick(.2, 120, 50), .55)
        if i % 4 == 2: put(b, t, fft_filter(noise(.08), lo=4000)*np.exp(-tt(.08)*45), .45)
        t += step*slow; i += 1
    # 3–6.8: разрядка — «power down» на каждом шаге, пульс замедляется, гул растёт
    for k, ts in enumerate((3.0, 4.0, 5.0, 6.0)):
        put(b, ts, power_down(.8, 900-k*160, 150-k*20), .55)
    bt, gap = 3.2, .7
    while bt < 6.7:
        put(b, bt, heartbeat(), .45); bt += gap; gap *= 1.12
    put(b, 3.0, tone(55, 3.8, attack=1.5, decay=-.15, wave_='saw')*.0 + fft_filter(tone(55, 3.8, attack=1.5, decay=0, wave_='saw'), hi=300)*.25, 1.0)
    for k, n in enumerate(CFGN):
        put(b, n, ding(900 + k*70), .30)
    # краш
    put(b, 3.0, glitch(.1), .35); put(b, 6.0, glitch(.08), .3)
    put(b, 6.75, glitch(.3), .55); put(b, 6.78, hit(), .9); put(b, 6.78, scratch(.3), .5)
    # 7.05–7.4 тишина; затем грустная часть
    put(b, 7.4, sigh(1.6), .9)
    chords = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (55, 59, 62)]
    for k, ct in enumerate(np.arange(7.4, 11.0, 2.0)):
        put(b, ct, pad([midi(n) for n in chords[k % 4]], 2.8, .16), 1.0)
        put(b, ct, tone(midi(chords[k % 4][0]-12), 2.4, attack=.05, decay=1.5), .35)
    for hb in np.arange(8.0, 11.0, 1.4): put(b, hb, kick(.45, 85, 36), .35)
    # печать
    typing(b, 'Понедельник: я полон сил!', .15, 22, .30)
    typing(b, 'Работа. Дедлайны. Чаты. Ещё чуть-чуть…', 3.2, 19, .30)
    typing(b, 'Ты не ленивый. Ты выгорел.', 7.6, 16, .35)
    # финал: удар, пэд, «низкий заряд» — писк
    put(b, 11.0, hit(), .6); put(b, 11.0, pad([midi(n) for n in (45, 52, 57)], 3.5, .2), 1.0)
    typing(b, 'На сколько % твоя батарейка?', 11.9, 17, .38)
    typing(b, 'Напиши цифру в комментариях', 13.9, 20, .32)
    for bp in (11.8, 12.9, 14.0):
        put(b, bp, beep(.14, 1000), .5); put(b, bp+.2, beep(.14, 1000), .5)
    finalize(b, os.path.join(HERE, 'burnout.wav'), fade_out=.7)

CFGN = [3.3, 3.8, 4.3, 4.8, 5.3, 5.8, 6.2]
if __name__ == '__main__': burnout(); print('ok')
