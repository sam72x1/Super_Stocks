# -*- coding: utf-8 -*-
"""🧭🏁 rank_eval — تقييمُ المرتِّب حرفًا بعقد RANKING_PROTOCOL.md (مدموجٌ قبل أيّ ترتيب). قراءةٌ فقط · لا إنتاج · لا تلغرام.

المدخلات: data/rank/rows.csv.gz (إعادةُ بناء الكون على رنر) · data/universe_manifest.json (الجدرانُ المخزَّنة) · weekly_watchlist.json
(reject_stats) · fm_forensics/phase3/FAISAL_TIMELINE.csv (الوحداتُ الموثَّقة) · out/universe_stages.csv (للاتّساق مع الاختبار السابق).
المخرجات: out/rank_summary.json · out/rank_cases.csv · out/rank_units.csv · out/rank_daily.csv · out/rank_fidelity.csv ·
out/rank_failures.csv · out/rank_anchor_cases.csv · out/rank_top108_<v>.csv.gz · RANKING_RESULT.md
`--check` يعيد التوليد في مجلّدٍ مؤقّت ويقارن البصمات بالملتزَم (معيار G)."""
import csv
import gzip
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import ranker as R                      # noqa: E402

DATA = os.path.join(HERE, "data", "rank")
OUT = os.environ.get("FE_RANK_OUT") or os.path.join(HERE, "out")
WINDOW = ("2026-08-14", "2026-10-08")
EVAL_FROM = "2026-08-07"
KS = (25, 50, 108)
K0 = 108
EARLY = 5
FIRST_LOOKBACK = 20
EPISODE_GAP = 30
FOLD_SPLIT = "2026-09-15"
SEED = 20261009
BOOT = 10000
MC = 100000
STATES = ("FOCUS", "WATCH", "READY", "ENTRY")
ANCHOR_REASON = "M_لا_مستوى_مختبر"
POSTHOC = list(R.POSTHOC_VARIANTS)      # §⑩ — التصحيحاتُ اللاحقة (الإضافة 1: D1) — تُقاس كاملةً ولا تُخلط بالمسجَّلة في الاختيار والحكم


def wilson(k, n, z=1.96):
    if not n:
        return [None, None, None]
    p = k / n; den = 1 + z * z / n; c = (p + z * z / (2 * n)) / den
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return [round(p, 4), round(c - h, 4), round(c + h, 4)]


def _median(xs):
    xs = sorted(x for x in xs if x is not None)
    if not xs:
        return None
    m = len(xs) // 2
    return xs[m] if len(xs) % 2 else (xs[m - 1] + xs[m]) / 2


# ---------------------------------------------------------------- inputs
def load():
    rows = R.load_rows(os.path.join(DATA, "rows.csv.gz"))
    man = json.load(open(os.path.join(DATA, "manifest.json"), encoding="utf-8"))
    uni = json.load(open(os.path.join(DATA, "universe.json"), encoding="utf-8"))
    umf = json.load(open(os.path.join(HERE, "data", "universe_manifest.json"), encoding="utf-8"))
    wl = json.load(open(os.path.join(ROOT, "weekly_watchlist.json"), encoding="utf-8"))
    return rows, man, uni, umf, wl


def session_of(sessions, day):
    for s in sessions:
        if s >= day:
            return s
    return None


def units(sessions):
    """الوحداتُ الموثَّقة (§③): IS_FAISAL=1 · الصنفُ من الأربعة · تاريخٌ كامل · الجلسةُ أوّلُ جلسةٍ ≥ DATE · داخل النافذة."""
    out = []
    for r in csv.DictReader(open(os.path.join(ROOT, "fm_forensics", "phase3", "FAISAL_TIMELINE.csv"), encoding="utf-8")):
        if r["IS_FAISAL"] != "1" or r["OBSERVATION_CLASS"] not in STATES or len(r["DATE"]) != 10:
            continue
        s = session_of(sessions, r["DATE"])
        if s is None or not (WINDOW[0] <= s <= WINDOW[1]):
            continue
        m = re.search(r"(20\d{2})(\d{2})(\d{2})", r["EVIDENCE_ID"])
        id_date = f"{m.group(1)}-{m.group(2)}-{m.group(3)}" if m else ""
        amb = []
        if s != r["DATE"]:
            amb.append("AMBIGUOUS_WEEKEND")
        if id_date and id_date != r["DATE"]:
            amb.append("AMBIGUOUS_ID")
        out.append(dict(ticker=r["TICKER"].upper().strip(), date=r["DATE"], session=s, state=r["OBSERVATION_CLASS"], evidence_id=r["EVIDENCE_ID"],
                        evidence_type=r["EVIDENCE_TYPE"], id_date=id_date, ambiguity="|".join(amb), action=r["ACTION"],
                        decision_raw=r["DECISION_RAW"], confidence=r["CONFIDENCE"], gist=(r["GIST"] or "")[:160]))
    return sorted(out, key=lambda u: (u["ticker"], u["session"], u["evidence_id"]))


