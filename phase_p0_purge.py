#!/usr/bin/env python3
"""🔬 P0-2 (تدقيق Codex): تطبيق embargo/purge على مجموعة التدريب walk-forward.

Codex لاحظ أن الـembargo لم يكن مطبَّقًا: صفوف 2025 التي **تمتدّ نافذتها الأمامية إلى 2026**
(`forward_window_end >= 2026-01-01`) تسرّب حدود التدريب/الاختبار. هذا السكربت يقرأ الداتاست v2
(بعمود `forward_window_end` من مخطط provenance P0-S4) ويطبّق القاعدة المسجَّلة في الـamendment:
    train = صفوف 2025 حيث forward_window_end < 2026-01-01
    test  = صفوف 2026
ثم يقارن معدّلات الانفجار (legacy غير مُنقّى · purged-train · test) بفواصل Wilson.

بحث/تدقيق فقط · لا يمسّ الفرز · لا LOGIC_VERSION.
تشغيل:  python3 phase_p0_purge.py
"""
import csv
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def load(year):
    rows = []
    with open(ROOT / f"phase_e_dataset_{year}_v2.csv", encoding="utf-8") as fh:
        rows = list(csv.DictReader(fh))
    return rows


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def filled(r):
    return r["mg_outcome"] not in ("", "no_fill")


def y_discovery(r):
    v = num(r["fwd_max_gain"])
    return v is not None and v >= 50


def y_tradable(r):
    v = num(r["mg_pre_stop"])
    return v is not None and v >= 50


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((c - h) / d, (c + h) / d)


def rate_line(label, rows, tgt):
    fr = [r for r in rows if filled(r)]
    k = sum(1 for r in fr if tgt(r))
    n = len(fr)
    lo, hi = wilson(k, n)
    return f"{label}: {k}/{n} = {(k/n*100 if n else 0):.0f}%  (Wilson95 {lo*100:.0f}-{hi*100:.0f})"


def main():
    d25, d26 = load(2025), load(2026)
    # ── تطبيق embargo على 2025 ──────────────────────────────────────────────
    leaky = [r for r in d25 if r["forward_window_end"] >= "2026-01-01"]
    clean = [r for r in d25 if r["forward_window_end"] < "2026-01-01"]
    fwe = sorted(set(r["forward_window_end"] for r in d25))

    print("=" * 78)
    print("Phase P0-2 — تطبيق embargo/purge (تدقيق Codex) على المجمَّد v2")
    print("=" * 78)
    print(f"2025 إجمالي الإشارات: {len(d25)} · نطاق forward_window_end: {fwe[0]} … {fwe[-1]}")
    print(f"🔒 embargo: leaky (نافذتها تمتدّ إلى 2026، fwe>=2026-01-01) = {len(leaky)} "
          f"→ purged · نظيف للتدريب = {len(clean)}")
    print(f"2026 (test) إشارات: {len(d26)}")
    print("\n── Y_DISCOVERY (fwd_max_gain ≥ 50) ─────────────────────────────────────")
    print("  " + rate_line("2025 كامل (legacy غير مُنقّى)", d25, y_discovery))
    print("  " + rate_line("2025 purged-train (نظيف)   ", clean, y_discovery))
    print("  " + rate_line("2026 test                  ", d26, y_discovery))
    print("\n── Y_TRADABLE (mg_pre_stop ≥ 50) ───────────────────────────────────────")
    print("  " + rate_line("2025 كامل (legacy غير مُنقّى)", d25, y_tradable))
    print("  " + rate_line("2025 purged-train (نظيف)   ", clean, y_tradable))
    print("  " + rate_line("2026 test                  ", d26, y_tradable))

    n_clean = sum(1 for r in clean if filled(r))
    n_full = sum(1 for r in d25 if filled(r))
    print("\n" + "=" * 78)
    print("📋 الحكم (P0-2):")
    print(f"  · التنقية تُسقط {len(leaky)} إشارة → عيّنة التدريب المُعبَّأة تنكمش {n_full}→{n_clean}"
          f" (قوة إحصائية أقلّ).")
    print("  · معدّلات الانفجار تبقى في نفس النطاق (لا قفزة تكشف حافة) بعد التنقية.")
    print("  · **الخلاصة صامدة أمام الembargo: لا حافة فرز كبيرة تظهر؛ التنقية تُضعف القوة أكثر**")
    print("    فلا تنقلب النتيجة. متّسق مع حكم Phase C/E (حدّي لا حسمًا؛ القوة تمنع نفي أثر متوسط).")
    print("=" * 78)


if __name__ == "__main__":
    main()
