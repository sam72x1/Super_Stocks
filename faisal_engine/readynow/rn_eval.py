"""READYNOW — the sealed evaluation: validation and holdout in one run, then HUBC's current state (descriptive).

Refuses to read any row (exit 9) unless `RN_SPEC.md` matches the pinned SHA-256. Computes C1–C3 of RN_SPEC §7 for the
candidate RN_A in each window and on the pooled windows, every reported metric of §7, and the status.
Run from the repo root:  python3 faisal_engine/readynow/rn_eval.py final   → data/result.json
"""
import hashlib
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rn_lib as K                                                       # noqa: E402

PREREG = os.path.join(HERE, "RN_SPEC.md")
PREREG_SHA256 = "79a3b8db1f15ef4ce0c2c117fbcf4317d7e0a5428246f12490438ecbeb10a1e7"
DATA = K.DATA
REPS = 2000
SEED = 20261011
ALPHA_W = 0.025
ALPHA_P = 0.05
FLOORS = {"eligible_events": 20, "c1_pairs": 300, "c3_pairs": 200}
OOS = ("validation", "holdout")


def prereg_ok():
    try:
        return hashlib.sha256(open(PREREG, "rb").read()).hexdigest() == PREREG_SHA256
    except OSError:
        return False


rd = K.rd


def _units(pairs):
    u = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        x = u[a["sym"]]
        x[0] += 1
        x[1] += a["lab"] == "POS710"
        x[2] += 1
        x[3] += c["lab"] == "POS710"
    return u


def window(w, rows_all, events_all, ewin, cal):
    rows = K.window_rows(rows_all, w)
    by = K.annotate(rows)
    six = {d: k for k, d in enumerate(cal)}
    events = K.events_index(rows, events_all, cal, w)
    cand, tc, r30 = K.ROUND2[K.CANDIDATE], K.EXISTING["TC_TECH"], K.COND[K.ABLATION]
    labs = Counter(r["lab"] for r in rows)
    res = {"window": K.WINDOWS[w], "rows": len(rows), "symbols": len({r["sym"] for r in rows}), "sessions": len(by),
           "labels": dict(sorted(labs.items())), "events_in_window": len(events),
           "eligible_events": sum(1 for e in events if e["pos_rows"]),
           "events_without_pivot_row_in_T10_T7": sum(1 for e in events if not e["in_window_pivot_rows"])}
    res["RN_A"] = K.evaluate(rows, by, events, six, cand, REPS, SEED, ALPHA_W, "RN_A")
    p1, u1 = K.match(by, cand)
    p3, u3 = K.match(by, K.only_beyond_tool(cand), exact=tc)
    res["C1"] = K.matched(by, cand, REPS, SEED, ALPHA_W)
    res["C3"] = K.matched(by, K.only_beyond_tool(cand), REPS, SEED, ALPHA_W, exact=tc)
    res["C2"] = {k: [res["RN_A"][k]["rule_minus_pp"], res["RN_A"][k]["rule_minus_pp_ci"]] for k in ("VOL_k", "VOLAT_k")}
    res["sufficient"] = (res["eligible_events"] >= FLOORS["eligible_events"] and res["C1"]["pairs"] >= FLOORS["c1_pairs"]
                         and res["C3"]["pairs"] >= FLOORS["c3_pairs"])
    ok = lambda ci, thr: bool(ci) and ci[0] > thr                              # noqa: E731
    res["pass"] = {"C1": ok(res["C1"]["ci"], 1.0),
                   "C2": ok(res["C2"]["VOL_k"][1], 0.0) and ok(res["C2"]["VOLAT_k"][1], 0.0),
                   "C3": ok(res["C3"]["ci"], 1.0)}
    # comparators and the ablation under the same metrics (never decisive)
    res["comparators"] = {}
    for n, f in (("TC_TECH", tc), ("LOC", K.EXISTING["LOC"]), ("RSI30", r30)):
        res["comparators"][n] = K.evaluate(rows, by, events, six, f, REPS, SEED, ALPHA_W, n)
        res["comparators"][n]["matched"] = K.matched(by, f, REPS, SEED, ALPHA_W)
    # events: paired with the tool, missed winners by archetype
    el = [e for e in events if e["pos_rows"]]
    ca = {e["sym"] + "|" + e["launch"] for e in el if any(cand(r) for r in e["pos_rows"])}
    ct = {e["sym"] + "|" + e["launch"] for e in el if any(tc(r) for r in e["pos_rows"])}
    res["events_paired"] = {"eligible": len(el), "RN_A": len(ca), "TC_TECH": len(ct), "RN_A_only": len(ca - ct),
                            "TC_only": len(ct - ca), "both": len(ca & ct), "either": len(ca | ct)}
    res["missed_by_RN_A_archetype"] = dict(sorted(Counter(K.archetype(e["pos_rows"][0]) for e in el
                                                          if e["sym"] + "|" + e["launch"] not in ca).items()))
    res["captured_by_RN_A_archetype"] = dict(sorted(Counter(K.archetype(e["pos_rows"][0]) for e in el
                                                            if e["sym"] + "|" + e["launch"] in ca).items()))
    ev_rows = [r for r in rows if r["lab"] in K.EVAL]
    mix = Counter(K.archetype(r) for r in ev_rows)
    pos_mix = Counter(K.archetype(r) for r in ev_rows if r["lab"] == "POS710")
    res["archetype_rates"] = {a: [mix[a], pos_mix.get(a, 0), round(pos_mix.get(a, 0) / mix[a], 4)] for a in sorted(mix)}
    # sensitivity labels (strict +70%, onset L10, onset IGN)
    res["sensitivity"] = {}
    for lab in ("lab_x70", "lab_l10", "lab_ign"):
        ev = [r for r in rows if r[lab] in K.EVAL]
        base = sum(r[lab] == "POS710" for r in ev) / len(ev) if ev else None
        res["sensitivity"][lab] = {"base": round(base, 4) if base else None}
        for n, f in (("RN_A", cand), ("TC_TECH", tc), ("RSI30", r30)):
            fl = [r for r in ev if f(r)]
            p = sum(r[lab] == "POS710" for r in fl) / len(fl) if fl else None
            res["sensitivity"][lab][n] = {"flagged": len(fl), "precision": round(p, 4) if p is not None else None,
                                          "lift": round(p / base, 3) if (p is not None and base) else None}
    # overlap with SEQ70's flag (top-quintile volume ratio and a negative 5-session return)
    hs = [r for r in ev_rows if r.get("p_v1x") is not None and r["p_v1x"] >= 0.8 and K.num(r.get("r5")) is not None
          and K.num(r.get("r5")) < 0]
    res["overlap_seq70"] = {"RN_A_rows": sum(1 for r in ev_rows if cand(r)), "SEQ70_flag_rows": len(hs),
                            "both": sum(1 for r in hs if cand(r))}
    # by month (descriptive)
    bym = defaultdict(lambda: [0, 0])
    for r in ev_rows:
        if cand(r):
            bym[r["t"][:7]][0] += 1
            bym[r["t"][:7]][1] += r["lab"] == "POS710"
    res["RN_A_by_month"] = {m: [n, p, round(p / n, 4)] for m, (n, p) in sorted(bym.items())}
    # events outside the pivot population: would RN_A have held on their bars at T-10 … T-7?
    lo, hi = K.WINDOWS[w]
    outs = defaultdict(list)
    for r in ewin:
        if lo <= r["t"] <= hi and r["sym"] not in K.EXCLUDE and r["cond_ok"] == "1":
            outs[(r["sym"], r["launch"])].append(r)
    nopiv = {k: v for k, v in outs.items() if not any(x["pivot"] == "1" for x in v)}
    res["outside_population"] = {"events_with_no_pivot_day_T10_T7": len(nopiv),
                                 "RN_A_held_at_least_once": sum(1 for v in nopiv.values() if any(cand(x) for x in v)),
                                 "TC_TECH_held_at_least_once": sum(1 for v in nopiv.values() if any(tc(x) for x in v)),
                                 "split120_at_T8": sum(1 for v in nopiv.values()
                                                       if any(x["off"] == "-8" and x["split120"] == "1" for x in v))}
    return res, p1, p3


