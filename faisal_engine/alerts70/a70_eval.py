"""ALERTS70 — the sealed evaluation (one run). Refuses to read any outcome unless A70_PREREG.md matches its hash.

Run from the repo root:  python3 faisal_engine/alerts70/a70_eval.py test
"""
import csv
import gzip
import hashlib
import json
import os
import random
import sys
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
PREREG = os.path.join(HERE, "A70_PREREG.md")
PREREG_SHA256 = "d8227f46c3054e972598cf1112694450b173e20a63515b5aac9dbb16f71eb8da"   # sealed 2026-10-11 before any alert outcome was read
T_FROM, T_TO = "2026-08-17", "2026-09-24"
WIN_TO = "2026-09-29"
BOOT, SEED, ALPHA = 1000, 20261011, 0.025   # 97.5% two-sided = Bonferroni over K1, K2
FLOOR_ROWS, FLOOR_EVENTS, FLOOR_PAIRS = 300, 20, 250
BEFORE70 = ("BEFORE_START", "START_DAY", "UNDERWAY_PRE70")


def prereg_ok():
    return bool(PREREG_SHA256) and os.path.exists(PREREG) and \
        hashlib.sha256(open(PREREG, "rb").read()).hexdigest() == PREREG_SHA256


def rd(name):
    with gzip.open(os.path.join(DATA, name), "rt", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def q(v, p):
    v = sorted(v)
    return v[int(p * (len(v) - 1))] if v else None


def bucket(px):
    return None if px is None else (0 if px < 1 else 1 if px < 3 else 2 if px < 10 else 3)


def cluster_ratio(units, reps=BOOT, seed=SEED, alpha=ALPHA):
    """units: {cluster: [a_n, a_pos, b_n, b_pos]} → ratio of rates with a cluster bootstrap interval."""
    keys = sorted(units)
    tot = [sum(units[k][j] for k in keys) for j in range(4)]

    def ratio(t):
        if not t[0] or not t[2] or not t[3]:
            return None
        return (t[1] / t[0]) / (t[3] / t[2])
    rnd = random.Random(seed)
    vals = []
    for _ in range(reps):
        t = [0, 0, 0, 0]
        for _k in range(len(keys)):
            v = units[keys[rnd.randrange(len(keys))]]
            for j in range(4):
                t[j] += v[j]
        x = ratio(t)
        if x is not None:
            vals.append(x)
    vals.sort()
    pt = ratio(tot)
    lo = vals[int(alpha / 2 * len(vals))] if vals else None
    hi = vals[min(len(vals) - 1, int((1 - alpha / 2) * len(vals)))] if vals else None
    return {"point": round(pt, 3) if pt else None, "lo": round(lo, 3) if lo else None,
            "hi": round(hi, 3) if hi else None, "a_rows": tot[0], "a_pos": tot[1], "b_rows": tot[2], "b_pos": tot[3],
            "clusters": len(keys), "reps_ok": len(vals)}


def pct_ranks(vals):
    s = sorted(v for v in vals if v is not None)
    n = len(s)
    out = {}
    for v in set(vals):
        if v is None:
            continue
        lo = sum(1 for x in s if x < v)
        eq = sum(1 for x in s if x == v)
        out[v] = (lo + 0.5 * eq) / n
    return out


def match_controls(rows):
    """K2 matched control: same session, same price bucket, nearest summed percentile distance on ret1 and volx."""
    by = defaultdict(list)
    for r in rows:
        by[r["t"]].append(r)
    pairs, unmatched = [], 0
    for t, rs in sorted(by.items()):
        rr = pct_ranks([num(r["ret1"]) for r in rs])
        rv = pct_ranks([num(r["volx"]) for r in rs])
        pool = [r for r in rs if r["alerted"] == "0" and num(r["ret1"]) is not None and num(r["volx"]) is not None
                and num(r["px"]) is not None]
        used = set()
        for a in sorted((r for r in rs if r["alerted"] == "1"), key=lambda r: r["sym"]):
            if num(a["ret1"]) is None or num(a["volx"]) is None or num(a["px"]) is None:
                unmatched += 1
                continue
            bk = bucket(num(a["px"]))
            cand = [c for c in pool if c["sym"] not in used and bucket(num(c["px"])) == bk]
            if not cand:
                unmatched += 1
                continue
            c = min(cand, key=lambda c: (abs(rr[num(c["ret1"])] - rr[num(a["ret1"])]) +
                                         abs(rv[num(c["volx"])] - rv[num(a["volx"])]), c["sym"]))
            used.add(c["sym"])
            pairs.append((a, c))
    return pairs, unmatched


def k_tests(rows):
    ev = [r for r in rows if r.get("bars") == "OK" and r["f10"] in ("POS", "NEG")]
    u1 = defaultdict(lambda: [0, 0, 0, 0])
    for r in ev:
        p = r["f10"] == "POS"
        v = u1[r["sym"]]
        if r["alerted"] == "1":
            v[0] += 1
            v[1] += p
        else:
            v[2] += 1
            v[3] += p
    k1 = cluster_ratio(u1)
    pairs, unmatched = match_controls(ev)
    u2 = defaultdict(lambda: [0, 0, 0, 0])
    for a, c in pairs:
        v = u2[a["sym"]]
        v[0] += 1
        v[1] += a["f10"] == "POS"
        v[2] += 1
        v[3] += c["f10"] == "POS"
    k2 = cluster_ratio(u2)
    k2["pairs"], k2["unmatched"] = len(pairs), unmatched
    k2["ret1_median_alerted_vs_control"] = [q([num(a["ret1"]) for a, _ in pairs], .5), q([num(c["ret1"]) for _, c in pairs], .5)]
    k2["volx_median_alerted_vs_control"] = [q([num(a["volx"]) for a, _ in pairs], .5), q([num(c["volx"]) for _, c in pairs], .5)]
    pos_events = {(r["sym"], r["t"], r["f10_k"]) for r in ev if r["alerted"] == "1" and r["f10"] == "POS"}
    return ev, k1, k2, pos_events


def test():
    if not prereg_ok():
        print("⛔ A70_PREREG.md missing or changed — no outcome is read.")
        sys.exit(9)
    obs = [r for r in rd("obs.csv.gz") if T_FROM <= r["t"] <= T_TO]
    alerts = rd("alerts.csv.gz")
    events = rd("events.csv.gz")
    side = rd("side.csv.gz")
    res = {"prereg_sha256": PREREG_SHA256, "window": [T_FROM, T_TO], "alpha": ALPHA, "boot": BOOT, "seed": SEED}
    # ── the test ──
    ev, k1, k2, pos_events = k_tests(obs)
    # distinct events among alerted positives: (symbol, crossing session index proxy t + k)
    sess = sorted({r["t"] for r in rd("obs.csv.gz")})
    six = {d: i for i, d in enumerate(sess)}
    distinct = {(s, six.get(t, 0) + int(float(k))) for s, t, k in pos_events if k}
    res["population"] = {"observed_rows": len(obs), "evaluable_rows": len(ev),
                         "labels": dict(Counter(r["f10"] for r in obs if r.get("bars") == "OK")),
                         "bars_missing": sum(1 for r in obs if r.get("bars") != "OK"),
                         "alerted_evaluable": sum(1 for r in ev if r["alerted"] == "1"),
                         "alerted_symbols": len({r["sym"] for r in ev if r["alerted"] == "1"}),
                         "observed_symbols": len({r["sym"] for r in ev}),
                         "distinct_positive_events_alerted": len(distinct)}
    res["K1"], res["K2"] = k1, k2
    floor_ok = (res["population"]["alerted_evaluable"] >= FLOOR_ROWS and len(distinct) >= FLOOR_EVENTS
                and k2["pairs"] >= FLOOR_PAIRS)
    if not floor_ok:
        verdict = "INSUFFICIENT HISTORICAL ALERT DATA"
    elif (k1["lo"] or 0) > 1.0 and (k2["lo"] or 0) > 1.0:
        verdict = "HISTORICAL ALERT SIGNAL VALIDATED"
    else:
        verdict = "HISTORICAL ALERT SIGNAL NOT VALIDATED"
    res["floor_ok"], res["verdict"] = floor_ok, verdict
    # ── descriptive ──
    d = {}
    win_alerts = [a for a in alerts if a["date"] <= WIN_TO]
    d["alerts"] = {"anchors": len(win_alerts), "symbols": len({a["symbol"] for a in win_alerts}),
                   "sessions": len({a["date"] for a in win_alerts}),
                   "by_record": dict(Counter(a["src"] for a in win_alerts)),
                   "exact_send_time": sum(1 for a in win_alerts if a["t_M1"]),
                   "alert_price": sum(1 for a in win_alerts if a["anchor_price"]),
                   "class": dict(Counter(a["link"] for a in win_alerts))}
    hrs = Counter(a["anchor_et"][:2] for a in win_alerts if a.get("anchor_et"))
    d["alerts"]["et_hour"] = dict(sorted(hrs.items()))
    linked = [a for a in win_alerts if a.get("event")]
    # alert episodes: one per (symbol, event) when linked; unlinked grouped by consecutive alert sessions
    eps = {}
    for a in linked:
        k = (a["symbol"], a["event"])
        if k not in eps or int(a["anchor_ms"]) < int(eps[k]["anchor_ms"]):
            eps[k] = a
    un = sorted((a for a in win_alerts if not a.get("event") and a["link"] not in ("NO_BARS",)),
                key=lambda a: (a["symbol"], a["date"]))
    runs, last = [], {}
    for a in un:
        i = six.get(a["date"])
        prev = last.get(a["symbol"])
        if prev is None or i is None or prev[0] is None or i - prev[0] > 1:
            runs.append(a)
        last[a["symbol"]] = (i, a)
    d["alert_episodes"] = {"linked_episodes": len(eps), "linked_class_first_alert": dict(Counter(a["link"] for a in eps.values())),
                           "unlinked_runs": len(runs), "unlinked_class": dict(Counter(a["link"] for a in runs))}
    lead_l = [int(float(a["to_launch"])) for a in eps.values() if a["link"] in BEFORE70 and a.get("to_launch")]
    lead_d = [int(float(a["to_d1"])) for a in eps.values() if a["link"] in BEFORE70 and a.get("to_d1")]
    gains = [num(a["gain_at_alert"]) for a in eps.values() if a["link"] in ("START_DAY", "UNDERWAY_PRE70")
             and num(a["gain_at_alert"]) is not None]
    d["lead_time_first_alert_before70"] = {
        "n": len(lead_d), "to_launch_q25_med_q75": [q(lead_l, .25), q(lead_l, .5), q(lead_l, .75)],
        "to_d1_q25_med_q75_q90": [q(lead_d, .25), q(lead_d, .5), q(lead_d, .75), q(lead_d, .9)],
        "to_d1_hist": dict(sorted(Counter(lead_d).items())),
        "gain_at_alert_start_or_underway_q25_med_q75": [q(gains, .25), q(gains, .5), q(gains, .75)]}
    el = [e for e in events if e["quality"] == "OK" and int(e["observed_days"] or 0) > 0]
    d["eligible_events"] = {"n": len(el), "symbols": len({e["sym"] for e in el}),
                            "with_any_linked_alert": sum(1 for e in el if int(e["alerts_linked"] or 0) > 0),
                            "first_alert_before_70": sum(1 for e in el if e.get("first_alert_class") in BEFORE70),
                            "first_alert_before_start": sum(1 for e in el if e.get("first_alert_class") == "BEFORE_START"),
                            "first_alert_class": dict(Counter(e.get("first_alert_class") or "NONE" for e in el)),
                            "excluded_split_or_unobserved": len(events) - len(el)}
    alerted_ev = [r for r in ev if r["alerted"] == "1"]
    d["burden"] = {"alerted_symbol_days_per_session": round(len([r for r in obs if r["alerted"] == "1"]) /
                                                          max(1, len({r["t"] for r in obs})), 2),
                   "alerted_evaluable": len(alerted_ev),
                   "alerted_f10_neg": sum(1 for r in alerted_ev if r["f10"] == "NEG"),
                   "alerted_f10_neg_share": round(sum(1 for r in alerted_ev if r["f10"] == "NEG") / max(1, len(alerted_ev)), 4),
                   "alerts_no_event_within_h": sum(1 for a in win_alerts if a["link"] == "NO_EVENT_WITHIN_H"),
                   "alerts_classified": sum(1 for a in win_alerts if a["link"] not in ("NO_BARS", "CENSORED", "UNKNOWN_SPLIT"))}
    full = [r for r in obs if r["final_snapshot_local"] == "1"]
    _ev, s1, s2, _p = k_tests(full)
    d["sensitivity_final_snapshot_days"] = {"rows": len(full), "K1": s1, "K2": s2}
    yk = defaultdict(lambda: [0, 0, 0, 0])
    for r in obs:
        if r.get("bars") != "OK" or r["y10"] not in ("POS", "NEG"):
            continue
        v = yk[r["sym"]]
        p = r["y10"] == "POS"
        if r["alerted"] == "1":
            v[0] += 1
            v[1] += p
        else:
            v[2] += 1
            v[3] += p
    d["strict_y10_K1"] = cluster_ratio(yk, reps=300, alpha=0.05)
    tiers = Counter()
    for a in win_alerts:
        if a.get("tier"):
            tiers[(a["tier"], a["link"])] += 1
    d["tier_by_class"] = {f"{t}|{c}": n for (t, c), n in sorted(tiers.items())}
    d["side_streams"] = {s: dict(Counter(r["link"] for r in side if r["stream"] == s and r["date"] <= WIN_TO))
                         for s in ("operator_entry", "ignition")}
    res["descriptive"] = d
    json.dump(res, open(os.path.join(DATA, "result.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print(json.dumps({k: res[k] for k in ("population", "K1", "K2", "floor_ok", "verdict")}, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if (sys.argv[1:] or [""])[0] == "test":
        test()
    else:
        print("usage: a70_eval.py test")
        sys.exit(2)
