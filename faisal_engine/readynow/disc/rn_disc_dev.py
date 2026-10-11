"""READY NOW discovery — development map (2025-05-01 → 2025-12-31 only; descriptive, nothing sealed is re-read).

Target = the corrected onset (`rn_disc_build.py`: start of the final +70% leg) 7–10 sessions after the decision.
1. Existing rules against the corrected target (they were sealed against READYNOW's trough onset; this is the
   correction of the affected calculation, not a new test of them).
2. Groups per eligible event (a POS710 pivot-day in [onset−10, onset−7]): A captured by the reference rules · B missed ·
   and per pivot-day C (flagged, no event) · D (not flagged, no event).
3. Missed-winner map: inside the rows the reference rules do NOT flag, the POS710 rate by pre-declared bins of every
   point-in-time feature (bins = quartiles of the window's NEG rows), with Wilson intervals — what separates missed
   winners (B rows) from inactive pivots the rules also ignore (D rows).
Seeds and HUBC are excluded from every statistic (they generated hypotheses).
Run from the repo root:  python3 faisal_engine/readynow/disc/rn_disc_dev.py   → disc/data/dev_map.json
"""
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
sys.path.insert(0, RN)
os.environ["FAISAL_ONLY"] = "1"
import rn_lib as K                                                        # noqa: E402

DATA = os.path.join(HERE, "data")
WIN = "development"
REPS, SEED = 2000, 20261011
num = K.num


def load(window=WIN):
    """Rows of one window with READYNOW's column names pointing at the corrected target (lab/ep), annotated."""
    rows = K.rd("rows.csv.gz", DATA)
    lo, hi = K.WINDOWS[window]
    out = []
    for r in rows:
        if lo <= r["t"] <= hi and r["sym"] not in K.EXCLUDE and r.get("cond_ok") == "1":
            r = dict(r, lab_L=r["lab"], lab=r["lab_on"], ep=r["ep_on"], pos110=r["pos110_on"])
            out.append(r)
    by = K.annotate(out)
    return out, by


def events(rows, window=WIN):
    cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    ev = [dict(e, launch=e["onset"], x70=e["q"]) for e in K.rd("events.csv.gz", DATA)]
    return K.events_index(rows, ev, cal, window), {d: k for k, d in enumerate(cal)}


def hs70(r):
    """SEQ70's sealed hypothesis H-S70: 5-session return below 0 and volume in the session's top quintile."""
    v, p = num(r.get("r5")), r.get("p_v1x")
    return v is not None and v < 0 and p is not None and p >= 0.8


REFS = {"TC_TECH": K.EXISTING["TC_TECH"], "RN_A": K.ALL_RULES["RN_A"],
        "APP_POS": lambda r: K.COND["NEAR15"](r) and K.COND["BOUNCE10_40"](r), "H_S70": hs70,
        "STAGE1": lambda r: r.get("pc_stage") == "1", "LOC": K.EXISTING["LOC"]}
REF_UNION = ("TC_TECH", "RN_A", "H_S70", "STAGE1", "LOC")


def union(r):
    return any(REFS[k](r) for k in REF_UNION)


FEATS = ("rsi", "rsi_low", "dist", "bounce", "hold_n", "boom5", "dv20", "range20", "tl_dist", "r5", "v1x", "v5x",
         "tr5x", "pos60", "bot_age", "nlow20", "clv5", "pc_bottom_ago", "pc_vs_bottom", "rise_low10", "ret1",
         "rsi_div_gap", "hl_count", "first_up", "px")
FLAGS = ("below3", "macd_pos", "ema_up", "ema_x5", "split120", "rsi_div", "rise10_vdry", "v_then_up", "in_drift",
         "pc_stage", "pc_first_rise", "loc")


def qcuts(vals):
    v = sorted(vals)
    return [v[int(len(v) * q)] for q in (0.25, 0.5, 0.75)] if len(v) >= 40 else None


def bin_of(x, cuts):
    return sum(x > c for c in cuts)


def rate(rows):
    ev = [r for r in rows if r["lab"] in K.EVAL]
    p = sum(r["lab"] == "POS710" for r in ev)
    return len(ev), p, (round(p / len(ev), 4) if ev else None), K.wilson(p, len(ev))


