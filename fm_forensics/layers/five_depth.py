"""Five vs rest — how far below the base did the price go before the move? (owner order 2026-10-14 «قارن الخمسة بالباقي في عمق
الهبوط» · descriptive only: no contract, no verdict, no production / V4 / H6 / Telegram / threshold / root change).

The measure is T-LAYERS stage B's, unchanged: over the 20 sessions O−20 … O−1 the deepest `sweep_pct` of the production cycle
`Super_stock.pivot_cycle_state(df[..x], sweep=99)` (no base reset) on days at stage ≥ 3 in the «sweep» branch — every reading from
`[..x]` with x ≤ O−1. Everything else is GEN5 / T-HEAT BY NAME: the five's episodes (`gen5_ext.realizations` since
`gen5_fix.GEN_SINCE`, the generation of GEN5), quality and the onset anchor O (`gen5_fix.row_stats` · `heat_test.build_events` anchor
"O" on the extended window), the reverse-split check (`gen5_ext.split_unadjusted` on `gen5_features.load_splits`), and the
TradingView split-adjusted daily bars (`gen5_fix.Data`: the rank archive for the window, the GEN5 fresh bars as a cross-check).
Unknown stays unknown (never zero); a symbol whose bars are split-unadjusted in the window is reported as such, not measured.

    python3 fm_forensics/layers/five_depth.py        # ⟶ data/five_depth.json (+ printed tables)
"""
import contextlib
import io
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
for _p in (os.path.join(ROOT, "fm_forensics", "gen5"), os.path.join(ROOT, "fm_forensics", "heat"), ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

OUT = os.path.join(HERE, "data", "five_depth.json")
LAYERS_RESULT = os.path.join(HERE, "data", "layers_result.json")
LEAD = 20                # the T-LAYERS stage B window O−20 … O−1
MIN_BARS = 60            # PIVOT_CYCLE_WIN
SW_LO, SW_HI = 7.0, 13.0  # «سحب السيوله متعارف عليه من 7٪ ل 13٪» (IMG_0297)
FREE_SWEEP = 99          # no base reset (the T-LAYERS free depth)
JUMP_X = 3.0             # descriptive: a close-to-close change beyond ×3 (or under ÷3) in the measured span = a possible unrecorded split


def depth_window(pc_fn, df, k, lead=LEAD, sweep=FREE_SWEEP):
    """Deepest sweep under the cycle base in [k−lead, k−1] ⟶ dict or {"depth": None, "why": ...}. sweep=99 (default): the T-LAYERS
    free depth (no base reset) · sweep=None: the production cycle as it runs (the base resets past PIVOT_SWEEP_PCT=13)."""
    best, short, seen = None, 0, 0
    for x in range(max(0, k - lead), k):
        if x + 1 < MIN_BARS:
            short += 1
            continue
        seen += 1
        pc = pc_fn(df.iloc[: x + 1], sweep=sweep)
        if not pc or int(pc.get("stage") or 0) < 3 or pc.get("branch") != "sweep":
            continue
        d = float(pc.get("sweep_pct") or 0.0)
        if best is None or d > best["depth"]:
            b = x - int(pc["bottom_ago"])
            best = {"depth": round(d, 2), "day": df.index[x].date().isoformat(), "base": pc["bottom"],
                    "base_day": df.index[b].date().isoformat() if 0 <= b < len(df) else None, "sweep_low": pc.get("retest_low"),
                    "stage": int(pc["stage"])}
    if best is not None:
        return best
    return {"depth": None, "why": "short_history" if seen == 0 else "no_sweep_in_window", "short_days": short}


def frame(rows):
    import pandas as pd
    rows = [list(r[:6]) + [float("nan")] * (6 - len(r[:6])) for r in rows]
    df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df.index = pd.to_datetime(df["Date"])
    return df[["Open", "High", "Low", "Close", "Volume"]].astype(float)


def band(d):
    if d is None:
        return "مجهول"
    return "أقلّ من 7%" if d < SW_LO else ("7-13% (نطاق فيصل)" if d <= SW_HI else "أعمق من 13%")


def quantiles(vals):
    v = sorted(vals)

    def q(p):
        if not v:
            return None
        i = (len(v) - 1) * p
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 2)
    return {"n": len(v), "q25": q(0.25), "median": q(0.5), "q75": q(0.75),
            "under_7": sum(1 for x in v if x < SW_LO), "in_band": sum(1 for x in v if SW_LO <= x <= SW_HI),
            "over_13": sum(1 for x in v if x > SW_HI)}


