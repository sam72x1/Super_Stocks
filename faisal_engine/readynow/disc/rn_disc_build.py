"""READY NOW historical discovery — the corrected-target dataset (research only · offline · read-only).

Target. For every clean episode of the bot's explosion detector (READY70 `episodes_for`, unchanged) three dates are
kept apart:
  L      launch = session after the trough close (READY70; retrospective, can sit on the 20-session window edge)
  ONSET  start of the final +70% leg = 1 + the latest close k in [L-1, Q-1] that is the lowest close of [k, Q-1] and
         from which the qualifying close was reached: close[Q] >= G x close[k]
         (Q = x70, the first close >= 1.70 x the trough close, G = 1.70; for a jump episode that never closes +70% above
         the trough, Q = D1 and G = 1.50). ONSET lies in [L, Q]. A one-day jump starts on the jump day; a clean run
         starts at L; a slow drift that ends in a jump starts at the jump.
  Q / D1 the +70% close (x70) and the detector's first detection (D1, observable that day)
Decision rows are READYNOW's pivot-days (`readynow/data/rows.csv.gz`: identity M1-M3 from bars <= t). Label `lab`:
  IN_EVENT     an episode's ONSET <= t <= max(P, D1, Q)  (already inside the move — never a pre-move prediction)
  CENSORED     t + 10 + 19 beyond the last bar (L/ONSET are known only after detection, up to 19 sessions later)
  UNKNOWN_SPLIT a split-near episode starts (ONSET) in [t+1, t+10]
  POS710       a clean episode's ONSET in [t+7, t+10]          NEG otherwise
Features (bars <= t only): every READYNOW condition column, READY70 features, SEQ70 path descriptors, and the
temporal-order features of `temporal()` (each documented where it is defined).
Outputs (disc/data/): rows.csv.gz · events.csv.gz · alerts.json · inventory.json
Run from the repo root:  python3 faisal_engine/readynow/disc/rn_disc_build.py   (--check regenerates and compares)
"""
import csv
import gzip
import hashlib
import io
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(RN))
DATA = os.path.join(HERE, "data")
sys.path.insert(0, RN)
sys.path.insert(0, os.path.join(ROOT, "faisal_engine", "seq70"))
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import rn_build as B                                                      # noqa: E402  (READYNOW, read-only)

R = B.R
H_LO, H_HI, MAXGAP = B.H_LO, B.H_HI, B.MAXGAP
SEEDS = ("DLXY", "RETO", "DKI", "SXTC")
ACTIVE = ("HUBC",)


def rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _r(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def onset_leg(c, e):
    """Start of the final +70% leg (see module docstring). Returns (onset index, Q index, G)."""
    L = e["L"]
    if e["x70"] is not None:
        q, g = e["x70"], 1.70
    else:
        q, g = e["D1"], 1.50
    run_min = np.inf
    for k in range(q - 1, L - 2, -1):
        if k < 0:
            break
        run_min = min(run_min, c[k])
        if c[k] <= run_min and c[k] > 0 and c[q] >= g * c[k]:
            return k + 1, q, g
    return L, q, g


def temporal(b, z, i):
    """Temporal-order features at index i from bars <= i only (each a question no earlier study asked; see
    READY_DISCOVERY.md §5 for the observation behind it).
    rsi_div    : the close is within 3% of its 60-session low AND the RSI there is >= 5 points above the RSI at the
                 previous 60-session low reached at least 10 sessions earlier (price holds / undercuts, momentum doesn't)
    hl_count   : number of higher closing swing lows (3-bar fractal on closes) since the 25-session low day
    rise10_vdry: close >= 10% above the 25-session low AND median volume of the last 5 sessions <= 0.7 x the median of
                 sessions i-30..i-11 (a quiet climb off the low)
    v_then_up  : the highest-volume session of the last 10 came at or before the 25-session low day's index + 2 and the
                 close is now above that day's close (volume at the low, price recovering after it)
    first_up   : sessions since the first close above EMA20 after at least 10 sessions below it (None if no such cross
                 in the last 20 sessions)"""
    if i < 70:
        return {}
    c, lw, v = b["c"][: i + 1], b["l"][: i + 1], b["v"][: i + 1]
    rsi = z["rsi"][: i + 1]
    out = {}
    lo60 = lw[i - 59: i + 1]
    k_now = i - 59 + int(np.argmin(lo60))
    prior = lw[i - 59: max(i - 59, k_now - 9)]
    if len(prior) >= 1 and k_now - (i - 59) >= 10:
        k_prev = i - 59 + int(np.argmin(prior))
        near_low = c[i] <= lw[k_now] * 1.03
        out["rsi_div"] = int(bool(near_low and lw[k_now] <= lw[k_prev] * 1.02 and np.isfinite(rsi[k_now])
                                  and np.isfinite(rsi[k_prev]) and rsi[k_now] >= rsi[k_prev] + 5))
        out["rsi_div_gap"] = _r(float(rsi[k_now] - rsi[k_prev]), 2) if np.isfinite(rsi[k_now] - rsi[k_prev]) else None
    else:
        out["rsi_div"], out["rsi_div_gap"] = 0, None
    lo25 = lw[i - 24: i + 1]
    k25 = i - 24 + int(np.argmin(lo25))
    lows = [k for k in range(k25 + 1, i) if c[k] < c[k - 1] and c[k] <= c[k + 1]]
    hl = 0
    prev = c[k25]
    for k in lows:
        if c[k] > prev:
            hl += 1
            prev = c[k]
    out["hl_count"] = hl
    low = float(lw[k25])
    base_v = float(np.median(v[i - 30: i - 10]))
    out["rise10_vdry"] = int(bool(low > 0 and c[i] >= low * 1.10 and base_v > 0 and np.median(v[i - 4: i + 1]) <= 0.7 * base_v))
    kv = i - 9 + int(np.argmax(v[i - 9: i + 1]))
    out["v_then_up"] = int(bool(kv <= k25 + 2 and kv < i and c[i] > c[kv]))
    e20 = z["ema20"][: i + 1]
    fu = None
    for k in range(i, max(i - 20, 10), -1):
        if c[k] > e20[k] and all(c[j] < e20[j] for j in range(k - 10, k)):
            fu = i - k
            break
    out["first_up"] = fu
    return out


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


TEMP = ("rsi_div", "rsi_div_gap", "hl_count", "rise10_vdry", "v_then_up", "first_up")
S70_ADD = ("v5x", "tr5x", "pos60", "bot_age", "nlow20", "clv5", "spell_age", "desc_ok")
R70_ADD = ("pc_held", "pc_bounce", "pc_first_rise", "pc_vs_bottom", "pc_bottom_ago", "ret5", "ret1", "rise_low10")


def label(eps, i, last):
    for e in eps:
        if e["ON"] <= i <= max(e["P"], e["D1"], e["Q"]):
            return "IN_EVENT", None, 0
    if i + H_HI + MAXGAP > last:
        return "CENSORED", None, 0
    soon = [e for e in eps if i + 1 <= e["ON"] <= i + H_HI]
    if any(e["quality"] != "OK" for e in soon):
        return "UNKNOWN_SPLIT", None, 0
    p = next((e for e in soon if i + H_LO <= e["ON"] <= i + H_HI), None)
    return ("POS710" if p else "NEG"), (p or (soon[0] if soon else None)), int(bool(soon))


def build(out_dir=DATA):
    meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    rn_rows = rd(os.path.join(B.DATA, "rows.csv.gz"))
    tr = {(r["sym"], r["t"]): r for r in rd(os.path.join(B.S70_DATA, "traj.csv.gz"))}
    pi = {(r["sym"], r["t"]): r for r in rd(os.path.join(B.R70_DATA, "pi_obs.csv.gz"))}
    ev_all = rd(os.path.join(B.S70_DATA, "events.csv.gz"))
    eps_by = {}
    for e in ev_all:
        eps_by.setdefault(e["sym"], []).append(e)
    cache = {}

    def prep(sym):
        if sym not in cache:
            cache.clear()
            b = bars[sym]
            b["fac"] = R.split_factor_after(splits.get(sym, []), b["d"])
            eps = B.episodes(b, eps_by.get(sym, []))
            for e in eps:
                e["ON"], e["Q"], e["G"] = onset_leg(b["c"], e)
            cache[sym] = (b, B.series(b), eps)
        return cache[sym]

    rows = []
    for r in sorted(rn_rows, key=lambda r: (r["sym"], r["t"])):
        sym = r["sym"]
        b, z, eps = prep(sym)
        i = b["ix"][r["t"]]
        lab, e, soon = label(eps, i, len(b["c"]) - 1)
        row = dict(r)
        row.update({"lab_on": lab, "pos110_on": soon, "ep_on": f'{sym}|{b["d"][e["ON"]]}' if e else None,
                    "to_onset_on": (e["ON"] - i) if e else None, "to_q_on": (e["Q"] - i) if e else None,
                    "to_d1_on": (e["D1"] - i) if e else None,
                    "in_drift": int(any(x["L"] <= i < x["ON"] for x in eps))})
        t = tr.get((sym, r["t"])) or {}
        for k in S70_ADD:
            row[k] = t.get(k)
        p = pi.get((sym, r["t"])) or {}
        for k in R70_ADD:
            row[k] = p.get(k)
        row.update(temporal(b, z, i))
        rows.append(row)
    events = []
    for sym in sorted(eps_by):
        if sym not in bars:
            continue
        b, z, eps = prep(sym)
        for e in eps:
            events.append({"sym": sym, "quality": e["quality"], "kind": e["kind_d1"], "gain_d1": e["gain_d1"],
                           "peak_gain": e["peak_gain"], "trough": b["d"][e["L"] - 1], "L": b["d"][e["L"]],
                           "onset": b["d"][e["ON"]], "q": b["d"][e["Q"]], "g": e["G"], "x70": b["d"][e["x70"]]
                           if e["x70"] is not None else "", "d1": b["d"][e["D1"]], "ign": b["d"][e["IGN"]],
                           "peak": b["d"][e["P"]], "L_to_onset": e["ON"] - e["L"], "onset_to_q": e["Q"] - e["ON"],
                           "onset_to_d1": e["D1"] - e["ON"], "l_to_d1": e["D1"] - e["L"],
                           "edge_clipped": int(e["D1"] - e["L"] == MAXGAP and e["L"] >= 2 and float(
                               b["c"][max(0, e["L"] - 21): e["L"] - 1].min()) < float(b["c"][e["L"] - 1])),
                           "seed": int(sym in SEEDS), "active": int(sym in ACTIVE)})
    os.makedirs(out_dir, exist_ok=True)
    fields = list(rn_rows[0].keys()) + ["lab_on", "pos110_on", "ep_on", "to_onset_on", "to_q_on", "to_d1_on",
                                         "in_drift"] + list(S70_ADD) + list(R70_ADD) + list(TEMP)
    _wcsv(os.path.join(out_dir, "rows.csv.gz"), rows, fields)
    _wcsv(os.path.join(out_dir, "events.csv.gz"), events, list(events[0].keys()))
    # recorded real-time alerts for the seeds and HUBC (the bot's alert history · ALERTS70 liquidity anchors)
    al = {}
    ah = json.load(open(os.path.join(ROOT, "alerts_history.json"), encoding="utf-8")).get("alerts") or []
    for a in ah:
        if a.get("symbol") in SEEDS + ACTIVE:
            al.setdefault(a["symbol"], []).append({"src": "alerts_history.json", "date": a.get("date"),
                                                   "ready": a.get("ready"), "status": a.get("status")})
    a70 = rd(os.path.join(ROOT, "faisal_engine", "alerts70", "data", "alerts.csv.gz"))
    for a in a70:
        if a.get("symbol") in SEEDS + ACTIVE:
            al.setdefault(a["symbol"], []).append({"src": "alerts70/alerts.csv.gz", "date": a.get("date"),
                                                   "anchor_et": a.get("anchor_et"), "tier": a.get("tier")})
    json.dump(al, open(os.path.join(out_dir, "alerts.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              sort_keys=True)
    ok = [e for e in events if e["quality"] == "OK"]
    from collections import Counter
    inv = {"rows": len(rows), "symbols": len({r["sym"] for r in rows}), "bars_symbols": len(bars),
           "episodes": len(events), "episodes_ok": len(ok), "labels_on": dict(sorted(Counter(r["lab_on"] for r in rows).items())),
           "labels_L": dict(sorted(Counter(r["lab"] for r in rows).items())),
           "onset_equals_L": sum(e["L"] == e["onset"] for e in ok), "onset_after_L": sum(e["onset"] > e["L"] for e in ok),
           "onset_equals_q": sum(e["onset"] == e["q"] for e in ok), "edge_clipped": sum(e["edge_clipped"] for e in ok),
           "no_x70": sum(1 for e in ok if not e["x70"]), "first_row": min(r["t"] for r in rows),
           "last_row": max(r["t"] for r in rows)}
    json.dump(inv, open(os.path.join(out_dir, "inventory.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    return inv


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("rows.csv.gz", "events.csv.gz", "alerts.json", "inventory.json")
               if _digest(os.path.join(tmp, f)) != _digest(os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    print(json.dumps(build(), indent=1))
