"""Daily + 4H readiness edge — local coverage and fetch sizing (research · read-only · offline).
Counts, from files already in the repository, the population a point-in-time daily + four-hour readiness test would use,
what of it is analyzable today, and how much intraday data a fetch would need. No network connection is opened and no
vendor is called; nothing under faisal_engine/readynow/fwd is read. Writes data/coverage.json and COVERAGE.md.
Run from the repo root:  python3 faisal_engine/h4_readiness/h4r_coverage.py   (--check: regenerate and compare)
"""
import bisect
import collections
import csv
import gzip
import hashlib
import json
import math
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
A100 = os.path.join(ROOT, "faisal_engine", "alerts100", "data")
ATLAS = os.path.join(ROOT, "faisal_engine", "readynow", "condition_atlas", "data")
CAL = os.path.join(ROOT, "faisal_engine", "readynow", "data", "calendar.json")
ARCHIVE = os.path.join(ROOT, "DECISIONS_ARCHIVE.md")
PRE_WINDOW = 10        # the task's earliest window starts 10 sessions before the move
LOOKBACK = 25          # PIVOT_LOOKBACK (the bot's 25-session low window, read by the 4H «hold at the low» conditions)
EXT_MIN = 960          # 04:00–20:00 New York minutes per full extended session
AGG_LIMIT = 50000      # the `limit` the project passes to /v2/aggs (documented maximum; whether it caps base minutes is unverified)
SMALL_N = 30           # a split with fewer winners than this cannot carry a stable precision estimate (reported, not a gate)
WINDOWS = {"development": ("2025-05-01", "2025-12-31"), "validation": ("2026-01-16", "2026-05-15"),
           "holdout": ("2026-06-02", "2026-08-27")}   # rn_lib.WINDOWS, copied; checked against rn_lib below


