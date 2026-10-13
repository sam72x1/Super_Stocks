"""GEN5 · stage C — the sealed test (research only). Contract: GEN5_PREREG.md (its SHA-256 is pinned below
and checked before any test-population number is computed; a changed contract ⇒ exit 9).

Population: fm_forensics/READY_NOW_MISSED_SIGNALS.csv rows with NEAR_WATCH_14D ∈ {INSIDE, OVERSOLD}, minus the five
generation symbols ⇒ 100 rows / 53 symbols (asserted). Each row is label-checked on the split-adjusted archive
(QA), duplicates of the same move are merged (earliest verified date kept), then every remaining event gets
matched controls from the same near-watch days. Features: gen5_features.features_at on bars[0..t].

Usage:  python3 fm_forensics/gen5/gen5_test.py            # the sealed run (writes data/gen5_result.json)
        python3 fm_forensics/gen5/gen5_test.py --guards   # synthetic guards only (no test-population read)
"""
import bisect
import csv
import datetime as dt
import hashlib
import json
import os
import random
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen5_features as G   # noqa: E402
import gen5_pit as PIT      # noqa: E402

PREREG = os.path.join(HERE, "GEN5_PREREG.md")
PREREG_SHA256 = "d36de881c5ce0419dd37fde1a42d8a49a09171e715bbde9cea695879ca73dfd5"
CSV_FILE = os.path.join(G.ROOT, "fm_forensics", "READY_NOW_MISSED_SIGNALS.csv")
OUT = os.path.join(HERE, "data", "gen5_result.json")
FIVE = ("SXTC", "DKI", "RETO", "DLXY", "HUBC")
WIN = 20                 # decision sessions E−20 … E−1
HIST = 80                # bars needed before E (60 for the cycle window + the 20-session window)
QA_GAIN = 2.0            # verified ⟺ max close in [E, E+20] ≥ 2 × close[E−1] (the register's own ≥ 100%)
DEDUP = 10               # same symbol, next verified E within 10 sessions ⇒ same move
POOL_DAYS = 14           # control pool: in near-watch on a decision day in the 14 calendar days before E
N_CTRL = 5
CTRL_JUMP, CTRL_RUN = 1.5, 1.7   # control invalid if a ≥ 50% close jump or a ≥ 70% run happens in [E−19, E+20]
CTRL_MIN_FOLLOW = 5      # sessions of follow-up after E needed to call a control "did not explode"
REG_WINDOW_DAYS = 30     # control invalid if it is in the 279 register within ±30 calendar days of E
BOOT, SEED = 4000, 20261013
PRIMARY = "RETEST"
BASELINE = "RSI33"
COMPONENTS = ("RETEST", "STAB3", "BOUNCE", "STAGE4", "SWEEP", "RSI33", "RSIMIN33", "RETEST_RSI",
              "CAPIT30", "VOL3", "GAPB")
FLOORS = {"events": 30, "symbols": 20, "min_ctrl": 3}


# ── pure helpers (guarded) ───────────────────────────────────────────────────────────────────────────
def price_band(p):
    if p is None:
        return "UNK"
    return "<0.40" if p < 0.40 else "0.40-1" if p < 1 else "1-5" if p < 5 else "5+"


def float_band(f):
    if f is None:
        return "UNK"
    return "<10M" if f < 10e6 else "10-50M" if f < 50e6 else "50M+"


def wall_group(w):
    if not w:
        return "UNK"
    if w == "M_لا_مستوى_مختبر":
        return "ANCHOR"
    if w.startswith("M1"):
        return "M1"
    if w.startswith("M4"):
        return "M4"
    if w in ("CUT", "ABSENT"):
        return "UNK"
    return "OTHER"


def qa_verified(closes, k):
    """closes: list of adjusted closes · k: index of E. Verified iff max close in [E, E+20] ≥ 2 × close[E−1]."""
    if k < 1 or closes[k - 1] is None or closes[k - 1] <= 0:
        return False
    seg = [c for c in closes[k:k + 21] if c is not None]
    return bool(seg) and max(seg) >= QA_GAIN * closes[k - 1]


