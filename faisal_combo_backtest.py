"""🥇 اختبار تمييزي مسجَّل مسبقًا: هل توليفة فيصل «الذهبية» (IMG_0076) تتنبّأ بالانفجار ≥100%؟

اختبار على **السوق كامل** من اللقطة المجمَّدة (بتخطّي بوابات البوت)، على العيّنة الصح
(المنفجرون مقابل لا). المعايير القابلة للقياس point-in-time: مقسّم عكسي (بديل الفلوت) ·
حركة 30-50% · قاعدة محفوظة 3 جلسات · انفجار سابق ≥100%. المعيار في `faisal_combo_prereg.md`.

**بحث/باكتيست فقط — صفر مسّ لـSuper_stock.py (لا جذور · لا LOGIC_VERSION).** يعيد استخدام
`load_frozen_dataset` و`spike_info` فقط. بلا تسريب: الميزات من ≤t، الناتج من (t, t+FWD].

التشغيل: `BT_FROZEN_PATH=frozen_backtest.pkl.gz python faisal_combo_backtest.py`
اختبار ذاتي (بلا لقطة): `python faisal_combo_backtest.py --selftest`
"""
import os
import sys
import math
import numpy as np
import pandas as pd

# ── عتبات مسجَّلة مسبقًا (faisal_combo_prereg.md) — لا تتغيّر بعد النتائج ──
def _env(name, default):
    """يقرأ env؛ الفارغ/التالف → الافتراضي (workflow يمرّر "" عند ترك المدخل)."""
    v = (os.environ.get(name) or "").strip()
    try:
        return type(default)(v) if v else default
    except (TypeError, ValueError):
        return default


FWD = _env("FC_FWD_DAYS", 60)              # نافذة أمامية (جلسات)
EXPLODE_PCT = _env("FC_EXPLODE_PCT", 100.0)  # الانفجار = صعود ≥ %
MOVE_LO, MOVE_HI = 0.30, 0.50      # حركة 30-50%
MOVE_WIN = 15                      # نافذة متوسط الحركة (جلسات)
BASE_HOLD_WIN = 3                  # حافظ ع قاعه 3 جلسات
BASE_HOLD_MAX = 0.15               # مدى آخر 3ج ≤15% = محفوظ
RSPLIT_LOOKBACK = 365              # مقسّم عكسي خلال سنة (أيام تقويم)
PRIOR_SPIKE_MIN = 100.0            # انفجار سابق ≥100% (M3 مثالي)
MIN_HIST = 60                      # أدنى تاريخ خلفي (جلسات)
YEARS = [2023, 2024, 2025]
Z = 1.96


def wilson(k, n, z=Z):
    """فاصل Wilson 95% لنسبة k/n → (p, lo, hi). فاشل-آمن."""
    if n <= 0:
        return (0.0, 0.0, 0.0)
    p = k / n
    d = 1.0 + z * z / n
    c = p + z * z / (2 * n)
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (p, (c - m) / d, (c + m) / d)


def _ts(x):
    t = pd.Timestamp(x)
    return t.tz_localize(None) if getattr(t, "tz", None) is not None else t


def rsplit_recent(splits, asof, lookback=RSPLIT_LOOKBACK):
    """هل وقع تقسيم **عكسي** (نسبة <1) خلال `lookback` يومًا قبل asof؟ (بديل الفلوت الصغير).
    نقيّة فاشلة-آمنة. splits = Series(نسبة، فهرسها التاريخ) أو قائمة أزواج."""
    if splits is None:
        return False
    try:
        a = _ts(asof)
        lo = a - pd.Timedelta(days=lookback)
        it = splits.items() if hasattr(splits, "items") else splits
        for d, r in it:
            dd = _ts(d)
            if lo <= dd <= a and r and float(r) < 1.0:
                return True
    except Exception:
        return False
    return False


