import asyncio, os, sys, time, subprocess, certifi
certifi.where = lambda *a, **k: "/root/.ccr/ca-bundle.crt"
import edge_tts
sys.path.insert(0, os.getcwd()); from script_ep import LINES
def valid(f):
    return os.path.exists(f) and subprocess.run(["ffmpeg","-v","error","-i",f,"-f","null","-"],capture_output=True).stderr==b""
async def main():
    for i,(t,_) in enumerate(LINES):
        f=f"voice/line_{i:02d}.mp3"
        for a in range(14):
            if valid(f): break
            try: await edge_tts.Communicate(t,"ru-RU-DmitryNeural",proxy=os.environ.get("HTTPS_PROXY")).save(f)
            except Exception as e: print(i,"retry",a); time.sleep(1+a)
        else: raise SystemExit("fail")
        print("ok",i)
asyncio.run(main())