def episodes(us, sessions):
    """المُعرَّفةُ مسبقًا (p5lib.EPISODE_GAP = 30 جلسة) — الحلقةُ الجديدة حين تتجاوز الفجوةُ 30 جلسة."""
    idx = {d: i for i, d in enumerate(sessions)}
    out, by = [], {}
    for u in us:
        by.setdefault(u["ticker"], []).append(u)
    for t, xs in sorted(by.items()):
        cur, last, n = None, None, 0
        for u in xs:
            i = idx[u["session"]]
            if cur is None or i - last > EPISODE_GAP:
                n += 1
                cur = dict(episode_id=f"{t}_E{n}", ticker=t, T_e=u["session"], units=[])
                out.append(cur)
            cur["units"].append(u)
            last = i
    for e in out:
        e["n_units"] = len(e["units"])
        e["first_state"] = e["units"][0]["state"]
        e["states"] = "|".join(sorted({u["state"] for u in e["units"]}))
        e["ambiguity"] = e["units"][0]["ambiguity"]
        e["fold"] = "DISCOVERY" if e["T_e"] < FOLD_SPLIT else "VALIDATION"
    return out


# ---------------------------------------------------------------- rankings
def build(rows):
    sessions = R.sessions_of(rows)
    by = {}
    for r in rows:
        by.setdefault(r["date"], []).append(r)
    hist = R.stage_history(rows)
    ranks = {}
    for v in list(R.VARIANTS) + list(POSTHOC):
        ranks[v] = {}
        for T in sessions:
            if T < EVAL_FROM:
                continue
            rk = R.rank_session(T, by[T], v, hist, sessions)
            ranks[v][T] = {x["symbol"]: x for x in rk}
    bot = {}
    for T in sessions:
        bs = [r for r in by[T] if r["bot_res"] == "PASS"]
        bs.sort(key=lambda r: (json.loads(r["bot_rank_key"]) if r["bot_rank_key"] else [9e9], r["symbol"]))
        bot[T] = {r["symbol"]: k for k, r in enumerate(bs, 1)}
    return sessions, by, hist, ranks, bot


def prev_sessions(sessions, T, n):
    i = sessions.index(T)
    return sessions[max(0, i - n):i]


# ---------------------------------------------------------------- case evaluation
def eval_case(tk, T, sessions, by, ranks, bot, universe_syms, variants):
    present = {r["symbol"]: r for r in by.get(T, [])}
    row = present.get(tk)
    rec = {"in_universe_list": int(tk in universe_syms), "evaluable": int(row is not None)}
    if row is None:
        rec["unevaluable_reason"] = "NOT_IN_RECONSTRUCTED_UNIVERSE" if tk not in universe_syms else "NO_ELIGIBLE_BARS_AT_T"
        return rec
    rec.update(stage_T=row["eng_stage"], tech_T=row.get("tech_state", ""), first_failed_T=row.get("eng_first_failed", ""),
               frame_T=row.get("frame", ""), bot_res_T=row["bot_res"], bot_gate_T=row.get("bot_gate", ""), universe_T=len(present),
               pool_T=sum(1 for r in present.values() if r["eng_stage"] in R.POOL), last_rsplit=row.get("last_rsplit", ""))
    pv = prev_sessions(sessions, T, EARLY)
    look = prev_sessions(sessions, T, FIRST_LOOKBACK) + [T]
    for v in variants:
        x = ranks[v].get(T, {}).get(tk)
        rec[f"{v}_rank"] = x["rank"] if x else ""
        rec[f"{v}_explain"] = x["explain"] if x else ""
        rec[f"{v}_temporal"] = (x or {}).get("temporal", "")
        for K in KS:
            rec[f"{v}_exact_{K}"] = int(bool(x) and x["rank"] <= K)
            rec[f"{v}_early_{K}"] = int(any((ranks[v].get(p, {}).get(tk) or {}).get("rank", 10 ** 9) <= K for p in pv))
        fi = next((p for p in look if (ranks[v].get(p, {}).get(tk) or {}).get("rank", 10 ** 9) <= K0), None)
        rec[f"{v}_first_incl"] = fi or ""
        if fi:
            fx = ranks[v][fi][tk]
            rec[f"{v}_first_rank"] = fx["rank"]; rec[f"{v}_first_stage"] = fx["stage"]
            rec[f"{v}_first_lead"] = sessions.index(T) - sessions.index(fi)
        else:
            rec[f"{v}_first_rank"] = rec[f"{v}_first_stage"] = rec[f"{v}_first_lead"] = ""
    rec["bot_op_exact"] = int(tk in bot.get(T, {}))
    rec["bot_op_early"] = int(any(tk in bot.get(p, {}) for p in pv))
    rec["bot_size_T"] = len(bot.get(T, {}))
    br = bot.get(T, {}).get(tk)
    rec["bot_rank"] = br or ""
    for K in KS:
        rec[f"bot_std_exact_{K}"] = int(bool(br) and br <= K)
        rec[f"bot_std_early_{K}"] = int(any((bot.get(p, {}).get(tk) or 10 ** 9) <= K for p in pv))
    for K in KS:
        rec[f"rnd_U_exact_{K}"] = round(min(1.0, K / len(present)), 6)
        q = 1.0
        for p in pv:
            n = len(by.get(p, []))
            if n and tk in {r["symbol"] for r in by[p]}:
                q *= 1 - min(1.0, K / n)
        rec[f"rnd_U_early_{K}"] = round(1 - q, 6)
        rec[f"rnd_P_exact_{K}"] = round(min(1.0, K / rec["pool_T"]), 6) if (row["eng_stage"] in R.POOL and rec["pool_T"]) else 0.0
    return rec


