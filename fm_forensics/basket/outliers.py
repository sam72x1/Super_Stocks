"""🔎 فحصُ الصفقات الشاذّة في `T-BASKET` — تشخيصٌ قارئٌ على شرائح تشغيلةٍ منتهية (لا شبكة · لا حكمَ جديد · لا إنتاج).

السبب (2026-11-16): تشغيلةُ `43955351411` أخرجت صفقةً بعائد +14,948% في ذراع (أ) 2024 و+758% في الجديدة 2024 —
وسقفُ الأمرين +73.2% · فالمطلوبُ تسميتُها ومعها تقسيماتُ نافذتها (من `prep`) ليُعرف: عطلُ مقياسٍ أم حركةٌ حقيقيّة.
يُقرأ من `out/`: `basket_rbprep.json.gz` والشرائح `basket_shard_*.json.gz` كما نزّلها الـworkflow من التشغيلة نفسِها.
"""
import glob
import gzip
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
HI, LO = 1.0, -0.95          # خارج [−95%، +100%] = شاذّ يُسمّى (سقفُ الأمرين +73.2% · وأدنى المعقول قبل −100%)


def _jload(path):
    with gzip.open(path, "rt", encoding="utf-8") as fh:
        return json.load(fh)


def flag(rec, hi=HI, lo=LO):
    """أذرعُ الصفقة الخارجة عن [lo، hi] ⟵ {الذراع: العائد} (نقيّة)."""
    out = {}
    for arm, v in (rec.get("res") or {}).items():
        r = (v or {}).get("r")
        if r is not None and (r > hi or r < lo):
            out[arm] = r
    return out


def window_splits(splits, d, last):
    """تقسيماتُ الرمز [تاريخ، نسبة to/from] (صيغةُ `prep` من `rebuild.py`) من يوم القرار حتى آخر النافذة (نقيّة)."""
    return [[str(e), r] for e, r in (splits or []) if d <= str(e) <= (last or d)]


def main():
    shards = sorted(glob.glob(os.path.join(OUT, "**", "basket_shard_*.json.gz"), recursive=True))
    prep = _jload(os.path.join(OUT, "basket_rbprep.json.gz"))
    sess = prep.get("sessions") or []
    pos = {d: i for i, d in enumerate(sess)}
    n, rows = 0, []
    for p in shards:
        for rec in _jload(p).get("recs") or []:
            n += 1
            f = flag(rec)
            if f:
                i = pos.get(rec["d"])
                last = sess[min(i + 21, len(sess) - 1)] if i is not None else None
                rows.append({"sym": rec["sym"], "d": rec["d"], "lists": rec.get("lists"), "st": rec.get("st"), "flags": f,
                             "splits": window_splits(prep["splits"].get(rec["sym"]), rec["d"], last)})
    print(f"OUTLIERS shards={len(shards)} entries={n} flagged={len(rows)} band=[{LO}, {HI}]")
    for r in sorted(rows, key=lambda x: -max(abs(v) for v in x["flags"].values())):
        print("OUTLIER " + json.dumps(r, ensure_ascii=False, separators=(",", ":")))
    return 0 if shards else 2


if __name__ == "__main__":
    sys.exit(main())
