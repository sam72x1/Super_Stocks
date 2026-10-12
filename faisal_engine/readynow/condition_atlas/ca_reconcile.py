"""Faisal condition atlas — post-seal reconciliation checks R1–R7 (RECONCILIATION_ADDENDUM.md §0). Descriptive only.

Reads the study's existing rows, labels, events and the frozen model; never writes the sealed files
(CA_PROTOCOL.md, data/model_frozen.json, data/final.json, data/verdict.json). Output: data/reconcile.json.
Run from the repo root:  python3 faisal_engine/readynow/condition_atlas/ca_reconcile.py   (--check regenerates and
compares; --render writes §1–§6 of RECONCILIATION_ADDENDUM.md; --doc-check is the fast CA12 check)
"""
import json
import math
import statistics
import os
import sys
import tempfile
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import numpy as np                                                        # noqa: E402
import ca_build as CB                                                     # noqa: E402
import ca_dev as CD                                                       # noqa: E402
import ca_final as CF                                                     # noqa: E402
import ca_lib as L                                                        # noqa: E402

K, D = L.K, L.D
DATA = L.DATA
WINDOWS = ("development", "validation", "holdout")
REPS, SEED = 2000, 20261011
RECENT = 20                     # R3: a previous episode detected in the 20 sessions before T
FOCUS = ("I04_GROUP_PROXY", "B01_RSI30", "B01b_RSI33")
CLASSES = ("READY_1", "READY_2", "READY_3", "WATCH", "NOT_READY", "INVALIDATED")
num = K.num


def _q(v):
    v = sorted(x for x in v if x is not None)
    if not v:
        return None
    return [v[int((len(v) - 1) * p)] for p in (0.25, 0.5, 0.75)]


def _units(er, f):
    u = defaultdict(lambda: [0, 0, 0, 0])
    for r in er:
        x = u[r["sym"]]
        x[2] += 1
        x[3] += r["lab"] == "POS710"
        if f(r):
            x[0] += 1
            x[1] += r["lab"] == "POS710"
    return u


def r0(rows, stored):
    """D1 (found during this reconciliation, not declared in §0): CA_PROTOCOL.md §⑥ counts 66 condition flags (76
    hypotheses); the code tests len(L.COND) flags and divides 0.05 by that number. For every flag whose stored Bonferroni
    lower bound is at or above 1: reproduce it, then recompute it at 0.05 / 76."""
    er = [r for r in rows if r["lab"] in K.EVAL]
    m = len(stored)
    out = {"flags_in_code": m, "protocol_condition_flags": 66, "protocol_total": 76, "flags": {}}
    for n, v in stored.items():
        b = v["lift_ci_bonferroni"]
        if b and b[0] >= 1.0:
            u = _units(er, L.COND[n])
            _l, c_m = K.cluster_ratio(u, REPS, SEED, 0.05 / m)
            _l, c76 = K.cluster_ratio(u, REPS, SEED, 0.05 / 76)
            out["flags"][n] = {"stored": b, "reproduced": c_m, "at_76": c76}
    return out


def r1(rows, w):
    """The exact claim for I04 in window w."""
    f = L.COND["I04_GROUP_PROXY"]
    er = [r for r in rows if r["lab"] in K.EVAL]
    fl = [r for r in er if f(r)]
    pos = [r for r in fl if r["lab"] == "POS710"]
    lift, ci = K.cluster_ratio(_units(er, f), REPS, SEED, 0.05)
    _m, bars = CB.R.load_bars() if not hasattr(r1, "_bars") else (None, r1._bars)
    r1._bars = bars
    gdays = set()
    for r in fl:
        b = bars[r["sym"]]
        i = b["ix"][r["t"]]
        for j in range(max(1, i - 9), i + 1):
            if CB.candles_at(b["o"], b["h"], b["l"], b["c"], j)["k_groupc"]:
                gdays.add((r["sym"], b["d"][j]))
    base = sum(r["lab"] == "POS710" for r in er) / len(er)
    return {"window": K.WINDOWS[w], "evaluable_rows": len(er), "flagged_rows": len(fl), "pos_flagged": len(pos),
            "base_rate": round(base, 4), "precision": round(len(pos) / len(fl), 4) if fl else None,
            "lift": lift, "lift_ci95": ci, "tickers_flagged": len({r["sym"] for r in fl}),
            "distinct_onsets_among_pos": len({r["ep"] for r in pos}), "distinct_group_candle_days": len(gdays),
            "lead_to_onset_q25_med_q75": _q([num(r.get("to_onset_on")) for r in pos]),
            "lead_to_plus70_close_q25_med_q75": _q([num(r.get("to_q_on")) for r in pos]),
            "decision_time": "the close of session T (bars ≤ T)",
            "label": "POS710 = a clean corrected onset in [T+7, T+10]; IN_EVENT, CENSORED, UNKNOWN_SPLIT rows excluded"}


def r2(rows, by, events, six):
    """Matched ratio and equal-burden differences vs volatility and drop for FOCUS (and any other R7a flag)."""
    saved = dict(K.BURDEN_SCORES)
    K.BURDEN_SCORES.clear()
    K.BURDEN_SCORES.update({"VOLAT_k": CD.SCORES["VOLAT_k"], "DROP_k": CD.SCORES["DROP_k"]})
    out = {}
    try:
        for n in FOCUS:
            f = L.COND[n]
            e = K.evaluate(rows, by, events, six, f, REPS, SEED, 0.05, n)
            m = K.matched(by, f, REPS, SEED, 0.05)
            out[n] = {"lift": e["lift"], "lift_ci95": e["lift_ci"], "matched_ratio": m["ratio"], "matched_ci95": m["ci"],
                      "matched_pairs": m["pairs"], "minus_VOLAT_k_pp": e["VOLAT_k"]["rule_minus_pp"],
                      "minus_VOLAT_k_ci95": e["VOLAT_k"]["rule_minus_pp_ci"],
                      "minus_DROP_k_pp": e["DROP_k"]["rule_minus_pp"], "minus_DROP_k_ci95": e["DROP_k"]["rule_minus_pp_ci"],
                      "flags_per_session": e["flags_per_session"]}
    finally:
        K.BURDEN_SCORES.clear()
        K.BURDEN_SCORES.update(saved)
    return out


