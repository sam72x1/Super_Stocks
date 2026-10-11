"""READY70 — unified +70% explosion events × bot-tracked pivots (research · offline · read-only).

Builds, from the repository alone (git history + archived bars), with **no network**:
  data/episodes.csv.gz   explosion episodes recomputed with the bot's own detector (scan_explosions logic)
  data/log_events.csv.gz the bot's logged explosion records (weekly_watchlist.json["explosions"] over git history)
                         with a match status against the recomputed episodes
  data/obs.csv.gz        one row per (pivot tracked by the bot, session t): bot state at decision time,
                         point-in-time features from bars <= t, and labels from bars > t
  data/inventory.json    counts, ranges and completeness of every source

Decision time for row (sym, t) = pre-open of the next session t+1 (13:30 UTC); the bot snapshot used is the
last weekly_watchlist.json commit at or before that moment. Features read bars dated <= t only.
Run from the repo root:  python3 faisal_engine/ready70/r70_build.py      (add --check to verify outputs)
"""
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import subprocess
import sys

os.environ.setdefault("FAISAL_ONLY", "1")
os.environ["FAISAL_ONLY"] = "1"
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT)
import numpy as np                                                        # noqa: E402
import pandas as pd                                                       # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
BARS_FILE = os.path.join(ROOT, "faisal_engine", "data", "rank", "bars.json.gz")
SPLITS_FILE = os.path.join(ROOT, "faisal_engine", "data", "rank", "splits.json")
FIRST_PARTIAL = "2026-10-09"          # bars fetched 2026-10-09 14:18 UTC (10:18 ET) ⇒ that bar is intraday-partial
OBS_FROM, OBS_TO = "2026-07-01", "2026-10-07"   # observation sessions t (decision before t+1 opens)
DET_FROM = "2025-04-01"               # detector evaluated as-of every session from here (before PI_FROM)
HORIZONS = (5, 10, 20)
PI_FROM, PI_TO = "2025-05-01", "2026-10-07"     # pivot-identity population (needs ~252 bars for the 52w high)
OPEN_UTC = (13, 30)                   # NY open in EDT (whole window is EDT)
_S = None


def S():
    """Import the bot lazily (constants and functions are read, never written)."""
    global _S
    if _S is None:
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            import Super_stock as mod                                     # noqa: E402
        _S = mod
    return _S


# ───────────────────────── bars ─────────────────────────
def load_bars(path=BARS_FILE, first_partial=FIRST_PARTIAL):
    raw = json.load(gzip.open(path, "rt", encoding="utf-8"))
    out = {}
    for sym, rows in raw["daily"].items():
        rows = [r for r in rows if r[0] < first_partial and all(x is not None for x in r[1:5])]
        if not rows:
            continue
        a = np.array([[float(x) for x in r[1:6]] for r in rows], dtype=float)
        ds = [r[0] for r in rows]
        out[sym] = {"d": ds, "ix": {d: k for k, d in enumerate(ds)},
                    "o": a[:, 0], "h": a[:, 1], "l": a[:, 2], "c": a[:, 3], "v": a[:, 4]}
    return raw["meta"], out


def sessions_calendar(bars, min_syms=500):
    cnt = {}
    for b in bars.values():
        for d in b["d"]:
            cnt[d] = cnt.get(d, 0) + 1
    return sorted(d for d, n in cnt.items() if n >= min_syms)


# ───────────────────────── detector (exact scan_explosions semantics, as-of a session) ─────────────────────────
def detect_asof(c, i):
    """The bot's explosion detector applied to closes c[0..i] (inclusive). Returns (kind, launch_idx, gain_pct) or None.
    Mirrors scan_explosions: one-day jump over the last EXPLOSION_LOOKBACK sessions (max gain, >= EXPLOSION_PCT),
    else S._run_explosion (trough->peak over EXPLOSION_RUN_LOOKBACK, >= EXPLOSION_RUN_PCT)."""
    C = S().CONFIG
    n = i + 1
    if n < C["MIN_BARS"] + 1:
        return None
    look = min(int(C["EXPLOSION_LOOKBACK"]), n - 1)
    gains = [(k, (c[i - k + 1] / c[i - k] - 1.0) * 100.0) for k in range(1, look + 1) if c[i - k] > 0]
    if gains:
        k_max, g1 = max(gains, key=lambda p: p[1])
        if g1 >= C["EXPLOSION_PCT"]:
            return ("jump", i - k_max + 1, float(g1))
    grun, launch = S()._run_explosion(c[:n])
    if grun is None:
        return None
    return ("run", int(launch), float(grun))


