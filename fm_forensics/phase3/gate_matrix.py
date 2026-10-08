"""🔬 PHASE 3 — مصفوفةُ المفهوم ⟵ البوّابة (GATE_CONCEPT_MATRIX.csv) ومصفوفةُ LOGO المجمَّعة (LOGO_SUMMARY.csv).
المفهومُ والمصدرُ والسندُ من تتبّع الكود ودفتر المصادر (`FAISAL_SOURCE_LEDGER.md`)؛ والضرورةُ/الكفايةُ من `out/logo_rows.csv`."""
import collections
import csv
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import p3lib as L                        # noqa: E402

C = L.S.CONFIG
GATES = [
    # gate, implementation, claimed purpose, faisal evidence, source image, direct support, contradictory, temporal position
    ("M1", f"price ≥ MIN_PRICE={C['MIN_PRICE']:.2f} (envelope P100 of Faisal catalog; fallback 1.5)", "exclude sub-penny / dying names",
     "Faisal: «السنتات خارج الشرح» (floor ≈ $1); catalog P100 gives 0.40", "IMG_0153", "PARTIAL (concept yes, number from catalog envelope)", "Faisal traded names < $1 post-split (HCAI 0.46 in his own list)", "any time (identity)"),
    ("M2_CEIL", f"drop from 252-bar adjusted high ≤ MAX_DROP_PCT={C['MAX_DROP_PCT']:.2f}", "reject 'dying / split-trap' names",
     "no Faisal text; code comment only. Faisal selects reverse-split names and measures from the post-split frame (TG_1807/1811/1824/2200)", "TG_1807,TG_1811,TG_1824,TG_2200", "NONE", "Faisal's post-split frame contradicts a cumulative-adjusted ceiling (SXTC/HUBC Phase 2)", "identity, evaluated before any state"),
    ("M2_FLOOR", f"drop ≥ MIN_DROP_FLOOR={C['MIN_DROP_FLOOR']:.2f}", "'pivot = collapsed ≥ 50%' identity",
     "Faisal: pivot stock = exploded then collapsed; number from catalog envelope (P100)", "IMG_0151,TG_2077", "PARTIAL (concept DIRECT; number envelope)", "B_PSH Phase 2: post-split reference makes 46/52 Faisal WAIT cases fail this floor", "identity"),
    ("M3", f"best prior spike ≥ PRIOR_SPIKE_FLOOR={C['PRIOR_SPIKE_FLOOR']:.1f}% within {C['PRIOR_SPIKE_WINDOW']} sessions (excl. base window)", "'exploded ≥100% before' identity",
     "Faisal: «هدفك 100٪ اقل شي» is about the TARGET not the prior spike; window 20 sessions engineering", "IMG_0151", "PARTIAL/MISREAD (target vs prior spike)", "Phase 2: M3 first wall on 18/63 dated Faisal cases", "identity"),
    ("M4_RANGE", f"range of last {C['BASE_WINDOW']} sessions ≤ BASE_RANGE_MAX_PCT={C['BASE_RANGE_MAX_PCT']:.0f}% (owner 120)", "'accumulating in a narrow base'",
     "Faisal: stability 3-5 sessions above the low (IMG_0151, TG_2066) — not a 15-session range cap", "IMG_0151,TG_2066", "NONE for the metric (stability is a different measure)", "Phase 2: M4 wall on 11/63; pivots that just swept are wide by construction", "identity/structure"),
    ("M4_RISE", f"5-session gain ≤ RECENT_RISE_BLOCK_PCT={C['RECENT_RISE_BLOCK_PCT']:.0f}% (envelope)", "'don't chase an already-exploded name'",
     "Faisal: «لا تلاحق» concept (inferred)", "—", "INFERRED", "Faisal's second-wave entries (TG_58417 two waves) happen after a first rise", "identity"),
    ("M5", f"20-session mean $volume ≥ MIN_DOLLAR_VOL=${C['MIN_DOLLAR_VOL']:.0f} (envelope)", "liquidity floor",
     "Faisal: «لا يبنى على السيولة الحالية — السيولة السابقة المتمركزة» (X_61_VEEE); no numeric floor", "X_61_VEEE", "NONE for a numeric floor", "Faisal's own picks traded $10-170K/day at the base (AZI/DSY/EHGO/ZCMD 2026-07-04 note)", "identity"),
    ("RSI_OS", f"RSI14 min over 25 sessions ≤ RSI_OS_HARD={C['RSI_OS_HARD']:.0f}", "'touched oversold'",
     "Faisal: RSI 23-27 / «أقل من 30» for entry; the hard ceiling 69 is the envelope P100", "TG_2043,DRCT", "PARTIAL", "—", "watch/ready (timing)"),
    ("RSI_NOW", f"RSI14 now ≤ RSI_NOW_HARD={C['RSI_NOW_HARD']:.0f}", "'not already flown'",
     "Faisal: «مستحيل يصعد إذا RSI بمناطق 40» — contradicted by his own READY calls (Phase 1 RSI>40 case)", "TG_2043", "CONTRADICTED", "Phase 1 RSI_READY_FORENSICS", "ready (timing)"),
    ("SOFT", f"soft fails ≤ WATCH_MAX_FAILS={C['WATCH_MAX_FAILS']}", "'too many missing confirmations'",
     "none — engineering count of M6-M14 soft gates", "—", "NONE", "—", "post-identity"),
    ("ANCHOR", "tested_level(30 bars, tol 1.5%, ≥2 independent touches of the 30-bar low) required (ANCHOR_MODE=tested_strict)", "'enter on a level tested twice' (Faisal IMG_0451)",
     "Faisal: «1.75 ضربها مرتين ولا كسرها» — a level for ENTRY/STOP, said at entry time", "IMG_0451", "DIRECT for the entry anchor; NOT for candidate rejection", "Faisal FOCUS/WATCH begins at the first low (one touch): DKI 09-11→10-01, 27/63 dated cases rejected here", "ENTRY (Faisal) vs CANDIDATE (bot) — temporal mismatch"),
    ("SCORE", f"score ≥ SCORE_MIN={C['SCORE_MIN']}", "'enough confirmations'", "none", "—", "NONE", "—", "post-identity"),
    ("DEPTH", f"≥ MIN_BARS={C['MIN_BARS']} daily bars", "data sufficiency", "none; Faisal measures from the split date (TG_1807/1811) so a post-split history of 20-40 bars is enough for him", "TG_1807,TG_1811", "NONE", "B_CUT Phase 2: post-split histories of 22-42 bars are rejected silently", "identity (silent)"),
    ("NEAR", f"readiness ≥ NEAR_PCT={C['NEAR_PCT']:.0f}% (0 = inactive)", "'far from entry'", "none", "—", "INACTIVE", "—", "ready"),
    ("M14_FLOAT", f"float ≤ FLOAT_GATE_MAX={C['FLOAT_GATE_MAX']:,} (unknown passes)", "small float", "Faisal: float < 2M for the split recipe; 50M is ours", "IMG_0151", "PARTIAL", "—", "post-select (enrich)"),
    ("BORROW", f"available-to-borrow ≤ BORROW_AVAIL_MAX={C['BORROW_AVAIL_MAX']:,} (unknown passes)", "Faisal's 'short under 20k'", "«تحت 20 ألف» (IMG_0151) — DIRECT", "IMG_0151", "DIRECT", "—", "post-select (enrich)"),
]


