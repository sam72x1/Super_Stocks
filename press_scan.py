#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🗜️📊 `T-PRESS` — «الضغط يولد الانفجار» (العقد: `press_prereg.md` · مدفوعٌ قبل
أيّ رقم).

**السؤال:** هل يومُ «الضغط الممسوك» (سعرٌ يُضغَط إلى/تحت أدنى شمعةٍ في `W` جلسةً
**ويُغلق فوقها** — نصُّ فيصل «اي سهم قبل يصعد يضغطه المضارب لادنى شمعه · اذا
حافظ ع ادنى قاع فنيا طبق نموذج الضغط قبل الانفجار») يسبق الانفجارَ بمعدّلٍ يفوق
الأساس ويفوق نظيرَه المكسور؟ ومعه طبقةُ الحجم (‏`H-VOL`) **بأثلاثٍ لا عتبة**.

🔒 بحث/قياس حصرًا: لا يستوردها الإنتاج (قفل `PS1`) · المجتمعُ **غيرُ مشروطٍ
بالنتيجة** (كلُّ رمزٍ وكلُّ جلسةٍ في لقطة PIT المجمَّدة) ⇒ حتميٌّ بت-بت ·
والنتيجةُ من ‏`i+1..i+N` حصرًا (‏`PV1` — صفرُ نظرٍ مستقبليّ، وانفجارُ يوم
الضغط نفسِه لا يُحسب)."""
from __future__ import annotations

import hashlib
import math
import os
import sys

W = 20            # نافذةُ أدنى شمعة — `engineering` مُعلَن (§③)
FWD = 10          # نافذةُ الانفجار الحاكمة — `engineering` مُعلَن («صعود قريبا»)
FWD_ALT = (5, 20)  # ثانويّتان تُنشَران ولا يُختار بينهما بعد الأرقام
X50, X100 = 1.5, 2.0
MIN_G1, MIN_G2 = 300, 100          # أرضيّاتُ الحكم (§④)
SPLIT_PAD = 10    # حارسُ التقسيم: ‏±10 جلسات حول تقسيمٍ عكسيّ — أفضل-جهد
BUCKETS = ((2.0, "≤$2"), (5.0, "$2-5"), (10.0, "$5-10"), (1e18, ">$10"))


def _log(msg: str) -> None:
    print(msg, flush=True)


def wilson(k: int, n: int, z: float = 1.96):
    """فاصل Wilson 95% — نفسُ آلة الدلالة في كلّ التجارب السابقة."""
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def classify(low: float, close: float, prior_min: float):
    """نقيّة — تصنيفُ يومٍ واحد (§③ حرفيًّا):
    يرجّع `(state, swept)`: state ∈ {'held', 'broken', None}.
    · ضُغط ⟺ `low ≤ prior_min` (**المساواةُ ضغط** — لمسُ القاع يُحسب)
    · حُفظ ⟺ ضُغط و`close ≥ prior_min` («حافظ ع ادنى قاع»)
    · مُسح ⟺ `low < prior_min` والإغلاقُ استعاد («مسح سيوله تحت هذي الشمعه»)."""
    if not (low <= prior_min):
        return None, False
    held = close >= prior_min
    swept = (low < prior_min) and held
    return ("held" if held else "broken"), swept


def bucket_of(price: float) -> str:
    for cap, name in BUCKETS:
        if price <= cap:
            return name
    return ">$10"


def _split_days(splits, index) -> set:
    """مواضعُ الاستبعاد حول التقسيمات العكسية — أفضل-جهد (بلا splits ⇒ فارغ)."""
    out = set()
    try:
        pairs = [(str(d)[:10], float(v)) for d, v in
                 (splits.items() if hasattr(splits, "items") else (splits or []))]
    except Exception:                                             # noqa: BLE001
        return out
    dates = [str(d.date()) for d in index]
    for d, v in pairs:
        if v >= 1.0:                       # عكسيٌّ فقط (نسبةٌ دون 1 = أمامي)
            continue
        for j, ds in enumerate(dates):
            if abs_idx_near(ds, d):
                out.update(range(max(0, j - SPLIT_PAD),
                                 min(len(dates), j + SPLIT_PAD + 1)))
                break
    return out


def abs_idx_near(ds: str, split_iso: str) -> bool:
    return ds >= split_iso[:10]            # أوّلُ جلسةٍ عند/بعد التقسيم


class Acc:
    """عدّاداتٌ انسيابية (لا صفوف — سابقة `YearAcc`)."""

    def __init__(self):
        self.n = {}
        self.k50 = {}
        self.k100 = {}
        self.alt = {}                      # (group, fwd) -> [n, k50]
        self.vol_g1 = []                   # (vol_x, exploded50) داخل G1
        self.bucket = {}                   # (group, bucket) -> [n, k50]
        self.skipped_tail = 0
        self.skipped_split = 0

    def add(self, grp, e50, e100, price):
        self.n[grp] = self.n.get(grp, 0) + 1
        self.k50[grp] = self.k50.get(grp, 0) + (1 if e50 else 0)
        self.k100[grp] = self.k100.get(grp, 0) + (1 if e100 else 0)
        b = (grp, bucket_of(price))
        r = self.bucket.setdefault(b, [0, 0])
        r[0] += 1
        r[1] += 1 if e50 else 0


def walk_symbol(df, year: int, acc: Acc, splits=None) -> None:
    """المشيُ غيرُ المشروط: كلُّ جلسةٍ في السنة تُصنَّف وتُقاس أماميًّا.

    `PV1`: الحالةُ من ‏≤i والنتيجةُ من `High[i+1..i+FWD]` حصرًا — شريحةُ بايثون
    `hi[i+1:i+1+fwd]` لا تشمل يومَ i بالبناء، ويُثبتها قفلٌ سلوكيّ (‏PS7)."""
    try:
        lo = df["Low"].values.astype(float)
        hi = df["High"].values.astype(float)
        cl = df["Close"].values.astype(float)
        vol = df["Volume"].values.astype(float)
        years = [d.year for d in df.index]
    except Exception:                                             # noqa: BLE001
        return
    n = len(cl)
    ex = _split_days(splits, df.index) if splits is not None else set()
    for i in range(W, n):
        if years[i] != year:
            continue
        if i in ex:
            acc.skipped_split += 1
            continue
        if i + FWD >= n:                   # ذيلٌ يُقصّ ويُعَدّ (‏PV5)
            acc.skipped_tail += 1
            continue
        prior_min = float(min(lo[i - W:i]))
        if prior_min <= 0 or cl[i] <= 0:
            continue
        e50 = float(max(hi[i + 1:i + 1 + FWD])) >= cl[i] * X50
        e100 = float(max(hi[i + 1:i + 1 + FWD])) >= cl[i] * X100
        acc.add("G0", e50, e100, cl[i])
        for f in FWD_ALT:
            if i + f < n:
                r = acc.alt.setdefault(("G0", f), [0, 0])
                r[0] += 1
                r[1] += 1 if float(max(hi[i + 1:i + 1 + f])) >= cl[i] * X50 else 0
        state, swept = classify(lo[i], cl[i], prior_min)
        if state is None:
            continue
        grp = "G1" if state == "held" else "G2"
        acc.add(grp, e50, e100, cl[i])
        if grp == "G1":
            base_v = float(sum(vol[i - W:i])) / W
            if base_v > 0:
                acc.vol_g1.append((float(vol[i]) / base_v, e50))
            for f in FWD_ALT:
                if i + f < n:
                    r = acc.alt.setdefault(("G1", f), [0, 0])
                    r[0] += 1
                    r[1] += (1 if float(max(hi[i + 1:i + 1 + f]))
                             >= cl[i] * X50 else 0)
        if swept:
            acc.add("G3", e50, e100, cl[i])


def report(acc: Acc, year: int) -> int:
    def row(g, label):
        n, k = acc.n.get(g, 0), acc.k50.get(g, 0)
        w = wilson(k, n)
        _log(f"  {label:<16} أيام={n:<8} انفجر50={k:<6} "
             f"نسبة={100.0 * k / n if n else 0.0:6.2f}% "
             f"Wilson=[{100 * w[0]:.2f},{100 * w[1]:.2f}] "
             f"· انفجر100={acc.k100.get(g, 0)}")
        return n, k, w

    _log(f"\n📊 T-PRESS سنة {year} — الجداول (النافذة الحاكمة {FWD}ج · ×1.5):")
    n0, k0, w0 = row("G0", "G0 الأساس")
    n1, k1, w1 = row("G1", "G1 ضُغط وحُفظ")
    n2, k2, w2 = row("G2", "G2 ضُغط وكُسر")
    row("G3", "G3 مسحٌ واستُعيد")
    _log(f"  (‏تُخطّي الذيل {acc.skipped_tail} · مستبعَدُ التقسيم "
         f"{acc.skipped_split} — يُعَدّان ولا يُصمَتان)")
    if not acc.n.get("G1"):
        _log("⛔ PV2: صفرُ أيام G1 ⇒ خروج 3 — لا تشغيلةَ خضراءَ بلا قياس.")
        return 3
    b_low = acc.bucket.get(("G0", "≤$2"), [0, 0])
    b_hi = acc.bucket.get(("G0", ">$10"), [0, 0])
    r_low = b_low[1] / b_low[0] if b_low[0] else 0.0
    r_hi = b_hi[1] / b_hi[0] if b_hi[0] else 0.0
    _log(f"  🧪 PV3 شاهدُ الضبط: rate50(>$10)={100 * r_hi:.2f}% مقابل "
         f"rate50(≤$2)={100 * r_low:.2f}%")
    if b_low[0] and b_hi[0] and r_hi >= r_low:
        _log("⛔ PV3 سقط: الكبارُ ينفجرون كالصغار ⇒ عطبُ أداةٍ محتمَل — خروج 3.")
        return 3
    _log("  سلالُ السعر (‏G1 · أيام/انفجر50/نسبة):")
    for _cap, name in BUCKETS:
        r = acc.bucket.get(("G1", name), [0, 0])
        _log(f"    {name:<7} {r[0]:<8} {r[1]:<6} "
             f"{100.0 * r[1] / r[0] if r[0] else 0.0:6.2f}%")
    _log("  نوافذُ ثانوية (‏rate50):")
    for g in ("G0", "G1"):
        for f in FWD_ALT:
            r = acc.alt.get((g, f), [0, 0])
            _log(f"    {g} fwd={f:<3} {100.0 * r[1] / r[0] if r[0] else 0.0:6.2f}% "
                 f"(ن={r[0]})")
    terc = sorted(acc.vol_g1)
    if len(terc) >= 9:
        third = len(terc) // 3
        parts = (terc[:third], terc[third:2 * third], terc[2 * third:])
        _log("  أثلاثُ الحجم داخل G1 (‏H-VOL — أثلاثٌ لا عتبة):")
        for j, part in enumerate(parts, 1):
            kk = sum(1 for _v, e in part if e)
            vmed = part[len(part) // 2][0]
            _log(f"    T{j} (وسيطُ vol_x={vmed:.2f}) نسبة="
                 f"{100.0 * kk / len(part):6.2f}% (ن={len(part)})")
    verdicts = []
    c1 = (n0 and n1 and (k1 / n1) >= 2.0 * (k0 / n0) and w1[0] > w0[1])
    verdicts.append(f"①(G1≥2×G0 وفاصلان منفصلان)={'✅' if c1 else '🔴'}")
    c2 = (n1 and n2 and (k1 / n1) > (k2 / n2))
    verdicts.append(f"②(G1>G2 المسكُ فارق)={'✅' if c2 else '🔴'}")
    floor_ok = n1 >= MIN_G1 and n2 >= MIN_G2
    verdicts.append(f"أرضيّات(G1≥{MIN_G1}·G2≥{MIN_G2})="
                    f"{'✅' if floor_ok else '🔴 لا حكم'}")
    _log("  🧭 معاييرُ السنة (الحكمُ النهائيّ بالسنوات الثلاث): "
         + " · ".join(verdicts))
    dig = hashlib.sha256(str(sorted(acc.n.items()) + sorted(acc.k50.items())
                             + sorted(acc.k100.items())).encode()).hexdigest()[:12]
    _log(f"  🔑 PV6 بصمةُ العدّادات: {dig} — تشغيلتان بنفس اللقطة تتطابقان")
    return 0


def main() -> int:
    year = int((os.environ.get("PRESS_YEAR") or "0").strip() or 0)
    if not year:
        _log("⛔ `PRESS_YEAR` غائب ⇒ خروج 4.")
        return 4
    path = (os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz").strip()
    _log(f"\n{'=' * 78}\n🗜️📊 T-PRESS — «الضغط يولد الانفجار» · سنة {year}"
         f"\n   W={W} · FWD={FWD} (ثانوي {FWD_ALT}) · x50={X50} · "
         f"لقطة={path}\n{'=' * 78}")
    import Super_stock as S                                      # noqa: PLC0415
    hist, splits, asof = S.load_frozen_dataset(path)
    if not hist:
        _log("⛔ PV4: لقطةٌ مفقودة/فارغة ⇒ خروج 4.")
        return 4
    _log(f"📥 لقطةٌ محمَّلة: {len(hist)} رمزًا · as-of {asof}")
    acc = Acc()
    done = 0
    for sym, df in hist.items():
        if df is None or len(df) < W + 2:
            continue
        walk_symbol(df, year, acc, (splits or {}).get(sym))
        done += 1
        if done % 500 == 0:
            _log(f"   … {done} رمزًا")
    _log(f"📊 مشى {done} رمزًا")
    rc = report(acc, year)
    _log("\n⚠️ **تشخيصُ معدَّلٍ لا ربحية (§⑥):** لا `R` هنا · انحيازُ بقاءٍ"
         " مخفَّف لا معدوم · بلا افتر · والفاعلُ «مضارب» تفسيرُ فيصل لا المقيس.")
    return rc


if __name__ == "__main__":
    sys.exit(main())
