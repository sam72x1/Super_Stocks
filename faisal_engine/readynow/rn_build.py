"""READYNOW — early technical readiness 7–10 sessions before a +70% move (research · offline · read-only).

Reuses, by import and without modification: READY70 (`faisal_engine/ready70/`: bars, splits, the bot's explosion
detector recomputed, the pivot-identity population `pi_obs.csv.gz`, its cycle-stage features) and SEQ70
(`faisal_engine/seq70/`: path descriptors `traj.csv.gz`, episodes with the alternative start `events.csv.gz`).

For every pivot-day it computes the source-backed conditions of `RN_SPEC.md` §2 from bars at or before that day only,
and the onset label: POS710 when a clean +70% episode starts (launch L = trough + 1, READY70) 7 to 10 sessions later.
For the four seeds and HUBC it writes every session from 2026-07-01, pivot or not.

Outputs (data/): rows.csv.gz · events.csv.gz · seeds.csv.gz · ewin.csv.gz · inventory.json
Run from the repo root:  python3 faisal_engine/readynow/rn_build.py   (--check verifies the outputs)
"""
import csv
import datetime as dt
import gzip
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
DATA = os.path.join(HERE, "data")
R70_DATA = os.path.join(ROOT, "faisal_engine", "ready70", "data")
S70_DATA = os.path.join(ROOT, "faisal_engine", "seq70", "data")
sys.path.insert(0, os.path.join(ROOT, "faisal_engine", "ready70"))
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import pandas as pd                                                       # noqa: E402
import r70_build as R                                                     # noqa: E402  (sealed READY70 code, read-only)

SEEDS = ("DLXY", "RETO", "DKI", "SXTC")
ACTIVE = ("HUBC",)
SEED_FROM = "2026-05-01"
LOOK_LOW = 25            # base-low window = the three-condition tool's PIVOT_LOOKBACK (S.CONFIG, 25)
RSI_OS = 33.0            # the tool's RSI limit = S.CONFIG["RSI_OVERSOLD"] (33)
BOOM_PCT = 50.0          # the tool's explosion limit = S.CONFIG["EXPLOSION_PCT"] (50)
BOOM_WIN = 5             # the tool's EXPLODE_WIN (5)
SPLIT_DAYS = 120         # S.CONFIG["SPLIT_LOOKBACK_DAYS"] (120)
H_LO, H_HI = 7, 10       # primary horizon: onset within sessions t+7 .. t+10
MAXGAP = 19              # max sessions from launch to first detection over all clean episodes (measured in inventory)
PI_COPY = ("px", "pc_stage", "pc_branch", "range20", "tl_dist", "loc", "bt_src", "bot_ready")
TR_COPY = ("spell", "split60", "v1x", "r5")


