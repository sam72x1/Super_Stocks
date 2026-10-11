"""READYNOW shared definitions — conditions, combinations, windows, burden-matched baselines, matching, bootstrap.

Imported by `rn_dev.py` (development only) and `rn_eval.py` (sealed validation + holdout) so the definitions cannot
drift between the exploration and the evaluation. Every condition reads the row's own fields, which `rn_build.py`
computed from bars at or before the decision session. Sources of each condition: `RN_SPEC.md` §2.
"""
import bisect
import csv
import gzip
import math
import os
from collections import defaultdict

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
SEEDS = ("DLXY", "RETO", "DKI", "SXTC")
ACTIVE = ("HUBC",)
EXCLUDE = frozenset(SEEDS + ACTIVE)
WINDOWS = {"development": ("2025-05-01", "2025-12-31"),
           "validation": ("2026-01-16", "2026-05-15"),
           "holdout": ("2026-06-02", "2026-08-27")}
EVAL = ("POS710", "NEG")
CALIPER = 0.10
MATCH_KEYS = ("p_v1x", "p_range20", "p_dv20")
QUIET = 5                      # a trigger = first flag on a symbol after at least QUIET sessions without one


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def rd(name, folder=DATA):
    with gzip.open(os.path.join(folder, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _lt(x, k):
    v = num(x)
    return v is not None and v < k


def _hold(r, n):
    h = num(r.get("hold_n"))
    return h is not None and h >= n and r.get("held") == "1"


def _between(x, lo, hi):
    v = num(x)
    return v is not None and lo <= v <= hi


# ───────── individual conditions (each with its source in RN_SPEC §2) ─────────
COND = {
    "RSI33": lambda r: _lt(r.get("rsi"), 33),                   # three-condition tool (RSI_OVERSOLD)
    "RSI30": lambda r: _lt(r.get("rsi"), 30),                   # Faisal «rsi اقل من 30» (DRCT)
    "OS_AT_LOW": lambda r: _lt(r.get("rsi_low"), 33),           # IMG_6814 oversold reached at the bottom
    "HOLD2": lambda r: _hold(r, 2),                             # app chip «daily stability» (2 sessions)
    "HOLD3": lambda r: _hold(r, 3),                             # IMG_0151 «hold the bottom 3 sessions»
    "HOLD5": lambda r: _hold(r, 5),                             # three-condition tool (STABILITY_REQ)
    "NEAR15": lambda r: _between(r.get("dist"), -1e9, 15),      # app chip «within 15% of the support»
    "BOUNCE10_40": lambda r: _between(r.get("bounce"), 10, 40),  # app chip «bounce within 10–40%»
    "BELOW3": lambda r: r.get("below3") == "1",                 # app chip / IMG_6814 «bearish averages»
    "EMA_UP": lambda r: r.get("ema_up") == "1",                 # Faisal panel EMA 9/26 (TG_57927)
    "EMA_X5": lambda r: r.get("ema_x5") == "1",                 # the 9/26 cross within 5 sessions (TG_57927)
    "MACD_POS": lambda r: r.get("macd_pos") == "1",             # app chip «MACD positive» (line above signal)
    "NO_BOOM": lambda r: _lt(r.get("boom5"), 50),               # three-condition tool (not exploded in a week)
    "SPLIT120": lambda r: r.get("split120") == "1",             # reverse split within SPLIT_LOOKBACK_DAYS
    "CYCLE3": lambda r: (num(r.get("pc_stage")) or 0) >= 3,     # TG_50584 cycle: returned to test the bottom
}


def _all(*names):
    return lambda r: all(COND[n](r) for n in names)


# ───────── combinations declared before any number was read (RN_SPEC §5) ─────────
COMBO = {
    "APP3": _all("NEAR15", "BOUNCE10_40", "HOLD2"),
    "SEQ_BASE": _all("OS_AT_LOW", "HOLD3", "NEAR15"),
    "SEQ_TURN": lambda r: _all("OS_AT_LOW", "HOLD3", "NEAR15")(r) and (COND["EMA_UP"](r) or COND["MACD_POS"](r)),
    "CYCLE_NEAR": _all("CYCLE3", "NEAR15"),
    "TC_SPLIT": _all("RSI33", "HOLD5", "NO_BOOM", "SPLIT120"),
}
# sequence (Layer C): the same ingredients with and without the order «oversold first, then hold»
SEQ_PAIRS = {"ORDERED": _all("OS_AT_LOW", "HOLD3"), "SIMULTANEOUS": _all("RSI33", "HOLD3")}
# round 2 on development only (post hoc, disclosed in RN_SPEC §5): the conditions with a matched lower bound above 1
# combined with the tool's technical part or with Faisal's RSI text
ROUND2 = {
    "TC_BOUNCE": _all("RSI33", "HOLD5", "NO_BOOM", "BOUNCE10_40"),
    "TC_NEAR": _all("RSI33", "HOLD5", "NO_BOOM", "NEAR15"),
    "TC_APP": _all("RSI33", "HOLD5", "NO_BOOM", "BOUNCE10_40", "NEAR15"),
    "RN_A": _all("RSI30", "BOUNCE10_40"),
}
# the sealed candidate (RN_SPEC §6): RSI below 30 now and the close 10–40% above the 25-session low's bounce band
CANDIDATE = "RN_A"
ABLATION = "RSI30"
# existing rules (comparators, never candidates)
EXISTING = {
    "TC_TECH": _all("RSI33", "HOLD5", "NO_BOOM"),               # the tool's reconstructible technical part
    "LOC": lambda r: r.get("loc") == "1",                       # current READY NOW location rule (READY70)
}
ALL_RULES = dict(COND, **COMBO, **SEQ_PAIRS, **ROUND2, **EXISTING)


def only_beyond_tool(flag):
    """Rows the rule flags and the tool's technical part does not (Layer B «beyond the tool»)."""
    return lambda r: flag(r) and not EXISTING["TC_TECH"](r)


BURDEN_SCORES = {"VOL_k": lambda r: num(r.get("v1x")), "VOLAT_k": lambda r: num(r.get("range20")),
                 "LOWPX_k": lambda r: (-num(r.get("px"))) if num(r.get("px")) is not None else None}


def archetype(r):
    """Mutually exclusive structure at a decision day (declared before reading outcomes)."""
    h, d, rsi = num(r.get("hold_n")), num(r.get("dist")), num(r.get("rsi"))
    if h is None or d is None:
        return "UNKNOWN"
    if h < 3:
        return "FRESH_LOW"
    if d <= 15:
        return "BASE_OVERSOLD" if (rsi is not None and rsi < 33) else "BASE_NOT_OVERSOLD"
    if d <= 40:
        return "LIFTED"
    return "EXTENDED"


def window_rows(rows, w):
    lo, hi = WINDOWS[w]
    return [r for r in rows if lo <= r["t"] <= hi and r["sym"] not in EXCLUDE and r.get("cond_ok") == "1"]


def bucket(px):
    v = num(px)
    return None if v is None else (0 if v < 1 else 1 if v < 3 else 2 if v < 10 else 3)


def annotate(rows):
    """Within-session percentiles (mid-rank) of v1x, range20, dv20 over the session's pivot-days."""
    by = defaultdict(list)
    for r in rows:
        by[r["t"]].append(r)
    for t, rs in by.items():
        for k in ("v1x", "range20", "dv20"):
            vals = sorted(v for v in (num(r.get(k)) for r in rs) if v is not None)
            n = len(vals)
            for r in rs:
                x = num(r.get(k))
                if x is None or not n:
                    r["p_" + k] = None
                    continue
                lo, hi = bisect.bisect_left(vals, x), bisect.bisect_right(vals, x)
                r["p_" + k] = (lo + 0.5 * (hi - lo)) / n
    return by


def burden_match(by, flag, score):
    """Equal burden: on each session, flag as many rows as `flag` does, choosing the highest `score` (ties by symbol;
    rows without a score last)."""
    out = set()
    for t, rs in by.items():
        k = sum(1 for r in rs if flag(r))
        if not k:
            continue
        ranked = sorted(rs, key=lambda r: (0 if score(r) is not None else 1, -(score(r) or 0.0), r["sym"]))
        out.update((r["sym"], t) for r in ranked[:k])
    return out


def match(by, flag, exact=None):
    """Matched controls: unflagged evaluable rows of the same session and traded-price bucket (and the same `exact`
    status if given), each of MATCH_KEYS within CALIPER, nearest by summed distance, without reuse in a session,
    ties by symbol. Returns pairs (flagged, control) and the unmatched count."""
    pairs, unmatched = [], 0
    k0 = MATCH_KEYS[0]
    for t in sorted(by):
        rs = [r for r in by[t] if r["lab"] in EVAL]
        fl = sorted((r for r in rs if flag(r)), key=lambda r: r["sym"])
        pool = sorted((r for r in rs if not flag(r) and all(r.get(k) is not None for k in MATCH_KEYS)),
                      key=lambda r: (r[k0], r["sym"]))
        pv = [r[k0] for r in pool]
        used = set()
        for a in fl:
            if any(a.get(k) is None for k in MATCH_KEYS):
                unmatched += 1
                continue
            bk, ex = bucket(a["px"]), (exact(a) if exact else None)
            lo, hi = bisect.bisect_left(pv, a[k0] - CALIPER - 1e-12), bisect.bisect_right(pv, a[k0] + CALIPER + 1e-12)
            cand = [c for c in pool[lo:hi] if c["sym"] not in used and bucket(c["px"]) == bk
                    and (exact is None or exact(c) == ex) and all(abs(c[k] - a[k]) <= CALIPER for k in MATCH_KEYS)]
            if not cand:
                unmatched += 1
                continue
            c = min(cand, key=lambda c: (sum(abs(c[k] - a[k]) for k in MATCH_KEYS), c["sym"]))
            used.add(c["sym"])
            pairs.append((a, c))
    return pairs, unmatched


def wilson(k, n, z=1.96):
    if not n:
        return None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return [round((c - h) / d, 4), round((c + h) / d, 4)]


def _q(v, p):
    v = sorted(v)
    if not v:
        return None
    k = (len(v) - 1) * p
    lo = int(math.floor(k))
    return v[lo] + (v[min(lo + 1, len(v) - 1)] - v[lo]) * (k - lo)


def _boot(units, reps, seed):
    """Ticker-cluster bootstrap sums: (reps × 4) totals of resampled tickers (numpy, deterministic for a seed)."""
    keys = sorted(units)
    a = np.array([units[k] for k in keys], dtype=float)
    rng = np.random.default_rng(seed)
    out = np.empty((reps, 4))
    for j in range(0, reps, 200):
        m = min(200, reps - j)
        idx = rng.integers(0, len(keys), size=(m, len(keys)))
        out[j:j + m] = a[idx].sum(axis=1)
    return a.sum(axis=0), out


def cluster_ratio(units, reps, seed, alpha):
    """units: {ticker: [n_a, pos_a, n_b, pos_b]} ⇒ (pos_a/n_a)/(pos_b/n_b) with a ticker-cluster percentile CI."""
    if not units:
        return None, None
    tot, b = _boot(units, reps, seed)
    est = (tot[1] / tot[0]) / (tot[3] / tot[2]) if tot[0] and tot[2] and tot[3] else None
    ok = (b[:, 0] > 0) & (b[:, 2] > 0) & (b[:, 3] > 0)
    v = (b[ok, 1] / b[ok, 0]) / (b[ok, 3] / b[ok, 2])
    ci = [round(float(np.quantile(v, alpha / 2)), 3), round(float(np.quantile(v, 1 - alpha / 2)), 3)] if len(v) else None
    return (round(float(est), 3) if est is not None else None), ci


def cluster_diff(units, reps, seed, alpha):
    """units: {ticker: [n_a, pos_a, n_b, pos_b]} ⇒ pos_a/n_a − pos_b/n_b (percentage points) with a cluster CI."""
    if not units:
        return None, None
    tot, b = _boot(units, reps, seed)
    est = 100.0 * (tot[1] / tot[0] - tot[3] / tot[2]) if tot[0] and tot[2] else None
    ok = (b[:, 0] > 0) & (b[:, 2] > 0)
    v = 100.0 * (b[ok, 1] / b[ok, 0] - b[ok, 3] / b[ok, 2])
    ci = [round(float(np.quantile(v, alpha / 2)), 2), round(float(np.quantile(v, 1 - alpha / 2)), 2)] if len(v) else None
    return (round(float(est), 2) if est is not None else None), ci


def triggers(rows_sorted, flag, sess_ix):
    """First flag on a symbol after at least QUIET sessions without a flag (rows sorted by symbol then date)."""
    out, last = [], {}
    for r in rows_sorted:
        if not flag(r):
            continue
        k = sess_ix[r["t"]]
        p = last.get(r["sym"])
        if p is None or k - p > QUIET:
            out.append(r)
        last[r["sym"]] = k
    return out


def evaluate(rows, by, events, sess_ix, flag, reps, seed, alpha, name="", vol_key="v1x"):
    """All per-rule metrics in one place (rows = the window's rows, annotated)."""
    ev_rows = [r for r in rows if r["lab"] in EVAL]
    base_pos = sum(r["lab"] == "POS710" for r in ev_rows)
    fl = [r for r in ev_rows if flag(r)]
    pos = sum(r["lab"] == "POS710" for r in fl)
    neg_all = len(ev_rows) - base_pos
    sessions = sorted(by)
    burden_all = sum(1 for r in rows if flag(r))
    syms_flagged = defaultdict(int)
    for r in rows:
        if flag(r):
            syms_flagged[r["sym"]] += 1
    res = {"rule": name, "flags_all_rows": burden_all, "flags_per_session": round(burden_all / max(len(sessions), 1), 2),
           "flagged_tickers": len(syms_flagged),
           "flagged_sessions_per_ticker_med_q90": [_q(list(syms_flagged.values()), .5), _q(list(syms_flagged.values()), .9)],
           "evaluable_flagged": len(fl), "pos710_flagged": pos,
           "precision": round(pos / len(fl), 4) if fl else None, "precision_ci95": wilson(pos, len(fl)),
           "base_rate": round(base_pos / len(ev_rows), 4) if ev_rows else None,
           "fpr": round((len(fl) - pos) / neg_all, 4) if neg_all else None,
           "groups_ABCD": {"A_pos_flag": pos, "B_pos_noflag": base_pos - pos, "C_neg_flag": len(fl) - pos,
                           "D_neg_noflag": neg_all - (len(fl) - pos)},
           "pos110_precision": round(sum(r["pos110"] == "1" for r in fl) / len(fl), 4) if fl else None}
    # lift vs the window's evaluable base (ticker clusters: flagged vs all evaluable)
    u = defaultdict(lambda: [0, 0, 0, 0])
    for r in ev_rows:
        x = u[r["sym"]]
        x[2] += 1
        x[3] += r["lab"] == "POS710"
        if flag(r):
            x[0] += 1
            x[1] += r["lab"] == "POS710"
    res["lift"], res["lift_ci"] = cluster_ratio(u, reps, seed, alpha)
    # event level: eligible events (≥ 1 POS710 row in [L-10, L-7]) captured when flagged at least once there
    elig = [e for e in events if e["pos_rows"]]
    cap = [e for e in elig if any(flag(r) for r in e["pos_rows"])]
    res["events_eligible"] = len(elig)
    res["events_captured"] = len(cap)
    res["recall"] = round(len(cap) / len(elig), 4) if elig else None
    res["recall_ci95"] = wilson(len(cap), len(elig))
    leads_l, leads_x = [], []
    for e in cap:
        first = min(sess_ix[r["t"]] for r in e["early_rows"] if flag(r))
        leads_l.append(e["L_ix"] - first)
        if e.get("x70_ix") is not None:
            leads_x.append(e["x70_ix"] - first)
    res["lead_to_onset_q25_med_q75"] = [_q(leads_l, p) for p in (.25, .5, .75)]
    res["lead_to_x70_q25_med_q75"] = [_q(leads_x, p) for p in (.25, .5, .75)]
    # triggers (no persistence double counting)
    tr = triggers(sorted(rows, key=lambda r: (r["sym"], r["t"])), flag, sess_ix)
    tre = [r for r in tr if r["lab"] in EVAL]
    tp = sum(r["lab"] == "POS710" for r in tre)
    res["triggers"] = len(tr)
    res["triggers_per_session"] = round(len(tr) / max(len(sessions), 1), 2)
    res["trigger_precision"] = round(tp / len(tre), 4) if tre else None
    res["trigger_precision_ci95"] = wilson(tp, len(tre))
    # equal-burden rankings: the same number of flags per session chosen by volume, volatility or lowest price
    for bn, score in BURDEN_SCORES.items():
        vb = burden_match(by, flag, score)
        vfl = [r for r in ev_rows if (r["sym"], r["t"]) in vb]
        vpos = sum(r["lab"] == "POS710" for r in vfl)
        vcap = [e for e in elig if any((r["sym"], r["t"]) in vb for r in e["pos_rows"])]
        dv = defaultdict(lambda: [0, 0, 0, 0])
        for r in ev_rows:
            x = dv[r["sym"]]
            if flag(r):
                x[0] += 1
                x[1] += r["lab"] == "POS710"
            if (r["sym"], r["t"]) in vb:
                x[2] += 1
                x[3] += r["lab"] == "POS710"
        d, dci = cluster_diff(dv, reps, seed, alpha)
        res[bn] = {"precision": round(vpos / len(vfl), 4) if vfl else None,
                   "recall": round(len(vcap) / len(elig), 4) if elig else None,
                   "events_captured": len(vcap), "rule_minus_pp": d, "rule_minus_pp_ci": dci}
    return res


def matched(by, flag, reps, seed, alpha, exact=None):
    pairs, un = match(by, flag, exact)
    u = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        x = u[a["sym"]]
        x[0] += 1
        x[1] += a["lab"] == "POS710"
        x[2] += 1
        x[3] += c["lab"] == "POS710"
    est, ci = cluster_ratio(u, reps, seed, alpha)
    fa = sum(a["lab"] == "POS710" for a, _c in pairs)
    fc = sum(c["lab"] == "POS710" for _a, c in pairs)
    bal = {k: [round(sum(a[k] for a, _c in pairs) / len(pairs), 3), round(sum(c[k] for _a, c in pairs) / len(pairs), 3)]
           for k in MATCH_KEYS} if pairs else {}
    return {"pairs": len(pairs), "unmatched": un, "flag_rate": round(fa / len(pairs), 4) if pairs else None,
            "ctrl_rate": round(fc / len(pairs), 4) if pairs else None, "ratio": est, "ci": ci, "balance": bal}


def events_index(rows, events, sess, w):
    """Eligible events of window w: clean, not excluded, whose early window [L-10, L-7] lies inside the window's
    decision dates; with their evaluable POS710 rows and all their flaggable rows in [L-20, L-1] for lead times."""
    lo, hi = WINDOWS[w]
    ix = {d: k for k, d in enumerate(sess)}
    by_sym = defaultdict(list)
    for r in rows:
        by_sym[r["sym"]].append(r)
    out = []
    for e in events:
        if e["quality"] != "OK" or e["sym"] in EXCLUDE or e["launch"] not in ix:
            continue
        L = ix[e["launch"]]
        if L - 10 < 0 or not (lo <= sess[L - 10] and sess[L - 7] <= hi):
            continue
        rs = by_sym.get(e["sym"], [])
        early = [r for r in rs if L - 20 <= ix[r["t"]] <= L - 1]
        posr = [r for r in rs if L - 10 <= ix[r["t"]] <= L - 7 and r["lab"] == "POS710"
                and r["ep"] == f'{e["sym"]}|{e["launch"]}']
        out.append({"sym": e["sym"], "launch": e["launch"], "L_ix": L,
                    "x70_ix": ix.get(e["x70"]) if e.get("x70") else None, "early_rows": early, "pos_rows": posr,
                    "in_window_pivot_rows": sum(1 for r in rs if L - 10 <= ix[r["t"]] <= L - 7)})
    return out
