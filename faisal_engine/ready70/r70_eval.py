"""READY70 evaluation — two modes, one file (research · offline · read-only).

  explore : DISCOVERY ONLY (t <= DISC_TO). Rows after DISC_TO are dropped at load time and never parsed into memory.
            Every examined cell is listed in data/explore.json (count of combinations examined).
  test    : runs the single preregistered comparison on the held-out window (t in [TEST_FROM, TEST_TO]).
            Refuses to run unless R70_PREREG.md exists and its SHA-256 equals PREREG_SHA256 below.

Run from the repo root:  python3 faisal_engine/ready70/r70_eval.py explore | test
"""
import csv
import gzip
import hashlib
import json
import math
import os
import random
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PI_FILE = os.path.join(DATA, "pi_obs.csv.gz")
OBS_FILE = os.path.join(DATA, "obs.csv.gz")
PREREG = os.path.join(HERE, "R70_PREREG.md")
PREREG_SHA256 = "67be5d57d8303cb616dad0cfaac09916b2c065ee47641b92c14982757468ee08"   # sealed 2026-10-11 before any test-window read
DISC_FROM, DISC_TO = "2025-05-01", "2025-12-31"
TEST_FROM, TEST_TO = "2026-01-16", "2026-09-24"   # embargo 2026-01-02 .. 2026-01-15 (10 sessions = H)
H = 10
BOOT = 1000
SEED = 20261011


