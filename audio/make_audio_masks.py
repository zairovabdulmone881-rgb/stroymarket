"""Звук для серии «Снаружи / Внутри». Запуск: python3 make_audio_masks.py   → perfect-family.wav, successful.wav"""
import os, sys, wave
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from make_audio import *                     # noqa
from make_audio_heist import piano, riser, strings, step, dip, timpani, shimmer   # noqa

DUR = 20
def shutter(): 
    out = buf(.2); put(out, 0, fft_filter(noise(.02), lo=1500, hi=9000)*np.exp(-tt(.02)*140), 1.0); put(out, .07, fft_filter(noise(.03), lo=800, hi=7000)*np.exp(-tt(.03)*90), .8); return out
def heartbeat2(): 
    out = buf(.5); put(out, 0, kick(.25, 100, 40), 1.0); put(out, .16, kick(.25, 85, 38), .65); return out
def breath(d=.9, g=1.0):
    t = tt(d); n = fft_filter(noise(d), lo=400, hi=3000); return n*np.sin(np.pi*np.clip(t/d,0,1))**2*g
def kaching():
    out = buf(.9); put(out, 0, tick(), 1.0); put(out, .05, ding(2093), .5); put(out, .12, ding(2637), .5); return out
def drip():
    out = buf(.5); put(out, 0, tone(1900, .25, attack=.001, decay=22), .5); put(out, .04, tone(1300, .3, attack=.001, decay=18), .3); return out

def finale(b, q, cta, cps_q=30, cps_c=15):
    put(b, 12.35, hit(), .5)
    put(b, 12.5, strings([midi(n) for n in (45, 52, 57, 60)], 5.4, .3), 1.0)
    put(b, 12.6, riser(4.8, 180, 2600), .45)
    prog = [((57, 60, 64), 76), ((53, 57, 60), 72), ((48, 52, 55), 72), ((55, 59, 62), 74)]
    for k, bt in enumerate(np.arange(13.4, 17.8, 1.1)):
        for j in range(4): put(b, bt + j*.25*(1-k*.1), kick(.25, 100, 45), .3 + k*.1)
    for k, (ch, mel) in enumerate(prog): put(b, 13.1 + k*1.1, piano(midi(mel+5), 1.2, .4))
    typing(b, q, 12.9, cps_q, .30); typing(b, cta, 16.6, cps_c, .32)

def master(b, path, tail_text='Продолжение — завтра.'):
    b = b.copy(); b[:int(.15*SR)] *= np.linspace(0, 1, int(.15*SR))
    b = np.tanh(b*1.2)/np.tanh(1.2)
    wet = np.zeros_like(b)
    for dly, g in ((.043, .28), (.071, .2), (.113, .14), (.167, .09)):
        k = int(dly*SR); wet[k:] += b[:-k]*g
    b = b + wet*.6
    cut = int(17.9*SR); b[cut:] = 0; b[cut-int(.01*SR):cut] *= np.linspace(1, 0, int(.01*SR))   # жёсткий обрыв
    tail = buf(DUR); typing(tail, tail_text, 18.4, 40, .1)
    b = b/np.max(np.abs(b))*.85 + tail; b[-int(.25*SR):] *= np.linspace(1, 0, int(.25*SR))
    with wave.open(os.path.join(HERE, path), 'wb') as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR)
        w.writeframes((np.clip(b, -1, 1)*32767).astype(np.int16).tobytes())

