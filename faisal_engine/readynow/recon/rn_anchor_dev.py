"""ANCHOR — development-only diagnostic (2025-05-01 → 2025-12-31): does the choice of target anchor change what looks
predictive? For rules already evaluated (none is re-tested or carried forward) the raw rate of a clean onset 7–10
sessions later under READYNOW's anchor L (trough + 1, retrospective) and under the detection anchor D1 (the detector's
first firing, observable that day), on the same rows. Also the composition of D1 positives: already inside their run
at t (L ≤ t) or not. Descriptive; no other window is read.
Run from the repo root:  python3 faisal_engine/readynow/recon/rn_anchor_dev.py   → recon/data/anchor_dev.json
"""
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
sys.path.insert(0, HERE)
os.environ["FAISAL_ONLY"] = "1"
import rn_build as B                                                      # noqa: E402
import rn_lib as K                                                        # noqa: E402
import rn_recon as RC                                                     # noqa: E402

RULES = {"RSI30": K.ALL_RULES["RSI30"], "RSI33": K.ALL_RULES["RSI33"], "TC_TECH": K.EXISTING["TC_TECH"],
         "RN_A": K.ALL_RULES["RN_A"], "APP_POS": lambda r: K.COND["NEAR15"](r) and K.COND["BOUNCE10_40"](r),
         "NEAR15": K.COND["NEAR15"], "BOUNCE10_40": K.COND["BOUNCE10_40"]}
DEV = K.WINDOWS["development"]


def main():
    meta, bars = B.R.load_bars()
    eps_by = defaultdict(list)
    for e in RC.rd(os.path.join(B.S70_DATA, "events.csv.gz")):
        eps_by[e["sym"]].append(e)
    rows = [r for r in K.rd("rows.csv.gz") if DEV[0] <= r["t"] <= DEV[1] and r["sym"] not in K.EXCLUDE
            and r["cond_ok"] == "1"]
    assert all(r["t"] <= DEV[1] for r in rows)           # development only
    cache = {}
    for r in rows:
        s = r["sym"]
        if s not in cache:
            cache.clear()
            cache[s] = (bars[s], B.episodes(bars[s], eps_by.get(s, [])))
        b, eps = cache[s]
        i = b["ix"][r["t"]]
        r["labd"], _e, r["started"] = RC.label_d1(eps, i, len(b["c"]) - 1)
    res = {"window": DEV, "rows": len(rows)}
    for lab in ("lab", "labd"):
        ev = [r for r in rows if r[lab] in K.EVAL]
        base = sum(r[lab] == "POS710" for r in ev) / len(ev)
        res[lab] = {"evaluable": len(ev), "base": round(base, 4), "rules": {}}
        for n, f in RULES.items():
            fl = [r for r in ev if f(r)]
            p = sum(r[lab] == "POS710" for r in fl)
            res[lab]["rules"][n] = {"flagged": len(fl), "rate": round(p / len(fl), 4) if fl else None,
                                    "raw_lift": round(p / len(fl) / base, 3) if fl else None}
    pos = [r for r in rows if r["labd"] == "POS710"]
    res["D1_positives_inside_run_at_t"] = round(sum(r["started"] for r in pos) / len(pos), 4)
    both = [r for r in rows if r["lab"] in K.EVAL and r["labd"] in K.EVAL]
    res["agreement_on_rows_evaluable_under_both"] = {
        "rows": len(both), "pos_L_and_D1": sum(r["lab"] == "POS710" and r["labd"] == "POS710" for r in both),
        "pos_L_only": sum(r["lab"] == "POS710" and r["labd"] != "POS710" for r in both),
        "pos_D1_only": sum(r["lab"] != "POS710" and r["labd"] == "POS710" for r in both),
        "D1_pos_rows_IN_EVENT_under_L": sum(1 for r in rows if r["labd"] == "POS710" and r["lab"] == "IN_EVENT")}
    json.dump(res, open(os.path.join(HERE, "data", "anchor_dev.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    return res


if __name__ == "__main__":
    print(json.dumps(main(), ensure_ascii=False, indent=1))