def _rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _r(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def series(b):
    """Causal indicator series over the whole adjusted history (value at i depends on bars ≤ i only)."""
    S = R.S()
    c = pd.Series(b["c"])
    out = {"rsi": S.rsi(c).to_numpy()}
    for n in (9, 12, 20, 26, 30, 50):
        out[f"ema{n}"] = c.ewm(span=n, adjust=False).mean().to_numpy()
    line = out["ema12"] - out["ema26"]
    out["macd"] = line
    out["macd_sig"] = pd.Series(line).ewm(span=9, adjust=False).mean().to_numpy()
    return out


def conditions(b, z, i, sdates):
    """The conditions of RN_SPEC §2 at session index i (bars ≤ i only; guarded by test_rn G1)."""
    if i < 60:
        return None
    c, h, lw, v = b["c"], b["h"], b["l"], b["v"]
    lo_w = lw[i - LOOK_LOW + 1: i + 1]
    low = float(lo_w.min())
    if not low > 0:
        return None
    lowday = i - LOOK_LOW + 1 + int(np.argmax(lo_w <= low))          # first session reaching the low
    hold_n = i - lowday
    held = bool(c[i] > low)
    bounce = float(h[lowday: i + 1].max()) / low - 1.0
    dist = float(c[i]) / low - 1.0
    # the tool's «exploded within a week», daily approximation: highs over the last 5 sessions vs the lowest close
    # before each day, starting from the close before the week (after-hours bars are not archived)
    ref = float(c[i - BOOM_WIN])
    best = -1e9
    for d in range(i - BOOM_WIN + 1, i + 1):
        if ref > 0:
            best = max(best, (float(h[d]) / ref - 1.0) * 100.0)
        ref = min(ref, float(c[d]))
    e9, e26 = z["ema9"], z["ema26"]
    up = e9[: i + 1] > e26[: i + 1]
    crossed = any(up[k] and not up[k - 1] for k in range(i - 4, i + 1))
    d_i = b["d"][i]
    lo_cal = (dt.date.fromisoformat(d_i) - dt.timedelta(days=SPLIT_DAYS)).isoformat()
    dv = np.median(c[i - 19: i + 1] * v[i - 19: i + 1])
    return {
        "rsi": _r(z["rsi"][i], 2), "rsi_low": _r(z["rsi"][lowday], 2),
        "low25": _r(low), "hold_n": hold_n, "held": int(held), "dist": _r(dist * 100.0, 2),
        "bounce": _r(bounce * 100.0, 2), "boom5": _r(best, 1),
        "ema_up": int(bool(up[i])), "ema_x5": int(crossed),
        "below3": int(bool(c[i] < z["ema20"][i] and c[i] < z["ema30"][i] and c[i] < z["ema50"][i])),
        "macd_pos": int(bool(z["macd"][i] > z["macd_sig"][i])),
        "split120": int(any(lo_cal < sd <= d_i for sd in sdates)),
        "dv20": _r(float(dv), 0),
    }


def episodes(b, eps_sym):
    """Episodes of one symbol with indices: launch L (trough + 1, READY70), L10 (first close ≥ 10% above the trough,
    SEQ70), IGN (largest one-day close gain in [L, D1]), x70 (first close ≥ 70% above the trough, None if never)."""
    out = []
    for e in eps_sym:
        if e["launch"] not in b["ix"] or e["d1"] not in b["ix"] or e["peak"] not in b["ix"]:
            continue
        L, D1, P = b["ix"][e["launch"]], b["ix"][e["d1"]], b["ix"][e["peak"]]
        c = b["c"]
        tc = float(c[max(L - 1, 0)])
        x70 = next((k for k in range(L, max(P, D1) + 1) if tc > 0 and c[k] >= tc * 1.70), None)
        gains = [((c[k] / c[k - 1] - 1.0) if c[k - 1] > 0 else -1.0, k) for k in range(L, D1 + 1)]
        ign = max(gains)[1] if gains else L
        l10 = b["ix"].get(e.get("l10") or "", L)
        out.append(dict(e, L=L, D1=D1, P=P, x70=x70, IGN=ign, L10=max(l10, L)))
    return out


def label(eps, i, last, key="L", strict=False):
    """Onset label at decision index i for onset `key` (L primary · L10 · IGN sensitivity): IN_EVENT (an episode under
    way: onset ≤ i ≤ max(P, D1)) · CENSORED (an onset at i+10 could still be undetected: i + 10 + MAXGAP beyond the last
    bar) · UNKNOWN_SPLIT (a split-near episode starts in [i+1, i+10]) · POS710 (a clean episode starts in [i+7, i+10];
    `strict`: and its close reaches +70% over the trough) · NEG. Also pos110 (a clean start in [i+1, i+10])."""
    for e in eps:
        if e[key] <= i <= max(e["P"], e["D1"]):
            return "IN_EVENT", None, 0
    if i + H_HI + MAXGAP > last:
        return "CENSORED", None, 0
    soon = [e for e in eps if i + 1 <= e[key] <= i + H_HI]
    if any(e["quality"] != "OK" for e in soon):
        return "UNKNOWN_SPLIT", None, 0
    if strict:
        soon = [e for e in soon if e["x70"] is not None]
    p710 = next((e for e in soon if i + H_LO <= e[key] <= i + H_HI), None)
    return ("POS710" if p710 else "NEG"), (p710 or (soon[0] if soon else None)), int(bool(soon))


def next_onset(eps, i):
    """Sessions from i to the next clean launch L after i (outcome field for lead-time reports; None if none)."""
    nx = [e["L"] - i for e in eps if e["L"] > i and e["quality"] == "OK"]
    return min(nx) if nx else None


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


COND = ("rsi", "rsi_low", "low25", "hold_n", "held", "dist", "bounce", "boom5", "ema_up", "ema_x5", "below3",
        "macd_pos", "split120", "dv20")


def build(out_dir=DATA):
    meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    pi = _rd(os.path.join(R70_DATA, "pi_obs.csv.gz"))
    tr = {(r["sym"], r["t"]): r for r in _rd(os.path.join(S70_DATA, "traj.csv.gz"))}
    ev_all = _rd(os.path.join(S70_DATA, "events.csv.gz"))
    eps_by = {}
    for e in ev_all:
        eps_by.setdefault(e["sym"], []).append(e)
    by_sym = {}
    for r in pi:
        by_sym.setdefault(r["sym"], []).append(r)
    rows, eps_out, cache = [], [], {}
    pivot_days = {}

    def prep(sym):
        if sym not in cache:
            b = bars[sym]
            b["fac"] = R.split_factor_after(splits.get(sym, []), b["d"])
            sd = sorted(d for d, r_ in (splits.get(sym) or []) if r_ and float(r_) < 1)
            cache[sym] = (b, series(b), sd, episodes(b, eps_by.get(sym, [])))
        return cache[sym]

    for sym in sorted(by_sym):
        b, z, sd, eps = prep(sym)
        last = len(b["c"]) - 1
        pivot_days[sym] = set()
        for r in sorted(by_sym[sym], key=lambda r: r["t"]):
            i = b["ix"][r["t"]]
            pivot_days[sym].add(i)
            cd = conditions(b, z, i, sd)
            lab, e, soon = label(eps, i, last)
            row = {"t": r["t"], "sym": sym, "cond_ok": int(cd is not None), "lab": lab, "pos110": soon,
                   "to_onset": (e["L"] - i) if e else None, "to_d1": (e["D1"] - i) if e else None,
                   "ep": f'{sym}|{e["launch"]}' if e else None, "nxt": next_onset(eps, i),
                   "lab_x70": label(eps, i, last, strict=True)[0], "lab_l10": label(eps, i, last, "L10")[0],
                   "lab_ign": label(eps, i, last, "IGN")[0]}
            row.update(cd or {})
            for k in PI_COPY:
                row[k] = r.get(k)
            t = tr.get((sym, r["t"])) or {}
            for k in TR_COPY:
                row[k] = t.get(k)
            rows.append(row)
    for sym in sorted(eps_by):
        if sym not in bars:
            continue
        b, z, sd, eps = prep(sym)
        piv = pivot_days.get(sym, set())
        for e in eps:
            L = e["L"]
            early = [k for k in range(L - H_HI, L - H_LO + 1) if k in piv]
            eps_out.append({"sym": sym, "launch": e["launch"], "d1": e["d1"], "peak": e["peak"], "kind": e["kind_d1"],
                            "gain_d1": e["gain_d1"], "peak_gain": e["peak_gain"], "quality": e["quality"],
                            "l10": b["d"][e["L10"]], "x70": b["d"][e["x70"]] if e["x70"] is not None else "",
                            "ign": b["d"][e["IGN"]], "l_to_ign": e["IGN"] - L, "l_to_d1": e["D1"] - L,
                            "l_to_x70": (e["x70"] - L) if e["x70"] is not None else "",
                            "early_pivot_days": len(early), "seed": int(sym in SEEDS), "active": int(sym in ACTIVE)})
    # every clean episode's early window [L-10, L-7], pivot-day or not (who was outside the pivot population?)
    wrows = []
    for sym in sorted(eps_by):
        if sym not in bars:
            continue
        b, z, sd, eps = prep(sym)
        piv = pivot_days.get(sym, set())
        for e in eps:
            if e["quality"] != "OK":
                continue
            for k in range(e["L"] - H_HI, e["L"] - H_LO + 1):
                if k < 0:
                    continue
                cd = conditions(b, z, k, sd) or {}
                row = {"sym": sym, "launch": e["launch"], "t": b["d"][k], "off": k - e["L"], "pivot": int(k in piv),
                       "px": _r(float(b["c"][k] * b["fac"][k])), "cond_ok": int(bool(cd))}
                row.update(cd)
                row.update(_pi(b, k))
                wrows.append(row)
    srows = []
    for sym in SEEDS + ACTIVE:
        if sym not in bars:
            srows.append({"sym": sym, "t": "", "note": "NO_BARS"})
            continue
        b, z, sd, eps = prep(sym)
        piv = pivot_days.get(sym, set())
        last = len(b["c"]) - 1
        for i, d in enumerate(b["d"]):
            if d < SEED_FROM:
                continue
            cd = conditions(b, z, i, sd) or {}
            cd.update(_pi(b, i) if i >= 60 else {})
            lab, e, soon = label(eps, i, last)
            row = {"sym": sym, "t": d, "pivot": int(i in piv), "close": _r(float(b["c"][i])),
                   "px": _r(float(b["c"][i] * b["fac"][i])), "vol": int(b["v"][i]), "lab": lab,
                   "to_onset": (e["L"] - i) if e else None, "nxt": next_onset(eps, i)}
            row.update(cd)
            srows.append(row)
    os.makedirs(out_dir, exist_ok=True)
    rf = (["t", "sym", "cond_ok", "lab", "pos110", "to_onset", "to_d1", "ep", "nxt", "lab_x70", "lab_l10", "lab_ign"]
          + list(COND) + list(PI_COPY) + list(TR_COPY))
    _wcsv(os.path.join(out_dir, "rows.csv.gz"), rows, rf)
    ef = ["sym", "launch", "d1", "peak", "kind", "gain_d1", "peak_gain", "quality", "l10", "x70", "ign", "l_to_ign",
          "l_to_d1", "l_to_x70", "early_pivot_days", "seed", "active"]
    _wcsv(os.path.join(out_dir, "events.csv.gz"), eps_out, ef)
    sf = ["sym", "t", "pivot", "close", "px", "vol", "lab", "to_onset", "nxt"] + list(COND) + list(PI_SIDE) + ["note"]
    _wcsv(os.path.join(out_dir, "seeds.csv.gz"), srows, sf)
    wf = ["sym", "launch", "t", "off", "pivot", "px", "cond_ok"] + list(COND) + list(PI_SIDE)
    _wcsv(os.path.join(out_dir, "ewin.csv.gz"), wrows, wf)
    gaps = [e["l_to_d1"] for e in eps_out if e["quality"] == "OK"]
    cal = R.sessions_calendar(bars)
    last_ok = cal[len(cal) - 1 - H_HI - MAXGAP]
    inv = {"rows": len(rows), "symbols": len(by_sym), "labels": dict(sorted(_count(r["lab"] for r in rows).items())),
           "label_known_last_decision": last_ok, "calendar_last": cal[-1],
           "episodes": len(eps_out), "episodes_ok": sum(1 for e in eps_out if e["quality"] == "OK"),
           "max_launch_to_detection": max(gaps) if gaps else None, "MAXGAP_used": MAXGAP,
           "ok_with_pivot_in_early_window": sum(1 for e in eps_out if e["quality"] == "OK" and e["early_pivot_days"]),
           "seed_rows": len(srows), "ewin_rows": len(wrows), "last_session": max(r["t"] for r in rows) if rows else None}
    json.dump(inv, open(os.path.join(out_dir, "inventory.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    json.dump({"sessions": cal}, open(os.path.join(out_dir, "calendar.json"), "w", encoding="utf-8"))
    return inv


PI_SIDE = ("pc_stage", "pc_branch", "loc", "tl_dist")


def _pi(b, i):
    """READY70's point-in-time cycle-stage and READY-location fields for a day outside the pivot population."""
    f = R.features(b, i)
    return {k: f.get(k) for k in PI_SIDE}


def _count(it):
    out = {}
    for x in it:
        out[x] = out.get(x, 0) + 1
    return out


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("rows.csv.gz", "events.csv.gz", "seeds.csv.gz", "ewin.csv.gz", "inventory.json",
                           "calendar.json")
               if _digest(os.path.join(tmp, f)) != _digest(os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    print(json.dumps(build(), indent=1))
