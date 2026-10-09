"""🎯 PERFORMANCE EXPERIMENT — frozen bot (A) vs architecture B vs simple screen (BASE2) on the Phase 4 frozen split with matched
controls (BASE3). Research only: bars < T, Faisal states dated ≤ T, no production code touched, no parameter set here.
Runs only after PERFORMANCE_EXPERIMENT_PREREG.md is merged; outputs under fm_forensics/perf/out/."""
import csv
import json
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
os.environ["FAISAL_ONLY"] = "1"
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "phase4"))
sys.path.insert(0, os.path.join(ROOT, "fm_forensics", "phase3"))
import p4lib as P                        # noqa: E402
import p3lib as L                        # noqa: E402

OUT = os.environ.get("PERF_OUT") or os.path.join(HERE, "out")
P4OUT = os.path.join(ROOT, "fm_forensics", "phase4", "out")
SETS = ("discovery", "validation", "anchor")
SEED, B = 20261009, 2000
RSI_MAX, DROP_MIN = 33.0, 70.0          # BASE2: Faisal's two numeric conditions as the bot encodes them (RSI_OVERSOLD=33; drop ≥ 70%)
HORIZONS = (10, 20, 40, 60)
MOVES = (30, 50, 100)
STRONG_ONLY_CLASSES = ("DIRECT_CHART", "WATCHLIST")


def rd(p):
    return list(csv.DictReader(open(p, encoding="utf-8")))


def base2(sym, T):
    c = L.context(sym, T)
    if not c or c.get("rsi14") is None or c.get("drop_pct") is None:
        return 0
    return int(c["rsi14"] < RSI_MAX and c["drop_pct"] >= DROP_MIN)


def first_a_candidate(sym, T, back=60):
    """earliest day in (T-back, T] with the frozen bot candidate (bot_states → run_gates fallback)."""
    days = [L.shift(T, -k) for k in range(back, -1, -1)]
    seen = set()
    for d in days:
        if d in seen or d > T:
            continue
        seen.add(d)
        g = P.gate_row(sym, d)
        if g["result"] == "PASS":
            return d
    return None


def outcomes(sym, T):
    o = L.outcomes(sym, T)
    if not o:
        return {}
    before = L.bars_before(sym, T); after = L.bars_from(sym, T)
    ref = float(before[-1][4])
    highs = [float(r[2]) for r in after]; lows = [float(r[3]) for r in after]
    res = {}
    for h in HORIZONS:
        for m in MOVES:
            hit = next((i + 1 for i, hh in enumerate(highs[:h]) if hh >= ref * (1 + m / 100)), None)
            res[f"MOVE{m}_{h}"] = int(hit is not None) if len(after) >= min(h, 1) else None
            res[f"T_MOVE{m}_{h}"] = hit
            upto = (hit - 1) if hit else min(h, len(lows))
            res[f"ADV{m}_{h}"] = round((1 - min(lows[:upto]) / ref) * 100, 1) if upto > 0 and lows[:upto] else 0.0
    res["n_after"] = len(after)
    res["right_censored"] = int(len(after) < 20)
    return res


def load_rows():
    rows, ctrls = [], []
    for s in SETS:
        for r in rd(os.path.join(P4OUT, f"arch_rows_{s}.csv")):
            rows.append(r)
        for r in rd(os.path.join(P4OUT, f"arch_controls_{s}.csv")):
            ctrls.append(r)
    return rows, ctrls


def enrich_positive(r):
    sym, T = r["TICKER"], r["DECISION_DATE"]
    a_first = first_a_candidate(sym, T)
    b_obs = r["OBS_SINCE"] or None
    b_alert = r["E2"] or None
    out = dict(r)
    out.update(A_IDENT=int(r["A_candidate"] == "1"), A_FIRST=a_first or "", B_OBS_FIRST=b_obs or "", B_ALERT=b_alert or "",
               B_ALERT_IDENT=int(bool(b_alert) and b_alert <= T), B_OBS_IDENT=int(r["B_observation"] == "1"), BASE2_IDENT=base2(sym, T),
               AMBIGUOUS=int(P.faisal_timeline() and any(x["ticker"] == sym and x["session"] == T and x["date_ambiguous"] for x in P.faisal_timeline())))
    for name, d in (("A", a_first), ("B_OBS", b_obs), ("B_ALERT", b_alert)):
        out[f"LEAD_{name}_TO_FAISAL"] = (L.cal_index(T) - L.cal_index(d)) if d else ""
    oc = outcomes(sym, T)
    out.update({f"OC_{k}": v for k, v in oc.items()})
    for name, d in (("A", a_first), ("B_OBS", b_obs), ("B_ALERT", b_alert)):
        if d:
            o2 = outcomes(sym, d)
            out[f"LEAD_{name}_TO_MOVE50_20"] = (o2.get("T_MOVE50_20") or "")
        else:
            out[f"LEAD_{name}_TO_MOVE50_20"] = ""
    return out


