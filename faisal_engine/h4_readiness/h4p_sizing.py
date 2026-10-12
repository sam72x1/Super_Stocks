"""T-H4 protocol — per-unit data windows and the reduced fetch estimate (research · read-only · offline).
For every alerted run of the ALERTS100 population (winners and controls) it derives the exact sessions the pre-registered
4H features need (PROTOCOL.md §4), merges them per symbol and estimates the requests and the download for three routes.
No network connection is opened and no vendor is called; nothing under faisal_engine/readynow/fwd is read; no outcome is
cross-tabulated with any feature. Writes data/sizing.json and SIZING.md.
Run from the repo root:  python3 faisal_engine/h4_readiness/h4p_sizing.py   (--check: regenerate and compare)
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
CAL = os.path.join(ROOT, "faisal_engine", "readynow", "data", "calendar.json")
BARS = os.path.join(ROOT, "faisal_engine", "data", "rank", "bars.json.gz")
ARCHIVE = os.path.join(ROOT, "DECISIONS_ARCHIVE.md")

LOOK = 25            # PIVOT_LOOKBACK — the exact-low window (R4H-2)
RECENT = 5           # a sweep's reclaim must fall in the last 5 sessions up to the cutoff (R4H-8)
RECLAIM = 2          # the reclaim follows the sweep within 2 sessions (R4H-8)
PRIMARY_SPAN = LOOK + RECENT + RECLAIM - 1   # 31 sessions before the cutoff session ⇒ 32 sessions in all
WIN_FIRST = 10       # winners are also evaluated at T−10 … T−1 relative to the launch
EXT_MIN = 960        # 04:00–20:00 New York minutes per full extended session
BARS30 = 32          # 30-minute bars per full extended session
AGG_LIMIT = 50000    # `limit` passed to /v2/aggs; vendor documents it as the cap on base aggregates (unverified here)
EVAL_SHARE = 0.9     # a window is evaluable with bars on ≥ 90% of its sessions and on every one of the last 7
UPPER_BOUND = ("operator_entry", "pullback_monitor")   # streams whose alert time is the first commit (an upper bound)
PILOT_N = 20
PILOT_SPLIT = 2      # pilot also takes up to 2 symbols whose unit carries a reverse split in the 120 calendar days before t0
PILOT_SALT = "h4p-pilot"
CONTROL_WITNESS = "AAPL"
SAMPLE_BAR = {"v": 123456.0, "vw": 1.2345, "o": 1.23, "c": 1.24, "h": 1.25, "l": 1.22, "t": 1726000000000, "n": 1234}


def rd(name):
    with gzip.open(os.path.join(A100, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def flat_measure():
    txt = open(ARCHIVE, encoding="utf-8").read()
    m = re.search(r"يومُ `minute_aggs` ‏≈(\d+)MB", txt)
    return int(m.group(1)) if m else None


def ranges(ix):
    out = []
    for i in sorted(ix):
        if out and i == out[-1][1] + 1:
            out[-1][1] = i
        else:
            out.append([i, i])
    return out


def reqs_for(rs):
    return sum(math.ceil((b - a + 1) * EXT_MIN / AGG_LIMIT) for a, b in rs)


def build():
    sessions = json.load(open(CAL, encoding="utf-8"))["sessions"]
    idx = {d: i for i, d in enumerate(sessions)}
    bars = json.load(gzip.open(BARS, "rt", encoding="utf-8"))["daily"]
    units = [u for u in rd("units.csv.gz") if u["label"] in ("WIN", "CTRL")]
    launch = {r["event"]: r["launch"] for r in rd("cohort.csv.gz")}
    out = {"inputs": {n: hashlib.sha256(open(os.path.join(A100, n), "rb").read()).hexdigest()
                      for n in ("units.csv.gz", "cohort.csv.gz")},
           "params": {"LOOK": LOOK, "RECENT": RECENT, "RECLAIM": RECLAIM, "PRIMARY_SPAN": PRIMARY_SPAN,
                      "WIN_FIRST": WIN_FIRST, "EXT_MIN": EXT_MIN, "BARS30": BARS30, "AGG_LIMIT": AGG_LIMIT}}
    per_sym = collections.defaultdict(set)
    prim_only = collections.defaultdict(set)
    miss_cal, miss_daily = [], []
    groups, daily_ok = collections.Counter(), collections.Counter()
    moved = collections.Counter()
    for u in units:
        t0 = idx.get(u["t0"])
        if t0 is None:
            miss_cal.append(u["symbol"] + "|" + u["t0"])
            continue
        if u["first_stream"] in UPPER_BOUND and u["t0"] >= u["first_alert_date"]:
            # the alert time is only an upper bound (first commit carrying the stamp): the alert may precede the close of
            # its own date, so the safe cutoff is the close of the last session before that date (t0*)
            t0 = bisect.bisect_left(sessions, u["first_alert_date"]) - 1
            moved[(u["label"], u["pre_move"])] += 1
        prim = set(range(max(0, t0 - PRIMARY_SPAN), t0 + 1))
        sset = set(prim)
        if u["label"] == "WIN":
            li = idx.get(launch.get(u["event"], ""))
            if li is not None:
                sset |= set(range(max(0, li - WIN_FIRST - PRIMARY_SPAN), li))
        per_sym[u["symbol"]] |= sset
        prim_only[u["symbol"]] |= prim
        have = {r[0] for r in bars.get(u["symbol"], [])}
        if not all(sessions[i] in have for i in prim):
            miss_daily.append(u["symbol"] + "|" + u["t0"])
        share = sum(1 for i in prim if sessions[i] in have) / len(prim)
        recent_ok = all(sessions[i] in have for i in range(max(0, t0 - RECENT - RECLAIM + 1), t0 + 1))
        key = (u["label"], u["pre_move"])
        groups[key] += 1
        if share >= EVAL_SHARE and recent_ok:
            daily_ok[key] += 1
    last = sessions[-1]
    last_bar = {s: (bars[s][-1][0] if bars.get(s) else None) for s in per_sym}
    stale = sorted(s for s, d in last_bar.items() if d is None or d < last)

    def route(ps):
        rs = {s: ranges(ix) for s, ix in ps.items()}
        n_ranges = sum(len(v) for v in rs.values())
        symsess = sum(len(ix) for ix in ps.values())
        distinct = set().union(*ps.values()) if ps else set()
        bb = len(json.dumps(SAMPLE_BAR, separators=(",", ":"))) + 1
        return {"symbols": len(ps), "merged_ranges": n_ranges, "symbol_sessions": symsess,
                "distinct_sessions": len(distinct),
                "first": sessions[min(distinct)] if distinct else None, "last": sessions[max(distinct)] if distinct else None,
                "rest_requests_upper_bound": sum(reqs_for(v) for v in rs.values()),
                "rest30_mb_upper_bound": round(symsess * BARS30 * bb / 1e6, 1),
                "rest1_mb_upper_bound": round(symsess * EXT_MIN * bb / 1e6, 1),
                "flat_files_mb": (len(distinct) * flat_measure()) if flat_measure() else None,
                "bytes_per_bar_json": bb}
    full, prim_r = route(per_sym), route(prim_only)
    # pilot: deterministic by hash; DXST when present; up to 5 symbols whose local bars stop before the last session
    order = sorted(per_sym, key=lambda s: hashlib.sha256(f"{PILOT_SALT}|{s}".encode()).hexdigest())
    pilot = ["DXST"] if "DXST" in per_sym else []
    pilot += [s for s in order if s in stale and s not in pilot][:5]
    split_syms = {u["symbol"] for u in units if (u.get("split120") or "").strip() in ("1", "1.0")}
    pilot += [s for s in order if s in split_syms and s not in pilot][:PILOT_SPLIT]
    pilot += [s for s in order if s not in pilot][:PILOT_N - len(pilot)]
    pilot_ps = {s: per_sym[s] for s in pilot}
    p_req = sum(reqs_for(ranges(per_sym[s])) for s in pilot)
    span = set().union(*pilot_ps.values()) if pilot_ps else set()
    witness_req = reqs_for(ranges(span))
    out.update({
        "units": {"total": len(units), "by_label_pre_move": {f"{a}|pre_move={b}": n for (a, b), n in sorted(groups.items())},
                  "winner_events": len({u["event"] for u in units if u["label"] == "WIN"}),
                  "cutoff_moved_to_t0_star_by_label_pre_move": {f"{a}|pre_move={b}": n for (a, b), n in sorted(moved.items())},
                  "daily_evaluable_by_label_pre_move": {f"{a}|pre_move={b}": n for (a, b), n in sorted(daily_ok.items())},
                  "missing_calendar_t0": miss_cal, "primary_window_missing_local_daily": len(miss_daily),
                  "primary_window_missing_local_daily_list": sorted(miss_daily)},
        "symbols_local_bars_end_before_last_session": stale,
        "fetch_full": full, "fetch_primary_only": prim_r,
        "pilot": {"symbols": pilot, "stale_included": [s for s in pilot if s in stale],
                  "split_included": [s for s in pilot if s in split_syms],
                  "requests_symbols": p_req, "requests_witness": witness_req, "requests_minute_crosscheck": 3,
                  "requests_total": p_req + witness_req + 3,
                  "span": [sessions[min(span)], sessions[max(span)]] if span else None},
    })
    return out


def render(c):
    f, p, u, pl = c["fetch_full"], c["fetch_primary_only"], c["units"], c["pilot"]
    L = ["# T-H4 protocol — reduced fetch sizing (generated)", "",
         "> Generated by `h4p_sizing.py` from local files only (no network, no vendor request, `fwd/` not read, no outcome "
         "crossed with any feature). Every number is read from `data/sizing.json`.", "",
         "## Units", "", "| group | runs |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in u["by_label_pre_move"].items()]
    L += [f"| total | {u['total']} |", "", "Runs whose primary window is evaluable on local daily bars (bars on ≥ 90% of "
          "the 32 sessions and on each of the last 7):", "", "| group | runs |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in u["daily_evaluable_by_label_pre_move"].items()]
    L += ["", "Runs whose cutoff moves one session earlier to t0* (first alert from a stream whose time is an upper "
          "bound, dated on its own t0):", "", "| group | runs |", "|---|---|"]
    L += [f"| {k} | {v} |" for k, v in u["cutoff_moved_to_t0_star_by_label_pre_move"].items()]
    L += ["",
          f"- Distinct winner events: {u['winner_events']}. Runs whose t0 is not a calendar session: "
          f"{len(u['missing_calendar_t0'])}. Runs whose primary window lacks a local daily bar on some session: "
          f"{u['primary_window_missing_local_daily']}.",
          f"- Symbols whose local daily bars stop before the last session (possible delisting or renaming): "
          f"{len(c['symbols_local_bars_end_before_last_session'])}.",
          "", "## Windows (PROTOCOL.md §4)", "",
          f"- Every run: sessions [t0* − {c['params']['PRIMARY_SPAN']}, t0*] — {c['params']['LOOK']} for the exact low, "
          f"{c['params']['RECENT']} for the sweep's recency, {c['params']['RECLAIM']} for its reclaim.",
          f"- Winner runs also: [launch − {c['params']['WIN_FIRST'] + c['params']['PRIMARY_SPAN']}, launch − 1] "
          f"(evaluation at T−{c['params']['WIN_FIRST']} … T−1).",
          "", "## Estimates (upper bounds; nothing requested)", "",
          "| scope | symbols | merged ranges | symbol-sessions | distinct sessions | REST requests | 30-min download | "
          "1-min download | flat files |", "|---|---|---|---|---|---|---|---|---|",
          f"| primary + winner windows | {f['symbols']} | {f['merged_ranges']} | {f['symbol_sessions']} | "
          f"{f['distinct_sessions']} ({f['first']} → {f['last']}) | {f['rest_requests_upper_bound']} | "
          f"≤ {f['rest30_mb_upper_bound']} MB | ≤ {f['rest1_mb_upper_bound']} MB | ≈ {f['flat_files_mb']} MB |",
          f"| primary windows only | {p['symbols']} | {p['merged_ranges']} | {p['symbol_sessions']} | "
          f"{p['distinct_sessions']} ({p['first']} → {p['last']}) | {p['rest_requests_upper_bound']} | "
          f"≤ {p['rest30_mb_upper_bound']} MB | ≤ {p['rest1_mb_upper_bound']} MB | ≈ {p['flat_files_mb']} MB |", "",
          f"- One request per merged range per {c['params']['AGG_LIMIT']} base minutes at {c['params']['EXT_MIN']} minutes "
          f"per session; a full session of 30-minute bars is {c['params']['BARS30']} bars; JSON ≈ {f['bytes_per_bar_json']} "
          "bytes per bar (uncompressed). Thin stocks trade fewer minutes, so the real figures are lower.",
          "- Flat files are whole-market day files: their size depends on distinct sessions, not on how many symbols are used.",
          "", "## Pilot (PROTOCOL.md §7)", "",
          f"- Symbols ({len(pl['symbols'])}): {', '.join(pl['symbols'])}; with local bars ending early: "
          f"{', '.join(pl['stale_included']) or 'none'}; with a reverse split in the 120 calendar days before t0 (`split120`): "
          f"{', '.join(pl['split_included']) or 'none'}.",
          f"- Requests: symbols {pl['requests_symbols']} + witness {CONTROL_WITNESS} {pl['requests_witness']} + one-minute "
          f"cross-check {pl['requests_minute_crosscheck']} = **{pl['requests_total']}**; span {pl['span'][0]} → {pl['span'][1]}."]
    return "\n".join(L) + "\n"


def write(c, folder):
    os.makedirs(os.path.join(folder, "data"), exist_ok=True)
    with open(os.path.join(folder, "data", "sizing.json"), "w", encoding="utf-8") as fh:
        json.dump(c, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    with open(os.path.join(folder, "SIZING.md"), "w", encoding="utf-8") as fh:
        fh.write(render(c))


if __name__ == "__main__":
    s = build()
    if "--check" in sys.argv:
        with tempfile.TemporaryDirectory() as tmp:
            write(s, tmp)
            diff = [n for n in ("data/sizing.json", "SIZING.md")
                    if open(os.path.join(tmp, n), "rb").read() != open(os.path.join(HERE, n), "rb").read()]
        print("h4p_sizing --check:", "OK" if not diff else f"DIFFERS {diff}")
        sys.exit(1 if diff else 0)
    write(s, HERE)
    print(open(os.path.join(HERE, "SIZING.md"), encoding="utf-8").read())