def dedupe(rows, ix_of):
    """rows: verified rows of ONE symbol · ix_of(row) → session index of E. Keep the earliest of each move."""
    keep, dropped = [], []
    for r in sorted(rows, key=ix_of):
        if keep and ix_of(r) - ix_of(keep[-1]) <= DEDUP:
            dropped.append(r)
        else:
            keep.append(r)
    return keep, dropped


def control_moved(closes, k):
    """True if a ≥ 50% one-day close jump or a ≥ 70% run (close ÷ running min) occurs in [k−19, k+20]."""
    lo = max(1, k - WIN + 1)
    hi = min(len(closes) - 1, k + 20)
    run_min = closes[lo - 1]
    for j in range(lo, hi + 1):
        a, b = closes[j - 1], closes[j]
        if a and b and a > 0 and b / a >= CTRL_JUMP:
            return True
        if run_min and run_min > 0 and b and b / run_min >= CTRL_RUN:
            return True
        if b and (run_min is None or b < run_min):
            run_min = b
    return False


def fires_ext(f):
    """gen5_features.fires + the pre-declared descriptive comparators. None ⇒ unknown."""
    z = G.fires(f)
    z["RETEST_RSI"] = (bool(z["RETEST"] and z["RSIMIN33"]) if None not in (z["RETEST"], z["RSIMIN33"]) else None)
    z["CAPIT30"] = (bool(f["ret5"] <= -30) if f.get("ret5") is not None else None)
    z["VOL3"] = (bool(f["vol_ratio"] >= 3) if f.get("vol_ratio") is not None else None)
    z["GAPB"] = bool(f.get("gap_below_unfilled")) if f.get("gap_below_unfilled") is not None else None
    return z


def window_fire(day_fires, comp):
    """Fired on ≥ 1 decision day; returns (fired, earliest_lead). Unknown days are skipped, never counted."""
    leads = [lead for lead, z in day_fires if z.get(comp)]
    return (bool(leads), max(leads) if leads else None)


def pick_controls(pool, ev, n=N_CTRL):
    """pool: [{sym, wall, price, float}] already valid. Returns (chosen, level). Deterministic by sha256."""
    def h(c):
        return hashlib.sha256(f"{ev['E']}|{ev['sym']}|{c['sym']}".encode()).hexdigest()
    keys = (("wall", "price", "float"), ("wall", "price"), ("wall",))
    for lvl, ks in enumerate(keys):
        m = [c for c in pool if all(c[k] == ev[k] for k in ks)]
        if len(m) >= n or lvl == len(keys) - 1:
            return sorted(m, key=h)[:n], lvl
    return [], len(keys)


def boot_delta(units, comp, base=None, reps=BOOT, seed=SEED):
    """units: [{sym, ev: {comp: 0/1}, ctrl: [{comp: 0/1}]}]. Δ = p_E − p_C (matched-set means), clustered by
    the event symbol. With `base`, returns the paired Δ(comp) − Δ(base)."""
    def stat(us):
        def d(c):
            e = [u["ev"][c] for u in us if u["ev"].get(c) is not None]
            k = [sum(x[c] for x in u["ctrl"] if x.get(c) is not None) / max(1, sum(1 for x in u["ctrl"] if x.get(c) is not None))
                 for u in us if any(x.get(c) is not None for x in u["ctrl"])]
            if not e or not k:
                return None
            return sum(e) / len(e) - sum(k) / len(k)
        a = d(comp)
        if base is None or a is None:
            return a
        b = d(base)
        return None if b is None else a - b
    by = {}
    for u in units:
        by.setdefault(u["sym"], []).append(u)
    syms = sorted(by)
    rng = random.Random(seed)
    vals = []
    for _ in range(reps):
        s = [u for t in (rng.choice(syms) for _ in syms) for u in by[t]]
        v = stat(s)
        if v is not None:
            vals.append(v)
    vals.sort()
    pt = stat(units)
    if not vals or pt is None:
        return {"point": pt, "ci95": None}
    return {"point": round(pt, 4), "ci95": [round(vals[int(0.025 * len(vals))], 4), round(vals[int(0.975 * len(vals)) - 1], 4)]}


# ── data readers ─────────────────────────────────────────────────────────────────────────────────────
def _git(*a):
    return subprocess.run(["git", *a], capture_output=True, text=True, check=False).stdout


