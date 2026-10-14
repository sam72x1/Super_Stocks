"""Find tag-like blocks (>=8 consecutive rows each holding a run >=30 px, overlapping x) of a dark shade
(V below the family floor) per family, in images whose records hold that family. Prints blocks with median RGB.
The consistency audit ran with the blue floor at 0.85 (a wider search than the final 0.80 rule in the protocol, changelog 3)."""
import json, os, sys
import numpy as np
from PIL import Image, ImageOps
REC = sys.argv[1]
FAM = {"purple": ((255, 300), 0.85), "blue": ((185, 235), 0.85), "red": ((345, 370), 0.80)}
last = {}
for ln in open(REC, encoding="utf-8"):
    x = json.loads(ln); last[x["id"]] = x
files = {os.path.splitext(f)[0]: f for f in os.listdir("faisal_images")}
for i, r in sorted(last.items()):
    fams = {l[0] for c in r.get("charts", []) for l in c["levels"]}
    want = [f for f in ("purple", "blue") if f in fams]
    if not want: continue
    im = ImageOps.exif_transpose(Image.open("faisal_images/" + files[i])).convert("RGB")
    rgb = np.asarray(im).astype(int)
    a = np.asarray(im.convert("HSV")).astype(np.float32)
    h = a[..., 0] * 360 / 255; s = a[..., 1] / 255; v = a[..., 2] / 255
    for f in want:
        (h0, h1), vf = FAM[f]
        m = (h >= h0) & (h <= h1) & (s >= 0.5) & (v >= 0.3) & (v < vf)
        blocks = []; cur = None
        for y, row in enumerate(m):
            if not row.any():
                seg = None
            else:
                d = np.diff(np.concatenate([[0], row.astype(np.int8), [0]])); st = np.where(d == 1)[0]; en = np.where(d == -1)[0]
                L = en - st; k = np.argmax(L)
                seg = (st[k], en[k]) if L[k] >= 30 else None
            if seg:
                if cur and abs(seg[0] - cur[2]) < 20: cur[1] = y; cur[3].append((y, seg))
                else:
                    if cur: blocks.append(cur)
                    cur = [y, y, seg[0], [(y, seg)]]
            else:
                if cur: blocks.append(cur); cur = None
        if cur: blocks.append(cur)
        for b in blocks:
            if b[1] - b[0] + 1 >= 8:
                y, (x0, x1) = b[3][len(b[3]) // 2]
                med = tuple(int(t) for t in np.median(rgb[y, x0:x1], axis=0))
                print(i, f, "rows", b[0], b[1], "x", x0, x1, "rgb", med, "W", im.size[0])
