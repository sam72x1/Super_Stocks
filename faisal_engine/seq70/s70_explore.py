"""SEQ70 — descriptive reconstruction on the DISCOVERY window only (2025-05-01 → 2025-12-31).

Reads data/traj.csv.gz and data/events.csv.gz and never uses a pivot-day dated after DISC_TO or an episode that
launches after DISC_TO (guard G2 in test_s70). Writes data/explore.json. It chooses nothing: the hypothesis is
written in S70_PREREG.md from what this prints.

  E1  duration: +70% rate (f10) by age in the pivot spell; spell age of the stock on the session before launch
  E2  event study: within-day percentile of each descriptor (vs every pivot-day of that session) at lags before the
      start of the move (L = trough + 1) and before the +70% crossing (D1); top-quintile share (chance = 0.20)
  E3  order: for events seen as pivots on the 10 sessions before L, the first lag at which volume (v5x) and price
      (r5) reach the top quintile — which comes first — against date-matched control pseudo-starts
  E4  (declared after E1-E3, before computing it) three candidate sequences on the decision day, each against a
      matched control (same session, same price bucket, nearest within-session percentile of r5 and range20,
      not flagged, without replacement), ticker-cluster bootstrap 95%:
        C-A  v1x in the session's top quintile and r5 < 0    (selling pressure met by volume today)
        C-B  v5x in the session's top quintile and r5 < 0    (the same over five sessions)
        C-C  tr5x in the session's top quintile and r5 < 0   (pressure met by range, not volume)
      rule written before the numbers: the hypothesis is the candidate with the highest lower bound if that bound
      is above 1.0; if no lower bound is above 1.0, no hypothesis is carried to the test windows
  E5  (added after E4, still discovery only) E4's matcher left the flagged rows more volatile than their controls
      (median range20 percentile 0.82 vs 0.76 and 0.68). The three candidates are re-run with the matcher of
      s70_eval.py (each matched percentile within CALIPER = 0.10), against both controls: K-V (same drop and
      volatility, no top-quintile signal) and K-P (same signal and volatility, 5-session return not negative).
  Run from the repo root:  python3 faisal_engine/seq70/s70_explore.py
"""
import csv
import gzip
import hashlib
import json
import os
import random
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
DISC_FROM, DISC_TO = "2025-05-01", "2025-12-31"
DESC = ("v1x", "v5x", "tr5x", "r5", "pos60", "bot_age", "nlow20", "clv5")
MECHANICAL_AT_L = ("r5", "pos60", "bot_age", "nlow20")      # L-1 is the trough close by construction
LAGS = (20, 10, 5, 3, 2, 1)
AGE_BINS = ((0, 4), (5, 9), (10, 19), (20, 39), (40, 79), (80, 10 ** 6))


