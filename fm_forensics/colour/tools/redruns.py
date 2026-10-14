"""For each image with a recorded red level: count rows that contain a horizontal run >= 30 px of
dark red (hue <=10 or >=345, S>=0.6, 0.30<=V<0.80) vs standard red (same hue, S>=0.6, V>=0.80).
Tags and drawn lines give long horizontal runs; candle bodies are narrow."""
import json, os, sys
import numpy as np
from PIL import Image, ImageOps
REC = sys.argv[1]
last = {}
for ln in open(REC, encoding="utf-8"):
    x = json.loads(ln); last[x["id"]] = x
files = {os.path.splitext(f)[0]: f for f in os.listdir("faisal_images")}
def runs(mask, minlen=30):
    rows = 0
    for row in mask:
        if not row.any(): continue
        d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]]))
        s = np.where(d == 1)[0]; e = np.where(d == -1)[0]
        if ((e - s) >= minlen).any(): rows += 1
    return rows
out = []
for i, r in last.items():
    nred = sum(1 for c in r.get("charts", []) for l in c["levels"] if l[0] == "red")
    if not nred: continue
    a = np.asarray(ImageOps.exif_transpose(Image.open("faisal_images/" + files[i])).convert("HSV")).astype(np.float32)
    h = a[..., 0] * 360 / 255; s = a[..., 1] / 255; v = a[..., 2] / 255
    red = ((h <= 10) | (h >= 345)) & (s >= 0.6)
    dark = runs(red & (v >= 0.30) & (v < 0.80)); std = runs(red & (v >= 0.80))
    out.append((dark, std, i, nred))
out.sort(key=lambda t: (-(t[0] > 2 and t[1] < 3), -t[0]))
for o in out: print(*o)
