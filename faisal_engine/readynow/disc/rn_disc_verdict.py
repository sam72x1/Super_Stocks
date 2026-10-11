"""READY NOW discovery — applies the sealed decision rules of DISC_PROTOCOL.md §③ and the predictions of §④ to the
stored 2026 results (`data/cand_final.json`, `data/model_final.json`). Reads only; no number is recomputed here.
Run from the repo root:  python3 faisal_engine/readynow/disc/rn_disc_verdict.py   → disc/data/verdict.json
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
W = ("validation", "holdout")
BURSTS = ("BURST_UP", "BURST_UP_3", "BURST_ANY_3", "PATH2")


def _lo(ci):
    return ci[0] if ci else None


def _gt(x, t):
    return x is not None and x > t


def burst(c, name):
    out = {}
    for w in W:
        r = c[w]["rules"][name]
        bu = r["beyond_REF_UNION"]
        out[w] = {"lift_lo": _lo(r["lift_ci"]), "matched_lo": _lo(r["matched"]["ci"]),
                  "extra_lo": _lo(bu["extra_precision_ci95"]), "free_base": bu["free_base"]}
        out[w]["ok"] = (_gt(out[w]["lift_lo"], 1) and _gt(out[w]["matched_lo"], 1)
                        and _gt(out[w]["extra_lo"], bu["free_base"]))
    out["verdict"] = "ADDS" if all(out[w]["ok"] for w in W) else "BURST_NOT_SUPPORTED"
    return out


def capit(c):
    a1 = all(_gt(_lo(c[w]["rules"]["CAPIT_TC"]["lift_ci"]), 1) for w in W)
    pooled = c["capit_pooled"]
    a2 = (_gt(_lo(pooled["TC_TECH"]["ci95"]), 0)
          and all(_gt(c[w]["capit_paired"]["TC_TECH"]["capit_minus_ctrl_pp"], 0) for w in W))
    a3 = _gt(_lo(pooled["DROP_k"]["ci95"]), 0) and _gt(_lo(pooled["VOLAT_k"]["ci95"]), 0)
    v = ("IMPROVES_ON_TOOL_BEYOND_GENERIC" if a1 and a2 and a3 else
         "IMPROVES_ON_TOOL_EQUAL_TO_GENERIC" if a1 and a2 else "NO_DEMONSTRATED_IMPROVEMENT")
    return {"A1": a1, "A2": a2, "A3": a3, "pooled": pooled, "verdict": v}


def two_paths(c):
    r = {w: c[w]["rules"]["TC_OR_CAPIT"] for w in W}
    sup = all(_gt(_lo(r[w]["lift_ci"]), 1) and _gt(_lo(r[w]["matched"]["ci"]), 1) for w in W)
    gen = all(_gt(r[w][b]["rule_minus_pp"], 0) for w in W for b in ("VOLAT_k", "DROP_k", "LOWRSI_k"))
    return {"supported": sup, "beats_generic": gen,
            "verdict": ("TWO_PATHS_SUPPORTED" + (" · BEATS_GENERIC" if gen else "")) if sup else "TWO_PATHS_NOT_SUPPORTED"}


def ceiling(m):
    ok = any(all(_gt(_lo(m[w]["all"][k]["minus_base_ci"]), 0) for w in W) for k in ("M_MAIN", "M_INT"))
    return {"verdict": "DAILY_FEATURES_BEYOND_VOLATILITY" if ok else "NO_INFORMATION_BEYOND_VOLATILITY",
            **{f"{k}_{w}": [m[w]["all"][k]["minus_base"], m[w]["all"][k]["minus_base_ci"]] for k in ("M_MAIN", "M_INT")
               for w in W}}


def main():
    c = json.load(open(os.path.join(DATA, "cand_final.json"), encoding="utf-8"))
    m = json.load(open(os.path.join(DATA, "model_final.json"), encoding="utf-8"))
    out = {"bursts": {n: burst(c, n) for n in BURSTS}, "CAPIT_TC": capit(c), "TC_OR_CAPIT": two_paths(c),
           "ceiling": ceiling(m)}
    ev = {w: (c[w]["rules"]["TC_OR_CAPIT"]["events_captured"], c[w]["rules"]["TC_TECH"]["events_captured"]) for w in W}
    out["predictions"] = {
        "Q1 every burst candidate BURST_NOT_SUPPORTED": all(v["verdict"] == "BURST_NOT_SUPPORTED"
                                                          for v in out["bursts"].values()),
        "Q2 CAPIT_TC passes A1": out["CAPIT_TC"]["A1"],
        "Q3 CAPIT_TC fails A2": not out["CAPIT_TC"]["A2"],
        "Q4 CAPIT_TC fails A3 against DROP_k": not _gt(_lo(c["capit_pooled"]["DROP_k"]["ci95"]), 0),
        "Q5 ceiling NO_INFORMATION_BEYOND_VOLATILITY": out["ceiling"]["verdict"] == "NO_INFORMATION_BEYOND_VOLATILITY",
        "Q6 TC_OR_CAPIT events >= 1.5 x TC_TECH in each window": all(a >= 1.5 * b for a, b in ev.values())}
    json.dump(out, open(os.path.join(DATA, "verdict.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    r = main()
    for n, v in r["bursts"].items():
        print(n, v["verdict"])
    print("CAPIT_TC", r["CAPIT_TC"]["verdict"], {k: r["CAPIT_TC"][k] for k in ("A1", "A2", "A3")})
    print("TC_OR_CAPIT", r["TC_OR_CAPIT"]["verdict"])
    print("ceiling", r["ceiling"]["verdict"])
    for k, v in r["predictions"].items():
        print(("✓ " if v else "✗ ") + k)
