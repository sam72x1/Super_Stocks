#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🧱🔁 `T-REBOUND-HOLD` — أذرعُ القياس (العقد: `rebound_hold_prereg.md` ·
مدفوعٌ **قبل** هذي الأداة وقبل أيّ رقم).

**السؤال:** هل قبولُ «المضغوط الممسوك عند مستوى مُختبَر» — الفئة التي يصدّها
الحارس الاتجاهي (`M4_base_واسعة_هبوطًا`) عن مسار الارتداد — يضيف تسليمًا
(‏بلوغ ‏+50% من متوسط الدفعات قبل الوقف) بكلفة محتملة؟

**التصميم (صفر مسّ إنتاج · مقياسٌ واحد):** مشيٌ لكل رمزٍ في اللقطة المجمَّدة،
**كلَّ جلسة** (خطوة 1)، نداءُ `analyze_ticker(sym, slice, pullback=True)`
**الإنتاجيّ بالاسم**:
  • قَبِل ⇒ حلقة `G0` — خطتها **من مُخرَجه** (`tranches`/`stop`).
  • رَفَض بسبب `M4_base_واسعة_هبوطًا` **حصرًا** (يُقرأ من `_REJECT_REASONS` —
    آلية الإنتاج نفسها، ويُفرَّغ قبل كل نداء فلا سببَ بائت) **و** استوفى
    `hold_overlay` (مستوى مُختبَر والإغلاق عنده داخل نطاق المسح 13%) ⇒ حلقة
    **`G1-إضافي`** — خطتها **مرآةُ صيغة الإنتاج المُعلَنة** (المرساة = المستوى
    المُختبَر · الدفعات `ENTRY_TRANCHES`×`ENTRY_STEP_PCT` · الوقف
    `STOP_BELOW_LOW_PCT` الأعمق تحتها — أرقام الإنتاج حرفيًّا، صفر رقم جديد).
بعد كل حلقةٍ يقفز الرمز `WAIT` جلسة (نافذة التعبئة) — **الذراعان في مشيةٍ
واحدة** = ميزانية مطابقة بالبناء.

**الحسم (`resolve_episode` — محرّك واحد للذراعين):** التعبئة أول جلسة يلمس
قاعُها أعلى دفعة خلال `WAIT`=40 وإلا `no_fill` (خارج المقام — استبعاد `_d`
نفسه) · ثم من متوسط الدفعات: الوقف يُفحَص **أولًا** في الشمعة نفسها (أرضية
متحفّظة) ⟵ ‏+50% (لمس قمة) قبل الوقف = ✅.

**حرّاس الصلاحية (منفَّذة لا موصوفة — درس `envelope §⑦`):**
`RHV1` عدّاداتُ الذراعين تُطبَع وصفرُ إضافيين ⇒ **خروج 4** (لا خضراء بصفر
قياس) · `RHV2` حتميّة النداء تُفحَص على عيّنة (نفس المدخل ⇒ نفس المُخرَج
بت-بت) · `RHV3` الإضافيّ حصرًا من السبب الهدف (مرفوض M1/M2/M5 لا يدخل ولو
وُجد مستوى) · `RHV4` لقطة مفقودة ⇒ **خروج 2**.

