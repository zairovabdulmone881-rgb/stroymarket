#!/usr/bin/env python3
"""Апскейл imgs/NN.png ×4 нейросетью Real-ESRGAN (anime 6B, ONNX) -> imgs_hd/NN.png"""
import os, sys, numpy as np, onnxruntime as ort
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
model = sys.argv[1]
s = ort.InferenceSession(model, providers=["CPUExecutionProvider"])
os.makedirs(os.path.join(ROOT, "imgs_hd"), exist_ok=True)
for i in range(1, 15):
    im = np.asarray(Image.open(os.path.join(ROOT, "imgs", f"{i:02d}.png")).convert("RGB"), np.float32) / 255
    x = im.transpose(2, 0, 1)[None]
    y = s.run(None, {"input": x})[0][0].transpose(1, 2, 0)
    Image.fromarray((np.clip(y, 0, 1) * 255 + 0.5).astype(np.uint8)).save(os.path.join(ROOT, "imgs_hd", f"{i:02d}.png"))
    print(i, y.shape, flush=True)