def avg_move(high, low, close, win=MOVE_WIN):
    """متوسط (high−low)/close لآخر `win` جلسة. None عند التعذّر."""
    h = np.asarray(high[-win:], float)
    l = np.asarray(low[-win:], float)
    c = np.asarray(close[-win:], float)
    if len(c) == 0:
        return None
    m = (h - l) / np.where(c > 0, c, np.nan)
    v = np.nanmean(m)
    return float(v) if np.isfinite(v) else None


def base_held(high, low, win=BASE_HOLD_WIN, maxr=BASE_HOLD_MAX):
    """آخر `win` جلسة: المدى (أعلى/أدنى−1) ≤ maxr = القاعدة محفوظة."""
    h = np.asarray(high[-win:], float)
    l = np.asarray(low[-win:], float)
    if len(l) == 0:
        return False
    hi = float(h.max())
    lo = float(l.min())
    if lo <= 0:
        return False
    return (hi / lo - 1.0) <= maxr


def _selftest():
    """اختبار ذاتي للدوال النقيّة (بلا لقطة/شبكة)."""
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("✅" if cond else "❌") + " " + name)

    p, lo, hi = wilson(5, 10)
    chk("wilson 5/10 → p=0.5", abs(p - 0.5) < 1e-9 and lo < 0.5 < hi)
    chk("wilson 0/0 آمن", wilson(0, 0) == (0.0, 0.0, 0.0))
    sp = pd.Series([0.1], index=[pd.Timestamp("2025-03-10")])   # عكسي 1:10
    chk("rsplit: عكسي خلال 365ي → True",
        rsplit_recent(sp, "2025-06-01") is True)
    chk("rsplit: خارج النافذة (قبل >365ي) → False",
        rsplit_recent(sp, "2026-06-01") is False)
    chk("rsplit: تقسيم بعد asof (تسريب) → False",
        rsplit_recent(sp, "2025-01-01") is False)
    chk("rsplit: تقسيم أمامي (نسبة>1) → False",
        rsplit_recent(pd.Series([2.0], index=[pd.Timestamp("2025-03-10")]), "2025-06-01") is False)
    chk("rsplit: بلا splits → False", rsplit_recent(None, "2025-06-01") is False)
    hi_a = np.array([1.40] * 15)
    lo_a = np.array([1.00] * 15)
    cl_a = np.array([1.00] * 15)
    mv = avg_move(hi_a, lo_a, cl_a)
    chk("avg_move: (1.40−1.00)/1.00=0.40", abs(mv - 0.40) < 1e-9)
    chk("avg_move 0.40 ضمن البند [0.30,0.50]", MOVE_LO <= mv <= MOVE_HI)
    chk("avg_move 0.20 خارج البند", not (MOVE_LO <= (avg_move(
        np.array([1.20] * 15), lo_a, cl_a)) <= MOVE_HI))
    chk("base_held: 3ج مدى 0% → محفوظ",
        base_held(np.array([2.0, 2.0, 2.0]), np.array([2.0, 2.0, 2.0])) is True)
    chk("base_held: 3ج مدى 50% → غير محفوظ",
        base_held(np.array([3.0, 2.5, 2.0]), np.array([3.0, 2.5, 2.0])) is False)
    print("\n" + ("✅✅ الاختبار الذاتي نجح" if ok else "❌ فشل الاختبار الذاتي"))
    return ok