def episodes_for(sym, b, det_from=DET_FROM):
    """Group daily detections into episodes. A detection whose launch <= the current episode's peak belongs to it
    (sliding-window re-detection of the same move); a launch after that peak opens a new, independent wave."""
    c, d = b["c"], b["d"]
    eps, cur = [], None
    start = next((i for i, x in enumerate(d) if x >= det_from), None)
    if start is None:
        return eps
    for i in range(start, len(c)):
        r = detect_asof(c, i)
        if r is None:
            continue
        kind, L, g = r
        if cur is not None and L <= cur["P"]:
            # same move: a later detection may reveal an earlier trough (slow ramp before a jump) ⇒ the move's start
            # is the earliest launch seen, never earlier than the previous episode's peak (waves stay disjoint)
            floor = (eps[-2]["P"] + 1) if len(eps) >= 2 else 0
            if max(L, floor) < cur["L"]:
                cur["L"] = max(L, floor)
                cur["trough_close"] = float(c[max(cur["L"] - 1, 0)])
            cur["last_det"] = i
            seg = c[cur["L"]:i + 1]
            cur["P"] = cur["L"] + int(np.argmax(seg))
            continue
        trough_i = max(L - 1, 0)
        seg = c[L:i + 1]
        cur = {"sym": sym, "L": L, "D1": i, "kind_d1": kind, "gain_d1": round(g, 1), "last_det": i,
               "P": L + int(np.argmax(seg)), "trough_close": float(c[trough_i])}
        eps.append(cur)
    out = []
    for e in eps:
        tc = e["trough_close"]
        out.append({"sym": sym, "launch": d[e["L"]], "d1": d[e["D1"]], "peak": d[e["P"]], "last_det": d[e["last_det"]],
                    "L_i": e["L"], "D1_i": e["D1"], "P_i": e["P"], "kind_d1": e["kind_d1"], "gain_d1": e["gain_d1"],
                    "peak_gain": round((float(c[e["P"]]) / tc - 1.0) * 100.0, 1) if tc > 0 else None,
                    "sessions_to_d1": e["D1"] - e["L"] + 1})
    return out


def split_flags(eps, splits):
    """SPLIT_NEAR: a split (any ratio) dated within [launch-5d, d1+1d] ⇒ the move may be a split artefact."""
    for e in eps:
        lo = (dt.date.fromisoformat(e["launch"]) - dt.timedelta(days=5)).isoformat()
        hi = (dt.date.fromisoformat(e["d1"]) + dt.timedelta(days=1)).isoformat()
        near = [s for s in (splits.get(e["sym"]) or []) if lo <= s[0] <= hi]
        e["split_near"] = bool(near)
        e["extreme"] = bool((e["gain_d1"] or 0) >= S().CONFIG["SPLIT_SUSPECT_GAIN_PCT"])
        e["quality"] = "SPLIT_NEAR" if near else "OK"
    return eps


# ───────────────────────── git history ─────────────────────────
def git_commits(path):
    out = []
    r = subprocess.run(["git", "log", "--reverse", "--format=%H %cI", "--", path], cwd=ROOT, capture_output=True, text=True)
    for line in r.stdout.splitlines():
        h, t = line.split()
        out.append((h, dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc)))
    return out


def git_json(h, path):
    r = subprocess.run(["git", "show", f"{h}:{path}"], cwd=ROOT, capture_output=True, text=True)
    if r.returncode:
        return None
    try:
        return json.loads(r.stdout)
    except Exception:                                                     # noqa: BLE001
        return None


WL_KEYS = ("symbol", "added", "status", "cont_status", "last_price", "price", "tranches", "entry", "stop", "pivot",
           "interp", "price_state", "price_bar", "hit")