def enrich_control(r):
    sym, T = r["CONTROL"], r["DECISION_DATE"]
    out = dict(r)
    out.update(A_IDENT=int(r["A_candidate"] == "1"), B_OBS_IDENT=int(r["B_observation"] == "1"), B_ALERT_IDENT=int(r["B_watch_ready"] == "1"), BASE2_IDENT=base2(sym, T))
    out.update({f"OC_{k}": v for k, v in outcomes(sym, T).items()})
    return out


def earliest_rows(rows):
    """one row per security: its earliest dated decision (ties → first evidence id)."""
    best = {}
    for r in rows:
        k = r["TICKER"]
        if k not in best or (r["DECISION_DATE"], r["EVIDENCE_ID"]) < (best[k]["DECISION_DATE"], best[k]["EVIDENCE_ID"]):
            best[k] = r
    return best


def sec_recall(rows, flag):
    """security-level: identified on/before the earliest dated decision = flag==1 on ANY row dated ≤ the earliest decision date (rows are ≤ by construction when we take the earliest row); we use the earliest row only."""
    e = earliest_rows(rows)
    return {k: int(v[flag] == 1 or v[flag] == "1") for k, v in e.items()}


def ctrl_rate(ctrls, flag):
    return (sum(int(c[flag]) for c in ctrls), len(ctrls))


def bootstrap(pos_by_sec, ctrl_rows, flag_a, flag_b, seed=SEED, nb=B):
    """cluster bootstrap by security for (recall_b - recall_a) and LR_b/LR_a; controls resampled by matched security."""
    rng = random.Random(seed)
    secs = sorted(pos_by_sec)
    csec = {}
    for c in ctrl_rows:
        csec.setdefault(c["MATCHED_POSITIVE"], []).append(c)
    ckeys = sorted(csec)
    d_rec, lr_ratio = [], []
    for _ in range(nb):
        s = [secs[rng.randrange(len(secs))] for _ in secs]
        ra = sum(pos_by_sec[x][0] for x in s) / len(s); rb = sum(pos_by_sec[x][1] for x in s) / len(s)
        cs = [ckeys[rng.randrange(len(ckeys))] for _ in ckeys]
        crows = [r for k in cs for r in csec[k]]
        fa = sum(int(r[flag_a]) for r in crows) / max(1, len(crows)); fb = sum(int(r[flag_b]) for r in crows) / max(1, len(crows))
        d_rec.append(rb - ra)
        lra = ra / fa if fa > 0 else (float("inf") if ra > 0 else 1.0)
        lrb = rb / fb if fb > 0 else (float("inf") if rb > 0 else 1.0)
        lr_ratio.append(lrb / lra if lra not in (0, float("inf")) and lrb != float("inf") else (float("inf") if lrb == float("inf") else 0.0))
    def ci(xs):
        xs = sorted(x for x in xs if x == x)
        return (xs[int(0.025 * len(xs))], xs[int(0.975 * len(xs)) - 1]) if xs else (None, None)
    return dict(d_recall_ci=ci(d_rec), lr_ratio_ci=ci(lr_ratio))


