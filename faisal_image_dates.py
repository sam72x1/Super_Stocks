# -*- coding: utf-8 -*-
"""📅 تواريخُ الصور من EXIF — **قراءةٌ فقط** (لا شبكة · لا حالة). يكتب
`faisal_image_dates.tsv`: (image, exif_datetime, date, source). التاريخُ هنا =
**وقتُ لقطة الشاشة على جهاز المالك** — قريبٌ من تاريخ الشارت لكنه ليس هو
بالضرورة (‏±يوم). **لا يُستنتَج تاريخٌ من رقم الصورة.**"""
import csv, glob, os, sys
try:
    from PIL import Image
except ImportError:
    print("PIL غيرُ متاحة"); sys.exit(2)

rows = []
for p in sorted(glob.glob("faisal_images/*")):
    if not p.lower().endswith((".jpg", ".jpeg", ".png")):
        continue
    name = os.path.basename(p)
    d = ""; src = ""
    try:
        ex = Image.open(p).getexif()
        raw = ex.get(36867) or ex.get(306)      # DateTimeOriginal ثمّ DateTime
        if raw:
            s = str(raw).strip()
            d = s[:10].replace(":", "-"); src = "exif"
    except Exception:                                      # noqa: BLE001
        pass
    if not d:
        import re
        m = re.search(r"_(20\d{2})(\d{2})(\d{2})_", name)
        if m:
            d = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"; src = "filename"
    rows.append({"image": name, "date": d, "source": src})
with open("faisal_image_dates.tsv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=["image", "date", "source"], delimiter="\t"); w.writeheader(); w.writerows(rows)
from collections import Counter
c = Counter(r["source"] or "none" for r in rows)
print(f"📅 صور: {len(rows)} · exif: {c['exif']} · filename: {c['filename']} · بلا تاريخ: {c['none']}")
ds = sorted({r['date'] for r in rows if r['date']})
print(f"   مدى التواريخ: {ds[0]} ⟶ {ds[-1]} · أيّامٌ متمايزة: {len(ds)}")
