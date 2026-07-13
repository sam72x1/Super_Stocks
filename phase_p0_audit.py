#!/usr/bin/env python3
"""Phase C/E — تدقيق P0 الحتمي (dual-target · train-only · CIs · permutation · FDR).

هذا هو **المرجع القانوني** لتدقيق P0 استجابةً لتدقيق Codex المستقل (2026-07-13). منطق الحساب
**مطابق حرفيًّا** لسكربت Codex `reproduce_phase_e_audit.py` (فيُنتج أرقامه بت-بت)، مع تكييف
المسارات + **فحص ذاتي** يقارن مخرجاتي بمرجع Codex المرفق (`p0_acceptance_reference_codex.json`)
ضمن التسامح المسجَّل، ويفشل (خروج 1) عند أي انحراف. تدقيق/بحث فقط · لا يمسّ الفرز · لا LOGIC_VERSION.

يصلح العيوب السبعة (طبقة قياس/توثيق): فصل الهدفين (Y_DISCOVERY/Y_TRADABLE/Y_POST_STOP) ·
estimand مصحَّح لـH_BEHAV (Y_POST_STOP) · عتبات train-only (2025→2026 primary، عكسي=حساسية،
pooled=legacy) · Newcombe/Wilson RD CI ضمنيًّا (proportion) · permutation للشهر · عائلات FDR
(legacy 4/5 + audit sensitivity) · تصحيح الصياغة (لا «حافة مثبتة»).

تشغيل:  python3 phase_p0_audit.py   → يكتب p0_audit_outputs/ + يطبع PASS/FAIL مقابل مرجع Codex.
"""
from __future__ import annotations
from pathlib import Path
import csv, json, math, hashlib, platform, sys, collections
import datetime as dt
import numpy as np
import scipy
from scipy.stats import fisher_exact, mannwhitneyu, chi2_contingency
from scipy.optimize import brentq
import statsmodels
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportion_confint, proportion_effectsize
from statsmodels.stats.power import NormalIndPower
import sklearn
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "p0_audit_outputs"
OUT.mkdir(exist_ok=True)
FILES = {
    2025: ROOT / "phase_e_dataset_2025_frozen.csv",
    2026: ROOT / "phase_e_dataset_2026_frozen.csv",
}
PREV = ROOT / "phase_e_previous_dataset_for_overlap.csv"
CODEX_REF = ROOT / "p0_acceptance_reference_codex.json"   # مرجع Codex للمطابقة
PERMUTATIONS = 50_000
BOOTSTRAPS = 20_000
SEED = 20260713

NUMERIC = ["readiness", "behav_score", "score", "fwd_max_gain", "mg_pre_stop", "entry",
           "raw_pit_entry", "drop_pct", "best_spike", "rr", "h4_bars", "h4_rsi"]


def fnum(x):
    if x is None or x == "":
        return None
    return float(x)


def bval(x):
    if x is None or x == "":
        return None
    return str(x).strip().lower() == "true"


def load(path, year):
    with path.open(newline="", encoding="utf-8-sig") as fh:
        rows = list(csv.DictReader(fh))
    for i, r in enumerate(rows, start=2):
        r["year"] = year
        r["source_row_number"] = i
        r["date"] = dt.date.fromisoformat(r["date"])
        for k in NUMERIC:
            r[k] = fnum(r[k])
        r["exploded"] = bval(r["exploded"])
        r["h4_reversal"] = bval(r["h4_reversal"])
        r["row_id"] = f"{year}|{r['symbol']}|{r['date'].isoformat()}|row{i}"
    return rows


D = {y: load(p, y) for y, p in FILES.items()}
R = D[2025] + D[2026]