def main():
    path = os.path.join(L.OUT, "logo_rows.csv")
    rows = list(csv.DictReader(open(path, encoding="utf-8"))) if os.path.exists(path) else []
    fa = [r for r in rows if r["group"] == "faisal"]
    neg = [r for r in rows if r["group"] in ("neg", "m2hi")]
    anc = [r for r in rows if r["group"] == "anchor"]
    first = collections.Counter(r["CURRENT_gate"] for r in fa if r["CURRENT"] != "PASS")
    base_pass_fa = sum(r["CURRENT"] == "PASS" for r in fa); base_pass_neg = sum(r["CURRENT"] == "PASS" for r in neg)
    out = []
    summ = []
    for g, impl, purpose, ev, src, direct, contra, tpos in GATES:
        col = f"NO_{g}"
        if rows and col in rows[0]:
            rest_fa = sum(r[col] == "PASS" for r in fa); rest_neg = sum(r[col] == "PASS" for r in neg)
            rest_anc = sum(r[col] == "PASS" for r in anc)
            nec = f"first wall on {first.get(g, 0)}/{len(fa)} Faisal rows"
            suf = (f"removing it: Faisal PASS {base_pass_fa}→{rest_fa} of {len(fa)}; negative/matched PASS {base_pass_neg}→{rest_neg} of {len(neg)}; anchor-days PASS {sum(r['CURRENT']=='PASS' for r in anc)}→{rest_anc} of {len(anc)}")
            summ.append(dict(GATE=g, FAISAL_FIRST_WALL=first.get(g, 0), FAISAL_N=len(fa), FAISAL_PASS_CURRENT=base_pass_fa, FAISAL_PASS_WITHOUT=rest_fa,
                             NEG_N=len(neg), NEG_PASS_CURRENT=base_pass_neg, NEG_PASS_WITHOUT=rest_neg, ANCHOR_DAYS=len(anc), ANCHOR_PASS_WITHOUT=rest_anc,
                             RESTORE_RATIO=round((rest_fa - base_pass_fa) / max(1, len(fa) - base_pass_fa), 3),
                             NEG_INFLATION=round(rest_neg / max(1, base_pass_neg), 2)))
        else:
            nec = "not in LOGO (post-select gate)"; suf = "not measurable from bars (needs float/borrow history)"
        status = ("CONTRADICTED" if "CONTRADICTED" in direct else "SUPPORTED" if direct.startswith("DIRECT") and "NOT" not in direct
                  else "PARTIALLY_SUPPORTED" if direct.startswith("PARTIAL") or direct.startswith("DIRECT") else "UNSUPPORTED" if direct in ("NONE", "INFERRED", "INACTIVE") or direct.startswith("NONE") else "UNKNOWN")
        out.append(dict(GATE=g, IMPLEMENTATION=impl, CLAIMED_PURPOSE=purpose, FAISAL_EVIDENCE=ev, SOURCE_IMAGE=src, DIRECT_SUPPORT=direct,
                        CONTRADICTORY_EVIDENCE=contra, TEMPORAL_POSITION=tpos, NECESSITY_EVIDENCE=nec, SUFFICIENCY_EVIDENCE=suf, STATUS=status))
    L.write_csv(os.path.join(HERE, "GATE_CONCEPT_MATRIX.csv"), out)
    if summ:
        L.write_csv(os.path.join(HERE, "LOGO_SUMMARY.csv"), summ)
        for s in summ:
            print(s)
    print("first walls (Faisal rows):", first.most_common(), "base PASS", base_pass_fa, "/", len(fa))
    if rows:
        allid = sum(r["NO_ALL_IDENTITY"] == "PASS" for r in fa)
        print("ALL identity gates neutral → Faisal PASS", allid, "/", len(fa), "| remaining:", collections.Counter(r["NO_ALL_IDENTITY"] for r in fa if r["NO_ALL_IDENTITY"] != "PASS"))


if __name__ == "__main__":
    main()
