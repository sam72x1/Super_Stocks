"""🔬 PHASE 5 §16–§20 — التحليلُ المسجَّل مسبقًا (`PHASE5_PREREG.md`): لكلّ عائلةٍ مقاماتٌ وتوافرٌ · غيرُ مُعدَّل (ويلسون · فيشر) ·
مطابَق (فرقٌ داخل الطبقة · بوتستراب عنقوديّ بالورقة · 98.75% بونفيروني) · مُعدَّل (مانتل-هينزل على دلاء السعر) · H5 · التكذيب (الضرورة ·
الإزاحة الزمنيّة 60 جلسة · الاجتثاث). الأوضاع: discovery · validation (تلزمها بصمةُ تجميد discovery) · all (وصفيّ). قراءةٌ فقط."""
import collections
import hashlib
import json
import math
import os
import random
import sys

import p5lib as P
import inventory as INV

L = P.L
SEED = 20261008
B = 2000
ALPHA = 0.05 / 4
FAMILIES = {
    "H1_FLOAT": dict(feature="FLOAT_SHARES", cond=lambda v: float(v) <= 5_000_000, cont=lambda v: math.log10(max(float(v), 1)), label="float <= 5,000,000", direction=+1),
    "H2_OFFERING": dict(feature="DAYS_SINCE_LAST_FINAL_PROSPECTUS", cond=lambda v: float(v) <= 90, cont=lambda v: float(v), label="final prospectus within 90 d", direction=-1),
    "H3_BORROW": dict(feature="AVAILABLE_SHARES", cond=lambda v: float(v) < 20_000, cont=lambda v: math.log10(max(float(v), 1)), label="available < 20,000", direction=+1),
    "H4_SPLIT": dict(feature="SESSIONS_SINCE_LAST_REVERSE_SPLIT", cond=None, cont=None, label="reverse split within 120 calendar days", direction=+1),
}
SENS_WINDOWS = (60, 252)


def wilson(k, n):
    return P.wilson(k, n)


def fisher(a, b, c, d):
    """two-sided Fisher exact p for [[a,b],[c,d]] (hypergeometric, no scipy)."""
    n = a + b + c + d
    r1, c1 = a + b, a + c
    def pmf(x):
        return math.exp(math.lgamma(r1 + 1) - math.lgamma(x + 1) - math.lgamma(r1 - x + 1) + math.lgamma(n - r1 + 1) - math.lgamma(c1 - x + 1) - math.lgamma(n - r1 - c1 + x + 1) - math.lgamma(n + 1) + math.lgamma(c1 + 1) + math.lgamma(n - c1 + 1))
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    p0 = pmf(a)
    return round(min(1.0, sum(pmf(x) for x in range(lo, hi + 1) if pmf(x) <= p0 * (1 + 1e-9))), 4)


def mh_or(strata):
    """Mantel–Haenszel pooled OR over strata [(a,b,c,d)] where a=pos&cond, b=pos&!cond, c=ctrl&cond, d=ctrl&!cond."""
    num = den = 0.0
    for a, b, c, d in strata:
        n = a + b + c + d
        if n == 0:
            continue
        num += a * d / n
        den += b * c / n
    return round(num / den, 3) if den > 0 else None


def sets():
    man = P.read_csv(os.path.join(P.HERE, "PHASE5_COHORT_MANIFEST.csv"))
    prim = sorted({r["SECURITY_ID"] for r in man if r["PHASE5_PRIMARY_UNIT"] == "1"})
    disc = [t for t in prim if int(hashlib.sha256(("P5-2026-10-08:" + t).encode()).hexdigest()[-1], 16) % 2 == 0]
    return man, prim, disc, [t for t in prim if t not in disc]


def fam_value(fam, rows_by_unit, unit):
    """(available, condition, continuous, verified) for a unit from inventory rows."""
    spec = FAMILIES[fam]
    for r in rows_by_unit.get(unit, []):
        if r["FEATURE_NAME"] != spec["feature"]:
            continue
        if fam == "H4_SPLIT":
            if r["VALUE"] == "NO_CONFIRMED_PRIOR_REVERSE_SPLIT":
                return True, False, None, int(r.get("POINT_IN_TIME_VERIFIED") or 0), r
            if r["VALUE"] == "" or r["MISSING_REASON"]:
                return False, None, None, 0, r
            days = float(r["DAYS_VALUE_TO_DECISION"])
            return True, days <= 120, math.log10(max(float(r["VALUE"]), 1)), int(r.get("POINT_IN_TIME_VERIFIED") or 0), r
        if fam == "H2_OFFERING":
            if r["MISSING_REASON"] in ("NOT_COLLECTED", "IDENTIFIER_UNRESOLVED", "SOURCE_CONFLICT"):
                return False, None, None, 0, r
            if r["VALUE"] == "":                       # filings exist, no final prospectus before T ⇒ documented absence
                return (r["MISSING_REASON"] == ""), False, None, 1, r
            return True, spec["cond"](r["VALUE"]), spec["cont"](r["VALUE"]), int(r.get("POINT_IN_TIME_VERIFIED") or 0), r
        if r["VALUE"] == "" or r["MISSING_REASON"]:
            return False, None, None, 0, r
        return True, spec["cond"](r["VALUE"]), spec["cont"](r["VALUE"]), int(r.get("POINT_IN_TIME_VERIFIED") or 0), r
    return False, None, None, 0, None


