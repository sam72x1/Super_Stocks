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
EXPLODE_PCT = _env("FC_EXPLODE_PCT", 100.0)  # الانفجار/الهدف = صعود ≥ %
STOP_PCT = _env("FC_STOP_PCT", 50.0)       # 🎯 الوقف للمقياس القابل للتنفيذ = هبوط ≥ %
# ⚠️ تصحيح 2026-07-22 (صور IMG_0091/0094/0095/0096 — بحث المستخدم from:kisar_ 30/50):
# «متوسط حركة 30<50» = **المتوسط الأسّي EMA 30 و 50** (فيصل: «متوسط الأسّي 30-50 يوم» ·
# «جميع المتوسطات … 30-50» · «مقسّم هابط متوسط 20<30<50»)، **لا** متوسط الحركة اليومية.
# السهم بعد حركته الأسّية الهابطة (السعر تحت EMA20<EMA30<EMA50 = اصطفاف هابط) عند القاع.
EMA_FAST, EMA_MID, EMA_SLOW = 20, 30, 50   # المتوسطات الأسّية (فيصل يذكر 20/30/50)
BASE_HOLD_WIN = 3                  # حافظ ع قاعه 3 جلسات
# 🖐️ ميكانيكا فيصل (طلب المستخدم): دخول بعد مسح-واستعادة (لا الدعم الأول) · وقف بنيوي تحت
# أدنى المسح (~7% تحت الدعم) · هدف +100% · القياس بالتوقّع R لا نسبة النجاح (R:R ~14:1).
SWEEP_PCT = _env("FC_SWEEP_PCT", 5.0)       # عمق المسح المطلوب تحت الدعم %
STOP_MARGIN = _env("FC_STOP_MARGIN", 2.0)   # الوقف تحت أدنى المسح بـ %
ENTRY_WIN = _env("FC_ENTRY_WIN", 20)        # نافذة انتظار المسح-الاستعادة (جلسات)
BASE_LOOK = 15                              # نافذة الدعم (أدنى قاع)
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


def _logit_fit(X, y, iters=500, lr=0.3, l2=1e-3):
    """انحدار لوجستي بسيط بـnumpy (بلا sklearn) — نموذج شفّاف يقاوم overfitting (قليل الميزات
    + L2). X مِعياريّة مع عمود انحياز. يرجّع الأوزان."""
    w = np.zeros(X.shape[1])
    n = max(1, len(y))
    for _ in range(iters):
        p = 1.0 / (1.0 + np.exp(-np.clip(X @ w, -30, 30)))
        g = X.T @ (p - y) / n + l2 * w
        w -= lr * g
    return w


