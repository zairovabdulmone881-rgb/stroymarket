import asyncio, os, time, certifi, subprocess
def valid(f):
    return os.path.exists(f) and subprocess.run(["ffprobe","-v","error","-i",f,"-f","null","-"],capture_output=True).returncode==0 and subprocess.run(["ffmpeg","-v","error","-i",f,"-f","null","-"],capture_output=True).stderr==b""
certifi.where = lambda *a, **k: "/root/.ccr/ca-bundle.crt"
import edge_tts
from script_ep import INTRO_LINE, LINES
texts = [INTRO_LINE] + [l[0] for l in LINES]
async def one(i, t):
    for a in range(14):
        try:
            await edge_tts.Communicate(t, "ru-RU-DmitryNeural", proxy=os.environ.get("HTTPS_PROXY")).save(f"voice/line_{i:02d}.mp3")
            return
        except Exception as e:
            print(i, "retry", a, type(e).__name__); time.sleep(1 + a)
    raise SystemExit(f"fail {i}")
async def main():
    for i, t in enumerate(texts):
        if not valid(f"voice/line_{i:02d}.mp3"): await one(i, t)
        print("ok", i)
asyncio.run(main())
