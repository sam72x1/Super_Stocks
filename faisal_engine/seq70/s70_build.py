"""SEQ70 — the path of pivot stocks before the bot's +70% events (research · offline · read-only).

Reuses, by import and without modification, the sealed READY70 outputs and code (faisal_engine/ready70/):
the pivot-identity population `pi_obs.csv.gz` (174,796 pivot-days, its labels f10/y10), the recomputed explosion
episodes `episodes.csv.gz` (launch = trough + 1, crossing D1, peak) and the archived daily bars.

For every pivot-day it adds eight path descriptors computed from bars at or before that day only, the pivot spell
it belongs to (consecutive pivot-days, gaps of at most SPELL_GAP sessions) and its age in the spell. For every
episode it adds the alternative start L10 (first close at least 10% above the trough close) and whether the
stock was a pivot on the session before the launch.

Outputs (data/):  traj.csv.gz (one row per pivot-day) · events.csv.gz (one row per episode) · inventory.json
Run from the repo root:  python3 faisal_engine/seq70/s70_build.py   (--check verifies the outputs)
No outcome is computed here: labels are copied from READY70 unchanged.
"""
import csv
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
sys.path.insert(0, os.path.join(ROOT, "faisal_engine", "ready70"))
os.environ["FAISAL_ONLY"] = "1"
import numpy as np                                                        # noqa: E402
import r70_build as R                                                     # noqa: E402  (sealed READY70 code, read-only)

SPELL_GAP = 5                 # a pivot spell continues across at most 5 non-pivot sessions
BASE = (60, 11)               # baseline window: sessions i-60 .. i-11 (50 sessions, the last 10 excluded)
DESC = ("v1x", "v5x", "tr5x", "r5", "pos60", "bot_age", "nlow20", "clv5")
COPY = ("px", "ret5", "range20", "pc_stage", "bt_src", "bot_ready", "f10", "f10_k", "f10_gain", "y10", "y10_to_launch",
        "y10_to_d1", "y10_ep", "g10_max", "g10_dd", "f20", "f20_k")


def _rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def _r(x, k=4):
    return None if x is None or not np.isfinite(x) else round(float(x), k)


def descriptors(b, i):
    """Eight path descriptors at session index i from bars [.. i] only (guarded by test_s70 G1).
    v1x   volume today / median volume of sessions i-60..i-11
    v5x   median volume of the last 5 sessions / the same baseline
    tr5x  mean daily range (high-low)/close of the last 5 sessions / mean of the baseline sessions
    r5    5-session close return (%)
    pos60 close inside the 60-session low..high band (0 = at the low, 1 = at the high)
    bot_age  sessions since the lowest low of the last 60 sessions (0 = today, ties → most recent)
    nlow20   sessions among the last 20 that printed a new 60-session low (low below the previous 59 lows)
    clv5  mean close location (close-low)/(high-low) over the last 5 sessions"""
    if i < 80:
        return None
    c, h, lw, v = b["c"][: i + 1], b["h"][: i + 1], b["l"][: i + 1], b["v"][: i + 1]
    bl = slice(i - BASE[0], i - BASE[1] + 1)
    vb = float(np.median(v[bl]))
    tr = (h - lw) / np.where(c > 0, c, np.nan)
    trb = float(np.nanmean(tr[bl]))
    lo60, hi60 = float(lw[i - 59: i + 1].min()), float(h[i - 59: i + 1].max())
    w = lw[i - 59: i + 1]
    bot = 59 - int(np.argmin(w[::-1]))                       # last occurrence of the minimum
    nl = 0
    for j in range(i - 19, i + 1):
        if lw[j] < lw[j - 59: j].min():
            nl += 1
    rng = h[i - 4: i + 1] - lw[i - 4: i + 1]
    clv = np.where(rng > 0, (c[i - 4: i + 1] - lw[i - 4: i + 1]) / np.where(rng > 0, rng, 1.0), 0.5)
    return {
        "v1x": _r(v[i] / vb) if vb > 0 else None,
        "v5x": _r(float(np.median(v[i - 4: i + 1])) / vb) if vb > 0 else None,
        "tr5x": _r(float(np.nanmean(tr[i - 4: i + 1])) / trb) if trb and trb > 0 else None,
        "r5": _r((c[i] / c[i - 5] - 1.0) * 100.0, 2) if c[i - 5] > 0 else None,
        "pos60": _r((c[i] - lo60) / (hi60 - lo60)) if hi60 > lo60 else None,
        "bot_age": i - (i - 59 + bot),
        "nlow20": nl,
        "clv5": _r(float(np.mean(clv))),
    }


