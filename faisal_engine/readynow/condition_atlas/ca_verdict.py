"""Faisal condition atlas — applies the sealed decision rules of CA_PROTOCOL.md §④ to `data/final.json`.
Reads only; no number is recomputed. Writes data/verdict.json.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_verdict.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
W = ("validation", "holdout")
ORDER = ("READY_1", "READY_2", "READY_3", "WATCH", "NOT_READY")


def _lo(x):
    return x["ci95"][0] if x and x.get("ci95") else None


def _pos(x):
    return x is not None and x > 0


def verdict(f=None):
    f = f or json.load(open(os.path.join(DATA, "final.json"), encoding="utf-8"))
    P = f["pooled"]

    def beats(name, ref):
        each = all(_pos(f[w]["compare"][name]["minus_" + ref]["pp"]) for w in W)
        return _pos(_lo(P[name][ref])) and each

    v1 = beats("W_k", "TC_TECH")
    v2 = _pos(_lo(P["W_k"]["DROP_k"])) and _pos(_lo(P["W_k"]["VOLAT_k"]))
    v3 = _pos(_lo(P["W_k"]["CAPIT_TC"]))
    v4 = _pos(_lo(P["W_k"]["COUNT_k"]))
    mono = {}
    for w in W:
        c = f[w]["classes"]
        prec = [c[k]["precision"] for k in ORDER]
        mono[w] = all(a is not None and b is not None and a >= b for a, b in zip(prec, prec[1:]))
    r1 = all((f[w]["compare"]["W_k"]["lift_ci"] or [0])[0] > 1 for w in W)
    v5 = all(mono.values()) and r1
    main = ("IMPROVES_BEYOND_GENERIC" if v1 and v2 and v3 else
            "IMPROVES_ON_TOOL_EQUAL_TO_GENERIC" if v1 else "NO_DEMONSTRATED_IMPROVEMENT")
    return {"V1_beats_tool": v1, "V2_beats_drop_and_volatility": v2, "V3_beats_CAPIT_TC": v3,
            "V4_weights_beat_count": v4, "V5_graded_classes": v5, "monotone_by_window": mono,
            "ready1_lift_lower_above_1_both": r1, "verdict": main,
            "classification": "GRADED" if v5 else "NOT_GRADED",
            "count_vs_tool": {w: f[w]["compare"]["COUNT_k"]["minus_TC_TECH"] for w in W},
            "app_vs_tool": {w: f[w]["compare"]["APPW_k"]["minus_TC_TECH"] for w in W}}


if __name__ == "__main__":
    v = verdict()
    json.dump(v, open(os.path.join(DATA, "verdict.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps(v, ensure_ascii=False, indent=1))