def filled(r): return r["mg_outcome"] not in ("", "no_fill")
def y_discovery(r): return r["fwd_max_gain"] is not None and r["fwd_max_gain"] >= 50
def y_tradable(r): return r["mg_pre_stop"] is not None and r["mg_pre_stop"] >= 50
def y_post_stop(r): return y_discovery(r) and not y_tradable(r)
def stopped(r): return r["mg_outcome"] == "stopped"
def h4_eligible(r): return filled(r) and (r["h4_bars"] or 0) >= 10
def price_eff(r): return r["raw_pit_entry"] if r["raw_pit_entry"] is not None else r["entry"]


def json_num(x):
    x = float(x)
    if math.isinf(x):
        return "inf" if x > 0 else "-inf"
    if math.isnan(x):
        return None
    return x


def binary_test(source, exposure, target, eligible):
    z = [r for r in source if eligible(r)]
    a = sum(bool(exposure(r)) and bool(target(r)) for r in z)
    b = sum(bool(exposure(r)) and not bool(target(r)) for r in z)
    c = sum(not bool(exposure(r)) and bool(target(r)) for r in z)
    d = sum(not bool(exposure(r)) and not bool(target(r)) for r in z)
    OR, p = fisher_exact([[a, b], [c, d]], alternative="two-sided")
    re = a / (a + b) if a + b else None
    rc = c / (c + d) if c + d else None
    return {"table": [[a, b], [c, d]], "success_exposed": a, "n_exposed": a + b,
            "success_control": c, "n_control": c + d, "risk_exposed": re, "risk_control": rc,
            "risk_difference": None if re is None or rc is None else re - rc,
            "odds_ratio": json_num(OR), "p_fisher_two_sided": float(p)}


def score_test(source, target):
    z = [r for r in source if filled(r) and r["score"] is not None]
    y = np.array([1 if target(r) else 0 for r in z], dtype=int)
    x = np.array([-r["score"] for r in z], dtype=float)
    if y.min() == y.max():
        return {"n": len(z), "positives": int(y.sum()), "auc": None, "p_mwu_one_sided": None}
    auc = roc_auc_score(y, x)
    p = mannwhitneyu(x[y == 1], x[y == 0], alternative="greater").pvalue
    return {"n": len(z), "positives": int(y.sum()), "negatives": int((1 - y).sum()),
            "auc_negative_score": float(auc), "p_mwu_one_sided": float(p)}