def recent_flags(rows):
    """R3 stratum: a previous episode (any quality) of the same symbol detected (D1) in the 20 sessions before T."""
    cal = json.load(open(os.path.join(K.DATA, "calendar.json"), encoding="utf-8"))["sessions"]
    ix = {d: k for k, d in enumerate(cal)}
    d1 = defaultdict(list)
    for e in D.unique_events(K.rd("events.csv.gz", D.DATA)):
        if e["d1"] in ix:
            d1[e["sym"]].append(ix[e["d1"]])
    for r in rows:
        t = ix.get(r["t"])
        r["_recent"] = bool(t is not None and any(t - RECENT <= k <= t - 1 for k in d1.get(r["sym"], [])))


def r3(rows):
    f = L.COND["I04_GROUP_PROXY"]
    er = [r for r in rows if r["lab"] in K.EVAL]
    out = {"i04_rows_recent_share": round(sum(1 for r in er if f(r) and r["_recent"]) / max(1, sum(1 for r in er if f(r))), 4)}
    for name, keep in (("recent", True), ("not_recent", False)):
        rs = [r for r in er if r["_recent"] == keep]
        fl = [r for r in rs if f(r)]
        lift, ci = K.cluster_ratio(_units(rs, f), REPS, SEED, 0.05)
        out[name] = {"rows": len(rs), "base_rate": round(sum(r["lab"] == "POS710" for r in rs) / len(rs), 4) if rs else None,
                     "i04_flagged": len(fl), "i04_prevalence": round(len(fl) / len(rs), 4) if rs else None,
                     "i04_precision": round(sum(r["lab"] == "POS710" for r in fl) / len(fl), 4) if fl else None,
                     "i04_lift": lift, "i04_lift_ci95": ci}
    return out


def r4(rows):
    return {str(k): v for k, v in CD.lead_profile(rows, L.COND["I04_GROUP_PROXY"], maxk=10).items()}


def _hyper_ge(N, Kp, n, x):
    """P(X ≥ x) for a hypergeometric draw of n from N containing Kp successes."""
    tot = math.comb(N, n)
    return round(sum(math.comb(Kp, k) * math.comb(N - Kp, n - k) for k in range(x, min(n, Kp) + 1)) / tot, 4) if tot else None


def r5(rows, events, cls):
    ev_all = {(e["sym"], e["onset"]): e for e in D.unique_events(K.rd("events.csv.gz", D.DATA))}
    elig = [e for e in events if e["pos_rows"]]
    gain = {(e["sym"], e["launch"]): num(ev_all[(e["sym"], e["launch"])]["peak_gain"]) for e in elig}
    ready = ("READY_1", "READY_2", "READY_3")
    allinv = {(e["sym"], e["launch"]) for e in elig if all(L.invalidated(r) for r in e["pos_rows"])}
    comp = {c: sum(1 for e in elig if (e["sym"], e["launch"]) in allinv and all(L.COND[c](r) for r in e["pos_rows"]))
            for c in L.INVALID}
    cap = [e for e in elig if any(cls.get((r["sym"], r["t"])) in ready for r in e["pos_rows"])]
    capk = {(e["sym"], e["launch"]) for e in cap}
    mis = [e for e in elig if (e["sym"], e["launch"]) not in capk]
    key = lambda e: -(gain[(e["sym"], e["launch"])] or 0.0)          # noqa: E731
    top6 = sorted(mis, key=key)[:6]
    x6 = sum(1 for e in top6 if (e["sym"], e["launch"]) in allinv)
    k_mis = sum(1 for e in mis if (e["sym"], e["launch"]) in allinv)
    top20 = sorted(elig, key=key)[:20]
    x20 = sum(1 for e in top20 if (e["sym"], e["launch"]) in allinv)
    g_inv = [gain[k] for k in gain if k in allinv]
    g_oth = [gain[k] for k in gain if k not in allinv]
    return {"eligible": len(elig), "all_invalidated": len(allinv), "all_invalidated_by_component_all_days": comp,
            "captured_by_ready": len(cap), "captured_and_all_invalidated": len(allinv & capk),
            "missed": len(mis), "missed_all_invalidated": k_mis,
            "top6_missed": [{"sym": e["sym"], "onset": e["launch"], "peak_gain": gain[(e["sym"], e["launch"])],
                             "all_invalidated": (e["sym"], e["launch"]) in allinv,
                             "components_on_every_day": [c for c in L.INVALID if all(L.COND[c](r) for r in e["pos_rows"])]}
                            for e in top6],
            "top6_missed_all_invalidated": x6, "p_top6_ge_x_given_missed_share": _hyper_ge(len(mis), k_mis, 6, x6),
            "top20_all_invalidated": x20, "p_top20_ge_x_given_eligible_share": _hyper_ge(len(elig), len(allinv), 20, x20),
            "median_peak_gain_invalidated": _q(g_inv), "median_peak_gain_other": _q(g_oth)}


def _class_units(er, cls):
    u = defaultdict(lambda: np.zeros(2 * len(CLASSES)))
    for r in er:
        c = cls.get((r["sym"], r["t"]))
        if c in CLASSES:
            j = CLASSES.index(c)
            u[r["sym"]][2 * j] += 1
            u[r["sym"]][2 * j + 1] += r["lab"] == "POS710"
    return u


PAIRS = (("READY_1", "READY_2"), ("READY_2", "READY_3"), ("READY_1", "READY_3"), ("READY", "WATCH"),
         ("WATCH", "NOT_READY"), ("INVALIDATED", "READY_1"))


