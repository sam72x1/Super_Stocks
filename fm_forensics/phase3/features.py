"""🔬 PHASE 3 — ميزاتُ فيصل مقابل تمثيل البوت (MISSING_FEATURE_MATRIX.csv) ومِجَسُّ الفصل بين الضوابط الموجبة والسالبة
(ميزاتٌ من الشموع والتقسيمات قبل يوم القرار وحدَها — لا نظرَ للأمام). الفصلُ يُقاس بنسبة الأرجحيّة على الضوابط المثبَّتة في العقد §⑤."""
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402


def f(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


FEATURES = [
    # name, test(row)->bool|None, evidence, first appearance, temporal role, bot representation, status
    ("post_split_reference_frame", lambda r: (f(r["drop_from_psh_pct"]) is not None), "TG_1807,TG_1811,TG_1813,TG_1824,TG_2200 (MA30 and ÷2 from the split date)", "2026-07-23 (TG_1807)", "FOCUS (defines the regime)", "ABSENT (M2 uses the cumulative-adjusted 252-bar high; BT_SPLIT_REF_M2 backtest-only)", ""),
    ("recent_reverse_split", lambda r: bool(r["last_rsplit"]), "IMG_0151,TG_2077 (split = founding event); X_checklist «تاريخ التقسيم»", "2026-07 (IMG_0151)", "FOCUS input", "PARTIAL (split hunter tool only; not in candidate gates; DQ quarantine only)", ""),
    ("one_touch_fresh_low (FOCUS starts at first low)", lambda r: (f(r["tested_touches"]) is not None and f(r["tested_touches"]) < 2), "DKI TG_57894 (wait for sweep after first low); X_13_NUWE; IMG_0689", "2026-07-28 (NUWE)", "FOCUS/WATCH", "CONTRADICTED by ANCHOR gate (two touches required to be a candidate)", ""),
    ("rsi_below_33_at_observation", lambda r: (f(r["rsi14"]) is not None and f(r["rsi14"]) < 33), "TG_2043 (23-27), DRCT («rsi اقل من 30»)", "2026-07 (TG_2043)", "WATCH→READY timing", "PRESENT (RSI_OS soft/hard; three-condition tool)", ""),
    ("price_below_ema30", lambda r: (f(r["vs_ema30_pct"]) is not None and f(r["vs_ema30_pct"]) < 0), "TG_1807 (MA30 from split date as the first target), M12 context", "2026-07-23", "WATCH", "PARTIAL (MA soft gate measures distance above, not the split-dated MA30)", ""),
    ("unfilled_gap_below", lambda r: bool(r["gap_below_level"]), "TG_57869 (CRE «الفجوة تحت لازم تتغطى»), SNAL", "2026-09 (CRE)", "validity rule (WAIT while unfilled)", "ABSENT (gap_analysis counts gaps above; gap-below is not a validity rule) — T-GAPBELOW «لا قياس»", ""),
    ("held_level_>=3_sessions (stability)", lambda r: (f(r["bars_since_low30"]) is not None and f(r["bars_since_low30"]) >= 3), "IMG_0151 «حافظ ع قاعه 3 جلسات», TG_2066, X_85_YMT (5 sessions)", "2026-07 (IMG_0151)", "WATCH→READY", "PRESENT as display (pivot_stability); NOT a gate (T-STABILITY rejected as reject-gate)", ""),
    ("drop_from_52w_in_band", lambda r: (f(r["drop_pct"]) is not None and 71.72 <= f(r["drop_pct"]) <= 99.95), "catalog envelope P100 (not a Faisal number)", "2026-08-06", "identity", "PRESENT (M2 band)", ""),
    ("prior_spike_>=78%", lambda r: (f(r["spike_pct"]) is not None and f(r["spike_pct"]) >= 78.27), "envelope; IMG_0151 is about the target", "2026-08-06", "identity", "PRESENT (M3)", ""),
    ("base_range_15<=120%", lambda r: (f(r["base_range_pct"]) is not None and f(r["base_range_pct"]) <= 120), "owner decision 2026-08-10 (not Faisal)", "2026-08-10", "identity", "PRESENT (M4)", ""),
]


def main():
    pos = list(csv.DictReader(open(os.path.join(HERE, "POSITIVE_TEMPORAL_CONTROLS.csv"), encoding="utf-8")))
    neg = list(csv.DictReader(open(os.path.join(HERE, "NEGATIVE_TEMPORAL_CONTROLS.csv"), encoding="utf-8")))
    pos_na = [r for r in pos if r["ANCHOR"] == "0"]
    out = []
    for name, test, ev, first, role, rep, _ in FEATURES:
        def cnt(rows):
            vals = [test(r) for r in rows]
            known = [v for v in vals if v is not None]
            return sum(1 for v in known if v), len(known)
        a, na = cnt(pos); b, nb = cnt(neg); a2, na2 = cnt(pos_na)
        pa = a / na if na else None; pb = b / nb if nb else None
        odds = None
        if na and nb and 0 < a < na and 0 < b < nb:
            odds = round(((a + 0.5) / (na - a + 0.5)) / ((b + 0.5) / (nb - b + 0.5)), 2)
        elif na and nb:
            odds = round(((a + 0.5) / (na - a + 0.5)) / ((b + 0.5) / (nb - b + 0.5)), 2)
        status = "ABSENT" if rep.startswith("ABSENT") else ("CONTRADICTED" if rep.startswith("CONTRADICTED") else ("PARTIAL" if rep.startswith("PARTIAL") else "PRESENT"))
        sep = "n/a"
        if pa is not None and pb is not None:
            sep = f"pos {a}/{na} ({pa:.0%}) vs neg {b}/{nb} ({pb:.0%}) · odds {odds}"
        causal = ("INSUFFICIENT_EVIDENCE" if (na < 5 or nb < 5) else ("SEPARATES (odds≥3)" if odds and odds >= 3 else ("INVERSE (odds≤0.33)" if odds and odds <= 0.33 else "NO_SEPARATION")))
        out.append(dict(FEATURE=name, EVIDENCE=ev, FIRST_APPEARANCE=first, TEMPORAL_ROLE=role, CURRENT_BOT_REPRESENTATION=rep, STATUS=status,
                        INDEPENDENT_SUPPORT=f"positive controls (non-anchor) {a2}/{na2}", CONTRADICTORY_CASES=f"negative controls with feature {b}/{nb}",
                        SEPARATION=sep, CAUSAL_STATUS=causal))
    L.write_csv(os.path.join(HERE, "MISSING_FEATURE_MATRIX.csv"), out)
    for r in out:
        print(r["FEATURE"], "|", r["STATUS"], "|", r["SEPARATION"], "|", r["CAUSAL_STATUS"])
    print("positives", len(pos), "(non-anchor", len(pos_na), ") negatives", len(neg))


if __name__ == "__main__":
    main()
