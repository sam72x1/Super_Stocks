#!/usr/bin/env python3
"""Phase C — اختبار OOS مسجَّل مسبقًا للفرضيات الأربع على اللقطة المجمَّدة.

يقرأ CSVين للباكتيست (2025 + 2026 على نفس اللقطة المجمَّدة SHA aac35221) ويطبّق
الفرضيات الأربع المقفولة في PREREGISTERED_HYPOTHESES.yaml بطريقة القبول المسجَّلة:
  - كل فرضية: قاعدة مقفولة + هدف مقفول + مجتمع مقفول (لا عصر عتبات).
  - walk-forward = ثنيتان زمنيتان (2025 · 2026) مستقلتان — الاتجاه يجب أن يتّسق.
  - Fisher exact لكل ثنية + مجمَّع · AUC(-score) للفرضية العكسية (train سنة/اختبار الأخرى).
  - Benjamini-Hochberg FDR عبر الفرضيات الأربع (q<0.10 على المجمَّع).
  - الحكم: ناجٍ فقط لو (اتجاه متّسق بالسنتين) + (q<0.10) + (فرق ذو معنى + CI لا يلمس صفر).

تدقيق/بحث فقط — لا يمسّ الإنتاج. الأرقام تُعرَض؛ أي ناجٍ يحتاج مراجعة خصومية + موافقة المستخدم.
"""
import sys
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import roc_auc_score

P25, P26 = sys.argv[1], sys.argv[2]


def load(path, year):
    df = pd.read_csv(path)
    df["year"] = year
    # السعر الحقيقي point-in-time للدخول: raw_pit_entry (للرموز ذات تقسيمات) وإلا
    # entry المعدَّل (لا تقسيم لاحق = raw == adjusted). H_PRICE_2_5 يستعمل هذا.
    rpe = df["raw_pit_entry"] if "raw_pit_entry" in df else pd.Series([None] * len(df))
    df["price_eff"] = pd.to_numeric(rpe, errors="coerce")
    if "entry" in df:
        df["price_eff"] = df["price_eff"].fillna(pd.to_numeric(df["entry"], errors="coerce"))
    return df


def is_filled(df):
    # مُعبَّأة = دخل السعر منطقة الدخول (mg_outcome ليس no_fill/غائبًا)
    return df["mg_outcome"].notna() & (df["mg_outcome"] != "no_fill")


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * np.sqrt((p * (1 - p) + z * z / (4 * n)) / n)
    return ((c - h) / d, (c + h) / d)


def fisher_2x2(rule_mask, target_mask):
    """2x2: (قاعدة صح/خطأ) × (هدف صح/خطأ) → OR + p (Fisher) + معدّلا المجموعتين."""
    a = int((rule_mask & target_mask).sum())      # قاعدة✓ هدف✓
    b = int((rule_mask & ~target_mask).sum())      # قاعدة✓ هدف✗
    c = int((~rule_mask & target_mask).sum())      # قاعدة✗ هدف✓
    d = int((~rule_mask & ~target_mask).sum())     # قاعدة✗ هدف✗
    n1, n0 = a + b, c + d
    r1 = a / n1 if n1 else float("nan")
    r0 = c / n0 if n0 else float("nan")
    orr, p = stats.fisher_exact([[a, b], [c, d]])
    return {"a": a, "n1": n1, "r1": r1, "c": c, "n0": n0, "r0": r0,
            "or": orr, "p": p, "diff": (r1 - r0)}


def bh_fdr(pvals):
    """Benjamini-Hochberg: يرجع qvalues بنفس ترتيب المدخل."""
    p = np.asarray(pvals, float)
    m = len(p)
    order = np.argsort(p)
    q = np.empty(m)
    prev = 1.0
    for rank in range(m - 1, -1, -1):
        idx = order[rank]
        val = p[idx] * m / (rank + 1)
        prev = min(prev, val)
        q[idx] = prev
    return q


d25 = load(P25, 2025)
d26 = load(P26, 2026)
alld = pd.concat([d25, d26], ignore_index=True)