def _boot_classes(units):
    keys = sorted(units)
    a = np.array([units[k] for k in keys])
    rng = np.random.default_rng(SEED)
    sums = np.empty((REPS, a.shape[1]))
    for j in range(0, REPS, 200):
        m = min(200, REPS - j)
        idx = rng.integers(0, len(keys), size=(m, len(keys)))
        sums[j:j + m] = a[idx].sum(axis=1)
    tot = a.sum(axis=0)

    def prec(s, c):
        if c == "READY":
            n = s[..., 0] + s[..., 2] + s[..., 4]
            p = s[..., 1] + s[..., 3] + s[..., 5]
        else:
            j = CLASSES.index(c)
            n, p = s[..., 2 * j], s[..., 2 * j + 1]
        with np.errstate(divide="ignore", invalid="ignore"):
            return 100.0 * p / n
    out = {"precision_pct": {}, "diff_pp": {}}
    for c in CLASSES + ("READY",):
        est, bs = float(prec(tot, c)), prec(sums, c)
        bs = bs[np.isfinite(bs)]
        out["precision_pct"][c] = [round(est, 2), [round(float(np.quantile(bs, .025)), 2),
                                                   round(float(np.quantile(bs, .975)), 2)]]
    for a1, b1 in PAIRS:
        est = float(prec(tot, a1) - prec(tot, b1))
        bs = prec(sums, a1) - prec(sums, b1)
        bs = bs[np.isfinite(bs)]
        out["diff_pp"][f"{a1}-{b1}"] = [round(est, 2), [round(float(np.quantile(bs, .025)), 2),
                                                        round(float(np.quantile(bs, .975)), 2)]]
    return out


def r6(w, rows, by, events, fz, cls):
    er = [r for r in rows if r["lab"] in K.EVAL]
    tab = CD.class_table(rows, cls, events)
    res = {"class_table_equals_sealed": (tab == json.load(open(os.path.join(DATA, "final.json"),
                                                               encoding="utf-8"))[w]["classes"]) if w != "development"
           else None, "units": None}
    # equal burden: W_k vs the tool's per-session count
    tc = D.REFS["TC_TECH"]
    short = 0
    for t, rs in by.items():
        k = sum(1 for r in rs if tc(r))
        valid = sum(1 for r in rs if not L.invalidated(r))
        if valid < k:
            short += 1
    res["sessions"] = len(by)
    res["sessions_where_valid_rows_fewer_than_k"] = short
    u = _class_units(er, cls)
    res["bootstrap"] = _boot_classes(u)
    res.pop("units")
    return res, u


def r7(stored_dev, final, r2_all):
    dev = stored_dev["strength"]
    a = [n for n in dev if dev[n]["lift_ci"] and dev[n]["lift_ci"][0] > 1 and all(
        final[w]["conditions"][n]["lift_ci"] and final[w]["conditions"][n]["lift_ci"][0] > 1 for w in ("validation",
                                                                                                       "holdout"))]
    b = {n: all(r2_all[w][n]["matched_ci95"] and r2_all[w][n]["matched_ci95"][0] > 1 for w in WINDOWS)
         for n in a if n in FOCUS}
    c_dev = [n for n in dev if (dev[n]["VOLAT_k"]["rule_minus_pp_ci"] or [0])[0] > 0
             or (dev[n]["DROP_k"]["rule_minus_pp_ci"] or [0])[0] > 0]
    c_26 = [n for n in FOCUS for w in ("validation", "holdout")
            if (r2_all[w][n]["minus_VOLAT_k_ci95"] or [0])[0] > 0 or (r2_all[w][n]["minus_DROP_k_ci95"] or [0])[0] > 0]
    return {"flags_tested": len(dev), "R7a_lift_lower_above_1_all_three": a, "R7a_all_in_focus": all(n in FOCUS for n in a),
            "R7b_matched_lower_above_1_all_three": b,
            "R7c_beats_volatility_or_drop_dev_any_flag": c_dev, "R7c_beats_volatility_or_drop_2026_focus": sorted(set(c_26))}


