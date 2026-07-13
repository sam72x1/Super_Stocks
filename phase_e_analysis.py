#!/usr/bin/env python3
"""Phase E — تحليل OOS المسجَّل مسبقًا (E1 شمعة 4س · E3 نظام السوق) على المجمَّد.
يقرأ CSVين موسَّعين (drop_pct/best_spike/rr + h4_bars/h4_reversal/h4_rsi).
E1: أولًا التغطية (h4_bars>=10) — إن <50% → جدار بيانات (4س حيّة فقط). وإلا اختبار الانعكاس/RSI.
E3: شرائح الثلث العليا (drop/spike/rr) + chi-square للربع. FDR عبر العائلة. تدقيق/بحث فقط.
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats

P25, P26 = sys.argv[1], sys.argv[2]


def load(path, year):
    d = pd.read_csv(path)
    d["year"] = year
    d["filled"] = d["mg_outcome"].notna() & (d["mg_outcome"] != "no_fill")
    d["explode"] = pd.to_numeric(d["fwd_max_gain"], errors="coerce") >= 50
    d["q"] = pd.to_datetime(d["date"]).dt.quarter
    for c in ("drop_pct", "best_spike", "rr", "h4_bars", "h4_rsi"):
        if c in d:
            d[c] = pd.to_numeric(d[c], errors="coerce")
    if "h4_reversal" in d:
        d["h4_rev"] = d["h4_reversal"].astype(str).str.strip().isin(["True", "true", "1"])
    return d


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((c - h) / d, (c + h) / d)


def fisher(rule, tgt):
    a = int((rule & tgt).sum()); b = int((rule & ~tgt).sum())
    c = int((~rule & tgt).sum()); d = int((~rule & ~tgt).sum())
    n1, n0 = a + b, c + d
    r1 = a / n1 if n1 else float("nan"); r0 = c / n0 if n0 else float("nan")
    orr, p = stats.fisher_exact([[a, b], [c, d]])
    return {"a": a, "n1": n1, "r1": r1, "c": c, "n0": n0, "r0": r0, "or": orr, "p": p, "diff": r1 - r0}


def bh_fdr(pvals):
    p = np.asarray(pvals, float); m = len(p); order = np.argsort(p)
    q = np.empty(m); prev = 1.0
    for rank in range(m - 1, -1, -1):
        idx = order[rank]; prev = min(prev, p[idx] * m / (rank + 1)); q[idx] = prev
    return q


d25, d26 = load(P25, 2025), load(P26, 2026)
alld = pd.concat([d25, d26], ignore_index=True)
results = []


def top_tercile(series_all, series):
    """قناع «أعلى ثلث» بعتبة محسوبة على مجتمع الاختبار نفسه (fold)."""
    thr = series_all.quantile(2 / 3)
    return series >= thr


def run_binary(hid, popcol, rulefn, direction="positive"):
    per = {}
    for yr, d in [(2025, d25), (2026, d26)]:
        pop = d[d[popcol]].copy()
        if len(pop) < 4:
            per[yr] = None; continue
        per[yr] = fisher(rulefn(pop), pop["explode"])
    popA = alld[alld[popcol]].copy()
    pool = fisher(rulefn(popA), popA["explode"])
    signs = [per[y]["diff"] > 0 if direction == "positive" else per[y]["diff"] < 0
             for y in (2025, 2026) if per[y] and not np.isnan(per[y]["diff"])]
    consistent = len(signs) == 2 and all(signs)
    results.append((hid, pool["p"], consistent, {"per": per, "pool": pool}))


print("=" * 80)
print("Phase E — E1 (4س) + E3 (نظام السوق) — OOS مسجَّل مسبقًا")
print("=" * 80)
for nm, d in [("2025", d25), ("2026", d26)]:
    f = d[d["filled"]]
    cov = int((f["h4_bars"] >= 10).sum()) if "h4_bars" in d else 0
    print(f"  {nm}: مُعبَّأة={int(d['filled'].sum())} · انفجر50%+={int(d['explode'].sum())} · "
          f"4س متوفّرة(h4_bars≥10)={cov}/{int(d['filled'].sum())}")

# ── E1: التغطية أولًا ───────────────────────────────────────────────────────
fa = alld[alld["filled"]]
covn = int((fa["h4_bars"] >= 10).sum()) if "h4_bars" in alld else 0
covpct = covn / len(fa) * 100 if len(fa) else 0
print("\n" + "─" * 80)
print(f"E1 — التغطية التاريخية لـ4س: {covn}/{len(fa)} مُعبَّأة ({covpct:.0f}%)")
if covpct < 50:
    print("  📋 الحكم المسجَّل: التغطية < 50% → جدار بيانات (yfinance 1h لا يغطّي المايكروكاب تاريخيًّا).")
    print("     ⇒ 4س حافة **حيّة فقط** (كما يستعملها البوت: fetch_4h في الإثراء + دقائق الرادار). لا اختبار OOS.")
    e1_testable = False
else:
    print("  ✅ التغطية كافية → أختبر H_4H_REVERSAL + H_4H_RSI_LOW.")
    e1_testable = True
    d25["h4ok"] = (d25["h4_bars"] >= 10)
    d26["h4ok"] = (d26["h4_bars"] >= 10)
    alld["h4ok"] = (alld["h4_bars"] >= 10)
    run_binary("H_4H_REVERSAL", "h4ok", lambda d: d["h4_rev"], "positive")
    run_binary("H_4H_RSI_LOW", "h4ok", lambda d: d["h4_rsi"] <= 35, "positive")

# ── E3: نظام السوق (على المجمَّد اليومي) ─────────────────────────────────────
run_binary("H_DROP_DEEP", "filled",
           lambda d: top_tercile(fa["drop_pct"], d["drop_pct"]), "positive")
run_binary("H_SPIKE_BIG", "filled",
           lambda d: top_tercile(fa["best_spike"], d["best_spike"]), "positive")
run_binary("H_RR_HIGH", "filled",
           lambda d: top_tercile(fa["rr"], d["rr"]), "positive")

# ── FDR عبر العائلة ─────────────────────────────────────────────────────────
ids = [r[0] for r in results]
qs = dict(zip(ids, bh_fdr([r[1] for r in results])))
print("\n" + "─" * 80)
print("النتائج (Fisher لكل سنة + مجمَّع + FDR):")
for hid, p_pool, consistent, det in results:
    q = qs[hid]
    print(f"\n▸ {hid}")
    for yr in (2025, 2026):
        e = det["per"][yr]
        if e is None:
            print(f"    {yr}: — (عيّنة <4)"); continue
        lo1, hi1 = wilson(e["a"], e["n1"]); lo0, hi0 = wilson(e["c"], e["n0"])
        print(f"    {yr}: قاعدة✓ {e['a']}/{e['n1']}={e['r1']*100:.0f}% (CI {lo1*100:.0f}-{hi1*100:.0f}) "
              f"مقابل {e['c']}/{e['n0']}={e['r0']*100:.0f}% · OR {e['or']:.2f} · p {e['p']:.3f} · فرق {e['diff']*100:+.0f}ن")
    pl = det["pool"]
    print(f"    مجمَّع: {pl['a']}/{pl['n1']}={pl['r1']*100:.0f}% مقابل {pl['c']}/{pl['n0']}={pl['r0']*100:.0f}% "
          f"· OR {pl['or']:.2f} · p {pl['p']:.3f}")
    verdict = "✅ ينجو" if (consistent and q < 0.10) else "❌ لا ينجو"
    print(f"    اتساق: {'نعم' if consistent else 'لا'} · q(FDR) {q:.3f} → {verdict}")

# ── H_MONTH_REGIME: chi-square على الربع (استكشافي) ─────────────────────────
print("\n▸ H_MONTH_REGIME (استكشافي — نظام سوق لا اختيار)")
ct = pd.crosstab(fa["q"], fa["explode"])
try:
    chi2, pmonth, dof, _ = stats.chi2_contingency(ct)
    for qq in sorted(fa["q"].unique()):
        sub = fa[fa["q"] == qq]
        print(f"    ربع {qq}: انفجر {int(sub['explode'].sum())}/{len(sub)} = {sub['explode'].mean()*100:.0f}%")
    print(f"    chi-square p={pmonth:.3f} → {'اختلاف جوهري' if pmonth < 0.05 else 'لا اختلاف جوهري (نظام السوق لا يميّز)'}")
except Exception as e:
    print(f"    تعذّر chi-square: {e}")

print("\n" + "=" * 80)
surv = [h for h, p, c, det in results if c and qs[h] < 0.10]
if surv:
    print(f"🎯 ناجون (يحتاجون مراجعة خصومية + موافقة): {surv}")
else:
    print("📋 الحكم المسجَّل: لا شيء ينجو من FDR بالسنتين →")
    print("   لا 4س ولا نظام سوق يميّز المنفجر على مستوى الفرز. يتّسق مع حكم السنتين: الحافة التوقيت لا الفرز.")
print("=" * 80)
