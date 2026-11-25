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
    x = im.transpose(2, 0, 1)[None]
    y = s.run(None, {"input": x})[0][0].transpose(1, 2, 0)
    Image.fromarray((np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(ROOT, dst_dir, f"{i:02d}.png"))
    print(i, y.shape, flush=True)