def summarise(rows, ctrls, label):
    e = earliest_rows(rows)
    out = dict(set=label, rows=len(rows), securities=len(e), control_days=len(ctrls), control_securities=len({c["MATCHED_POSITIVE"] for c in ctrls}))
    pos_by_sec = {k: (int(v["A_IDENT"]), int(v["B_ALERT_IDENT"])) for k, v in e.items()}
    for m, flag in (("A", "A_IDENT"), ("B_ALERT", "B_ALERT_IDENT"), ("B_OBS", "B_OBS_IDENT"), ("BASE2", "BASE2_IDENT")):
        rec = sum(int(v[flag]) for v in e.values()); fk, fn = ctrl_rate(ctrls, flag)
        out[f"{m}_recall_sec"] = f"{rec}/{len(e)}"; out[f"{m}_recall_sec_pct"] = round(rec / len(e), 3) if e else None
        out[f"{m}_recall_rows"] = f"{sum(int(r[flag]) for r in rows)}/{len(rows)}"
        out[f"{m}_ctrl_rate"] = f"{fk}/{fn}"; out[f"{m}_ctrl_rate_pct"] = round(fk / fn, 3) if fn else None
        out[f"{m}_ctrl_wilson"] = P.wilson(fk, fn)
        out[f"{m}_LR"] = round((rec / len(e)) / (fk / fn), 2) if e and fn and fk else (None if not e or not fn else ("inf" if rec else 0.0))
    bs = bootstrap(pos_by_sec, ctrls, "A_IDENT", "B_ALERT_IDENT")
    out["B_minus_A_recall_ci95"] = bs["d_recall_ci"]; out["LRB_over_LRA_ci95"] = bs["lr_ratio_ci"]
    # lead times (securities identified by B alert / A)
    for m, key in (("A", "LEAD_A_TO_FAISAL"), ("B_OBS", "LEAD_B_OBS_TO_FAISAL"), ("B_ALERT", "LEAD_B_ALERT_TO_FAISAL")):
        xs = [int(v[key]) for v in e.values() if v[key] != ""]
        out[f"{m}_lead_to_faisal_sessions"] = P.q(xs)
        out[f"{m}_identified_before_faisal"] = f"{sum(1 for x in xs if x >= 1)}/{len(xs)}"
    # Target C on flagged objects vs controls flagged by the same method
    for m, flag in (("A", "A_IDENT"), ("B_ALERT", "B_ALERT_IDENT"), ("B_OBS", "B_OBS_IDENT"), ("BASE2", "BASE2_IDENT")):
        for grp, rr in (("pos", list(e.values())), ("ctrl", ctrls)):
            fl = [r for r in rr if int(r[flag]) == 1 and r.get("OC_MOVE50_20") not in ("", None)]
            k = sum(int(r["OC_MOVE50_20"]) for r in fl)
            out[f"{m}_{grp}_move50_20"] = f"{k}/{len(fl)}"
            tt = [int(r["OC_T_MOVE50_20"]) for r in fl if r.get("OC_T_MOVE50_20") not in ("", None)]
            out[f"{m}_{grp}_t_move50_median"] = P.q(tt)["median"]
            adv = [float(r["OC_ADV50_20"]) for r in fl if r.get("OC_ADV50_20") not in ("", None)]
            out[f"{m}_{grp}_adverse_median_pct"] = P.q(adv)["median"]
    # all positives / all controls outcome base rates
    for grp, rr in (("pos_all", list(e.values())), ("ctrl_all", ctrls)):
        fl = [r for r in rr if r.get("OC_MOVE50_20") not in ("", None)]
        out[f"{grp}_move50_20"] = f"{sum(int(r['OC_MOVE50_20']) for r in fl)}/{len(fl)}"
    return out


def robustness(rows, ctrls, label):
    res = {}
    r1 = [r for r in rows if r["AMBIGUOUS"] == 0]
    res["no_ambiguous"] = summarise(r1, ctrls, label + "/no_ambiguous") if r1 else None
    strong = {r["TICKER"] for r in rows} - {r["TICKER"] for r in rows if r["EVIDENCE_CLASS"] not in STRONG_ONLY_CLASSES}
    r2 = [r for r in rows if r["TICKER"] not in strong]
    res["no_strong_only"] = summarise(r2, [c for c in ctrls if c["MATCHED_POSITIVE"] not in strong], label + "/no_strong_only") if r2 else None
    res["strong_only_securities"] = sorted(strong)
    return res