def main():
    rows, by = load()
    evs, six = events(rows)
    ev_rows = [r for r in rows if r["lab"] in K.EVAL]
    base = sum(r["lab"] == "POS710" for r in ev_rows) / len(ev_rows)
    out = {"window": K.WINDOWS[WIN], "rows": len(rows), "evaluable": len(ev_rows), "base_rate": round(base, 4),
           "labels": dict(Counter(r["lab"] for r in rows)),
           "eligible_events": sum(1 for e in evs if e["pos_rows"]), "events_in_window": len(evs)}
    # 1. existing rules against the corrected target
    out["existing_rules"] = {}
    for name, f in list(REFS.items()) + [("REF_UNION", union)]:
        e = K.evaluate(rows, by, evs, six, f, REPS, SEED, 0.05, name)
        m = K.matched(by, f, REPS, SEED, 0.05)
        out["existing_rules"][name] = {k: e[k] for k in ("flags_per_session", "precision", "lift", "lift_ci",
                                                         "events_captured", "events_eligible", "recall",
                                                         "lead_to_onset_q25_med_q75", "lead_to_x70_q25_med_q75")}
        out["existing_rules"][name]["matched"] = {k: m[k] for k in ("pairs", "ratio", "ci")}
        out["existing_rules"][name]["minus_VOL_k_pp"] = [e["VOL_k"]["rule_minus_pp"], e["VOL_k"]["rule_minus_pp_ci"]]
        out["existing_rules"][name]["minus_VOLAT_k_pp"] = [e["VOLAT_k"]["rule_minus_pp"], e["VOLAT_k"]["rule_minus_pp_ci"]]
    # 2. groups
    elig = [e for e in evs if e["pos_rows"]]
    A = [e for e in elig if any(union(r) for r in e["pos_rows"])]
    Bm = [e for e in elig if not any(union(r) for r in e["pos_rows"])]
    tc_cap = [e for e in elig if any(REFS["TC_TECH"](r) for r in e["pos_rows"])]
    neg = [r for r in ev_rows if r["lab"] == "NEG"]
    out["groups"] = {"A_events_captured_by_union": len(A), "B_events_missed_by_union": len(Bm),
                     "captured_by_TC_TECH": len(tc_cap), "missed_by_TC_TECH": len(elig) - len(tc_cap),
                     "C_rows_flagged_no_event": sum(1 for r in neg if union(r)),
                     "D_rows_not_flagged_no_event": sum(1 for r in neg if not union(r)),
                     "union_flags_share_of_rows": round(sum(1 for r in ev_rows if union(r)) / len(ev_rows), 4)}
    # representative row per event: the earliest POS row in its window
    rep = lambda e: min(e["pos_rows"], key=lambda r: r["t"])            # noqa: E731
    prof = {}
    for gname, grp in (("A", [rep(e) for e in A]), ("B", [rep(e) for e in Bm]),
                       ("D_rows", [r for r in neg if not union(r)])):
        p = {}
        for k in FEATS:
            v = sorted(x for x in (num(r.get(k)) for r in grp) if x is not None)
            p[k] = [v[len(v) // 4], v[len(v) // 2], v[3 * len(v) // 4]] if v else None
        for k in FLAGS:
            v = [r.get(k) for r in grp if r.get(k) not in (None, "")]
            p[k] = dict(Counter(v).most_common(6)) if v else None
        p["n"] = len(grp)
        prof[gname] = p
    out["profiles_q25_med_q75"] = prof
    # 3. missed-winner map inside the rows the reference rules do not flag
    free = [r for r in ev_rows if not union(r)]
    fb = sum(r["lab"] == "POS710" for r in free) / len(free)
    mp = {"rows": len(free), "base": round(fb, 4), "numeric": {}, "flags": {}}
    for k in FEATS:
        cuts = qcuts([x for x in (num(r.get(k)) for r in free if r["lab"] == "NEG") if x is not None])
        if not cuts:
            continue
        cells = defaultdict(list)
        for r in free:
            x = num(r.get(k))
            cells["missing" if x is None else f"Q{bin_of(x, cuts) + 1}"].append(r)
        mp["numeric"][k] = {"cuts": [round(c, 4) for c in cuts],
                            **{b: (lambda t: {"n": t[0], "pos": t[1], "rate": t[2], "lift": round(t[2] / fb, 3)
                                              if t[2] is not None else None, "wilson": t[3]})(rate(rs))
                               for b, rs in sorted(cells.items())}}
    for k in FLAGS:
        cells = defaultdict(list)
        for r in free:
            cells[r.get(k) if r.get(k) not in (None, "") else "missing"].append(r)
        mp["flags"][k] = {b: (lambda t: {"n": t[0], "pos": t[1], "rate": t[2], "lift": round(t[2] / fb, 3)
                                         if t[2] is not None else None, "wilson": t[3]})(rate(rs))
                          for b, rs in sorted(cells.items(), key=lambda kv: str(kv[0])) if len(rs) >= 30}
    out["missed_winner_map"] = mp
    json.dump(out, open(os.path.join(DATA, "dev_map.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


if __name__ == "__main__":
    r = main()
    print(json.dumps({k: r[k] for k in ("window", "rows", "evaluable", "base_rate", "eligible_events", "groups")}, indent=1))
    for n, v in r["existing_rules"].items():
        print(n, v)