def wl_history():
    snaps = []
    for h, t in git_commits("weekly_watchlist.json"):
        wl = git_json(h, "weekly_watchlist.json")
        if not isinstance(wl, dict):
            continue
        snaps.append({"h": h, "t": t,
                      "stocks": [{k: s.get(k) for k in WL_KEYS if k in s} for s in (wl.get("stocks") or []) if isinstance(s, dict)],
                      "pullback": [{k: s.get(k) for k in ("symbol", "status", "last_price", "entry", "tranches") if k in s}
                                   for s in (wl.get("pullback") or []) if isinstance(s, dict)],
                      "explosions": [e for e in (wl.get("explosions") or []) if isinstance(e, dict)]})
    return snaps


def nw_history():
    out = []
    for h, t in git_commits("near_watch.json"):
        nw = git_json(h, "near_watch.json")
        if isinstance(nw, dict):
            out.append({"h": h, "t": t, "e": {k: {"last_seen": v.get("last_seen"), "outside": v.get("outside") or []}
                                              for k, v in nw.items() if isinstance(v, dict)}})
    return out


def reject_walls():
    path = os.path.join(ROOT, "reject_log.json")
    out = {}
    for e in json.load(open(path, encoding="utf-8")):
        m = {}
        for code, syms in (e.get("walls") or {}).items():
            for s in syms:
                m[s] = code
        out[e["date"]] = m
    return out


def snapshot_at(snaps, when):
    """Last snapshot committed at or before `when` (UTC)."""
    lo, hi, best = 0, len(snaps) - 1, None
    while lo <= hi:
        mid = (lo + hi) // 2
        if snaps[mid]["t"] <= when:
            best, lo = mid, mid + 1
        else:
            hi = mid - 1
    return None if best is None else snaps[best]


# ───────────────────────── features (bars <= t only) ─────────────────────────
def frame_upto(b, i, tail=80):
    """Bars [i-tail+1 .. i]. pivot_cycle_state reads only tail(PIVOT_CYCLE_WIN=60), so tail=80 gives the same output
    as the full history (asserted in test_r70) at a fraction of the cost."""
    lo = max(0, i + 1 - tail)
    sl = slice(lo, i + 1)
    return pd.DataFrame({"Open": b["o"][sl], "High": b["h"][sl], "Low": b["l"][sl], "Close": b["c"][sl],
                         "Volume": b["v"][sl]}, index=pd.to_datetime(b["d"][lo: i + 1]))


class _Col:
    __slots__ = ("a",)

    def __init__(self, a):
        self.a = a

    def to_numpy(self, dtype=None):
        return self.a.astype(dtype) if dtype is not None else self.a

    def tolist(self):
        return self.a.tolist()


class FastFrame:
    """Duck-typed OHLC frame for S.pivot_cycle_state / S.tested_level (they use only .tail(w) and
    ["Low"|"High"|"Close"].to_numpy()/.tolist()). Equality with the pandas path is asserted in test_r70."""
    __slots__ = ("cols",)

    def __init__(self, cols):
        self.cols = cols

    def tail(self, w):
        w = int(w)
        return FastFrame({k: v[-w:] for k, v in self.cols.items()})

    def __getitem__(self, k):
        return _Col(self.cols[k])

    def __len__(self):
        return len(self.cols["Close"])


def fast_frame(b, i, tail=80):
    lo = max(0, i + 1 - tail)
    return FastFrame({"Open": b["o"][lo:i + 1], "High": b["h"][lo:i + 1], "Low": b["l"][lo:i + 1],
                      "Close": b["c"][lo:i + 1]})


def split_factor_after(splits_sym, dates):
    """Per-bar factor that turns split-adjusted prices back into the price traded that day:
    actual = adjusted × Π ratio over splits dated after the bar (and not after the archive end)."""
    sp = sorted((d, float(r)) for d, r in (splits_sym or []) if r and d <= dates[-1])
    f = np.ones(len(dates))
    for d, r in sp:
        k = int(np.searchsorted(np.array(dates), d, side="left"))   # bars strictly before the split date
        f[:k] *= r
    return f