def session_label(where):
    w = (where or "").lower()
    return "بري" if w.startswith("pre") else ("أفتر" if w.startswith("after") else ("نظاميّة" if w else None))


def split_check(X, D, s, df, k):
    """Reverse splits dated in the measured span (the 60-bar cycle before the window + the window) and whether the bars are
    split-unadjusted there (gen5_ext.split_unadjusted by name) ⟶ (span_from, window, reverse_splits, unadjusted_days)."""
    lo_day = df.index[max(0, k - LEAD - MIN_BARS)].date().isoformat()
    hi_day = df.index[k - 1].date().isoformat()
    splits = D.splits.get(s) or []
    rev = [[d, f] for d, f in splits if lo_day < d <= hi_day and 0 < float(f) < 1]
    arow = [[t.date().isoformat(), 0, 0, 0, float(c), 0] for t, c in zip(df.index, df["Close"])]
    return lo_day, [df.index[max(0, k - LEAD)].date().isoformat(), hi_day], rev, X.split_unadjusted(arow, splits, lo_day, hi_day)


def jumps(df, k):
    """Close-to-close changes beyond ×JUMP_X either way in the measured span [k−LEAD−MIN_BARS, k−1] (descriptive flag only)."""
    c = df["Close"].to_numpy(float)
    out = []
    for i in range(max(1, k - LEAD - MIN_BARS), k):
        if c[i - 1] > 0 and c[i] > 0 and (c[i] / c[i - 1] > JUMP_X or c[i - 1] / c[i] > JUMP_X):
            out.append([df.index[i].date().isoformat(), round(float(c[i] / c[i - 1]), 4)])
    return out


def robustness(pc_fn, df, k, split_days, jump_days):
    """Descriptive checks for a flagged seed: (a) THE SAME measure with each split day's low neutralised to min(open, close) — a
    split-day intraday low is the least trustworthy print; (b) after the last ×3 jump in the span, a plain drawdown (first close after
    it ⟶ lowest low before the anchor) — labelled as a drawdown, not the cycle measure."""
    out = {}
    if split_days:
        d2 = df.copy()
        for i, t in enumerate(d2.index):
            if t.date().isoformat() in split_days:
                d2.iloc[i, d2.columns.get_loc("Low")] = min(float(d2["Open"].iloc[i]), float(d2["Close"].iloc[i]))
        out["depth_split_low_neutral"] = depth_window(pc_fn, d2, k).get("depth")
    if jump_days:
        lo = df["Low"].to_numpy(float)
        c = df["Close"].to_numpy(float)
        days = [t.date().isoformat() for t in df.index]
        j = days.index(jump_days[-1])
        seg = lo[j: k]
        if len(seg) and c[j] > 0:
            m = int(seg.argmin())
            out["drawdown_after_last_jump"] = {"from_close": round(float(c[j]), 4), "from_day": days[j], "min_low": round(float(seg[m]), 4),
                                               "min_day": days[j + m], "fall_pct": round((1.0 - float(seg[m]) / float(c[j])) * 100.0, 2)}
    return out


