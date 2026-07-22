"""🥇 اختبار تمييزي مسجَّل مسبقًا: هل توليفة فيصل «الذهبية» (IMG_0076) تتنبّأ بالانفجار ≥100%؟

اختبار على **السوق كامل** من اللقطة المجمَّدة (بتخطّي بوابات البوت)، على العيّنة الصح
(المنفجرون مقابل لا). المعايير القابلة للقياس point-in-time: مقسّم عكسي (بديل الفلوت) ·
**المتوسط الأسّي EMA 30/50 هابط** (فيصل «متوسط الأسّي 30-50 يوم» — تصحيح 2026-07-22 من
صور المستخدم؛ كان يُفهم خطأً كتذبذب يومي) · قاعدة محفوظة 3ج. المعيار في `faisal_combo_prereg.md`.

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
# ⚠️ تصحيح 2026-07-22 (صور IMG_0091/0094/0095/0096 — بحث المستخدم from:kisar_ 30/50):
# «متوسط حركة 30<50» = **المتوسط الأسّي EMA 30 و 50** (فيصل: «متوسط الأسّي 30-50 يوم» ·
# «جميع المتوسطات … 30-50» · «مقسّم هابط متوسط 20<30<50»)، **لا** متوسط الحركة اليومية.
# السهم بعد حركته الأسّية الهابطة (السعر تحت EMA20<EMA30<EMA50 = اصطفاف هابط) عند القاع.
EMA_FAST, EMA_MID, EMA_SLOW = 20, 30, 50   # المتوسطات الأسّية (فيصل يذكر 20/30/50)
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


def ema_bear_stack(close, price):
    """المتوسط الأسّي «30<50» (فيصل: «متوسط الأسّي 30-50 يوم» · «مقسّم هابط متوسط 20<30<50»):
    اصطفاف أسّي هابط EMA20 ≤ EMA30 ≤ EMA50 **والسعر تحت EMA20** = السهم أنهى حركته الأسّية
    الهابطة وعند القاع (يمهّد للمضاعفة). يرجّع (stack_bool, gap50) حيث gap50 = price/EMA50−1
    (للتفصيل الثانوي). (False, nan) عند قصر التاريخ (<EMA_SLOW). نقيّة فاشلة-آمنة."""
    c = np.asarray(close, float)
    if len(c) < EMA_SLOW:
        return False, float("nan")
    s = pd.Series(c)
    e20 = float(s.ewm(span=EMA_FAST, adjust=False).mean().iloc[-1])
    e30 = float(s.ewm(span=EMA_MID, adjust=False).mean().iloc[-1])
    e50 = float(s.ewm(span=EMA_SLOW, adjust=False).mean().iloc[-1])
    stack = bool(price <= e20 <= e30 <= e50)
    gap = (price / e50 - 1.0) if e50 > 0 else float("nan")
    return stack, gap


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
    dec = np.linspace(100.0, 10.0, 80)   # سلسلة هابطة (حركة أسّية هابطة)
    st, gp = ema_bear_stack(dec, dec[-1])
    chk("ema: هابطة → اصطفاف أسّي هابط EMA20≤30≤50 والسعر تحت (True)", st is True)
    chk("ema: هابطة → السعر تحت EMA50 (gap سالب)", gp < 0)
    inc = np.linspace(10.0, 100.0, 80)   # سلسلة صاعدة
    chk("ema: صاعدة → ليست اصطفافًا هابطًا (False)",
        ema_bear_stack(inc, inc[-1])[0] is False)
    chk("ema: تاريخ قصير (<50) → False",
        ema_bear_stack(np.arange(10.0), 5.0)[0] is False)
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

    # الأعمدة: year, is_rs, ema_ok, base_ok, spike_ok, combo3, exploded, gap50
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
            ema_ok, gap = ema_bear_stack(close[:i + 1], c0)
            base_ok = base_held(high[:i + 1], low[:i + 1])
            best_spike, _ = S.spike_info(close[:i + 1], exclude_last=0)
            spike_ok = best_spike >= PRIOR_SPIKE_MIN
            # التوليفة الأساسية = معايير IMG_0076 الثلاثة القابلة للقياس (مقسّم + أسّي30/50
            # هابط + قاعدة3ج). «انفجار سابق» يُعرَض كميزة منفصلة (ليس ضمن قائمة IMG_0076).
            combo3 = is_rs and ema_ok and base_ok
            fwd = close[i + 1:i + 1 + FWD]
            exploded = (len(fwd) > 0 and
                        (float(np.nanmax(fwd)) / c0 - 1.0) * 100.0 >= EXPLODE_PCT)
            rows.append((ts.year, is_rs, ema_ok, base_ok, spike_ok,
                         combo3, exploded, gap))

    if not rows:
        print("⚠️ صفر نقاط تقييم — تحقّق من تغطية اللقطة للسنوات.")
        return 1
    arr = np.array([(r[0], r[1], r[2], r[3], r[4], r[5], r[6]) for r in rows], float)
    gaps = np.array([r[7] for r in rows], float)
    N = len(arr)
    yr, is_rs, ema_ok, bs_ok, sp_ok, combo, expl = (arr[:, k] for k in range(7))

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
    feats = [("مقسّم عكسي (365ي)", is_rs), ("أسّي 30/50 هابط (السعر تحت 20≤30≤50)", ema_ok),
             ("قاعدة محفوظة 3ج", bs_ok), ("انفجار سابق ≥100% (خارج IMG_0076)", sp_ok)]
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
    out.append("\n## 🥇 التوليفة (معايير IMG_0076 الثلاثة: مقسّم + أسّي30/50-هابط + قاعدة3ج)\n")
    out.append(f"- **المطابق:** {cn} نقطة · انفجر {ck} · **{cp*100:.2f}%** "
               f"Wilson [{clo*100:.2f}, {chi*100:.2f}] · رفع {lift:.2f}× الأساس")
    out.append(f"- **غير المطابق:** {nn} نقطة · {np_*100:.2f}% "
               f"Wilson [{nlo*100:.2f}, {nhi*100:.2f}]")
    # التوليفة + انفجار سابق (معلومة ثانوية)
    c4 = cm & sp_ok.astype(bool)
    f4n, f4k, f4p, f4lo, f4hi = rate(c4)
    out.append(f"- **+ انفجار سابق ≥100%:** {f4n} نقطة · {f4p*100:.2f}% "
               f"Wilson [{f4lo*100:.2f}, {f4hi*100:.2f}] · رفع "
               f"{(f4p/bp) if bp>0 else float('nan'):.2f}×")

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

    # تفصيل فجوة السعر عن EMA50 (secondary — هل الأعمق تحت الأسّي ينفجر أكثر؟)
    out.append("\n## (secondary) الانفجار حسب فجوة السعر عن EMA50 (price/EMA50−1)\n")
    out.append("| الفجوة عن EMA50 | N | معدّل الانفجار |")
    out.append("|---|--:|--:|")
    fin = np.isfinite(gaps)
    for a, b in [(-1.0, -.5), (-.5, -.3), (-.3, -.15), (-.15, 0), (0, .2), (.2, 9)]:
        m = fin & (gaps >= a) & (gaps < b)
        n, k, p, *_ = rate(m)
        if n:
            out.append(f"| [{a:+.0%}, {b:+.0%}) | {n} | {p*100:.2f}% |")

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