def rd(folder, name):
    with gzip.open(os.path.join(folder, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return v if math.isfinite(v) else None


def flat_measure():
    """The one documented measurement of a day of Polygon/Massive minute-aggregate flat files (T-AH, 2026-08-12)."""
    txt = open(ARCHIVE, encoding="utf-8").read()
    m = re.search(r"يومُ `minute_aggs` ‏≈(\d+)MB", txt)
    s = re.search(r"واختزالُه ‏([\d.]+)ث", txt)
    return (int(m.group(1)) if m else None), (float(s.group(1)) if s else None)


def build():
    sessions = json.load(open(CAL, encoding="utf-8"))["sessions"]
    idx = {d: i for i, d in enumerate(sessions)}
    out = {"inputs": {}, "definitions": {}, "timing": {}, "units": {}, "matching": {}, "local_intraday": {},
           "fetch_alert_population": {}, "fetch_atlas_population": {}}
    rn_lib = None
    try:
        sys.path.insert(0, os.path.join(ROOT, "faisal_engine", "readynow"))
        import rn_lib
        out["inputs"]["windows_match_rn_lib"] = dict(rn_lib.WINDOWS) == WINDOWS
    except Exception as e:                                                   # noqa: BLE001
        out["inputs"]["windows_match_rn_lib"] = f"unreadable: {type(e).__name__}"
    for name in ("units.csv.gz", "cohort.csv.gz", "alt_definitions.csv.gz", "build_result.json"):
        p = os.path.join(A100, name)
        out["inputs"][name] = hashlib.sha256(open(p, "rb").read()).hexdigest()
    out["inputs"]["calendar"] = [sessions[0], sessions[-1], len(sessions)]

    # ① event definitions — kept apart, never merged into one measure
    alt = rd(A100, "alt_definitions.csv.gz")
    cohort = rd(A100, "cohort.csv.gz")
    res = json.load(open(os.path.join(A100, "build_result.json"), encoding="utf-8"))
    d = out["definitions"]
    d["linked_episodes_rows"] = len(alt)
    for k in ("w100_close", "w100_high", "w100_alert_price", "w100_after_alert"):
        d[k] = sum(1 for r in alt if r[k] == "1")
    d["close_and_high"] = sum(1 for r in alt if r["w100_close"] == "1" and r["w100_high"] == "1")
    d["high_not_close"] = sorted(r["event"] for r in alt if r["w100_high"] == "1" and r["w100_close"] != "1")
    d["alert_price_not_close"] = sorted(r["event"] for r in alt if r["w100_alert_price"] == "1" and r["w100_close"] != "1")
    cw = [r for r in alt if r["w100_close"] == "1" and r["w100_after_alert"] != "1"]
    d["close_not_after_alert"] = {"priced_alert_not_doubled": sum(1 for r in cw if num(r["r_after_first_priced_alert"]) is not None),
                                  "no_priced_alert": sum(1 for r in cw if num(r["r_after_first_priced_alert"]) is None)}
    d["alert_price_hit_by_session"] = dict(collections.Counter(
        r["max_alert_price_session"] or "unpriced" for r in alt if r["w100_alert_price"] == "1"))
    d["max_alert_session_all"] = dict(collections.Counter(r["max_alert_price_session"] or "unpriced" for r in alt))
    d["YMAT"] = [r for r in alt if r["event"].startswith("YMAT|")]
    d["split_near_linked_w100"] = len(res.get("w100_split_near_linked") or [])
    d["unalerted_w100"] = (res.get("unalerted_w100_in_window") or {}).get("n") \
        if isinstance(res.get("unalerted_w100_in_window"), dict) else len(rd(A100, "unalerted_w100.csv.gz"))
    d["cohort_close_definition"] = len(cohort)
    out["timing"] = {"first_alert": dict(collections.Counter(r["first_alert_timing"] for r in cohort)),
                     "first_alert_time_kind": dict(collections.Counter(r["first_alert_time_kind"] for r in cohort))}

    # ② alerted runs (the unit of the winners-vs-controls comparison)
    units = rd(A100, "units.csv.gz")
    u = out["units"]
    u["runs"] = len(units)
    u["by_label"] = dict(collections.Counter(r["label"] for r in units))
    win = [r for r in units if r["label"] == "WIN"]
    ctrl = [r for r in units if r["label"] == "CTRL"]
    feat = lambda r: r["pivot_day_t0"] == "1" and num(r["rsi"]) is not None   # noqa: E731
    pre = [r for r in win if r["pre_move"] == "1"]
    u["winners"] = len(win)
    u["winners_pre_move"] = len(pre)
    u["winners_pre_move_with_daily_features"] = sum(1 for r in pre if feat(r))
    u["controls"] = len(ctrl)
    u["controls_with_daily_features"] = sum(1 for r in ctrl if feat(r))
    u["excluded_reasons"] = {k: v for k, v in u["by_label"].items() if k.startswith("EXCLUDED")}
    prim_w = [r for r in pre if feat(r)]
    prim_c = [r for r in ctrl if feat(r)]

    def grp(rows, key):
        return dict(sorted(collections.Counter(key(r) for r in rows).items()))
    month = lambda r: r["decision_t"][:7]                                       # noqa: E731
    price = lambda r: ("unknown" if num(r["px"]) is None else ("below_1" if num(r["px"]) < 1 else "at_or_above_1"))  # noqa: E731
    u["primary_by_month"] = {"winners": grp(prim_w, month), "controls": grp(prim_c, month)}
    u["primary_by_price"] = {"winners": grp(prim_w, price), "controls": grp(prim_c, price)}
    u["primary_by_list_at_t0"] = {"winners": grp(prim_w, lambda r: r["src_t0"] or "none"),
                                  "controls": grp(prim_c, lambda r: r["src_t0"] or "none")}
    u["primary_by_first_stream"] = {"winners": grp(prim_w, lambda r: r["first_stream"]),
                                    "controls": grp(prim_c, lambda r: r["first_stream"])}
    allp = sorted(prim_w + prim_c, key=lambda r: (r["decision_t"], r["symbol"]))
    dates = sorted({r["decision_t"] for r in allp})
    cut = [dates[len(dates) // 3], dates[2 * len(dates) // 3]] if len(dates) >= 3 else []
    third = lambda r: 0 if r["decision_t"] < cut[0] else (1 if r["decision_t"] < cut[1] else 2)  # noqa: E731
    u["chronological_thirds"] = {"cuts": cut, "decision_sessions": len(dates),
                                 "winners": [sum(1 for r in prim_w if third(r) == k) for k in range(3)],
                                 "controls": [sum(1 for r in prim_c if third(r) == k) for k in range(3)]}
    u["thirds_below_small_n"] = all(x < SMALL_N for x in u["chronological_thirds"]["winners"])

    # ③ matching feasibility (same price group, same range20 tercile, decision within ±5 sessions)
    r20 = sorted(num(r["range20"]) for r in prim_w + prim_c if num(r["range20"]) is not None)
    t1, t2 = (r20[len(r20) // 3], r20[2 * len(r20) // 3]) if r20 else (None, None)
    terc = lambda r: None if num(r["range20"]) is None else (0 if num(r["range20"]) < t1 else (1 if num(r["range20"]) < t2 else 2))  # noqa: E731
    pool = []
    for w in prim_w:
        wi = idx.get(w["decision_t"])
        pool.append(sum(1 for c in prim_c if wi is not None and idx.get(c["decision_t"]) is not None
                        and abs(idx[c["decision_t"]] - wi) <= 5 and price(c) == price(w) and terc(c) == terc(w)))
    pool.sort()
    out["matching"] = {"rule": "same price group (<$1 / ≥$1), same 20-session range tercile, decision within ±5 sessions",
                       "controls_per_winner_min_median_max": [pool[0], pool[len(pool) // 2], pool[-1]] if pool else None,
                       "winners_with_zero_controls": sum(1 for x in pool if x == 0)}

    # ④ intraday or four-hour bars stored locally (from the sealed 4H audit)
    h4 = json.load(open(os.path.join(ATLAS, "h4_audit.json"), encoding="utf-8"))
    v = h4["verdict"]
    out["local_intraday"] = {"eligible_events_all_windows": v.get("eligible_events_all_windows"),
                             "eligible_events_with_intraday_ohlc": len(v.get("eligible_events_with_intraday_ohlc") or []),
                             "eligible_events_with_any_intraday_bar": len(v.get("eligible_events_with_any_intraday_bar") or []),
                             "neg_rows_with_intraday_ohlc": v.get("neg_rows_with_intraday_ohlc"),
                             "alert_population_units_with_4h": 0,
                             "cov30": h4.get("cov30")}

    # ⑤ fetch sizing — alert population (winners + controls), per-unit window [anchor − 35, last anchor]
    launch = {r["event"]: r["launch"] for r in cohort}
    span = PRE_WINDOW + LOOKBACK
    per_sym = collections.defaultdict(set)
    no_cal = 0
    for r in win + ctrl:
        a = [r["decision_t"]]
        if r["event"] and r["event"] in launch:
            a.append(launch[r["event"]])
        ii = [idx[x] for x in a if x in idx]
        if not ii:
            no_cal += 1
            continue
        lo, hi = max(0, min(ii) - span), max(ii)
        per_sym[r["symbol"]].update(range(lo, hi + 1))
    def ranges(ix):
        s, out_r = sorted(ix), []
        for i in s:
            if out_r and i == out_r[-1][1] + 1:
                out_r[-1][1] = i
            else:
                out_r.append([i, i])
        return out_r
    reqs, symsess, allsess = 0, 0, set()
    for sym, ix in per_sym.items():
        for a0, a1 in ranges(ix):
            n = a1 - a0 + 1
            reqs += math.ceil(n * EXT_MIN / AGG_LIMIT)
            symsess += n
        allsess |= ix
    mb, sec = flat_measure()
    days = sorted(sessions[i] for i in allsess)
    out["fetch_alert_population"] = {
        "units": len(win) + len(ctrl), "units_without_calendar_date": no_cal, "symbols": len(per_sym),
        "symbol_sessions": symsess, "distinct_sessions": len(allsess), "first": days[0] if days else None,
        "last": days[-1] if days else None,
        "rest_requests_upper_bound": reqs,
        "flat_files_mb": (len(allsess) * mb) if mb else None, "flat_files_reduce_min": round(len(allsess) * sec / 60, 1) if sec else None,
        "assumptions": {"window": f"[earliest anchor − {span} sessions, latest anchor]; anchors = alert decision session and, for linked winners, launch",
                        "rest": f"one /v2/aggs minute request per {AGG_LIMIT} base minutes at {EXT_MIN} minutes per session (upper bound)",
                        "flat_files": f"{mb} MB and {sec} s per day, measured once on 2026-08-12 (T-AH) — may differ today"}}

    # ⑥ fetch sizing — the larger atlas population (pivot-days of the three windows)
    rows = rd(ATLAS, "ca_rows.csv.gz")
    try:
        excl = frozenset(rn_lib.EXCLUDE)                                     # the four seeds and HUBC, as in the atlas
    except Exception:                                                        # noqa: BLE001
        excl = frozenset()
    inwin = [r for r in rows if r["sym"] not in excl and any(a <= r["t"] <= b for a, b in WINDOWS.values())]
    syms = {r["sym"] for r in inwin}
    i0 = max(0, idx[min(r["t"] for r in inwin)] - span) if inwin else 0
    i1 = idx[max(r["t"] for r in inwin)] if inwin else 0
    n_sess = i1 - i0 + 1
    out["fetch_atlas_population"] = {
        "pivot_days_in_windows": len(inwin), "symbols": len(syms), "first": sessions[i0], "last": sessions[i1],
        "sessions": n_sess, "rest_requests_upper_bound": len(syms) * math.ceil(n_sess * EXT_MIN / AGG_LIMIT),
        "flat_files_mb": (n_sess * mb) if mb else None, "flat_files_reduce_min": round(n_sess * sec / 60, 1) if sec else None,
        "excluded_symbols": sorted(excl), "eligible_events": v.get("eligible_events_all_windows")}
    return out


def render(c):
    d, u, f, g = c["definitions"], c["units"], c["fetch_alert_population"], c["fetch_atlas_population"]
    L = ["# Daily + 4H readiness — local coverage (generated)", "",
         "> Generated by `h4r_coverage.py` from local files only (no network, no vendor request, `fwd/` not read). "
         "Every number below is read from `data/coverage.json`.", "",
         "## 1. Event definitions (kept apart)", "",
         "| definition | linked events reaching +100% |", "|---|---|",
         f"| close from the trough reference (the A100 cohort) | {d['w100_close']} |",
         f"| regular-session high from the trough reference | {d['w100_high']} |",
         f"| both close and high | {d['close_and_high']} |",
         f"| any priced alert at +100% over the reference | {d['w100_alert_price']} |",
         f"| +100% after the first priced alert | {d['w100_after_alert']} |", "",
         f"- High but not close: {len(d['high_not_close'])} events. Alert price but not close: "
         f"{', '.join(d['alert_price_not_close']) or 'none'}. Close winners without +100% after the first priced alert: "
         f"{d['close_not_after_alert']['priced_alert_not_doubled']} (and {d['close_not_after_alert']['no_priced_alert']} "
         "with no priced alert, so this definition cannot be measured for them).",
         f"- Session of the best priced alert, for alert-price hits: "
         + " · ".join(f"{k} {v}" for k, v in sorted(d["alert_price_hit_by_session"].items())) + ".",
         f"- Linked +100% with a split near the window (listed apart): {d['split_near_linked_w100']} · +100% with no linked alert: "
         f"{d['unalerted_w100']}.",
         "- First-alert timing (cohort): " + " · ".join(f"{k} {v}" for k, v in sorted(c["timing"]["first_alert"].items())) + ".",
         "", "## 2. Analyzable units (alerted runs)", "",
         "| group | count |", "|---|---|",
         f"| runs | {u['runs']} |", f"| winners (all) | {u['winners']} |",
         f"| winners first alerted before the launch | {u['winners_pre_move']} |",
         f"| … with daily pivot-day features at t0 | {u['winners_pre_move_with_daily_features']} |",
         f"| controls | {u['controls']} |", f"| … with daily pivot-day features at t0 | {u['controls_with_daily_features']} |",
         ] + [f"| excluded: {k} | {v} |" for k, v in sorted(u["excluded_reasons"].items())] + [
         "", "Primary (pre-move winners and controls with daily features):", "",
         "| split | winners | controls |", "|---|---|---|"]
    for k in sorted(set(u["primary_by_month"]["winners"]) | set(u["primary_by_month"]["controls"])):
        L.append(f"| month {k} | {u['primary_by_month']['winners'].get(k, 0)} | {u['primary_by_month']['controls'].get(k, 0)} |")
    for k in sorted(set(u["primary_by_price"]["winners"]) | set(u["primary_by_price"]["controls"])):
        L.append(f"| price {k} | {u['primary_by_price']['winners'].get(k, 0)} | {u['primary_by_price']['controls'].get(k, 0)} |")
    for k in sorted(set(u["primary_by_list_at_t0"]["winners"]) | set(u["primary_by_list_at_t0"]["controls"])):
        L.append(f"| list at t0: {k} | {u['primary_by_list_at_t0']['winners'].get(k, 0)} | "
                 f"{u['primary_by_list_at_t0']['controls'].get(k, 0)} |")
    ct = u["chronological_thirds"]
    for k in range(3):
        L.append(f"| chronological third {k + 1} | {ct['winners'][k]} | {ct['controls'][k]} |")
    m = c["matching"]
    L += ["", f"- Thirds cut at {', '.join(ct['cuts'])} over {ct['decision_sessions']} decision sessions; every third has "
          f"fewer than {SMALL_N} winners: {u['thirds_below_small_n']}.",
          f"- Matching ({m['rule']}): controls per winner min/median/max {m['controls_per_winner_min_median_max']}; "
          f"winners with none: {m['winners_with_zero_controls']}.",
          "", "## 3. Four-hour and intraday data stored locally", "",
          f"- Atlas eligible events {c['local_intraday']['eligible_events_all_windows']}: with intraday OHLC "
          f"{c['local_intraday']['eligible_events_with_intraday_ohlc']}, with any intraday bar "
          f"{c['local_intraday']['eligible_events_with_any_intraday_bar']}; control rows with intraday OHLC "
          f"{c['local_intraday']['neg_rows_with_intraday_ohlc']} (one symbol).",
          f"- Alert-population units with 4H bars: {c['local_intraday']['alert_population_units_with_4h']}. "
          "Every 4H feature needs a fetch.",
          "", "## 4. What a fetch would need (estimates, not requests)", "",
          "| population | symbols | sessions | REST requests (upper bound) | flat files |", "|---|---|---|---|---|",
          f"| alerted runs (winners + controls) | {f['symbols']} | {f['distinct_sessions']} distinct · {f['symbol_sessions']} "
          f"symbol-sessions · {f['first']} → {f['last']} | {f['rest_requests_upper_bound']} | ≈{f['flat_files_mb']} MB · "
          f"≈{f['flat_files_reduce_min']} min to reduce |",
          f"| atlas pivot-days ({g['pivot_days_in_windows']} rows, {g['eligible_events']} eligible events) | {g['symbols']} | "
          f"{g['sessions']} · {g['first']} → {g['last']} | {g['rest_requests_upper_bound']} | ≈{g['flat_files_mb']} MB · "
          f"≈{g['flat_files_reduce_min']} min to reduce |", ""] + [f"- {k}: {v}." for k, v in f["assumptions"].items()]
    return "\n".join(L) + "\n"


def write(c, folder):
    os.makedirs(os.path.join(folder, "data"), exist_ok=True)
    with open(os.path.join(folder, "data", "coverage.json"), "w", encoding="utf-8") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(folder, "COVERAGE.md"), "w", encoding="utf-8") as fh:
        fh.write(render(c))


if __name__ == "__main__":
    cov = build()
    if "--check" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            write(cov, tmp)
            diff = [n for n in ("data/coverage.json", "COVERAGE.md")
                    if open(os.path.join(tmp, n), "rb").read() != open(os.path.join(HERE, n), "rb").read()]
        print("h4r_coverage --check:", "OK" if not diff else f"DIFFERS {diff}")
        sys.exit(1 if diff else 0)
    write(cov, HERE)
    print(json.dumps({k: cov[k] for k in ("units", "matching", "fetch_alert_population", "fetch_atlas_population")},
                     ensure_ascii=False, indent=1)[:4000])