def identity_vec(b, splits_sym=None):
    """Vectorised `_had_pivot_identity` (M1 price · M2 drop band from the 52w high · M3 prior spike) for every bar.
    M2/M3 are ratio-based (split-invariant); M1 uses the price actually traded that day (split-unadjusted)."""
    C = S().CONFIG
    c, h = b["c"], b["h"]
    n = len(c)
    r_end = np.zeros(n)
    for w in range(1, int(C["PRIOR_SPIKE_WINDOW"]) + 1):
        if n <= w:
            break
        with np.errstate(divide="ignore", invalid="ignore"):
            ratio = c[w:] / np.where(c[:-w] > 0, c[:-w], np.nan) - 1.0
        r_end[w:] = np.maximum(r_end[w:], np.nan_to_num(ratio, nan=0.0))
    cum = np.maximum.accumulate(r_end)
    ex = int(C["BASE_WINDOW"])
    fac = split_factor_after(splits_sym, b["d"]) if splits_sym is not None else np.ones(n)
    out = np.zeros(n, dtype=bool)
    for t in range(int(C["MIN_BARS"]), n):
        m = t + 1 - ex
        best = cum[m - 1] * 100.0 if m >= 15 else 0.0
        hi = h[max(0, t - 251): t + 1].max()
        if not hi > 0:
            continue
        drop = (1.0 - c[t] / hi) * 100.0
        out[t] = bool(c[t] * fac[t] >= C["MIN_PRICE"] and C["MIN_DROP_FLOOR"] <= drop <= C["MAX_DROP_PCT"]
                      and best >= C["PRIOR_SPIKE_FLOOR"])
    return out


def features(b, i):
    """Point-in-time features for session index i. Reads b[...][:i+1] only (guarded by test_r70).
    `px` is the price actually traded that day (split-unadjusted with b["fac"], set by the caller when known)."""
    c, h, l = b["c"][: i + 1], b["h"][: i + 1], b["l"][: i + 1]
    f = {"px": round(float(c[-1] * b["fac"][i]), 4) if b.get("fac") is not None else None}
    ff = fast_frame(b, i)
    pc = S().pivot_cycle_state(ff)
    tl = S().tested_level(ff)
    lvl = float(tl["level"]) if tl else None
    f["tl_dist"] = round((c[-1] / lvl - 1.0) * 100.0, 2) if lvl else None
    # current READY location rule on the frozen anchor: stop = anchor (rounded), top tranche = anchor×1.06 (rounded)
    f["loc"] = int(bool(lvl and round(lvl, 2) < c[-1] <= round(lvl * (1 + 2 * S().CONFIG["ENTRY_STEP_PCT"] / 100.0), 2)))
    f["pc_stage"] = int(pc["stage"]) if pc else 0
    f["pc_branch"] = (pc.get("branch") or "") if pc else ""
    f["pc_held"] = int(pc.get("held") or 0) if pc else 0
    f["pc_bounce"] = pc.get("bounce_pct") if pc else None
    f["pc_first_rise"] = int(bool(pc.get("first_rise"))) if pc else 0
    f["pc_vs_bottom"] = pc.get("vs_bottom_pct") if pc else None
    f["pc_bottom_ago"] = pc.get("bottom_ago") if pc else None
    f["ret5"] = round((c[-1] / c[-6] - 1.0) * 100.0, 2) if len(c) >= 6 and c[-6] > 0 else None
    f["ret1"] = round((c[-1] / c[-2] - 1.0) * 100.0, 2) if len(c) >= 2 and c[-2] > 0 else None
    f["rise_low10"] = round((c[-1] / l[-10:].min() - 1.0) * 100.0, 2) if len(l) >= 10 and l[-10:].min() > 0 else None
    f["range20"] = round((h[-20:].max() / l[-20:].min() - 1.0) * 100.0, 2) if len(l) >= 20 and l[-20:].min() > 0 else None
    return f