def rank_bucket(r):
    if r in ("", None):
        return "not_in_pool"
    r = int(r)
    return "1-25" if r <= 25 else ("26-50" if r <= 50 else ("51-108" if r <= 108 else ">108"))


# ---------------------------------------------------------------- uncertainty
def boot_diff(eps, a_key, b_key, seed=SEED, B=BOOT):
    """فرقُ نسبتين مقترنٌ ببوتستراب عنقوديّ على الرموز ⟵ (نقطة · 95% · 98.33%)."""
    tick = sorted({e["ticker"] for e in eps})
    if not tick:
        return {"point": None}
    by = {t: [e for e in eps if e["ticker"] == t] for t in tick}
    a = {t: (sum(e[a_key] for e in by[t]), len(by[t])) for t in tick}
    b = {t: (sum(e[b_key] for e in by[t]), len(by[t])) for t in tick}
    rng = np.random.default_rng(seed)
    n = len(tick)
    A = np.array([a[t][0] for t in tick], float); Bv = np.array([b[t][0] for t in tick], float); N = np.array([a[t][1] for t in tick], float)
    idx = rng.integers(0, n, size=(B, n))
    den = N[idx].sum(1)
    d = (A[idx].sum(1) - Bv[idx].sum(1)) / den
    pt = (A.sum() - Bv.sum()) / N.sum()
    q = np.quantile(d, [0.025, 0.975, 0.008333, 0.991667])
    return {"point": round(float(pt), 4), "ci95": [round(float(q[0]), 4), round(float(q[1]), 4)],
            "ci9833": [round(float(q[2]), 4), round(float(q[3]), 4)], "clusters": n, "B": B, "seed": seed}


def loo(eps, a_key, b_key):
    out = {"ticker": {}, "date": {}}
    for t in sorted({e["ticker"] for e in eps}):
        xs = [e for e in eps if e["ticker"] != t]
        out["ticker"][t] = round((sum(e[a_key] for e in xs) - sum(e[b_key] for e in xs)) / len(xs), 4) if xs else None
    for d in sorted({e["T_e"] for e in eps}):
        xs = [e for e in eps if e["T_e"] != d]
        out["date"][d] = round((sum(e[a_key] for e in xs) - sum(e[b_key] for e in xs)) / len(xs), 4) if xs else None
    vals_t = [v for v in out["ticker"].values() if v is not None]; vals_d = [v for v in out["date"].values() if v is not None]
    out["min_ticker"] = min(vals_t) if vals_t else None; out["min_date"] = min(vals_d) if vals_d else None
    out["argmin_ticker"] = min(out["ticker"], key=lambda k: out["ticker"][k] if out["ticker"][k] is not None else 9) if vals_t else None
    return out


def random_mc(eps, by, sessions, K, kind, seed=SEED, sims=MC):
    """توزيعُ عدد الملتقَط تحت قائمةٍ عشوائيّةٍ منتظمة من U(T) — الحالاتُ في الجلسة نفسِها تُسحب معًا بلا إرجاع."""
    rng = np.random.default_rng(seed + K + (0 if kind == "exact" else 7))
    need = {}
    for j, e in enumerate(eps):
        days = [e["T_e"]] if kind == "exact" else prev_sessions(sessions, e["T_e"], EARLY)
        for d in days:
            if e["ticker"] in {r["symbol"] for r in by.get(d, [])}:
                need.setdefault(d, []).append(j)
    hit = np.zeros((sims, len(eps)), bool)
    for d, js in need.items():
        N = len(by[d]); m = len(js)
        k = rng.hypergeometric(m, max(N - m, 0), min(K, N), size=sims)
        order = rng.random((sims, m)).argsort(1).argsort(1)          # أيُّ k من الـm وقع في القائمة (اختيارٌ منتظم بلا إرجاع)
        hit[:, js] |= order < k[:, None]
    tot = hit.sum(1)
    return {"mean": round(float(tot.mean()), 3), "p2_5": int(np.quantile(tot, 0.025)), "p97_5": int(np.quantile(tot, 0.975)),
            "sims": sims, "seed": int(seed + K + (0 if kind == "exact" else 7))}


