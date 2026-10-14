"""T-LAYERS — three layers (follow-up ⟶ readiness ⟶ TRIGGER): how often does a Faisal sweep-and-reclaim trigger fire on the bot's
queue, and what would it have caught among the 107 tracked movers? Research and display only (contract `T_LAYERS_prereg.md`, pinned
below and required on origin/main before any count: exit 9 otherwise). No production, threshold, root, LOGIC_VERSION or Telegram change.

The core trigger (all five from Faisal's words) is read on the production cycle `Super_stock.pivot_cycle_state` BY NAME:
  ① in the queue Q(t)  ② 7 ≤ sweep depth ≤ 13 % below the base (pc.bottom)  ③ close(t) > base  ④ first reclaim for this base
  ⑤ a later close under the sweep low cancels it.
Boosters (each alone first): VOL (link100_probe.daily_feats vol_x ≥ 3, by name) · NODE (volume node below the base, engineering) ·
CANDLE (long lower wick, close in the upper half, engineering).

    python3 fm_forensics/layers/layers_test.py --guards   # synthetic guards (no population read)
    python3 fm_forensics/layers/layers_test.py            # the sealed run ⟶ data/layers_result.json · data/*.csv
"""
import csv
import datetime as dt
import hashlib
import inspect
import json
import math
import os
import statistics as st
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
GEN5 = os.path.join(ROOT, "fm_forensics", "gen5")
HEAT = os.path.join(ROOT, "fm_forensics", "heat")
for _p in (GEN5, HEAT, ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

import gen5_features as G   # noqa: E402
import gen5_ext as X        # noqa: E402

PREREG = os.path.join(HERE, "T_LAYERS_prereg.md")
PREREG_SHA256 = "d847849edae25026de2d9fd7e56cec3eeb3aa966d65178449f7e723d9e88dd4c"
PROD_SRC_SHA256 = "ef96b9bdd94cd8a2f397969503960787ac9274d76fce8934b1d4884a0eed7dfb"
OUT = os.path.join(HERE, "data", "layers_result.json")
A_CSV = os.path.join(HERE, "data", "stage_a_daily.csv")
B_CSV = os.path.join(HERE, "data", "stage_b_events.csv")
FA_CSV = os.path.join(HERE, "data", "stage_b_false_alarms.csv")

# ── frozen design (the contract quotes each one) ────────────────────────────────────────────────────────
SW_LO, SW_HI = 7.0, 13.0          # «سحب السيوله متعارف عليه من 7٪ ل 13٪» (IMG_0297) — a band, not one number
MIN_BARS = 60                     # PIVOT_CYCLE_WIN: 60 bars before t or the day is unknown
WIN_A = ("2026-09-16", "2026-10-13")   # stage A: the last 20 sessions
FA_WIN = ("2026-08-17", "2026-09-15")  # false alarms: decision days with 20 forward sessions known by 2026-10-13
LEAD = 20                         # stage B window O−20 … O−1
FWD = 20                          # «لم يبلغ الضعف خلال 20 جلسة»
NODE_MAX, NODE_MIN, NODE_BIN = 120, 60, 0.01   # engineering: volume profile before the sweep, 1 % bins
WICK_MIN = 0.5                    # engineering: lower wick ≥ 50 % of the range and close ≥ mid-range
F1_MED_MAX, F2_ROLL_MIN, F3_SILENCE_MAX, F4_DAY_MAX = 2, 1, 4, 4
FLOOR_SYMS = 20
PUBLISHED_READY = 2 / 279         # the published reference: 2 of 279 = 0.7 %
BOOSTERS = ("VOL", "NODE", "CANDLE")
ORDER = ((), ("VOL",), ("NODE",), ("CANDLE",), ("VOL", "NODE"), ("VOL", "CANDLE"), ("NODE", "CANDLE"), ("VOL", "NODE", "CANDLE"))
FIVE = ("SXTC", "DKI", "RETO", "DLXY", "HUBC")


def _sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if os.path.exists(path) else None


def _mods():
    import gen5_test as T
    import gen5_fix as F
    import heat_test as H
    import link100_probe as L
    return G.S(), T, F, H, L


def prod_src_sha():
    S, T, F, H, L = _mods()
    fns = (S.pivot_cycle_state, S._cycle_sweep_reclaimed, S.entry_status, L.daily_feats, L._bucket, T.pre_open,
           T.nearwatch_history, H.build_events, X.explosion_stats, X.split_unadjusted)
    return hashlib.sha256("".join(inspect.getsource(f) for f in fns).encode()).hexdigest()


def check_pins(prereg=PREREG, prereg_sha=None):
    want = PREREG_SHA256 if prereg_sha is None else prereg_sha
    if _sha(prereg) != want:
        print(f"⛔ contract changed or not pinned: {_sha(prereg)} ≠ {want}")
        sys.exit(9)
    if prod_src_sha() != PROD_SRC_SHA256:
        print(f"⛔ production functions changed: {prod_src_sha()} ≠ {PROD_SRC_SHA256}")
        sys.exit(9)


def _main_contract():
    import subprocess
    rel = os.path.relpath(PREREG, ROOT).replace(os.sep, "/")
    p = subprocess.run(["git", "-C", ROOT, "show", f"origin/main:{rel}"], capture_output=True)
    return p.stdout if p.returncode == 0 else None


def check_merged(read=None):
    """«يُدمج في main قبل أيّ عدّ»: origin/main must carry the pinned contract bytes, else exit 9."""
    blob = (read or _main_contract)()
    got = hashlib.sha256(blob).hexdigest() if blob is not None else None
    if got != PREREG_SHA256:
        print(f"⛔ the pinned contract is not on origin/main ({got}) — merge it first (git fetch --force)")
        sys.exit(9)


# ── the trigger (pure) ──────────────────────────────────────────────────────────────────────────────────
def core23(pc, close):
    """② ∧ ③ on one day ⟶ (ok, reason). reason: no_cycle · no_retest · shallow · deep · not_reclaimed."""
    if not pc:
        return False, "no_cycle"
    if int(pc.get("stage") or 0) < 3:
        return False, "no_retest"
    sp = float(pc.get("sweep_pct") or 0.0)
    if pc.get("branch") != "sweep" or sp < SW_LO:
        return False, "shallow"
    if sp > SW_HI:
        return False, "deep"
    if not float(close) > float(pc["bottom"]):
        return False, "not_reclaimed"
    return True, None


class Cycle:
    """pivot_cycle_state on df[..x] for any x, memoised; `sweep` passes through (99 = no base reset, for the free depth)."""

    def __init__(self, df, pc_fn, sweep=None):
        self.df, self.pc_fn, self.sweep, self.memo = df, pc_fn, sweep, {}
        self.close = df["Close"].to_numpy(dtype=float)

    def pc(self, x):
        if x not in self.memo:
            self.memo[x] = (self.pc_fn(self.df.iloc[: x + 1], sweep=self.sweep) if x + 1 >= MIN_BARS else None)
        return self.memo[x]

    def c23(self, x):
        return core23(self.pc(x), self.close[x])


def day_state(cy, x):
    """Core ②-④ on day x (bars [..x]) ⟶ dict(status, reason, base, sweep_low, depth). status: TRIGGER · NOT_FIRST · NO · UNKNOWN."""
    if x + 1 < MIN_BARS:
        return {"status": "UNKNOWN", "reason": "short_history"}
    pc = cy.pc(x)
    ok, why = cy.c23(x)
    out = {"base": pc["bottom"] if pc else None, "sweep_low": pc.get("retest_low") if pc else None,
           "depth": pc.get("sweep_pct") if pc else None}
    if not ok:
        return {**out, "status": "NO", "reason": why}
    for y in range(x - 1, x - 1 - int(pc["bottom_ago"]), -1):
        if y + 1 < MIN_BARS:
            break
        py = cy.pc(y)
        if not py or py["bottom"] != pc["bottom"]:
            break
        if cy.c23(y)[0]:
            return {**out, "status": "NOT_FIRST", "reason": "not_first"}
    return {**out, "status": "TRIGGER", "reason": None}


def cancelled(close, x, until, sweep_low):
    """⑤ a close under the sweep low in (x, until] ⟶ True."""
    return any(float(close[y]) < float(sweep_low) for y in range(x + 1, min(until, len(close) - 1) + 1))


def hist_rows(df):
    return [[d.date().isoformat(), float(o), float(h), float(lo), float(c), float(v)]
            for d, o, h, lo, c, v in zip(df.index, df["Open"], df["High"], df["Low"], df["Close"], df["Volume"])]


def b_vol(L, rows, x):
    f = L.daily_feats(rows, x + 1, False)
    return bool(f) and f.get("vol_x") == "≥3"


def b_node(df, x, base, sweep_low):
    """Engineering (R-PRIOR-LIQ has no number): heaviest 1 % price bin in [base·(1−SW_HI%), base) in the volume profile of up to
    NODE_MAX bars before the first day whose low went under the base; True if the sweep low reached that bin's top."""
    lo, hi = df["Low"].to_numpy(float), df["High"].to_numpy(float)
    vo = df["Volume"].to_numpy(float)
    s0 = None
    for y in range(x, -1, -1):
        if lo[y] < base:
            s0 = y
        elif s0 is not None:
            break
    if s0 is None:
        return False
    a = max(0, s0 - NODE_MAX)
    if s0 - a < NODE_MIN:
        return False
    floor = base * (1.0 - SW_HI / 100.0)
    width = base * NODE_BIN
    nb = int(math.ceil((base - floor) / width))
    bins = [0.0] * nb
    for y in range(a, s0):
        l, h, v = lo[y], hi[y], vo[y]
        if not (v > 0) or h < floor or l >= base:
            continue
        for k in range(nb):
            b0, b1 = floor + k * width, min(base, floor + (k + 1) * width)
            if h <= l:
                share = 1.0 if b0 <= l < b1 else 0.0
            else:
                share = max(0.0, min(h, b1) - max(l, b0)) / (h - l)
            bins[k] += v * share
    if max(bins) <= 0:
        return False
    k = max(range(nb), key=lambda i: bins[i])
    return float(sweep_low) <= floor + (k + 1) * width


def b_candle(df, x):
    o, h, l, c = (float(df[k].iloc[x]) for k in ("Open", "High", "Low", "Close"))
    rng = h - l
    return rng > 0 and (min(o, c) - l) >= WICK_MIN * rng and c >= l + 0.5 * rng


def boosters(L, df, rows, x, st_):
    return {"VOL": b_vol(L, rows, x), "NODE": b_node(df, x, st_["base"], st_["sweep_low"]), "CANDLE": b_candle(df, x)}


def passes(bst, combo):
    return all(bst.get(b) for b in combo)


# ── frequency metrics and the selection rule (pure) ──────────────────────────────────────────────────────
def freq_metrics(counts):
    """counts: per-session trigger counts (unknown days excluded upstream) ⟶ the F1-F4 readings."""
    if not counts:
        return None
    roll = [sum(counts[i:i + 3]) for i in range(len(counts) - 2)]
    run = best = 0
    for v in counts:
        run = run + 1 if v == 0 else 0
        best = max(best, run)
    m = {"sessions": len(counts), "total": sum(counts), "median": st.median(counts), "min": min(counts), "max": max(counts),
         "zero_days": sum(1 for v in counts if v == 0), "longest_silence": best,
         "roll3_median": st.median(roll) if roll else None}
    m["F1"] = m["median"] <= F1_MED_MAX
    m["F2"] = m["roll3_median"] is not None and m["roll3_median"] >= F2_ROLL_MIN
    m["F3"] = m["longest_silence"] <= F3_SILENCE_MAX
    m["F4"] = m["max"] <= F4_DAY_MAX
    m["pass"] = m["F1"] and m["F2"] and m["F3"] and m["F4"]
    return m


def select(metrics_by_combo):
    """The pre-registered rule: core passes ⟶ core · core dry (F2/F3) ⟶ stop · core crowded ⟶ first passing combo in ORDER."""
    core = metrics_by_combo.get(())
    if core is None:
        return None, "NO_DATA"
    if core["pass"]:
        return (), "CORE"
    if not (core["F2"] and core["F3"]):
        return None, "DRY"
    for combo in ORDER[1:]:
        m = metrics_by_combo.get(combo)
        if m and m["pass"]:
            return combo, "BOOSTED"
    return None, "NONE_PASSES"


def wilson(k, n, z=1.959964):
    if n <= 0:
        return None
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, c - h), min(1.0, c + h)