def boot_ci(vals_by_cluster, fn, seed=SEED, b=B, alpha=ALPHA):
    """cluster bootstrap: resample clusters (positive securities) with replacement; fn(list_of_cluster_values) → statistic."""
    keys = sorted(vals_by_cluster)
    rng = random.Random(seed)
    stats = []
    for _ in range(b):
        sample = [vals_by_cluster[keys[rng.randrange(len(keys))]] for _ in keys]
        s = fn(sample)
        if s is not None:
            stats.append(s)
    if not stats:
        return (None, None)
    stats.sort()
    lo = stats[int((alpha / 2) * (len(stats) - 1))]
    hi = stats[int((1 - alpha / 2) * (len(stats) - 1))]
    return (round(lo, 4), round(hi, 4))


def analyse(mode, fam, units_pos, ctrl_by_pos, rows_by_unit, out_rows, tag=""):
    spec = FAMILIES[fam]
    # availability
    pos_av = {u: fam_value(fam, rows_by_unit, u) for u in units_pos}
    ctrl_units = sorted({c for u in units_pos for c in ctrl_by_pos.get(u, [])})
    ctrl_av = {c: fam_value(fam, rows_by_unit, c) for c in ctrl_units}
    n_pos_av = sum(1 for v in pos_av.values() if v[0])
    n_ctrl_av = sum(1 for v in ctrl_av.values() if v[0])
    av_pos = n_pos_av / len(units_pos) if units_pos else 0
    av_ctrl = n_ctrl_av / len(ctrl_units) if ctrl_units else 0
    verified = sum(1 for v in list(pos_av.values()) + list(ctrl_av.values()) if v[0] and v[3])
    used = n_pos_av + n_ctrl_av
    rec = dict(MODE=mode, FAMILY=fam, CONDITION=spec["label"], TAG=tag, N_POSITIVES=len(units_pos), N_POS_WITH_VALUE=n_pos_av, N_CONTROL_UNITS=len(ctrl_units), N_CTRL_WITH_VALUE=n_ctrl_av,
               AVAIL_POS=round(av_pos, 3), AVAIL_CTRL=round(av_ctrl, 3), AVAIL_DIFF_POINTS=round((av_pos - av_ctrl) * 100, 1), POINT_IN_TIME_VERIFIED_SHARE=(round(verified / used, 3) if used else None),
               MISSING_REASONS_POS=json.dumps(collections.Counter((v[4] or {}).get("MISSING_REASON", "NO_ROW") for v in pos_av.values() if not v[0])),
               MISSING_REASONS_CTRL=json.dumps(collections.Counter((v[4] or {}).get("MISSING_REASON", "NO_ROW") for v in ctrl_av.values() if not v[0])))
    if n_pos_av < 10:
        rec.update(STATUS="NOT_TESTABLE (fewer than 10 positives with a point-in-time value — prereg §O)")
        out_rows.append(rec)
        return rec
    # unadjusted
    a = sum(1 for v in pos_av.values() if v[0] and v[1])
    b = n_pos_av - a
    c = sum(1 for v in ctrl_av.values() if v[0] and v[1])
    d = n_ctrl_av - c
    rec.update(POS_COND=a, POS_RATE=round(a / n_pos_av, 3), POS_WILSON95=wilson(a, n_pos_av), CTRL_COND=c, CTRL_RATE=(round(c / n_ctrl_av, 3) if n_ctrl_av else None),
               CTRL_WILSON95=(wilson(c, n_ctrl_av) if n_ctrl_av else None), FISHER_P=(fisher(a, b, c, d) if n_ctrl_av else None))
    # matched strata
    strata = {}
    for u in units_pos:
        pv = pos_av[u]
        cs = [ctrl_av[cc] for cc in ctrl_by_pos.get(u, []) if ctrl_av[cc][0]]
        if pv[0] and cs:
            strata[u] = (int(pv[1]) - sum(int(x[1]) for x in cs) / len(cs), (pv[2], [x[2] for x in cs]))
    rec["N_MATCHED_STRATA"] = len(strata)
    if len(strata) >= 10:
        diffs = {u: s[0] for u, s in strata.items()}
        est = sum(diffs.values()) / len(diffs)
        ci = boot_ci(diffs, lambda xs: sum(xs) / len(xs))
        rec.update(MATCHED_DIFF=round(est, 4), MATCHED_CI_98_75=ci, MATCHED_CI_EXCLUDES_0=int(ci[0] is not None and (ci[0] > 0 or ci[1] < 0)))
        # continuous
        cont = {u: (s[1][0] - sorted(s[1][1])[len(s[1][1]) // 2]) for u, s in strata.items() if s[1][0] is not None and all(x is not None for x in s[1][1])}
        if len(cont) >= 10:
            ce = sorted(cont.values())[len(cont) // 2]
            rec.update(CONT_MEDIAN_DIFF=round(ce, 4), CONT_CI_98_75=boot_ci(cont, lambda xs: sorted(xs)[len(xs) // 2]))
        # MH across price buckets
        pb = {}
        for u in strata:
            key = price_bucket_of(rows_by_unit, u)
            s = pb.setdefault(key, [0, 0, 0, 0])
            s[0] += int(pos_av[u][1]); s[1] += 1 - int(pos_av[u][1])
            for cc in ctrl_by_pos.get(u, []):
                if ctrl_av[cc][0]:
                    s[2] += int(ctrl_av[cc][1]); s[3] += 1 - int(ctrl_av[cc][1])
        rec.update(MH_OR_PRICE_BUCKETS=mh_or(list(pb.values())), STRATA_BY_PRICE=json.dumps({k: v for k, v in pb.items()}))
        # necessity: share of positives failing the condition
        rec["NECESSITY_FAIL_SHARE"] = round(b / n_pos_av, 3)
        rec["STATUS"] = "TESTED"
    else:
        rec["STATUS"] = "INSUFFICIENT_MATCHED_STRATA (fewer than 10 — prereg §N)"
    if abs(rec["AVAIL_DIFF_POINTS"]) > 20:
        rec["STATUS"] += " · AVAILABILITY-CONFOUNDED (|availability differential| > 20 points — prereg §I)"
    out_rows.append(rec)
    return rec


_PB = {}


def price_bucket_of(rows_by_unit, unit):
    if unit in _PB:
        return _PB[unit]
    sym, T = unit.split("|")
    c = L.context(sym, T)
    px = float(c["price"]) if c else None
    _PB[unit] = "?" if px is None else ("<1" if px < 1 else ("1-5" if px <= 5 else ">5"))
    return _PB[unit]


def placebo_rows(S, units, shift=-60):
    """§M(iii): الميزاتُ نفسُها عند T − 60 جلسة للأوراق نفسها."""
    out = {}
    for u in units:
        sym, T = u.split("|")
        T2 = L.shift(T, shift)
        if not T2:
            continue
        base = dict(SECURITY_ID=sym, DECISION_EPISODE_ID=u, DECISION_DATE=T2, ROLE="PLACEBO")
        out[u] = INV.feature_rows(S, base, sym, T2)
    return out


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "discovery"
    man, prim, disc, val = sets()
    fz = os.path.join(P.OUT, "discovery_frozen.json")
    if mode == "validation" and not os.path.exists(fz):
        print("⛔ validation requires out/discovery_frozen.json (commit of the frozen discovery results)")
        sys.exit(2)
    sel = {"discovery": disc, "validation": val, "all": prim}[mode]
    pdate = {r["SECURITY_ID"]: r["DECISION_DATE"] for r in man if r["PHASE5_PRIMARY_UNIT"] == "1"}
    cm = P.read_csv(os.path.join(P.HERE, "PHASE5_MATCHED_CONTROL_MANIFEST.csv"))
    ctrl_by_pos = collections.defaultdict(list)
    for r in cm:
        ctrl_by_pos[f"{r['MATCHED_POSITIVE']}|{r['MATCHING_DATE']}"].append(f"{r['CONTROL']}|{r['MATCHING_DATE']}")
    fa = P.read_csv(os.path.join(P.HERE, "PHASE5_FEATURE_AVAILABILITY.csv"))
    rows_by_unit = collections.defaultdict(list)
    for r in fa:
        rows_by_unit[f"{r['SECURITY_ID']}|{r['DECISION_DATE']}"].append(r)
    units_pos = [f"{t}|{pdate[t]}" for t in sel]
    out_rows = []
    res = {}
    for fam in FAMILIES:
        res[fam] = analyse(mode, fam, units_pos, ctrl_by_pos, rows_by_unit, out_rows)
    # sensitivity windows for H4
    for w in SENS_WINDOWS:
        spec = FAMILIES["H4_SPLIT"]
        # reuse analyse with a temporary family
        FAMILIES[f"H4_SPLIT_{w}D"] = dict(feature=spec["feature"], cond=None, cont=None, label=f"reverse split within {w} calendar days (sensitivity)", direction=+1)
        rows_tmp = {u: [dict(r, DAYS_VALUE_TO_DECISION=r["DAYS_VALUE_TO_DECISION"]) for r in rs] for u, rs in rows_by_unit.items()}
        _orig = fam_value
        def fam_value_w(fam, rbu, unit, _w=w):
            r = _orig("H4_SPLIT", rbu, unit)
            if r[0] and r[4] is not None and r[4]["VALUE"] not in ("", "NO_CONFIRMED_PRIOR_REVERSE_SPLIT"):
                return r[0], float(r[4]["DAYS_VALUE_TO_DECISION"]) <= _w, r[2], r[3], r[4]
            return r
        globals()["fam_value"] = fam_value_w
        analyse(mode, f"H4_SPLIT_{w}D", units_pos, ctrl_by_pos, rows_tmp, out_rows, tag="sensitivity")
        globals()["fam_value"] = _orig
        del FAMILIES[f"H4_SPLIT_{w}D"]
    # H5 joint over testable families
    testable = [f for f in ("H1_FLOAT", "H2_OFFERING", "H3_BORROW", "H4_SPLIT") if res[f].get("STATUS", "").startswith("TESTED")]
    if len(testable) >= 2:
        def count_sat(u):
            vals = [fam_value(f, rows_by_unit, u) for f in testable]
            if not all(v[0] for v in vals):
                return None
            return sum(int(v[1]) for v in vals)
        diffs = {}
        for u in units_pos:
            pv = count_sat(u)
            cs = [count_sat(c) for c in ctrl_by_pos.get(u, [])]
            cs = [x for x in cs if x is not None]
            if pv is not None and cs:
                diffs[u] = pv - sum(cs) / len(cs)
        rec = dict(MODE=mode, FAMILY="H5_JOINT", CONDITION=f"count of satisfied conditions among {testable}", N_POSITIVES=len(units_pos), N_MATCHED_STRATA=len(diffs))
        if len(diffs) >= 10:
            rec.update(MATCHED_DIFF=round(sum(diffs.values()) / len(diffs), 4), MATCHED_CI_98_75=boot_ci(diffs, lambda xs: sum(xs) / len(xs)), STATUS="TESTED")
        else:
            rec["STATUS"] = "INSUFFICIENT_MATCHED_STRATA"
        out_rows.append(rec)
    else:
        out_rows.append(dict(MODE=mode, FAMILY="H5_JOINT", CONDITION="joint", STATUS=f"NOT_COMPUTED (testable families: {testable})"))
    # placebo (time shift) for tested families
    S = INV.Sources()
    pl = placebo_rows(S, units_pos + sorted({c for u in units_pos for c in ctrl_by_pos.get(u, [])}))
    rows_pl = collections.defaultdict(list)
    for u, rs in pl.items():
        rows_pl[u] = rs
    for fam in ("H1_FLOAT", "H2_OFFERING", "H3_BORROW", "H4_SPLIT"):
        if res[fam].get("STATUS", "").startswith("TESTED"):
            analyse(mode, fam, units_pos, ctrl_by_pos, rows_pl, out_rows, tag="placebo T-60 sessions")
    P.write_csv(os.path.join(P.OUT, f"results_{mode}.csv"), out_rows)
    for r in out_rows:
        print(json.dumps({k: v for k, v in r.items() if k not in ("MISSING_REASONS_POS", "MISSING_REASONS_CTRL", "STRATA_BY_PRICE")}, ensure_ascii=False, default=str))
    if mode == "discovery":
        import subprocess
        sha = subprocess.run(["git", "rev-parse", "HEAD"], capture_output=True, text=True, cwd=P.REPO).stdout.strip()
        json.dump(dict(commit=sha, rows=len(out_rows), results_sha=hashlib.sha256(open(os.path.join(P.OUT, "results_discovery.csv"), "rb").read()).hexdigest()[:16]), open(fz, "w"))
        print("discovery results written; freeze by committing out/results_discovery.csv and out/discovery_frozen.json before running validation")


if __name__ == "__main__":
    main()