# ---------------------------------------------------------------- fidelity
def fidelity(sessions, by, umf, wl):
    out = []
    stored = {r["date"]: r for r in wl.get("reject_stats", [])}
    for d, r in sorted(stored.items()):
        T = session_of(sessions, d)
        if T is None or T not in by:
            continue
        rec_pass = sum(1 for x in by[T] if x["bot_res"] == "PASS")
        st_pass = r["valid"] - sum(r["stats"].values())
        row = dict(run_date=d, T=T, stored_valid=r["valid"], recon_universe=len(by[T]), stored_pass=st_pass, recon_pass=rec_pass,
                   pass_rel_err=round((rec_pass - st_pass) / st_pass, 4) if st_pass else None,
                   universe_ratio=round(len(by[T]) / r["valid"], 4) if r["valid"] else None)
        if d in umf["anchor_wall"]:
            sw = set(umf["anchor_wall"][d]); rw = {x["symbol"] for x in by[T] if x["bot_reason"] == ANCHOR_REASON}
            row.update(stored_wall=len(sw), recon_wall=len(rw), wall_recall=round(len(sw & rw) / len(sw), 4) if sw else None,
                       wall_jaccard=round(len(sw & rw) / len(sw | rw), 4) if (sw | rw) else None)
        out.append(row)
    return out


def stage_consistency(sessions, by):
    """اتّساقُ مرحلة المحرّك لرموز الجدار مع الاختبار السابق (out/universe_stages.csv) — مقارنةٌ بالفهرس (التاريخ ⟵ جلسته)."""
    p = os.path.join(HERE, "out", "universe_stages.csv")
    if not os.path.exists(p):
        return None
    idx = {(T, y["symbol"]): y["eng_stage"] for T in by for y in by[T]}
    agree = n = prev = 0
    for r in csv.DictReader(open(p, encoding="utf-8")):
        prev += 1
        T = session_of(sessions, r["date"])
        if T is None or r["stage"] == "NO_BARS":
            continue
        s = idx.get((T, r["symbol"]))
        if s is None:
            continue
        n += 1
        agree += int(s == r["stage"])
    return {"compared": n, "agree": agree, "rate": round(agree / n, 4) if n else None, "previous_rows": prev}


# ---------------------------------------------------------------- diagnosis
def diagnose(c, v):
    """فئةٌ أوّليّة وثانويّةٌ مبرَّرة (§13) لكلّ حالةٍ لم تدخل أعلى 108 في يومها — من صفّ إعادة البناء وحده (السؤال A)."""
    sec = []
    if not c["evaluable"]:
        return "8 Missing historical data", sec, f"not in U(T): {c.get('unevaluable_reason')}"
    if "AMBIGUOUS" in (c.get("ambiguity") or ""):
        sec.append("9 Ambiguous source timestamp")
    st = c["stage_T"]
    if st == "INSUFFICIENT_DATA":
        return "8 Missing historical data", sec, "engine: fewer than 40 bars"
    if st == "REJECTED":
        ff = c.get("first_failed_T") or ""
        if c.get("last_rsplit") and any(g in ff for g in ("M2", "M4", "M3", "M1")):
            sec.append("7 Split or corporate-action handling (possible: reverse split on record)")
        return "1 Candidate-generation failure", sec, f"engine REJECTED at {ff} (bot {c['bot_res_T']}/{c['bot_gate_T']})"
    if st == "HOLD":
        sec.append("10 Unsupported reconstruction assumption (offering blocker while Faisal attended)")
    fs = c["first_state"]
    if (fs in ("READY", "ENTRY") and st in ("FOCUS", "WATCH")) or (fs == "FOCUS" and st in ("READY", "TRIGGER")):
        sec.append("3 Incorrect state transition (engine stage ≠ Faisal's documented state)")
    if c.get(f"{v}_early_{K0}") and not c.get(f"{v}_exact_{K0}"):
        sec.append("4 Incorrect temporal-state handling (in shortlist earlier, dropped on decision date)")
    if c.get("higher_stage_count", 0) >= K0:
        return "2 Candidate-ranking failure (stage priority cut-off)", sec, f"rank {c[f'{v}_rank']} · {c['higher_stage_count']} pool members in higher stages"
    return "11 Candidate is ranked too low despite satisfying the existing rules", sec, f"rank {c[f'{v}_rank']} inside its stage group"