def acceptance(sd, sv, rob):
    def lr(x):
        return float("inf") if x == "inf" else (x or 0.0)
    rules = {}
    for name, s in (("discovery", sd), ("validation", sv)):
        rules[f"1_LR_B>=2xLR_A_{name}"] = bool(lr(s["B_ALERT_LR"]) >= 2 * lr(s["A_LR"]) and s["LRB_over_LRA_ci95"][0] is not None and s["LRB_over_LRA_ci95"][0] > 1)
        rules[f"2_recall_gain>=0.10_{name}"] = bool((s["B_ALERT_recall_sec_pct"] - s["A_recall_sec_pct"]) >= 0.10 and s["B_minus_A_recall_ci95"][0] > 0)
        rules[f"3_B_ctrl_rate<=A_{name}"] = bool(s["B_ALERT_ctrl_rate_pct"] <= s["A_ctrl_rate_pct"])
        med = s["B_ALERT_lead_to_faisal_sessions"]["median"]
        rules[f"4_median_lead>=1_{name}"] = bool(med is not None and med >= 1)
        rules[f"6_B_beats_BASE2_LR_{name}"] = bool(lr(s["B_ALERT_LR"]) > lr(s["BASE2_LR"]))
        rb = rob[name]
        ok5 = True
        for sub in ("no_ambiguous", "no_strong_only"):
            t = rb.get(sub)
            if t:
                ok5 = ok5 and lr(t["B_ALERT_LR"]) > lr(t["A_LR"]) and (t["B_ALERT_recall_sec_pct"] - t["A_recall_sec_pct"]) > 0 and t["B_ALERT_ctrl_rate_pct"] <= t["A_ctrl_rate_pct"]
        rules[f"5_robust_direction_{name}"] = bool(ok5)
    evaluable = min(sd["securities"], sv["securities"])
    verdict = "D. INSUFFICIENT EVIDENCE TO TEST" if evaluable < 10 else ("B. PROMISING BUT UNVALIDATED" if all(rules.values()) else "C. NO DEMONSTRATED IMPROVEMENT")
    return rules, verdict


def main():
    os.makedirs(OUT, exist_ok=True)
    P.load_extra()
    rows, ctrls = load_rows()
    pos = [enrich_positive(r) for r in rows]
    ctl = [enrich_control(r) for r in ctrls]
    # Phase 4's cache (phase4/out/extra_states.csv) is a frozen artefact: not rewritten by this experiment
    L.write_csv(os.path.join(OUT, "perf_rows.csv"), pos)
    L.write_csv(os.path.join(OUT, "perf_controls.csv"), ctl)
    summ, rob = {}, {}
    for s in SETS:
        pr = [r for r in pos if r["SET"] == s]; cr = [c for c in ctl if c["SET"] == s]
        summ[s] = summarise(pr, cr, s)
        rob[s] = robustness(pr, cr, s)
    rules, verdict = acceptance(summ["discovery"], summ["validation"], rob)
    # universe-level volume proxy from production logs
    rl = json.load(open(os.path.join(ROOT, "reject_log.json")))
    anchor_per_day = [len(d["walls"].get("M_لا_مستوى_مختبر", [])) for d in rl]
    wl = json.load(open(os.path.join(ROOT, "weekly_watchlist.json")))
    rs = wl.get("reject_stats") or []
    passes = [(x["date"], x["valid"] - sum(x["stats"].values()), x["stats"].get("M_لا_مستوى_مختبر", 0), x["valid"]) for x in rs if isinstance(x, dict) and "valid" in x]
    bs = P.bot_states()
    by = {}
    for (sym, d), r in bs.items():
        b = by.setdefault(d, [0, 0, 0]); b[0] += 1; b[1] += int(r["candidate"] == "1"); b[2] += int(r["gate"] == "ANCHOR")
    vol = dict(reject_log_days=len(rl), anchor_rejects_per_day_min_max=(min(anchor_per_day), max(anchor_per_day)), reject_log_cap=400,
               reject_stats_rows=passes[-10:], panel_days=len(by), panel_median_symbols=sorted(v[0] for v in by.values())[len(by) // 2],
               panel_median_A_candidates=sorted(v[1] for v in by.values())[len(by) // 2], panel_median_anchor_rejects=sorted(v[2] for v in by.values())[len(by) // 2])
    res = dict(main=b"".decode() if False else "b8b1242e91c9fce079a95e6b32e0c76b0e4ba697", summary=summ, robustness=rob, acceptance=rules, verdict=verdict, volume=vol,
               seed=SEED, bootstrap=B)
    json.dump(res, open(os.path.join(OUT, "perf_results.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    print(json.dumps(summ, ensure_ascii=False, indent=1, default=str))
    print("ACCEPTANCE", json.dumps(rules, indent=1)); print("VERDICT", verdict); print("VOLUME", json.dumps(vol, default=str))
    return res


if __name__ == "__main__":
    main()