def build(out_dir=DATA):
    fz = json.load(open(os.path.join(DATA, "model_frozen.json"), encoding="utf-8"))
    stored_dev = json.load(open(os.path.join(DATA, "strength_dev.json"), encoding="utf-8"))
    final = json.load(open(os.path.join(DATA, "final.json"), encoding="utf-8"))
    res = {"note": "post-seal descriptive reconciliation; sealed files unchanged", "R0": {}, "R1": {}, "R2": {}, "R3": {},
           "R4": {}, "R5": {}, "R6": {}}
    pooled_units = {}
    for w in WINDOWS:
        rows, by, _m = L.load(w)
        events, six = D.events(rows, w)
        cls = CF.classify_window(w, fz)
        recent_flags(rows)
        if w == "development":
            res["R0"] = r0(rows, stored_dev["strength"])
        res["R1"][w] = r1(rows, w)
        res["R2"][w] = r2(rows, by, events, six)
        res["R3"][w] = r3(rows)
        res["R4"][w] = r4(rows)
        res["R5"][w] = r5(rows, events, cls)
        res["R6"][w], u = r6(w, rows, by, events, fz, cls)
        if w != "development":
            pooled_units.update({f"{w[0]}|{k}": v for k, v in u.items()})
    res["R6"]["pooled_2026"] = _boot_classes(pooled_units)
    res["R7"] = r7(stored_dev, final, res["R2"])
    os.makedirs(out_dir, exist_ok=True)
    json.dump(res, open(os.path.join(out_dir, "reconcile.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1,
              sort_keys=True)
    return res


# ───────────────────────── RECONCILIATION_ADDENDUM.md §1–§6 (rendered from data/reconcile.json) ─────────────────────────
ADDENDUM = os.path.join(HERE, "RECONCILIATION_ADDENDUM.md")
PREFIX_BYTES = 3140           # §0 as written before the first run (2026-10-11 23:50 UTC); pinned below
PREFIX_SHA256 = "6a6422ae3b9c3e2fd562dd2014e5479909c2af0ea87e1178b26315509873699b"
MARK = ("<!-- §1–§6 below are generated by `ca_reconcile.py --render` from data/reconcile.json, data/casebook.json and "
        "the sealed files; §0 above is pinned by SHA-256 (test_ca.py CA12). -->")
SEALED_DATA = {           # bytes of the sealed run's inputs and outputs (CA12 checks every value)
    "CA_PROTOCOL.md": "457d9703963a988be2806aad0cdfb80788ad8bf7ac025280c309ad78a5941d34",
    "data/model_frozen.json": "482b9d580c3cccaf5aace7c06deab312356f4b10baa73f46054ada94e4d2d849",
    "data/final.json": "546c5a5ca6e1b720163ff099e89292c2e8eb7ee0a10751e48a5e1faea0de2148",
    "data/verdict.json": "1bb2238b7c2cb1a173bb397d541a59c74a09c9710c8db506fa6fd110447ee87a",
    "data/ca_rows.csv.gz": "423937f24c59478d9223c68861dd8e44732344d567dc7f9c2c6fb2e4587147df",
    "data/strength_dev.json": "887c1b2ebe0a1885ce4a0a7428bcfee43a82aaf2843ecb68d88e1a77d1d0c581",
    "data/model_dev.json": "de54d3902fde349788b650d5d17477b1e59afe67cac5847eec7ccddafdc74414"}
SEALED_CODE = {           # recorded when this task started; compared before the commit, not pinned by a guard
    "ca_final.py": "9c0b6a18595258351a336ec40f801a8cc42e42ea068c595f01c6aaea73c19716",
    "ca_lib.py": "8053c9078a6486d766733728e51dd0c0164b418827a55daefb3786164ff67640",
    "ca_build.py": "8ce2db9cab641209fe0836f550572e6e93d9e73feb2d2f3c306b2711f93b552b",
    "ca_dev.py": "ce7d02297b35d6208f2e7a23dde3d4d923a2c9355d718509dc13829ceb671ce2",
    "ca_atlas.py": "a188464a1f1f1ae664e77b52bf3d80c005390a3183d9c984335e23fcb0b88b3b"}
NAMES = {"I04_GROUP_PROXY": "group-candle proxy", "B01_RSI30": "RSI < 30", "B01b_RSI33": "RSI < 33"}


def _sha(path):
    import hashlib
    return hashlib.sha256(open(os.path.join(HERE, path), "rb").read()).hexdigest()


def _ci(x):
    return f"[{x[0]}, {x[1]}]" if x else "—"


def _pp(v, c):
    return f"{v:+.2f} [{c[0]:+.2f}, {c[1]:+.2f}]" if v is not None and c else "—"


def _q3(x):
    return " · ".join(str(int(v)) if float(v).is_integer() else str(v) for v in x) if x else "—"


def _lo_above(c, x=1.0):
    return bool(c) and c[0] > x


def _wl(ws):
    return ", ".join(ws) if ws else "none"


def render(res, cb):
    R0, R1, R2, R3, R4, R5, R6, R7 = (res[k] for k in ("R0", "R1", "R2", "R3", "R4", "R5", "R6", "R7"))
    L = [MARK, "", "## 1. «شمعة القروب»: the original meaning and the exact claim", "",
         "**In the sources (traced to the images; the quotes are verbatim).** Faisal uses «القروبات» (retail pump "
         "groups) as a validity and risk condition, never as a forecast:", "",
         "- What it looks like: «القروبات ترفع السهم بشموع غبيه توصل 20٪ تجد شمعه طويله خضرا او حمرا بدون جسم ع فريم "
         "4 ساعات» (X_20260827_checklist_7points, item 6).",
         "- The rule: «الشرط خالي من القروبات» (IMG_0151, TG_1819); «شرط شموعه شموع مضارب مادخل فيه قروبات لعبت "
         "بالشموع» (IMG_0497); «الشرط كالعاده مالم تدخل قروبات» (TG_2090).",
         "- Why: «دخول سيوله قروبات او غيره لا انا ولا اكبر محلل يستطيع قراءة الشموع» (IMG_0488) — the candles stop "
         "being readable.",
         "- What follows: «دخل قروب غبي رفع السهم من 2.50 ل 3.30 … المضارب ضغط السهم ب 86 الف سهم من 2.80 ل 1.90» "
         "(IMG_0316); «سهم تجميع تدخل سيوله قروبات الى الهاويه» ($LABT, TG_1835).",
         "- The words «شمعة قروب» themselves come from a third-party education channel (EDU_20260827_dki_group_candle: "
         "a DKI 4-hour candle 3.91 → 5.05, then a collapse, «يربح 5 يخسر 50»). A follower's post (TG_20260905_03, "
         "not Faisal): «Jz · Ezra · Icu كلها لقطوها قروبات ع 20٪ وهبطت علينا ودخلنا من جديد».", "",
         "So the condition means: groups are in, the candles cannot be read, the operator may press the stock down — "
         "stay out. It says nothing about whether a +70% leg comes 7–10 sessions later.", "",
         "**In the study.** I04_GROUP_PROXY = at least one daily candle in T−9…T whose range is at least 20% of the "
         "previous close and whose body is at most 25% of the range (`k_groupc`, `a_grp10 ≥ 1`). It is a daily "
         "stand-in for a 4-hour shape; group participation itself is not observable in the data. One such candle "
         "flags up to ten consecutive pivot-days of the stock.", "",
         "**R1 · the exact claim.** Decision time: the close of session T, bars ≤ T only. Label: POS710 = a clean "
         "corrected onset (start of the final +70% leg) in [T+7, T+10]; rows inside an event, censored or with an "
         "unknown split are not evaluable. Baseline: the window's base rate over all evaluable pivot-days. Interval: "
         "ticker-cluster bootstrap, 2,000 resamples, seed 20261011.", "",
         "| window | evaluable | flagged | POS710 flagged | base | precision | lift [95%] | tickers | distinct "
         "onsets among POS | distinct group-candle days | T → onset (q25 · med · q75) | T → +70% close |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in WINDOWS:
        x = R1[w]
        L.append(f'| {w} {x["window"][0]} → {x["window"][1]} | {x["evaluable_rows"]:,} | {x["flagged_rows"]:,} | '
                 f'{x["pos_flagged"]} | {x["base_rate"]:.2%} | {x["precision"]:.2%} | {x["lift"]} {_ci(x["lift_ci95"])} | '
                 f'{x["tickers_flagged"]} | {x["distinct_onsets_among_pos"]} | {x["distinct_group_candle_days"]:,} | '
                 f'{_q3(x["lead_to_onset_q25_med_q75"])} | {_q3(x["lead_to_plus70_close_q25_med_q75"])} |')
    rpo = [round(R1[w]["pos_flagged"] / R1[w]["distinct_onsets_among_pos"], 1) for w in WINDOWS]
    L += ["", f'The lifts are the stored ones (CONDITION_STRENGTH_RESULTS.md: {R1["development"]["lift"]} · '
              f'{R1["validation"]["lift"]} · {R1["holdout"]["lift"]}). **Independence:** the POS710 rows come from far '
              f'fewer onsets ({rpo[0]} · {rpo[1]} · {rpo[2]} flagged POS rows per onset) and one candle flags up to ten '
              "rows, so the rows are not independent; the interval resamples tickers for that reason. The lead to the "
              "onset is 7–10 by construction of the label; the median lead to the +70% close is "
              f'{_q3([R1[w]["lead_to_plus70_close_q25_med_q75"][1] for w in WINDOWS])} sessions.', "",
          "## 2. Prediction, or a marker of stocks that are already active? (R2 · R3 · R4)", "",
          "**R2 · beyond volatility.** Matched = same session, same price bucket, volume, volatility and dollar-volume "
          "percentiles within 0.10 (unmatched rows dropped). Equal burden = as many rows per session as the flag, "
          "ranked by 20-session range (volatility) or by the 5-session fall (drop).", "",
          "| flag | window | lift [95%] | matched ratio [95%] · pairs | − volatility pp [95%] | − drop pp [95%] |",
          "|---|---|---|---|---|---|"]
    for n in FOCUS:
        for w in WINDOWS:
            x = R2[w][n]
            L.append(f'| {NAMES[n]} | {w} | {x["lift"]} {_ci(x["lift_ci95"])} | {x["matched_ratio"]} '
                     f'{_ci(x["matched_ci95"])} · {x["matched_pairs"]:,} | {_pp(x["minus_VOLAT_k_pp"], x["minus_VOLAT_k_ci95"])} | '
                     f'{_pp(x["minus_DROP_k_pp"], x["minus_DROP_k_ci95"])} |')
    surv = {n: [w for w in WINDOWS if _lo_above(R2[w][n]["matched_ci95"])] for n in FOCUS}
    beat = {n: [w for w in WINDOWS if (R2[w][n]["minus_VOLAT_k_ci95"] or [0])[0] > 0
                or (R2[w][n]["minus_DROP_k_ci95"] or [0])[0] > 0] for n in FOCUS}
    L += ["", "**R3 · after a recent episode.** «recent» = an earlier episode of the same stock was detected (D1) in the "
              "20 sessions before T.", "",
          "| window | stratum | rows | base | group-candle prevalence | lift [95%] |", "|---|---|---|---|---|---|"]
    hot, cold = [], []
    for w in WINDOWS:
        for s in ("recent", "not_recent"):
            x = R3[w][s]
            L.append(f'| {w} | {s.replace("_", " ")} | {x["rows"]:,} | {x["base_rate"]:.2%} | {x["i04_prevalence"]:.1%} | '
                     f'{x["i04_lift"]} {_ci(x["i04_lift_ci95"])} |')
        r_, n_ = _lo_above(R3[w]["recent"]["i04_lift_ci95"]), _lo_above(R3[w]["not_recent"]["i04_lift_ci95"])
        (hot if r_ and not n_ else cold if n_ and not r_ else []).append(w)
    L += ["", "**R4 · countdown or state?** Share of rows with the group-candle proxy k sessions before a clean onset, "
              "against rows with no onset within 10 sessions («far»).", "",
          "| window | far | T−10 | T−9 | T−8 | T−7 | T−6 | T−5 | T−4 | T−3 | T−2 | T−1 |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in WINDOWS:
        lp = R4[w]
        L.append(f'| {w} | {lp["far"][1]:.1%} | ' + " | ".join(f'{lp[str(k)][1]:.1%}' for k in range(10, 0, -1)) + " |")
    span = {w: (min(R4[w][str(k)][1] for k in range(1, 11)), max(R4[w][str(k)][1] for k in range(1, 11))) for w in WINDOWS}
    prev = {w: (R3[w]["recent"]["i04_prevalence"], R3[w]["not_recent"]["i04_prevalence"]) for w in WINDOWS}
    L += ["", "**Reading.**", "",
          "- **Association:** the group-candle proxy has a lift lower bound above 1 in all three windows (R1).",
          f'- **Beyond volatility:** its matched lower bound is above 1 in {_wl(surv["I04_GROUP_PROXY"])} only; at equal '
          f'burden it beats the volatility or drop ranking in {_wl(beat["I04_GROUP_PROXY"])}. Most of its association '
          "is the volatility it marks.",
          "- **Already active:** it is about three times as common after a recent episode (prevalence "
          + " · ".join(f"{prev[w][0]:.0%} vs {prev[w][1]:.0%}" for w in WINDOWS) + "). The R3 criterion (lift lower "
          f'bound above 1 only in the recent stratum) is met in {_wl(hot)}; the opposite pattern in {_wl(cold)}; '
          f'{_wl([w for w in WINDOWS if w not in hot + cold])}: neither stratum. Mixed, '
          "so «only an already-hot marker» is not established either.",
          "- **Timing:** its prevalence is flat from T−10 to T−1 ("
          + " · ".join(f"{span[w][0]:.0%}–{span[w][1]:.0%} vs far {R4[w]['far'][1]:.0%}" for w in WINDOWS)
          + "): a state that is somewhat more common before onsets, not a countdown to one.",
          "- **Answer:** the proxy marks wide, active stocks. It is not shown to predict a leg 7–10 sessions ahead "
          "beyond volatility, it is not an entry condition (Faisal's use is the opposite: stay out), and it is a daily "
          "stand-in for a 4-hour shape. In-event rows never enter (they are not evaluable).", "",
          "## 3. The missed winners (R5)", "",
          "An invalidated pivot-day cannot be READY (CA7). An event whose every pivot-day in T−10…T−7 is invalidated "
          "is therefore missed by construction. Invalidated = chasing (I01) or exploded within 5 sessions (I03) or the "
          "group-candle proxy (I04).", "",
          "| window | eligible | all T−10…T−7 invalidated | … I04 every day · I01 · I03 | captured by READY | "
          "captured and all invalidated | missed | missed and all invalidated | 6 largest missed: all invalidated "
          "(P ≥) | 20 largest: all invalidated (P ≥) | peak gain % q25 · med · q75: invalidated / other |",
          "|---|---|---|---|---|---|---|---|---|---|---|"]
    for w in WINDOWS:
        x = R5[w]
        c = x["all_invalidated_by_component_all_days"]
        L.append(f'| {w} | {x["eligible"]} | {x["all_invalidated"]} ({x["all_invalidated"] / x["eligible"]:.1%}) | '
                 f'{c["I04_GROUP_PROXY"]} ({c["I04_GROUP_PROXY"] / x["eligible"]:.1%}) · {c["I01_CHASE"]} · '
                 f'{c["I03_BOOM5"]} | {x["captured_by_ready"]} | {x["captured_and_all_invalidated"]} | {x["missed"]} | '
                 f'{x["missed_all_invalidated"]} ({x["missed_all_invalidated"] / x["missed"]:.1%}) | '
                 f'{x["top6_missed_all_invalidated"]}/6 ({x["p_top6_ge_x_given_missed_share"]}) | '
                 f'{x["top20_all_invalidated"]}/20 ({x["p_top20_ge_x_given_eligible_share"]}) | '
                 f'{_q3(x["median_peak_gain_invalidated"])} / {_q3(x["median_peak_gain_other"])} |')
    L += ["", "The six largest missed events per window (peak gain; components present on every pivot-day of "
              "T−10…T−7; trough of the final leg against T−7; from data/casebook.json):", "",
          "| window | symbol | onset | peak gain | all invalidated | components every day | trough | trough after T−7 | "
          "kind | max distance above the 25-session low at T−10…T−7 |", "|---|---|---|---|---|---|---|---|---|---|"]
    after, dmx, kinds = {}, {}, {}
    for w in WINDOWS:
        cases = {(c["sym"], c["dates"]["onset"]): c for c in cb[w]["missed"]}
        for e in R5[w]["top6_missed"]:
            c = cases.get((e["sym"], e["onset"]))
            tr = c["dates"]["trough"] if c else None
            t7 = next((t["date"] for t in c["timeline"] if t["T"] == "T-7"), None) if c else None
            dmax = max((float(t["dist"]) for t in c["timeline"] if t.get("dist") not in (None, "")), default=None) if c else None
            aft = bool(tr and t7 and tr > t7)
            after.setdefault(w, []).append(aft)
            kinds.setdefault(w, []).append(c["dates"]["kind"] if c else None)
            if dmax is not None:
                dmx.setdefault(w, []).append(dmax)
            L.append(f'| {w} | {e["sym"]} | {e["onset"]} | {e["peak_gain"]}% | {"yes" if e["all_invalidated"] else "no"} | '
                     f'{", ".join(e["components_on_every_day"]) or "—"} | {tr or "—"} | {"yes" if aft else "no"} | '
                     f'{c["dates"]["kind"] if c else "—"} | {dmax if dmax is not None else "—"}% |')
    v = R5["validation"]
    v_i04 = sum(1 for e in v["top6_missed"] if "I04_GROUP_PROXY" in e["components_on_every_day"])
    L += ["", "**Reading.**", "",
          "- **By construction:** «captured and all invalidated» is 0 in every window. "
          + " · ".join(f'{R5[w]["missed_all_invalidated"] / R5[w]["missed"]:.0%}' for w in WINDOWS)
          + " of the missed events (development · validation · holdout) were unreachable for READY before any score "
          "was read.",
          "- **The «20–31%» figure** in the first FINAL_FINDINGS.md was the union of the three invalidation states ("
          + " · ".join(f'{R5[w]["all_invalidated"] / R5[w]["eligible"]:.1%}' for w in WINDOWS)
          + "), not the group-candle proxy alone ("
          + " · ".join(f'{R5[w]["all_invalidated_by_component_all_days"]["I04_GROUP_PROXY"] / R5[w]["eligible"]:.1%}'
                       for w in WINDOWS) + ").",
          f'- **The six largest missed winners of validation** were all invalidated ({v_i04} with the group-candle '
          f'proxy on every day; the rest chasing). Given {v["missed_all_invalidated"]} of {v["missed"]} missed events '
          f'invalidated, six of six has P = {v["p_top6_ge_x_given_missed_share"]}. It does not repeat: development '
          f'{R5["development"]["top6_missed_all_invalidated"]}/6 (P {R5["development"]["p_top6_ge_x_given_missed_share"]}), '
          f'holdout {R5["holdout"]["top6_missed_all_invalidated"]}/6 (P {R5["holdout"]["p_top6_ge_x_given_missed_share"]}); '
          "the 20 largest by peak gain: " + " · ".join(f'{R5[w]["top20_all_invalidated"]}/20' for w in WINDOWS)
          + ". The peak gain of invalidated events is not larger than the others' (medians above).",
          "- **Why the six:** in every window most of the six largest missed legs have the trough of the final leg "
          "after T−7 (" + " · ".join(f"{sum(after[w])} of 6" for w in WINDOWS) + ") and are one-day jumps ("
          + " · ".join(f'{sum(1 for k in kinds[w] if k == "jump")} of 6' for w in WINDOWS)
          + "): at T−10…T−7 these stocks were still falling toward the trough the final leg starts from. What sets "
          "the validation six apart is how far they were falling from: the median of their maximum distance above the "
          "25-session low over T−10…T−7 is " + " · ".join(f"{statistics.median(dmx[w]):.1f}%" for w in WINDOWS)
          + " (development · validation · holdout). Coming off an earlier spike is what put them in the chasing or "
          "group-candle state (a reading of these six cases, not a measured cause); the state describes that earlier "
          "move. Six of six is a property of the validation tail, selected after the fact, not a general rule.", "",
          "## 4. The classes (R6) and «consistently discriminative» (R7)", "",
          "Class precision in % (ticker-cluster bootstrap 2,000, seed 20261011) and differences in percentage points. "
          "READY = READY_1–3 together.", "",
          "| window | READY_1 | READY_2 | READY_3 | READY | WATCH | NOT_READY | INVALIDATED |", "|---|---|---|---|---|---|---|---|"]
    order = ("READY_1", "READY_2", "READY_3", "READY", "WATCH", "NOT_READY", "INVALIDATED")
    for w in WINDOWS + ("pooled_2026",):
        b = R6[w]["bootstrap"] if w != "pooled_2026" else R6[w]
        L.append(f"| {w.replace('_', ' ')} | " + " | ".join(f'{b["precision_pct"][k][0]} {_ci(b["precision_pct"][k][1])}'
                                                          for k in order) + " |")
    pairs = [f"{a}-{b}" for a, b in PAIRS]
    L += ["", "| window | " + " | ".join(p.replace("-", " − ") for p in pairs) + " |", "|---" * (len(pairs) + 1) + "|"]
    for w in WINDOWS + ("pooled_2026",):
        b = R6[w]["bootstrap"] if w != "pooled_2026" else R6[w]
        L.append(f"| {w.replace('_', ' ')} | " + " | ".join(
            _pp(b["diff_pp"][p][0], b["diff_pp"][p][1]) for p in pairs) + " |")
    fine = [p for p in pairs[:3] if any(_lo_above((R6[w]["bootstrap"] if w != "pooled_2026" else R6[w])["diff_pp"][p][1], 0)
                                        for w in WINDOWS + ("pooled_2026",))]
    P6 = R6["pooled_2026"]["diff_pp"]
    rep = all(R6[w]["class_table_equals_sealed"] for w in ("validation", "holdout"))
    L += ["", "**Reading.**", "",
          f'- The class tables recomputed from the frozen model equal the sealed ones: {"yes" if rep else "NO"} '
          f'(validation and holdout). Equal burden holds: sessions with fewer valid rows than k = '
          + " · ".join(str(R6[w]["sessions_where_valid_rows_fewer_than_k"]) for w in WINDOWS) + ".",
          f'- **Fine order not supported:** READY_1 − READY_2, READY_2 − READY_3 and READY_1 − READY_3 have an interval '
          f'above 0 in {"none" if not fine else ", ".join(fine)} of the windows or the pool.',
          f'- **Coarse order:** READY − WATCH pooled {_pp(*P6["READY-WATCH"])} and WATCH − NOT_READY pooled '
          f'{_pp(*P6["WATCH-NOT_READY"])} — a descriptive difference in 2026, not repeated with confidence in every '
          f'window. INVALIDATED − READY_1 pooled {_pp(*P6["INVALIDATED-READY_1"])}.',
          "- **Verdict unchanged:** NOT_GRADED (sealed V5 = False). READY_1, READY_2 and READY_3 are rank bands of the C "
          "score inside a session, not validated grades. The coarse READY − WATCH difference is not value beyond the "
          "baselines: the sealed W_k did not beat the drop ranking or CAPIT_TC (V2, V3 = False).", "",
          "**R7.**", "",
          "| test | flags |", "|---|---|",
          f'| R7a lift lower bound above 1 in development, validation and holdout (all {R7["flags_tested"]} flags) | '
          f'{", ".join(R7["R7a_lift_lower_above_1_all_three"]) or "none"} |',
          "| R7b … and the matched lower bound above 1 in all three | "
          + (", ".join(n for n, ok in R7["R7b_matched_lower_above_1_all_three"].items() if ok) or "none") + " |",
          "| R7c beats the volatility or drop ranking at equal burden (development, any flag; 2026, the R7a flags) | "
          + (", ".join(sorted(set(R7["R7c_beats_volatility_or_drop_dev_any_flag"])
                              | set(R7["R7c_beats_volatility_or_drop_2026_focus"]))) or "none") + " |", "",
          "«RSI is the only consistently discriminative condition» is **not accurate as written**. RSI < 30 and RSI < 33 "
          "share a lift lower bound above 1 in all three windows with the group-candle proxy. None of the three keeps a "
          f'matched lower bound above 1 in all three windows (RSI < 30: {_wl(surv["B01_RSI30"])}; RSI < 33: '
          f'{_wl(surv["B01b_RSI33"])}; group-candle proxy: {_wl(surv["I04_GROUP_PROXY"])}), and none beats volatility '
          "or the 5-session drop at equal burden in any window. Correct wording: RSI oversold is the most consistent "
          "*raw association* among Faisal's readiness conditions (the group-candle proxy, as consistent in raw lift, "
          "is one of his exclusion states), and in no window is it shown to add anything beyond volatility and the "
          "recent fall.", "",
          "## 5. Sealed files (unchanged by this task)", "",
          "| file | SHA-256 | guarded by |", "|---|---|---|"]
    guard = {"CA_PROTOCOL.md": "CA6, CA12", "data/model_frozen.json": "CA6, CA12", "data/verdict.json": "CA10, CA12",
             "data/ca_rows.csv.gz": "CA1, CA2, CA12"}
    for f, h in SEALED_DATA.items():
        L.append(f"| {f} | `{h}` | {guard.get(f, 'CA12')} |")
    for f, h in SEALED_CODE.items():
        L.append(f"| {f} | `{h}` | recorded at the start of this task and compared before the commit"
                 f"{'; its pinned hashes are CA6' if f == 'ca_final.py' else ''} |")
    L += ["", "The code files are not pinned by a guard, so that the mutation round can still edit them; the data files "
              "and the protocol are.", "",
          "**D1 · a miscount in the sealed protocol (found during this reconciliation, not declared in §0).** "
          f'CA_PROTOCOL.md §⑥ counts {R0["protocol_condition_flags"]} condition flags and {R0["protocol_total"]} '
          f'hypotheses; the code tests {R0["flags_in_code"]} flags (`ca_lib.COND`) and its Bonferroni intervals divide '
          f'0.05 by {R0["flags_in_code"]}, as CONDITION_STRENGTH_RESULTS.md states. The development total is therefore '
          f'{R0["protocol_total"] - (R0["protocol_condition_flags"] - R0["flags_in_code"])}. No decision rule uses the '
          "Bonferroni intervals (V1–V5 use the primary intervals). Minimum check: every flag whose stored Bonferroni "
          f'lower bound is at or above 1, recomputed at 0.05 / {R0["protocol_total"]}:', "",
          "| flag | stored | reproduced | at 0.05 / 76 |", "|---|---|---|---|"]
    L += [f'| {n} | {_ci(x["stored"])} | {_ci(x["reproduced"])} | {_ci(x["at_76"])} |' for n, x in R0["flags"].items()]
    L += ["", "The protocol is not edited; FINAL_FINDINGS.md now gives the count the code used.", "",
          "## 6. Corrections to the canonical reports (originals kept here)", "",
          "| report | original wording | corrected to |", "|---|---|---|",
          "| FINAL_FINDINGS.md point 1 | «only RSI oversold separates, and it does so in every period» | the most "
          "consistent raw association among his technical conditions; not beyond volatility or the drop (R7) |",
          "| FINAL_FINDINGS.md point 4 | «His «no-entry» states mark the stocks most likely to start another leg … 20–31% "
          "of all eligible events were in that state … The six largest missed winners of the 2026 validation window "
          "were all invalidated» | association vs prediction vs entry suitability kept apart; 20–31% is the union; "
          "the six are the validation tail and missed by construction (§2, §3) |",
          "| FINAL_FINDINGS.md point 5 | «its classes are NOT_GRADED (READY_1 is not more precise than READY_2–3)» | "
          "the same verdict with the class intervals (§4) |",
          "| CONDITION_STRENGTH_RESULTS.md §5 (generated) | «Faisal's invalidation states raise the odds of a +70% leg» "
          "· «RSI oversold is Faisal's one condition that holds» | association only, with the matched and "
          "equal-burden results |",
          "| HISTORICAL_CLASSIFICATION_RESULTS.md §5 (generated) | «INVALIDATED pivot-days start a leg about as often as "
          "READY_1 … Faisal's invalidation marks hot, volatile stocks» | with the class differences and their intervals |",
          "| READY_CLASSIFICATION_SPEC.md (generated) | — | a note that READY_1–3 are score-rank bands, NOT_GRADED |",
          "| CHART_CASEBOOK.md (generated) | «were in Faisal's invalidated state» | names the three states and the "
          "group-candle-only count; missed by construction |", "",
          "The sealed verdict stays **NO_DEMONSTRATED_IMPROVEMENT · NOT_GRADED**. Nothing here is production-ready, "
          "and nothing changes the bot, the lists, Telegram or any frozen axis.", ""]
    return "\n".join(L) + "\n"


def _prefix():
    raw = open(ADDENDUM, "rb").read()
    return raw[:PREFIX_BYTES], raw[PREFIX_BYTES:]


def doc_text():
    res = json.load(open(os.path.join(DATA, "reconcile.json"), encoding="utf-8"))
    cb = json.load(open(os.path.join(DATA, "casebook.json"), encoding="utf-8"))
    return "\n" + render(res, cb)


def doc_check():
    """Fast check (CA12): §0 unchanged since written, §1–§6 equal their rendering, the sealed data unchanged, and the
    reconciliation reproduces the sealed numbers it re-reads."""
    import hashlib
    pre, body = _prefix()
    bad = []
    if hashlib.sha256(pre).hexdigest() != PREFIX_SHA256:
        bad.append("§0 changed")
    if body.decode("utf-8") != doc_text():
        bad.append("§1–§6 differ from their rendering")
    bad += [f"{f} hash" for f, h in SEALED_DATA.items() if _sha(f) != h]
    res = json.load(open(os.path.join(DATA, "reconcile.json"), encoding="utf-8"))
    fin = json.load(open(os.path.join(DATA, "final.json"), encoding="utf-8"))
    dev = json.load(open(os.path.join(DATA, "strength_dev.json"), encoding="utf-8"))["strength"]
    if not all(res["R6"][w]["class_table_equals_sealed"] for w in ("validation", "holdout")):
        bad.append("class tables differ from final.json")
    for n in FOCUS:
        if res["R2"]["development"][n]["matched_ratio"] != dev[n]["matched"]["ratio"]:
            bad.append(f"{n} development matched ratio")
        for w in ("validation", "holdout"):
            if res["R2"][w][n]["lift"] != fin[w]["conditions"][n]["lift"]:
                bad.append(f"{n} {w} lift")
    if any(x["reproduced"] != x["stored"] for x in res["R0"]["flags"].values()):
        bad.append("Bonferroni intervals not reproduced")
    if res["R1"]["development"]["lift"] != dev["I04_GROUP_PROXY"]["lift"]:
        bad.append("I04 development lift")
    for w in ("validation", "holdout"):
        if res["R1"][w]["lift"] != fin[w]["conditions"]["I04_GROUP_PROXY"]["lift"]:
            bad.append(f"I04 {w} lift (R1)")
    return not bad, "; ".join(bad)


if __name__ == "__main__":
    if "--check" in sys.argv:
        tmp = tempfile.mkdtemp()
        build(tmp)
        same = open(os.path.join(tmp, "reconcile.json"), "rb").read() == open(os.path.join(DATA, "reconcile.json"),
                                                                              "rb").read()
        print("✅ regenerated identically" if same else "❌ differs: reconcile.json")
        sys.exit(0 if same else 1)
    if "--render" in sys.argv:
        import hashlib
        pre, _ = _prefix()
        if hashlib.sha256(pre).hexdigest() != PREFIX_SHA256:          # never write over a damaged §0
            print("❌ §0 does not match its pinned SHA-256; nothing written")
            sys.exit(1)
        out = pre + doc_text().encode("utf-8")                       # built before the file is opened
        with open(ADDENDUM, "wb") as fh:
            fh.write(out)
        print("rendered", ADDENDUM)
        sys.exit(0)
    if "--doc-check" in sys.argv:
        ok, why = doc_check()
        print("✅ addendum matches" if ok else "❌ " + why)
        sys.exit(0 if ok else 1)
    r = build()
    print(json.dumps(r, ensure_ascii=False, indent=1)[:12000])
