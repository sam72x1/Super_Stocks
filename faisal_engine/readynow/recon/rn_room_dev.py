"""ROOM — development-only look (2025-05-01 → 2025-12-31) at one untested structure: the room between the close and
the nearest overhead daily resistance of the bot's own resistance map (descriptive discovery; no other window is read).

Resistance map at session i (bars ≤ i only, the last LOOK sessions): the bot's `_swing_highs` (windows 3 and 6) and
`_red_candle_heads` on the daily frame and `_swing_highs` (window 2) on the weekly frame (`resample_ohlc`), rounded and
clustered within 3% exactly as `resistance_levels` does before psychological fillers; ROOM = the first cluster above
the close ÷ close − 1 (open = no real level above inside the window).
Target: the detection-anchored label of `rn_recon.label_d1` (a clean episode first detected 7–10 sessions later).
Matched controls hold the early-move state constant: same session and price bucket, within-session percentiles of the
distance above the 25-session low, range20 and v1x within 0.10.
Run from the repo root:  python3 faisal_engine/readynow/recon/rn_room_dev.py   → recon/data/room_dev.json
"""
import bisect
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
sys.path.insert(0, HERE)
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import pandas as pd                                                       # noqa: E402
import rn_build as B                                                      # noqa: E402
import rn_lib as K                                                        # noqa: E402
import rn_recon as RC                                                     # noqa: E402

R = B.R
DEV = K.WINDOWS["development"]
LOOK = 250
BINS = ((None, 10), (10, 30), (30, 70), (70, None))      # ROOM %; open (no level) joins the last bin
DIST_STRATA = ((None, 10), (10, 40), (40, None))
KEYS = ("p_dist", "p_range20", "p_v1x")
REPS, SEED = 2000, 20261011


def room(S, b, i, look=LOOK):
    lo = max(0, i + 1 - look)
    df = pd.DataFrame({"Open": b["o"][lo:i + 1], "High": b["h"][lo:i + 1], "Low": b["l"][lo:i + 1],
                       "Close": b["c"][lo:i + 1], "Volume": b["v"][lo:i + 1]},
                      index=pd.to_datetime(b["d"][lo:i + 1]))
    price = float(b["c"][i])
    h = df["High"].values.astype(float)
    real = S._swing_highs(h, price, 3) + S._swing_highs(h, price, 6) + S._red_candle_heads(df, price)
    wk = S.resample_ohlc(df, "W")
    if wk is not None and len(wk) >= 7:
        real += S._swing_highs(wk["High"].values.astype(float), price, 2)
    real = sorted(set(round(s, 2) for s in real if s > price))
    cl = []
    for s in real:
        if cl and s <= cl[-1] * 1.03:
            cl[-1] = max(cl[-1], s)
        else:
            cl.append(s)
    return (cl[0] / price - 1.0) * 100.0 if cl else None


def in_bin(v, lo, hi):
    return (lo is None or v >= lo) and (hi is None or v < hi)


def room_bin(r):
    v = r["room"]
    if v is None:
        return len(BINS) - 1
    return next(k for k, (lo, hi) in enumerate(BINS) if in_bin(v, lo, hi))


def pctl(by, key):
    for t, rs in by.items():
        vals = sorted(r[key] for r in rs if r.get(key) is not None)
        n = len(vals)
        for r in rs:
            x = r.get(key)
            if x is None or not n:
                r["p_" + key] = None
                continue
            lo, hi = bisect.bisect_left(vals, x), bisect.bisect_right(vals, x)
            r["p_" + key] = (lo + 0.5 * (hi - lo)) / n


def match(by, flag):
    pairs, unmatched = [], 0
    for t in sorted(by):
        rs = [r for r in by[t] if r["labd"] in K.EVAL]
        fl = sorted((r for r in rs if flag(r)), key=lambda r: r["sym"])
        pool = [r for r in rs if not flag(r) and all(r.get(k) is not None for k in KEYS)]
        used = set()
        for a in fl:
            if any(a.get(k) is None for k in KEYS):
                unmatched += 1
                continue
            cand = [c for c in pool if c["sym"] not in used and K.bucket(c["px"]) == K.bucket(a["px"])
                    and all(abs(c[k] - a[k]) <= K.CALIPER for k in KEYS)]
            if not cand:
                unmatched += 1
                continue
            c = min(cand, key=lambda c: (sum(abs(c[k] - a[k]) for k in KEYS), c["sym"]))
            used.add(c["sym"])
            pairs.append((a, c))
    return pairs, unmatched