def perfect_family():
    b = buf(DUR); mus = buf(DUR)
    for t0 in (.4, .75):
        for k in range(3): put(b, t0 + k/3.2, step(.45), 1.0)
    # тёплая музыка 0–4.6 (вальс 3/4, музыкальная шкатулка)
    beat = .667; mel = [76, 79, 81, 79, 76, 72, 74, 76]
    for k in range(int(4.6/beat)+1):
        t = k*beat
        put(mus, t, tone(midi(48 if k % 2 == 0 else 43), .6, decay=4, wave_='tri'), .5)
        for j in (1, 2): put(mus, t + j*beat/3, tone(midi(64 + j*3), .4, decay=7, wave_='tri'), .22)
        put(mus, t, tone(midi(mel[k % 8]), .9, decay=6), .28); put(mus, t+beat/2, tone(midi(mel[(k+3) % 8]+12), .7, decay=8), .14)
    put(mus, 0, pad([midi(n) for n in (48, 55, 64)], 4.6, .1), 1.0)
    mus[int(4.62*SR):] = 0; b += mus
    for f in (2.3, 3.7): put(b, f, shutter(), .9); put(b, f, shimmer(.8), .35)
    typing(b, 'СНАРУЖИ: Идеальная семья. 10 лет вместе', 1.0, 19, .38)
    put(b, 4.59, glitch(.3), .75); put(b, 4.6, scratch(.3), .55)
    # кухня ночью 4.9–12
    t = 4.9
    while t < 11.9: put(b, t, clock_tick(True), .8); t += 1.0
    put(b, 4.9, tone(100, 7, attack=.5, decay=0, wave_='saw')*.0 + fft_filter(tone(100, 7, attack=.5, decay=0, wave_='saw'), hi=260), .10)
    put(b, 5.45, ding(1760), .18)
    put(b, 6.0, piano(midi(40), 3.0, .8), 1.0); put(b, 6.0, breath(1.3, .9), .35); put(b, 6.0, tone(220, .5, decay=8), .2)
    ch = [(57, 60, 64), (53, 57, 60), (48, 52, 55), (52, 55, 59)]
    for k, c in enumerate(ch):
        ct = 5.0 + k*1.7
        for j, n in enumerate(c): put(b, ct + j*.35, piano(midi(n), 2.4, .4))
    for k in range(18): put(b, 7.0 + k/9, tick(), .5)                       # набор текста
    for k in range(20): put(b, 10.0 + k/14, tick(), .35)                    # стирание
    put(b, 11.5, piano(midi(45), 2.5, .6), 1.0)
    put(b, 11.95, dip(), .8)
    finale(b, 'Как думаешь, сколько таких «идеальных» пар прячутся за улыбками?', 'Пиши в комментах', 30, 15)
    master(b, 'perfect-family.wav')

def successful():
    b = buf(DUR); mus = buf(DUR)
    for k in range(3): put(b, .4 + k/3.2, step(.45), 1.0)
    # корпоративный бит 124 bpm, 0–4.6
    beat = 60/124
    for k in range(int(4.6/beat)+1):
        t = k*beat
        put(mus, t, kick(.3, 110, 45), .7); put(mus, t + beat/2, fft_filter(noise(.06), lo=5000)*np.exp(-tt(.06)*60), .35)
        put(mus, t, tone(midi([45, 45, 48, 43][k % 4]), .4, decay=6, wave_='saw')*.0 + fft_filter(tone(midi([45, 45, 48, 43][k % 4]), .4, decay=6, wave_='saw'), hi=500), .5)
        for j, n in enumerate([69, 72, 76, 72]): put(mus, t + j*beat/4, tone(midi(n + (0 if k % 2 == 0 else 3)), .2, decay=10, wave_='sq')*.0 + tone(midi(n + (0 if k % 2 == 0 else 3)), .2, decay=10, wave_='tri'), .22)
    mus[int(4.62*SR):] = 0; b += mus
    for f in (1.2, 2.6): put(b, f, kaching(), .6); put(b, f, shimmer(.8), .3)
    for k in range(int((4.3-.9)*22)): put(b, .9 + k/22, tick(), .3)
    typing(b, 'СНАРУЖИ: Карьерист. Заработал первый миллион', 1.0, 19, .38)
    put(b, 4.59, glitch(.3), .75); put(b, 4.6, scratch(.3), .55)
    # туалет офиса: гул ламп, шум в ушах, капли, сердце ускоряется, дыхание
    lamp = fft_filter(tone(120, 7.2, attack=.3, decay=0, wave_='saw'), hi=900)
    lamp *= (0.6 + 0.4*np.sign(np.sin(2*np.pi*7.3*tt(7.2))*np.sin(2*np.pi*1.1*tt(7.2))))
    put(b, 4.9, lamp, .12)
    t = 5.0
    while t < 11.9: put(b, t, drip(), .5); t += 1.1
    tt_ = tt(6.6); put(b, 5.4, tone(6500, 6.6, attack=3, decay=0)*np.minimum(1, tt_/4), .12)
    put(b, 6.2, tone(1500, .6, decay=14), .3); put(b, 6.2, kick(.5, 130, 50), .8); put(b, 6.2, fft_filter(noise(.3), lo=2000)*np.exp(-tt(.3)*20), .4)
    t, gap = 5.6, .95
    while t < 11.9: put(b, t, heartbeat2(), .55); t += gap; gap = max(.3, gap*.9)
    t, gap = 7.0, 1.4
    while t < 11.8: put(b, t, breath(min(.9, gap*.7), .5), 1.0); t += gap; gap = max(.45, gap*.85)
    put(b, 8.2, breath(.5, 1.0), .6)
    put(b, 6.5, pad([midi(n) for n in (45, 46, 52, 58)], 5.4, .22), 1.0)
    put(b, 7.0, riser(4.9, 150, 3200), .4)
    put(b, 11.95, dip(), .8)
    finale(b, 'Успех — это всегда счастье? Или это просто маска?', 'Напиши, что думаешь', 30, 18)
    master(b, 'successful.wav')

if __name__ == '__main__': perfect_family(); successful(); print('ok')
