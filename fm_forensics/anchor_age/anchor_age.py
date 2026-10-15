"""T-ANCHOR-AGE · measurement (research only · read-only · no network · no production state · definitions: ANCHOR_AGE_DEFS.md).

Inputs (all committed): data/snapshots.json.gz (anchor_extract.py · git history) · data/anchor_bars.json.gz (anchor_fetch.py on a runner ·
TradingView regular session adjustment=splits through Super_stock.tv_download) · fm_forensics/gen5/data/gen5_generation_days.csv (the five's
windows, by name). Production functions are called by name: Super_stock.pivot_stability · tested_level · entry_status (via the extracted
verdict) — through gen5_features.S() (the GEN5 import with the live FAISAL_ONLY constants).

  python3 fm_forensics/anchor_age/anchor_age.py            write data/anchor_result.json and ANCHOR_AGE_TABLES.md
  python3 fm_forensics/anchor_age/anchor_age.py --check    rebuild in memory, compare both outputs byte for byte, and check that
                                                           ANCHOR_AGE_RESULT.md carries the JSON's numbers (doc_check)
  python3 fm_forensics/anchor_age/anchor_age.py --guards   synthetic guards (no data read)

Exit codes: 0 done · 1 guards failed or outputs differ.
"""
import bisect
import collections
import csv
import datetime as dt
import gzip
import json
import math
import os
import statistics
import sys
from zoneinfo import ZoneInfo

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "gen5"))
SNAP = os.path.join(HERE, "data", "snapshots.json.gz")
BARS = os.path.join(HERE, "data", "anchor_bars.json.gz")
GEN5_DAYS = os.path.join(ROOT, "fm_forensics", "gen5", "data", "gen5_generation_days.csv")
OUT_JSON = os.path.join(HERE, "data", "anchor_result.json")
OUT_MD = os.path.join(HERE, "ANCHOR_AGE_TABLES.md")
NY = ZoneInfo("America/New_York")
FIVE = ("SXTC", "DKI", "RETO", "DLXY", "HUBC")
BINS = ((0, 2, "0-2"), (3, 8, "3-8"), (9, 15, "9-15"), (16, 25, "16-25"), (26, 10 ** 6, "26+"))
STEP, N_TR, FAR_MULT, RECLAIM = 0.03, 3, 1.05, 0.995      # production: ENTRY_STEP_PCT · ENTRY_TRANCHES · :10961 · :10959
K_OK, K_SPLIT = 0.03, math.log(1.5)
TOUCH_TOL, TOUCH_LOOK = 0.005, 60
MIN_BARS = 30


# ── pure helpers ────────────────────────────────────────────────────────────────────────────────────
def bin_of(n):
    if n is None:
        return None
    for lo, hi, name in BINS:
        if lo <= n <= hi:
            return name
    return None


def k_flag(k):
    """Stored last_price ÷ bar close at s: 'ok' within 3% · 'split' beyond a ×1.5 ratio (a split after s) · else 'mismatch'."""
    if k is None or not (k > 0):
        return "unknown"
    if abs(k - 1.0) <= K_OK + 1e-12:              # closed bound (float noise at exactly 3%)
        return "ok"
    if abs(math.log(k)) >= K_SPLIT:
        return "split"
    return "mismatch"


def prod_category(status, reason):
    if status == "ready_now":
        return "ready"
    r = reason or ""
    if "كسر الوقف" in r:
        return "stop"
    if "تحت الدعم" in r:
        return "reclaim"
    if "بعيد" in r:
        return "far"
    if "فوق نطاق الدفعات" in r:
        return "above_band"
    if "بيانات" in r or "سعر" in r:
        return "stale"
    return "other"


def zone_status(price, anchor, stop=None, pivot=None, tol_pct=0.0):
    """The production entry formulas (entry_mode :10957-:10965 then entry_status :15372-:15386) on one anchor.
    zone = anchor × (1, 1.03, 1.06) · stop defaults to the anchor (PIVOT_STOP_AT_LOW) · pivot defaults to the anchor."""
    if price is None or anchor is None or not (anchor > 0):
        return None
    stop = anchor if stop is None else stop
    pivot = anchor if pivot is None else pivot
    hi = anchor * (1 + STEP * (N_TR - 1))
    if stop and price <= stop:
        return "stop"
    if price < pivot * RECLAIM:
        return "reclaim"
    if price > hi * FAR_MULT:
        return "far"
    if price > hi * (1 + tol_pct / 100.0):
        return "above_band"
    return "ready"


def touch_age(lows, level):
    """Sessions since the most recent bar whose low is within 0.5% of `level` in the last 60 bars (None if none)."""
    if level is None or not (level > 0):
        return None
    n = len(lows)
    for j in range(n - 1, max(-1, n - 1 - TOUCH_LOOK), -1):
        if abs(lows[j] / level - 1.0) <= TOUCH_TOL:
            return n - 1 - j
    return None