def c1(k_trig, k_ready, n):
    """C1: Wilson lower bound of the trigger's symbol capture above the ready's Wilson upper bound AND above 0.7 % ·
    under the floor ⟶ None (no measure)."""
    if n < FLOOR_SYMS:
        return None
    lo_t = wilson(k_trig, n)[0]
    hi_r = wilson(k_ready, n)[1]
    return lo_t > hi_r and lo_t > PUBLISHED_READY


def mde_symbols(k_ready, n):
    """Smallest number of captured symbols that would pass C1 with this n."""
    for k in range(0, n + 1):
        if c1(k, k_ready, n):
            return k
    return None


def best_failure(day_rows):
    """Missed attribution: the day that went furthest along ②⟶③⟶④⟶①⟶⑤ and its first failing step."""
    rank = {"no_cycle": 0, "no_retest": 1, "shallow": 2, "deep": 2, "not_reclaimed": 3, "not_first": 4, "booster": 5,
            "not_member": 6, "member_unknown": 6, "cancelled": 7}
    best = None
    for r in day_rows:
        why = r.get("fail")
        if why is None or why not in rank:
            continue
        if best is None or rank[why] > rank[best["fail"]]:
            best = r
    return best


# ── membership (git snapshots, no look-ahead) ───────────────────────────────────────────────────────────
def watchlist_history():
    """[(commit_time_utc, {sym: entry})] of weekly_watchlist.json on origin/main — active stocks only."""
    import gen5_test as T
    out = []
    for line in T._git("log", "origin/main", "--format=%H %cI", "--since=2026-06-01", "--", "weekly_watchlist.json").splitlines():
        h, t = line.split()
        try:
            d = json.loads(T._git("show", f"{h}:weekly_watchlist.json"))
        except Exception:                                        # noqa: BLE001
            continue
        stocks = {s["symbol"]: s for s in (d.get("stocks") or []) if isinstance(s, dict) and s.get("status") == "active"}
        out.append((dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc), stocks))
    return sorted(out, key=lambda x: x[0])