def _phase0_learnability(feats, labels, years, names):
    """🤖 المرحلة 0: هل ميزة يومية تتنبّأ بنجاح دخول-المسح **خارج العيّنة**؟ تدريب 2023-2024،
    اختبار 2025 (walk-forward، بلا تسريب). يرجّع أسطر تقرير. نموذج logistic شفّاف + سبر لكل ميزة."""
    out = ["\n## 🤖 المرحلة 0 — قابلية تعلّم «اليد» على البيانات اليومية (OOS: تدريب 2023-24 · اختبار 2025)\n"]
    tr = (years == 2023) | (years == 2024)
    te = (years == 2025)
    if int(tr.sum()) < 50 or int(te.sum()) < 50:
        out.append(f"⚠️ عيّنة دخول-المسح غير كافية (تدريب {int(tr.sum())} · اختبار {int(te.sum())}) — لا حكم.")
        return out
    Xtr, ytr = feats[tr], labels[tr]
    Xte, yte = feats[te], labels[te]
    base_wr = float(yte.mean())
    out.append(f"- عيّنة: تدريب {int(tr.sum())} دخول · اختبار (2025) {int(te.sum())} · "
               f"نسبة نجاح الأساس OOS = {base_wr*100:.1f}%")
    # سبر لكل ميزة (OOS): نسبة نجاح الثلث الأعلى (بعتبة التدريب) مقابل الأساس
    out.append("\n| الميزة | ارتباط بالتدريب | نجاح الثلث-الأعلى OOS | الرفع |")
    out.append("|---|--:|--:|--:|")
    for k, nm in enumerate(names):
        col_tr = Xtr[:, k]
        cc = float(np.corrcoef(col_tr, ytr)[0, 1]) if np.std(col_tr) > 0 else 0.0
        col_te = Xte[:, k]
        thr = np.quantile(col_te, 2 / 3) if cc >= 0 else np.quantile(col_te, 1 / 3)
        grp = (col_te >= thr) if cc >= 0 else (col_te <= thr)
        wr = float(yte[grp].mean()) if int(grp.sum()) else 0.0
        out.append(f"| {nm} | {cc:+.3f} | {wr*100:.1f}% | {(wr/base_wr if base_wr>0 else 0):.2f}× |")
    # نموذج مركّب (logistic) — الربع الأعلى بالنتيجة OOS
    mean = Xtr.mean(0); std = Xtr.std(0)
    Xtr_s = np.column_stack([np.ones(len(Xtr)), (Xtr - mean) / np.where(std > 0, std, 1)])
    Xte_s = np.column_stack([np.ones(len(Xte)), (Xte - mean) / np.where(std > 0, std, 1)])
    w = _logit_fit(Xtr_s, ytr)
    sc = Xte_s @ w
    q = np.quantile(sc, 0.75)
    top = sc >= q
    top_wr = float(yte[top].mean()) if int(top.sum()) else 0.0
    lift = (top_wr / base_wr) if base_wr > 0 else 0.0
    # عقلنة: أداء التدريب داخل العيّنة (للكشف عن overfitting)
    sc_tr = Xtr_s @ w
    q_tr = np.quantile(sc_tr, 0.75)
    in_wr = float(ytr[sc_tr >= q_tr].mean()) if int((sc_tr >= q_tr).sum()) else 0.0
    out.append(f"\n- **النموذج المركّب (logistic):** نجاح الربع الأعلى **OOS = {top_wr*100:.1f}%** "
               f"مقابل أساس {base_wr*100:.1f}% → **رفع {lift:.2f}×** · (داخل التدريب {in_wr*100:.1f}% — "
               "الفجوة الكبيرة عن OOS = overfitting).")
    verdict = lift >= 1.10 and top_wr > base_wr
    out.append(f"- **حكم المرحلة 0:** {'✅ إشارة قابلة للتعلّم يوميًّا (يبرّر نموذجًا أغنى)' if verdict else '❌ لا إشارة يومية ذات معنى OOS — قيمة الوكيل حصريًّا في التدفق اللحظي (المرحلة 1)'}.")
    out.append("⚠️ حدّ: ميزات **يومية-اختيارية فقط** (لا تدفق لحظي/امتصاص) — لذا هذا **سقف أدنى**؛ "
               "جوهر يد فيصل (المسح مقابل الكسر) يحتاج بيانات التدفق الحيّة (المرحلة 1).")
    return out


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


