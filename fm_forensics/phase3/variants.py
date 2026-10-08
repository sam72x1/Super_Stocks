"""🔬 PHASE 3 — §9 GATE_DEFINITION_VARIANT لمرساة اللمستين (بحثٌ فقط · لا إنتاج):
الإنتاجُ `tested_level(df, 30, 0.015, 2)`. الأشكالُ: tol 3% · tol 5% · lookback 60 · min_touches 1 — على صفوف فيصل المؤرَّخة والضوابط السالبة.
ومعه مِجَسٌّ تكميليٌّ (post-hoc · مُعلَن) لمصفوفة الميزات: ضابطٌ سالبٌ مطابَقُ التاريخ (رموزٌ غيرُ فيصل في المِجَسّ في تواريخ الإيجابيّات نفسِها)
لأن الضابطَ السالبَ المسجَّل (أيّامُ ترشيح البوت) يمرّ بالبوّابات بالبناء فيُربك ميزاتِ البوّابات."""
import csv
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

VARIANTS = {"tol3": dict(tol=0.03), "tol5": dict(tol=0.05), "lb60": dict(lookback=60), "touch1": dict(min_touches=1), "tol3_lb60": dict(tol=0.03, lookback=60)}


def make_tl(**kw):
    def f(df, lookback=30, tol=0.015, min_touches=2):
        return L._ORIG_TL(df, kw.get("lookback", lookback), kw.get("tol", tol), kw.get("min_touches", min_touches))
    return f


def run_variants():
    rows = list(csv.DictReader(open(os.path.join(L.OUT, "logo_rows.csv"), encoding="utf-8")))
    out = []
    for r in rows:
        if r["group"] not in ("faisal", "neg", "m2hi"):
            continue
        df = L.frame(L.bars_before(r["symbol"], r["date"]))
        row = dict(group=r["group"], symbol=r["symbol"], date=r["date"], CURRENT=r["CURRENT"], CURRENT_gate=r["CURRENT_gate"])
        for name, kw in VARIANTS.items():
            L.S.tested_level = make_tl(**kw)
            try:
                res, why, _ = L.run_gates(r["symbol"], df)
            finally:
                L.S.tested_level = L._ORIG_TL
            row[f"V_{name}"] = res if res != "REJECT" else L.reason_gate(why)
        out.append(row)
    L.write_csv(os.path.join(L.OUT, "anchor_variants.csv"), out)
    summ = []
    for grp in ("faisal", "neg", "m2hi"):
        g = [r for r in out if r["group"] == grp]
        s = dict(group=grp, n=len(g), PASS_current=sum(r["CURRENT"] == "PASS" for r in g))
        for name in VARIANTS:
            s[f"PASS_{name}"] = sum(r[f"V_{name}"] == "PASS" for r in g)
        summ.append(s)
    L.write_csv(os.path.join(HERE, "ANCHOR_VARIANTS.csv"), summ)
    for s in summ:
        print(s)


def supp_features():
    pos = list(csv.DictReader(open(os.path.join(HERE, "POSITIVE_TEMPORAL_CONTROLS.csv"), encoding="utf-8")))
    faisal_t = {r["ticker"] for r in L.faisal_rows()}
    pool = sorted(s for s in L.load()["daily"] if s not in faisal_t)
    random.seed(20261008)
    ctrl = []
    for p in pos:
        for s in random.sample(pool, 6):
            c = L.context(s, p["READY_OR_ENTRY_DATE"])
            if c:
                ctrl.append(dict(TICKER=s, DATE=p["READY_OR_ENTRY_DATE"], **c))
    L.write_csv(os.path.join(L.OUT, "supp_date_matched_controls.csv"), ctrl)
    def f(x):
        try:
            return float(x)
        except (TypeError, ValueError):
            return None
    tests = {"one_touch_fresh_low": lambda r: (f(r["tested_touches"]) is not None and f(r["tested_touches"]) < 2),
             "post_split_reference_frame": lambda r: f(r["drop_from_psh_pct"]) is not None,
             "rsi_below_33": lambda r: (f(r["rsi14"]) is not None and f(r["rsi14"]) < 33),
             "price_below_ema30": lambda r: (f(r["vs_ema30_pct"]) is not None and f(r["vs_ema30_pct"]) < 0),
             "unfilled_gap_below": lambda r: bool(r["gap_below_level"]),
             "held_>=3_sessions": lambda r: (f(r["bars_since_low30"]) is not None and f(r["bars_since_low30"]) >= 3),
             "drop_in_band": lambda r: (f(r["drop_pct"]) is not None and 71.72 <= f(r["drop_pct"]) <= 99.95),
             "spike_>=78": lambda r: (f(r["spike_pct"]) is not None and f(r["spike_pct"]) >= 78.27),
             "base_range<=120": lambda r: (f(r["base_range_pct"]) is not None and f(r["base_range_pct"]) <= 120)}
    out = []
    for name, t in tests.items():
        a = sum(1 for r in pos if t(r)); b = sum(1 for r in ctrl if t(r))
        odds = round(((a + 0.5) / (len(pos) - a + 0.5)) / ((b + 0.5) / (len(ctrl) - b + 0.5)), 2)
        out.append(dict(FEATURE=name, POS=f"{a}/{len(pos)}", DATE_MATCHED_CTRL=f"{b}/{len(ctrl)}", ODDS=odds,
                        NOTE="post-hoc supplementary (not pre-registered): date-matched non-Faisal names from the probe universe, 6 per positive, seed 20261008"))
        print(out[-1])
    L.write_csv(os.path.join(HERE, "MISSING_FEATURE_SUPP_DATE_MATCHED.csv"), out)


if __name__ == "__main__":
    run_variants()
    supp_features()