def matched(by, flag):
    pairs, un = match(by, flag)
    u = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        x = u[a["sym"]]
        x[0] += 1
        x[1] += a["labd"] == "POS710"
        x[2] += 1
        x[3] += c["labd"] == "POS710"
    est, ci = K.cluster_ratio(u, REPS, SEED, 0.05)
    fa = sum(a["labd"] == "POS710" for a, _ in pairs)
    fc = sum(c["labd"] == "POS710" for _, c in pairs)
    return {"pairs": len(pairs), "unmatched": un, "flag_rate": round(fa / len(pairs), 4) if pairs else None,
            "ctrl_rate": round(fc / len(pairs), 4) if pairs else None, "ratio": est, "ci95": ci,
            "balance_median_dist": [K._q([a["dist"] for a, _ in pairs], .5), K._q([c["dist"] for _, c in pairs], .5)]}


def main():
    meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    S = R.S()
    eps_by = defaultdict(list)
    for e in RC.rd(os.path.join(B.S70_DATA, "events.csv.gz")):
        eps_by[e["sym"]].append(e)
    rows = [r for r in K.rd("rows.csv.gz") if DEV[0] <= r["t"] <= DEV[1] and r["sym"] not in K.EXCLUDE
            and r["cond_ok"] == "1"]
    assert all(r["t"] <= DEV[1] for r in rows)           # development only
    cache = {}
    out_rows = []
    for r in sorted(rows, key=lambda r: (r["sym"], r["t"])):
        sym = r["sym"]
        if sym not in cache:
            b = bars[sym]
            cache.clear()
            cache[sym] = (b, B.episodes(b, eps_by.get(sym, [])))
        b, eps = cache[sym]
        i = b["ix"][r["t"]]
        lab, ep, started = RC.label_d1(eps, i, len(b["c"]) - 1)
        out_rows.append({"sym": sym, "t": r["t"], "px": r["px"], "labd": lab, "started": started,
                         "dist": K.num(r["dist"]), "range20": K.num(r["range20"]), "v1x": K.num(r["v1x"]),
                         "room": room(S, b, i)})
    by = defaultdict(list)
    for r in out_rows:
        by[r["t"]].append(r)
    for k in ("dist", "range20", "v1x"):
        pctl(by, k)
    ev = [r for r in out_rows if r["labd"] in K.EVAL]
    base = sum(r["labd"] == "POS710" for r in ev) / len(ev)
    pos = [r for r in ev if r["labd"] == "POS710"]
    res = {"window": DEV, "look_sessions": LOOK, "rows": len(out_rows), "evaluable": len(ev),
           "labels": dict(Counter(r["labd"] for r in out_rows)), "base_rate_D1": round(base, 4),
           "positives_inside_their_run_at_t": round(sum(r["started"] for r in pos) / len(pos), 4),
           "room_open_share": round(sum(r["room"] is None for r in ev) / len(ev), 4),
           "room_q10_q25_q50_q75_q90": [round(K._q([r["room"] for r in ev if r["room"] is not None], p), 1)
                                        for p in (.1, .25, .5, .75, .9)]}
    tab = []
    for k, (lo, hi) in enumerate(BINS):
        rr = [r for r in ev if room_bin(r) == k]
        p = sum(r["labd"] == "POS710" for r in rr)
        row = {"room_bin": f"{lo}-{hi}" + (" or open" if k == len(BINS) - 1 else ""), "n": len(rr), "pos": p,
               "rate": round(p / len(rr), 4) if rr else None, "lift": round(p / len(rr) / base, 3) if rr else None}
        for dlo, dhi in DIST_STRATA:
            ss = [r for r in rr if r["dist"] is not None and in_bin(r["dist"], dlo, dhi)]
            sp = sum(r["labd"] == "POS710" for r in ss)
            row[f"dist {dlo}-{dhi}"] = [len(ss), round(sp / len(ss), 4) if ss else None]
        tab.append(row)
    res["by_room_bin"] = tab
    res["by_dist_stratum_base"] = {f"{lo}-{hi}": [len(ss), round(sum(r["labd"] == "POS710" for r in ss) / len(ss), 4)]
                                   for lo, hi in DIST_STRATA
                                   for ss in [[r for r in ev if r["dist"] is not None and in_bin(r["dist"], lo, hi)]]}
    res["matched_ROOM70_vs_lt70"] = matched(by, lambda r: r["room"] is None or r["room"] >= 70)
    res["matched_ROOM30_vs_lt30"] = matched(by, lambda r: r["room"] is None or r["room"] >= 30)
    res["matched_ROOM_lt10_vs_ge10"] = matched(by, lambda r: r["room"] is not None and r["room"] < 10)
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(res, open(os.path.join(HERE, "data", "room_dev.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
