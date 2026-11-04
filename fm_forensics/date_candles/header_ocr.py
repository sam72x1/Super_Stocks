# -*- coding: utf-8 -*-
"""🔤 الملحق 4 §④ — القراءةُ الآليّة لكلّ صورة (على الرنر · tesseract) ⟵ سطرُ `DHO\t{json}` لكلّ صورة في السجلّ.

الصورةُ كاملةً (القصاصةُ = الصورة: الرأسُ كثيرًا داخل لقطةٍ مضمَّنة) مكبَّرةً ×2 ⟵ `tesseract --psm 11` (نصٌّ متناثر · TSV) ⟵ تُجمع الكلماتُ
أسطرًا (`block`/`par`/`line`) ⟵ **يُطبع السطرُ الذي فيه رقمٌ وحدَه** بنصّه ومستطيله (بإحداثيّات الصورة الأصل) — والتفسيرُ (الصيغ · السنة ·
الوصول) في `header.py` بلا شبكة. 🔒 قراءةٌ فقط · لا كتابةَ في المستودع · والصورُ لا تُرفع.
"""
from __future__ import annotations

import collections
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
IMG_DIR = os.path.join(REPO, "faisal_images")
EXTS = (".jpg", ".jpeg", ".png")
SCALE = 2
PSM = "11"


def images() -> list:
    return sorted(f for f in os.listdir(IMG_DIR) if f.lower().endswith(EXTS))


def ocr_lines(path: str) -> dict:
    from PIL import Image                                          # noqa: PLC0415
    im = Image.open(path).convert("RGB")
    W, H = im.size
    big = im.resize((W * SCALE, H * SCALE), Image.LANCZOS)
    with tempfile.NamedTemporaryFile(suffix=".png") as t:
        big.save(t.name)
        out = subprocess.run(["tesseract", t.name, "stdout", "--psm", PSM, "tsv"], capture_output=True, text=True,
                             timeout=180).stdout
    lines = collections.OrderedDict()
    for row in out.splitlines()[1:]:
        p = row.split("\t")
        if len(p) < 12 or not p[11].strip():
            continue
        key = (p[2], p[3], p[4])
        x, y, w, h = (int(p[6]) // SCALE, int(p[7]) // SCALE, int(p[8]) // SCALE, int(p[9]) // SCALE)
        lines.setdefault(key, []).append((p[11].strip(), x, y, x + w, y + h, float(p[10])))
    keep = []
    for ws in lines.values():
        txt = " ".join(w[0] for w in ws)
        if any(ch.isdigit() for ch in txt):
            keep.append([txt, min(w[1] for w in ws), min(w[2] for w in ws), max(w[3] for w in ws), max(w[4] for w in ws),
                         round(min(w[5] for w in ws), 1)])
    return {"W": W, "H": H, "lines": keep}


def main() -> int:
    batch = int(os.environ.get("DH_BATCH", "0") or 0)
    size = int(os.environ.get("DH_SIZE", "230") or 230)
    fs = images()[batch * size:(batch + 1) * size]
    print(f"DHB\t{json.dumps({'batch': batch, 'size': size, 'n': len(fs), 'total': len(images())})}", flush=True)
    for f in fs:
        iid = os.path.splitext(f)[0]
        try:
            row = {"id": iid, **ocr_lines(os.path.join(IMG_DIR, f))}
        except Exception as e:                                     # noqa: BLE001
            row = {"id": iid, "error": f"{type(e).__name__}: {e}"[:200]}
        print(f"DHO\t{json.dumps(row, ensure_ascii=False)}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