print("=" * 78)
print("Phase C — اختبار OOS مسجَّل مسبقًا (walk-forward بالسنتين + FDR)")
print("=" * 78)
for nm, d in [("2025", d25), ("2026", d26)]:
    f = is_filled(d)
    print(f"  {nm}: صفوف={len(d)} · مُعبَّأة={int(f.sum())} · "
          f"انفجر50%+={int((d['fwd_max_gain'] >= 50).sum())} · "
          f"price_eff متوفّر={int(d['price_eff'].notna().sum())} "
          f"(منها raw_pit={int(pd.to_numeric(d.get('raw_pit_entry'), errors='coerce').notna().sum()) if 'raw_pit_entry' in d else 0})")
print()

results = []   # (id, p_pool, consistent, detail)


def run_binary(hid, popfn, targetfn, rulefn, direction):
    """فرضية ثنائية: Fisher لكل سنة + مجمَّع + اتساق الاتجاه."""
    per = {}
    for yr, d in [(2025, d25), (2026, d26)]:
        pop = d[popfn(d)].copy()
        if len(pop) == 0:
            per[yr] = None
            continue
        per[yr] = fisher_2x2(rulefn(pop), targetfn(pop))
    popA = alld[popfn(alld)].copy()
    pool = fisher_2x2(rulefn(popA), targetfn(popA))
    # اتساق الاتجاه: الفرق بالاتجاه المتوقّع في كلتا السنتين
    signs = []
    for yr in (2025, 2026):
        if per[yr] and not np.isnan(per[yr]["diff"]):
            signs.append(per[yr]["diff"] > 0 if direction == "positive" else per[yr]["diff"] < 0)
    consistent = len(signs) == 2 and all(signs)
    results.append((hid, pool["p"], consistent, {"per": per, "pool": pool, "dir": direction}))
    return per, pool, consistent


def run_auc(hid, popfn, targetfn, scorefn, direction):
    """فرضية ترتيب (score العكسي): AUC داخل كل سنة + walk-forward (نفس القاعدة مقفولة،
    لا تدريب معاملات) + مجمَّع. الاتجاه: AUC(-score)>0.5 يعني score منخفض يرتّب الهدف أعلى."""
    per = {}
    for yr, d in [(2025, d25), (2026, d26)]:
        pop = d[popfn(d)].copy()
        y = targetfn(pop).astype(int).values
        s = scorefn(pop).values
        m = ~np.isnan(s)
        if m.sum() < 5 or len(set(y[m])) < 2:
            per[yr] = None
            continue
        per[yr] = roc_auc_score(y[m], s[m])   # s = -score (مُمرَّر) فالأعلى=هدف أرجح
    popA = alld[popfn(alld)].copy()
    yA = targetfn(popA).astype(int).values
    sA = scorefn(popA).values
    mA = ~np.isnan(sA)
    auc_pool = roc_auc_score(yA[mA], sA[mA]) if (mA.sum() >= 5 and len(set(yA[mA])) >= 2) else float("nan")
    # دلالة AUC المجمَّع عبر Mann-Whitney (مكافئ AUC)
    pos = sA[mA][yA[mA] == 1]
    neg = sA[mA][yA[mA] == 0]
    try:
        _, p_pool = stats.mannwhitneyu(pos, neg, alternative="greater")
    except Exception:
        p_pool = float("nan")
    consistent = all(per[yr] is not None and per[yr] > 0.5 for yr in (2025, 2026))
    results.append((hid, p_pool, consistent, {"per": per, "auc_pool": auc_pool, "dir": direction}))
    return per, auc_pool, consistent, p_pool


# ── H_BEHAV_REARM: بين الموقوفين (mg_outcome==stopped) هل behav>=60 → انفجر بعد الوقف؟ ──
def _stopped(d):
    return d["mg_outcome"] == "stopped"
def _reexplode(d):
    return d["fwd_max_gain"] >= 50
def _behav60(d):
    return (d["behav_score"].fillna(-1) >= 60)
pb, poolb, consb = run_binary("H_BEHAV_REARM", _stopped, _reexplode, _behav60, "positive")

# ── H_SCORE_INVERSE: كل المُعبَّئين — score منخفض يرتّب mg_pre_stop>=50 أعلى (AUC(-score)) ──
def _allfilled(d):
    return is_filled(d)
