"""READYNOW reconciliation — seed timelines, the label limit and sample inclusion (descriptive; no statistic is tested).

Answers, from local data only (bars, the bot's detector recomputed by READY70, the pivot population, the READYNOW,
READY70, SEQ70 and ALERTS70 label files), three questions:
  1. For every episode of the seed symbols (DLXY, RETO, DKI, SXTC; HUBC kept separate): the detector dates (launch L,
     L10, IGN, x70, first detection D1, peak), the source records, and the sessions 7–10 before each anchor with the
     data available that day, its labels, and whether it was in a window and in any study's evaluated sample.
  2. Why READYNOW's last label-known decision is 2026-08-27, and where READY70 / SEQ70 / ALERTS70 stop.
  3. For all clean episodes: where the sessions 7–10 before L and before D1 fall, and how many of the sessions before
     D1 were IN_EVENT under READYNOW's L-anchored label (pre-expansion sessions the primary label never asked about).
No outcome is compared with any condition here. Run from the repo root:
  python3 faisal_engine/readynow/recon/rn_recon.py          → recon/data/recon.json, recon/data/seed_dates.csv.gz
  python3 faisal_engine/readynow/recon/rn_recon.py --check  (regenerates and compares)
"""
import csv
import gzip
import hashlib
import io
import json
import os
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
RN = os.path.dirname(HERE)
ROOT = os.path.dirname(os.path.dirname(RN))
OUT = os.path.join(HERE, "data")
sys.path.insert(0, RN)
os.environ["FAISAL_ONLY"] = "1"
import rn_build as B                                                      # noqa: E402  (READYNOW, read-only)
import rn_lib as K                                                        # noqa: E402

R = B.R
SEEDS = K.SEEDS
ACTIVE = K.ACTIVE
# the five seed events reported in RN_REPORT §2 (the owner-raised moves); every other episode of a seed symbol is listed
FOCUS = {("DLXY", "2026-08-31"), ("RETO", "2026-09-15"), ("SXTC", "2026-06-08"), ("SXTC", "2026-07-30"),
         ("SXTC", "2026-10-07")}
ANCHORS = ("L", "IGN", "x70", "D1")
OFFS = (-10, -9, -8, -7)
R70_WIN = {"discovery": ("2025-05-01", "2025-12-31"), "test": ("2026-01-16", "2026-09-24")}          # r70_eval.py
S70_WIN = {"discovery": ("2025-05-01", "2025-12-31"), "validation": ("2026-01-16", "2026-05-15"),
           "test": ("2026-06-02", "2026-09-24")}                                                     # s70_eval.py
A70_WIN = ("2026-08-17", "2026-09-24")                                                                # A70_PREREG §2
PIVOT_FROM = "2025-05-01"
NOT_ARCHIVED = ["hourly / 4H bars", "after-hours and pre-market bars", "float history", "available-to-borrow history",
                "the app's own condition states (except the dated screenshots in audit/chip_parity.json)"]


def rd(path):
    with gzip.open(path, "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def rn_window(d, limit):
    for w, (lo, hi) in K.WINDOWS.items():
        if lo <= d <= hi:
            return w
    if d < PIVOT_FROM:
        return "before_pivot_population"
    if d > limit:
        return "after_label_limit"
    return "embargo_gap"


def win_of(d, wins):
    return next((w for w, (lo, hi) in wins.items() if lo <= d <= hi), None)


def label_d1(eps, i, last):
    """Detection-anchored label (descriptive): IN_EVENT if a move is under way and not past its peak
    (min(x70, D1) ≤ i ≤ max(P, D1): the +70% close can precede D1 when the detector first merges the move into an earlier
    episode inside its 20-session window) · CENSORED if i + 10 beyond the last bar (D1 is observable on its own day, so
    no MAXGAP) ·
    UNKNOWN_SPLIT if a split-near episode is first detected in [i+1, i+10] · POS710 if a clean one is first detected
    in [i+7, i+10] · NEG. Returns (label, episode, run_started) where run_started = that episode's L ≤ i."""
    for e in eps:
        start = min(e["D1"], e["x70"]) if e.get("x70") is not None else e["D1"]
        if start <= i <= max(e["P"], e["D1"]):
            return "IN_EVENT", None, 0
    if i + B.H_HI > last:
        return "CENSORED", None, 0
    soon = [e for e in eps if i + 1 <= e["D1"] <= i + B.H_HI]
    if any(e["quality"] != "OK" for e in soon):
        return "UNKNOWN_SPLIT", None, 0
    p = next((e for e in soon if i + B.H_LO <= e["D1"] <= i + B.H_HI), None)
    return ("POS710" if p else "NEG"), p, int(bool(p) and p["L"] <= i)


def _wcsv(path, rows, fields):
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=fields, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k) for k in fields})
    with gzip.GzipFile(path, "wb", mtime=0) as f:
        f.write(buf.getvalue().encode("utf-8"))