def q(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    def p(f):
        k = (len(xs) - 1) * f
        i = int(math.floor(k))
        j = min(i + 1, len(xs) - 1)
        return xs[i] + (xs[j] - xs[i]) * (k - i)
    return {"n": len(xs), "median": round(statistics.median(xs), 2), "q3": round(p(0.75), 2), "max": round(xs[-1], 2),
            "min": round(xs[0], 2)}


def close_utc(day):
    import market_calendar as MC
    info = MC.session_info(day)
    m = info.get("close_ny_min") or 16 * 60
    d = dt.date.fromisoformat(day)
    return dt.datetime(d.year, d.month, d.day, m // 60, m % 60, tzinfo=NY).astimezone(dt.timezone.utc)


def decision_session(sessions, closes_utc, t):
    """Last session whose close is at or before t (bars [..s] only)."""
    k = bisect.bisect_right(closes_utc, t) - 1
    return sessions[k] if k >= 0 else None


# ── data ────────────────────────────────────────────────────────────────────────────────────────────
def load():
    snap = json.load(gzip.open(SNAP, "rt", encoding="utf-8"))
    bars = json.load(gzip.open(BARS, "rt", encoding="utf-8"))
    return snap, bars


def frames(bars):
    import pandas as pd
    out = {}
    for sym, rows in bars["daily"].items():
        if not rows:
            continue
        df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        df.index = pd.to_datetime(df["Date"])
        out[sym] = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return out


def calendar(dfs):
    cnt = collections.Counter()
    for df in dfs.values():
        cnt.update(df.index.strftime("%Y-%m-%d"))
    sess = sorted(d for d, n in cnt.items() if n >= 0.5 * len(dfs))
    return sess, [close_utc(d) for d in sess]


def features(S, df, s):
    """Everything from bars [..s] only. None when fewer than 30 bars."""
    x = df[df.index <= s]
    if len(x) < MIN_BARS:
        return None
    lows = x["Low"].values.astype(float)
    closes = x["Close"].values.astype(float)
    ps = S.pivot_stability(lows, closes)
    tl = S.tested_level(x)
    return {"close": float(closes[-1]), "pivot25": (ps or {}).get("pivot"), "bars_after": (ps or {}).get("bars_after"),
            "tested": (tl or {}).get("level"), "touches": (tl or {}).get("touches"), "m5": float(lows[-5:].min()),
            "last_bar": x.index[-1].strftime("%Y-%m-%d"), "lows": lows}


# ── measurement ─────────────────────────────────────────────────────────────────────────────────────
def measure():
    import gen5_features as G
    S = G.S()
    snap, bars = load()
    dfs = frames(bars)
    sess, cu = calendar(dfs)
    rows, missing = [], collections.Counter()
    episodes = {}
    cache = {}

    def feat(sym, s):
        key = (sym, s)
        if key not in cache:
            df = dfs.get(sym)
            cache[key] = None if df is None or s is None else features(S, df, s)
        return cache[key]

    for snapx in snap["watch"]:
        t = dt.datetime.fromisoformat(snapx["utc"])
        s = decision_session(sess, cu, t)
        era = "R2" if "anchorb2" in (snapx.get("logic_version") or "") else "R1"
        day = t.date().isoformat()
        for r in snapx["stocks"]:
            sym = r["symbol"]
            trs = [float(v) for v in (r.get("tranches") or []) if v]
            ep_key = (sym, tuple(round(v, 4) for v in trs))
            prev = episodes.get(sym)
            if prev is None or prev["key"] != ep_key:          # a new zone (first sight, selection, migration, renewal) = a new episode
                episodes[sym] = {"key": ep_key, "build_day": day, "build_s": s}
            ep = episodes[sym]
            f = feat(sym, s)
            cat = prod_category((r.get("prod") or {}).get("status"), (r.get("prod") or {}).get("reason"))
            row = {"sym": sym, "day": day, "s": s, "era": era, "prod": cat, "stored_bars_after": r.get("bars_after"),
                   "build_day": ep["build_day"], "build_s": ep["build_s"], "price_state": r.get("price_state")}
            if f is None or not trs or not r.get("last_price"):
                row["unknown"] = "no_bars" if f is None else "no_record_fields"
                missing[row["unknown"]] += 1
                rows.append(row)
                continue
            k = float(r["last_price"]) / f["close"] if f["close"] > 0 else None
            kf = k_flag(k)
            A = trs[0] / k if k else None
            P = float(r["pivot"]) / k if (k and r.get("pivot")) else None
            st = r.get("stop")
            stop = (float(st[0]) if isinstance(st, (list, tuple)) and st else (float(st) if isinstance(st, (int, float)) else None))
            stop = stop / k if (k and stop) else None
            fb = feat(sym, ep["build_s"])
            row.update({
                "k": round(k, 4) if k else None, "k_flag": kf, "close": round(f["close"], 4), "anchor": round(A, 4) if A else None,
                "pivot_stored": round(P, 4) if P else None, "pivot25": f["pivot25"], "bars_after": f["bars_after"],
                "tested": f["tested"], "m5": f["m5"],
                "anchor_age": touch_age(f["lows"], A),
                "gap_anchor": round((f["m5"] / A - 1) * 100, 2) if A else None,
                "gap_pivot25": round((f["m5"] / f["pivot25"] - 1) * 100, 2) if f["pivot25"] else None,
                "recomputed": zone_status(f["close"], A, stop=stop, pivot=P),
                "build_bars_after": fb["bars_after"] if fb else None,
                "build_anchor_age": touch_age(fb["lows"], A) if fb else None,
                "m5_build": fb["m5"] if fb else None,
                "shadow_build": zone_status(f["close"], fb["m5"]) if fb else None,
                "shadow_roll": zone_status(f["close"], f["m5"]),
            })
            rows.append(row)
    return {"rows": rows, "missing": dict(missing), "near": near_rows(snap, dfs, sess, cu, feat),
            "five": five_rows(snap, dfs, sess, cu, feat), "anpa": anpa(snap, feat),
            "meta": {"snap_head": snap["meta"]["head"], "bars_utc": bars["meta"]["utc"], "bars_got": bars["meta"]["got"],
                     "bars_asked": bars["meta"]["asked"], "sessions": [sess[0], sess[-1]]}}


def near_rows(snap, dfs, sess, cu, feat):
    out = []
    for run in snap["near"]:
        t = dt.datetime.fromisoformat(run["utc"])
        s = decision_session(sess, cu, t)
        for sym, price in sorted(run["rows"].items()):
            f = feat(sym, s)
            if f is None:
                out.append({"sym": sym, "run": run["run_date"], "s": s, "unknown": "no_bars"})
                continue
            out.append({"sym": sym, "run": run["run_date"], "s": s, "bars_after": f["bars_after"], "tested": f["tested"],
                        "gap_pivot25": round((f["m5"] / f["pivot25"] - 1) * 100, 2) if f["pivot25"] else None})
    return out


def _wall_session(day, sess):
    """A wall dated D belongs to the last closed session before D (the run is before the open)."""
    k = bisect.bisect_left(sess, day) - 1
    return sess[k] if k >= 0 else None


def five_rows(snap, dfs, sess, cu, feat):
    win = collections.defaultdict(list)
    with open(GEN5_DAYS, encoding="utf-8") as f:
        for r in csv.DictReader(f):
            win[(r["sym"], r["event"])].append(r["t"])
    walls_by_s = {}
    for D, m in snap["walls"].items():
        s = _wall_session(D, sess)
        if s:
            walls_by_s.setdefault(s, {}).update(m)
    listed = collections.defaultdict(dict)
    for x in snap["watch"]:
        s = decision_session(sess, cu, dt.datetime.fromisoformat(x["utc"]))
        for r in x["stocks"]:
            listed[r["symbol"]][s] = r
    near = collections.defaultdict(set)
    for run in snap["near"]:
        s = decision_session(sess, cu, dt.datetime.fromisoformat(run["utc"]))
        for sym in run["rows"]:
            near[sym].add(s)
    out = []
    for (sym, ev), ts in sorted(win.items()):
        for t in sorted(set(ts)):
            f = feat(sym, t)
            rec = listed[sym].get(t)
            row = {"sym": sym, "event": ev, "t": t, "listed": rec is not None, "near": t in near[sym],
                   "wall": (walls_by_s.get(t) or {}).get(sym)}
            if f:
                row.update({"pivot25": f["pivot25"], "bars_after": f["bars_after"], "tested": f["tested"], "m5": f["m5"],
                            "gap_pivot25": round((f["m5"] / f["pivot25"] - 1) * 100, 2) if f["pivot25"] else None,
                            "close": round(f["close"], 4)})
            if rec:
                row["prod"] = prod_category((rec.get("prod") or {}).get("status"), (rec.get("prod") or {}).get("reason"))
            out.append(row)
    return out


def anpa(snap, feat):
    out = []
    for s in ("2026-10-09", "2026-10-12", "2026-10-13", "2026-10-14"):
        f = feat("ANPA", s)
        if not f:
            continue
        out.append({"s": s, "close": f["close"], "pivot25": f["pivot25"], "bars_after": f["bars_after"], "tested": f["tested"],
                    "touches": f["touches"], "m5": f["m5"],
                    "gap_to_1858": round((1.858 / f["m5"] - 1) * 100, 2), "depth_from_1858_to_m5": round((1 - f["m5"] / 1.858) * 100, 2)})
    walls = {D: m.get("ANPA") for D, m in snap["walls"].items() if m.get("ANPA")}
    nw = [{"run": r["run_date"], "price": r["rows"]["ANPA"]} for r in snap["near"] if "ANPA" in r["rows"]]
    return {"rows": out, "walls": walls, "near": nw}


# ── summaries ───────────────────────────────────────────────────────────────────────────────────────
def summarize(m):
    rows = m["rows"]
    res = {"meta": m["meta"], "missing": m["missing"]}
    for era in ("R2", "R1"):
        R = [r for r in rows if r["era"] == era and "unknown" not in r]
        Rall = [r for r in rows if r["era"] == era]
        builds = {}
        for r in R:
            builds.setdefault((r["sym"], r["build_day"]), r)
        B = list(builds.values())

        def dist(xs, field):
            c = collections.Counter(bin_of(x.get(field)) for x in xs)
            n = sum(v for k, v in c.items() if k)
            return {"n": n, "unknown": c.get(None, 0),
                    "bins": {name: c.get(name, 0) for _, _, name in BINS},
                    "pct": {name: (round(100 * c.get(name, 0) / n, 1) if n else None) for _, _, name in BINS},
                    "over8_pct": round(100 * sum(c.get(nm, 0) for _, _, nm in BINS[2:]) / n, 1) if n else None}
        gaps = {}
        for _, _, name in BINS:
            sub = [r for r in R if bin_of(r.get("bars_after")) == name]
            gaps[name] = {"gap_anchor": q([r.get("gap_anchor") for r in sub]), "gap_pivot25": q([r.get("gap_pivot25") for r in sub])}
        build_gaps = {}
        for _, _, name in BINS:
            sub = [r for r in B if bin_of(r.get("build_bars_after")) == name]
            build_gaps[name] = q([(r["m5_build"] / r["anchor"] - 1) * 100 if r.get("m5_build") and r.get("anchor") else None
                                  for r in sub])
        prod = collections.Counter(r["prod"] for r in Rall)
        over8 = [r for r in R if (r.get("bars_after") or 0) > 8]
        watch8 = [r for r in over8 if r["prod"] != "ready"]
        far8 = [r for r in over8 if r["prod"] == "far"]

        def flips(xs, key):
            return {"days": sum(r.get(key) == "ready" for r in xs), "of": len(xs),
                    "symbols": len({r["sym"] for r in xs if r.get(key) == "ready"}), "of_symbols": len({r["sym"] for r in xs})}
        agree = [r for r in R if r.get("recomputed")]
        pv = [r for r in R if r.get("k_flag") == "ok" and r.get("pivot_stored") and r.get("pivot25")]
        res[era] = {
            "stock_days": len(Rall), "known": len(R), "symbols": len({r["sym"] for r in Rall}), "episodes": len(B),
            "snap_days": len({r["day"] for r in Rall}),
            # display check (not a decision): the stored pivot vs today's 25-session low, k-consistent rows only, tolerance = K_OK
            "pivot_vs_today": {"n": len(pv), "differ": sum(abs(r["pivot_stored"] / r["pivot25"] - 1) > K_OK for r in pv),
                               "tol_pct": round(100 * K_OK, 2)},
            "k_flags": dict(collections.Counter(r.get("k_flag") for r in R)),
            "bars_after_daily": dist(R, "bars_after"), "bars_after_build": dist(B, "build_bars_after"),
            "anchor_age_daily": dist(R, "anchor_age"), "anchor_age_build": dist(B, "build_anchor_age"),
            "gaps_daily": gaps, "gaps_build_anchor": build_gaps,
            "prod": dict(prod),
            "recomputed_agree": {"n": len(agree), "same": sum((r["recomputed"] == r["prod"]) or (r["recomputed"] in ("far", "above_band")
                                                                  and r["prod"] in ("far", "above_band")) for r in agree)},
            "over8": {"days": len(over8), "symbols": len({r["sym"] for r in over8}),
                      "prod": dict(collections.Counter(r["prod"] for r in over8)),
                      "watch_flip_build": flips(watch8, "shadow_build"), "watch_flip_roll": flips(watch8, "shadow_roll"),
                      "far_flip_build": flips(far8, "shadow_build"), "far_flip_roll": flips(far8, "shadow_roll")},
            "all_watch": {"flip_build": flips([r for r in R if r["prod"] != "ready"], "shadow_build"),
                          "flip_roll": flips([r for r in R if r["prod"] != "ready"], "shadow_roll"),
                          "ready_lost_build": flips([r for r in R if r["prod"] == "ready"], "shadow_build"),
                          "ready_lost_roll": flips([r for r in R if r["prod"] == "ready"], "shadow_roll")},
            "far_by_build_age": {name: dict(collections.Counter(r["prod"] for r in R if bin_of(r.get("build_bars_after")) == name))
                                 for _, _, name in BINS},
            "far_share_by_build_age": {name: _share([r["prod"] for r in R if bin_of(r.get("build_bars_after")) == name], "far")
                                       for _, _, name in BINS},
            "ready_share_by_build_age": {name: _share([r["prod"] for r in R if bin_of(r.get("build_bars_after")) == name], "ready")
                                         for _, _, name in BINS},
            "build_day": {name: {"price_over_anchor": q([(r["close"] / r["anchor"] - 1) * 100 for r in B
                                                         if bin_of(r.get("build_bars_after")) == name and r.get("anchor")]),
                                 "price_over_m5": q([(r["close"] / r["m5_build"] - 1) * 100 for r in B
                                                     if bin_of(r.get("build_bars_after")) == name and r.get("m5_build")]),
                                 "prod": dict(collections.Counter(r["prod"] for r in B if bin_of(r.get("build_bars_after")) == name))}
                          for _, _, name in BINS},
            "days_since_build_far": q([_sess_between(r["build_s"], r["s"]) for r in R if r["prod"] == "far"]),
            "days_since_build_ready": q([_sess_between(r["build_s"], r["s"]) for r in R if r["prod"] == "ready"]),
            "rise_since_build_far": q([(r["close"] / r["m5_build"] - 1) * 100 if r.get("m5_build") else None
                                      for r in R if r["prod"] == "far"]),
            "anchor_vs_m5build": q([(r["m5_build"] / r["anchor"] - 1) * 100 if r.get("m5_build") and r.get("anchor") else None for r in B]),
            "gap_build_over8_pooled": q([(r["m5_build"] / r["anchor"] - 1) * 100 if r.get("m5_build") and r.get("anchor") else None
                                         for r in B if (r.get("build_bars_after") or 0) > 8]),
        }
    n = m["near"]
    nk = [r for r in n if "unknown" not in r]
    c = collections.Counter(bin_of(r.get("bars_after")) for r in nk)
    tot = sum(v for k, v in c.items() if k)
    res["near"] = {"rows": len(n), "known": len(nk), "symbols": len({r["sym"] for r in n}),
                   "bins": {name: c.get(name, 0) for _, _, name in BINS},
                   "over8_pct": round(100 * sum(c.get(nm, 0) for _, _, nm in BINS[2:]) / tot, 1) if tot else None,
                   "no_tested": sum(r.get("tested") is None for r in nk),
                   "gap_pivot25": q([r.get("gap_pivot25") for r in nk])}
    res["five"] = m["five"]
    res["anpa"] = m["anpa"]
    res["verdict"] = verdict(res["R2"])
    return res


_SESS = []


def _share(xs, what):
    return {"n": len(xs), "k": sum(x == what for x in xs), "pct": round(100 * sum(x == what for x in xs) / len(xs), 1) if xs else None}


def _sess_between(a, b):
    if not _SESS or a is None or b is None:
        return None
    return bisect.bisect_left(_SESS, b) - bisect.bisect_left(_SESS, a)


def verdict(r2):
    """ANCHOR_AGE_DEFS.md §④ — fixed before the numbers. (d) the five is read from the five's table by hand-free rule:
    a five-row counts only if it was LISTED on that session (an old anchor can only silence a listed stock)."""
    a = r2["bars_after_build"]["over8_pct"]
    pooled = r2.get("gap_build_over8_pooled")        # §④ (ب): the median of the pooled over-8 build rows — as written
    b_med = pooled["median"] if pooled else None
    wf = r2["over8"]["watch_flip_build"]
    c_share = round(100 * wf["days"] / wf["of"], 1) if wf["of"] else None
    out = {"a_over8_build_pct": a, "b_gap_median_over8_build": b_med, "c_flip_share_pct": c_share}
    if a is None:
        out["verdict"] = "no_measure"
    elif a < 25:
        out["verdict"] = "dropped"
    elif a >= 50 and (b_med or 0) >= 5 and (c_share or 0) >= 25:
        out["verdict"] = "candidate_defect_needs_five"
    else:
        out["verdict"] = "present_no_explanatory_effect"
    return out


# ── rendering ───────────────────────────────────────────────────────────────────────────────────────
def _row(cells):
    return "| " + " | ".join("—" if c is None else str(c) for c in cells) + " |"


def render(res):
    L = ["# `T-ANCHOR-AGE` — الجداول (مولَّدةٌ من `data/anchor_result.json` بـ`anchor_age.py` · لا تُحرَّر باليد)", ""]
    me = res["meta"]
    L += [f"الشموع: TradingView `adjustment=splits` عبر `Super_stock.tv_download` · جُلبت {me['bars_got']} من {me['bars_asked']} · "
          f"جلساتٌ {me['sessions'][0]} ⟶ {me['sessions'][1]} · لقطاتُ القائمة من `{me['snap_head'][:9]}` · مجهول: {res['missing']}", ""]
    for era, title in (("R2", "R2 — منذ اعتماد المِرساة المُختبَرة (`anchorb2` · 2026-08-14) — الإنتاجُ اليوم"),
                       ("R1", "R1 — قبلها (المِرساة `pivot`) — للسياق")):
        e = res[era]
        L += [f"## {title}", "",
              f"أيّامُ سهم {e['stock_days']} (معلومةٌ {e['known']}) · رموز {e['symbols']} · نطاقاتٌ مبنيّة {e['episodes']} · أيّامُ لقطة {e['snap_days']} · معاملُ المقياس {e['k_flags']}",
              f"عرضٌ لا قرار: `pivot` المخزَّن يخالف قاعَ الـ25 اليوم (تسامح {e['pivot_vs_today']['tol_pct']}% = تسامحُ `k`) في "
              f"{e['pivot_vs_today']['differ']} من {e['pivot_vs_today']['n']} يومًا متّسقَ المعامل", ""]
        L += ["### ① `bars_after` (‏`pivot_stability` على `[..s]`)", "", "| اللحظة | n | 0-2 | 3-8 | 9-15 | 16-25 | 26+ | فوق 8 % |", "|---|---|---|---|---|---|---|---|"]
        for key, name in (("bars_after_build", "يومَ بناء النطاق"), ("bars_after_daily", "كلَّ يومٍ نشط"),
                          ("anchor_age_build", "عمرُ المِرساة المستعملة يومَ البناء (آخرُ لمسة)"), ("anchor_age_daily", "عمرُ المِرساة المستعملة كلَّ يوم")):
            d = e[key]
            L.append(_row([name, d["n"]] + [f"{d['bins'][nm]} ({d['pct'][nm]}%)" for _, _, nm in BINS] + [d["over8_pct"]]))
        L += ["", "### ② الفارقُ عن قاع الخمس جلسات `m5` (‏`(m5 − A) ÷ A`)", "",
              "| `bars_after` | n | المِرساة المستعملة: وسيط · ربعٌ أعلى · أقصى | `pivot` (25): وسيط · ربعٌ أعلى · أقصى |", "|---|---|---|---|"]
        for _, _, nm in BINS:
            g = e["gaps_daily"][nm]
            ga, gp = g["gap_anchor"], g["gap_pivot25"]
            L.append(_row([nm, (ga or {}).get("n"), f"{ga['median']} · {ga['q3']} · {ga['max']}" if ga else None,
                           f"{gp['median']} · {gp['q3']} · {gp['max']}" if gp else None]))
        L += ["", f"**وفوق 8 يومَ البناء مجمَّعًا** (معيارُ §④-ب): {e['gap_build_over8_pooled']}", ""]
        L += ["يومَ بناء النطاق (`m5` يومَها مقابل المِرساة المستعملة): " +
              " · ".join(f"{nm}: {g['median']}% (n {g['n']})" for nm, g in e["gaps_build_anchor"].items() if g), ""]
        L += ["### ③ حالةُ الدخول (الإنتاج) والظلّ", "", f"الإنتاج على أيّام السهم: {e['prod']} · وإعادةُ الحساب بالصيغ تطابق المخزَّن في "
              f"{e['recomputed_agree']['same']} من {e['recomputed_agree']['n']}", ""]
        o = e["over8"]
        L += [f"**`bars_after` فوق 8:** {o['days']} يومًا · {o['symbols']} رمزًا · الإنتاج {o['prod']}", "",
              "| الظلّ | من «متابعة» (كلّ الأسباب) صار «جاهز» | من «بعيد» صار «جاهز» |", "|---|---|---|"]
        for lab, kb, kf in (("ظلّ-البناء (`m5` يومَ البناء مجمَّدًا)", "watch_flip_build", "far_flip_build"),
                            ("ظلّ-اليوم (`m5` كلَّ يوم)", "watch_flip_roll", "far_flip_roll")):
            a, b = o[kb], o[kf]
            L.append(_row([lab, f"{a['days']} من {a['of']} يومًا · {a['symbols']} من {a['of_symbols']} رمزًا",
                           f"{b['days']} من {b['of']} يومًا · {b['symbols']} من {b['of_symbols']} رمزًا"]))
        w = e["all_watch"]
        L += ["", f"**وعلى كلّ الأيّام:** «متابعة» ⟵ «جاهز» بظلّ-البناء {w['flip_build']['days']} من {w['flip_build']['of']} · "
              f"بظلّ-اليوم {w['flip_roll']['days']} من {w['flip_roll']['of']} · و«جاهز» الإنتاج يبقى «جاهز» بظلّ-البناء "
              f"{w['ready_lost_build']['days']} من {w['ready_lost_build']['of']} · بظلّ-اليوم {w['ready_lost_roll']['days']} من {w['ready_lost_roll']['of']}", ""]
        L += ["**حصّةُ «بعيد» و«جاهز» من أيّام النطاق بعمر قاعه يومَ البناء:** " + " · ".join(
            f"{nm}: بعيد {e['far_share_by_build_age'][nm]['pct']}% · جاهز {e['ready_share_by_build_age'][nm]['pct']}% (n {e['far_share_by_build_age'][nm]['n']})"
            for _, _, nm in BINS if e["far_share_by_build_age"][nm]["n"]), ""]
        L += ["**يومَ البناء نفسَه** (السعرُ فوق المِرساة · فوق `m5` · وحالةُ الإنتاج):", ""]
        for _, _, nm in BINS:
            bd = e["build_day"][nm]
            if bd["price_over_anchor"]:
                L.append(f"- {nm}: فوق المِرساة وسيطُه {bd['price_over_anchor']['median']}% (ربعٌ أعلى {bd['price_over_anchor']['q3']}) · "
                         f"فوق `m5` {bd['price_over_m5']['median'] if bd['price_over_m5'] else '—'}% · الحالة {bd['prod']}")
        L += [""]
        L += [f"**«بعيد» بعمر القاع يومَ البناء:** " + " · ".join(f"{nm}: {v}" for nm, v in e["far_by_build_age"].items() if v), "",
              f"**جلساتٌ منذ البناء:** «بعيد» {e['days_since_build_far']} · «جاهز» {e['days_since_build_ready']}", "",
              f"**صعودُ السعر عن `m5` يومَ البناء في أيّام «بعيد»:** {e['rise_since_build_far']} · **و`m5` يومَ البناء فوق المِرساة:** {e['anchor_vs_m5build']}", ""]
    n = res["near"]
    L += ["## «تحت المتابعة» (`near_watch.json`) — وصفُ العمر والفارق وحدَه", "",
          f"صفوف {n['rows']} (معلومة {n['known']}) · رموز {n['symbols']} · `bars_after` {n['bins']} · فوق 8: {n['over8_pct']}% · "
          f"بلا مستوًى مُختبَر {n['no_tested']} · الفارق `m5` عن `pivot` {n['gap_pivot25']}", ""]
    L += ["## الخمسة (نوافذُ GEN5 بالاسم)", "", "| الرمز | الحدث | الجلسة | في القائمة | تحت المتابعة | الجدار | `pivot` | `bars_after` | `m5` | الفارق % | الإنتاج |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for r in res["five"]:
        L.append(_row([r["sym"], r["event"], r["t"], "نعم" if r["listed"] else "لا", "نعم" if r["near"] else "لا", r.get("wall"),
                       r.get("pivot25"), r.get("bars_after"), r.get("m5"), r.get("gap_pivot25"), r.get("prod")]))
    a = res["anpa"]
    L += ["", "## ANPA", "", "| الجلسة | الإغلاق | `pivot` | `bars_after` | `tested_level` | لمسات | `m5` | 1.858 فوق `m5` % | العمق من 1.858 إلى `m5` % |",
          "|---|---|---|---|---|---|---|---|---|"]
    for r in a["rows"]:
        L.append(_row([r["s"], r["close"], r["pivot25"], r["bars_after"], r["tested"], r["touches"], r["m5"], r["gap_to_1858"], r["depth_from_1858_to_m5"]]))
    L += ["", f"الجدار: {a['walls']} · «تحت المتابعة»: {a['near']}", "", "## الحكم (‏`ANCHOR_AGE_DEFS.md §④`)", "",
          "```json", json.dumps(res["verdict"], ensure_ascii=False, indent=1, sort_keys=True), "```", ""]
    return "\n".join(L)


def outputs():
    global _SESS
    m = measure()
    import gen5_features  # noqa: F401
    snap, bars = load()
    _SESS = calendar(frames(bars))[0]
    res = summarize(m)
    return {OUT_JSON: json.dumps(res, ensure_ascii=False, indent=1, sort_keys=True) + "\n", OUT_MD: render(res) + "\n"}


# ── guards ──────────────────────────────────────────────────────────────────────────────────────────
def guards():
    ok = []

    def g(name, cond, why=""):
        ok.append(bool(cond))
        print(("✅ " if cond else "❌ ") + name + ("" if cond else f" — {why}"))
    g("AG1 الفئات: 0-2 · 3-8 · 9-15 · 16-25 · 26+ وحدودُها مغلقة",
      [bin_of(x) for x in (0, 2, 3, 8, 9, 15, 16, 25, 26, None)] == ["0-2", "0-2", "3-8", "3-8", "9-15", "9-15", "16-25", "16-25", "26+", None])
    g("AG2 صيغُ الإنتاج على مِرساةٍ واحدة: وقف ⟵ تحت الدعم ⟵ بعيد (×1.05 فوق أعلى دفعة) ⟵ فوق النطاق ⟵ جاهز",
      [zone_status(p, 1.0) for p in (1.0, 0.99, 1.115, 1.12, 1.07, 1.06, 1.03)]
      == ["stop", "stop", "far", "far", "above_band", "ready", "ready"]
      and zone_status(1.0, 1.0, stop=0.9, pivot=1.006) == "reclaim" and zone_status(None, 1.0) is None and zone_status(1.0, 0) is None,
      [zone_status(p, 1.0) for p in (1.0, 0.99, 1.115, 1.12, 1.07, 1.06, 1.03)])
    g("AG3 معاملُ المقياس: ضمن 3% «ok» · ×1.5 فأكثر «split» · وبينهما «mismatch» · ومجهولٌ بلا قيمة",
      [k_flag(x) for x in (1.0, 1.03, 0.971, 1.031, 1.49, 1.5, 0.66, None, 0)] ==
      ["ok", "ok", "ok", "mismatch", "mismatch", "split", "split", "unknown", "unknown"])
    g("AG4 تصنيفُ سبب الإنتاج من نصّه: جاهز · كسرُ الوقف · تحت الدعم · بعيد · فوق النطاق · بيانات",
      [prod_category("ready_now", "x"), prod_category("watch", "كسر الوقف — الفكرة"), prod_category("watch", "تحت الدعم — يتحوّل"),
       prod_category("watch", "بعيد فوق منطقة الدفعات"), prod_category("watch", "فوق نطاق الدفعات بـ1%"),
       prod_category("watch", "بيانات آخر جلسة"), prod_category("watch", "شيء")] == ["ready", "stop", "reclaim", "far", "above_band", "stale", "other"])
    g("AG5 عمرُ اللمسة: آخرُ شمعةٍ ضمن 0.5% · ولا لمسةَ ⟵ None",
      touch_age([1.0, 2.0, 1.004, 3.0, 3.0], 1.0) == 2 and touch_age([2.0, 2.0], 1.0) is None and touch_age([1.0], None) is None)
    g("AG6 الربيعيّات: الوسيط والربع الأعلى والأقصى · والفارغ None", q([1, 2, 3, 4]) == {"n": 4, "median": 2.5, "q3": 3.25, "max": 4, "min": 1}
      and q([None]) is None and q([1, 2, 30, None])["median"] == 2)
    import bisect as _b  # noqa: F401
    sess = ["2026-10-09", "2026-10-12", "2026-10-13"]
    cu = [close_utc(d) for d in sess]
    g("AG7 جلسةُ القرار: آخرُ جلسةٍ أُغلقت قبل اللقطة (‏20:00 UTC صيفًا) · ولقطةُ الصباح تقرأ جلسةَ الأمس",
      decision_session(sess, cu, dt.datetime(2026, 10, 13, 6, 0, tzinfo=dt.timezone.utc)) == "2026-10-12"
      and decision_session(sess, cu, dt.datetime(2026, 10, 13, 20, 1, tzinfo=dt.timezone.utc)) == "2026-10-13"
      and decision_session(sess, cu, dt.datetime(2026, 10, 13, 19, 59, tzinfo=dt.timezone.utc)) == "2026-10-12"
      and decision_session(sess, cu, dt.datetime(2026, 10, 9, 0, 0, tzinfo=dt.timezone.utc)) is None)
    g("AG8 جدارُ يومٍ D لجلسة ما قبله", _wall_session("2026-10-13", sess) == "2026-10-12" and _wall_session("2026-10-09", sess) is None)
    r2 = {"bars_after_build": {"over8_pct": 60.0}, "gap_build_over8_pooled": {"median": 6.0},
          "gaps_build_anchor": {"9-15": {"median": 9.0}, "16-25": {"median": 1.0}, "26+": None},
          "over8": {"watch_flip_build": {"days": 30, "of": 100}}}
    v1 = verdict(r2)["verdict"]
    r2["bars_after_build"]["over8_pct"] = 20.0
    v2 = verdict(r2)["verdict"]
    r2["bars_after_build"]["over8_pct"] = 40.0
    v3 = verdict(r2)["verdict"]
    r2["bars_after_build"]["over8_pct"] = 60.0
    r2["over8"]["watch_flip_build"]["days"] = 20
    v4 = verdict(r2)["verdict"]
    r2b = dict(r2, gap_build_over8_pooled={"median": 4.0})
    v5 = verdict(r2b)["verdict"]
    g("AG11 الحصّة: العددُ والنسبةُ من المقام · والفارغُ بلا نسبة",
      _share(["far", "ready", "far", "x"], "far") == {"n": 4, "k": 2, "pct": 50.0} and _share([], "far")["pct"] is None)
    g("AG10 (ب) وسيطُ المجمَّع فوق 8 كما كُتب — لا أكبرُ وسيطِ فئة (‏9.0 في فئةٍ والمجمَّعُ 4.0 ⟵ لا يُعَدّ 5% فأكثر)",
      v5 == "present_no_explanatory_effect" and verdict(r2b)["b_gap_median_over8_build"] == 4.0, v5)
    g("AG9 الحكمُ كما كُتب قبل الرقم: (أ) 50% ‏+ (ب) 5% ‏+ (ج) ربع ⟵ مرشَّحٌ يلزمه الخمسة · دون الربع ساقطة · وبينهما موجودةٌ بلا أثر",
      (v1, v2, v3, v4) == ("candidate_defect_needs_five", "dropped", "present_no_explanatory_effect", "present_no_explanatory_effect"),
      (v1, v2, v3, v4))
    try:
        import inspect
        import gen5_features as G
        S = G.S()
        src = inspect.getsource(S.build_interpretation)
        i = src.find("hi_z = round(max(trs), 2)")                # the entry_mode block, bounded to its first decisions
        blk = src[i:i + 600] if i >= 0 else ""
        p12 = (abs(S.CONFIG["ENTRY_STEP_PCT"] / 100.0 - STEP) < 1e-12 and int(S.CONFIG["ENTRY_TRANCHES"]) == N_TR
               and blk.count("price > hi_z * %s" % FAR_MULT) == 1 and blk.count("price < pivot * %s" % RECLAIM) == 1)
        w12 = (S.CONFIG["ENTRY_STEP_PCT"], S.CONFIG["ENTRY_TRANCHES"])
    except Exception as e:                                           # noqa: BLE001
        p12, w12 = False, f"⛔ {type(e).__name__}"
    _res = {"verdict": {"a_over8_build_pct": 31.0, "b_gap_median_over8_build": 3.42, "c_flip_share_pct": 17.5,
                        "verdict": "present_no_explanatory_effect"},
            "R2": {"snap_days": 51, "episodes": 174, "stock_days": 1857, "pivot_vs_today": {"n": 1658, "differ": 539}}}
    _body = "\n## ⓪ x\n51 يومَ لقطة · 174 نطاقًا مبنيًّا · 1,857 يومَ سهم · 539 من 1,658 (32.5%)"
    _good = "# h\n69.0% · 31.0% · 3.42% · 17.5% · ظاهرةٌ موجودةٌ بلا أثرٍ يفسّر الصمت" + _body
    _late = "# h\n69.0% · 31.0% · 3.42% · ظاهرةٌ موجودةٌ بلا أثرٍ يفسّر الصمت" + _body + " 17.5%"
    _wrongv = _good.replace("ظاهرةٌ موجودةٌ بلا أثرٍ يفسّر الصمت", "ساقطة")
    g("AG13 وثيقةُ النتيجة: الحكمُ ومعاييرُه الثلاثة في الرأس (قبل «## ⓪») لا في أيّ مكان · والمجتمعُ في المتن",
      doc_check(_res, _good) == [] and doc_check(_res, _late) == ["17.5%"] and "ظاهرةٌ موجودةٌ بلا أثرٍ يفسّر الصمت" in doc_check(_res, _wrongv)
      and doc_check(_res, _good.replace("539 من", "538 من")) == ["539 من 1,658"],
      (doc_check(_res, _good), doc_check(_res, _late)))
    try:
        import pandas as pd
        import gen5_features as G
        S = G.S()
        idx = pd.bdate_range("2026-01-01", periods=40)
        lows = [10.0 - 0.1 * i for i in range(30)] + [7.5, 7.6, 7.7, 7.8, 7.9, 8.0, 8.1, 8.2, 8.3, 0.5]
        df = pd.DataFrame({"Open": 9.0, "High": 11.0, "Low": lows, "Close": [x + 0.5 for x in lows], "Volume": 1e6}, index=idx)
        s39 = idx[38].strftime("%Y-%m-%d")
        f1 = features(S, df, s39)
        f2 = features(S, df.iloc[:39], s39)
        p14 = (f1["m5"] == min(lows[34:39]) and f1["pivot25"] == f2["pivot25"] == min(lows[14:39])
               and f1["bars_after"] == f2["bars_after"] == 38 - (14 + lows[14:39].index(min(lows[14:39])))
               and f1["last_bar"] == s39 and features(S, df, idx[20].strftime("%Y-%m-%d")) is None)
        w14 = (f1["m5"], f1["pivot25"], f1["bars_after"], f1["last_bar"])
    except Exception as e:                                           # noqa: BLE001
        p14, w14 = False, f"⛔ {type(e).__name__}"
    g("AG14 بلا نظرٍ للمستقبل: شمعةٌ بعد s لا تغيّر شيئًا · `m5` أدنى خمس شموع حتى s · و`pivot`/`bars_after` من pivot_stability · ودون 30 شمعة None",
      p14, w14)
    g("AG12 ثوابتُ الصيغ = الإنتاجُ بالاسم (ENTRY_STEP_PCT · ENTRY_TRANCHES · ×1.05 «بعيد» · ×0.995 «تحت الدعم» في build_interpretation)",
      p12, w12)
    print(("✅ الحرّاس كلُّهم" if all(ok) else "❌ سقط حارس") + f" ({sum(ok)}/{len(ok)})")
    return 0 if all(ok) else 1


RESULT_MD = os.path.join(HERE, "ANCHOR_AGE_RESULT.md")
VERDICT_AR = {"present_no_explanatory_effect": "ظاهرةٌ موجودةٌ بلا أثرٍ يفسّر الصمت", "dropped": "ساقطة",
              "candidate_defect_needs_five": "عطلٌ مُثبَت", "no_measure": "لا قياس"}


def _norm(t):
    return (t or "").replace("\u200f", "").replace("\u2212", "-")


def doc_check(res, text=None):
    """The result document carries the JSON's numbers: the head (before «## ⓪») the verdict and its three criteria, the body the
    population and the display count. Returns the missing strings ([] = consistent)."""
    if text is None:
        text = open(RESULT_MD, encoding="utf-8").read() if os.path.exists(RESULT_MD) else ""
    t = _norm(text)
    head = t.split("## ⓪")[0] if "## ⓪" in t else ""
    v, e = res["verdict"], res["R2"]
    a = v["a_over8_build_pct"]
    want_head = [f"{100 - a:.1f}%", f"{a}%", f"{v['b_gap_median_over8_build']}%", f"{v['c_flip_share_pct']}%", VERDICT_AR[v["verdict"]]]
    pv = e["pivot_vs_today"]
    want_body = [f"{e['snap_days']} يومَ لقطة", f"{e['episodes']} نطاقًا مبنيًّا", f"{e['stock_days']:,} يومَ سهم",
                 f"{pv['differ']} من {pv['n']:,}", f"{round(100 * pv['differ'] / pv['n'], 1)}%"]
    return [w for w in want_head if w not in head] + [w for w in want_body if w not in t]


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--guards" in argv:
        return guards()
    outs = outputs()
    if "--check" in argv:
        bad = [os.path.relpath(p, ROOT) for p, s in outs.items() if not os.path.exists(p) or open(p, encoding="utf-8").read() != s]
        print("✅ المخرَجاتُ تُعاد بايتًا" if not bad else f"❌ تختلف: {bad}")
        miss = doc_check(json.loads(outs[OUT_JSON]))
        print("✅ وثيقةُ النتيجة تحمل أرقامَ الـJSON" if not miss else f"❌ وثيقةُ النتيجة لا تحمل: {miss}")
        return 0 if not (bad or miss) else 1
    for p, s in outs.items():
        with open(p, "w", encoding="utf-8") as f:
            f.write(s)
        print("✍️", os.path.relpath(p, ROOT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