# ───────────────────────── labels (bars > t only) ─────────────────────────
def label(eps_sym, i, n_bars, H):
    """POS: an episode launches after t (L > i) and is detected within H sessions (D1 <= i+H).
    IN_EVENT: an episode is under way at t (L <= i <= peak). CENSORED: i+H beyond the last complete bar."""
    for e in eps_sym:
        if e["L_i"] <= i <= e["P_i"]:
            return ("IN_EVENT" if e.get("quality", "OK") == "OK" else "UNKNOWN_SPLIT"), e
    if i + H > n_bars - 1:
        return "CENSORED", None
    for e in eps_sym:
        if i < e["L_i"] and e["D1_i"] <= i + H:
            return "POS", e
    return "NEG", None


def label_fwd(b, eps_sym, splits_sym, i, H):
    """F70 — the tool's own condition measured from the decision onward (no trough before the decision):
    within sessions (i, i+H]: a close-to-close day >= EXPLOSION_PCT, or close_k / min(close_i..close_{k-1}) - 1 >=
    EXPLOSION_RUN_PCT. DURING: the tool had already detected an episode and it has not peaked (D1 <= i <= peak).
    UNKNOWN_SPLIT: a split dated within (t, t+H]. CENSORED: i+H beyond the last complete bar."""
    C = S().CONFIG
    c, d = b["c"], b["d"]
    for e in eps_sym:
        if e["D1_i"] <= i <= e["P_i"]:
            return "DURING", None, None
    if i + H > len(c) - 1:
        return "CENSORED", None, None
    lo_d, hi_d = d[i], d[i + H]
    if any(lo_d < sd <= hi_d for sd, _r in (splits_sym or [])):
        return "UNKNOWN_SPLIT", None, None
    run_min = c[i]
    best = 0.0
    for k in range(i + 1, i + H + 1):
        jump = (c[k] / c[k - 1] - 1.0) * 100.0 if c[k - 1] > 0 else 0.0
        rise = (c[k] / run_min - 1.0) * 100.0 if run_min > 0 else 0.0
        best = max(best, rise)
        if jump >= C["EXPLOSION_PCT"] or rise >= C["EXPLOSION_RUN_PCT"]:
            return "POS", k - i, round(max(rise, jump), 1)
        run_min = min(run_min, c[k])
    return "NEG", None, round(best, 1)


def fwd_path(b, i, H):
    """From the decision close: max close gain and min close drawdown over (t, t+H] (outcome-only fields)."""
    c = b["c"]
    if i + H > len(c) - 1 or not c[i] > 0:
        return None, None
    seg = c[i + 1:i + H + 1]
    return round((seg.max() / c[i] - 1.0) * 100.0, 1), round((seg.min() / c[i] - 1.0) * 100.0, 1)


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