def reject_history():
    """[(commit_time_utc, newest entry)] of reject_log.json on origin/main, oldest first."""
    out = []
    for line in _git("log", PIT.REF, "--format=%H %cI", "--", "reject_log.json").splitlines():
        h, t = line.split()
        try:
            d = json.loads(_git("show", f"{h}:reject_log.json"))
        except Exception:                                        # noqa: BLE001
            continue
        ents = [e for e in d if isinstance(e, dict) and "walls" in e] if isinstance(d, list) else []
        if ents:
            out.append((dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc), max(ents, key=lambda e: e["date"])))
    return sorted(out, key=lambda x: x[0])


def nearwatch_history():
    """[(commit_time_utc, run_date, {sym: row})] for rows seen by that run (last_seen == run date)."""
    out = []
    for line in _git("log", PIT.REF, "--format=%H %cI", "--", "near_watch.json").splitlines():
        h, t = line.split()
        try:
            d = json.loads(_git("show", f"{h}:near_watch.json"))
        except Exception:                                        # noqa: BLE001
            continue
        if not isinstance(d, dict) or not d:
            continue
        D = max((v.get("last_seen") or "") for v in d.values() if isinstance(v, dict))
        out.append((dt.datetime.fromisoformat(t).astimezone(dt.timezone.utc), D,
                    {s: v for s, v in d.items() if isinstance(v, dict) and v.get("last_seen") == D}))
    return sorted(out, key=lambda x: x[0])


def pre_open(hist, t, nxt):
    """newest record committed after the close of t (20:00 UTC) and at or before the next open (13:30 UTC)."""
    lo = dt.datetime.fromisoformat(t).replace(hour=20, tzinfo=dt.timezone.utc)
    hi = dt.datetime.fromisoformat(nxt).replace(hour=13, minute=30, tzinfo=dt.timezone.utc)
    times = [x[0] for x in hist]
    k = bisect.bisect_right(times, hi) - 1
    return hist[k] if k >= 0 and hist[k][0] > lo else None


def wall_of(sym, ent):
    for w, lst in ent["walls"].items():
        if sym in lst:
            return w
    return "CUT" if ent.get("sampled") else "ABSENT"


# ── the run ──────────────────────────────────────────────────────────────────────────────────────────
def check_contract():
    got = hashlib.sha256(open(PREREG, "rb").read()).hexdigest()
    if got != PREREG_SHA256:
        print(f"⛔ contract changed or not pinned: {got} ≠ {PREREG_SHA256}")
        sys.exit(9)


