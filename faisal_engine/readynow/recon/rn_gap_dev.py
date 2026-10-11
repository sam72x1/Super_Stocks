"""GAPS — development-only look (2025-05-01 → 2025-12-31) at Faisal's untested pivot condition «فجواته عالية»
(IMG_6814 · F4 of audit/RN_AUDIT.md §1), read through the bot's own `unfilled_gaps_above` (M9's detector: a full
down-gap of at least GAP_MIN_PCT whose bottom is above the close and never refilled, within GAP_ABOVE_LOOKBACK_D=120
sessions, bars ≤ t). Three readings fixed before any number: GAP_ANY (at least one such gap) · GAP_FAR70 (the nearest
gap bottom at least 70% above the close — the gap lies beyond the +70% level) · GAP_BIG (the largest gap at least 30%).
Same target, rows and matched controls as rn_room_dev.py. Descriptive discovery; no other window is read.
Run from the repo root:  python3 faisal_engine/readynow/recon/rn_gap_dev.py   → recon/data/gap_dev.json
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rn_room_dev as RM                                                   # noqa: E402

K, B, R, RC, pd = RM.K, RM.B, RM.R, RM.RC, RM.pd
DEV = RM.DEV
READINGS = {"GAP_ANY": lambda r: r["g_n"] > 0,
            "GAP_FAR70": lambda r: r["g_near"] is not None and r["g_near"] >= 70,
            "GAP_BIG": lambda r: r["g_big"] is not None and r["g_big"] >= 30}


def gaps(S, b, i):
    look = int(S.CONFIG["GAP_ABOVE_LOOKBACK_D"])
    lo = max(0, i + 1 - look - 1)
    df = pd.DataFrame({"High": b["h"][lo:i + 1], "Low": b["l"][lo:i + 1], "Close": b["c"][lo:i + 1]})
    g = S.unfilled_gaps_above(df, look) or {}
    z = g.get("zones") or []
    return len(z), g.get("nearest_dist_pct"), (max(x["size_pct"] for x in z) if z else None)


def main():
    meta, bars = R.load_bars()
    S = R.S()
    eps_by = defaultdict(list)
    for e in RC.rd(os.path.join(B.S70_DATA, "events.csv.gz")):
        eps_by[e["sym"]].append(e)
    rows = [r for r in K.rd("rows.csv.gz") if DEV[0] <= r["t"] <= DEV[1] and r["sym"] not in K.EXCLUDE
            and r["cond_ok"] == "1"]
    assert all(r["t"] <= DEV[1] for r in rows)
    cache, out = {}, []
    for r in sorted(rows, key=lambda r: (r["sym"], r["t"])):
        sym = r["sym"]
        if sym not in cache:
            cache.clear()
            cache[sym] = (bars[sym], B.episodes(bars[sym], eps_by.get(sym, [])))
        b, eps = cache[sym]
        i = b["ix"][r["t"]]
        lab, ep, started = RC.label_d1(eps, i, len(b["c"]) - 1)
        n, near, big = gaps(S, b, i)
        out.append({"sym": sym, "t": r["t"], "px": r["px"], "labd": lab, "started": started, "dist": K.num(r["dist"]),
                    "range20": K.num(r["range20"]), "v1x": K.num(r["v1x"]), "g_n": n, "g_near": near, "g_big": big})
    by = defaultdict(list)
    for r in out:
        by[r["t"]].append(r)
    for k in ("dist", "range20", "v1x"):
        RM.pctl(by, k)
    ev = [r for r in out if r["labd"] in K.EVAL]
    base = sum(r["labd"] == "POS710" for r in ev) / len(ev)
    res = {"window": DEV, "lookback": int(S.CONFIG["GAP_ABOVE_LOOKBACK_D"]), "gap_min_pct": S.CONFIG["GAP_MIN_PCT"],
           "evaluable": len(ev), "base_rate_D1": round(base, 4),
           "gap_count_distribution": dict(sorted(Counter(min(r["g_n"], 5) for r in ev).items())),
           "nearest_q25_q50_q75": [round(K._q([r["g_near"] for r in ev if r["g_near"] is not None], p), 1)
                                   for p in (.25, .5, .75)]}
    for name, f in READINGS.items():
        fl = [r for r in ev if f(r)]
        p = sum(r["labd"] == "POS710" for r in fl)
        res[name] = {"share_flagged": round(len(fl) / len(ev), 4), "rate": round(p / len(fl), 4) if fl else None,
                     "lift": round(p / len(fl) / base, 3) if fl else None, "matched": RM.matched(by, f)}
    json.dump(res, open(os.path.join(HERE, "data", "gap_dev.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
