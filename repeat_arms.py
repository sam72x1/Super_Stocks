#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔁 T-REPEAT — «سلوكُ المضارب يتكرّر؟» (العقد: `repeat_prereg.md` مدفوعٌ
**قبل** أيّ رقم · أمرُ المالك).

**إعادةُ استعمالٍ بالاسم:** تعريفُ الرفعة = عناقيدُ `spike_info` الإنتاجية
بثوابتها (`PRIOR_SPIKE_WINDOW` · `PRIOR_SPIKE_PCT` · فجوة 20 جلسة) — هنا فقط
نستخرج **مقدارَ كلّ عنقودٍ** بدل الأكبر. 🔒 خارج مسار الفرز كليًّا (الإنتاج لا
يستورد هذا الملف) · لا `LOGIC_VERSION` · قياسٌ فقط."""
from __future__ import annotations

import os
import random
import sys

SHUFFLES = 200            # عددُ الخلطات (العقد §③)
SEED = 42                 # بذرةٌ حتمية (العقد §③)
CLUSTER_GAP = 20          # فجوةُ استقلال العناقيد — رقمُ `spike_info` نفسُه


def _log(m):
    print(m, flush=True)


def spike_magnitudes(close) -> list:
    """نقيّة: مقاديرُ الرفعات المستقلّة بترتيبها الزمنيّ (‏% لكل عنقود).

    نفسُ آلة `spike_info` حرفيًّا (النِسَبُ على كل نافذة 1..`PRIOR_SPIKE_WINDOW`
    وعتبةُ `PRIOR_SPIKE_PCT` وفجوةُ 20 جلسة) — والمختلفُ الوحيد: بدل «الأكبر
    عبر التاريخ» نُرجع **أكبرَ نسبةٍ داخل كلّ عنقود**."""
    import numpy as np                                           # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    c = np.asarray(close, dtype=float)
    n = len(c)
    if n < 15:
        return []
    w_max = int(S.CONFIG["PRIOR_SPIKE_WINDOW"])
    # 📜 ملحق ⑥: العتبة = `EXPLOSION_PCT` الإنتاجية (كاشف الانفجارات) لا
    # `PRIOR_SPIKE_PCT` — النافذةُ تحت الظرف 164% تجعل شريحة «دون 100%»
    # فارغةً بالبناء فيموت مقياسُ سؤال المالك (اكتُشف قبل أيّ تشغيلة).
    thr = float(S.CONFIG.get("EXPLOSION_PCT", 50.0)) / 100.0
    best_at = {}                                  # فهرسُ النهاية ⟶ أقصى نسبةٍ عنده
    for w in range(1, w_max + 1):
        if n <= w:
            break
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = c[w:] / np.where(c[:-w] > 0, c[:-w], np.nan) - 1.0
        ratio = np.nan_to_num(ratio, nan=0.0)
        for j in np.where(ratio >= thr)[0]:
            i = int(j + w)
            v = float(ratio[j])
            if v > best_at.get(i, 0.0):
                best_at[i] = v
    if not best_at:
        return []
    mags, cur, last = [], 0.0, -10_000
    for i in sorted(best_at):
        if i - last >= CLUSTER_GAP and cur > 0.0:
            mags.append(cur * 100.0)
            cur = 0.0
        cur = max(cur, best_at[i])
        last = i
    if cur > 0.0:
        mags.append(cur * 100.0)
    return mags


def spearman(xs, ys) -> float:
    """نقيّة: سبيرمان بلا scipy (رُتَبٌ بمتوسط التعادل ثم بيرسون على الرُتَب)."""
    import numpy as np                                           # noqa: PLC0415

    def _ranks(v):
        v = np.asarray(v, dtype=float)
        order = np.argsort(v, kind="mergesort")
        r = np.empty(len(v), dtype=float)
        i = 0
        while i < len(v):
            j = i
            while j + 1 < len(v) and v[order[j + 1]] == v[order[i]]:
                j += 1
            r[order[i:j + 1]] = (i + j) / 2.0 + 1.0
            i = j + 1
        return r
    rx, ry = _ranks(xs), _ranks(ys)
    rx -= rx.mean()
    ry -= ry.mean()
    den = float((rx ** 2).sum() ** 0.5 * (ry ** 2).sum() ** 0.5)
    return float((rx * ry).sum() / den) if den > 0 else 0.0


def wilson(k, n, z=1.96):
    """نقيّة: فاصل Wilson (نفس صيغة `rebound_arms.wilson`)."""
    if n <= 0:
        return (0.0, 1.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    m = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - m) / d, (c + m) / d)


def collect_pairs(hist, catalog=frozenset()):
    """أزواجُ (السابقة، التالية) لكل الرموز + شريحةُ الكتالوج. ترجع (أزواج، أزواج-كتالوج، عدّادات)."""
    pairs, cat_pairs = [], []
    n_syms = n_spiky = 0
    for sym, df in hist.items():
        try:
            c = df["Close"].values
        except Exception:                                        # noqa: BLE001
            continue
        n_syms += 1
        mags = spike_magnitudes(c)
        if len(mags) < 2:
            continue
        n_spiky += 1
        ps = list(zip(mags[:-1], mags[1:]))
        pairs.extend(ps)
        if str(sym).upper() in catalog:
            cat_pairs.extend(ps)
    return pairs, cat_pairs, {"syms": n_syms, "spiky": n_spiky}


def judge(pairs) -> dict:
    """المقياسان المسجَّلان (§③): سبيرمان مقابل 200 خلطة · وشريحتا 30/100."""
    prev = [a for a, _ in pairs]
    nxt = [b for _, b in pairs]
    rho = spearman(prev, nxt)
    rng = random.Random(SEED)
    null = []
    for _ in range(SHUFFLES):
        sh = list(nxt)
        rng.shuffle(sh)
        null.append(spearman(prev, sh))
    null.sort()
    p95 = null[int(0.95 * (len(null) - 1))]
    p50 = null[len(null) // 2]
    # شريحتا سؤال المالك: السابقة دون 100% مقابل 100% فأكثر
    lo_next = [b for a, b in pairs if a < 100.0]
    hi_next = [b for a, b in pairs if a >= 100.0]

    def _med(v):
        s = sorted(v)
        return s[len(s) // 2] if s else None

    def _p100(v):
        k = sum(1 for x in v if x >= 100.0)
        w = wilson(k, len(v))
        return {"k": k, "n": len(v), "pct": (100.0 * k / len(v)) if v else None,
                "lo": 100 * w[0], "hi": 100 * w[1]}
    return {"n_pairs": len(pairs), "rho": rho, "null_p95": p95, "null_p50": p50,
            "beats_null": bool(rho > p95),
            "lo_bin": {"median_next": _med(lo_next), **_p100(lo_next)},
            "hi_bin": {"median_next": _med(hi_next), **_p100(hi_next)}}


def report(tag, res):
    _log(f"\n📊 {tag}: أزواج={res['n_pairs']} · ρ={res['rho']:+.4f} "
         f"(عشوائي p50={res['null_p50']:+.4f} · p95={res['null_p95']:+.4f}) ⇒ "
         f"{'✅ فوق p95' if res['beats_null'] else '🔴 لا يتجاوز p95'}")
    for name, b in (("السابقة دون 100%", res["lo_bin"]),
                    ("السابقة 100% فأكثر", res["hi_bin"])):
        if b["n"]:
            _log(f"   {name:<22} n={b['n']:<6} وسيطُ التالية="
                 f"{b['median_next']:.1f}% · P(التالية≥100%)="
                 f"{b['pct']:.1f}% [{b['lo']:.1f},{b['hi']:.1f}]")
        else:
            _log(f"   {name:<22} n=0 — لا شريحة")


CATALOG = frozenset("""AZI DSY EHGO ZCMD JZ SPRC JEM WORX NUWE ONCO KUST LABT
ELAB XHLD GWAV AUUD FRSX ENPH VMAR CUR NAMM MTVA TRUG MWC SVRE MBRX HTCR BNKK
CHSN PAVS HUBC WETO CAPR APVO CMTL KLXE""".split())


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 74}\n🔁 T-REPEAT — لقطة {year}\n{'=' * 74}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 as-of {asof} · رموز {len(hist)}")
    pairs, cat_pairs, cnt = collect_pairs(hist, CATALOG)
    _log(f"🩺 رموز {cnt['syms']} · فيها رفعتان فأكثر {cnt['spiky']}")
    if not pairs:
        _log("⛔ صفرُ أزواج (بصمة الـno-op) ⇒ خروج 4.")
        return 4
    report("السوق الكامل", judge(pairs))
    if cat_pairs:
        report("شريحة الكتالوج (وصفيًّا — لا حكم، n صغير)", judge(cat_pairs))
    else:
        _log("\nℹ️ شريحة الكتالوج: صفر أزواج في هذي اللقطة.")
    _log("\n⚠️ العقد §④: سقفُ النجاح سطرُ عرضٍ فقط — لا بوّابةَ خروجٍ ولا عتبة.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