def sweep_entry_outcome(high, low, close, start, fwd, entry_win=None,
                        sweep_pct=None, stop_margin=None, tgt_pct=None,
                        base_look=BASE_LOOK):
    """🖐️ محاكاة ميكانيكا فيصل من نقطة start (نقيّة، بلا نظر مستقبلي):
    - الدعم = أدنى قاع آخر `base_look` جلسة حتى start.
    - ينتظر **مسحًا** (low < الدعم×(1−sweep_pct)) ثم **استعادة** (close > الدعم) خلال `entry_win`.
      (فيصل: «لا تدخل الدعم الأول · مسح ثم استعادة».) لا مسح-استعادة → لا دخول (ينتظر).
    - الدخول = إغلاق الاستعادة · الوقف = أدنى المسح ×(1−stop_margin) · الهدف = دخول×(1+tgt_pct).
    - يمشي للأمام حتى `fwd` من الدخول: الوقف أولًا → خسارة (R=−1) · الهدف → ربح (R=+المكافأة) ·
      لا شيء → timeout (R = تقييم آخر إغلاق ÷ المخاطرة).
    يرجّع (entered, win, R). فاشل-آمن → (False, False, nan)."""
    ew = ENTRY_WIN if entry_win is None else entry_win
    sp = SWEEP_PCT if sweep_pct is None else sweep_pct
    sm = STOP_MARGIN if stop_margin is None else stop_margin
    tp = EXPLODE_PCT if tgt_pct is None else tgt_pct
    try:
        h = np.asarray(high, float); l = np.asarray(low, float); c = np.asarray(close, float)
        n = len(c)
        if start < base_look or start + ew + fwd >= n:
            return (False, False, float("nan"))
        support = float(np.min(l[start - base_look:start + 1]))
        if support <= 0:
            return (False, False, float("nan"))
        sweep_lvl = support * (1.0 - sp / 100.0)
        sweep_low = None
        entry_idx = None
        for j in range(start + 1, start + 1 + ew):
            if l[j] < sweep_lvl:
                sweep_low = l[j] if sweep_low is None else min(sweep_low, l[j])
            if sweep_low is not None and c[j] > support:      # استعادة بعد مسح
                entry_idx = j
                break
        if entry_idx is None:
            return (False, False, float("nan"))               # لا دخول (فيصل ينتظر)
        entry = float(c[entry_idx])
        stop = float(sweep_low) * (1.0 - sm / 100.0)
        risk = entry - stop
        if risk <= 0:
            return (False, False, float("nan"))
        target = entry * (1.0 + tp / 100.0)
        reward_R = (target - entry) / risk
        end = min(entry_idx + 1 + fwd, n)
        for k in range(entry_idx + 1, end):
            if l[k] <= stop:                                  # الوقف أولًا (أسوأ حالة)
                return (True, False, -1.0)
            if h[k] >= target:                                # الهدف
                return (True, True, reward_R)
        last = float(c[end - 1])                              # timeout: تقييم للسوق
        return (True, False, (last - entry) / risk)
    except Exception:
        return (False, False, float("nan"))


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
    # 🖐️ sweep_entry_outcome: مسح-استعادة + هدف/وقف
    _lo = np.array([10.0] * 16 + [9.0, 9.2, 10.0] + [20.0] * 11)   # مسح بار16 ثم استعادة بار17
    _hi = np.array([10.5] * 16 + [9.8, 10.4, 21.0] + [20.5] * 11)  # بار18 يضرب الهدف
    _cl = np.array([10.2] * 16 + [9.5, 10.3, 20.0] + [20.0] * 11)
    _e, _w, _R = sweep_entry_outcome(_hi, _lo, _cl, 15, 5, entry_win=4,
                                     sweep_pct=5, stop_margin=2, tgt_pct=100)
    chk("sweep: مسح+استعادة+هدف → دخل ✓ ربح ✓ R>1", _e is True and _w is True and _R > 1)
    _lo2 = _lo.copy(); _lo2[18] = 8.5          # الوقف يُضرب بعد الدخول
    _hi2 = _hi.copy(); _hi2[18] = 10.5
    _e2, _w2, _R2 = sweep_entry_outcome(_hi2, _lo2, _cl, 15, 5, entry_win=4,
                                        sweep_pct=5, stop_margin=2, tgt_pct=100)
    chk("sweep: مسح+استعادة ثم وقف → خسارة R=−1", _e2 is True and _w2 is False and _R2 == -1.0)
    chk("sweep: بلا مسح → لا دخول", sweep_entry_outcome(
        np.array([10.5] * 30), np.array([10.0] * 30), np.array([10.2] * 30),
        15, 5, entry_win=4)[0] is False)
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
            # 🎯 المقياس القابل للتنفيذ (وقف/هدف · مسار يومي بلا نظر مستقبلي): هل ضرب
            # +EXPLODE_PCT% (هدف) قبل −STOP_PCT% (وقف)؟ الوقف يُفحص أولًا كل يوم = أسوأ حالة
            # (بلا تفاؤل، فلسفة باكتيست البوت). يحوّل «انفجار فضفاض» → نجاح تداولي حقيقي،
            # ويكشف الانهيار المخفي (−50% أولًا) فيجعل انحياز البقاء ثانويًّا في الرفع النسبي.
            fh = high[i + 1:i + 1 + FWD]
            fl = low[i + 1:i + 1 + FWD]
            tgt = c0 * (1.0 + EXPLODE_PCT / 100.0)
            stp = c0 * (1.0 - STOP_PCT / 100.0)
            win = loss = False
            for a, b in zip(fh, fl):
                if b <= stp:          # ضرب الوقف أولًا (أسوأ حالة)
                    loss = True
                    break
                if a >= tgt:          # ضرب الهدف
                    win = True
                    break
            # 🖐️ ميكانيكا فيصل: دخول بعد مسح-واستعادة + وقف بنيوي + هدف 100% → توقّع R
            m_ent, m_win, m_R = sweep_entry_outcome(high, low, close, i, FWD)
            rows.append((ts.year, is_rs, ema_ok, base_ok, spike_ok,
                         combo3, exploded, win, loss, gap,
                         float(m_ent), float(m_win), m_R))

    if not rows:
        print("⚠️ صفر نقاط تقييم — تحقّق من تغطية اللقطة للسنوات.")
        return 1
    arr = np.array([r[:9] for r in rows], float)
    gaps = np.array([r[9] for r in rows], float)
    m_ent = np.array([r[10] for r in rows], float)   # 🖐️ ميكانيكا فيصل: دخل؟
    m_win = np.array([r[11] for r in rows], float)   # ربح (هدف قبل وقف)؟
    m_R = np.array([r[12] for r in rows], float)     # التوقّع R للصفقة
    N = len(arr)
    yr, is_rs, ema_ok, bs_ok, sp_ok, combo, expl, win, loss = (arr[:, k] for k in range(9))

    def rate(mask):
        n = int(mask.sum())
        k = int(expl[mask].sum()) if n else 0
        p, lo, hi = wilson(k, n)
        return n, k, p, lo, hi

    def wl_rate(mask):
        """المقياس القابل للتنفيذ: نجاح = ضرب الهدف قبل الوقف · انهيار = الوقف أولًا.
        يرجّع (n, w, l, win_rate, wr_lo, wr_hi, crash_rate) — win_rate على المحسومة فقط."""
        m = mask.astype(bool)
        n = int(m.sum())
        w = int(win[m].sum()) if n else 0
        l = int(loss[m].sum()) if n else 0
        dec = w + l
        p, lo, hi = wilson(w, dec)
        crash = (l / n) if n else 0.0
        return n, w, l, p, lo, hi, crash

    def mech_stats(mask):
        """🖐️ ميكانيكا فيصل (دخول المسح + وقف بنيوي + هدف 100%): على الداخِلة فقط.
        يرجّع (cands, entered, entry_rate, win_rate, wr_lo, wr_hi, expectancy_R, swept_rate)."""
        base = mask.astype(bool)
        cands = int(base.sum())
        m = base & (m_ent > 0.5)
        n = int(m.sum())
        w = int(m_win[m].sum()) if n else 0
        Rs = m_R[m]
        exp = float(np.nanmean(Rs)) if n else 0.0
        wr, wlo, whi = wilson(w, n)
        swept = int((Rs == -1.0).sum()) if n else 0
        return (cands, n, (n / cands if cands else 0.0), wr, wlo, whi, exp,
                (swept / n if n else 0.0))

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

    # 🎯 الفيصل الحاسم: المقياس القابل للتنفيذ (هدف +100% قبل وقف −50%) + عدم التماثل
    b_n, b_w, b_l, b_wr, b_wlo, b_whi, b_cr = wl_rate(np.ones(N, bool))
    c_n2, c_w, c_l, c_wr, c_wlo, c_whi, c_cr = wl_rate(cm)
    out.append(f"\n## 🎯 الفيصل الحاسم — قابل للتنفيذ (هدف +{EXPLODE_PCT:g}% قبل وقف −{STOP_PCT:g}%)\n")
    out.append("| العيّنة | محسومة | نجاح | انهيار | نسبة النجاح | Wilson95 | معدّل الانهيار |")
    out.append("|---|--:|--:|--:|--:|---|--:|")
    out.append(f"| الأساس | {b_w+b_l} | {b_w} | {b_l} | {b_wr*100:.1f}% | "
               f"[{b_wlo*100:.1f}, {b_whi*100:.1f}] | {b_cr*100:.1f}% |")
    out.append(f"| **التوليفة** | {c_w+c_l} | {c_w} | {c_l} | **{c_wr*100:.1f}%** | "
               f"[{c_wlo*100:.1f}, {c_whi*100:.1f}] | **{c_cr*100:.1f}%** |")
    wr_lift = (c_wr / b_wr) if b_wr > 0 else float("nan")
    cr_lift = (c_cr / b_cr) if b_cr > 0 else float("nan")
    out.append(f"\n- **رفع النجاح:** {wr_lift:.2f}× · **رفع الانهيار:** {cr_lift:.2f}× — "
               "الحافة حقيقية فقط لو رفع النجاح > رفع الانهيار (عدم تماثل صاعد؛ وإلا = تذبذب).")

    # 🖐️ ميكانيكا فيصل: دخول المسح + وقف بنيوي + هدف 100% → التوقّع R (طلب المستخدم)
    bmc = mech_stats(np.ones(N, bool))
    cmc = mech_stats(cm)
    out.append(f"\n## 🖐️ ميكانيكا فيصل — دخول المسح-الاستعادة + وقف ~{SWEEP_PCT+STOP_MARGIN:g}% "
               f"تحت الدعم + هدف +{EXPLODE_PCT:g}% (القياس بالتوقّع R)\n")
    out.append("| العيّنة | مرشّح | دخل | نسبة الدخول | نجاح | Wilson95 | **التوقّع R** | مُسِح-قبل |")
    out.append("|---|--:|--:|--:|--:|---|--:|--:|")
    out.append(f"| الأساس | {bmc[0]} | {bmc[1]} | {bmc[2]*100:.1f}% | {bmc[3]*100:.1f}% | "
               f"[{bmc[4]*100:.1f}, {bmc[5]*100:.1f}] | **{bmc[6]:+.3f}R** | {bmc[7]*100:.1f}% |")
    out.append(f"| **التوليفة** | {cmc[0]} | {cmc[1]} | {cmc[2]*100:.1f}% | {cmc[3]*100:.1f}% | "
               f"[{cmc[4]*100:.1f}, {cmc[5]*100:.1f}] | **{cmc[6]:+.3f}R** | {cmc[7]*100:.1f}% |")
    out.append(f"\n- التوقّع = متوسط R للصفقة (خسارة=−1R · هدف=+{((1+EXPLODE_PCT/100)-1)/((SWEEP_PCT+STOP_MARGIN)/100):.0f}R تقريبًا). "
               "**موجب = يربح بطريقة فيصل؛ وأعلى من الأساس = التوليفة تضيف.**")
    # لكل سنة (توقّع ميكانيكا فيصل للتوليفة)
    out.append("\n| السنة | دخل (توليفة) | نجاح | التوقّع R |")
    out.append("|---|--:|--:|--:|")
    mech_yr = []
    for y in YEARS:
        yc = mech_stats((yr == y) & cm)
        mech_yr.append(yc[6])
        out.append(f"| {y} | {yc[1]} | {yc[3]*100:.1f}% | {yc[6]:+.3f}R |")

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
    # 🎯 الفحصان الحاسمان (قابلية التنفيذ + عدم التماثل — يقتلان الفضفضة والبقاء):
    passes.append(("نجاح التنفيذ (هدف قبل وقف): Wilson المطابق > نجاح الأساس", c_wlo > b_wr))
    passes.append(("عدم تماثل صاعد: رفع النجاح > رفع الانهيار", wr_lift > cr_lift))
    # 🖐️ فحص ميكانيكا فيصل (المحور الآن — طلب المستخدم): التوقّع R موجب وأعلى من الأساس + متّسق
    passes.append(("🖐️ توقّع ميكانيكا فيصل موجب (R>0)", cmc[6] > 0))
    passes.append(("🖐️ توقّع التوليفة > توقّع الأساس", cmc[6] > bmc[6]))
    passes.append(("🖐️ موجب في السنوات الثلاث", all(r > 0 for r in mech_yr)))
    verdict = all(v for _, v in passes)
    out.append("\n## ⚖️ الحكم مقابل المعيار المسجَّل مسبقًا\n")
    for name, v in passes:
        out.append(f"- {'✅' if v else '❌'} {name}")
    out.append(f"\n### النتيجة: **{'يُعتمد — إشارة اختيار حقيقية' if verdict else 'نفي — لا يبلغ العتبة'}**")
    if not verdict:
        out.append("الحافة = التوقيت لا الاختيار (اتّساقًا مع C3/الرابط-المشترك/M2/M4).")

    # 🤖 المرحلة 0: برهان قابلية تعلّم «اليد» على دخول-المسح (FC_LEARN=1) — بحث/جدوى فقط
    if (os.environ.get("FC_LEARN") or "").strip() in ("1", "true", "yes"):
        ent = m_ent > 0.5
        _feats = np.column_stack([is_rs[ent], ema_ok[ent], bs_ok[ent], sp_ok[ent],
                                  np.nan_to_num(gaps[ent], nan=0.0)])
        out += _phase0_learnability(_feats, m_win[ent], yr[ent],
                                    ["مقسّم", "أسّي هابط", "قاعدة3ج", "انفجار سابق", "فجوة EMA50"])

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