def measure_row(S, X, H, D, r, st, anchor="O"):
    """One row through quality + the anchor (by name) and the depth on the archive and on the fresh bars."""
    s = r["SYMBOL"]
    ev, acc = H.build_events(D, [r], [st], anchor)
    out = {"sym": s, "expl": r["EXPL_DATE"], "src": r.get("_src"), "status": None}
    if st:
        out.update({"E_star": st.get("realized_day"), "where": session_label(st.get("realized_where")),
                    "where_raw": st.get("realized_where"), "ext_peak": st.get("ext_peak"), "reg_peak": st.get("reg_peak"),
                    "close_peak": st.get("close_peak"), "qa": st.get("status")})
    if not ev:
        why = next((k for k, v in acc.items() if isinstance(v, list) and v), "unknown")
        out["status"] = why
        hit = acc.get(why) or []
        if why == "not_2x_from_onset" and hit and len(hit[0]) > 2:
            out["O"] = hit[0][2]
        return out
    e = ev[0]
    out.update({"status": "EVENT", "O": e["A"], "k": e["k"]})
    df = D.arch[s]
    k = e["k"]
    lo_day, window, rev, unadj = split_check(X, D, s, df, k)
    hi_day = window[1]
    splits = D.splits.get(s) or []
    out.update({"window": window, "span_from": lo_day, "reverse_splits": rev, "archive_unadjusted": unadj, "jumps": jumps(df, k)})
    out["archive"] = depth_window(S.pivot_cycle_state, df, k) if not unadj else {"depth": None, "why": "split_unadjusted"}
    a = out["archive"]
    if a.get("depth") is not None and (rev or out["jumps"]):
        out["robust"] = robustness(S.pivot_cycle_state, df, k, {d for d, _f in rev}, [d for d, _x in out["jumps"]])
    out["prod_cycle"] = (depth_window(S.pivot_cycle_state, df, k, sweep=None) if not unadj
                         else {"depth": None, "why": "split_unadjusted"})
    fr = D.fresh.get(s) or []
    kf = D.fidx(s, e["A"])
    if fr and kf is not None and fr[0][0] > lo_day:
        out["fresh"] = {"depth": None, "why": f"fresh bars start {fr[0][0]} after the span start {lo_day} (base may predate them)",
                        "partial": depth_window(S.pivot_cycle_state, frame(fr), kf)}
    elif fr and kf is not None:
        funadj = X.split_unadjusted(fr, splits, lo_day, hi_day)
        out["fresh"] = (depth_window(S.pivot_cycle_state, frame(fr), kf) if not funadj
                        else {"depth": None, "why": "split_unadjusted"})
    else:
        out["fresh"] = {"depth": None, "why": "no_fresh_bars"}
    return out


