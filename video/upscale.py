#!/usr/bin/env python3
"""Апскейл imgs/NN.png ×4 нейросетью Real-ESRGAN (anime 6B, ONNX) -> imgs_hd/NN.png"""
import os, sys, numpy as np, onnxruntime as ort
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = sys.argv[1]
src_dir = sys.argv[2] if len(sys.argv) > 2 else "imgs"
dst_dir = sys.argv[3] if len(sys.argv) > 3 else "imgs_hd"
n = len([f for f in os.listdir(os.path.join(ROOT, src_dir)) if f.endswith(".png")])
s = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
os.makedirs(os.path.join(ROOT, dst_dir), exist_ok=True)
for i in range(1, n + 1):
    src = Image.open(os.path.join(ROOT, src_dir, f"{i:02d}.png")).convert("RGB")
    if src.width >= 1000:  # и так достаточно крупная — не трогаем
        src.save(os.path.join(ROOT, dst_dir, f"{i:02d}.png")); print(i, "as is", src.size); continue
    im = np.asarray(src, np.float32) / 255
    T, P = 160, 12                       # тайлы 160 px с перекрытием 12 px
    h, w = im.shape[:2]; y = np.zeros((h * 4, w * 4, 3), np.float32)
    for ty in range(0, h, T):
        for tx in range(0, w, T):
            a0, b0 = max(0, ty - P), max(0, tx - P); a1, b1 = min(h, ty + T + P), min(w, tx + T + P)
            o = s.run(None, {"input": im[a0:a1, b0:b1].transpose(2, 0, 1)[None]})[0][0].transpose(1, 2, 0)
            oy, ox = (ty - a0) * 4, (tx - b0) * 4; hh, ww = min(T, h - ty) * 4, min(T, w - tx) * 4
            y[ty * 4:ty * 4 + hh, tx * 4:tx * 4 + ww] = o[oy:oy + hh, ox:ox + ww]
    Image.fromarray((np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(ROOT, dst_dir, f"{i:02d}.png"))
    print(i, y.shape, flush=True)
