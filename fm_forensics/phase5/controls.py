"""🔬 PHASE 5 §11 — الضوابطُ المطابَقة بإجراء `PHASE5_PREREG.md §H` (مجمَّدٌ قبل أيّ رقم): لكلّ وحدةٍ أوّليّةٍ (ورقةٌ غيرُ مرساة لها شموع)
عند يوم قرارها D: المرشَّحون = مجمعُ 160 رمزًا بلا أيّ ذكرٍ لفيصل · أهلٌ بلا مرساة عند D (بوّاباتُ الإنتاج بالاسم عبر `p4lib.eligible`) ·
≥120 شمعة · الأقربُ في (log سعر · ATR14%/10 · log حجمِ الدولار 20 /2) بكاليبر 1.5 حتى 4 · **بلا مطابقةٍ على الميزات المختبَرة**
(لا تقسيم) · بذرة 20261008 ⟵ `PHASE5_MATCHED_CONTROL_MANIFEST.csv` بتشخيصات التوازن. لا تُقرأ ميزةٌ غيرُ شمعيّةٍ هنا."""
import collections
import math
import os
import statistics

import p5lib as P

Q, L = P.Q, P.L
CALIPER = 1.5
K = 4
MIN_BARS = 120


def dist(a, b):
    la, lb = math.log10(max(float(a["price"]), 1e-6)), math.log10(max(float(b["price"]), 1e-6))
    da, db = math.log10(max(float(a.get("dollar_vol20") or 1), 1)), math.log10(max(float(b.get("dollar_vol20") or 1), 1))
    aa, ab = float(a.get("atr14_pct") or 0), float(b.get("atr14_pct") or 0)
    return ((la - lb) ** 2 + ((aa - ab) / 10.0) ** 2 + ((da - db) / 2.0) ** 2) ** 0.5


def price_bucket(px):
    return "<1" if px < 1 else ("1-5" if px <= 5 else ">5")


def smd(xs, ys):
    """standardized mean difference (positives vs controls) على متغيّرات المطابقة."""
    xs = [x for x in xs if x is not None]
    ys = [y for y in ys if y is not None]
    if len(xs) < 2 or len(ys) < 2:
        return None
    sx, sy = statistics.pstdev(xs), statistics.pstdev(ys)
    s = ((sx * sx + sy * sy) / 2) ** 0.5
    return round((statistics.mean(xs) - statistics.mean(ys)) / s, 3) if s > 0 else 0.0


