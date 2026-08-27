#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🥇🎯 T-GOLD-ENTRY — أذرعُ «آلة دخول فيصل» على اللقطات المجمَّدة.

العقد: `gold_entry_prereg.md` (مدفوعٌ **قبل** هذا الملفّ — والترتيبُ مُثبَتٌ
بتاريخ الكوميتات). بحث/قياسٌ فقط · **صفرُ مسٍّ بالإنتاج** · لا `LOGIC_VERSION`
· الإنتاجُ لا يستورد هذا الملفّ.

**إعادةُ استعمالٍ بالاسم — صفرُ منطقٍ منسوخ:** القراءةُ
`press_radar.press_read(sl, w=40)` (‏كما في `press_wake_arms` حرفيًّا) ·
الخطةُ الإنتاجية `rebound_arms.mirror_plan` · **ومحرّكُ الحسم الوحيد
`rebound_arms.resolve_episode`** — تُنادى في كلّ ذراعٍ بلا استثناء، **حتى في
فرع الانطلاق** (بدفعةٍ واحدةٍ هي سعرُ الدخول و`wait=1` ⇒ التعبئةُ مضمونةٌ
عند إغلاق الشمعة نفسِها) فلا يوجد محرّكُ حسمٍ ثانٍ في المستودع.

🔴 **مِشيةٌ واحدة · ميزانيةٌ ثابتةٌ بالبناء:** `press_read` تُقرأ **مرّةً
واحدةً لكلّ فهرس**، والأذرعُ السبع تُقيَّم على **مجموعة الحلقات نفسِها**
بنفس الكادنس (‏`i += WAIT` بعد كلّ مطابقة) ⇒ يستحيل أن يكون الفرقُ بين
ذراعين أثرَ ميزانيةٍ (درسُ `T-CLIFF`).