def run():
    check_contract()
    rows = list(csv.DictReader(open(CSV_FILE, encoding="utf-8")))
    tracked = [r for r in rows if r["NEAR_WATCH_14D"] in ("INSIDE", "OVERSOLD")]
    pop = [r for r in tracked if r["SYMBOL"] not in FIVE]
    assert len(tracked) == 107 and len(pop) == 100 and len({r["SYMBOL"] for r in pop}) == 53
    assert sum(r["WAS_PIVOT_IDENTITY"] == "True" for r in pop) == 67
    assert not ({r["SYMBOL"] for r in pop} & set(FIVE))
    register = {}
    for r in rows:
        register.setdefault(r["SYMBOL"], []).append(r["EXPL_DATE"])
    bars = G.load_bars()
    splits = G.load_splits()
    cnt = {}
    for df in bars.values():
        for d in df.index.strftime("%Y-%m-%d"):
            cnt[d] = cnt.get(d, 0) + 1
    cal = sorted(d for d, n in cnt.items() if n >= 0.5 * len(bars))
    cix = {d: i for i, d in enumerate(cal)}
    acc = {"rows": len(pop), "no_bars": [], "qa_unverified": [], "dup_merged": [], "short_history": [],
           "no_pool": [], "few_controls": []}
    # 1) QA + dedupe
    ver = {}
    for r in pop:
        s, e = r["SYMBOL"], r["EXPL_DATE"]
        df = bars.get(s)
        if df is None or e not in set(df.index.strftime("%Y-%m-%d")):
            acc["no_bars"].append((s, e))
            continue
        ix = list(df.index.strftime("%Y-%m-%d"))
        k = ix.index(e)
        if not qa_verified(list(df["Close"]), k):
            acc["qa_unverified"].append((s, e))
            continue
        ver.setdefault(s, []).append(r)
    events = []
    for s, rs in ver.items():
        keep, drop = dedupe(rs, lambda r: cix.get(r["EXPL_DATE"], -1))
        acc["dup_merged"] += [(x["SYMBOL"], x["EXPL_DATE"]) for x in drop]
        for r in keep:
            ix = list(bars[s].index.strftime("%Y-%m-%d"))
            k = ix.index(r["EXPL_DATE"])
            if k < HIST:
                acc["short_history"].append((s, r["EXPL_DATE"]))
                continue
            events.append({"sym": s, "E": r["EXPL_DATE"], "k": k, "identity": r["WAS_PIVOT_IDENTITY"] == "True",
                           "kind": r["KIND"]})
    # 2) states at decision time (pre-open snapshots)
    nwh, rjh = nearwatch_history(), reject_history()
    need_dates = set()
    for ev in events:
        k = cix[ev["E"]]
        for j in range(k - WIN, k):
            need_dates.add(cal[j])
    nxt = {t: cal[cix[t] + 1] for t in need_dates}
    pit = PIT.PIT(sorted(need_dates), nxt)
    nw_at = {t: pre_open(nwh, t, nxt[t]) for t in need_dates}
    rj_at = {t: pre_open(rjh, t, nxt[t]) for t in need_dates}

    def state(sym, E):
        """last pre-open near-watch decision of sym in the POOL_DAYS before E → (t, price, wall)."""
        k = cix[E]
        lo = (dt.date.fromisoformat(E) - dt.timedelta(days=POOL_DAYS)).isoformat()
        for j in range(k - 1, k - WIN - 1, -1):
            t = cal[j]
            if t < lo:
                break
            sn = nw_at.get(t)
            if sn and sym in sn[2]:
                rj = rj_at.get(t)
                fl, _ = pit.float_at(sym, t)
                return {"t": t, "price": price_band(G._num(sn[2][sym].get("price"), 4)),
                        "wall": wall_group(wall_of(sym, rj[1]) if rj else None), "float": float_band(fl)}
        return None

    def window(sym, E):
        df = bars[sym]
        ix = list(df.index.strftime("%Y-%m-%d"))
        k = ix.index(E)
        out = []
        for j in range(k - WIN, k):
            f = G.features_at(df, j, splits.get(sym))
            out.append((k - j, fires_ext(f), f))
        return out

    units = []
    for ev in events:
        st = state(ev["sym"], ev["E"])
        if st is None:
            acc["no_pool"].append((ev["sym"], ev["E"]))
            continue
        ev.update(st)
        k = cix[ev["E"]]
        lo = (dt.date.fromisoformat(ev["E"]) - dt.timedelta(days=POOL_DAYS)).isoformat()
        members = set()
        for j in range(k - WIN, k):
            t = cal[j]
            if t >= lo and nw_at.get(t):
                members |= set(nw_at[t][2])
        pool = []
        for c in sorted(members - {ev["sym"]} - set(FIVE)):
            df = bars.get(c)
            if df is None:
                continue
            ix = list(df.index.strftime("%Y-%m-%d"))
            if ev["E"] not in ix:
                continue
            kc = ix.index(ev["E"])
            if kc < HIST or len(ix) - 1 - kc < CTRL_MIN_FOLLOW:
                continue
            if any(abs((dt.date.fromisoformat(d) - dt.date.fromisoformat(ev["E"])).days) <= REG_WINDOW_DAYS
                   for d in register.get(c, [])):
                continue
            if control_moved(list(df["Close"]), kc):
                continue
            cs = state(c, ev["E"])
            if cs is None:
                continue
            pool.append({"sym": c, **cs})
        chosen, lvl = pick_controls(pool, ev)
        if len(chosen) < FLOORS["min_ctrl"]:
            acc["few_controls"].append((ev["sym"], ev["E"], len(chosen)))
            continue
        ew = window(ev["sym"], ev["E"])
        u = {"sym": ev["sym"], "E": ev["E"], "identity": ev["identity"], "match_level": lvl,
             "follow": len(bars[ev["sym"]]) - 1 - ev["k"], "ev": {}, "ev_lead": {}, "ctrl": [], "ctrl_syms": []}
        for comp in COMPONENTS:
            fired, lead = window_fire([(ld, z) for ld, z, _ in ew], comp)
            known = any(z.get(comp) is not None for _, z, _ in ew)
            u["ev"][comp] = int(fired) if known else None
            u["ev_lead"][comp] = lead
        for c in chosen:
            cw = window(c["sym"], ev["E"])
            row = {}
            for comp in COMPONENTS:
                fired, _ = window_fire([(ld, z) for ld, z, _ in cw], comp)
                known = any(z.get(comp) is not None for _, z, _ in cw)
                row[comp] = int(fired) if known else None
            u["ctrl"].append(row)
            u["ctrl_syms"].append(c["sym"])
        units.append(u)
    return summarize(units, acc)


