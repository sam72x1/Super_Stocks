"""SEQ70 — the bot's own states before +70% events (descriptive only; run after the seal).

Reads READY70's bot-list rows (`faisal_engine/ready70/data/obs.csv.gz`: one row per symbol and decision session,
2026-07 → 2026-09, with the list it sat on and the reconstructed READY flag). For every symbol it builds the
sequence of states and asks, for symbol-days whose f10 window holds a +70% event versus the rest:
how long had the symbol been tracked, on which list, and had READY fired. Never decisive (the bot's lists exist only
from 2026-06-20, inside the test window; READY70 already reported the event counts).
Run from the repo root:  python3 faisal_engine/seq70/s70_states.py   → data/states.json
"""
import csv
import gzip
import json
import os
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OBS = os.path.join(ROOT, "faisal_engine", "ready70", "data", "obs.csv.gz")


def q(v, p):
    v = sorted(v)
    return v[int(p * (len(v) - 1))] if v else None


def states():
    with gzip.open(OBS, "rt", encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if r["bars"] == "OK"]
    cal = sorted({r["t"] for r in rows})
    cix = {d: i for i, d in enumerate(cal)}
    by = defaultdict(list)
    for r in rows:
        by[r["sym"]].append(r)
    out_rows = []
    for sym, rs in by.items():
        rs.sort(key=lambda r: r["t"])
        start, prev, ready_seen, lists = None, None, 0, set()
        for r in rs:
            k = cix[r["t"]]
            if prev is None or k - prev > 5:
                start, ready_seen, lists = k, 0, set()
            lists.add(r["src"])
            ready_seen = max(ready_seen, int(r["bot_ready"] == "1"))
            out_rows.append({"sym": sym, "t": r["t"], "age": k - start, "src": r["src"], "lists": "+".join(sorted(lists)),
                             "ready_now": int(r["bot_ready"] == "1"), "ready_seen": ready_seen, "f10": r["f10"]})
            prev = k
    ev = [r for r in out_rows if r["f10"] in ("POS", "NEG")]
    res = {"rows": len(out_rows), "evaluable": len(ev), "sessions": len(cal), "symbols": len(by),
           "window": [cal[0], cal[-1]] if cal else None}
    for lab in ("POS", "NEG"):
        g = [r for r in ev if r["f10"] == lab]
        res[lab] = {"rows": len(g), "tracking_age_q25_med_q75": [q([r["age"] for r in g], p) for p in (.25, .5, .75)],
                    "list_today": dict(Counter(r["src"] for r in g)),
                    "ready_now_share": round(sum(r["ready_now"] for r in g) / len(g), 4) if g else None,
                    "ready_seen_in_run_share": round(sum(r["ready_seen"] for r in g) / len(g), 4) if g else None}
    rate_by_list = {}
    for src in sorted({r["src"] for r in ev}):
        g = [r for r in ev if r["src"] == src]
        rate_by_list[src] = [len(g), round(sum(r["f10"] == "POS" for r in g) / len(g), 4)]
    res["f10_rate_by_list"] = rate_by_list
    age_bins = ((0, 4), (5, 9), (10, 19), (20, 39), (40, 10 ** 6))
    res["f10_rate_by_tracking_age"] = {
        f"{a}-{b if b < 10 ** 6 else '+'}": [len(g), round(sum(r["f10"] == "POS" for r in g) / len(g), 4) if g else None]
        for a, b in age_bins for g in [[r for r in ev if a <= r["age"] <= b]]}
    return res


if __name__ == "__main__":
    res = states()
    json.dump(res, open(os.path.join(HERE, "data", "states.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(res, ensure_ascii=False, indent=1))
