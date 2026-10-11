"""READYNOW — Phase 1 (seeds) and Phase 2 / Layers A–C on the DEVELOPMENT window only (2025-05-01 → 2025-12-31).

`seeds`: the four seeds at T-10 … T-7 before each qualifying onset (and DKI, which has none), every condition and
          rule of `rn_lib` → data/seeds_matrix.json (hypothesis generation; seeds never enter a statistic).
`dev`:   development rows only (guarded by test_rn G2) → data/dev.json: population and events, groups A–D, Layer A
          (each condition), Layer B (matched on price bucket, volume, volatility, liquidity; and within the tool's
          status), Layer C (declared combinations and the order test), equal-burden volume ranking, the existing
          rules, missed winners by archetype, events outside the pivot population.
Run from the repo root:  python3 faisal_engine/readynow/rn_dev.py seeds|dev
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rn_lib as K                                                       # noqa: E402

DEV_REPS = 1000
SEED = 20261011
ALPHA = 0.05
SEED_EVENTS = (("DLXY", "2026-08-31"), ("RETO", "2026-09-15"), ("SXTC", "2026-06-08"), ("SXTC", "2026-07-30"),
               ("SXTC", "2026-10-07"))
FAISAL_DATES = {   # dated Faisal units in the local corpus (fm_forensics/phase3/FAISAL_TIMELINE.csv); none ⇒ stated
    "DLXY": "none in the corpus (phase-5 control pool «without any Faisal unit»); raised by the owner 2026-09-26",
    "RETO": "none in the corpus (phase-5 control pool «without any Faisal unit»); raised by the owner 2026-09-26",
    "DKI": "FOCUS 2026-09-13 (X_20260918_22_pipeline · X_20260918_23_watchlist); WAIT for a sweep (TG_57893/57894)",
    "SXTC": "READY 2026-09-10 (WA_20260918_31_SXTC) · ENTRY 2026-09-11 (X_20260918_24_SXTC) · FOCUS 2026-09-13 · "
            "ENTRY inferred 2026-09-24 (TG_58527)",
}


def _cal():
    return json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]


def load_window(w):
    """Rows of one window only — the reader for development (G2 asserts nothing later is returned)."""
    rows = K.window_rows(K.rd("rows.csv.gz"), w)
    return rows


def _rules(r):
    return {n: int(bool(f(r))) for n, f in K.ALL_RULES.items()}


def seeds():
    cal = _cal()
    ix = {d: k for k, d in enumerate(cal)}
    srows = K.rd("seeds.csv.gz")
    ev = {(e["sym"], e["launch"]): e for e in K.rd("events.csv.gz")}
    by = defaultdict(dict)
    for r in srows:
        if r.get("t"):
            by[r["sym"]][r["t"]] = r
    out = {"faisal_dates": FAISAL_DATES, "events": [], "dki": {}}
    for sym, launch in SEED_EVENTS:
        e = ev[(sym, launch)]
        L = ix[launch]
        days = []
        for off in range(-10, -6):
            d = cal[L + off]
            r = by[sym].get(d) or {}
            vals = {k: r.get(k) for k in ("pivot", "px", "rsi", "rsi_low", "hold_n", "held", "dist", "bounce", "boom5",
                                          "pc_stage", "pc_branch", "loc", "split120")}
            days.append({"off": off, "t": d, "values": vals, "rules": _rules(r) if r else {}})
        sat = {n: sum(d["rules"].get(n, 0) for d in days) for n in K.ALL_RULES}
        out["events"].append({"sym": sym, "onset_L": launch, "L10": e["l10"], "ignition": e["ign"],
                              "x70": e["x70"] or None, "d1": e["d1"], "kind": e["kind"], "peak_gain": e["peak_gain"],
                              "in_pivot_population_T10_T7": sum(int(d["values"]["pivot"] or 0) for d in days),
                              "days": days, "satisfied_of_4": sat})
    # DKI: no qualifying close-based onset; state at Faisal's FOCUS and before the 2026-10-07 intraday spike
    for tag, d0 in (("faisal_focus_2026-09-13_next_session", "2026-09-14"), ("T-10_of_2026-10-07", cal[ix["2026-10-07"] - 10]),
                    ("T-7_of_2026-10-07", cal[ix["2026-10-07"] - 7])):
        r = by["DKI"].get(d0) or {}
        out["dki"][tag] = {"t": d0, "values": {k: r.get(k) for k in ("pivot", "px", "rsi", "rsi_low", "hold_n", "dist",
                                                                       "bounce", "boom5", "pc_stage", "loc")},
                           "rules": _rules(r) if r else {}}
    out["dki"]["note"] = ("no clean episode of the bot's detector (close-to-close jump ≥ 50% or run ≥ 70%) from "
                          "2026-05-01 to 2026-10-08: 2026-10-07 closed +22.8% (1.36 → 1.67) after an intraday high of "
                          "3.64; the move is invisible to a daily-close rule")
    json.dump(out, open(os.path.join(K.DATA, "seeds_matrix.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def dev():
    w = "development"
    rows = load_window(w)
    cal = _cal()
    sess_ix = {d: k for k, d in enumerate(cal)}
    by = K.annotate(rows)
    events = K.events_index(rows, K.rd("events.csv.gz"), cal, w)
    labs = Counter(r["lab"] for r in rows)
    out = {"window": K.WINDOWS[w], "rows": len(rows), "symbols": len({r["sym"] for r in rows}), "sessions": len(by),
           "labels": dict(sorted(labs.items())), "events_in_window": len(events),
           "events_with_evaluable_early_row": sum(1 for e in events if e["pos_rows"]),
           "events_without_pivot_row_in_T10_T7": sum(1 for e in events if not e["in_window_pivot_rows"])}
    out["layerA"] = {n: K.evaluate(rows, by, events, sess_ix, f, DEV_REPS, SEED, ALPHA, n) for n, f in K.COND.items()}
    out["layerC"] = {n: K.evaluate(rows, by, events, sess_ix, f, DEV_REPS, SEED, ALPHA, n)
                     for n, f in dict(K.COMBO, **K.SEQ_PAIRS).items()}
    out["existing"] = {n: K.evaluate(rows, by, events, sess_ix, f, DEV_REPS, SEED, ALPHA, n) for n, f in K.EXISTING.items()}
    tc = K.EXISTING["TC_TECH"]
    out["layerB"] = {}
    for n, f in dict(K.COND, **K.COMBO, **K.SEQ_PAIRS).items():
        out["layerB"][n] = {"matched": K.matched(by, f, DEV_REPS, SEED, ALPHA),
                            "matched_within_tool_status": K.matched(by, f, DEV_REPS, SEED, ALPHA, exact=tc)}
    out["layerB"]["TC_TECH"] = {"matched": K.matched(by, tc, DEV_REPS, SEED, ALPHA)}
    # missed winners and alternative structures (descriptive): the archetype of each eligible event's POS710 rows vs
    # the archetype mix of all evaluable rows
    ev_rows = [r for r in rows if r["lab"] in K.EVAL]
    mix = Counter(K.archetype(r) for r in ev_rows)
    pos_mix = Counter(K.archetype(r) for r in ev_rows if r["lab"] == "POS710")
    out["archetypes"] = {a: {"rows": mix[a], "pos710": pos_mix.get(a, 0),
                             "rate": round(pos_mix.get(a, 0) / mix[a], 4) if mix[a] else None} for a in sorted(mix)}
    ev_first = Counter(K.archetype(e["pos_rows"][0]) for e in events if e["pos_rows"])
    out["archetypes_events_first_row"] = dict(sorted(ev_first.items()))
    # events outside the pivot population: their structure at T-8 (from ewin, the bars themselves)
    ew = [r for r in K.rd("ewin.csv.gz") if K.WINDOWS[w][0] <= r["t"] <= K.WINDOWS[w][1] and r["sym"] not in K.EXCLUDE]
    outside = [r for r in ew if r["off"] == "-8" and r["pivot"] == "0" and r["cond_ok"] == "1"]
    out["outside_population_T8"] = {"rows": len(outside), "archetype": dict(Counter(K.archetype(r) for r in outside)),
                                    "split120": sum(r["split120"] == "1" for r in outside),
                                    "rules_satisfied": {n: sum(1 for r in outside if f(r)) for n, f in
                                                        dict(K.COMBO, **K.EXISTING).items() if n != "LOC"}}
    json.dump(out, open(os.path.join(K.DATA, "dev.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def dev2():
    """Round 2 on development (post hoc, disclosed): the tool's part plus the conditions whose matched lower bound
    exceeded 1, Faisal's RSI text with the bounce chip; the tool's own increment tests; overlap with SEQ70's
    volume-and-negative-return flag; onset/event sensitivity; the choice rule of RN_SPEC §6."""
    w = "development"
    rows = load_window(w)
    cal = _cal()
    sess_ix = {d: k for k, d in enumerate(cal)}
    by = K.annotate(rows)
    events = K.events_index(rows, K.rd("events.csv.gz"), cal, w)
    tc = K.EXISTING["TC_TECH"]
    ev_rows = [r for r in rows if r["lab"] in K.EVAL]
    out = {"round2": {}, "within_tool": {}, "beyond_tool": {}, "sensitivity": {}}
    for n, f in dict(K.ROUND2, RSI30=K.COND["RSI30"], TC_TECH=tc).items():
        out["round2"][n] = K.evaluate(rows, by, events, sess_ix, f, DEV_REPS, SEED, ALPHA, n)
        out["round2"][n]["matched"] = K.matched(by, f, DEV_REPS, SEED, ALPHA)
    for n in ("TC_BOUNCE", "TC_NEAR", "TC_APP"):
        f = K.ROUND2[n]
        u = defaultdict(lambda: [0, 0, 0, 0])
        for r in ev_rows:
            if tc(r):
                x = u[r["sym"]]
                j = 0 if f(r) else 2
                x[j] += 1
                x[j + 1] += r["lab"] == "POS710"
        out["within_tool"][n] = list(K.cluster_ratio(u, DEV_REPS, SEED, ALPHA))
    for n, f in (("RSI30", K.COND["RSI30"]), ("RN_A", K.ROUND2["RN_A"]), ("RSI33", K.COND["RSI33"])):
        out["beyond_tool"][n] = K.matched(by, K.only_beyond_tool(f), DEV_REPS, SEED, ALPHA, exact=tc)
    rna, r30 = K.ROUND2["RN_A"], K.COND["RSI30"]
    u = defaultdict(lambda: [0, 0, 0, 0])
    for r in ev_rows:
        if r30(r):
            x = u[r["sym"]]
            j = 0 if rna(r) else 2
            x[j] += 1
            x[j + 1] += r["lab"] == "POS710"
    out["bounce_within_rsi30"] = list(K.cluster_ratio(u, DEV_REPS, SEED, ALPHA))
    hs = [r for r in ev_rows if r.get("p_v1x") is not None and r["p_v1x"] >= 0.8 and (K.num(r.get("r5")) or 0) < 0
          and K.num(r.get("r5")) is not None]
    out["overlap"] = {"RN_A_rows": sum(1 for r in ev_rows if rna(r)), "TC_TECH_rows": sum(1 for r in ev_rows if tc(r)),
                      "both": sum(1 for r in ev_rows if rna(r) and tc(r)),
                      "SEQ70_flag_rows": len(hs), "SEQ70_flag_and_RN_A": sum(1 for r in hs if rna(r))}
    el = [e for e in events if e["pos_rows"]]
    ca = {e["sym"] + e["launch"] for e in el if any(rna(r) for r in e["pos_rows"])}
    ct = {e["sym"] + e["launch"] for e in el if any(tc(r) for r in e["pos_rows"])}
    out["events_paired"] = {"eligible": len(el), "RN_A": len(ca), "TC_TECH": len(ct), "RN_A_only": len(ca - ct),
                            "TC_only": len(ct - ca), "both": len(ca & ct),
                            "missed_by_RN_A_archetype": dict(Counter(K.archetype(e["pos_rows"][0]) for e in el
                                                                     if e["sym"] + e["launch"] not in ca)),
                            "captured_by_RN_A_archetype": dict(Counter(K.archetype(e["pos_rows"][0]) for e in el
                                                                       if e["sym"] + e["launch"] in ca))}
    for lab in ("lab_x70", "lab_l10", "lab_ign"):
        ev = [r for r in rows if r[lab] in K.EVAL]
        base = sum(r[lab] == "POS710" for r in ev) / len(ev)
        out["sensitivity"][lab] = {"base": round(base, 4)}
        for n, f in (("TC_TECH", tc), ("RSI30", r30), ("RN_A", rna)):
            fl = [r for r in ev if f(r)]
            p = sum(r[lab] == "POS710" for r in fl) / len(fl) if fl else None
            out["sensitivity"][lab][n] = {"flagged": len(fl), "precision": round(p, 4) if p is not None else None,
                                          "lift": round(p / base, 3) if p is not None else None}
    json.dump(out, open(os.path.join(K.DATA, "dev_round2.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "seeds":
        print(json.dumps(seeds(), ensure_ascii=False, indent=1)[:4000])
    elif mode == "dev":
        res = dev()
        keep = ("flags_per_session", "precision", "base_rate", "lift", "lift_ci", "recall", "events_eligible",
                "VOL_k", "trigger_precision")
        for sec in ("layerA", "layerC", "existing"):
            print(f"\n## {sec}")
            for n, v in res[sec].items():
                print(n, {k: v.get(k) for k in keep})
        print("\n## layerB")
        for n, v in res["layerB"].items():
            print(n, {k: (x["ratio"], x["ci"], x["pairs"]) for k, x in v.items()})
        print({k: res[k] for k in ("rows", "symbols", "sessions", "labels", "events_in_window",
                                   "events_with_evaluable_early_row", "events_without_pivot_row_in_T10_T7")})
        print(res["archetypes"], res["archetypes_events_first_row"], res["outside_population_T8"])
    elif mode == "dev2":
        print(json.dumps(dev2(), ensure_ascii=False, indent=1)[:6000])
    else:
        sys.exit("usage: rn_dev.py seeds|dev|dev2")