def main():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        import gen5_ext as X
        import gen5_fix as F
        import gen5_test as T
        import heat_test as H
        S = F.G.S() if hasattr(F, "G") else __import__("gen5_features").S()
        D = F.Data()
    import csv
    pop = [r for r in csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "READY_NOW_MISSED_SIGNALS.csv"), encoding="utf-8"))
           if r["NEAR_WATCH_14D"] in ("INSIDE", "OVERSOLD")]
    five = list(T.FIVE)
    # the five: GEN5's own episodes (generation) + their rows in the T-LAYERS population (register)
    rows5 = []
    for s in five:
        fr = D.fresh.get(s) or []
        sess, cov = D.ext_sess(s)
        for j, day, where, ratio in X.realizations(fr, sess, cov, since=F.GEN_SINCE):
            rows5.append({"SYMBOL": s, "EXPL_DATE": day, "WAS_PIVOT_IDENTITY": "False", "_src": "GEN5"})
    rows5 += [dict(r, _src="register") for r in pop if r["SYMBOL"] in five]
    seeds, seeds_b = [], []
    for r in rows5:
        st = F.row_stats(D, r["SYMBOL"], r["EXPL_DATE"])
        seeds.append(measure_row(S, X, H, D, r, st))
        seeds_b.append(measure_row(S, X, H, D, r, st, anchor="B"))
    # the rest: the same population minus the five, through the same event construction as T-LAYERS stage B
    rest_rows = [r for r in pop if r["SYMBOL"] not in five]
    stats = [F.row_stats(D, r["SYMBOL"], r["EXPL_DATE"]) for r in rest_rows]
    events, acc = H.build_events(D, rest_rows, stats, "O")
    rest = []
    for e in events:
        df = D.arch[e["sym"]]
        lo_day, window, rev, unadj = split_check(X, D, e["sym"], df, e["k"])
        dw = depth_window(S.pivot_cycle_state, df, e["k"]) if not unadj else {"depth": None, "why": "split_unadjusted"}
        pr = depth_window(S.pivot_cycle_state, df, e["k"], sweep=None) if not unadj else {"depth": None}
        rest.append({"sym": e["sym"], "O": e["A"], "expl": e["E_reg"], "reverse_splits": rev, "unadjusted": unadj,
                     "jumps": jumps(df, e["k"]), **dw, "prod_depth": pr.get("depth")})
    dvals = [x["depth"] for x in rest if x.get("depth") is not None]
    # sensitivity (descriptive): anchor B = E* for the rest, the same depth
    ev_b, acc_b = H.build_events(D, rest_rows, stats, "B")
    rest_b = []
    for e in ev_b:
        df = D.arch[e["sym"]]
        _lo, _w, _rev, unadj = split_check(X, D, e["sym"], df, e["k"])
        rest_b.append({"sym": e["sym"], "E_star": e["A"], "jumps": jumps(df, e["k"]), **(depth_window(S.pivot_cycle_state, df, e["k"]) if not unadj
                                                              else {"depth": None, "why": "split_unadjusted"})})
    # consistency with the stored T-LAYERS run 2 (same measure, same events)
    check = None
    if os.path.exists(LAYERS_RESULT):
        tl = {(e["sym"], e["A"]): e.get("depth_free_max") for e in json.load(open(LAYERS_RESULT, encoding="utf-8"))["events"]}
        pairs = [(tl.get((x["sym"], x["O"])), x.get("depth")) for x in rest if (x["sym"], x["O"]) in tl]
        check = {"compared": len(pairs), "equal": sum(1 for a, b in pairs if a == b), "rest_events": len(rest)}
    res = {"five_rows": seeds, "five_rows_anchor_B": seeds_b,
           "rest_anchor_B": {"events": len(rest_b), "dist": quantiles([x["depth"] for x in rest_b if x.get("depth") is not None]),
                             "per_event": rest_b},
           "rest_jump_events": [[x["sym"], x["jumps"], x.get("depth")] for x in rest if x["jumps"]],
           "rest_dist_without_jumps": quantiles([x["depth"] for x in rest if x.get("depth") is not None and not x["jumps"]]),
           "rest_B_jump_events": sum(1 for x in rest_b if x["jumps"]),
           "rest_B_dist_without_jumps": quantiles([x["depth"] for x in rest_b if x.get("depth") is not None and not x["jumps"]]),
           "rest_prod_cycle": quantiles([x["prod_depth"] for x in rest if x.get("prod_depth") is not None]),
           "rest_prod_cycle_none": sum(1 for x in rest if x.get("prod_depth") is None),
           "rest_reverse_split_events": sum(1 for x in rest if x["reverse_splits"]),
           "rest_unadjusted_events": [x["sym"] for x in rest if x["unadjusted"]],
           "rest": {"rows": len(rest_rows), "symbols": len({r["SYMBOL"] for r in rest_rows}),
                                        "events": len(rest), "accounting": {k: (len(v) if isinstance(v, list) else v)
                                                                             for k, v in acc.items()},
                                        "no_depth": [x for x in rest if x.get("depth") is None],
                                        "dist": quantiles(dvals), "per_event": rest},
           "five_in_population": sorted({r["SYMBOL"] for r in pop if r["SYMBOL"] in five}),
           "five_not_in_population": sorted(set(five) - {r["SYMBOL"] for r in pop}),
           "consistency_with_T_LAYERS_run2": check}
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print("rest", res["rest"]["rows"], "rows ·", res["rest"]["symbols"], "symbols ·", res["rest"]["events"], "events · dist", res["rest"]["dist"])
    print("accounting", res["rest"]["accounting"], "· consistency", check)
    print("rest anchor B", res["rest_anchor_B"]["events"], res["rest_anchor_B"]["dist"], "· rest prod cycle", res["rest_prod_cycle"],
          "none", res["rest_prod_cycle_none"], "· rest reverse-split events", res["rest_reverse_split_events"],
          "unadjusted", res["rest_unadjusted_events"])
    for x, xb in zip(seeds, seeds_b):
        a, f, pc = x.get("archive") or {}, x.get("fresh") or {}, x.get("prod_cycle") or {}
        print(x["sym"], x["src"], x["expl"], x["status"], "O", x.get("O"), "E*", x.get("E_star"), x.get("where_raw"),
              "| archive", a.get("depth"), a.get("why", ""), a.get("base"), a.get("base_day"), a.get("day"),
              "| prod", pc.get("depth"), "| fresh", f.get("depth"), (f.get("partial") or {}).get("depth"),
              "| B", (xb.get("archive") or {}).get("depth"), xb.get("O"), "| rsplits", x.get("reverse_splits"),
              "unadj", x.get("archive_unadjusted"), "jumps", x.get("jumps"), "B jumps", xb.get("jumps"), "robust", x.get("robust"))
    print("rest jump events", res["rest_jump_events"], "· without", res["rest_dist_without_jumps"],
          "· B jump events", res["rest_B_jump_events"], "· B without", res["rest_B_dist_without_jumps"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