# ---------------------------------------------------------------- main
def run(out_dir=OUT, write_md=True):
    rows, man, uni, umf, wl = load()
    sessions, by, hist, ranks, bot = build(rows)
    variants = list(R.VARIANTS) + list(POSTHOC)
    usyms = set(uni["symbols"])
    us = units(sessions)
    eps = episodes(us, sessions)
    for e in eps:
        e.update(eval_case(e["ticker"], e["T_e"], sessions, by, ranks, bot, usyms, variants))
        if e["evaluable"]:
            st = e["stage_T"]
            e["higher_stage_count"] = (sum(1 for r in by[e["T_e"]] if r["eng_stage"] in R.POOL and R.STAGE_PRIORITY[r["eng_stage"]] < R.STAGE_PRIORITY[st])
                                       if st in R.POOL else "")
    for u in us:
        u.update(eval_case(u["ticker"], u["session"], sessions, by, ranks, bot, usyms, variants))
    ev = [e for e in eps if e["evaluable"]]
    evu = [u for u in us if u["evaluable"]]
    S = {"protocol": "RANKING_PROTOCOL.md", "label": "EXPLORATORY", "ranker": R.RANKER_VERSION, "inputs": man.get("files"), "run_id": man.get("run_id"),
         "sessions_computed": len(sessions), "eval_sessions": len([T for T in sessions if T >= EVAL_FROM]), "window": WINDOW,
         "units": len(us), "units_evaluable": len(evu), "episodes": len(eps), "episodes_evaluable": len(ev),
         "unevaluable": [{"episode": e["episode_id"], "reason": e["unevaluable_reason"]} for e in eps if not e["evaluable"]],
         "tickers_evaluable": len({e["ticker"] for e in ev})}
    # daily burden
    daily = []
    for T in sessions:
        if T < EVAL_FROM:
            continue
        rs = by[T]; pool = [r for r in rs if r["eng_stage"] in R.POOL]
        d = dict(date=T, universe=len(rs), pool=len(pool), bot_pass=sum(1 for r in rs if r["bot_res"] == "PASS"),
                 anchor_wall=sum(1 for r in rs if r["bot_reason"] == ANCHOR_REASON))
        for s in R.POOL:
            d[f"stage_{s}"] = sum(1 for r in pool if r["eng_stage"] == s)
        for K in KS:
            d[f"shortlist_{K}"] = min(K, len(pool)); d[f"pct_universe_{K}"] = round(min(K, len(pool)) / len(rs) * 100, 3) if rs else None
        tc = {}
        for r in pool:
            tm = R.temporal(r["symbol"], T, r["eng_stage"], hist, sessions)
            tc[tm["cls"]] = tc.get(tm["cls"], 0) + 1
        for c in R.TEMPORAL:
            d[f"temporal_{c}"] = tc.get(c, 0)
        cases_T = [u for u in us if u["session"] == T]
        d["cases"] = len(cases_T)
        for v in variants:
            d[f"{v}_case_ranks"] = "|".join(f"{u['ticker']}:{u.get(f'{v}_rank') or '-'}" for u in cases_T)
            for K in KS:
                d[f"{v}_cases_{K}"] = sum(1 for u in cases_T if u.get(f"{v}_exact_{K}"))
        daily.append(d)
    S["daily"] = {"universe_median": _median([d["universe"] for d in daily]), "pool_median": _median([d["pool"] for d in daily]),
                  "pool_range": [min(d["pool"] for d in daily), max(d["pool"] for d in daily)],
                  "bot_pass_median": _median([d["bot_pass"] for d in daily]), "bot_pass_range": [min(d["bot_pass"] for d in daily), max(d["bot_pass"] for d in daily)],
                  "shortlist_max": {K: max(d[f"shortlist_{K}"] for d in daily) for K in KS},
                  "pct_universe_108_median": _median([d["pct_universe_108"] for d in daily]),
                  "stage_median": {s: _median([d[f"stage_{s}"] for d in daily]) for s in R.POOL},
                  "temporal_median": {c: _median([d[f"temporal_{c}"] for d in daily]) for c in R.TEMPORAL}}
    # capture
    cap = {}
    n = len(ev); nu = len(evu)
    for v in variants:
        cap[v] = {}
        for K in KS:
            ke = sum(e[f"{v}_exact_{K}"] for e in ev); kr = sum(e[f"{v}_early_{K}"] for e in ev)
            cap[v][K] = {"exact": [ke, n] + wilson(ke, n), "early": [kr, n] + wilson(kr, n),
                         "unit_exact": [sum(u[f"{v}_exact_{K}"] for u in evu), nu], "unit_early": [sum(u[f"{v}_early_{K}"] for u in evu), nu]}
        cap[v]["rank_buckets"] = {b: sum(1 for e in ev if rank_bucket(e[f"{v}_rank"]) == b) for b in ("1-25", "26-50", "51-108", ">108", "not_in_pool")}
        rks = [int(e[f"{v}_rank"]) for e in ev if e[f"{v}_rank"] != ""]
        cap[v]["rank_median_in_pool"] = _median(rks)
        cap[v]["stage_at_T"] = {s: sum(1 for e in ev if e["stage_T"] == s) for s in sorted({e["stage_T"] for e in ev})}
        cap[v]["lift_108_exact"] = round((cap[v][K0]["exact"][0] / n) / (K0 / S["daily"]["universe_median"]), 2) if n and cap[v][K0]["exact"][0] else 0.0
    kb = sum(e["bot_op_exact"] for e in ev); kbe = sum(e["bot_op_early"] for e in ev)
    cap["bot_operational"] = {"exact": [kb, n] + wilson(kb, n), "early": [kbe, n] + wilson(kbe, n),
                              "unit_exact": [sum(u["bot_op_exact"] for u in evu), nu], "unit_early": [sum(u["bot_op_early"] for u in evu), nu],
                              "daily_size_median": S["daily"]["bot_pass_median"], "daily_size_range": S["daily"]["bot_pass_range"]}
    cap["bot_standardized"] = {K: {"exact": [sum(e[f"bot_std_exact_{K}"] for e in ev), n], "early": [sum(e[f"bot_std_early_{K}"] for e in ev), n]} for K in KS}
    cap["random_U"] = {K: {"exact_expected": round(sum(e[f"rnd_U_exact_{K}"] for e in ev), 3), "early_expected": round(sum(e[f"rnd_U_early_{K}"] for e in ev), 3),
                           "exact_mc": random_mc(ev, by, sessions, K, "exact"), "early_mc": random_mc(ev, by, sessions, K, "early")} for K in KS}
    cap["random_P"] = {K: {"exact_expected": round(sum(e[f"rnd_P_exact_{K}"] for e in ev), 3)} for K in KS}
    S["capture"] = cap
    # comparisons (exact & early separately) vs operational and standardized baselines
    comp = {}
    for v in variants:
        comp[v] = {}
        for kind in ("exact", "early"):
            a = f"{v}_{kind}_{K0}"
            comp[v][kind] = {"vs_operational": boot_diff(ev, a, f"bot_op_{kind}"), "vs_standardized_108": boot_diff(ev, a, f"bot_std_{kind}_{K0}"),
                             "loo_vs_operational": loo(ev, a, f"bot_op_{kind}")}
            folds = {}
            for f in ("DISCOVERY", "VALIDATION"):
                xs = [e for e in ev if e["fold"] == f]
                folds[f] = {"episodes": len(xs), "tickers": len({e['ticker'] for e in xs}), "variant": sum(e[a] for e in xs), "bot_op": sum(e[f"bot_op_{kind}"] for e in xs),
                            "diff": round((sum(e[a] for e in xs) - sum(e[f"bot_op_{kind}"] for e in xs)) / len(xs), 4) if xs else None}
            comp[v][kind]["folds"] = folds
    S["comparisons"] = comp
    S["folds_disjoint_tickers"] = not ({e["ticker"] for e in ev if e["fold"] == "DISCOVERY"} & {e["ticker"] for e in ev if e["fold"] == "VALIDATION"})
    # sensitivity: excluding ambiguous episodes
    na = [e for e in ev if not e["ambiguity"]]
    S["sensitivity_unambiguous"] = {"episodes": len(na), **{v: {"exact_108": sum(e[f"{v}_exact_{K0}"] for e in na), "early_108": sum(e[f"{v}_early_{K0}"] for e in na)} for v in variants},
                                    "bot_op_exact": sum(e["bot_op_exact"] for e in na), "bot_op_early": sum(e["bot_op_early"] for e in na)}
    # temporal hypothesis H-C: capture by temporal class at T_e (C)
    hc = {}
    for e in ev:
        c = e.get("C_temporal") or "not_in_pool"
        hc.setdefault(c, [0, 0]); hc[c][1] += 1; hc[c][0] += e[f"C_exact_{K0}"]
    S["H_C_by_temporal_class"] = hc
    # fidelity
    fid = fidelity(sessions, by, umf, wl)
    f1 = _median([abs(x["pass_rel_err"]) for x in fid if x.get("pass_rel_err") is not None])
    f2 = _median([x["wall_recall"] for x in fid if x.get("wall_recall") is not None])
    f2j = _median([x["wall_jaccard"] for x in fid if x.get("wall_jaccard") is not None])
    f3 = _median([x["universe_ratio"] for x in fid if x.get("universe_ratio") is not None])
    S["fidelity"] = {"F1_pass_abs_rel_err_median": f1, "F2_wall_recall_median": f2, "F2_wall_jaccard_median": f2j, "F3_universe_ratio_median": f3,
                     "dates_F1": sum(1 for x in fid if x.get("pass_rel_err") is not None), "dates_F2": sum(1 for x in fid if x.get("wall_recall") is not None),
                     "operational_baseline_label": ("reproduced" if (f1 is not None and f1 <= 0.25 and f2 is not None and f2 >= 0.80)
                                                    else "reconstructed (not reproduced from historical outputs)"),
                     "stage_consistency_with_previous_test": stage_consistency(sessions, by)}
    # selection + verdict (§⑩ §⑪)
    def sel_key(v):
        c = cap[v]
        return (-c[K0]["exact"][0], -c[K0]["early"][0], -c[50]["exact"][0], -c[25]["exact"][0], "ABC".index(v) if v in "ABC" else 9)
    pref = sorted(R.VARIANTS, key=sel_key)[0]
    S["preferred_variant"] = pref
    S["verdict"] = verdict(S, pref, daily)
    ph = {}
    for v in POSTHOC:
        disc = [e for e in ev if e["fold"] == "DISCOVERY"]
        ph[v] = {"label": "POST-HOC · EXPLORATORY — cannot carry verdict 1 (validation rows were viewed during the iteration-2 diagnosis · ADDENDA §1)",
                 "acceptance_i_targeted": {t: bool(next((e[f"{v}_exact_{K0}"] for e in ev if e["episode_id"] == t), 0)) for t in ("DKI_E1", "NUWE_E1")},
                 "acceptance_ii_discovery": {"D": sum(e[f"{v}_exact_{K0}"] for e in disc), "C": sum(e[f"C_exact_{K0}"] for e in disc)},
                 "gained_vs_C": [e["episode_id"] for e in ev if e[f"{v}_exact_{K0}"] and not e[f"C_exact_{K0}"]],
                 "lost_vs_C": [e["episode_id"] for e in ev if e[f"C_exact_{K0}"] and not e[f"{v}_exact_{K0}"]],
                 "early_gained_vs_C": [e["episode_id"] for e in ev if e[f"{v}_early_{K0}"] and not e[f"C_early_{K0}"]],
                 "early_lost_vs_C": [e["episode_id"] for e in ev if e[f"C_early_{K0}"] and not e[f"{v}_early_{K0}"]],
                 "criteria_if_it_were_preregistered": verdict(S, v, daily).get("criteria")}
        ph[v]["acceptance_passed"] = bool(any(ph[v]["acceptance_i_targeted"].values()) and ph[v]["acceptance_ii_discovery"]["D"] >= ph[v]["acceptance_ii_discovery"]["C"])
    S["posthoc"] = ph
    S["predictions"] = predictions(S, ev, daily)
    # files
    os.makedirs(out_dir, exist_ok=True)
    case_keys = []
    for e in eps:
        for k in e:
            if k != "units" and k not in case_keys:
                case_keys.append(k)
    _write(os.path.join(out_dir, "rank_cases.csv"), [{k: e.get(k, "") for k in case_keys} for e in eps], case_keys)
    unit_keys = []
    for u in us:
        for k in u:
            if k not in unit_keys:
                unit_keys.append(k)
    _write(os.path.join(out_dir, "rank_units.csv"), us, unit_keys)
    _write(os.path.join(out_dir, "rank_daily.csv"), daily, list(daily[0].keys()))
    fk = []
    for x in fid:
        for k in x:
            if k not in fk:
                fk.append(k)
    _write(os.path.join(out_dir, "rank_fidelity.csv"), fid, fk)
    fails = []
    for v in variants:
        for e in eps:
            if e.get("evaluable") and e.get(f"{v}_exact_{K0}"):
                continue
            pc, sc, qa = diagnose(e, v)
            u0 = e["units"][0]
            fails.append(dict(variant=v, episode=e["episode_id"], ticker=e["ticker"], T_e=e["T_e"], fold=e.get("fold"), primary=pc, secondary=" ; ".join(sc),
                              question_A=qa, question_B=(f"{u0['evidence_id']} ({u0['evidence_type']}) · Faisal {u0['state']} · action «{u0['action']}» · "
                                                         f"decision {u0['decision_raw']} · source text: «{u0['gist'][:120]}» — the source documents attention/action; "
                                                         "the reason is UNKNOWN unless the text states it"),
                              stage_T=e.get("stage_T", ""), rank=e.get(f"{v}_rank", "")))
    _write(os.path.join(out_dir, "rank_failures.csv"), fails, list(fails[0].keys()) if fails else ["variant"])
    S["failures_primary"] = {v: _count([f["primary"] for f in fails if f["variant"] == v]) for v in variants}
    S["failures_primary_discovery"] = {v: _count([f["primary"] for f in fails if f["variant"] == v and f["fold"] == "DISCOVERY"]) for v in variants}
    anc = anchors(sessions, by, ranks, bot, variants)
    _write(os.path.join(out_dir, "rank_anchor_cases.csv"), anc, list(anc[0].keys()) if anc else ["ticker"])
    for v in variants:
        with gzip.GzipFile(os.path.join(out_dir, f"rank_top108_{v}.csv.gz"), "wb", mtime=0) as gz, \
                io.TextIOWrapper(gz, encoding="utf-8", newline="") as f:     # mtime=0 ⟵ بايتاتٌ حتميّة (معيار G)
            w = csv.writer(f)
            w.writerow(["date", "rank", "symbol", "stage", "tech_state", "frame", "offering", "state_rule", "rule_status", "temporal", "age", "universe", "pool", "explain"])
            for T in sorted(ranks[v]):
                xs = sorted(ranks[v][T].values(), key=lambda x: x["rank"])[:K0]
                for x in xs:
                    w.writerow([T, x["rank"], x["symbol"], x["stage"], x["tech_state"], x["frame"], x["offering"], x["state_rule"], x["rule_status"],
                                x["temporal"], x["age"], len(by[T]), len(ranks[v][T]), x["explain"]])
    json.dump({"ranker": R.RANKER_VERSION, "variants": list(R.VARIANTS), "posthoc": list(R.POSTHOC_VARIANTS), "features": R.FEATURES},
              open(os.path.join(out_dir, "rank_feature_registry.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(S, open(os.path.join(out_dir, "rank_summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
    if write_md:
        md(S, eps, anc, out_dir)
    return S


def _count(xs):
    c = {}
    for x in xs:
        c[x] = c.get(x, 0) + 1
    return dict(sorted(c.items(), key=lambda kv: -kv[1]))


def _write(path, rows, keys):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys, extrasaction="ignore"); w.writeheader(); w.writerows(rows)


def verdict(S, v, daily):
    ev = S["episodes_evaluable"]
    f3 = S["fidelity"]["F3_universe_ratio_median"] if "fidelity" in S else None
    reasons = {}
    if ev < 15 or f3 is None or f3 < 0.90:
        return {"verdict": 3, "text": "INSUFFICIENT EVIDENCE TO DECIDE", "why": {"episodes_evaluable": ev, "F3": f3}}
    c = S["comparisons"][v]["exact"]
    reasons["A_budget"] = all(d["shortlist_108"] <= 108 for d in daily)
    reasons["B_ci9833_lb_gt0"] = bool(c["vs_operational"].get("ci9833") and c["vs_operational"]["ci9833"][0] > 0)
    reasons["B_vs_standardized_point_gt0"] = bool((c["vs_standardized_108"].get("point") or 0) > 0)
    reasons["E_loo_ticker_gt0"] = bool((c["loo_vs_operational"].get("min_ticker") or -1) > 0)
    reasons["E_loo_date_gt0"] = bool((c["loo_vs_operational"].get("min_date") or -1) > 0)
    reasons["E_folds_gt0"] = all((x.get("diff") or -1) > 0 for x in c["folds"].values())
    reasons["F_locks"] = "suite locks RNK0-RNK13 (exit code recorded in RANKING_REPORT.md)"
    reasons["G_reproduced"] = "see --check"
    early = S["comparisons"][v]["early"]["vs_operational"].get("point")
    ok = all(val is True for k, val in reasons.items() if k[0] in "ABE")
    return {"verdict": 1 if ok else 2, "text": ("DEFENSIBLE IMPROVEMENT UNDER THE FIXED BUDGET" + ("" if (early or 0) > 0 else " — exact-date only; early not demonstrated"))
            if ok else "IMPROVEMENT NOT DEMONSTRATED", "variant": v, "criteria": reasons, "early_point_vs_operational": early, "label": "EXPLORATORY"}


def predictions(S, ev, daily):
    cap = S["capture"]
    best = max(cap[v][K0]["exact"][0] for v in R.VARIANTS)
    f1 = S["fidelity"]["F1_pass_abs_rel_err_median"]
    return {"P1_bot_median_within_25pct_of_108": (abs(S["daily"]["bot_pass_median"] - 108) / 108 <= 0.25) if S["daily"]["bot_pass_median"] else None,
            "P1_note": f"reconstructed median {S['daily']['bot_pass_median']} · F1 median |rel err| {f1}",
            "P2_wall_recall_median_ge_0.80": (S["fidelity"]["F2_wall_recall_median"] or 0) >= 0.80,
            "P3_no_FOCUS_case_captured_exact_108": not any(e["stage_T"] == "FOCUS" and any(e[f"{v}_exact_{K0}"] for v in R.VARIANTS) for e in ev),
            "P4_best_exact_108_le_6": best <= 6, "P4_best": best,
            "P5_no_variant_meets_verdict1": S["verdict"]["verdict"] != 1,
            "P6_persistent_largest_temporal_class": max(S["daily"]["temporal_median"], key=lambda c: S["daily"]["temporal_median"][c] or 0) == "PERSISTENT"}


def anchors(sessions, by, ranks, bot, variants):
    """§14 — DKI · SXTC · HUBC: كلُّ جلسةٍ محسوبة: المرحلة · البوت · الرتبُ — بلا استثناءٍ رمزيّ."""
    out = []
    for tk in ("DKI", "SXTC", "HUBC"):
        for T in sessions:
            if T < EVAL_FROM:
                continue
            row = next((r for r in by[T] if r["symbol"] == tk), None)
            rec = dict(ticker=tk, date=T, in_universe=int(row is not None), stage=(row or {}).get("eng_stage", ""), tech=(row or {}).get("tech_state", ""),
                       first_failed=(row or {}).get("eng_first_failed", ""), frame=(row or {}).get("frame", ""), last_rsplit=(row or {}).get("last_rsplit", ""),
                       bot=(row or {}).get("bot_res", ""), bot_gate=(row or {}).get("bot_gate", ""), bot_rank=bot.get(T, {}).get(tk, ""))
            for v in variants:
                rec[f"{v}_rank"] = (ranks[v].get(T, {}).get(tk) or {}).get("rank", "")
            out.append(rec)
    return out


def md(S, eps, anc, out_dir):
    """تقريرٌ نصّيٌّ من الملخّص وحدَه (لا رقمَ باليد)."""
    from rank_report import render            # noqa: E402
    open(os.path.join(HERE if out_dir == OUT else out_dir, "RANKING_RESULT.md"), "w", encoding="utf-8").write(render(S, eps, anc))


def check():
    tmp = tempfile.mkdtemp(prefix="rank_check_")
    run(out_dir=tmp, write_md=False)
    bad = []
    for f in ("rank_summary.json", "rank_cases.csv", "rank_units.csv", "rank_daily.csv", "rank_fidelity.csv", "rank_failures.csv",
              "rank_anchor_cases.csv", "rank_feature_registry.json") + tuple(f"rank_top108_{v}.csv.gz" for v in R.ALL_VARIANTS):
        a = os.path.join(OUT, f); b = os.path.join(tmp, f)
        ha = hashlib.sha256(open(a, "rb").read()).hexdigest() if os.path.exists(a) else None
        hb = hashlib.sha256(open(b, "rb").read()).hexdigest()
        if ha != hb:
            bad.append(f)
    print("✅ regenerated identically" if not bad else f"❌ differs: {bad}")
    return 0 if not bad else 1


if __name__ == "__main__":
    if "--check" in sys.argv:
        sys.exit(check())
    S = run()
    print(json.dumps({k: S[k] for k in ("episodes_evaluable", "preferred_variant", "verdict")}, ensure_ascii=False, indent=1, default=str))