def month_test(source, target, permutations=PERMUTATIONS, seed=SEED):
    z = [r for r in source if filled(r)]
    table = []
    qlabels = []
    yy = []
    for q in range(4):
        qr = [r for r in z if (r["date"].month - 1) // 3 == q]
        s = sum(target(r) for r in qr)
        table.append([s, len(qr) - s])
    chi = chi2_contingency(table, correction=False)
    for r in z:
        qlabels.append((r["date"].month - 1) // 3)
        yy.append(1 if target(r) else 0)
    qlabels = np.array(qlabels)
    yy = np.array(yy)
    rng = np.random.default_rng(seed)
    ge = 0
    for _ in range(permutations):
        yp = rng.permutation(yy)
        tt = [[int(((qlabels == q) & (yp == 1)).sum()), int(((qlabels == q) & (yp == 0)).sum())]
              for q in range(4)]
        st = chi2_contingency(tt, correction=False).statistic
        ge += st >= chi.statistic - 1e-12
    return {"table": table, "chi_square": float(chi.statistic), "p_chi_square": float(chi.pvalue),
            "expected": np.asarray(chi.expected_freq).tolist(), "permutation_seed": seed,
            "permutations": permutations, "p_permutation": (ge + 1) / (permutations + 1)}


def by_scope_binary(exposure, target, eligible):
    return {"2025": binary_test(D[2025], exposure, target, eligible),
            "2026": binary_test(D[2026], exposure, target, eligible),
            "pooled": binary_test(R, exposure, target, eligible)}


def quantile_threshold(source, feature):
    vals = np.array([r[feature] for r in source if filled(r) and r[feature] is not None], dtype=float)
    return float(np.quantile(vals, 2 / 3, method="linear"))


def transfer_test(train_year, test_year, feature, target):
    th = quantile_threshold(D[train_year], feature)
    res = binary_test(D[test_year], lambda r: r[feature] is not None and r[feature] >= th,
                      target, lambda r: filled(r) and r[feature] is not None)
    return {"train_year": train_year, "test_year": test_year, "feature": feature,
            "quantile": 2 / 3, "quantile_method": "linear", "comparison": ">=",
            "threshold": th, "result": res}


def bh(ps):
    return multipletests(np.asarray(ps, dtype=float), method="fdr_bh")[1].tolist()


def detectable_rate(n1, n0, p0, alpha, target_power=.8):
    calc = NormalIndPower()
    ratio = n0 / n1

    def fn(p1):
        h = abs(proportion_effectsize(p1, p0))
        return calc.power(h, nobs1=n1, ratio=ratio, alpha=alpha, alternative="two-sided") - target_power
    return float(brentq(fn, p0 + 1e-9, .999999))


summary = {}
for y in (2025, 2026):
    fy = [r for r in D[y] if filled(r)]
    summary[str(y)] = {
        "signals": len(D[y]), "filled": len(fy),
        "settled_t1": sum(r["outcome"] in ("win", "loss") for r in D[y]),
        "t1_wins": sum(r["outcome"] == "win" for r in D[y]),
        "Y_DISCOVERY": sum(y_discovery(r) for r in fy),
        "Y_TRADABLE": sum(y_tradable(r) for r in fy),
        "Y_POST_STOP": sum(y_post_stop(r) for r in fy),
        "h4_covered": sum((r["h4_bars"] or 0) >= 10 for r in fy),
        "date_min": min(r["date"] for r in D[y]).isoformat(),
        "date_max": max(r["date"] for r in D[y]).isoformat()}
rate_ci = {}
for label, k, n in [("2025_discovery", 12, 68), ("2025_tradable", 9, 68), ("2026_discovery", 8, 56),
                    ("2026_tradable", 7, 56), ("pooled_discovery", 20, 124), ("pooled_tradable", 16, 124)]:
    lo, hi = proportion_confint(k, n, method="wilson")
    rate_ci[label] = {"k": k, "n": n, "rate": k / n, "wilson95": [float(lo), float(hi)]}

hyp = {}
hyp["H_BEHAV_REARM"] = {
    "eligibility": "mg_outcome == stopped", "exposure": "behav_score >= 60",
    "Y_DISCOVERY": by_scope_binary(lambda r: r["behav_score"] >= 60, y_discovery, stopped),
    "Y_TRADABLE": by_scope_binary(lambda r: r["behav_score"] >= 60, y_tradable, stopped),
    "Y_POST_STOP": by_scope_binary(lambda r: r["behav_score"] >= 60, y_post_stop, stopped)}
hyp["H_SCORE_INVERSE"] = {"direction": "lower score is positive; evaluate AUC(-score)",
    "Y_DISCOVERY": {"2025": score_test(D[2025], y_discovery), "2026": score_test(D[2026], y_discovery), "pooled": score_test(R, y_discovery)},
    "Y_TRADABLE": {"2025": score_test(D[2025], y_tradable), "2026": score_test(D[2026], y_tradable), "pooled": score_test(R, y_tradable)}}
hyp["H_PRICE_2_5"] = {"exposure": "2 <= effective_entry < 5",
    "Y_DISCOVERY": by_scope_binary(lambda r: 2 <= price_eff(r) < 5, y_discovery, filled),
    "Y_TRADABLE": by_scope_binary(lambda r: 2 <= price_eff(r) < 5, y_tradable, filled)}
hyp["H_READINESS_LOW"] = {"exposure": "readiness <= 54",
    "Y_DISCOVERY": by_scope_binary(lambda r: r["readiness"] <= 54, y_discovery, filled),
    "Y_TRADABLE": by_scope_binary(lambda r: r["readiness"] <= 54, y_tradable, filled)}
hyp["H_4H_REVERSAL"] = {"eligibility": "filled and h4_bars >= 10", "exposure": "h4_reversal == True",
    "Y_DISCOVERY": by_scope_binary(lambda r: r["h4_reversal"] is True, y_discovery, h4_eligible),
    "Y_TRADABLE": by_scope_binary(lambda r: r["h4_reversal"] is True, y_tradable, h4_eligible)}
hyp["H_4H_RSI_LOW"] = {"eligibility": "filled and h4_bars >= 10 and h4_rsi nonmissing", "exposure": "h4_rsi <= 35",
    "Y_DISCOVERY": by_scope_binary(lambda r: r["h4_rsi"] <= 35, y_discovery, lambda r: h4_eligible(r) and r["h4_rsi"] is not None),
    "Y_TRADABLE": by_scope_binary(lambda r: r["h4_rsi"] <= 35, y_tradable, lambda r: h4_eligible(r) and r["h4_rsi"] is not None)}
for name, feature in [("H_DROP_DEEP", "drop_pct"), ("H_SPIKE_BIG", "best_spike"), ("H_RR_HIGH", "rr")]:
    pooled_th = quantile_threshold(R, feature)
    hyp[name] = {"feature": feature,
        "pooled_legacy": {"threshold": pooled_th, "comparison": ">=",
            "Y_DISCOVERY": by_scope_binary(lambda r, f=feature, t=pooled_th: r[f] >= t, y_discovery, lambda r, f=feature: filled(r) and r[f] is not None),
            "Y_TRADABLE": by_scope_binary(lambda r, f=feature, t=pooled_th: r[f] >= t, y_tradable, lambda r, f=feature: filled(r) and r[f] is not None)},
        "forward_2025_to_2026": {"Y_DISCOVERY": transfer_test(2025, 2026, feature, y_discovery), "Y_TRADABLE": transfer_test(2025, 2026, feature, y_tradable)},
        "reverse_sensitivity_2026_to_2025": {"Y_DISCOVERY": transfer_test(2026, 2025, feature, y_discovery), "Y_TRADABLE": transfer_test(2026, 2025, feature, y_tradable)}}
hyp["H_MONTH_REGIME"] = {"Y_DISCOVERY": month_test(R, y_discovery), "Y_TRADABLE": month_test(R, y_tradable)}

legacy_p = {
    "H_BEHAV_REARM": hyp["H_BEHAV_REARM"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_SCORE_INVERSE": hyp["H_SCORE_INVERSE"]["Y_TRADABLE"]["pooled"]["p_mwu_one_sided"],
    "H_PRICE_2_5": hyp["H_PRICE_2_5"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_READINESS_LOW": hyp["H_READINESS_LOW"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_4H_REVERSAL": hyp["H_4H_REVERSAL"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_4H_RSI_LOW": hyp["H_4H_RSI_LOW"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_DROP_DEEP": hyp["H_DROP_DEEP"]["pooled_legacy"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_SPIKE_BIG": hyp["H_SPIKE_BIG"]["pooled_legacy"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_RR_HIGH": hyp["H_RR_HIGH"]["pooled_legacy"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_MONTH_REGIME": hyp["H_MONTH_REGIME"]["Y_DISCOVERY"]["p_permutation"]}
primary_p = {
    "H_BEHAV_REARM": hyp["H_BEHAV_REARM"]["Y_POST_STOP"]["pooled"]["p_fisher_two_sided"],
    "H_SCORE_INVERSE": hyp["H_SCORE_INVERSE"]["Y_TRADABLE"]["pooled"]["p_mwu_one_sided"],
    "H_PRICE_2_5": hyp["H_PRICE_2_5"]["Y_TRADABLE"]["pooled"]["p_fisher_two_sided"],
    "H_READINESS_LOW": hyp["H_READINESS_LOW"]["Y_TRADABLE"]["pooled"]["p_fisher_two_sided"],
    "H_4H_REVERSAL": hyp["H_4H_REVERSAL"]["Y_TRADABLE"]["pooled"]["p_fisher_two_sided"],
    "H_4H_RSI_LOW": hyp["H_4H_RSI_LOW"]["Y_TRADABLE"]["pooled"]["p_fisher_two_sided"],
    "H_DROP_DEEP": hyp["H_DROP_DEEP"]["forward_2025_to_2026"]["Y_TRADABLE"]["result"]["p_fisher_two_sided"],
    "H_SPIKE_BIG": hyp["H_SPIKE_BIG"]["forward_2025_to_2026"]["Y_TRADABLE"]["result"]["p_fisher_two_sided"],
    "H_RR_HIGH": hyp["H_RR_HIGH"]["forward_2025_to_2026"]["Y_TRADABLE"]["result"]["p_fisher_two_sided"],
    "H_MONTH_REGIME": hyp["H_MONTH_REGIME"]["Y_TRADABLE"]["p_permutation"]}
secondary_p = {
    "H_BEHAV_REARM": hyp["H_BEHAV_REARM"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_SCORE_INVERSE": hyp["H_SCORE_INVERSE"]["Y_DISCOVERY"]["pooled"]["p_mwu_one_sided"],
    "H_PRICE_2_5": hyp["H_PRICE_2_5"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_READINESS_LOW": hyp["H_READINESS_LOW"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_4H_REVERSAL": hyp["H_4H_REVERSAL"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_4H_RSI_LOW": hyp["H_4H_RSI_LOW"]["Y_DISCOVERY"]["pooled"]["p_fisher_two_sided"],
    "H_DROP_DEEP": hyp["H_DROP_DEEP"]["forward_2025_to_2026"]["Y_DISCOVERY"]["result"]["p_fisher_two_sided"],
    "H_SPIKE_BIG": hyp["H_SPIKE_BIG"]["forward_2025_to_2026"]["Y_DISCOVERY"]["result"]["p_fisher_two_sided"],
    "H_RR_HIGH": hyp["H_RR_HIGH"]["forward_2025_to_2026"]["Y_DISCOVERY"]["result"]["p_fisher_two_sided"],
    "H_MONTH_REGIME": hyp["H_MONTH_REGIME"]["Y_DISCOVERY"]["p_permutation"]}


def attach_q(pmap):
    names = list(pmap)
    qs = bh([pmap[n] for n in names])
    return {n: {"p": pmap[n], "q_bh": qs[i]} for i, n in enumerate(names)}


prev_summary = {}
overlap_rows = []
if PREV.exists():
    with PREV.open(newline="", encoding="utf-8-sig") as fh:
        old = list(csv.DictReader(fh))
    for i, r in enumerate(old, start=2):
        r["year"] = int(r["year"])
        r["date"] = dt.date.fromisoformat(r["date"])
        r["source_row_number"] = i
    om = collections.defaultdict(list)
    nm = collections.defaultdict(list)
    for r in old:
        om[(r["year"], r["symbol"])].append(r)
    for r in R:
        nm[(r["year"], r["symbol"])].append(r)
    common = sorted(om.keys() & nm.keys())
    af = at = 0

    def of(r, k):
        try:
            return float(r[k]) if r[k] else None
        except Exception:
            return None
    for key in common:
        oe = any((of(r, "fwd_max_gain") or -999) >= 50 for r in om[key])
        ne = any(y_discovery(r) for r in nm[key])
        ot = any((of(r, "mg_pre_stop") or -999) >= 50 for r in om[key])
        nt = any(y_tradable(r) for r in nm[key])
        af += oe == ne
        at += ot == nt
        od = sorted(r["date"].isoformat() for r in om[key])
        nd = sorted(r["date"].isoformat() for r in nm[key])
        overlap_rows.append({"year": key[0], "symbol": key[1], "old_dates": "|".join(od), "new_dates": "|".join(nd),
                             "exact_date_overlap": bool(set(od) & set(nd)), "old_Y_DISCOVERY": oe, "new_Y_DISCOVERY": ne,
                             "discovery_agrees": oe == ne, "old_Y_TRADABLE": ot, "new_Y_TRADABLE": nt, "tradable_agrees": ot == nt})
    oldkeys = {(r["year"], r["symbol"], r["date"]) for r in old}
    newkeys = {(r["year"], r["symbol"], r["date"]) for r in R}
    oldsy = set(om)
    newsy = set(nm)
    prev_summary = {"old_rows": len(old), "new_rows": len(R), "exact_symbol_date_overlap": len(oldkeys & newkeys),
                    "exact_symbol_date_pct_of_new": len(oldkeys & newkeys) / len(newkeys), "symbol_year_overlap": len(oldsy & newsy),
                    "symbol_year_pct_of_new": len(oldsy & newsy) / len(newsy), "common_symbol_year": len(common),
                    "discovery_label_agreement": af / len(common), "tradable_label_agreement": at / len(common)}

issues = []
for r in R:
    cats = []
    if r["exploded"] != y_discovery(r):
        cats.append("EXPLODED_COLUMN_MISMATCH")
    if r["mg_pre_stop"] is not None and r["fwd_max_gain"] is not None and r["mg_pre_stop"] > r["fwd_max_gain"] + 1e-12:
        cats.append("MG_PRE_STOP_GT_FWD_MAX_GAIN")
    if r["raw_pit_entry"] is None:
        cats.append("RAW_PIT_ENTRY_MISSING")
    if price_eff(r) is not None and price_eff(r) < 1.5:
        cats.append("EFFECTIVE_ENTRY_LT_1_5")
    if r["mg_outcome"] == "no_fill" and r["mg_pre_stop"] is not None:
        cats.append("NO_FILL_HAS_MG_PRE_STOP")
    if r["mg_outcome"] != "no_fill" and r["mg_pre_stop"] is None:
        cats.append("FILLED_MISSING_MG_PRE_STOP")
    if cats:
        issues.append({"row_id": r["row_id"], "year": r["year"], "symbol": r["symbol"], "date": r["date"].isoformat(),
                       "source_row_number": r["source_row_number"], "categories": "|".join(cats), "mg_outcome": r["mg_outcome"],
                       "entry": r["entry"], "raw_pit_entry": r["raw_pit_entry"], "effective_entry": price_eff(r),
                       "fwd_max_gain": r["fwd_max_gain"], "mg_pre_stop": r["mg_pre_stop"], "Y_DISCOVERY": y_discovery(r), "Y_TRADABLE": y_tradable(r)})

hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in list(FILES.values()) + ([PREV] if PREV.exists() else [])}
power = {"method": "statsmodels NormalIndPower using Cohen h from proportion_effectsize; two-sided z approximation",
         "n_exposed": 42, "n_control": 82, "baseline_control": .16, "target_power": .8,
         "alpha_0_05_detectable_rate": detectable_rate(42, 82, .16, .05),
         "alpha_0_0125_detectable_rate": detectable_rate(42, 82, .16, .0125)}

result = {"schema_version": "2.0", "generated_by": "phase_p0_audit.py (logic identical to Codex reproduce_phase_e_audit.py)",
          "seeds": {"global": SEED, "permutations": PERMUTATIONS, "bootstraps_reserved": BOOTSTRAPS},
          "environment": {"python": sys.version, "platform": platform.platform(), "numpy": np.__version__,
                          "scipy": scipy.__version__, "statsmodels": statsmodels.__version__, "sklearn": sklearn.__version__},
          "input_sha256": hashes, "locked_targets": {"Y_DISCOVERY": "fwd_max_gain >= 50", "Y_TRADABLE": "mg_pre_stop >= 50",
          "Y_POST_STOP": "Y_DISCOVERY and not Y_TRADABLE; used only for H_BEHAV_REARM"},
          "summary": summary, "rate_confidence_intervals": rate_ci, "hypotheses": hyp,
          "fdr": {"legacy_mapping": attach_q(legacy_p), "recommended_primary_family_10": attach_q(primary_p),
                  "recommended_secondary_family_10": attach_q(secondary_p),
                  "global_20_sensitivity": attach_q({**{f"PRIMARY::{k}": v for k, v in primary_p.items()}, **{f"SECONDARY::{k}": v for k, v in secondary_p.items()}})},
          "power": power, "equivalence_spec": {"scale": "risk difference", "primary_margin": 0.08, "sensitivity_margin": 0.05,
          "alpha": 0.05, "accept_equivalence_if": "90% CI for risk difference lies wholly inside [-margin,+margin]"},
          "previous_dataset_overlap_summary": prev_summary,
          "integrity_summary": {"rows_flagged": len(issues), "category_counts": dict(collections.Counter(c for x in issues for c in x["categories"].split("|")))},
          "train_only_rule": {"train": 2025, "test": 2026, "q": 2 / 3, "numpy_method": "linear", "comparison": ">=",
          "reverse_2026_to_2025": "sensitivity only; never call it forward OOS"}}

(OUT / "audit_results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
with (OUT / "row_integrity_issues.csv").open("w", newline="", encoding="utf-8-sig") as fh:
    fields = list(issues[0])
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(issues)
with (OUT / "previous_dataset_overlap.csv").open("w", newline="", encoding="utf-8-sig") as fh:
    fields = list(overlap_rows[0])
    w = csv.DictWriter(fh, fieldnames=fields)
    w.writeheader()
    w.writerows(overlap_rows)

accept = {"input_sha256": hashes, "exact_counts": summary, "legacy_required": {
    "BEHAV_REARM": {"table": hyp["H_BEHAV_REARM"]["Y_DISCOVERY"]["pooled"]["table"], "OR": hyp["H_BEHAV_REARM"]["Y_DISCOVERY"]["pooled"]["odds_ratio"], "p": legacy_p["H_BEHAV_REARM"]},
    "SCORE": {"AUC": hyp["H_SCORE_INVERSE"]["Y_TRADABLE"]["pooled"]["auc_negative_score"], "p": legacy_p["H_SCORE_INVERSE"]},
    "PRICE": {"table": hyp["H_PRICE_2_5"]["Y_DISCOVERY"]["pooled"]["table"], "OR": hyp["H_PRICE_2_5"]["Y_DISCOVERY"]["pooled"]["odds_ratio"], "p": legacy_p["H_PRICE_2_5"]},
    "READINESS": {"table": hyp["H_READINESS_LOW"]["Y_DISCOVERY"]["pooled"]["table"], "OR": hyp["H_READINESS_LOW"]["Y_DISCOVERY"]["pooled"]["odds_ratio"], "p": legacy_p["H_READINESS_LOW"]},
    "PHASE_C_Q": [x["q_bh"] for x in attach_q({k: legacy_p[k] for k in ["H_BEHAV_REARM", "H_SCORE_INVERSE", "H_PRICE_2_5", "H_READINESS_LOW"]}).values()],
    "H4_REV": {"table": hyp["H_4H_REVERSAL"]["Y_DISCOVERY"]["pooled"]["table"], "OR": hyp["H_4H_REVERSAL"]["Y_DISCOVERY"]["pooled"]["odds_ratio"], "p": legacy_p["H_4H_REVERSAL"]},
    "POOLED_THRESHOLDS": {k: hyp[n]["pooled_legacy"]["threshold"] for k, n in [("drop_pct", "H_DROP_DEEP"), ("best_spike", "H_SPIKE_BIG"), ("rr", "H_RR_HIGH")]},
    "POWER": power, "OVERLAP": prev_summary},
    "tolerances": {"integer_counts_and_2x2_tables": "exact", "sha256": "exact", "thresholds": 1e-12, "OR_AUC_p_q_CI_MDE": 1e-6,
                   "permutation_p": 5e-4, "canonical_json_byte_match": "required only with identical package versions and platform"}}
(OUT / "acceptance_reference.json").write_text(json.dumps(accept, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")

# ── الفحص الذاتي: طابق مخرجاتي بمرجع Codex ضمن التسامح (fail = خروج 1) ───────
FAILS = []


def _close(a, b, tol):
    try:
        return abs(float(a) - float(b)) <= tol
    except Exception:
        return a == b


if CODEX_REF.exists():
    ref = json.loads(CODEX_REF.read_text(encoding="utf-8"))
    # counts + SHA (تام — نقارن قيم البصمات لا أسماء الملفات؛ ملف التداخل أُعيد تسميته
    # `phase_e_previous_dataset_for_overlap.csv` بالمستودع، ومحتواه بت-بت = ملف Codex).
    if sorted(accept["input_sha256"].values()) != sorted(ref["input_sha256"].values()):
        FAILS.append("input_sha256 values mismatch")
    for y in ("2025", "2026"):
        for k, v in ref["exact_counts"][y].items():
            if accept["exact_counts"][y].get(k) != v:
                FAILS.append(f"count {y}.{k}: {accept['exact_counts'][y].get(k)} != {v}")
    lr, rr = accept["legacy_required"], ref["legacy_required"]
    for hk in ("BEHAV_REARM", "PRICE", "READINESS", "H4_REV"):
        if lr[hk]["table"] != rr[hk]["table"]:
            FAILS.append(f"{hk} table mismatch")
        for m in ("OR", "p"):
            if not _close(lr[hk][m], rr[hk][m], 1e-6):
                FAILS.append(f"{hk}.{m}: {lr[hk][m]} != {rr[hk][m]}")
    for m in ("AUC", "p"):
        if not _close(lr["SCORE"][m], rr["SCORE"][m], 1e-6):
            FAILS.append(f"SCORE.{m}")
    for i, (a, b) in enumerate(zip(lr["PHASE_C_Q"], rr["PHASE_C_Q"])):
        if not _close(a, b, 1e-6):
            FAILS.append(f"PHASE_C_Q[{i}]")
    for k in ("drop_pct", "best_spike", "rr"):
        if not _close(lr["POOLED_THRESHOLDS"][k], rr["POOLED_THRESHOLDS"][k], 1e-12):
            FAILS.append(f"POOLED_THRESHOLD {k}")
    for k in ("alpha_0_05_detectable_rate", "alpha_0_0125_detectable_rate"):
        if not _close(lr["POWER"][k], rr["POWER"][k], 1e-6):
            FAILS.append(f"POWER {k}")
    for k, v in rr["OVERLAP"].items():
        if not _close(lr["OVERLAP"].get(k), v, 1e-6):
            FAILS.append(f"OVERLAP {k}")
else:
    FAILS.append(f"مرجع Codex غير موجود: {CODEX_REF}")

# التصحيحات المصحَّحة المهمّة (للعرض)
_beh_ps = hyp["H_BEHAV_REARM"]["Y_POST_STOP"]["pooled"]
_fwd = hyp["H_DROP_DEEP"]["forward_2025_to_2026"]["Y_DISCOVERY"]
print(json.dumps({
    "status": "PASS" if not FAILS else "FAIL",
    "fails": FAILS,
    "outputs": str(OUT),
    "corrected_estimand_H_BEHAV_Y_POST_STOP": {"table": _beh_ps["table"], "OR": _beh_ps["odds_ratio"], "p": _beh_ps["p_fisher_two_sided"]},
    "train_only_thresholds": {"drop_pct": _fwd["threshold"], "best_spike": hyp["H_SPIKE_BIG"]["forward_2025_to_2026"]["Y_DISCOVERY"]["threshold"], "rr": hyp["H_RR_HIGH"]["forward_2025_to_2026"]["Y_DISCOVERY"]["threshold"]},
    "verdict": "لم تُكتشف حافة فرز كبيرة مستقرة ضمن الفرضيات المختبرة؛ القوة منخفضة تمنع نفي أثر متوسط. التوقيت اللحظي فرضية تالية غير مثبتة.",
}, ensure_ascii=False, indent=2))
if FAILS:
    sys.exit(1)