def spells(days_idx):
    """days_idx: sorted session indices of one symbol's pivot-days → [(spell_no, age_in_spell)] in the same order."""
    out, sp, start, prev = [], -1, None, None
    for k in days_idx:
        if prev is None or k - prev > SPELL_GAP + 1:
            sp, start = sp + 1, k
        out.append((sp, k - start))
        prev = k
    return out


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


def build(out_dir=DATA):
    meta, bars = R.load_bars()
    cal = R.sessions_calendar(bars)
    cix = {d: k for k, d in enumerate(cal)}
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    pi = _rd(os.path.join(R70_DATA, "pi_obs.csv.gz"))
    eps = _rd(os.path.join(R70_DATA, "episodes.csv.gz"))
    by_sym = {}
    for r in pi:
        by_sym.setdefault(r["sym"], []).append(r)
    rows, pivot_days = [], set()
    for sym in sorted(by_sym):
        b = bars[sym]
        rs = sorted(by_sym[sym], key=lambda r: r["t"])
        sp = spells([cix[r["t"]] for r in rs])
        sdates = sorted(d for d, _r in (splits.get(sym) or []))
        for r, (s_no, age) in zip(rs, sp):
            i = b["ix"][r["t"]]
            row = {"t": r["t"], "sym": sym, "spell": f"{sym}#{s_no}", "spell_age": age}
            lo_d = b["d"][max(0, i - BASE[0])]
            row["split60"] = int(any(lo_d < d <= r["t"] for d in sdates))
            ds = descriptors(b, i)
            row["desc_ok"] = int(ds is not None)
            row.update(ds or {})
            for k in COPY:
                row[k] = r.get(k)
            rows.append(row)
            pivot_days.add((sym, r["t"]))
    erows = []
    for e in eps:
        sym = e["sym"]
        b = bars.get(sym)
        if b is None or e["launch"] not in b["ix"]:
            continue
        L, D1 = b["ix"][e["launch"]], b["ix"][e["d1"]]
        tc = float(b["c"][max(L - 1, 0)])
        L10 = next((k for k in range(L, D1 + 1) if b["c"][k] >= tc * 1.10), D1)
        erows.append({"sym": sym, "launch": e["launch"], "d1": e["d1"], "peak": e["peak"], "kind_d1": e["kind_d1"],
                      "gain_d1": e["gain_d1"], "peak_gain": e["peak_gain"], "quality": e["quality"],
                      "sessions_to_d1": e["sessions_to_d1"], "l10": b["d"][L10], "l10_to_d1": D1 - L10,
                      "pivot_lm1": int(L >= 1 and (sym, b["d"][L - 1]) in pivot_days),
                      "pivot_lm10": int(any((sym, b["d"][k]) in pivot_days for k in range(max(0, L - 10), L)))})
    os.makedirs(out_dir, exist_ok=True)
    tf = ["t", "sym", "spell", "spell_age", "split60", "desc_ok"] + list(DESC) + list(COPY)
    _wcsv(os.path.join(out_dir, "traj.csv.gz"), rows, tf)
    ef = ["sym", "launch", "d1", "peak", "kind_d1", "gain_d1", "peak_gain", "quality", "sessions_to_d1", "l10",
          "l10_to_d1", "pivot_lm1", "pivot_lm10"]
    _wcsv(os.path.join(out_dir, "events.csv.gz"), erows, ef)
    sp_all = {r["spell"] for r in rows}
    inv = {"bars": {"symbols": len(bars), "first": meta.get("first_session") or cal[0], "sessions": len(cal),
                    "last_complete_session": cal[-1]},
           "pivot_days": {"rows": len(rows), "symbols": len(by_sym), "spells": len(sp_all),
                          "from": min(r["t"] for r in rows) if rows else None, "to": max(r["t"] for r in rows) if rows else None,
                          "desc_ok": sum(r["desc_ok"] for r in rows), "split_in_lookback": sum(r["split60"] for r in rows)},
           "episodes": {"rows": len(erows), "ok": sum(1 for e in erows if e["quality"] == "OK"),
                        "pivot_on_session_before_launch": sum(e["pivot_lm1"] for e in erows if e["quality"] == "OK"),
                        "pivot_within_10_before_launch": sum(e["pivot_lm10"] for e in erows if e["quality"] == "OK")}}
    json.dump(inv, open(os.path.join(out_dir, "inventory.json"), "w", encoding="utf-8"), indent=1, sort_keys=True)
    return inv


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("traj.csv.gz", "events.csv.gz", "inventory.json")
               if _digest(os.path.join(tmp, f)) != _digest(os.path.join(DATA, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    print(json.dumps(build(), indent=1))
