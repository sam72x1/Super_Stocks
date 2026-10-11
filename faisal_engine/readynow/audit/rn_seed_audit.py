"""READYNOW audit — seed timelines and the onset definition (descriptive; no statistic is tested).

For DLXY, RETO, SXTC (every clean episode since 2026-05-01) and HUBC (history + current state), and DKI (no episode):
the detector dates (L = trough + 1, L10, IGN = largest one-day close gain in [L, D1], x70, D1, peak), the T−10 … T−7
sessions under the primary onset L and under IGN, pivot membership, the label READYNOW gave each day, and the
source conditions computed point in time (bars ≤ t). Also, for every condition, the first session within 30 sessions
before IGN where it held (how early, if at all, it became visible). Plus, over all clean episodes, how far the primary
onset L sits from IGN and from the +70% close (the onset-alignment check).
Run from the repo root:  python3 faisal_engine/readynow/audit/rn_seed_audit.py   → audit/data/seed_audit.json
"""
import json
import os
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
import rn_lib as K                                                        # noqa: E402

RULES = ("RSI30", "RSI33", "NEAR15", "BOUNCE10_40", "HOLD5", "RN_A", "TC_TECH", "APP_POS")
APP_POS = lambda r: K.COND["NEAR15"](r) and K.COND["BOUNCE10_40"](r)     # noqa: E731


def rule(n):
    if n == "APP_POS":
        return APP_POS
    return K.ALL_RULES[n]


def q(v, p):
    v = sorted(v)
    return v[int(p * (len(v) - 1))] if v else None


def main():
    cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    ix = {d: k for k, d in enumerate(cal)}
    seeds = K.rd("seeds.csv.gz")
    ev = K.rd("events.csv.gz")
    by = {}
    for r in seeds:
        if r.get("t"):
            by.setdefault(r["sym"], {})[r["t"]] = r
    out = {"episodes": [], "dki": {}, "hubc_now": {}, "onset_alignment": {}}
    for e in ev:
        if e["sym"] not in ("DLXY", "RETO", "SXTC", "HUBC") or e["launch"] < "2026-05-01":
            continue
        rec = {k: e[k] for k in ("sym", "launch", "l10", "ign", "x70", "d1", "peak", "kind", "gain_d1", "peak_gain",
                                 "quality", "l_to_ign", "l_to_d1", "l_to_x70")}
        for onset_name, onset in (("L", e["launch"]), ("IGN", e["ign"])):
            k0 = ix[onset]
            days = []
            for off in range(-10, -6):
                d = cal[k0 + off]
                r = by[e["sym"]].get(d, {})
                days.append({"off": off, "t": d, "pivot": r.get("pivot"), "label_under_L": r.get("lab"),
                             "rsi": r.get("rsi"), "dist": r.get("dist"), "bounce": r.get("bounce"),
                             "hold_n": r.get("hold_n"), "held": {n: int(bool(r) and rule(n)(r)) for n in RULES}})
            rec["window_" + onset_name] = days
        first = {}
        k_ign = ix[e["ign"]]
        for n in RULES:
            hit = [k for k in range(k_ign - 30, k_ign) if rule(n)(by[e["sym"]].get(cal[k], {}) or {"rsi": None})]
            first[n] = {"first_session": cal[hit[0]] if hit else None, "lead_to_IGN": (k_ign - hit[0]) if hit else None,
                        "sessions_held_in_30": len(hit)}
        rec["first_visible_before_IGN"] = first
        out["episodes"].append(rec)
    dk = by["DKI"]
    out["dki"] = {"episodes_since_2026_05": [e["launch"] for e in ev if e["sym"] == "DKI" and e["launch"] >= "2026-05-01"],
                  "2026-10-06": {k: dk["2026-10-06"].get(k) for k in ("close", "rsi", "dist", "bounce")},
                  "2026-10-07": {k: dk["2026-10-07"].get(k) for k in ("close", "rsi", "dist", "bounce", "vol")},
                  "2026-10-08": {k: dk["2026-10-08"].get(k) for k in ("close", "rsi")},
                  "note": "close-to-close 2026-10-07 = 1.67 / 1.36 − 1 = +22.8% (below the 50% jump); the intraday high "
                          "is not a daily-close event; 10-07 is also after the last label-known decision 2026-08-27"}
    hb = sorted(by["HUBC"])
    out["hubc_now"] = {d: {k: by["HUBC"][d].get(k) for k in ("pivot", "close", "rsi", "low25", "hold_n", "dist", "bounce",
                                                              "boom5", "split120")}
                       | {n: int(rule(n)(by["HUBC"][d])) for n in RULES} for d in hb[-6:]}
    ok = [e for e in ev if e["quality"] == "OK"]
    l2i = [int(e["l_to_ign"]) for e in ok]
    l2x = [int(e["l_to_x70"]) for e in ok if e["l_to_x70"] != ""]
    out["onset_alignment"] = {
        "clean_episodes": len(ok), "kind": dict(Counter(e["kind"] for e in ok)),
        "L_to_IGN_q25_med_q75_max": [q(l2i, .25), q(l2i, .5), q(l2i, .75), max(l2i)],
        "share_IGN_on_L": round(sum(x == 0 for x in l2i) / len(l2i), 4),
        "share_IGN_7plus_after_L": round(sum(x >= 7 for x in l2i) / len(l2i), 4),
        "share_IGN_7plus_after_L_by_kind": {k: round(sum(1 for e in ok if e["kind"] == k and int(e["l_to_ign"]) >= 7)
                                                     / max(1, sum(1 for e in ok if e["kind"] == k)), 4)
                                            for k in ("jump", "run")},
        "reached_x70": len(l2x), "share_x70_on_L": round(sum(x == 0 for x in l2x) / len(l2x), 4),
        "L_to_x70_q25_med_q75": [q(l2x, .25), q(l2x, .5), q(l2x, .75)]}
    os.makedirs(os.path.join(HERE, "data"), exist_ok=True)
    json.dump(out, open(os.path.join(HERE, "data", "seed_audit.json"), "w", encoding="utf-8"), ensure_ascii=False,
              indent=1)
    return out


if __name__ == "__main__":
    r = main()
    for e in r["episodes"]:
        print(f'\n{e["sym"]} L {e["launch"]} L10 {e["l10"]} IGN {e["ign"]} x70 {e["x70"] or "-"} D1 {e["d1"]} {e["kind"]} '
              f'peak {e["peak_gain"]}% · L→IGN {e["l_to_ign"]}')
        for w in ("window_L", "window_IGN"):
            print(" ", w, [(d["t"], d["pivot"], d["label_under_L"], d["rsi"], d["dist"], d["bounce"],
                            "".join(n[0] if v else "." for n, v in d["held"].items())) for d in e[w]])
        print("  first visible ≤30 before IGN:", {n: (v["first_session"], v["lead_to_IGN"], v["sessions_held_in_30"])
                                                  for n, v in e["first_visible_before_IGN"].items()})
    print("\nDKI", json.dumps(r["dki"], ensure_ascii=False))
    print("HUBC", json.dumps(r["hubc_now"], ensure_ascii=False)[:1500])
    print("onset", json.dumps(r["onset_alignment"]))