def load(path, t_from, t_to):
    """Stream rows and keep only t in [t_from, t_to]; other rows are discarded before any field is converted."""
    out = []
    with gzip.open(path, "rt", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if t_from <= r["t"] <= t_to:
                out.append(r)
    return out


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


LAB = f"y{H}"                              # switched by set_label()
DURING = {"y": "IN_EVENT", "f": "DURING"}
EPKEY = {"y": f"y{H}_ep", "f": None}


def set_label(kind):
    global LAB
    LAB = f"{kind}{H}"


def evaluable(rows):
    return [r for r in rows if r[LAB] in ("POS", "NEG")]


def _ep(r):
    k = EPKEY[LAB[0]]
    return r[k] if k else f'{r["sym"]}|{int(r["t"][:4]) * 400 + int(r["t"][5:7]) * 31 + int(r["t"][8:10]) + int(r[f"{LAB}_k"] or 0)}'



def cell_stats(rows, flag, base_rate, name):
    """Rate of a launch within H among flagged evaluable rows; flags during an event counted apart."""
    ev = [r for r in rows if r[LAB] in ("POS", "NEG") and flag(r)]
    during = sum(1 for r in rows if r[LAB] == DURING[LAB[0]] and flag(r))
    pos = [r for r in ev if r[LAB] == "POS"]
    days = len({r["t"] for r in rows})
    rate = len(pos) / len(ev) if ev else None
    return {"cell": name, "rows": len(ev), "pos_rows": len(pos), "rate": round(rate, 4) if rate is not None else None,
            "lift": round(rate / base_rate, 3) if rate is not None and base_rate else None,
            "tickers": len({r["sym"] for r in ev}), "events_flagged_before": len({_ep(r) for r in pos}),
            "flags_per_day": round(len(ev) / days, 2) if days else None, "flags_during_event": during}


def cluster_boot_ratio(rows, flag_a, flag_b, reps=BOOT, seed=SEED):
    """Ticker-cluster bootstrap of rate(flag_a) / rate(flag_b) on evaluable rows. Returns (point, lo95, hi95)."""
    ev = evaluable(rows)
    by = defaultdict(lambda: [0, 0, 0, 0])            # a_n, a_pos, b_n, b_pos per ticker
    for r in ev:
        p = r[LAB] == "POS"
        v = by[r["sym"]]
        if flag_a(r):
            v[0] += 1
            v[1] += p
        if flag_b(r):
            v[2] += 1
            v[3] += p
    keys = sorted(by)
    tot = [sum(by[k][j] for k in keys) for j in range(4)]

    def ratio(t):
        if not t[0] or not t[2] or not t[3]:
            return None
        return (t[1] / t[0]) / (t[3] / t[2])
    point = ratio(tot)
    rnd = random.Random(seed)
    vals = []
    for _ in range(reps):
        t = [0, 0, 0, 0]
        for _k in range(len(keys)):
            v = by[keys[rnd.randrange(len(keys))]]
            for j in range(4):
                t[j] += v[j]
        x = ratio(t)
        if x is not None:
            vals.append(x)
    vals.sort()
    if not vals:
        return point, None, None
    lo = vals[int(0.025 * len(vals))]
    hi = vals[min(len(vals) - 1, int(0.975 * len(vals)))]
    return (round(point, 3) if point else None), round(lo, 3), round(hi, 3)


def mom_matched(rows, flag):
    """Burden-matched momentum control: each day, the k rows with the highest 5-session return, k = number of
    rows the candidate flags that day (ties by symbol). Returns a set of (t, sym)."""
    by_day = defaultdict(list)
    for r in rows:
        by_day[r["t"]].append(r)
    keep = set()
    for t, rs in by_day.items():
        k = sum(1 for r in rs if flag(r))
        if not k:
            continue
        ranked = sorted((r for r in rs if num(r["ret5"]) is not None), key=lambda r: (-num(r["ret5"]), r["sym"]))
        keep |= {(r["t"], r["sym"]) for r in ranked[:k]}
    return keep


# ───────────────────────── explore (discovery only) ─────────────────────────
def explore():
    rows = load(PI_FILE, DISC_FROM, DISC_TO)
    assert rows and max(r["t"] for r in rows) <= DISC_TO, "discovery guard"
    st = lambda k: (lambda r: r["pc_stage"] == str(k))                                   # noqa: E731

    def quint(field, ev):
        q = sorted(num(r[field]) for r in ev if num(r[field]) is not None)
        cuts = [q[int(len(q) * p)] for p in (0.2, 0.4, 0.6, 0.8)]
        return cuts, [(f"{field}_q{b + 1}", (lambda bb: lambda r: num(r[field]) is not None
                       and sum(num(r[field]) > c for c in cuts) == bb)(b)) for b in range(5)]
    report = {"window": [DISC_FROM, DISC_TO], "horizon_sessions": H, "labels": {}, "combinations_examined": 0}
    for kind in ("y", "f"):
        set_label(kind)
        ev = evaluable(rows)
        base = sum(r[LAB] == "POS" for r in ev) / len(ev)
        cells = [("ALL", lambda r: True)] + [(f"stage={k}", st(k)) for k in range(5)]
        cells += [("stage=3&sweep", lambda r: r["pc_stage"] == "3" and r["pc_branch"] == "sweep"),
                  ("stage=3&hold", lambda r: r["pc_stage"] == "3" and r["pc_branch"] == "hold"),
                  ("stage=4&sweep", lambda r: r["pc_stage"] == "4" and r["pc_branch"] == "sweep"),
                  ("stage=4&hold", lambda r: r["pc_stage"] == "4" and r["pc_branch"] == "hold"),
                  ("first_rise", lambda r: r["pc_first_rise"] == "1"),
                  ("LOC(current rule approx)", lambda r: r["loc"] == "1")]
        c5, q5 = quint("ret5", ev)
        c20, q20 = quint("range20", ev)
        cells += q5 + q20
        block = {"label": LAB, "counts": dict(Counter(r[LAB] for r in rows)), "base_rate": round(base, 4),
                 "evaluable_rows": len(ev), "tickers": len({r["sym"] for r in ev}),
                 "ret5_cuts": c5, "range20_cuts": c20, "cells": [cell_stats(rows, f, base, n) for n, f in cells],
                 "stage_vs_rest_ci": {}}
        for k in range(5):
            block["stage_vs_rest_ci"][f"stage={k}"] = list(
                cluster_boot_ratio(rows, st(k), lambda r, kk=k: r["pc_stage"] != str(kk), reps=400))
        report["labels"][LAB] = block
        report["combinations_examined"] += len(cells)
    json.dump(report, open(os.path.join(DATA, "explore.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    for lab, blk in report["labels"].items():
        print("==", lab, "base", blk["base_rate"], "rows", blk["evaluable_rows"], "tickers", blk["tickers"], blk["counts"])
        print("   stage_vs_rest_ci", blk["stage_vs_rest_ci"])
        for c in blk["cells"]:
            print("  ", c)
    print("combinations_examined", report["combinations_examined"])


# ───────────────────────── test (held-out window · runs once after the seal) ─────────────────────────
ALPHA = 0.01                                   # 99% intervals = Bonferroni over the 5 preregistered comparisons
BURDEN_MAX_X = 2.0                             # reused limit (UNIVERSE_TEST_PROTOCOL: burden at most 2x the baseline)
MIN_TEST_POS_ROWS, MIN_TEST_EVENTS = 200, 100  # below either ⇒ INSUFFICIENT DATA


def prereg_ok():
    if not os.path.exists(PREREG) or not PREREG_SHA256:
        return False
    return hashlib.sha256(open(PREREG, "rb").read()).hexdigest() == PREREG_SHA256


def wilson(k, n, z=1.959964):
    if not n:
        return None, None
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    r = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return round((c - r) / d, 4), round((c + r) / d, 4)


def boot_ratio(rows, fa, fb, reps=BOOT, seed=SEED, alpha=ALPHA):
    """Ticker-cluster bootstrap of rate(fa)/rate(fb) on evaluable rows (current LAB)."""
    ev = evaluable(rows)
    by = defaultdict(lambda: [0, 0, 0, 0])
    for r in ev:
        p = r[LAB] == "POS"
        v = by[r["sym"]]
        if fa(r):
            v[0] += 1
            v[1] += p
        if fb(r):
            v[2] += 1
            v[3] += p
    keys = sorted(by)
    tot = [sum(by[k][j] for k in keys) for j in range(4)]

    def ratio(t):
        if not t[0] or not t[2] or not t[3]:
            return None
        return (t[1] / t[0]) / (t[3] / t[2])
    rnd = random.Random(seed)
    vals = []
    for _ in range(reps):
        t = [0, 0, 0, 0]
        for _k in range(len(keys)):
            v = by[keys[rnd.randrange(len(keys))]]
            for j in range(4):
                t[j] += v[j]
        x = ratio(t)
        if x is not None:
            vals.append(x)
    vals.sort()
    pt = ratio(tot)
    if not vals:
        return {"point": pt, "lo": None, "hi": None, "reps_ok": 0}
    lo = vals[int((alpha / 2) * len(vals))]
    hi = vals[min(len(vals) - 1, int((1 - alpha / 2) * len(vals)))]
    return {"point": round(pt, 3) if pt else None, "lo": round(lo, 3), "hi": round(hi, 3), "reps_ok": len(vals)}


def matched_set(rows, base_flag, field, sign):
    """Each day: the k rows ranked first by sign*field (ties by symbol), k = #rows base_flag marks that day."""
    by = defaultdict(list)
    for r in rows:
        by[r["t"]].append(r)
    keep = set()
    for t, rs in by.items():
        k = sum(1 for r in rs if base_flag(r))
        if not k:
            continue
        ranked = sorted((r for r in rs if num(r[field]) is not None), key=lambda r: (sign * num(r[field]), r["sym"]))
        keep |= {(r["t"], r["sym"]) for r in ranked[:k]}
    return lambda r: (r["t"], r["sym"]) in keep


def describe(rows, flag, name, cal_ix):
    """All READY-NOW metrics for one rule on the current label (LAB)."""
    ev = [r for r in rows if r[LAB] in ("POS", "NEG")]
    fl = [r for r in ev if flag(r)]
    pos = [r for r in fl if r[LAB] == "POS"]
    days = sorted({r["t"] for r in rows})
    k = f"{LAB}_k" if LAB.startswith("f") else f"{LAB}_to_d1"

    def ev_key(r):
        return (r["sym"], cal_ix[r["t"]] + int(float(r[k])))
    # events = distinct (symbol, crossing session) among POS rows of ANY rule (the observable events)
    all_events = {}
    for r in ev:
        if r[LAB] == "POS":
            key = ev_key(r)
            all_events.setdefault(key, []).append(r)
    caught = {}
    for key, rs in all_events.items():
        fr = [r for r in rs if flag(r)]
        if fr:
            first = min(fr, key=lambda r: r["t"])
            caught[key] = int(float(first[k]))
    leads = sorted(caught.values())
    gains = sorted(num(r["g10_max"]) for r in fl if num(r["g10_max"]) is not None)
    dds = sorted(num(r["g10_dd"]) for r in fl if num(r["g10_dd"]) is not None)
    # READY spells: consecutive flagged sessions per ticker; a spell "returns to watch" without an event if none of its rows is POS
    spells = []
    for sym in {r["sym"] for r in fl}:
        ix = sorted(cal_ix[r["t"]] for r in fl if r["sym"] == sym)
        lab = {cal_ix[r["t"]]: r[LAB] for r in fl if r["sym"] == sym}
        run = [ix[0]]
        for x in ix[1:]:
            if x == run[-1] + 1:
                run.append(x)
            else:
                spells.append((len(run), any(lab[y] == "POS" for y in run)))
                run = [x]
        spells.append((len(run), any(lab[y] == "POS" for y in run)))
    med = (lambda v: v[len(v) // 2] if v else None)
    q = (lambda v, p: v[int(p * (len(v) - 1))] if v else None)
    lo, hi = wilson(len(pos), len(fl))
    return {"rule": name, "flag_rows": len(fl), "pos_rows": len(pos), "rate": round(len(pos) / len(fl), 4) if fl else None,
            "rate_wilson95": [lo, hi], "unproductive_rows": len(fl) - len(pos),
            "flags_per_day": round(len(fl) / len(days), 2), "tickers": len({r["sym"] for r in fl}),
            "tickers_per_day": round(sum(len({r["sym"] for r in fl if r["t"] == d}) for d in days) / len(days), 2),
            "flags_during_detected_event": sum(1 for r in rows if r[LAB] in ("DURING", "IN_EVENT") and flag(r)),
            "events_total": len(all_events), "events_caught_before": len(caught),
            "capture": round(len(caught) / len(all_events), 4) if all_events else None,
            "lead_sessions_median": med(leads), "lead_sessions_q25_q75": [q(leads, .25), q(leads, .75)],
            "gain_from_decision_median": med(gains), "drawdown_from_decision_median": med(dds),
            "spells": len(spells), "spell_len_median": med(sorted(x for x, _ in spells)),
            "spells_without_event": sum(1 for _, e in spells if not e),
            "spells_without_event_share": round(sum(1 for _, e in spells if not e) / len(spells), 4) if spells else None}


def test():
    if not prereg_ok():
        print("⛔ R70_PREREG.md missing or its SHA-256 differs from PREREG_SHA256 — the test window is not read.")
        sys.exit(9)
    rows = load(PI_FILE, TEST_FROM, TEST_TO)
    assert rows and min(r["t"] for r in rows) >= TEST_FROM and max(r["t"] for r in rows) <= TEST_TO
    cal = sorted({r["t"] for r in load(PI_FILE, "0000", "9999")})
    cal_ix = {d: i for i, d in enumerate(cal)}
    disc_tickers = {r["sym"] for r in load(PI_FILE, DISC_FROM, DISC_TO)}
    S1 = lambda r: r["pc_stage"] == "1"                                                    # noqa: E731
    LOC = lambda r: r["loc"] == "1"                                                        # noqa: E731
    ALL = lambda r: True                                                                   # noqa: E731
    res = {"window": [TEST_FROM, TEST_TO], "prereg_sha256": PREREG_SHA256, "alpha": ALPHA, "boot": BOOT, "seed": SEED}
    set_label("f")
    DROP = matched_set(rows, S1, "ret5", +1)
    VOL = matched_set(rows, S1, "range20", -1)
    PRICE = matched_set(rows, S1, "px", +1)
    ev = evaluable(rows)
    res["primary"] = {"label": LAB, "counts": dict(Counter(r[LAB] for r in rows)), "evaluable_rows": len(ev),
                      "tickers": len({r["sym"] for r in ev}), "sessions": len({r["t"] for r in rows}),
                      "pos_rows": sum(r[LAB] == "POS" for r in ev)}
    rules = [("ALL (watch every pivot)", ALL), ("LOC (current READY rule)", LOC), ("STAGE1 (hypothesis)", S1),
             ("DROP-k (generic control)", DROP), ("VOL-k (generic control)", VOL), ("PRICE-k (generic control)", PRICE)]
    res["rules"] = [describe(rows, f, n, cal_ix) for n, f in rules]
    res["primary"]["events_total"] = res["rules"][0]["events_total"]
    comps = {"C1 STAGE1/LOC": (S1, LOC), "C2 STAGE1/ALL": (S1, ALL), "C3a STAGE1/DROP-k": (S1, DROP),
             "C3b STAGE1/VOL-k": (S1, VOL), "C3c STAGE1/PRICE-k": (S1, PRICE)}
    res["ratios_99"] = {k: boot_ratio(rows, a, b) for k, (a, b) in comps.items()}
    r = res["ratios_99"]
    burden_x = (res["rules"][2]["flags_per_day"] / res["rules"][1]["flags_per_day"]) if res["rules"][1]["flags_per_day"] else None
    res["burden_vs_current_x"] = round(burden_x, 3) if burden_x else None
    c = {"C1": bool(r["C1 STAGE1/LOC"]["lo"] and r["C1 STAGE1/LOC"]["lo"] > 1.0),
         "C2": bool(r["C2 STAGE1/ALL"]["lo"] and r["C2 STAGE1/ALL"]["lo"] > 1.0),
         "C3": all(r[k]["lo"] and r[k]["lo"] > 1.0 for k in ("C3a STAGE1/DROP-k", "C3b STAGE1/VOL-k", "C3c STAGE1/PRICE-k")),
         "C4_burden": bool(burden_x is not None and burden_x <= BURDEN_MAX_X)}
    res["criteria"] = c
    enough = res["primary"]["pos_rows"] >= MIN_TEST_POS_ROWS and res["primary"]["events_total"] >= MIN_TEST_EVENTS
    if not enough:
        verdict = "C. INSUFFICIENT DATA"
    elif all(c.values()):
        verdict = "A. VALIDATED SHADOW IMPROVEMENT"
    else:
        verdict = "B. NO VALIDATED IMPROVEMENT"
    res["verdict"] = verdict
    # ── secondary (descriptive, preregistered as non-decisive) ──
    sec = {}
    by_m = defaultdict(list)
    for x in rows:
        by_m[x["t"][:7]].append(x)
    sec["monthly"] = {}
    for m, rs in sorted(by_m.items()):
        e = evaluable(rs)
        rt = (lambda f: (sum(1 for x in e if f(x) and x[LAB] == "POS") / max(1, sum(1 for x in e if f(x)))))
        sec["monthly"][m] = {"rows": len(e), "ALL": round(rt(ALL), 4), "LOC": round(rt(LOC), 4), "STAGE1": round(rt(S1), 4),
                             "DROP-k": round(rt(DROP), 4)}
    for grp, f in (("tickers_seen_in_discovery", lambda x: x["sym"] in disc_tickers),
                   ("tickers_new_in_test", lambda x: x["sym"] not in disc_tickers)):
        sub = [x for x in rows if f(x)]
        sec[grp] = {"tickers": len({x["sym"] for x in sub}),
                    "STAGE1/ALL": boot_ratio(sub, S1, ALL, reps=300, alpha=0.05),
                    "STAGE1/LOC": boot_ratio(sub, S1, LOC, reps=300, alpha=0.05)}
    sec["stages_vs_all_95"] = {f"stage={k}": boot_ratio(rows, (lambda kk: lambda x: x["pc_stage"] == str(kk))(k), ALL,
                                                       reps=300, alpha=0.05) for k in range(5)}
    for kind in ("y",):
        set_label(kind)
        sec["strict_label_y10"] = {"counts": dict(Counter(x[LAB] for x in rows)),
                                   "STAGE1/ALL": boot_ratio(rows, S1, ALL, reps=300, alpha=0.05),
                                   "STAGE1/LOC": boot_ratio(rows, S1, LOC, reps=300, alpha=0.05),
                                   "LOC/ALL": boot_ratio(rows, LOC, ALL, reps=300, alpha=0.05)}
    set_label("f")
    sec["other_horizons_rates"] = {}
    for Hh in (5, 20):
        lab = f"f{Hh}"
        e = [x for x in rows if x[lab] in ("POS", "NEG")]
        if Hh == 20:
            e = [x for x in e if x["t"] <= "2026-09-10"]
        rt = (lambda f: round(sum(1 for x in e if f(x) and x[lab] == "POS") / max(1, sum(1 for x in e if f(x))), 4))
        sec["other_horizons_rates"][lab] = {"rows": len(e), "ALL": rt(ALL), "LOC": rt(LOC), "STAGE1": rt(S1), "DROP-k": rt(DROP)}
    res["secondary"] = sec
    res["bot_tracked"] = bot_tracked_block(cal_ix)
    json.dump(res, open(os.path.join(DATA, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("primary", "ratios_99", "criteria", "burden_vs_current_x", "verdict")},
                     ensure_ascii=False, indent=1))
    for x in res["rules"]:
        print(x)


def bot_tracked_block(cal_ix):
    """The bot's real lists inside the test window (Jul–Sep 2026): actual bot READY vs the hypothesis, same rows;
    and where each +70% event on a tracked symbol stood before it happened (section 9)."""
    rows = [r for r in load(OBS_FILE, TEST_FROM, TEST_TO) if r.get("bars") == "OK"]
    out = {"rows": len(rows), "by_src": dict(Counter(r["src"] for r in rows))}
    set_label("f")
    piv = [r for r in rows if r["src"] in ("watchlist", "carried", "pullback")]
    nw = [r for r in rows if r["src"] == "near_watch"]
    for name, rs in (("pivot_lists", piv), ("near_watch", nw)):
        e = evaluable(rs)
        def rate(f, e=e):
            sel = [x for x in e if f(x)]
            k = sum(1 for x in sel if x[LAB] == "POS")
            return {"rows": len(sel), "pos": k, "rate": round(k / len(sel), 4) if sel else None}
        out[name] = {"ALL": rate(lambda x: True), "BOT_READY (actual)": rate(lambda x: x["bot_ready"] == "1"),
                     "STAGE1": rate(lambda x: x["pc_stage"] == "1"), "LOC": rate(lambda x: x["loc"] == "1")}
    # section 9: events on tracked symbols — state before the event
    ev_rows = defaultdict(list)
    for r in rows:
        if r[LAB] == "POS":
            ev_rows[(r["sym"], cal_ix.get(r["t"], -1) + int(float(r[f"{LAB}_k"])))].append(r)
    s9 = Counter()
    walls = Counter()
    for key, rs in ev_rows.items():
        srcs = {r["src"] for r in rs}
        s9["events"] += 1
        s9["on_pivot_lists"] += bool(srcs & {"watchlist", "carried", "pullback"})
        s9["near_watch_only"] += srcs == {"near_watch"}
        s9["bot_ready_before"] += any(r["bot_ready"] == "1" for r in rs)
        s9["stage1_before"] += any(r["pc_stage"] == "1" for r in rs)
        s9["loc_before"] += any(r["loc"] == "1" for r in rs)
        for r in rs:
            if r["src"] == "near_watch" and r["wall_t1"] not in ("", "NO_LOG"):
                walls[r["wall_t1"]] += 1
                break
        s9["wall_logged"] += any(r["wall_t1"] not in ("", "NO_LOG") for r in rs)
    out["section9_events_on_tracked_symbols"] = dict(s9)
    out["section9_first_logged_wall"] = dict(walls.most_common(8))
    return out


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "explore":
        explore()
    elif mode == "test":
        test()
    else:
        print("usage: r70_eval.py explore | test")
        sys.exit(2)