def main():
    man = P.read_csv(os.path.join(P.HERE, "PHASE5_COHORT_MANIFEST.csv"))
    prim = [r for r in man if r["PHASE5_PRIMARY_UNIT"] == "1"]
    tl = P.timeline_all()
    any_faisal = {r["TICKER"] for r in tl} | set(P.ANCHORS)
    pool = sorted(s for s in L.load()["daily"] if s not in any_faisal)
    Q.load_extra()
    rows, posd = [], []
    used = collections.Counter()
    diag = collections.defaultdict(list)
    for r in sorted(prim, key=lambda x: (x["DECISION_DATE"], x["SECURITY_ID"])):
        t, D = r["SECURITY_ID"], r["DECISION_DATE"]
        c = L.context(t, D)
        if not c:
            posd.append(dict(SECURITY_ID=t, DECISION_EPISODE_ID=r["DECISION_EPISODE_ID"], MATCHING_DATE=D, N_CONTROLS=0, UNMATCHED_CASES=1, EXCLUSION_REASON="no context (insufficient bars)"))
            continue
        cands = []
        for s in pool:
            if (s, D) not in Q.bot_states() and (s, D) not in Q._EXTRA:
                continue                      # gate rows for pool×D were produced in Phase 4 (cached); a missing pair is counted below
            el, g = Q.eligible(s, D)
            if not el:
                continue
            cs = L.context(s, D)
            if not cs or cs["bars"] < MIN_BARS:
                continue
            dd = dist(c, cs)
            if dd <= CALIPER:
                cands.append((dd, s, cs))
        cands.sort(key=lambda x: (x[0], x[1]))
        chosen = cands[:K]
        missing_gate = sum(1 for s in pool if (s, D) not in Q.bot_states() and (s, D) not in Q._EXTRA)
        for dd, s, cs in chosen:
            used[s] += 1
            rsp = int(bool(cs.get("last_rsplit")) and (cs.get("bars_since_split") or 9999) <= 252)
            rows.append(dict(CONTROL=s, CONTROL_EPISODE_ID=f"{s}_C{D}", MATCHED_POSITIVE=t, POSITIVE_EPISODE_ID=r["DECISION_EPISODE_ID"], MATCHING_DATE=D,
                             MATCHING_VARIABLES="log10 price · ATR14%/10 · log10 dollar-vol20/2 (candles < D) · eligibility without anchor · >=120 bars",
                             MATCHING_DISTANCE=round(dd, 3), CALIPER_IF_USED=CALIPER, CONTROL_SELECTION_METHOD="nearest-neighbour, up to 4, pool without any Faisal unit, seed 20261008 (deterministic tie-break by symbol)",
                             PRICE=cs["price"], ATR14_PCT=cs["atr14_pct"], DOLLAR_VOL20=cs["dollar_vol20"], PRICE_BUCKET=price_bucket(float(cs["price"])),
                             POS_PRICE=c["price"], POS_ATR14_PCT=c["atr14_pct"], POS_DOLLAR_VOL20=c["dollar_vol20"], POS_PRICE_BUCKET=price_bucket(float(c["price"])),
                             RSPLIT_252_NOT_MATCHED=rsp, MATCH_QUALITY=("close" if dd <= 0.5 else ("fair" if dd <= 1.0 else "loose")),
                             LABEL_TIER="UNKNOWN (absence of a Faisal post; see prereg §F)", EXCHANGE="NASDAQ", DATA_DEPTH_BARS=cs["bars"],
                             CURRENT_RESULT=Q.gate_row(s, D)["result"], CURRENT_GATE=Q.gate_row(s, D)["gate"], POOL_GATE_ROWS_MISSING=missing_gate))
            diag["price"].append((math.log10(max(float(c["price"]), 1e-6)), math.log10(max(float(cs["price"]), 1e-6))))
            diag["atr"].append((float(c.get("atr14_pct") or 0), float(cs.get("atr14_pct") or 0)))
            diag["dv"].append((math.log10(max(float(c.get("dollar_vol20") or 1), 1)), math.log10(max(float(cs.get("dollar_vol20") or 1), 1))))
            diag["rsp"].append((int(bool(c.get("last_rsplit")) and (c.get("bars_since_split") or 9999) <= 252), rsp))
        posd.append(dict(SECURITY_ID=t, DECISION_EPISODE_ID=r["DECISION_EPISODE_ID"], MATCHING_DATE=D, N_CONTROLS=len(chosen), N_CANDIDATES_IN_CALIPER=len(cands),
                         UNMATCHED_CASES=int(not chosen), EXCLUSION_REASON=("" if chosen else "no eligible pool symbol within the caliper"), POOL_GATE_ROWS_MISSING=missing_gate))
    bal = {k: smd([a for a, _ in v], [b for _, b in v]) for k, v in diag.items()}
    for r in rows:
        r["BALANCE_DIAGNOSTICS"] = f"SMD log10price={bal.get('price')} · ATR14={bal.get('atr')} · log10dv={bal.get('dv')} · rsplit252(not matched)={bal.get('rsp')}"
        r["UNMATCHED_CASES"] = sum(1 for p in posd if p["UNMATCHED_CASES"])
        r["EXCLUSION_REASON"] = ""
    P.write_csv(os.path.join(P.HERE, "PHASE5_MATCHED_CONTROL_MANIFEST.csv"), rows)
    P.write_csv(os.path.join(P.OUT, "control_matching_positives.csv"), posd)
    print(f"primary units {len(prim)} · matched {sum(1 for p in posd if not p['UNMATCHED_CASES'])} · unmatched {sum(1 for p in posd if p['UNMATCHED_CASES'])} · control-days {len(rows)} · distinct controls {len(used)} · reused {sum(1 for v in used.values() if v > 1)} (max {max(used.values()) if used else 0})")
    print("balance (SMD pos−ctrl):", bal)
    print("controls per positive:", dict(collections.Counter(p["N_CONTROLS"] for p in posd)))
    print("pool gate rows missing (max over dates):", max((p["POOL_GATE_ROWS_MISSING"] for p in posd), default=0))


if __name__ == "__main__":
    main()