def membership(T, S, nwh, wlh, t, nxt):
    """Q(t) and its parts from the snapshot committed after the close of t and before the next open (gen5_test.pre_open)."""
    nw = T.pre_open(nwh, t, nxt)
    wl = T.pre_open(wlh, t, nxt)
    out = {"nw_known": nw is not None, "wl_known": wl is not None,
           "NW": set(nw[2]) if nw else set(), "WL": set(wl[1]) if wl else set(), "READY": set()}
    if wl:
        for s, e in wl[1].items():
            try:
                if S.entry_status(e).get("status") == "ready_now":
                    out["READY"].add(s)
            except Exception:                                    # noqa: BLE001
                pass
    out["Q"] = out["NW"] | out["WL"]
    out["known"] = out["nw_known"] and out["wl_known"]   # «not a member» needs both snapshots; a name found in either counts
    return out


def sessions(lo, hi):
    import market_calendar as MC
    d, out = dt.date.fromisoformat(lo), []
    while d <= dt.date.fromisoformat(hi):
        if d.weekday() < 5 and d.isoformat() not in MC.HOLIDAYS:
            out.append(d.isoformat())
        d += dt.timedelta(days=1)
    return out


def frame(rows):
    import pandas as pd
    df = pd.DataFrame([r[:6] for r in rows], columns=["Date", "Open", "High", "Low", "Close", "Volume"])
    df.index = pd.to_datetime(df["Date"])
    return df[["Open", "High", "Low", "Close", "Volume"]].astype(float)