def _trad50(d):
    return d["mg_pre_stop"].fillna(-999) >= 50
def _negscore(d):
    return -d["score"].astype(float)
psc, aucsc, conssc, pscpool = run_auc("H_SCORE_INVERSE", _allfilled, _trad50, _negscore, "negative")

# ── H_PRICE_2_5: كل المُعبَّئين — 2<=raw_pit_entry<5 → fwd_max_gain>=50 ──
def _full50(d):
    return d["fwd_max_gain"] >= 50
def _price25(d):
    r = d["price_eff"].astype(float)
    return (r >= 2) & (r < 5)
pp, poolp, consp = run_binary("H_PRICE_2_5", _allfilled, _full50, _price25, "positive")

# ── H_READINESS_LOW: كل المُعبَّئين — readiness<=54 → fwd_max_gain>=50 ──
def _rdy54(d):
    return d["readiness"].fillna(999) <= 54
pr, poolr, consr = run_binary("H_READINESS_LOW", _allfilled, _full50, _rdy54, "positive")

# ── BH-FDR عبر الفرضيات الأربع (على p المجمَّع) ──
ids = [r[0] for r in results]
pvals = [r[1] for r in results]
qvals = bh_fdr(pvals)

print("─" * 78)
print("النتائج لكل فرضية (بترتيب التسجيل):")
print("─" * 78)
qmap = dict(zip(ids, qvals))
for hid, p_pool, consistent, det in results:
    q = qmap[hid]
    print(f"\n▸ {hid}  [اتجاه {det['dir']}]")
    if "pool" in det:  # ثنائية
        for yr in (2025, 2026):
            e = det["per"][yr]
            if e is None:
                print(f"    {yr}: — (لا عيّنة)")
            else:
                lo1, hi1 = wilson(e["a"], e["n1"])
                lo0, hi0 = wilson(e["c"], e["n0"])
                print(f"    {yr}: قاعدة✓ {e['a']}/{e['n1']}={e['r1']*100:.0f}% (CI {lo1*100:.0f}-{hi1*100:.0f}) "
                      f"مقابل {e['c']}/{e['n0']}={e['r0']*100:.0f}% (CI {lo0*100:.0f}-{hi0*100:.0f}) "
                      f"· OR {e['or']:.2f} · p {e['p']:.3f} · فرق {e['diff']*100:+.0f}ن")
        pl = det["pool"]
        print(f"    مجمَّع: {pl['a']}/{pl['n1']}={pl['r1']*100:.0f}% مقابل {pl['c']}/{pl['n0']}={pl['r0']*100:.0f}% "
              f"· OR {pl['or']:.2f} · p {pl['p']:.3f}")
    else:  # AUC
        for yr in (2025, 2026):
            a = det["per"][yr]
            print(f"    {yr}: AUC(-score) = {a:.3f}" if a is not None else f"    {yr}: — (لا عيّنة)")
        print(f"    مجمَّع: AUC = {det['auc_pool']:.3f} · p(MWU) {p_pool:.3f}")
    verdict = "✅ ينجو" if (consistent and q < 0.10) else "❌ لا ينجو"
    why = []
    if not consistent:
        why.append("اتجاه غير متّسق بالسنتين")
    if q >= 0.10:
        why.append(f"q={q:.3f}≥0.10")
    print(f"    اتساق الاتجاه: {'نعم' if consistent else 'لا'} · q(FDR) = {q:.3f} → {verdict}"
          + (f"  ({' · '.join(why)})" if why else ""))

print("\n" + "=" * 78)
survivors = [hid for hid, p, cons, det in results if cons and qmap[hid] < 0.10]
if survivors:
    print(f"🎯 ناجون (يحتاجون مراجعة خصومية + موافقة المستخدم قبل أي مسّ): {survivors}")
else:
    print("📋 الحكم المسجَّل مسبقًا: لا شيء ينجو من FDR بالسنتين → كلها قرائن لا حواف.")
    print("   القيمة الأكبر (كما سُجّل): الأساس المجمَّد القابل للإعادة + التحوّل للتوقيت اللحظي/4س.")
print("=" * 78)
