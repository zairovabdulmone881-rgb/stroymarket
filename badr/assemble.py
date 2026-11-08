import json, subprocess, sys, numpy as np, soundfile as sf, glob
SR=24000
files=sorted(glob.glob("voice/line_*.mp3"))
def load(f):
    subprocess.run(["ffmpeg","-y","-loglevel","error","-i",f,"-ar",str(SR),"-ac","1","/tmp/_y.wav"],check=True); return sf.read("/tmp/_y.wav")[0]
cl=[load(f) for f in files]
t=0.5; tm=[]
total=0.5+sum(len(c)/SR for c in cl)+0.35*(len(cl)-1)+1.0
v=np.zeros(int(total*SR)+SR)
for c in cl:
    v[int(t*SR):int(t*SR)+len(c)]+=c; tm.append([t,t+len(c)/SR]); t+=len(c)/SR+0.35
dur=t-0.35+1.0; v=v[:int(dur*SR)]; tt=np.arange(len(v))/SR
mus=sum(np.sin(2*np.pi*f*tt) for f in (73,110,165))/3
mix=(v*1.9+mus*0.06)*np.minimum(1,(dur-tt)/1.0)
mix=np.tanh(mix*1.2)/np.tanh(1.2); mix*=0.8/np.abs(mix).max()
sf.write("voice.wav",mix,SR); json.dump({"lines":tm,"dur":dur},open("timing.json","w")); print("dur",dur)