# ── stage A ─────────────────────────────────────────────────────────────────────────────────────────────
def stage_a(S, T, L, fresh, splits, nwh, wlh):
    days = sessions(*WIN_A)
    nxt = {d: n for d, n in zip(days, days[1:] + sessions("2026-10-14", "2026-10-20")[:1])}
    mem = {d: membership(T, S, nwh, wlh, d, nxt[d]) for d in days}
    trig = {d: [] for d in days}                 # (sym, boosters, base, sweep_low, depth)
    state_cnt = {d: 0 for d in days}
    unknown = {"short_or_split": 0, "member_unknown_days": [d for d in days if not mem[d]["known"]]}
    for sym, rows in fresh.items():
        if len(rows) < MIN_BARS + 1:
            continue
        df = frame(rows)
        ix = {r[0]: i for i, r in enumerate(rows)}
        cy = Cycle(df, S.pivot_cycle_state)
        hrows = hist_rows(df)
        for d in days:
            x = ix.get(d)
            if x is None:
                continue
            if X.split_unadjusted(rows, splits.get(sym), rows[max(0, x - MIN_BARS - 20)][0], d):
                unknown["short_or_split"] += 1
                continue
            s_ = day_state(cy, x)
            if s_["status"] == "UNKNOWN":
                unknown["short_or_split"] += 1
                continue
            if sym in mem[d]["Q"] and S._cycle_sweep_reclaimed(cy.pc(x)):
                state_cnt[d] += 1
            if s_["status"] == "TRIGGER":
                trig[d].append({"sym": sym, "base": s_["base"], "sweep_low": s_["sweep_low"], "depth": s_["depth"],
                                **boosters(L, df, hrows, x, s_)})
    known_days = [d for d in days if mem[d]["known"]]
    table = {}

    def row(name, sel):
        cnt = [sum(1 for e in trig[d] if sel(d, e)) for d in known_days]
        table[name] = freq_metrics(cnt)
        table[name]["daily"] = dict(zip(known_days, cnt))

    row("ALL_COVERED_core", lambda d, e: True)
    for combo in ORDER:
        row("Q_core" + "".join("+" + b for b in combo), lambda d, e, c=combo: e["sym"] in mem[d]["Q"] and passes(e, c))
    row("Q_NW_core", lambda d, e: e["sym"] in mem[d]["NW"])
    row("Q_WL_core", lambda d, e: e["sym"] in mem[d]["WL"])
    row("Q_READY_core", lambda d, e: e["sym"] in mem[d]["READY"])
    sc = [state_cnt[d] for d in known_days]
    table["PROD_SWEEP_STATE_Q"] = freq_metrics(sc)
    table["PROD_SWEEP_STATE_Q"]["daily"] = dict(zip(known_days, sc))
    live = live_sweeps(wlh, days)
    lc = [live.get(d, 0) for d in known_days]
    table["LIVE_SWEEP_FINGERPRINTS"] = freq_metrics(lc)
    table["LIVE_SWEEP_FINGERPRINTS"]["daily"] = dict(zip(known_days, lc))
    alln = table["ALL_COVERED_core"]["total"]
    table["ALL_COVERED_core"]["share_on_Q"] = (round(table["Q_core"]["total"] / alln, 4) if alln else None)
    by_combo = {combo: table["Q_core" + "".join("+" + b for b in combo)] for combo in ORDER}
    chosen, why = select(by_combo)
    names = {d: sorted(e["sym"] for e in trig[d] if e["sym"] in mem[d]["Q"]) for d in known_days}
    return {"sessions": days, "known_days": known_days, "unknown": unknown,
            "q_size": {d: len(mem[d]["Q"]) for d in days}, "nw_size": {d: len(mem[d]["NW"]) for d in days},
            "ready_size": {d: len(mem[d]["READY"]) for d in days}, "table": table,
            "selected": list(chosen) if chosen is not None else None, "selection": why, "q_trigger_names": names,
            "q_triggers": {d: [e for e in trig[d] if e["sym"] in mem[d]["Q"]] for d in known_days}}


def live_sweeps(wlh, days):
    seen = set()
    for _t, stocks in wlh:
        for s, e in stocks.items():
            la = (e.get("live_alert") or {}).get("sweep")
            if la in days:
                seen.add((s, la))
    out = {}
    for _s, d in seen:
        out[d] = out.get(d, 0) + 1
    return out


# ── stage B ─────────────────────────────────────────────────────────────────────────────────────────────
def population():
    rows = list(csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "READY_NOW_MISSED_SIGNALS.csv"), encoding="utf-8")))
    pop = [r for r in rows if r["NEAR_WATCH_14D"] in ("INSIDE", "OVERSOLD")]
    return pop


def stage_b(S, T, F, H, L, nwh, wlh, combo):
    D = F.Data()
    pop = population()
    stats = [F.row_stats(D, r["SYMBOL"], r["EXPL_DATE"]) for r in pop]
    events, acc = H.build_events(D, pop, stats, "O")
    out_ev = []
    for ev in events:
        s = ev["sym"]
        df = D.arch.get(s)
        rows = [[d.date().isoformat(), 0, 0, 0, float(c), 0] for d, c in zip(df.index, df["Close"])]
        k = ev["k"]
        cy = Cycle(df, S.pivot_cycle_state)
        free = Cycle(df, S.pivot_cycle_state, sweep=99)
        hrows = hist_rows(df)
        days, captured, depth_free = [], None, []
        ready_hit = False
        for x in range(k - LEAD, k):
            d = rows[x][0]
            nxt = rows[x + 1][0]
            m = membership(T, S, nwh, wlh, d, nxt)
            ready_hit = ready_hit or s in m["READY"]
            pf = free.pc(x) if x + 1 >= MIN_BARS else None
            if pf and int(pf.get("stage") or 0) >= 3 and pf.get("branch") == "sweep":
                depth_free.append(float(pf.get("sweep_pct") or 0.0))
            if X.split_unadjusted(rows, D.splits.get(s), rows[max(0, x - MIN_BARS - 20)][0], d):
                days.append({"day": d, "fail": None, "unknown": "split"})
                continue
            s_ = day_state(cy, x)
            if s_["status"] == "UNKNOWN":
                days.append({"day": d, "fail": None, "unknown": s_["reason"]})
                continue
            fail = s_["reason"] if s_["status"] in ("NO", "NOT_FIRST") else None
            bst = boosters(L, df, hrows, x, s_) if s_["status"] == "TRIGGER" else {}
            if fail is None and combo and not passes(bst, combo):
                fail = "booster"
            if fail is None and s not in m["Q"]:
                fail = "not_member" if m["known"] else "member_unknown"
            if fail is None and cancelled(cy.close, x, k - 1, s_["sweep_low"]):
                fail = "cancelled"
            row = {"day": d, "fail": fail, "lead": k - x, "depth": s_.get("depth"), "base": s_.get("base"),
                   "sweep_low": s_.get("sweep_low"), **{b: bst.get(b) for b in BOOSTERS}}
            days.append(row)
            if fail is None and captured is None:
                captured = row
        out_ev.append({"sym": s, "A": ev["A"], "E_reg": ev["E_reg"], "identity": ev["identity"], "seed": s in FIVE,
                       "captured": captured, "best_fail": None if captured else best_failure(days),
                       "unknown_days": sum(1 for r in days if r.get("unknown")), "ready_in_window": ready_hit,
                       "depth_free_max": max(depth_free) if depth_free else None})
    return D, events, acc, out_ev


