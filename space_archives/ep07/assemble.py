import json, subprocess, numpy as np, soundfile as sf, glob
from script_ep import LINES
SR = 24000
files = sorted(glob.glob("voice/line_*.mp3"))
def load(f):
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f,"-ar",str(SR),"-ac","1","/tmp/_x.wav"],check=True)
    return sf.read("/tmp/_x.wav")[0]
clips = [load(f) for f in files]
total = 2.6 + sum(len(c)/SR for c in clips[1:]) + 0.4*(len(clips)-2) + 1.5
voice = np.zeros(int(total*SR)+SR)
voice[int(.06*SR):int(.06*SR)+len(clips[0])] += clips[0][:int(2.5*SR)]
t = 2.6; timing = []
for c in clips[1:]:
    voice[int(t*SR):int(t*SR)+len(c)] += c
    timing.append([t, t+len(c)/SR]); t += len(c)/SR + 0.4
dur = t - 0.4 + 1.5
voice = voice[:int(dur*SR)]
tt = np.arange(len(voice))/SR
music = sum(np.sin(2*np.pi*f*tt) for f in (73,110,165))/3
mix = voice*1.9 + music*0.06
mix *= np.clip(1, 0, 1)*np.minimum(1, (dur-tt)/1.6)
mix = np.tanh(mix*1.2)/np.tanh(1.2)
mix *= 0.89/np.abs(mix).max()
sf.write("voice.wav", mix, SR)
json.dump({"intro":[0.06,0.06+len(clips[0])/SR],"lines":timing,"dur":dur}, open("timing.json","w"))
print("dur", dur)