def build(out_dir=DATA):
    os.makedirs(out_dir, exist_ok=True)
    meta, bars = load_bars()
    cal = sessions_calendar(bars)
    splits = json.load(open(SPLITS_FILE, encoding="utf-8"))["splits"]
    # 1) episodes for every symbol in the archive
    eps = {}
    for sym in sorted(bars):
        eps[sym] = split_flags(episodes_for(sym, bars[sym]), splits)
    all_eps = [e for v in eps.values() for e in v]
    # 2) bot history
    snaps = wl_history()
    nws = nw_history()
    walls = reject_walls()
    # 3) logged explosion records vs recomputed episodes
    logged = {}
    for s in snaps:
        for e in s["explosions"]:
            k = (e.get("symbol"), e.get("expl_date") or e.get("date"))
            if k not in logged:
                logged[k] = dict(e, first_commit=s["t"].isoformat())
    log_rows = []
    for (sym, ed), e in sorted(logged.items(), key=lambda kv: (kv[0][1] or "", kv[0][0] or "")):
        st = "NO_BARS" if sym not in bars else "UNMATCHED"
        if sym in bars:
            for ep in eps[sym]:
                lo = cal[max(0, cal.index(ep["launch"]) - 3)] if ep["launch"] in cal else ep["launch"]
                if lo <= ed <= ep["last_det"]:
                    st = "MATCHED"
                    break
        log_rows.append({"symbol": sym, "expl_date": ed, "scan_date": e.get("date"), "kind": e.get("kind"),
                         "gain": e.get("gain"), "was_pivot": e.get("was_pivot"), "base_reason": e.get("base_reason"),
                         "suspect_split": e.get("suspect_split"), "match": st})
    # 4) observations: bot-tracked pivots at each decision
    obs = []
    cal_idx = {d: k for k, d in enumerate(cal)}
    t_days = [d for d in cal if OBS_FROM <= d <= OBS_TO]
    nw_i = 0
    for t in t_days:
        k = cal_idx[t]
        if k + 1 >= len(cal):
            break
        t1 = cal[k + 1]
        when = dt.datetime.fromisoformat(t1).replace(hour=OPEN_UTC[0], minute=OPEN_UTC[1], tzinfo=dt.timezone.utc)
        snap = snapshot_at(snaps, when)
        if snap is None:
            continue
        age_h = round((when - snap["t"]).total_seconds() / 3600.0, 1)
        mem = {}
        for s in snap["stocks"]:
            sym = s.get("symbol")
            if not sym:
                continue
            carried = s.get("cont_status") in ("continues", "exited")
            ready = (not carried) and S().entry_status(s).get("status") == "ready_now"
            mem[sym] = {"src": "carried" if carried else "watchlist", "bot_ready": int(ready),
                        "has_interp": int(bool(s.get("interp")))}
        for s in snap["pullback"]:
            sym = s.get("symbol")
            if sym and sym not in mem:
                mem[sym] = {"src": "pullback", "bot_ready": int(s.get("status") == "triggered"), "has_interp": 0}
        nsnap = snapshot_at(nws, when) if nws else None
        nw_seen = set()
        if nsnap is not None:
            nw_seen = {s for s, v in nsnap["e"].items() if v.get("last_seen") == t1}
            for s in nw_seen:
                if s not in mem:
                    mem[s] = {"src": "near_watch", "bot_ready": 0, "has_interp": 0}
        wall = walls.get(t1, {})
        for sym, m in sorted(mem.items()):
            row = {"t": t, "t1": t1, "sym": sym, "src": m["src"], "bot_ready": m["bot_ready"],
                   "has_interp": m["has_interp"], "snap_age_h": age_h, "in_near_watch": int(sym in nw_seen),
                   "wall_t1": wall.get(sym, "") if walls.get(t1) is not None else "NO_LOG"}
            b = bars.get(sym)
            i = None if b is None else b["ix"].get(t)
            if b is None or i is None:
                row["bars"] = "MISSING"
                obs.append(row)
                continue
            row["bars"] = "OK"
            if b.get("fac") is None:
                b["fac"] = split_factor_after(splits.get(sym, []), b["d"])
            row.update(features(b, i))
            for H in HORIZONS:
                lab, e = label(eps[sym], i, len(b["c"]), H)
                if lab == "POS" and e.get("quality") != "OK":
                    lab = "UNKNOWN_SPLIT"
                row[f"y{H}"] = lab
                if lab == "POS":
                    row[f"y{H}_to_launch"] = e["L_i"] - i
                    row[f"y{H}_to_d1"] = e["D1_i"] - i
                    row[f"y{H}_gain"] = e["gain_d1"]
                    row[f"y{H}_ep"] = f'{sym}|{e["launch"]}'
                fl, fk, fg = label_fwd(b, eps[sym], splits.get(sym, []), i, H)
                row[f"f{H}"], row[f"f{H}_k"], row[f"f{H}_gain"] = fl, fk, fg
                row[f"g{H}_max"], row[f"g{H}_dd"] = fwd_path(b, i, H)
            obs.append(row)
    # 5) write
    ep_fields = ["sym", "launch", "d1", "peak", "last_det", "kind_d1", "gain_d1", "peak_gain", "sessions_to_d1",
                 "split_near", "extreme", "quality"]
    _wcsv(os.path.join(out_dir, "episodes.csv.gz"), [e for e in all_eps if e["d1"] >= DET_FROM], ep_fields)
    _wcsv(os.path.join(out_dir, "log_events.csv.gz"), log_rows,
          ["symbol", "expl_date", "scan_date", "kind", "gain", "was_pivot", "base_reason", "suspect_split", "match"])
    o_fields = ["t", "t1", "sym", "src", "bot_ready", "has_interp", "snap_age_h", "in_near_watch", "wall_t1", "bars",
                "px", "pc_stage", "pc_branch", "pc_held", "pc_bounce", "pc_first_rise", "pc_vs_bottom", "pc_bottom_ago",
                "ret5", "ret1", "rise_low10", "range20", "tl_dist", "loc"]
    for H in HORIZONS:
        o_fields += [f"y{H}", f"y{H}_to_launch", f"y{H}_to_d1", f"y{H}_gain", f"y{H}_ep",
                     f"f{H}", f"f{H}_k", f"f{H}_gain", f"g{H}_max", f"g{H}_dd"]
    _wcsv(os.path.join(out_dir, "obs.csv.gz"), obs, o_fields)
    # 6) point-in-time pivot-identity population over the whole archive (the tool's own `was_pivot` notion)
    bt = {(o["t"], o["sym"]): o for o in obs}
    pi = build_pi(bars, eps, splits, bt)
    pi_fields = ["t", "sym", "bt_src", "bot_ready"] + o_fields[o_fields.index("px"):]
    _wcsv(os.path.join(out_dir, "pi_obs.csv.gz"), pi, pi_fields)
    inv = inventory(meta, bars, cal, all_eps, log_rows, snaps, nws, walls, obs)
    inv["pi"] = {"rows": len(pi), "symbols": len({r["sym"] for r in pi}), "from": PI_FROM, "to": PI_TO,
                 "sessions": len({r["t"] for r in pi}),
                 "definition": "Super_stock._had_pivot_identity (M1 price, M2 drop band, M3 prior spike; live FAISAL_ONLY constants)"
                               " evaluated per bar; M1 on the split-unadjusted price"}
    inv["other_live_sources"] = other_sources()
    json.dump(inv, open(os.path.join(out_dir, "inventory.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              sort_keys=True)
    return inv


def build_pi(bars, eps, splits, bt):
    rows = []
    for sym in sorted(bars):
        b = bars[sym]
        ident = identity_vec(b, splits.get(sym, []))
        b["fac"] = split_factor_after(splits.get(sym, []), b["d"])
        for i, d in enumerate(b["d"]):
            if not (PI_FROM <= d <= PI_TO) or not ident[i]:
                continue
            o = bt.get((d, sym))
            row = {"t": d, "sym": sym, "bt_src": (o or {}).get("src", ""), "bot_ready": (o or {}).get("bot_ready", "")}
            row.update(features(b, i))
            for H in HORIZONS:
                lab, e = label(eps[sym], i, len(b["c"]), H)
                if lab == "POS" and e.get("quality") != "OK":
                    lab = "UNKNOWN_SPLIT"
                row[f"y{H}"] = lab
                if lab == "POS":
                    row[f"y{H}_to_launch"] = e["L_i"] - i
                    row[f"y{H}_to_d1"] = e["D1_i"] - i
                    row[f"y{H}_gain"] = e["gain_d1"]
                    row[f"y{H}_ep"] = f'{sym}|{e["launch"]}'
                fl, fk, fg = label_fwd(b, eps[sym], splits.get(sym, []), i, H)
                row[f"f{H}"], row[f"f{H}_k"], row[f"f{H}_gain"] = fl, fk, fg
                row[f"g{H}_max"], row[f"g{H}_dd"] = fwd_path(b, i, H)
            rows.append(row)
    return rows


def other_sources():
    """Counts and ranges of the other in-repo live-alert ledgers (inventory only; not used as the outcome)."""
    out = {}

    def jl(path):
        p = os.path.join(ROOT, path)
        if not os.path.exists(p):
            return None
        return [json.loads(x) for x in open(p, encoding="utf-8") if x.strip()]
    for path, dk, sk in (("tier_fwd_ledger.jsonl", "date", "symbol"), ("presession_outcomes.jsonl", "day", "sym"),
                         ("press_radar_ledger.jsonl", "session", "symbol"), ("hunter_ledger.jsonl", "session", "symbol"),
                         ("pmfwd_log.jsonl", "day", "sym"), ("hand_flow_log.jsonl", None, "symbol"),
                         ("cumrise_fwd_ledger.jsonl", "day", None)):
        r = jl(path)
        if r is None:
            out[path] = "MISSING"
            continue
        ds = sorted(str(x.get(dk)) for x in r if dk and x.get(dk))
        out[path] = {"rows": len(r), "symbols": (len({x.get(sk) for x in r}) if sk else None),
                     "range": [ds[0], ds[-1]] if ds else None}
    ig = json.load(open(os.path.join(ROOT, "ignition_log.json"), encoding="utf-8"))
    out["ignition_log.json"] = {"rows": len(ig), "symbols": len({x.get("symbol") for x in ig}),
                                "range": [min(x["date"] for x in ig), max(x["date"] for x in ig)]}
    ah = json.load(open(os.path.join(ROOT, "alerts_history.json"), encoding="utf-8")).get("alerts") or []
    out["alerts_history.json"] = {"rows": len(ah), "symbols": len({x.get("symbol") for x in ah}),
                                  "range": [min(x["date"] for x in ah), max(x["date"] for x in ah)] if ah else None}
    return out


def inventory(meta, bars, cal, all_eps, log_rows, snaps, nws, walls, obs):
    import collections
    win_eps = [e for e in all_eps if "2026-06-22" <= e["d1"] <= cal[-1]]
    lr = collections.Counter(r["match"] for r in log_rows)
    lr_ok = [r for r in log_rows if not r["suspect_split"] and r["scan_date"] and r["scan_date"] <= "2026-10-08"]
    mem_syms = {o["sym"] for o in obs if o["src"] in ("watchlist", "carried", "pullback")}
    return {
        "bars": {"file": os.path.relpath(BARS_FILE, ROOT), "source": meta.get("source"), "fetched_utc": meta.get("utc"),
                 "symbols": len(bars), "first_partial_dropped": FIRST_PARTIAL, "last_complete_session": cal[-1],
                 "sessions": len(cal), "first_session": cal[0]},
        "detector": {"code": "Super_stock.scan_explosions / _run_explosion", "EXPLOSION_PCT": S().CONFIG["EXPLOSION_PCT"],
                     "EXPLOSION_LOOKBACK": S().CONFIG["EXPLOSION_LOOKBACK"],
                     "EXPLOSION_RUN_PCT": S().CONFIG["EXPLOSION_RUN_PCT"],
                     "EXPLOSION_RUN_LOOKBACK": S().CONFIG["EXPLOSION_RUN_LOOKBACK"], "price": "daily close",
                     "runs": "after the daily screener (morning) and the Friday renewal; logged to weekly_watchlist.json[explosions] (30-day retention)"},
        "episodes_recomputed_d1_from_2026_06_22": {"n": len(win_eps), "symbols": len({e['sym'] for e in win_eps}),
                                                   "split_near": sum(e["split_near"] for e in win_eps),
                                                   "extreme_ge_300": sum(e["extreme"] for e in win_eps),
                                                   "kind_d1": dict(collections.Counter(e["kind_d1"] for e in win_eps))},
        "log": {"records_unique_symbol_explDate": len(log_rows), "symbols": len({r["symbol"] for r in log_rows}),
                "scan_range": [min(r["scan_date"] for r in log_rows if r["scan_date"]),
                               max(r["scan_date"] for r in log_rows if r["scan_date"])],
                "match_status": dict(lr), "commits_read": len(snaps),
                "match_rate_non_suspect_with_bars": round(
                    sum(r["match"] == "MATCHED" for r in lr_ok) / max(1, sum(r["match"] != "NO_BARS" for r in lr_ok)), 4)},
        "tracked": {"watchlist_commits": len(snaps), "first_commit": snaps[0]["t"].isoformat(),
                    "last_commit": snaps[-1]["t"].isoformat(), "near_watch_commits": len(nws),
                    "reject_log_days": len(walls), "pivot_symbols_in_obs": len(mem_syms)},
        "obs": {"rows": len(obs), "bars_missing": sum(o.get("bars") == "MISSING" for o in obs),
                "by_src": dict(collections.Counter(o["src"] for o in obs))},
    }


def _digest(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("episodes.csv.gz", "log_events.csv.gz", "obs.csv.gz", "pi_obs.csv.gz", "inventory.json")
               if _digest(os.path.join(tmp, f)) != _digest(os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    inv = build()
    print(json.dumps(inv, ensure_ascii=False, indent=1))