def depth_summary(evs):
    v = sorted(e["depth_free_max"] for e in evs if e["depth_free_max"] is not None)
    none = sum(1 for e in evs if e["depth_free_max"] is None)

    def q(p):
        if not v:
            return None
        i = (len(v) - 1) * p
        lo, hi = int(math.floor(i)), int(math.ceil(i))
        return round(v[lo] + (v[hi] - v[lo]) * (i - lo), 2)
    return {"n": len(v), "no_sweep": none, "median": q(0.5), "q1": q(0.25), "q3": q(0.75),
            "under_7": sum(1 for x in v if x < SW_LO), "in_band": sum(1 for x in v if SW_LO <= x <= SW_HI),
            "over_13": sum(1 for x in v if x > SW_HI)}


def by_symbol(evs, key):
    syms = {}
    for e in evs:
        syms[e["sym"]] = syms.get(e["sym"], False) or bool(key(e))
    return syms


def false_alarms(S, T, L, D, nwh, wlh, combo):
    days = [d for d in D.cal if FA_WIN[0] <= d <= FA_WIN[1]]
    rows_out, fired = [], 0
    mem = {d: membership(T, S, nwh, wlh, d, D.cal[D.cix[d] + 1]) for d in days}
    syms = set().union(*[m["Q"] for m in mem.values()])
    for s in sorted(syms):
        df = D.arch.get(s)
        if df is None:
            continue
        ix = {d.date().isoformat(): i for i, d in enumerate(df.index)}
        crow = [[d.date().isoformat(), 0, 0, 0, float(c), 0] for d, c in zip(df.index, df["Close"])]
        cy = Cycle(df, S.pivot_cycle_state)
        hrows = hist_rows(df)
        fr = D.fresh.get(s)
        sess, cov = D.ext_sess(s)
        for d in days:
            x = ix.get(d)
            if x is None or s not in mem[d]["Q"]:
                continue
            if X.split_unadjusted(crow, D.splits.get(s), crow[max(0, x - MIN_BARS - 20)][0], d):
                continue
            s_ = day_state(cy, x)
            if s_["status"] != "TRIGGER":
                continue
            bst = boosters(L, df, hrows, x, s_)
            if combo and not passes(bst, combo):
                continue
            fired += 1
            fi = D.fidx(s, d) if fr else None
            stx = X.explosion_stats(fr, sess, cov, fi, fi + 1, FWD - 1) if fi is not None else None
            if stx is None:
                outcome = "UNKNOWN"
            elif stx["realized_idx"] is not None:
                outcome = "REACHED_2X"
            elif stx["days"] < FWD or not stx["complete"]:
                outcome = "UNKNOWN"
            else:
                outcome = "FALSE"
            rows_out.append({"sym": s, "day": d, "depth": s_["depth"], "outcome": outcome,
                             "ext_peak": stx["ext_peak"] if stx else None, **bst})
    return rows_out


# ── today's layer ② (display only) ──────────────────────────────────────────────────────────────────────
def today_layer2(S, T, fresh, wlh, nwh):
    t = max(r[-1][0] for r in fresh.values() if r)
    snap = wlh[-1][1] if wlh else {}
    out = []
    for s, e in sorted(snap.items()):
        try:
            ready = S.entry_status(e).get("status") == "ready_now"
        except Exception:                                        # noqa: BLE001
            ready = False
        rows = fresh.get(s)
        if not rows:
            out.append({"sym": s, "ready": ready, "note": "no_bars"})
            continue
        df = frame(rows)
        df = df[df.index <= t]
        pc = S.pivot_cycle_state(df)
        rsi = S.rsi(df["Close"]).iloc[-1] if len(df) > 20 else None
        out.append({"sym": s, "ready": ready, "asof": df.index[-1].date().isoformat(), "rsi": None if rsi is None else round(float(rsi), 1),
                    "stage": pc.get("stage") if pc else None, "held": pc.get("held") if pc else None,
                    "bounce": pc.get("bounce_pct") if pc else None, "vs_bottom": pc.get("vs_bottom_pct") if pc else None,
                    "missing": gaps(rsi, pc)})
    return {"asof": t, "watchlist": out, "near_watch_today": len(nwh[-1][2]) if nwh else None}


def gaps(rsi, pc):
    """«باقي له» at Faisal's thresholds (display): RSI 23-27 · hold 5 · test rise 15-20 % · zone ≤ 15 % above the bottom."""
    out = []
    if rsi is not None and float(rsi) > 27:
        out.append(f"RSI باقي {float(rsi) - 27:.1f} نقطة إلى 27")
    if pc:
        if int(pc.get("stage") or 0) < 2 or float(pc.get("bounce_pct") or 0) < 15:
            out.append(f"ارتداد الاختبار {float(pc.get('bounce_pct') or 0):.0f}% من 15-20%")
        if int(pc.get("stage") or 0) >= 3 and int(pc.get("held") or 0) < 5:
            out.append(f"الثبات {int(pc.get('held') or 0)} من 5 جلسات")
        vb = pc.get("vs_bottom_pct")
        if vb is not None and float(vb) > 15:
            out.append(f"فوق المنطقة بـ{float(vb) - 15:.1f}%")
    else:
        out.append("لا دورة ارتكاز مقروءة")
    return out