📐 **وحدةُ المخاطرة لكلّ ذراعٍ من خطّتها هي** (‏§⑦-1 من العقد):
`R_win = 0.5×المتوسّط ÷ (المتوسّط − الوقف)` — و`GE3` يقفل أن قيمتَها لخطة
الإنتاج تساوي `press_backtest.r_win_value()` بت-بت.
"""
from __future__ import annotations

import os
import sys

# ═══ ثوابتُ الأذرع — مثبَّتةٌ في العقد قبل أيّ رقم ═══
ARMS = ("P0", "P1", "P2", "P3", "P4", "P5", "P6")
# سلّمُ فيصل: من أرقام AMIX الحرفية (وقف 4.60 · دفعات 4.65/4.75/4.85)
LADDER = (1.01, 1.03, 1.05)          # faisal_adopted
K_LAUNCH = 5                          # engineering (نصُّه «خلال كم جلسه» بلا رقم)
GROUP_OSC_MAX = 10.0                  # faisal: «تذبذب نقاط 10٪ حد اقصى»
GROUP_RANGE_MIN = 20.0                # faisal: «شموع غبيه توصل 20٪» (تقريبٌ يوميّ)
GROUP_BODY_MAX = 0.30                 # engineering: «بدون جسم»
GROUP_LOOKBACK = 10                   # engineering
RSI_MAX = 30.0                        # faisal: «Rsi … مادون 30»
MA_FAST, MA_SLOW = 30, 50             # faisal: «ثبات السعر اعلى من متوسط 30-50»
LAUNCH_FAST, LAUNCH_SLOW = 50, 200    # faisal: «خط متوسط 50 اكبر من 200»
LAUNCH_MIN_BARS = 200                 # §⑦-4: متوسّطُ 200 غيرُ معرَّفٍ قبلها
HOLD5 = 5                             # faisal: بند ⑦ «5 جلسات»
PRESS_W = 40                          # = مِشيةُ `press_wake_arms` حرفيًّا


def _log(m):
    print(m, flush=True)


# ═══════════════════ دوالُّ نقيّة (تُختبَر مباشرةً) ═══════════════════
def r_win_of(tranches, stop):
    """نقيّة: ربحُ الصفقة الرابحة بوحدة مخاطرة **هذي الخطة**:
    `0.5×المتوسّط ÷ (المتوسّط − الوقف)`. مخاطرةٌ غيرُ موجبة ⇒ 0.0 (فاشلٌ-آمن).
    🔒 `GE3`: قيمتُها لخطة الإنتاج = `press_backtest.r_win_value()` بت-بت."""
    try:
        tr = [float(x) for x in tranches]
        if not tr:
            return 0.0
        avg = sum(tr) / len(tr)
        risk = avg - float(stop)
        return (0.5 * avg) / risk if risk > 0 else 0.0
    except Exception:                                            # noqa: BLE001
        return 0.0


def faisal_ladder(bottom):
    """نقيّة: سلّمُ فيصل — دفعاتٌ **فوق القاع** والوقفُ **القاعُ نفسُه**
    («‏1.50 قاع دخوله طلبات من 1.60 ل 1.70 **وقفه قاعه**» · وأرقامُ AMIX)."""
    b = float(bottom)
    return [round(b * f, 6) for f in LADDER], round(b, 6)


def osc_pct(hi, lo, a, b):
    """نقيّة: مدى تذبذّب النافذة `[a,b]` نسبةً إلى أدنى قاعها. تعذّرٌ ⇒ inf
    (‏= يُستبعَد ببوّابة القروبات — فاشلٌ-آمنٌ **مُشدِّد** لأن الاستبعاد هنا
    ليس كتمَ تنبيهٍ بل إقصاءُ حلقةٍ من ذراعٍ بحثيّة)."""
    try:
        a = max(int(a), 0)
        b = int(b)
        if b < a:
            return float("inf")
        seg_hi = max(float(x) for x in hi[a:b + 1])
        seg_lo = min(float(x) for x in lo[a:b + 1])
        return (seg_hi - seg_lo) / seg_lo * 100.0 if seg_lo > 0 else float("inf")
    except Exception:                                            # noqa: BLE001
        return float("inf")


def group_candle(op, hi, lo, cl, a, b):
    """نقيّة: أفيها شمعةُ قروبٍ «غبيّة»؟ مدًى `GROUP_RANGE_MIN`% فأكثر
    **وجسمٌ دون** `GROUP_BODY_MAX` من مداها.
    ⚠️ **تقريبٌ يوميّ مُعلَن** (‏§⑦-2): قاعدةُ فيصل على فريم 4 ساعات
    واللقطةُ يوميّةٌ حصرًا — فيُقاس الشكلُ نفسُه على اليوميّ بحدّه هو،
    **ولا يُسمّى قاعدةَ فيصل**."""
    try:
        for k in range(max(int(a), 0), int(b) + 1):
            _lo = float(lo[k])
            rng = float(hi[k]) - _lo
            if _lo <= 0 or rng <= 0:
                continue
            if (rng / _lo * 100.0 >= GROUP_RANGE_MIN
                    and abs(float(cl[k]) - float(op[k])) < GROUP_BODY_MAX * rng):
                return True
        return False
    except Exception:                                            # noqa: BLE001
        return False


def ema_series(cl, span):
    """نقيّة: سلسلةُ EMA بنفس تعريف الإنتاج (`ewm(span, adjust=False)`).
    🔒 **سببيّةٌ بالبناء** فقيمتُها عند `j` تعتمد بارات `≤ j` حصرًا (لا نظر
    مستقبليّ) — و`GE4` يقفل أن آخرَ قيمةٍ = `Super_stock.ema` بت-بت."""
    import pandas as pd                                          # noqa: PLC0415
    return pd.Series([float(x) for x in cl]).ewm(
        span=int(span), adjust=False).mean().values


def fill_index(lo, i, top, wait, n=None):
    """نقيّة: أوّلُ بارٍ بعد `i` يلمس `top` خلال `wait`. لا شيء ⇒ None.
    🔒 نفسُ حلقة التعبئة في `resolve_episode` حرفيًّا (‏`GE5` يقفل التكافؤ)."""
    try:
        n = len(lo) if n is None else int(n)
        for j in range(int(i) + 1, min(int(i) + 1 + int(wait), n)):
            if float(lo[j]) <= float(top):
                return j
        return None
    except Exception:                                            # noqa: BLE001
        return None


def launch_index(ef, es, start, end, n):
    """نقيّة: أوّلُ إغلاقٍ في `[start, end)` يكون فيه المتوسّطُ السريع فوق
    البطيء — «باول انطلاقة السهم». لا شيء ⇒ None."""
    try:
        for j in range(max(int(start), 0), min(int(end), int(n))):
            if float(ef[j]) > float(es[j]):
                return j
        return None
    except Exception:                                            # noqa: BLE001
        return None


def wilson(k, n, z=1.96):
    import rebound_arms as RB                                    # noqa: PLC0415
    return RB.wilson(k, n, z)


# ═══════════════════ المِشية ═══════════════════
def walk_symbol_gold(sym, df, year=None):
    """مِشيةُ §⑬ نفسُها (كادنسًا وقراءةً) + حصيلةُ الأذرع السبع لكلّ حلقة.

    ترجع قائمةَ قواميس: لكلّ ذراعٍ `(eligible, outcome, rwin)`.
    """
    import press_backtest as PB                                  # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    recs = []
    # 🔒 ثابتُ الإنتاج لخطة الإنتاج **حرفيًّا** (لا مكافئًا جبريًّا): درسُ
    # `ES9` المقيس — صيغتان متساويتان جبريًّا تتفرّقان عائمًا، و`V0` تكاملٌ
    # بت-بت مع §⑬ فيجب أن يكون رقمُ P0 هو رقمَ الإنتاج نفسَه لا مكافئَه.
    # وأذرعُ الخطط الأخرى تحسب وحدتَها بـ`r_win_of` (‏`GE3` يقفل تطابقَهما).
    try:
        op = df["Open"].values.astype(float)
        hi = df["High"].values.astype(float)
        lo = df["Low"].values.astype(float)
        cl = df["Close"].values.astype(float)
        yrs = [str(d)[:4] for d in df.index]
    except Exception:                                            # noqa: BLE001
        return recs
    n = len(df)
    try:
        ef = ema_series(cl, LAUNCH_FAST)
        es = ema_series(cl, LAUNCH_SLOW)
    except Exception:                                            # noqa: BLE001
        ef = es = None
    i = RB.MIN_BARS
    while i < n:
        if year and yrs[i] != str(year):
            i += 1
            continue
        sl = df.iloc[:i + 1]
        r = PR.press_read(sl, w=PRESS_W)
        if not r:
            i += 1
            continue
        pl = float(r["press_low"])
        hold = int(r.get("hold_sessions") or 0)
        j_low = max(i - hold, 0)

        tr0, st0 = RB.mirror_plan(pl)             # خطةُ الإنتاج
        trF, stF = faisal_ladder(pl)              # سلّمُ فيصل
        oc0 = RB.resolve_episode(hi, lo, i, tr0, st0)
        oc1 = RB.resolve_episode(hi, lo, i, tr0, pl)
        oc2 = RB.resolve_episode(hi, lo, i, trF, stF)
        rw0, rw1 = PB.r_win_value(), r_win_of(tr0, pl)
        rw2 = r_win_of(trF, stF)

        # ── P3: مركَّب — سلّمُ فيصل خلال K جلسات وإلّا بديلُ الانطلاق
        p3_ok = (ef is not None and es is not None and i + 1 >= LAUNCH_MIN_BARS)
        oc3, rw3, p3_branch = "no_fill", 0.0, "—"
        if p3_ok:
            fj = fill_index(lo, i, max(trF), K_LAUNCH, n)
            if fj is not None:
                oc3, rw3, p3_branch = oc2, rw2, "سلّم"
            else:
                lj = launch_index(ef, es, i + 1 + K_LAUNCH,
                                  i + 1 + RB.WAIT, n)
                if lj is None:
                    oc3, rw3, p3_branch = "no_fill", 0.0, "لا انطلاق"
                else:
                    entry = float(cl[lj])
                    oc3 = RB.resolve_episode(hi, lo, lj - 1, [entry], pl, wait=1)
                    rw3 = r_win_of([entry], pl)
                    p3_branch = "انطلاق"

        # ── بوّابةُ خلوّ القروبات (‏P4/P5) — نافذةُ الجلوس **بعد** يوم القاع
        # (‏ملحق ① من العقد، مؤرَّخٌ قبل أيّ تشغيلة): يومُ القاع هو شمعةُ
        # الانهيار غالبًا فيبتلع مداها القياسَ ويَسِمُ **سبب الهبوط** «قروبًا».
        a_sit = min(j_low + 1, i)
        osc = osc_pct(hi, lo, a_sit, i)
        grp = group_candle(op, hi, lo, cl, a_sit, i)
        group_free = bool(osc <= GROUP_OSC_MAX and not grp)
        # 📌 القراءةُ المسجَّلة أوّلًا — **وصفيّةٌ لا تحكم** (ملحق ①)
        osc_raw = osc_pct(hi, lo, j_low, i)
        grp_raw = group_candle(op, hi, lo, cl, i - GROUP_LOOKBACK + 1, i)

        # ── شرطا الترويسة السباعية (‏P5)
        rsi_ok = ma_ok = False
        try:
            import Super_stock as S                              # noqa: PLC0415
            _rsi = float(S.rsi(sl["Close"]).iloc[-1])
            rsi_ok = _rsi < RSI_MAX
            _c = float(cl[i])
            ma_ok = (_c > S.ema(sl["Close"], MA_FAST)
                     and _c > S.ema(sl["Close"], MA_SLOW))
        except Exception:                                        # noqa: BLE001
            rsi_ok = ma_ok = False

        h3 = hold >= PR.READY_HOLD
        recs.append({
            "sym": sym, "i": i, "hold": hold, "osc": round(osc, 2),
            "grp": grp, "p3b": p3_branch, "p3_ok": p3_ok,
            "osc_raw": round(osc_raw, 2), "grp_raw": grp_raw,
            "rsi_ok": bool(rsi_ok), "ma_ok": bool(ma_ok),
            "P0": (h3, oc0, rw0),
            "P1": (h3, oc1, rw1),
            "P2": (h3, oc2, rw2),
            "P3": (h3 and p3_ok, oc3, rw3),
            "P4": (h3 and group_free, oc2, rw2),
            "P5": (h3 and group_free and rsi_ok and ma_ok, oc2, rw2),
            "P6": (hold >= HOLD5, oc0, rw0),
        })
        i += RB.WAIT
    return recs


# ═══════════════════ التقرير ═══════════════════
def _arm_stats(recs, arm):
    """حصيلةُ ذراع: (مؤهَّلة · محسومة · فائزة · E لكلّ صفقة · E لكلّ حلقة)."""
    elig = [e for e in recs if e[arm][0]]
    dec = [e for e in elig if e[arm][1] in ("win", "loss")]
    k = sum(1 for e in dec if e[arm][1] == "win")
    tot = sum((e[arm][2] if e[arm][1] == "win" else -1.0) for e in dec)
    ev = tot / len(dec) if dec else None
    ev_ep = tot / len(elig) if elig else None       # `no_fill`/`open` = 0R
    return len(elig), len(dec), k, ev, ev_ep


def _paired_ci(recs, arm, base="P0"):
    """فاصلُ 95% للفرق **المقترن** على الحلقات المحسومة في الذراعين معًا
    (‏§⑦ من التقرير: القراءةُ مثبَّتةٌ في الكود قبل أيّ تشغيل)."""
    ds = []
    for e in recs:
        ea, eb = e[arm], e[base]
        if not (ea[0] and eb[0]):
            continue
        if ea[1] not in ("win", "loss") or eb[1] not in ("win", "loss"):
            continue
        ra = ea[2] if ea[1] == "win" else -1.0
        rb = eb[2] if eb[1] == "win" else -1.0
        ds.append(ra - rb)
    m = len(ds)
    if m < 2:
        return None, None, m
    mean = sum(ds) / m
    var = sum((d - mean) ** 2 for d in ds) / (m - 1)
    se = (var / m) ** 0.5
    return mean - 1.96 * se, mean + 1.96 * se, m


def _diff_counts(recs, arm):
    """حارسُ `V1`: كم حلقةً تفرّقت عن P0 — **أهليةً أو حصيلة**.
    🔴 الأهليةُ جزءٌ من الحارس عمدًا: P6 خطتُه خطةُ P0 ولا يختلف إلّا
    بالأهلية، فحارسٌ على الحصيلة وحدها كان سيقرؤه `no-op` كذبًا."""
    d_el = sum(1 for e in recs if e[arm][0] != e["P0"][0])
    d_oc = sum(1 for e in recs if e[arm][1] != e["P0"][1])
    return d_el, d_oc


def report(recs, n_syms, n_uni, skipped, year) -> int:
    _log(f"\n{'—' * 78}\n📊 T-GOLD-ENTRY سنة {year} — "
         f"رموزٌ مُشيت {n_syms} من {n_uni} · حلقات {len(recs)}")
    if not recs:
        _log("⛔ صفرُ حلقات (بصمةُ الـ`no-op`) — خروج 4.")
        return 4
    # V3: تغطيةُ الرموز (تكييفُ §⑦-3 — لا ملفَّ أيامٍ في هذا الشاسيه)
    cov = 100.0 * n_syms / max(n_uni, 1)
    _log(f"🩺 V3 تغطيةُ الكون: {cov:.1f}% · مستبعَدون {n_uni - n_syms} "
         f"({' · '.join(f'{k}={v}' for k, v in sorted(skipped.items())) or 'لا شيء'})")
    rc = 0
    if cov < 95.0:
        _log("⛔ V3: التغطيةُ دون 95% ⇒ خروج 3.")
        rc = 3

    base = _arm_stats(recs, "P0")
    _log(f"\n{'الذراع':<6}{'مؤهَّلة':>9}{'محسومة':>9}{'فائزة':>8}"
         f"{'بلغ الهدف':>11}{'R_win':>8}{'E/صفقة':>10}{'E/حلقة':>10}"
         f"{'Δ عن P0':>10}")
    rows = {}
    for arm in ARMS:
        el, dec, k, ev, ev_ep = _arm_stats(recs, arm)
        # 🐞 **عيبُ عرضٍ أُصلح (‏`gold_entry_result.md §⑨-8`):** كان يطبع
        #    **أوّلَ** قيمةٍ موجبة، و`P3` خطّتُه **متغيّرةٌ لكلّ حلقة** (فرعُ
        #    السلّم ثابت · وفرعُ الانطلاق يتغيّر بسعر الإغلاق) ⇒ كان يطبع
        #    رقمًا واحدًا لِما ليس واحدًا = **سطرُ عرضٍ يكذب**. الآن: قيمةٌ
        #    واحدةٌ فقط تُطبَع رقمًا، وأكثرُ من قيمةٍ تُطبَع «متغيّر».
        _rws = {round(e[arm][2], 6) for e in recs if e[arm][0] and e[arm][2] > 0}
        rw = _rws.pop() if len(_rws) == 1 else None
        rw_txt = f"{rw:>8.2f}" if rw is not None else f"{'متغيّر':>8}"
        d = (ev - base[3]) if (ev is not None and base[3] is not None) else None
        rows[arm] = (el, dec, k, ev, ev_ep, d)
        _log(f"{arm:<6}{el:>9}{dec:>9}{k:>8}"
             f"{(100.0 * k / dec if dec else 0):>10.2f}%{rw_txt}"
             f"{(f'{ev:+.3f}' if ev is not None else '—'):>10}"
             f"{(f'{ev_ep:+.3f}' if ev_ep is not None else '—'):>10}"
             f"{(f'{d:+.3f}' if d is not None else '—'):>10}")

    _log("\n🔎 V1 حارسُ الـ`no-op` (تفرّقٌ عن P0: أهليةً · حصيلةً):")
    for arm in ARMS[1:]:
        d_el, d_oc = _diff_counts(recs, arm)
        lo95, hi95, m = _paired_ci(recs, arm)
        ci = (f"[{lo95:+.3f},{hi95:+.3f}] ن={m}"
              if lo95 is not None else "— (ن دون 2)")
        _log(f"  {arm}: أهلية={d_el:<6} حصيلة={d_oc:<6} · "
             f"فاصلُ الفرق المقترن 95% {ci}")
        if d_el == 0 and d_oc == 0:
            _log(f"  ⛔ V1: {arm} لا يتفرّق عن P0 إطلاقًا (`no-op`) ⇒ خروج 4.")
            rc = 4 if rc == 0 else rc

    _log(f"\n🔗 مِرساةُ التكامل (‏V0): P0/HOLD3 محسومة={base[1]} · "
         f"فائزة={base[2]} · "
         f"بلغ الهدف={(100.0 * base[2] / base[1] if base[1] else 0):.2f}% · "
         f"التوقّع {(f'{base[3]:+.3f}R' if base[3] is not None else '—')}")
    _log("   (المجموعُ عبر الثلاث يجب أن يعيد §⑬: ‏5371 محسومة · 19.08% · +0.174R)")

    p3 = [e for e in recs if e["hold"] >= 3]
    _log(f"\n📌 P3: حلقاتُ HOLD3 بلا 200 شمعة (خارج مقامه، §⑦-4) = "
         f"{sum(1 for e in p3 if not e['p3_ok'])} من {len(p3)} · "
         f"فروعُه: سلّم={sum(1 for e in p3 if e['p3b'] == 'سلّم')} · "
         f"انطلاق={sum(1 for e in p3 if e['p3b'] == 'انطلاق')} · "
         f"لا انطلاق={sum(1 for e in p3 if e['p3b'] == 'لا انطلاق')}")
    _log(f"📌 بوّابةُ القروبات (نافذةُ الجلوس بعد القاع — الحاكمة، ملحق ①):"
         f" تذبذّبٌ فوق {GROUP_OSC_MAX}% = "
         f"{sum(1 for e in p3 if e['osc'] > GROUP_OSC_MAX)} · "
         f"شمعةٌ غبيّة (تقريبٌ يوميّ) = {sum(1 for e in p3 if e['grp'])}"
         f" · خالٍ = {sum(1 for e in p3 if e['osc'] <= GROUP_OSC_MAX and not e['grp'])}"
         f" من {len(p3)}")
    _log(f"   ↳ وصفيًّا لا حكمًا (القراءةُ المسجَّلةُ أوّلًا، شاملةً يومَ القاع):"
         f" تذبذّب={sum(1 for e in p3 if e['osc_raw'] > GROUP_OSC_MAX)} · "
         f"شمعة={sum(1 for e in p3 if e['grp_raw'])} · "
         f"خالٍ={sum(1 for e in p3 if e['osc_raw'] <= GROUP_OSC_MAX and not e['grp_raw'])}")
    # 📌 تشخيصُ شرطَي الترويسة السباعية (‏P5) — **وصفيٌّ لا يحكم**: إن خرج
    #    P5 فارغًا فالسببُ يُقرأ بالرقم لا بالادّعاء (هل الشرطان نادران في
    #    مجتمعِ القيعان أصلًا؟ وهو سؤالٌ عن **بنية** الوصفة لا عن ذراع).
    _log(f"📌 شرطا الترويسة على HOLD3: RSI دون {RSI_MAX} = "
         f"{sum(1 for e in p3 if e['rsi_ok'])} · "
         f"الإغلاقُ فوق متوسّطَي {MA_FAST}/{MA_SLOW} = "
         f"{sum(1 for e in p3 if e['ma_ok'])} · "
         f"الاثنان معًا = {sum(1 for e in p3 if e['rsi_ok'] and e['ma_ok'])} "
         f"من {len(p3)}")
    _log("\n⚠️ الهدفُ ثابتٌ في كلّ الأذرع (‏1.5×) — التجربةُ عن الدخول ·"
         " و«التعبئة» لمسٌ لا تنفيذ · و«الشمعةُ الغبيّة» تقريبٌ يوميّ مُعلَن.")
    return rc


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    import rebound_arms as RB                                    # noqa: PLC0415
    year = (os.environ.get("BACKTEST_YEAR") or "?").strip()
    path = os.environ.get("BT_FROZEN_PATH") or "frozen_backtest.pkl.gz"
    _log(f"\n{'=' * 78}\n🥇🎯 T-GOLD-ENTRY — سنة {year}\n{'=' * 78}")
    _log(f"📐 الأذرع: {' · '.join(ARMS)} · سلّم فيصل {LADDER} · K={K_LAUNCH} ·"
         f" قروب: تذبذّب {GROUP_OSC_MAX}% / مدًى {GROUP_RANGE_MIN}% / جسم"
         f" {GROUP_BODY_MAX} · RSI {RSI_MAX} · متوسّطات {MA_FAST}/{MA_SLOW}"
         f" وانطلاق {LAUNCH_FAST}/{LAUNCH_SLOW}")
    if not os.path.exists(path):
        _log(f"⛔ اللقطةُ المجمَّدة مفقودة ({path!r}) ⇒ خروج 2.")
        return 2
    hist, _sp, asof = S.load_frozen_dataset(path)
    if not hist:
        _log("⛔ اللقطةُ فارغة ⇒ خروج 2.")
        return 2
    _log(f"📦 لقطة as-of {asof} · رموز {len(hist)}")
    recs, n_syms, skipped = [], 0, {}
    yr = year if year and year != "?" else None
    for sym, df in hist.items():
        if df is None:
            skipped["إطارٌ غائب"] = skipped.get("إطارٌ غائب", 0) + 1
            continue
        if len(df) < RB.MIN_BARS + 5:
            skipped["تاريخٌ قصير"] = skipped.get("تاريخٌ قصير", 0) + 1
            continue
        n_syms += 1
        recs.extend(walk_symbol_gold(sym, df, year=yr))
        if n_syms % 500 == 0:
            _log(f"  … مشى {n_syms} رمزًا · حلقات {len(recs)}")
    return report(recs, n_syms, len(hist), skipped, year)


if __name__ == "__main__":
    sys.exit(main())
