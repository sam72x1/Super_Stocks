#!/usr/bin/env python3
"""🕯️📅 `T-DATE-CANDLES` — بوّابةُ الجدوى F0 (قراءةٌ فقط · بلا شبكة · بلا كتابة).

العقد: `fm_forensics/date_candles/T_DATE_CANDLES_prereg.md` (§③).
الوحدة = (الرمز، سطر الكاتالوج) في `faisal_levels_table.tsv`.
«متاحة» = صورةٌ واحدةٌ على الأقلّ من صورها ملفٌّ على القرص في `faisal_images/` باسمها،
أو عبر `data/image_map.tsv` (اسمُ الكاتالوج ⟵ اسمُ الملفّ على القرص · يُكتب بعد سجلّ العين).

الخروج: 0 = F0 تعبر (① و③ قابلان للتشغيل) · 3 = «لا قياس» (المحورُ متوقّف).
"""
import csv
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
TABLE = os.path.join(ROOT, "faisal_levels_table.tsv")
IMAGES = os.path.join(ROOT, "faisal_images")
MAP = os.path.join(HERE, "data", "image_map.tsv")

NUMERIC_SOURCES = ("price", "indicator")   # نصُّ المالك: «date_source = price أو indicator»
MIN_TEST_UNITS = 50                        # نصُّ المالك: «خذ 50 وحدة مؤرَّخة بالرقم»
RC_PASS, RC_NO_MEASURE = 0, 3


def expand_images(field: str) -> list:
    """«IMG_6004/6005/6006» ⟵ [IMG_6004, IMG_6005, IMG_6006] · والفواصلُ مسافةٌ أو فاصلة."""
    out = []
    for tok in re.split(r"[ ,;]+", (field or "").strip()):
        if not tok:
            continue
        m = re.match(r"([A-Z]+_)(\w+)((?:/\w+)*)$", tok)
        if not m:
            out.append(tok)
            continue
        pre, first, rest = m.groups()
        out.append(pre + first)
        out.extend(pre + x for x in rest.split("/")[1:])
    return out


def units(rows: list) -> dict:
    """{(الرمز، السطر): {"src": وسمُ التاريخ, "images": [...]}} — وسمٌ واحدٌ لكلّ وحدة (صفوفُها تشترك فيه)."""
    out = {}
    for r in rows:
        key = (r.get("symbol", ""), r.get("line", ""))
        u = out.setdefault(key, {"src": set(), "images": []})
        u["src"].add(r.get("date_source", "") or "")
        for i in expand_images(r.get("images", "")):
            if i not in u["images"]:
                u["images"].append(i)
    return out


def f0(rows: list, on_disk: set, mapping: dict) -> dict:
    """البوّابة نقيّةً: الوحداتُ المؤرَّخة بالرقم المتاحة · وغيرُ المؤرَّخة المتاحة · والحكم."""
    U = units(rows)

    def available(u):
        return any(i in on_disk or (mapping.get(i) in on_disk) for i in u["images"])

    numeric = {k: u for k, u in U.items() if u["src"] & set(NUMERIC_SOURCES)}
    undated = {k: u for k, u in U.items() if u["src"] == {""}}
    num_ok = sorted(k for k, u in numeric.items() if available(u))
    und_ok = sorted(k for k, u in undated.items() if available(u))
    imgs = lambda d: sorted({i for u in d.values() for i in u["images"]})  # noqa: E731
    pass_1 = len(num_ok) >= MIN_TEST_UNITS
    return {
        "numeric_units": len(numeric), "numeric_images": imgs(numeric), "numeric_available": num_ok,
        "undated_units": len(undated), "undated_rows": sum(1 for r in rows if not (r.get("date_source") or "")),
        "undated_images": imgs(undated), "undated_available": und_ok,
        "pass_1": pass_1, "pass_3": pass_1 and bool(und_ok),
        "rc": RC_PASS if (pass_1 and und_ok) else RC_NO_MEASURE,
    }


def _disk() -> set:
    if not os.path.isdir(IMAGES):
        return set()
    return {os.path.splitext(f)[0] for f in os.listdir(IMAGES)}


def _mapping() -> dict:
    if not os.path.exists(MAP):
        return {}
    with open(MAP, encoding="utf-8") as fh:
        return {r["catalog_image"]: os.path.splitext(r["disk_file"])[0]
                for r in csv.DictReader(fh, delimiter="\t") if r.get("catalog_image") and r.get("disk_file")}


def main() -> int:
    with open(TABLE, encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    disk, mp = _disk(), _mapping()
    g = f0(rows, disk, mp)
    print(f"📁 صورُ القرص في faisal_images/: {len(disk)} · صفوفُ خريطة الصور: {len(mp)}")
    print(f"① المؤرَّخةُ بالرقم ({'/'.join(NUMERIC_SOURCES)}): {g['numeric_units']} وحدة · "
          f"{len(g['numeric_images'])} صورة · المتاحُ منها {len(g['numeric_available'])} · المطلوب {MIN_TEST_UNITS}")
    print(f"③ غيرُ المؤرَّخة: {g['undated_rows']} صفًّا = {g['undated_units']} وحدة · "
          f"{len(g['undated_images'])} صورة · المتاحُ منها {len(g['undated_available'])}")
    print(f"⚖️ ① {'تعبر' if g['pass_1'] else 'لا قياس'} · ③ {'تعبر' if g['pass_3'] else 'لا قياس'} "
          f"⟵ {'التشغيلُ ممكن' if g['rc'] == RC_PASS else 'المحورُ متوقّف (العقد §③)'}")
    return g["rc"]


if __name__ == "__main__":
    sys.exit(main())