def build(out_dir=OUT):
    meta, bars = R.load_bars()
    splits = json.load(open(R.SPLITS_FILE, encoding="utf-8"))["splits"]
    cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    cix = {d: k for k, d in enumerate(cal)}
    inv = json.load(open(os.path.join(K.DATA, "inventory.json"), encoding="utf-8"))
    limit = inv["label_known_last_decision"]
    s70_ev = rd(os.path.join(R.ROOT, "faisal_engine", "seq70", "data", "events.csv.gz"))
    r70_ep = {(e["sym"], e["launch"]): e for e in rd(os.path.join(B.R70_DATA, "episodes.csv.gz"))}
    pi = {(r["sym"], r["t"]): r for r in rd(os.path.join(B.R70_DATA, "pi_obs.csv.gz"))}
    obs = {(r["sym"], r["t"]): r for r in rd(os.path.join(B.R70_DATA, "obs.csv.gz"))}
    tr = {(r["sym"], r["t"]): r for r in rd(os.path.join(B.S70_DATA, "traj.csv.gz"))}
    a70 = {(r["sym"], r["t"]): r for r in rd(os.path.join(ROOT, "faisal_engine", "alerts70", "data", "obs.csv.gz"))}
    rn_rows = {(r["sym"], r["t"]): r for r in K.rd("rows.csv.gz")}
    eps_by = defaultdict(list)
    for e in s70_ev:
        eps_by[e["sym"]].append(e)
    cache = {}

    def prep(sym):
        if sym not in cache:
            b = bars[sym]
            b["fac"] = R.split_factor_after(splits.get(sym, []), b["d"])
            sd = sorted(d for d, r_ in (splits.get(sym) or []) if r_ and float(r_) < 1)
            cache[sym] = (b, B.series(b), sd, B.episodes(b, eps_by.get(sym, [])))
        return cache[sym]

    def day(sym, d, eps, b, z, sd):
        """Everything known about (sym, d) for the reconciliation."""
        last = len(b["c"]) - 1
        i = b["ix"].get(d)
        rec = {"sym": sym, "t": d, "has_bar": int(i is not None), "pivot": int((sym, d) in pi)}
        if i is None:
            return rec
        cd = B.conditions(b, z, i, sd) or {}
        rec.update({k: cd.get(k) for k in ("rsi", "low25", "dist", "bounce", "hold_n", "held", "below3", "split120")})
        rec["close"] = round(float(b["c"][i]), 4)
        rec["lab_L"] = B.label(eps, i, last)[0]
        rec["lab_ign"] = B.label(eps, i, last, "IGN")[0]
        rec["lab_L_strict70"] = B.label(eps, i, last, strict=True)[0]
        ld, ep, started = label_d1(eps, i, last)
        rec["lab_D1"], rec["d1_run_started"] = ld, started
        rec["rn_window"] = rn_window(d, limit)
        rr = rn_rows.get((sym, d))
        rec["rn_row"] = int(rr is not None)
        reasons = []
        if sym in K.EXCLUDE:
            reasons.append("EXCLUDED_SYMBOL")
        if not rec["pivot"]:
            reasons.append("NOT_PIVOT_DAY")
        if rec["rn_window"] not in K.WINDOWS:
            reasons.append("OUTSIDE_WINDOWS:" + rec["rn_window"])
        if rec["lab_L"] not in K.EVAL:
            reasons.append("LABEL_" + rec["lab_L"])
        rec["rn_evaluated"] = int(not reasons)
        rec["rn_not_evaluated_because"] = "; ".join(reasons)
        rec["rn_A"] = int(bool(rr) and K.ALL_RULES["RN_A"](rr))
        rec["app_pos"] = int(bool(rr) and K.COND["NEAR15"](rr) and K.COND["BOUNCE10_40"](rr))
        p = pi.get((sym, d)) or {}
        rec["r70_f10"], rec["r70_y10"] = p.get("f10", ""), p.get("y10", "")
        w70 = win_of(d, R70_WIN)
        rec["r70_evaluated"] = int(bool(p) and w70 is not None and p.get("f10") in ("POS", "NEG"))
        t = tr.get((sym, d)) or {}
        w = win_of(d, S70_WIN)
        rec["s70_f10"], rec["s70_split60"] = t.get("f10", ""), t.get("split60", "")
        rec["s70_evaluated"] = int(bool(t) and w is not None and t.get("split60") == "0" and t.get("desc_ok") == "1"
                                   and t.get("f10") in ("POS", "NEG"))
        a = a70.get((sym, d)) or {}
        rec["a70_f10"] = a.get("f10", "")
        rec["a70_evaluated"] = int(bool(a) and A70_WIN[0] <= d <= A70_WIN[1] and a.get("bars") == "OK"
                                   and a.get("f10") in ("POS", "NEG"))
        o = obs.get((sym, d)) or {}
        rec["bot_list"] = (o.get("src", "") + (" READY" if o.get("bot_ready") == "1" else "")) if o else ""
        return rec

    # ── 1. seed episodes ──
    seed_eps, seed_dates = [], []
    for sym in SEEDS + ACTIVE:
        b, z, sd, eps = prep(sym)
        for e in eps:
            ix = {"L": e["L"], "IGN": e["IGN"], "x70": e["x70"], "D1": e["D1"]}
            rec = {"sym": sym, "focus": int((sym, e["launch"]) in FOCUS), "active": int(sym in ACTIVE),
                   "source_record_ready70": r70_ep.get((sym, e["launch"])),
                   "source_record_seq70": {k: e[k] for k in ("sym", "launch", "d1", "peak", "kind_d1", "gain_d1",
                                                            "peak_gain", "quality", "sessions_to_d1", "l10")},
                   "dates": {"trough": b["d"][e["L"] - 1], "L": b["d"][e["L"]], "L10": b["d"][e["L10"]],
                             "IGN": b["d"][e["IGN"]], "x70": b["d"][e["x70"]] if e["x70"] is not None else None,
                             "D1": b["d"][e["D1"]], "peak": b["d"][e["P"]]},
                   "trough_close": round(float(b["c"][e["L"] - 1]), 4),
                   "ign_gain_pct": round((float(b["c"][e["IGN"]]) / float(b["c"][e["IGN"] - 1]) - 1) * 100, 1),
                   "sessions": {"L_to_IGN": e["IGN"] - e["L"], "L_to_D1": e["D1"] - e["L"],
                                "L_to_x70": (e["x70"] - e["L"]) if e["x70"] is not None else None}}
            for a in ANCHORS:
                k0 = ix[a]
                if k0 is None:
                    rec["window_" + a] = None
                    continue
                days = []
                for off in OFFS:
                    k = k0 + off
                    d = b["d"][k] if k >= 0 else None
                    dd = day(sym, d, eps, b, z, sd) if d else {"t": None}
                    dd.update({"anchor": a, "off": off, "episode": f"{sym}|{e['launch']}"})
                    days.append(dd)
                    seed_dates.append(dd)
                rec["window_" + a] = days
            seed_eps.append(rec)
    # DKI's reported 2026-10-07 move: daily bars only
    b, z, sd, eps = prep("DKI")
    k = b["ix"]["2026-10-07"]
    dki = {"episodes": [{"L": b["d"][e["L"]], "D1": b["d"][e["D1"]], "kind": e["kind_d1"], "gain_d1": e["gain_d1"],
                         "peak_gain": e["peak_gain"]} for e in eps],
           "bars": {b["d"][j]: {"open": round(float(b["o"][j]), 4), "high": round(float(b["h"][j]), 4),
                                "low": round(float(b["l"][j]), 4), "close": round(float(b["c"][j]), 4),
                                "volume": int(b["v"][j])} for j in range(k - 1, len(b["c"]))},
           "close_to_close_10_07_pct": round((float(b["c"][k]) / float(b["c"][k - 1]) - 1) * 100, 1),
           "high_vs_prior_close_10_07_pct": round((float(b["h"][k]) / float(b["c"][k - 1]) - 1) * 100, 1),
           "detector_asof": {b["d"][j]: R.detect_asof(b["c"], j) for j in range(k - 1, len(b["c"]))}}
    # ── 2. label limits ──
    gaps = Counter(int(e["l_to_d1"]) for e in rd(os.path.join(K.DATA, "events.csv.gz")) if e["quality"] == "OK")
    lim = {"calendar_last_complete_session": cal[-1], "H_HI": B.H_HI, "MAXGAP": B.MAXGAP,
           "max_L_to_D1_clean": max(gaps), "episodes_at_max_gap": gaps[max(gaps)],
           "L_to_D1_share_ge_7": round(sum(n for g, n in gaps.items() if g >= 7) / sum(gaps.values()), 4),
           "readynow_L_anchored_last_known": cal[len(cal) - 1 - B.H_HI - B.MAXGAP],
           "detection_anchored_last_known (READY70 f10 · SEQ70 · ALERTS70 · a D1-anchored label)":
               cal[len(cal) - 1 - B.H_HI],
           "readynow_holdout_end": K.WINDOWS["holdout"][1], "ready70_test_end": R70_WIN["test"][1],
           "seq70_test_end": S70_WIN["test"][1], "alerts70_unit_end": A70_WIN[1]}
    # ── 3. all clean episodes: placement and the pre-expansion sessions under each label ──
    # Same window rule as rn_lib.events_index (global calendar; pivot rows with cond_ok = 1; the POS710 row must belong
    # to this episode), applied to two anchors: L (READYNOW's primary) and D1 (first detection, observable that day).
    acc = defaultdict(Counter)
    both = Counter()
    edge = Counter()
    for sym in sorted(eps_by):
        if sym not in bars:
            continue
        b, z, sd, eps = prep(sym)
        last = len(b["c"]) - 1
        for e in eps:
            if e["quality"] != "OK":
                continue
            excl = sym in K.EXCLUDE
            gap = e["D1"] - e["L"]
            if gap == B.MAXGAP:          # trough = first close of the 20-session run window (window edge)
                edge["L_to_D1_19"] += 1
                edge["of_which_an_earlier_lower_close_within_20_sessions"] += int(
                    e["L"] >= 2 and float(min(b["c"][max(0, e["L"] - 21): e["L"] - 1])) < float(b["c"][e["L"] - 1]))
            elig = {}
            for a in ("L", "D1"):
                g0 = cix.get(b["d"][e[a]])
                if g0 is None or g0 - 10 < 0:
                    acc["placement"][f"{a}:no_calendar_window"] += 1
                    continue
                lo, hi = cal[g0 - 10], cal[g0 - 7]
                wl, wh = rn_window(lo, limit), rn_window(hi, limit)
                place = wl if wl == wh else f"{wl}|{wh}"
                acc["placement"][f"{a}:{place}"] += 1
                if excl:
                    acc["placement_excluded_symbol"][f"{a}:{place}"] += 1
                days = [cal[g] for g in range(g0 - 10, g0 - 6)]
                piv = [b["ix"][d] for d in days if d in b["ix"] and (rn_rows.get((sym, d)) or {}).get("cond_ok") == "1"]
                labs_L = Counter(B.label(eps, k, last)[0] for k in piv)
                labs_D = Counter(label_d1(eps, k, last)[0] for k in piv)
                own_L = any(B.label(eps, k, last)[1] is e and B.label(eps, k, last)[0] == "POS710" for k in piv)
                own_D = any(label_d1(eps, k, last)[1] is e and label_d1(eps, k, last)[0] == "POS710" for k in piv)
                inrun = sum(1 for k in piv if k >= e["L"])
                c = acc["by_anchor_" + a]
                c["episodes"] += 1
                c["with_pivot_day_in_window"] += bool(piv)
                c["pivot_days_in_window"] += len(piv)
                c["pivot_days_inside_own_run(L<=t)"] += inrun
                c["episodes_with_window_inside_own_run"] += bool(inrun)
                for lab, n in labs_L.items():
                    c["pivot_days_L_label:" + lab] += n
                for lab, n in labs_D.items():
                    c["pivot_days_D1_label:" + lab] += n
                if place in K.WINDOWS and not excl:
                    cw = acc[f"{a}:{place}"]
                    cw["episodes"] += 1
                    cw["with_pivot_day"] += bool(piv)
                    cw["eligible_under_L_label"] += own_L
                    cw["eligible_under_D1_label"] += own_D
                    cw["pivot_days"] += len(piv)
                    cw["pivot_days_IN_EVENT_under_L"] += labs_L.get("IN_EVENT", 0)
                    cw["episodes_all_pivot_days_IN_EVENT_under_L"] += bool(piv) and labs_L.get("IN_EVENT", 0) == len(piv)
                    elig[a] = (place, own_L if a == "L" else own_D)
            if "L" in elig and "D1" in elig and elig["L"][1] and elig["D1"][1]:
                both[elig["D1"][0]] += 1
    acc["eligible_under_both_anchors"] = both
    acc["L_at_run_window_edge"] = edge
    # the symbol-level exclusion: what it removed besides the five seed events
    removed = []
    for s in seed_eps:
        dl = s["dates"]["L"]
        k0 = cix.get(dl)
        if k0 is None or k0 - 10 < 0:
            continue
        place = rn_window(cal[k0 - 10], limit), rn_window(cal[k0 - 7], limit)
        removed.append({"episode": f'{s["sym"]}|{dl}', "focus": s["focus"], "active": s["active"],
                        "window_L": place[0] if place[0] == place[1] else "|".join(place),
                        "rn_pos710_rows_lost": sum(1 for d in s["window_L"] or [] if d.get("pivot") and
                                                   d.get("lab_L") == "POS710" and d.get("rn_window") in K.WINDOWS)})
    excl_rows = Counter()
    for (sym, d), r in rn_rows.items():
        if sym in K.EXCLUDE and r.get("cond_ok") == "1":
            w = rn_window(d, limit)
            if w in K.WINDOWS and r["lab"] in K.EVAL:
                excl_rows[f"{w}:{r['lab']}"] += 1
    # which studies counted seed dates (any of the 7–10-session windows of the five focus events)
    inc = defaultdict(Counter)
    for dd in seed_dates:
        if not dd.get("t") or dd["sym"] in ACTIVE:
            continue
        grp = "focus" if (dd["sym"], dd["episode"].split("|")[1]) in FOCUS else "other"
        for st in ("rn", "r70", "s70", "a70"):
            if dd.get(st + "_evaluated"):
                lab = dd.get("lab_L") if st == "rn" else dd.get(st + "_f10")
                inc[st][f"{grp} · before {dd['anchor']} · {lab}"] += 1
    out = {"note": "descriptive reconciliation; no condition is compared with an outcome",
           "detector": {"code": "ready70/r70_build.detect_asof + episodes_for (Super_stock.scan_explosions)",
                        "jump": "max one-day close-to-close gain over the last EXPLOSION_LOOKBACK=5 sessions >= "
                                "EXPLOSION_PCT=50", "run": "Super_stock._run_explosion: largest trough-to-later-close "
                                "rise within the last EXPLOSION_RUN_LOOKBACK=20 sessions >= EXPLOSION_RUN_PCT=70",
                        "L": "launch = session after the trough close; moved earlier when a later detection of the same"
                             " move reveals an earlier trough (never before the previous episode's peak)",
                        "D1": "first session the detector fires for the episode (observable that day)",
                        "x70": "first close >= 1.70 × the trough close (retrospective: needs L)",
                        "IGN": "largest one-day close gain in [L, D1]", "L10": "first close >= 10% above the trough",
                        "quality": "SPLIT_NEAR if any split is dated in [L − 5 days, D1 + 1 day]",
                        "note": "a jump episode qualifies at +50% close-to-close; x70 may be later or absent"},
           "not_archived_for_any_date": NOT_ARCHIVED,
           "seed_episodes": seed_eps, "dki_2026_10_07": dki, "label_limits": lim,
           "inclusion_by_study_seed_windows": {k: dict(v) for k, v in inc.items()},
           "symbol_exclusion_removed_episodes": removed,
           "symbol_exclusion_removed_rn_rows": dict(excl_rows),
           "all_clean_episodes": {k: dict(v) for k, v in sorted(acc.items())}}
    os.makedirs(out_dir, exist_ok=True)
    json.dump(out, open(os.path.join(out_dir, "recon.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              default=str)
    fields = ["episode", "anchor", "off", "sym", "t", "has_bar", "pivot", "close", "rsi", "low25", "dist", "bounce",
              "hold_n", "held", "below3", "split120", "lab_L", "lab_ign", "lab_L_strict70", "lab_D1", "d1_run_started",
              "rn_window", "rn_row", "rn_evaluated", "rn_not_evaluated_because", "rn_A", "app_pos", "r70_f10", "r70_y10",
              "r70_evaluated", "s70_f10", "s70_split60", "s70_evaluated", "a70_f10", "a70_evaluated", "bot_list"]
    _wcsv(os.path.join(out_dir, "seed_dates.csv.gz"), seed_dates, fields)
    return out


def _digest(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


if __name__ == "__main__":
    if "--check" in sys.argv:
        import tempfile
        tmp = tempfile.mkdtemp()
        build(tmp)
        bad = [f for f in ("recon.json", "seed_dates.csv.gz") if _digest(os.path.join(tmp, f)) != _digest(os.path.join(OUT, f))]
        print("❌ differs: " + ", ".join(bad) if bad else "✅ regenerated identically")
        sys.exit(1 if bad else 0)
    r = build()
    print(json.dumps(r["label_limits"], indent=1))
    print(json.dumps(r["inclusion_by_study_seed_windows"], indent=1, ensure_ascii=False))