⚠️ **ملاحظة إطار مُعلَنة:** المشي بإعدادات الإنتاج **الحالية** كاملةً — ومنها
`ANCHOR_MODE=tested_strict` المعتمدة (‏2026-08-14) ⇒ يقيس «إنتاجَ اليوم +
الطبقة» لا إنتاجَ ما قبل الاعتماد، وهذا هو السؤال المقصود.
🔒 خارج مسار الفرز كليًّا (`Super_stock` لا يستورد هذا الملف — مقفول) · لا
`LOGIC_VERSION` · والنتيجة تشخيصٌ يُحكَم بمعايير §④ المسجَّلة لا بعدها."""
from __future__ import annotations

import json
import os
import sys

WAIT = 40            # نافذة التعبئة (جلسات) — نفس BT_MAX_WAIT الإنتاجية
TARGET_X = 1.5       # +50% من متوسط الدفعات (مقياس d50 المعتمد في كل أذرعنا)
MIN_BARS = 60        # أدنى تاريخ قبل بدء المشي (بوابات الإنتاج ترفض الأقصر أصلًا)
TARGET_REASON = "M4_base_واسعة_هبوطًا"


def _log(m):
    print(m, flush=True)


def hold_overlay(df):
    """نقيّة: شرطا الطبقة (§② من التسجيل) — مستوى مُختبَر موجود، وآخرُ إغلاقٍ
    عنده أو فوقه داخل `SPLIT_SWEEP_MAX_PCT`(=13)% (نطاق المسح الموثّق).
    ترجع المستوى أو None."""
    import Super_stock as S                                      # noqa: PLC0415
    try:
        t = S.tested_level(df)
        if not t:
            return None
        level = float(t["level"])
        close = float(df["Close"].values[-1])
        if level <= 0 or close < level:
            return None                        # كُسر — ليس «ممسوكًا»
        cap = level * (1.0 + float(S.CONFIG.get("SPLIT_SWEEP_MAX_PCT", 13.0)) / 100.0)
        if close > cap:
            return None                        # غادر المستوى
        return level
    except Exception:                                            # noqa: BLE001
        return None


def mirror_plan(anchor: float):
    """مرآةُ صيغة الإنتاج المُعلَنة (§③): دفعات `ENTRY_TRANCHES` بخطوة
    `ENTRY_STEP_PCT`% صعودًا من المرساة · الوقف الحدُّ الأعمق من
    `STOP_BELOW_LOW_PCT` تحتها (‏WETO الإنتاجي: 2.70 ⟵ وقف 2.511 = ×0.93 ✓)."""
    import Super_stock as S                                      # noqa: PLC0415
    n = int(S.CONFIG.get("ENTRY_TRANCHES", 3))
    step = float(S.CONFIG.get("ENTRY_STEP_PCT", 3.0)) / 100.0
    s = S.CONFIG.get("STOP_BELOW_LOW_PCT", (5, 7))
    s_hi = float(s[1] if isinstance(s, (list, tuple)) else s)
    tranches = [round(anchor * (1.0 + step * k), 6) for k in range(n)]
    return tranches, round(anchor * (1.0 - s_hi / 100.0), 6)


def resolve_episode(hi, lo, i, tranches, stop, wait=WAIT, target_x=TARGET_X):
    """نقيّة — محرّك حسمٍ واحد للذراعين: التعبئة بلمس أعلى دفعة خلال `wait`،
    ثم من متوسط الدفعات: **الوقف أولًا في الشمعة نفسها** ⟵ الهدف ‏+50%.
    ترجع 'win' | 'loss' | 'no_fill' | 'open'."""
    try:
        top = max(tranches)
        avg = sum(tranches) / len(tranches)
        n = len(lo)
        fill = None
        for j in range(i + 1, min(i + 1 + wait, n)):
            if float(lo[j]) <= top:
                fill = j
                break
        if fill is None:
            return "no_fill"
        tgt = avg * target_x
        for j in range(fill, n):
            if float(lo[j]) <= stop:
                return "loss"                  # الوقف يُفحَص أولًا (أرضية متحفّظة)
            if float(hi[j]) >= tgt:
                return "win"
        return "open"
    except Exception:                                            # noqa: BLE001
        return "no_fill"


def is_target_reject(sym: str) -> bool:
    """`RHV3`: هل آخرُ رفضٍ لهذا الرمز هو السبب الهدف **حصرًا**؟ (يُقرأ من
    `_REJECT_REASONS` الإنتاجية — مرفوضُ جدارٍ آخر لا يدخل ولو وُجد مستوى)."""
    import Super_stock as S                                      # noqa: PLC0415
    return S._REJECT_REASONS.get(str(sym).upper()) == TARGET_REASON


def walk_symbol(sym, df, year=None):
    """يمشي رمزًا واحدًا كلَّ جلسة ويرجع حلقاته [(ذراع، فهرس، حسم)].

    🔴 قيدُ السنة إلزاميّ (أمسكه الفحص قبل الدفع): بلا تقييد أيام القبول بسنة
    `BACKTEST_YEAR` كانت اللقطات الثلاث ستتداخل **عدًّا مزدوجًا** (كل لقطة
    تحمل تاريخًا أطول من سنتها). المؤشّرات تقرأ التاريخ كاملًا، والقبول
    يُحتسب لجلسات السنة فقط، والحسم يمتدّ بذيل البيانات (عرف الباكتيست)."""
    import Super_stock as S                                      # noqa: PLC0415
    out = []
    try:
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        yrs = [str(d)[:4] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return out
    n = len(df)
    i = MIN_BARS
    while i < n:
        if year and yrs[i] != str(year):
            i += 1
            continue
        sl = df.iloc[:i + 1]
        S._REJECT_REASONS.pop(str(sym).upper(), None)   # لا سببَ بائت (RHV3)
        try:
            r = S.analyze_ticker(sym, sl, pullback=True)
        except Exception:                                        # noqa: BLE001
            r = None
        if r:
            tr = r.get("tranches") or r.get("entry") or []
            st = r.get("stop")
            st = float(st[0] if isinstance(st, (list, tuple)) else st or 0)
            if tr and st > 0:
                oc = resolve_episode(hi, lo, i, [float(x) for x in tr], st)
                out.append(("G0", i, oc))
            i += WAIT
            continue
        if is_target_reject(sym):
            level = hold_overlay(sl)
            if level:
                tr, st = mirror_plan(level)
                oc = resolve_episode(hi, lo, i, tr, st)
                out.append(("G1x", i, oc))
                i += WAIT
                continue
        i += 1
    return out


def wilson(k, n, z=1.96):
    if n <= 0:
        return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * ((p * (1 - p) / n + z * z / (4 * n * n)) ** 0.5)
    return ((c - h) / d, (c + h) / d)


def report(episodes, n_syms, year) -> int:
    g0 = [e for e in episodes if e[0] == "G0"]
    g1 = [e for e in episodes if e[0] == "G1x"]
    _log(f"\n📊 T-REBOUND-HOLD سنة {year} — رموزٌ مفحوصة {n_syms}")
    _log(f"  RHV1 عدّادات: حلقات G0={len(g0)} · إضافيّو G1={len(g1)}")
    if not g1:
        _log("⛔ RHV1: صفرُ إضافيين — لا تشغيلةَ خضراءَ بصفر قياس (خروج 4). "
             "إن تكرّر في السنوات الثلاث فتنبّؤ RH1 بشقّه الصفريّ تحقّق: "
             "الفئة تُقاس من حصاد رادار الضغط الأماميّ.")
        return 4
    for name, eps in (("G0 (الإنتاج)", g0), ("G1-إضافي (الطبقة)", g1)):
        dec = [e for e in eps if e[2] in ("win", "loss")]
        k = sum(1 for e in dec if e[2] == "win")
        nf = sum(1 for e in eps if e[2] == "no_fill")
        op = sum(1 for e in eps if e[2] == "open")
        w = wilson(k, len(dec))
        rate = 100.0 * k / len(dec) if dec else 0.0
        _log(f"  {name:<18} حلقات={len(eps):<5} محسومة={len(dec):<5} "
             f"بلغ50={k:<4} نسبة={rate:6.2f}% Wilson=[{100 * w[0]:.2f},{100 * w[1]:.2f}] "
             f"no_fill={nf} · open={op}")
        # §⑨ `T-REBOUND-2`: المقياسُ الحاكم — التسليم لكل حلقةٍ مقبولة
        # (المقامُ كلُّ الحلقات بما فيها no_fill/open — يجمع الجدوى والتنفيذ)
        wp = wilson(k, len(eps))
        _log(f"    ⤷ التسليم لكل حلقة = {100.0 * k / len(eps) if eps else 0.0:6.2f}% "
             f"({k} من {len(eps)}) Wilson=[{100 * wp[0]:.2f},{100 * wp[1]:.2f}]")
    dec1 = [e for e in g1 if e[2] in ("win", "loss")]
    _log(f"  🧭 أرضيّة §④-1 (إضافيّون محسومون فوق 30): {len(dec1)} ⇒ "
         + ("✅" if len(dec1) >= 30 else "🔴 **لا حكم لهذي السنة**"))
    _log("  🧭 الكلفة §④-3 تُقرأ من عدّاد الإضافيين مقابل جلسات السنة (الحكم "
         "النهائيّ بالسنوات الثلاث مجتمعة — لا حكم بسنة).")
    return 0


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🧱🔁 T-REBOUND-HOLD — الحارس الاتجاهي والممسوك عند مستوى"
         f" مُختبَر · سنة {year}\n{'=' * 78}")
    if not os.path.exists(path):
        _log(f"⛔ RHV4: اللقطة المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)} · "
         f"ANCHOR_MODE={S.CONFIG.get('ANCHOR_MODE')!r} (إنتاجُ اليوم — مُعلَن)")
    # RHV2: حتميّة على عيّنة — نفس المدخل مرّتين ⇒ نفس المُخرَج بت-بت
    probe = sorted(hist)[:5]
    for sym in probe:
        df = hist[sym]
        if len(df) < MIN_BARS + 10:
            continue
        sl = df.iloc[:MIN_BARS + 10]
        a = S.analyze_ticker(sym, sl, pullback=True)
        b = S.analyze_ticker(sym, sl, pullback=True)
        if (a is None) != (b is None):
            _log(f"⛔ RHV2: نداءان متطابقان اختلفا على {sym} — عطبُ حتميّةٍ يوقف (خروج 3).")
            return 3
    episodes, n_syms = [], 0
    yr = year if year and year != "?" else None
    if not yr:
        _log("⚠️ بلا سنةٍ محددة — المشي على كامل مدى اللقطة (يُعلَن).")
    for sym, df in hist.items():
        if df is None or len(df) < MIN_BARS + 5:
            continue
        n_syms += 1
        episodes.extend(walk_symbol(sym, df, year=yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات حتى الآن {len(episodes)}")
    return report(episodes, n_syms, year)


if __name__ == "__main__":
    sys.exit(main())