def hubc():
    rows = [r for r in rd("seeds.csv.gz") if r["sym"] == "HUBC" and r.get("t")]
    rows.sort(key=lambda r: r["t"])
    out = []
    for r in rows[-10:]:
        out.append({"t": r["t"], "pivot": r["pivot"], "px": r["px"], "rsi": r["rsi"], "hold_n": r["hold_n"],
                    "dist": r["dist"], "bounce": r["bounce"], "boom5": r["boom5"], "split120": r["split120"],
                    "RN_A": int(K.ROUND2["RN_A"](r)), "TC_TECH": int(K.EXISTING["TC_TECH"](r)),
                    "RSI30": int(K.COND["RSI30"](r))})
    return {"last_sessions": out,
            "context": "outside the pivot population (M2 ceiling after the 2026-09-14 1:25 reverse split, frozen); the "
                       "data-quality gate quarantines recent splits; no statistic of this study involves HUBC; the "
                       "outcome after 2026-10-08 is unknown (no bars)"}


def status(win, pooled):
    suff = [win[w]["sufficient"] for w in OOS]
    if not any(suff):
        return "BLOCKED_BY_SPECIFIC_DATA_GAP"
    if all(suff) and all(all(win[w]["pass"].values()) for w in OOS):
        return "VALIDATED_READY_SIGNAL"
    if (pooled["C1"]["ci"] and pooled["C1"]["ci"][0] > 1.0 and pooled["C3"]["ci"] and pooled["C3"]["ci"][0] > 1.0):
        return "PROMISING_UNVALIDATED"
    return "NO_INCREMENTAL_EDGE_FOUND"


def final():
    if not prereg_ok():
        print("⛔ RN_SPEC.md differs from the sealed version — nothing read")
        sys.exit(9)
    cal = json.load(open(os.path.join(DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    rows_all = rd("rows.csv.gz")
    events_all = rd("events.csv.gz")
    ewin = rd("ewin.csv.gz")
    win, pairs1, pairs3 = {}, [], []
    for w in OOS:
        res, p1, p3 = window(w, rows_all, events_all, ewin, cal)
        win[w] = res
        pairs1 += p1
        pairs3 += p3
    pooled = {}
    for name, pr in (("C1", pairs1), ("C3", pairs3)):
        est, ci = K.cluster_ratio(_units(pr), REPS, SEED, ALPHA_P)
        pooled[name] = {"pairs": len(pr), "ratio": est, "ci": ci}
    out = {"spec_sha256": PREREG_SHA256, "candidate": "RN_A = RSI14 < 30 and bounce from the 25-session low 10–40%",
           "windows": win, "pooled_95": pooled, "status": status(win, pooled), "HUBC": hubc()}
    json.dump(out, open(os.path.join(DATA, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    if (sys.argv[1] if len(sys.argv) > 1 else "") != "final":
        sys.exit("usage: rn_eval.py final")
    r = final()
    for w in OOS:
        x = r["windows"][w]
        print(w, x["window"], "sufficient", x["sufficient"], "pass", x["pass"], "C1", x["C1"]["ratio"], x["C1"]["ci"],
              "C2", x["C2"], "C3", x["C3"]["ratio"], x["C3"]["ci"])
    print("pooled", r["pooled_95"], "→", r["status"])
