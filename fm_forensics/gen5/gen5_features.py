"""GEN5 — shared point-in-time features (research only · no production import of this module).

Owner's prompt v4 (2026-10-13): generate a readiness combination on the five known stocks
(SXTC · DKI · RETO · DLXY · HUBC), freeze it, then test it on the bot-tracked pivot names that exploded.

Every feature at decision session t reads bars[0 .. t] only (the next open is the earliest action).
Production functions are called by name and are never modified here:
  Super_stock.pivot_stability · pivot_cycle_state · _cycle_sweep_reclaimed · rsi · _gaps_on_frame ·
  unfilled_gaps_above · spike_info · tested_level.
The identity gates (M1–M3 drop band) are NOT applied: research, per the owner's prompt §3-A.
"""
import gzip
import json
import math
import os
import sys

import numpy as np
import pandas as pd

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BARS_FILE = os.path.join(ROOT, "faisal_engine", "data", "rank", "bars.json.gz")
SPLITS_FILE = os.path.join(ROOT, "faisal_engine", "data", "rank", "splits.json")

_S = None


def S():
    """Import the production module once, with the live FAISAL_ONLY constants, from the repo root."""
    global _S
    if _S is None:
        os.environ["FAISAL_ONLY"] = "1"
        cwd = os.getcwd()
        try:
            os.chdir(ROOT)
            if ROOT not in sys.path:
                sys.path.insert(0, ROOT)
            import Super_stock as mod
            mod.log = lambda *a, **k: None
            _S = mod
        finally:
            os.chdir(cwd)
    return _S


def load_bars(symbols=None):
    """{sym: DataFrame(Open, High, Low, Close, Volume)} from the frozen TradingView archive (split-adjusted)."""
    raw = json.load(gzip.open(BARS_FILE, "rt", encoding="utf-8"))["daily"]
    out = {}
    for sym, rows in raw.items():
        if symbols is not None and sym not in symbols:
            continue
        if not rows:
            continue
        df = pd.DataFrame(rows, columns=["Date", "Open", "High", "Low", "Close", "Volume"])
        df.index = pd.to_datetime(df["Date"])
        out[sym] = df[["Open", "High", "Low", "Close", "Volume"]].astype(float)
    return out


def load_splits():
    return json.load(open(SPLITS_FILE, encoding="utf-8"))["splits"]


def _num(x, nd=2):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    return round(x, nd) if math.isfinite(x) else None


def features_at(df, i, splits=None):
    """Components at decision session index i (bars 0..i only). Returns a flat dict; unknown stays None."""
    mod = S()
    d = df.iloc[: i + 1]
    c = d["Close"].to_numpy(dtype=float)
    lo = d["Low"].to_numpy(dtype=float)
    v = d["Volume"].to_numpy(dtype=float)
    t = d.index[-1].date().isoformat()
    f = {"t": t, "close": _num(c[-1], 4)}
    # base stability (production pivot_stability: pivot low in PIVOT_LOOKBACK, held 3..STABILITY_MAX)
    st = mod.pivot_stability(lo, c) if len(c) >= 2 else None
    f["stab_bars_after"] = int(st["bars_after"]) if st else None
    f["stab_held"] = bool(st["held"]) if st else None
    # Faisal's pivot cycle (production pivot_cycle_state: 1 bottom · 2 bounce ≥10% · 3 retest · 4 hold after retest)
    pc = mod.pivot_cycle_state(d)
    f["pc_stage"] = int(pc["stage"]) if pc else None
    f["pc_branch"] = (pc.get("branch") or "") if pc else None
    f["pc_bounce"] = _num(pc.get("bounce_pct"), 1) if pc else None
    f["pc_typical"] = bool(pc.get("typical")) if pc else None
    f["pc_first_rise"] = bool(pc.get("first_rise")) if pc else None
    f["pc_sweep_pct"] = _num(pc.get("sweep_pct"), 2) if pc else None
    f["pc_held"] = int(pc.get("held") or 0) if pc else None
    f["pc_bottom_ago"] = int(pc.get("bottom_ago")) if pc else None
    f["pc_vs_bottom"] = _num(pc.get("vs_bottom_pct"), 1) if pc else None
    f["sweep_reclaimed"] = bool(mod._cycle_sweep_reclaimed(pc)) if pc else None
    # RSI
    r = mod.rsi(d["Close"].astype(float)) if len(c) >= 15 else None
    f["rsi"] = _num(r.iloc[-1], 1) if r is not None else None
    f["rsi_min20"] = _num(r.tail(20).min(), 1) if r is not None else None
    # volume of the decision day ÷ median of the 15 sessions t−19 .. t−5 (owner: «حجم أمس ÷ وسيط d−20..d−6»)
    if len(v) >= 20:
        base = np.median(v[-20:-5])
        f["vol_ratio"] = _num(v[-1] / base, 2) if base > 0 else None
    else:
        f["vol_ratio"] = None
    f["ret5"] = _num((c[-1] / c[-6] - 1.0) * 100.0, 2) if len(c) >= 6 and c[-6] > 0 else None
    # gaps: unfilled UP gap = gap below the price (support) · unfilled DOWN gap above the price (target zone)
    g = mod._gaps_on_frame(d, int(mod.CONFIG["GAP_LOOKBACK"]))
    f["gap_below_unfilled"] = bool(g.get("unfilled")) if g.get("count") else False
    ga = mod.unfilled_gaps_above(d, int(mod.CONFIG["GAP_LOOKBACK"]))
    f["gap_above_n"] = int(ga.get("count") or 0)
    f["gap_above_dist"] = _num(ga.get("nearest_dist_pct"), 1)
    # founding event: last reverse split on or before t · prior spike · drop from the 52-week high
    last_rs = None
    for dd, fac in (splits or []):
        if dd <= t and fac and float(fac) < 1.0:
            last_rs = dd
    f["days_since_rsplit"] = ((pd.Timestamp(t) - pd.Timestamp(last_rs)).days if last_rs else None)
    sp, nsp = mod.spike_info(c, exclude_last=int(mod.CONFIG["BASE_WINDOW"]))
    f["prior_spike"] = _num(sp, 0)                     # spike_info already returns percent
    hi52 = float(d["High"].tail(252).max())
    f["drop52"] = _num((1.0 - c[-1] / hi52) * 100.0, 1) if hi52 > 0 else None
    # frozen-axis information only (H6): does a two-touch tested level exist? never part of a rule here
    try:
        f["tested_level"] = bool(mod.tested_level(d))
    except Exception:                                            # noqa: BLE001
        f["tested_level"] = None
    return f


def fires(f):
    """Binary components (the candidates). None ⇒ unknown, never False."""
    def ok(*ks):
        return all(f.get(k) is not None for k in ks)
    st = f.get("pc_stage")
    return {
        "STAB3": (bool(f["stab_held"] and f["stab_bars_after"] >= 3) if ok("stab_held", "stab_bars_after") else None),
        "BOUNCE": (bool(st is not None and st >= 2 and not f["pc_first_rise"] and (f["pc_bounce"] or 0) >= 10)
                   if ok("pc_stage") else None),
        "RETEST": (bool(st is not None and st >= 3) if ok("pc_stage") else None),
        "STAGE4": (bool(st == 4) if ok("pc_stage") else None),
        "SWEEP": (bool(f["sweep_reclaimed"]) if ok("sweep_reclaimed") else None),
        "RSI33": (bool(f["rsi"] < 33) if ok("rsi") else None),
        "RSIMIN33": (bool(f["rsi_min20"] < 33) if ok("rsi_min20") else None),
    }