def rd(name):
    with gzip.open(os.path.join(DATA, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def pct_rank_day(rows, key):
    """Within-session mid-rank percentile of `key` among the given rows (one session)."""
    vals = sorted(num(r[key]) for r in rows if num(r[key]) is not None)
    n = len(vals)
    out = {}
    if not n:
        return out
    import bisect
    for r in rows:
        x = num(r[key])
        if x is None:
            continue
        lo = bisect.bisect_left(vals, x)
        hi = bisect.bisect_right(vals, x)
        out[(r["sym"], r["t"])] = (lo + 0.5 * (hi - lo)) / n
    return out


def q(v, p):
    v = sorted(v)
    return v[int(p * (len(v) - 1))] if v else None


def load_discovery():
    traj = [r for r in rd("traj.csv.gz") if DISC_FROM <= r["t"] <= DISC_TO]
    events = [e for e in rd("events.csv.gz") if e["quality"] == "OK" and DISC_FROM <= e["launch"] <= DISC_TO]
    return traj, events


def explore():
    traj, events = load_discovery()
    assert all(r["t"] <= DISC_TO for r in traj) and all(e["launch"] <= DISC_TO for e in events)
    clean = [r for r in traj if r["split60"] == "0" and r["desc_ok"] == "1"]
    by_day = defaultdict(list)
    for r in clean:
        by_day[r["t"]].append(r)
    pct = {k: {} for k in DESC}
    for t, rs in by_day.items():
        for k in DESC:
            pct[k].update(pct_rank_day(rs, k))
    days = sorted(by_day)
    row_at = {(r["sym"], r["t"]): r for r in clean}
    res = {"window": [DISC_FROM, DISC_TO], "pivot_days": len(traj), "clean_pivot_days": len(clean),
           "sessions": len(days), "events_ok_launch_in_window": len(events)}
    # E1 duration
    ev = [r for r in clean if r["f10"] in ("POS", "NEG")]
    e1 = []
    for lo, hi in AGE_BINS:
        g = [r for r in ev if lo <= int(r["spell_age"]) <= hi]
        pos = [r for r in g if r["f10"] == "POS"]
        e1.append({"age": f"{lo}-{hi if hi < 10 ** 6 else '+'}", "rows": len(g), "pos": len(pos),
                   "rate": round(len(pos) / len(g), 4) if g else None, "tickers": len({r["sym"] for r in g})})
    res["E1_rate_by_spell_age"] = e1
    res["E1_base_rate"] = round(sum(r["f10"] == "POS" for r in ev) / len(ev), 4)
    # trading-session index per symbol for lags (sessions of the pivot table are the market calendar here)
    cal = sorted({r["t"] for r in traj})
    cix = {d: i for i, d in enumerate(cal)}

    def lag_day(d, k):
        i = cix.get(d)
        return cal[i - k] if i is not None and i - k >= 0 else None

    # E2 event study
    e2 = {}
    for anchor in ("launch", "d1"):
        tab = {}
        for k in LAGS:
            cells = {}
            for key in DESC:
                vals = []
                for e in events:
                    d = lag_day(e[anchor], k)
                    p = pct[key].get((e["sym"], d)) if d else None
                    if p is not None:
                        vals.append(p)
                cells[key] = {"n": len(vals), "median_pct": round(q(vals, .5), 3) if vals else None,
                              "top_quintile_share": round(sum(v >= 0.8 for v in vals) / len(vals), 3) if vals else None}
            tab[f"-{k}"] = cells
        e2[anchor] = tab
    res["E2_event_study"] = e2
    res["E2_mechanical_near_L"] = list(MECHANICAL_AT_L)
    # E3 order of volume vs price reaching the top quintile, 10 sessions before L, events vs date-matched controls
    neg_by_day = defaultdict(list)
    for r in clean:
        if r["f10"] == "NEG" and r["y10"] == "NEG":
            neg_by_day[r["t"]].append(r)

    def first_top(sym, d0, key):
        for k in range(10, 0, -1):
            d = lag_day(d0, k)
            p = pct[key].get((sym, d)) if d else None
            if p is not None and p >= 0.8:
                return k
        return None

    def order(sym, d0):
        seen = sum(1 for k in range(1, 11) if lag_day(d0, k) and (sym, lag_day(d0, k)) in row_at)
        if seen < 8:
            return None
        kv, kp = first_top(sym, d0, "v5x"), first_top(sym, d0, "r5")
        if kv is None and kp is None:
            return "neither"
        if kp is None:
            return "volume_only"
        if kv is None:
            return "price_only"
        return "volume_first" if kv > kp else ("price_first" if kp > kv else "same_session")

    ev_o, ct_o = Counter(), Counter()
    rnd = random.Random(20261011)
    for e in events:
        o = order(e["sym"], e["launch"])
        if o is None:
            continue
        ev_o[o] += 1
        pool = sorted(r["sym"] for r in neg_by_day.get(e["launch"], []) if r["sym"] != e["sym"])
        for s in rnd.sample(pool, min(5, len(pool))):
            oc = order(s, e["launch"])
            if oc is not None:
                ct_o[oc] += 1
    res["E3_order_events"] = dict(ev_o)
    res["E3_order_controls"] = dict(ct_o)
    res["E3_note"] = ("first lag (10 → 1 before L) at which the descriptor's within-day percentile is ≥ 0.8; controls = up to "
                      "5 pivot-days of the same date with f10 and y10 NEG; r5 near L is mechanically low for events")
    # E4 candidates vs matched controls (discovery only)
    for key in ("range20",):
        pct[key] = {}
        for t, rs in by_day.items():
            pct[key].update(pct_rank_day(rs, key))
    cands = {"C-A": ("v1x", None), "C-B": ("v5x", None), "C-C": ("tr5x", None)}
    e4 = {}
    for name, (vk, _x) in cands.items():
        def flag(r, vk=vk):
            return pct[vk].get((r["sym"], r["t"]), 0) >= 0.8 and num(r["r5"]) is not None and num(r["r5"]) < 0
        e4[name] = matched_ratio(ev, flag, pct, rnd_seed=20261011)
        e4[name]["leads"] = leads(ev, flag)
    res["E4_candidates"] = e4
    best = max(e4, key=lambda k: (e4[k]["lo"] or 0))
    res["E4_choice"] = best if (e4[best]["lo"] or 0) > 1.0 else None
    # E5 balanced re-run with the sealed matcher (discovery only)
    import s70_eval as V
    cl = [dict(r) for r in clean]
    byv = V.annotate(cl)
    evk = {(r["sym"], r["t"]) for r in cl if r["f10"] in ("POS", "NEG")}
    e5 = {}
    for name, sk in (("C-A", "v1x"), ("C-B", "v5x"), ("C-C", "tr5x")):
        cell = {}
        for mode in ("V", "P"):
            pr, un = V.match(byv, evk, mode, sk)
            x = V.cluster_ratio(pr, reps=2000, alpha=0.05)
            x.update(pairs=len(pr), unmatched=un,
                     median_range20_pct=[q([a["p_range20"] for a, _ in pr], .5), q([c["p_range20"] for _, c in pr], .5)])
            cell["K_" + mode] = x
        e5[name] = cell
    res["E5_balanced"] = e5
    return res


def bucket(px):
    px = num(px)
    return None if px is None else (0 if px < 1 else 1 if px < 3 else 2 if px < 10 else 3)


def matched_ratio(ev, flag, pct, rnd_seed, reps=1000):
    by = defaultdict(list)
    for r in ev:
        by[r["t"]].append(r)
    pairs = []
    for t, rs in sorted(by.items()):
        fl = sorted((r for r in rs if flag(r)), key=lambda r: r["sym"])
        pool = [r for r in rs if not flag(r) and (r["sym"], t) in pct["r5"] and (r["sym"], t) in pct["range20"]]
        used = set()
        for a in fl:
            if (a["sym"], t) not in pct["range20"]:
                continue
            bk = bucket(a["px"])
            cand = [c for c in pool if c["sym"] not in used and bucket(c["px"]) == bk]
            if not cand:
                continue
            c = min(cand, key=lambda c: (abs(pct["r5"][(c["sym"], t)] - pct["r5"][(a["sym"], t)]) +
                                         abs(pct["range20"][(c["sym"], t)] - pct["range20"][(a["sym"], t)]), c["sym"]))
            used.add(c["sym"])
            pairs.append((a, c))
    units = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        u = units[a["sym"]]
        u[0] += 1
        u[1] += a["f10"] == "POS"
        u[2] += 1
        u[3] += c["f10"] == "POS"
    keys = sorted(units)
    rnd = random.Random(rnd_seed)

    def ratio(tt):
        return (tt[1] / tt[0]) / (tt[3] / tt[2]) if tt[0] and tt[2] and tt[3] else None
    tot = [sum(units[k][j] for k in keys) for j in range(4)]
    vals = []
    for _ in range(reps):
        tt = [0, 0, 0, 0]
        for _k in keys:
            v = units[keys[rnd.randrange(len(keys))]]
            for j in range(4):
                tt[j] += v[j]
        x = ratio(tt)
        if x is not None:
            vals.append(x)
    vals.sort()
    pt = ratio(tot)
    return {"pairs": len(pairs), "flag_pos": tot[1], "ctrl_pos": tot[3],
            "flag_rate": round(tot[1] / tot[0], 4) if tot[0] else None,
            "ctrl_rate": round(tot[3] / tot[2], 4) if tot[2] else None,
            "point": round(pt, 3) if pt else None, "lo": round(vals[int(.025 * len(vals))], 3) if vals else None,
            "hi": round(vals[int(.975 * len(vals))], 3) if vals else None, "tickers": len(keys)}


def leads(ev, flag):
    """Descriptive: for f10-positive flagged rows, sessions from the decision to the +70% condition (f10_k)."""
    ks = [int(float(r["f10_k"])) for r in ev if flag(r) and r["f10"] == "POS" and r["f10_k"]]
    return {"n": len(ks), "q25_med_q75": [q(ks, .25), q(ks, .5), q(ks, .75)]}


if __name__ == "__main__":
    out = explore()
    json.dump(out, open(os.path.join(DATA, "explore.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1))
    print(hashlib.sha256(open(os.path.join(DATA, "explore.json"), "rb").read()).hexdigest())