def summarize(units, acc):
    def block(us):
        n_sym = len({u["sym"] for u in us})
        res = {"events": len(us), "symbols": n_sym,
               "floors_met": len(us) >= FLOORS["events"] and n_sym >= FLOORS["symbols"], "components": {}}
        for comp in COMPONENTS:
            e = [u["ev"][comp] for u in us if u["ev"][comp] is not None]
            cr = [x[comp] for u in us for x in u["ctrl"] if x.get(comp) is not None]
            leads = sorted(u["ev_lead"][comp] for u in us if u["ev_lead"][comp] is not None)
            res["components"][comp] = {
                "p_events": round(sum(e) / len(e), 4) if e else None, "n_events": len(e),
                "p_controls": round(sum(cr) / len(cr), 4) if cr else None, "n_controls": len(cr),
                "delta": boot_delta(us, comp),
                "lead_earliest_median": leads[len(leads) // 2] if leads else None,
                "lead_q25_q75": [leads[len(leads) // 4], leads[(3 * len(leads)) // 4]] if leads else None}
        res["primary_vs_baseline"] = boot_delta(us, PRIMARY, base=BASELINE)
        return res

    out = {"prereg_sha256": PREREG_SHA256, "accounting": {k: (v if isinstance(v, int) else len(v)) for k, v in acc.items()},
           "accounting_detail": acc,
           "primary": block(units),
           "sensitivity_identity": block([u for u in units if u["identity"]]),
           "descriptive_follow10": block([u for u in units if u["follow"] >= 10]),
           "match_levels": {lv: sum(1 for u in units if u["match_level"] == lv) for lv in (0, 1, 2)},
           "units": units}
    out["verdict"] = verdict(out["primary"], out["sensitivity_identity"])
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    return out


def _branch(b):
    if not b["floors_met"]:
        return "D"
    d = b["components"][PRIMARY]["delta"]["ci95"]
    if not d or d[0] <= 0:
        return "C"
    p = b["primary_vs_baseline"]["ci95"]
    return "A" if p and p[0] > 0 else "B"


def verdict(primary, sens):
    """Weakest reading: A only if both readings are A; an unmeasurable sensitivity caps the verdict at B."""
    a, s = _branch(primary), _branch(sens)
    if a == "D":
        return "D"
    if s == "D":
        return "B" if a == "A" else a
    order = {"A": 3, "B": 2, "C": 1}
    return min((a, s), key=lambda x: order[x])


# ── guards (synthetic; no test-population read) ─────────────────────────────────────────────────────
def guards():
    import numpy as np
    import pandas as pd
    fails = []

    def chk(name, cond):
        print(("✅ " if cond else "❌ ") + name)
        if not cond:
            fails.append(name)
    # G1 leakage: features at t ignore every bar after t
    rng = np.random.default_rng(7)
    n = 160
    c = np.cumprod(1 + rng.normal(0, 0.05, n)) * 3
    df = pd.DataFrame({"Open": c, "High": c * 1.04, "Low": c * 0.96, "Close": c, "Volume": rng.integers(1e4, 1e6, n)},
                      index=pd.bdate_range("2025-01-01", periods=n)).astype(float)
    t = 120
    a = G.features_at(df, t)
    df2 = df.copy()
    df2.iloc[t + 1:] = df2.iloc[t + 1:] * 7.0
    b = G.features_at(df2, t)
    chk("G1 features at t do not read bars after t", a == b)
    # G2 the five never enter the population (assert in run) — static check on constants
    chk("G2 the five are the generation set", set(FIVE) == {"SXTC", "DKI", "RETO", "DLXY", "HUBC"})
    # G3 QA: +100% verified, +80% not
    chk("G3 QA verifies a +100% close and rejects +80%",
        qa_verified([1, 1, 1, 2.0, 1.5], 3) and not qa_verified([1, 1, 1, 1.8, 1.5], 3))
    # G4 dedupe keeps the earliest of a move and a later separate move
    rs = [{"i": 10}, {"i": 12}, {"i": 30}]
    keep, drop = dedupe(rs, lambda r: r["i"])
    chk("G4 dedupe: same move merged, separate move kept", [r["i"] for r in keep] == [10, 30] and len(drop) == 1)
    # G5 control_moved catches a jump and a run, and passes a quiet path
    quiet = [1.0] * 60
    jump = quiet[:40] + [1.6] + [1.6] * 19
    run = quiet[:40] + [1.0 + 0.05 * k for k in range(1, 21)]
    chk("G5 control exclusion: jump and run caught, quiet passes",
        control_moved(jump, 40) and control_moved(run, 40) and not control_moved(quiet, 40))
    # G6 deterministic matching with fallback levels
    pool = [{"sym": f"C{k}", "wall": "ANCHOR", "price": "<0.40", "float": "UNK"} for k in range(7)]
    ev = {"sym": "X", "E": "2026-09-01", "wall": "ANCHOR", "price": "<0.40", "float": "<10M"}
    p1, l1 = pick_controls(pool, ev)
    p2, l2 = pick_controls(pool, ev)
    chk("G6 matching deterministic, falls back one level", p1 == p2 and l1 == 1 and len(p1) == N_CTRL)
    # G7 unknown never counts as fired
    chk("G7 unknown component is not a fire", window_fire([(3, {"RETEST": None}), (2, {"RETEST": None})], "RETEST") == (False, None))
    # G8 bootstrap: a clean separation has a positive CI; identical arms straddle zero
    us = [{"sym": f"S{k}", "ev": {"RETEST": 1, "RSI33": 0}, "ctrl": [{"RETEST": 0, "RSI33": 0}] * 3} for k in range(30)]
    d = boot_delta(us, "RETEST", reps=500)
    us2 = [{"sym": f"S{k}", "ev": {"RETEST": k % 2, "RSI33": 0}, "ctrl": [{"RETEST": (k + 1) % 2, "RSI33": 0}] * 3}
           for k in range(30)]
    d2 = boot_delta(us2, "RETEST", reps=500)
    chk("G8 bootstrap separates a clean effect and not a null", d["ci95"][0] > 0 and d2["ci95"][0] <= 0 <= d2["ci95"][1])
    # G9 verdict: weakest reading
    A = {"floors_met": True, "components": {PRIMARY: {"delta": {"ci95": [0.1, 0.3]}}}, "primary_vs_baseline": {"ci95": [0.01, 0.2]}}
    B = {"floors_met": True, "components": {PRIMARY: {"delta": {"ci95": [0.1, 0.3]}}}, "primary_vs_baseline": {"ci95": [-0.1, 0.2]}}
    Cc = {"floors_met": True, "components": {PRIMARY: {"delta": {"ci95": [-0.1, 0.3]}}}, "primary_vs_baseline": {"ci95": [-0.1, 0.2]}}
    Dd = {"floors_met": False, "components": {}, "primary_vs_baseline": {}}
    chk("G9 verdict is the weakest reading",
        verdict(A, A) == "A" and verdict(A, B) == "B" and verdict(A, Cc) == "C" and verdict(A, Dd) == "B"
        and verdict(Dd, A) == "D")
    print(f"\nguards failed: {len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    if "--guards" in sys.argv:
        sys.exit(guards())
    res = run()
    print(json.dumps({k: res[k] for k in ("accounting", "match_levels", "verdict")}, ensure_ascii=False, indent=1))
    for name in ("primary", "sensitivity_identity", "descriptive_follow10"):
        b = res[name]
        print(f"\n== {name}: events {b['events']} · symbols {b['symbols']} · floors {b['floors_met']}")
        for comp, v in b["components"].items():
            print(f"  {comp:10s} E {v['p_events']} (n {v['n_events']}) · C {v['p_controls']} (n {v['n_controls']}) · "
                  f"Δ {v['delta']['point']} {v['delta']['ci95']} · earliest lead med {v['lead_earliest_median']} {v['lead_q25_q75']}")
        print(f"  primary − baseline: {b['primary_vs_baseline']}")
