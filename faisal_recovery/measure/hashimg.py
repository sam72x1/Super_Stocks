"""SHA256 + dHash(64) + pHash(64, DCT via numpy) + dims for a list of image paths. Read-only."""
import hashlib, json, sys
import numpy as np
from PIL import Image

def _dct_mat(n):
    k = np.arange(n)[:, None]; i = np.arange(n)[None, :]
    m = np.cos(np.pi * (2 * i + 1) * k / (2 * n)); m[0] *= 1 / np.sqrt(2)
    return m * np.sqrt(2 / n)
_D32 = _dct_mat(32)

def hashes(path):
    b = open(path, "rb").read()
    sha = hashlib.sha256(b).hexdigest()
    try:
        im = Image.open(path); im.load()
        w, h = im.size
        g = im.convert("L")
        d = np.asarray(g.resize((9, 8), Image.LANCZOS), dtype=float)
        dh = (d[:, 1:] > d[:, :-1]).flatten()
        p = np.asarray(g.resize((32, 32), Image.LANCZOS), dtype=float)
        c = _D32 @ p @ _D32.T
        low = c[:8, :8].flatten()
        ph = low > np.median(low[1:])
        tohex = lambda bits: "%016x" % int("".join("1" if x else "0" for x in bits), 2)
        return {"sha256": sha, "bytes": len(b), "w": w, "h": h, "dhash": tohex(dh), "phash": tohex(ph), "fmt": im.format}
    except Exception as e:
        return {"sha256": sha, "bytes": len(b), "w": None, "h": None, "dhash": None, "phash": None, "fmt": None, "err": type(e).__name__}

if __name__ == "__main__":
    paths = [l.rstrip("\n") for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    out = {p: hashes(p) for p in paths}
    json.dump(out, open(sys.argv[2], "w"), ensure_ascii=False, indent=0)
    print(len(out), sum(1 for v in out.values() if v.get("err")))