# ── the sealed run ──────────────────────────────────────────────────────────────────────────────────────
def run():
    check_pins()
    check_merged()
    S, T, F, H, L = _mods()
    cwd = os.getcwd()
    os.chdir(ROOT)
    try:
        e = X.load()
        fresh = e["daily"]
        splits = G.load_splits()
        nwh = T.nearwatch_history()
        wlh = watchlist_history()
        a = stage_a(S, T, L, fresh, splits, nwh, wlh)
        combo = tuple(a["selected"]) if a["selected"] is not None else ()
        D, events, acc, evs = stage_b(S, T, F, H, L, nwh, wlh, combo)
        fa = false_alarms(S, T, L, D, nwh, wlh, combo)
        today = today_layer2(S, T, fresh, wlh, nwh)
    finally:
        os.chdir(cwd)
    res = verdict_block(a, events, acc, evs, fa, combo)
    res["stage_a"] = {k: v for k, v in a.items() if k != "q_triggers"}
    res["stage_a"]["q_triggers"] = {d: v for d, v in a["q_triggers"].items()}
    res["today_layer2"] = today
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(res, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    write_csvs(res, evs, fa)
    report(res)
    return res


def verdict_block(a, events, acc, evs, fa, combo):
    cap = by_symbol(evs, lambda e: e["captured"] is not None)
    rdy = by_symbol(evs, lambda e: e["ready_in_window"])
    n = len(cap)
    k_t, k_r = sum(cap.values()), sum(rdy.values())
    no5 = [e for e in evs if not e["seed"]]
    cap5 = by_symbol(no5, lambda e: e["captured"] is not None)
    rdy5 = by_symbol(no5, lambda e: e["ready_in_window"])
    resolved = [r for r in fa if r["outcome"] != "UNKNOWN"]
    fals = [r for r in resolved if r["outcome"] == "FALSE"]
    a_pass = a["selected"] is not None
    c1v = c1(k_t, k_r, n)
    if not a_pass:
        verdict = "A-FAIL"
    elif c1v is None:
        verdict = "NO-MEASURE"
    elif c1v:
        verdict = "PASS"
    else:
        verdict = "B-FAIL"
    fails = {}
    for e in evs:
        if e["captured"] is None:
            w = (e["best_fail"] or {}).get("fail") or "no_readable_day"
            fails[w] = fails.get(w, 0) + 1
    return {"prereg_sha256": PREREG_SHA256, "verdict": verdict, "selection": a["selection"],
            "selected_combo": list(combo) if a_pass else None,
            "stage_b": {"events": len(evs), "symbols": n, "captured_symbols": k_t, "ready_symbols": k_r,
                        "capture_wilson": wilson(k_t, n), "ready_wilson": wilson(k_r, n), "C1": c1v,
                        "mde_symbols": mde_symbols(k_r, n) if n else None,
                        "without_five": {"symbols": len(cap5), "captured": sum(cap5.values()), "ready": sum(rdy5.values()),
                                         "C1": c1(sum(cap5.values()), sum(rdy5.values()), len(cap5))},
                        "missed_by_condition": fails, "depth": depth_summary(evs),
                        "accounting": {k: (len(v) if isinstance(v, list) else v) for k, v in acc.items()},
                        "excluded": {k: v for k, v in acc.items() if isinstance(v, list) and v},
                        "false_alarms": {"fired": len(fa), "resolved": len(resolved), "false": len(fals),
                                         "rate": round(len(fals) / len(resolved), 4) if resolved else None,
                                         "symbols_fired": len({r["sym"] for r in fa}),
                                         "symbols_false_only": len({r["sym"] for r in fals} - {r["sym"] for r in resolved
                                                                                              if r["outcome"] == "REACHED_2X"})}},
            "events": evs}


def write_csvs(res, evs, fa):
    with open(A_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        tab = res["stage_a"]["table"]
        names = list(tab)
        w.writerow(["day"] + names)
        for d in res["stage_a"]["known_days"]:
            w.writerow([d] + [tab[n]["daily"].get(d) for n in names])
    with open(B_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sym", "onset_O", "expl_date", "seed", "captured", "trigger_day", "sessions_before_O", "depth", "VOL", "NODE",
                    "CANDLE", "missed_condition", "missed_day", "ready_in_window", "depth_free_max", "unknown_days"])
        for e in evs:
            c, b = e["captured"] or {}, e["best_fail"] or {}
            w.writerow([e["sym"], e["A"], e["E_reg"], e["seed"], bool(e["captured"]), c.get("day"), c.get("lead"), c.get("depth"),
                        c.get("VOL"), c.get("NODE"), c.get("CANDLE"), b.get("fail"), b.get("day"), e["ready_in_window"],
                        e["depth_free_max"], e["unknown_days"]])
    with open(FA_CSV, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["sym", "trigger_day", "depth", "outcome", "ext_peak", "VOL", "NODE", "CANDLE"])
        for r in fa:
            w.writerow([r["sym"], r["day"], r["depth"], r["outcome"], r["ext_peak"], r["VOL"], r["NODE"], r["CANDLE"]])


def report(res):
    print("verdict", res["verdict"], "selection", res["selection"], "combo", res["selected_combo"])
    for n, m in res["stage_a"]["table"].items():
        print(f"{n:28s} med {m['median']} range {m['min']}-{m['max']} zero {m['zero_days']} silence {m['longest_silence']} "
              f"roll3 {m['roll3_median']} total {m['total']} pass {m['pass']}")
    b = res["stage_b"]
    print("stage B", {k: b[k] for k in ("events", "symbols", "captured_symbols", "ready_symbols", "C1", "mde_symbols")})
    print("false alarms", b["false_alarms"], "depth", b["depth"])


# ── synthetic guards ────────────────────────────────────────────────────────────────────────────────────
def _syn(path, vols=None):
    """A daily frame from a list of (low, high, close) with open = previous close; volumes default 1000."""
    import pandas as pd
    o, rows = None, []
    for i, (lo, hi, c) in enumerate(path):
        op = c if o is None else o
        rows.append([op, max(hi, op, c), min(lo, op, c), c, (vols[i] if vols else 1000.0)])
        o = c
    idx = pd.bdate_range("2026-01-02", periods=len(rows))
    return pd.DataFrame(rows, columns=["Open", "High", "Low", "Close", "Volume"], index=idx)


def _base_path(n_pre=55):
    """n_pre gently falling bars, a bottom at 1.00, a 15 % test rise, a drift back to 1.04."""
    p = [(1.30 - 0.004 * i, 1.32 - 0.004 * i, 1.31 - 0.004 * i) for i in range(n_pre)]
    p += [(1.00, 1.08, 1.05)]
    p += [(1.04 + 0.01 * i, 1.08 + 0.01 * i, 1.07 + 0.01 * i) for i in range(8)]    # high reaches 1.15
    p += [(1.12 - 0.02 * i, 1.15 - 0.02 * i, 1.13 - 0.02 * i) for i in range(4)]    # back to ≈1.06
    return p


def guards():
    S, T, F, H, L = _mods()
    fails = []

    def chk(name, ok):
        print(("✅ " if ok else "❌ ") + name)
        if not ok:
            fails.append(name)

    pcf = S.pivot_cycle_state
    # core23 reasons and band edges
    base = {"stage": 3, "branch": "sweep", "bottom": 1.0}
    chk("LG1 core23: none ⟶ no_cycle · stage 2 ⟶ no_retest · hold branch ⟶ shallow · 6.99 ⟶ shallow · 7.00 and 13.00 in band · "
        "13.01 ⟶ deep · close = base ⟶ not reclaimed",
        core23(None, 1.1) == (False, "no_cycle") and core23({**base, "stage": 2}, 1.1) == (False, "no_retest")
        and core23({**base, "branch": "hold", "sweep_pct": 9}, 1.1) == (False, "shallow")
        and core23({**base, "sweep_pct": 6.99}, 1.1) == (False, "shallow")
        and core23({**base, "sweep_pct": 7.0}, 1.01) == (True, None) and core23({**base, "sweep_pct": 13.0}, 1.01) == (True, None)
        and core23({**base, "sweep_pct": 13.01}, 1.01) == (False, "deep") and core23({**base, "sweep_pct": 9}, 1.0)
        == (False, "not_reclaimed"))
    # single-candle sweep and reclaim
    p1 = _base_path() + [(0.90, 1.05, 1.02)]
    df1 = _syn(p1)
    s1 = day_state(Cycle(df1, pcf), len(p1) - 1)
    chk("LG2 one candle sweeps 10 % under the base and closes above it ⟶ TRIGGER · depth 10 · sweep low 0.90",
        s1["status"] == "TRIGGER" and abs(s1["depth"] - 10.0) < 1e-6 and abs(s1["sweep_low"] - 0.90) < 1e-9)
    # multi-day: sweep then a close under, then the reclaim
    p2 = _base_path() + [(0.91, 1.03, 0.95), (0.92, 0.99, 0.97), (0.96, 1.06, 1.03)]
    df2 = _syn(p2)
    cy2 = Cycle(df2, pcf)
    st2 = [day_state(cy2, x)["status"] for x in range(len(p2) - 3, len(p2))]
    chk("LG3 two days under the base then the first close above ⟶ TRIGGER on the reclaim day only", st2 == ["NO", "NO", "TRIGGER"])
    # second reclaim of the same base is not a trigger
    p3 = p2 + [(0.95, 1.00, 0.98), (0.97, 1.07, 1.04)]
    df3 = _syn(p3)
    cy3 = Cycle(df3, pcf)
    chk("LG4 a second reclaim of the same base ⟶ NOT_FIRST (one trigger per base)",
        day_state(cy3, len(p3) - 1)["status"] == "NOT_FIRST" and day_state(cy3, len(p3) - 3)["status"] == "TRIGGER")
    # shallow (5 %) and deep (16 %) sweeps
    p4 = _base_path() + [(0.95, 1.04, 1.02)]
    p5 = _base_path() + [(0.84, 1.04, 1.02)]
    chk("LG5 a 5 % sweep is noise (shallow) · a 16 % sweep breaks the base (no trigger)",
        day_state(Cycle(_syn(p4), pcf), len(p4) - 1)["status"] == "NO"
        and day_state(Cycle(_syn(p5), pcf), len(p5) - 1)["status"] == "NO")
    # no test rise before the sweep ⟶ no cycle step 3
    p6 = [(1.30 - 0.004 * i, 1.32 - 0.004 * i, 1.31 - 0.004 * i) for i in range(55)] + [(1.00, 1.03, 1.02)] \
        + [(1.01, 1.04, 1.03)] * 6 + [(0.90, 1.05, 1.02)]
    chk("LG6 no 10 % test rise before the dip ⟶ no trigger (cycle step 2 missing)",
        day_state(Cycle(_syn(p6), pcf), len(p6) - 1)["status"] == "NO")
    # history floor and no look-ahead
    chk("LG7 fewer than 60 bars ⟶ UNKNOWN", day_state(Cycle(_syn(p1[-50:]), pcf), 49)["status"] == "UNKNOWN")
    p7 = p1 + [(1.03, 1.10, 1.08)] * 5
    chk("LG8 no look-ahead: the reading at t is the same with or without later bars",
        day_state(Cycle(_syn(p7), pcf), len(p1) - 1) == s1)
    chk("LG9 cancellation: a later close under the sweep low cancels · above it does not",
        cancelled([1, 1.02, 0.89], 1, 2, 0.90) and not cancelled([1, 1.02, 0.91], 1, 2, 0.90))
    # boosters
    v = [1000.0] * (len(p1) - 1) + [3500.0]
    dfv = _syn(p1, v)
    chk("LG10 VOL by link100.daily_feats: 3.5× the median of t−19…t−5 ⟶ True · 2.5× ⟶ False",
        b_vol(L, hist_rows(dfv), len(p1) - 1) and not b_vol(L, hist_rows(_syn(p1, v[:-1] + [2500.0])), len(p1) - 1))
    pn = _base_path(130)
    pn = [(0.92, 0.96, 0.94)] * 0 + pn
    dn = _syn([(0.93, 0.97, 0.95)] * 70 + pn[70:] + [(0.90, 1.05, 1.02)])
    xn = len(dn) - 1
    ds = _syn([(0.93, 0.97, 0.95)] * 20 + [(1.02, 1.06, 1.04)] * 25 + [(0.90, 1.05, 1.02)])
    chk("LG11 NODE: prior volume traded at 0.93-0.97 below the base · a sweep to 0.90 reaches it · a sweep to 0.98 does not · "
        "no volume under the base ⟶ False · the same node with only 45 bars before the sweep ⟶ False (60 required)",
        b_node(dn, xn, 1.00, 0.90) and not b_node(dn, xn, 1.00, 0.98) and not b_node(df1, len(p1) - 1, 1.00, 0.90)
        and not b_node(ds, len(ds) - 1, 1.00, 0.90))
    chk("LG12 CANDLE: hammer (long lower wick, close high) ⟶ True · close at the low ⟶ False · "
        "a full green body (close high, wick 1 %) ⟶ False",
        b_candle(_syn([(0.90, 1.05, 1.04)] * 2), 1) and not b_candle(_syn([(1.04, 1.05, 1.04), (0.90, 1.05, 0.91)]), 1)
        and not b_candle(_syn([(0.91, 0.92, 0.91), (0.90, 1.05, 1.04)]), 1))
    # frequency metrics and the selection rule
    m = freq_metrics([0, 1, 2, 0, 0, 0, 0, 1, 3])
    chk("LG13 metrics: median 0 · max 3 · zero days 5 · longest silence 4 · rolling-3 sums 3,3,2,0,0,1,4 ⟶ median 2",
        m["median"] == 0 and m["max"] == 3 and m["zero_days"] == 5 and m["longest_silence"] == 4 and m["roll3_median"] == 2
        and m["F1"] and m["F3"] and m["F4"] and m["F2"])
    m5 = freq_metrics([1, 0, 0, 0, 0, 0, 1])
    chk("LG14 a 5-session silence fails F3 · median 3 fails F1 · a day of 5 fails F4 · edges pass (median 2 · a day of 4)",
        not m5["F3"] and not freq_metrics([3, 3, 3])["F1"] and not freq_metrics([1, 5, 1])["F4"]
        and freq_metrics([2, 2, 2])["F1"] and freq_metrics([1, 4, 1])["F4"])
    ok_m, crowd, dry = freq_metrics([1, 1, 1]), freq_metrics([3, 4, 3]), freq_metrics([0, 0, 0, 0, 0, 1])
    chk("LG15 selection: core passes ⟶ core · core dry ⟶ stop · core crowded ⟶ the first passing combo in the written order",
        select({(): ok_m})[1] == "CORE" and select({(): dry})[1] == "DRY"
        and select({(): crowd, ("VOL",): crowd, ("NODE",): ok_m, ("CANDLE",): ok_m}) == (("NODE",), "BOOSTED")
        and select({(): crowd, ("VOL",): crowd})[1] == "NONE_PASSES")
    chk("LG16 C1: Wilson lower bound of the trigger over the ready's upper bound · under 20 symbols ⟶ None (no measure)",
        c1(10, 1, 50) is True and c1(3, 1, 50) is False and c1(10, 1, 19) is None and mde_symbols(1, 50) is not None)
    # membership from snapshots (no look-ahead)
    t0 = dt.datetime(2026, 9, 17, 7, 0, tzinfo=dt.timezone.utc)
    nwh = [(t0, "2026-09-17", {"AAA": {}})]
    wlh = [(t0, {"BBB": {"interp": {"mode": "near_support"}}})]
    m_in = membership(T, S, nwh, wlh, "2026-09-16", "2026-09-17")
    m_out = membership(T, S, nwh, wlh, "2026-09-17", "2026-09-18")
    m_half = membership(T, S, nwh, [], "2026-09-16", "2026-09-17")
    chk("LG17 membership = the snapshot between the close of t and the next open (pre_open) · none ⟶ unknown · "
        "only the near_watch snapshot ⟶ its names are members but «not a member» stays unknown",
        m_in["Q"] == {"AAA", "BBB"} and m_in["known"] and not m_out["known"] and m_out["Q"] == set()
        and m_half["Q"] == {"AAA"} and not m_half["known"])
    chk("LG18 missed attribution takes the furthest step: not_member beats not_reclaimed beats shallow",
        (best_failure([{"fail": "shallow", "day": "a"}, {"fail": "not_member", "day": "x"}, {"fail": "not_reclaimed", "day": "b"}])
         or {}).get("day") == "x")
    deep = _base_path() + [(0.84, 1.04, 0.95)]
    pf = Cycle(_syn(deep), pcf, sweep=99).pc(len(deep) - 1)
    chk("LG19 the free depth (sweep = 99, by name) keeps a 16 % sweep on the same base",
        pf is not None and abs(float(pf["sweep_pct"]) - 16.0) < 1e-6)

    def code(fn):
        try:
            fn()
            return 0
        except SystemExit as e:
            return e.code
    pinned = open(PREREG, "rb").read() if os.path.exists(PREREG) else b""
    chk("LG20 merged gate: absent ⟶ 9 · altered ⟶ 9 · pinned bytes ⟶ passes",
        code(lambda: check_merged(lambda: None)) == 9 and code(lambda: check_merged(lambda: pinned + b" ")) == 9
        and (code(lambda: check_merged(lambda: pinned)) == 0) == (hashlib.sha256(pinned).hexdigest() == PREREG_SHA256))
    chk("LG21 constants (band 7/13 · 60 bars · windows · F 2/1/4/4 · floor 20 · node 120/60/1 % · wick 50 %)",
        (SW_LO, SW_HI, MIN_BARS, WIN_A, FA_WIN, LEAD, FWD, F1_MED_MAX, F2_ROLL_MIN, F3_SILENCE_MAX, F4_DAY_MAX, FLOOR_SYMS,
         NODE_MAX, NODE_MIN, NODE_BIN, WICK_MIN)
        == (7.0, 13.0, 60, ("2026-09-16", "2026-10-13"), ("2026-08-17", "2026-09-15"), 20, 20, 2, 1, 4, 4, 20, 120, 60, 0.01, 0.5))
    chk("LG22 the stage A window is 20 sessions", len(sessions(*WIN_A)) == 20)
    print(f"\nguards failed: {len(fails)}")
    return fails


if __name__ == "__main__":
    if "--guards" in sys.argv:
        sys.exit(1 if guards() else 0)
    run()