def run():
    import Super_stock as S
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        print("⚠️ لا BT_FROZEN_PATH — مرّر مسار اللقطة المجمَّدة. (للاختبار الذاتي: --selftest)")
        return 2
    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        print(f"⚠️ تعذّر تحميل اللقطة {path}")
        return 2
    splits_map = splits_map or {}
    print(f"🥇 توليفة فيصل — لقطة {path} · as-of {asof} · {len(hist)} رمز · "
          f"نافذة أمامية {FWD}ج · انفجار ≥{EXPLODE_PCT:g}%")

    # الأعمدة: year, is_rs, move_ok, base_ok, spike_ok, combo, exploded, move_val
    rows = []
    n_sym_used = 0
    for sym, df in hist.items():
        if df is None or len(df) < MIN_HIST + FWD + 2:
            continue
        try:
            idx = df.index
            close = df["Close"].to_numpy(float)
            high = df["High"].to_numpy(float)
            low = df["Low"].to_numpy(float)
        except Exception:
            continue
        sp = splits_map.get(sym)
        n_sym_used += 1
        seen = set()
        hi_lim = len(df) - FWD - 1
        for i in range(MIN_HIST, hi_lim):
            ts = _ts(idx[i])
            ym = (ts.year, ts.month)
            if ym in seen:
                continue
            seen.add(ym)
            if ts.year not in YEARS:
                continue
            c0 = close[i]
            if not (c0 > 0):
                continue
            is_rs = rsplit_recent(sp, ts)
            mv = avg_move(high[:i + 1], low[:i + 1], close[:i + 1])
            move_ok = (mv is not None) and (MOVE_LO <= mv <= MOVE_HI)
            base_ok = base_held(high[:i + 1], low[:i + 1])
            best_spike, _ = S.spike_info(close[:i + 1], exclude_last=0)
            spike_ok = best_spike >= PRIOR_SPIKE_MIN
            combo = is_rs and move_ok and base_ok and spike_ok
            fwd = close[i + 1:i + 1 + FWD]
            exploded = (len(fwd) > 0 and
                        (float(np.nanmax(fwd)) / c0 - 1.0) * 100.0 >= EXPLODE_PCT)
            rows.append((ts.year, is_rs, move_ok, base_ok, spike_ok,
                         combo, exploded, mv if mv is not None else np.nan))

    if not rows:
        print("⚠️ صفر نقاط تقييم — تحقّق من تغطية اللقطة للسنوات.")
        return 1
    arr = np.array([(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows], float)
    moves = np.array([r[7] for r in rows], float)
    N = len(arr)
    yr, is_rs, mv_ok, bs_ok, sp_ok, combo, expl = (arr[:, k] for k in range(7))

    def rate(mask):
        n = int(mask.sum())
        k = int(expl[mask].sum()) if n else 0
        p, lo, hi = wilson(k, n)
        return n, k, p, lo, hi

    out = []
    out.append(f"# 🥇 نتيجة توليفة فيصل «الذهبية» — اختبار تمييزي (السوق كامل)\n")
    out.append(f"> اللقطة `{path}` · as-of {asof} · {n_sym_used} رمز مُستخدَم · "
               f"**{N} نقطة تقييم شهرية** · نافذة {FWD}ج · انفجار ≥{EXPLODE_PCT:g}%\n")
    bn, bk, bp, blo, bhi = rate(np.ones(N, bool))
    out.append(f"**معدّل الأساس (كل النقاط):** {bp*100:.2f}% ({bk}/{bn}) · "
               f"Wilson [{blo*100:.2f}, {bhi*100:.2f}]\n")

    # الميزات المفردة
    out.append("## الميزات المفردة (معدّل الانفجار | الميزة مقابل الأساس)\n")
    out.append("| الميزة | N | انفجر | المعدّل | Wilson95 | الرفع×الأساس |")
    out.append("|---|--:|--:|--:|---|--:|")
    feats = [("مقسّم عكسي (365ي)", is_rs), ("حركة 30-50%", mv_ok),
             ("قاعدة محفوظة 3ج", bs_ok), ("انفجار سابق ≥100%", sp_ok)]
    for name, m in feats:
        n, k, p, lo, hi = rate(m.astype(bool))
        lift = (p / bp) if bp > 0 else float("nan")
        out.append(f"| {name} | {n} | {k} | {p*100:.2f}% | "
                   f"[{lo*100:.2f}, {hi*100:.2f}] | {lift:.2f}× |")

    # التوليفة الكاملة
    cm = combo.astype(bool)
    cn, ck, cp, clo, chi = rate(cm)
    nn, nk, np_, nlo, nhi = rate(~cm)
    lift = (cp / bp) if bp > 0 else float("nan")
    out.append("\n## 🥇 التوليفة الكاملة (الأربعة معًا)\n")
    out.append(f"- **المطابق:** {cn} نقطة · انفجر {ck} · **{cp*100:.2f}%** "
               f"Wilson [{clo*100:.2f}, {chi*100:.2f}] · رفع {lift:.2f}× الأساس")
    out.append(f"- **غير المطابق:** {nn} نقطة · {np_*100:.2f}% "
               f"Wilson [{nlo*100:.2f}, {nhi*100:.2f}]")

    # لكل سنة (LOYO)
    out.append("\n## الاتّساق عبر السنوات (LOYO — التوليفة)\n")
    out.append("| السنة | N مطابق | انفجر | معدّل المطابق | معدّل الأساس(السنة) | الرفع |")
    out.append("|---|--:|--:|--:|--:|--:|")
    yr_signs = []
    for y in YEARS:
        ym = (yr == y)
        b_n, b_k, b_p, *_ = rate(ym)
        c_mask = ym & cm
        c_n, c_k, c_p, c_lo, c_hi = rate(c_mask)
        lf = (c_p / b_p) if b_p > 0 else float("nan")
        yr_signs.append((c_n, c_p, b_p))
        out.append(f"| {y} | {c_n} | {c_k} | {c_p*100:.2f}% | {b_p*100:.2f}% | {lf:.2f}× |")

    # تفصيل عشور الحركة (secondary — نتعلّم الشكل)
    out.append("\n## (secondary) الانفجار حسب متوسط الحركة (نتعلّم البند الصحيح)\n")
    out.append("| شريحة الحركة | N | معدّل الانفجار |")
    out.append("|---|--:|--:|")
    fin = np.isfinite(moves)
    for a, b in [(0, .10), (.10, .20), (.20, .30), (.30, .50), (.50, 1.0), (1.0, 99)]:
        m = fin & (moves >= a) & (moves < b)
        n, k, p, *_ = rate(m)
        if n:
            out.append(f"| [{a:.0%}, {b:.0%}) | {n} | {p*100:.2f}% |")

    # الحكم المسبق
    passes = []
    passes.append(("N≥30", cn >= 30))
    passes.append(("Wilson المطابق > سقف الأساس", clo > bhi))
    consistent = all((cp_ > bp_) for (_, cp_, bp_) in yr_signs if bp_ >= 0)
    passes.append(("موجب في السنوات الثلاث (LOYO)", consistent))
    # Bonferroni: 5 اختبارات → z أعلى؛ نتحقّق أن أرضية المطابق (bonf) > الأساس
    zb = 2.576  # ~99.5% ≈ Bonferroni لـ5 اختبارات عند 95%
    _, cblo, _ = wilson(ck, cn, z=zb)
    passes.append(("يصمد بعد Bonferroni (أرضية 99.5% > الأساس)", cblo > bp))
    verdict = all(v for _, v in passes)
    out.append("\n## ⚖️ الحكم مقابل المعيار المسجَّل مسبقًا\n")
    for name, v in passes:
        out.append(f"- {'✅' if v else '❌'} {name}")
    out.append(f"\n### النتيجة: **{'يُعتمد — إشارة اختيار حقيقية' if verdict else 'نفي — لا يبلغ العتبة'}**")
    if not verdict:
        out.append("الحافة = التوقيت لا الاختيار (اتّساقًا مع C3/الرابط-المشترك/M2/M4).")

    report = "\n".join(out)
    print("\n" + report)
    try:
        with open("faisal_combo_result.md", "w", encoding="utf-8") as fh:
            fh.write(report + "\n")
    except Exception:
        pass
    # تلغرام (اختياري — أول 12 سطر)
    try:
        S.send_telegram("🥇 <b>توليفة فيصل — نتيجة الاختبار التمييزي</b>\n"
                        + f"المطابق {cn}: {cp*100:.1f}% · الأساس {bp*100:.2f}% · رفع {lift:.2f}×\n"
                        + ("✅ يُعتمد" if verdict else "❌ نفي (دون العتبة)"))
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        sys.exit(0 if _selftest() else 1)
    sys.exit(run())
