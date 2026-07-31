#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⚡ T-EVENT-EXEC — **المُشغِّل** (`event_exec_prereg.md`).

يبني كون **ARMED** من أداة الإعادة الأمينة نفسها (`T-REPLAY10` · الذراع `R0`)، ثم
يُعيد تشغيل **زناد الرادار الإنتاجيّ** دقيقةً بدقيقة على كل (رمز، جلسة) مسلَّحة،
وينفّذ الأذرع الأربع بقواعد التنفيذ المسجَّلة.

🔒 صفر مسّ إنتاج · النتائج **تُطبَع للسجلّ** (تنزيل الـartifacts محجوبٌ بسياسة الشبكة).
"""
from __future__ import annotations

import os
import sys

# ⚠️ قبل الاستيراد (‏`_apply_backtest_overrides` يُنفَّذ وقت التحميل — وإلا خرج العلم خاملًا)
os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_REPLAY10"] = "1"

import event_exec as EX                                        # noqa: E402
import replay10 as RP                                          # noqa: E402
import Super_stock as S                                        # noqa: E402

MAX_SYMBOLS = int(os.environ.get("EVENT_EXEC_MAX_SYMBOLS", "0") or 0)   # 0 = بلا حدّ
PROBE_ONLY = os.environ.get("EVENT_EXEC_PROBE", "").strip() == "1"
SCALE_TOL = 0.15


def _armed(trades):
    """كون ARMED = **ما كان على القائمة فعلًا** (الذراع `R0`)، لا ما رشّحه الفارز."""
    cands, idx, outcome_of = RP.candidates_from_trades(trades)
    res = RP.replay(cands, outcome_of=outcome_of, ranker=RP.rank_actual,
                    sessions=range(0, len(idx)))
    inv = {v: k for k, v in idx.items()}
    out = []
    for c in res["taken"]:
        _, held = outcome_of(c)
        out.append({"symbol": c.symbol, "trade": c.payload,
                    "start": c.payload["date"],
                    "end": inv.get(c.session + max(int(held), 0),
                                   c.payload["exit_date"])})
    return out, res


def plan_levels(t, tol=0.03):
    """مستويات الخطة من الصفقة المخزَّنة.

    **الأرضية تُستعاد من الوقف بمعادلة الإنتاج نفسها:** `stop[0] = pivot × (1 −
    s_hi/100)` (‏`Super_stock.py` عند بناء المستويات) ⇒ `pivot = stop ÷ 0.93`.
    ⚠️ **ولا تُترَك افتراضًا صامتًا:** تُشتقّ الأرضيةُ **ثانيةً** من متوسط الدفعات
    (`entry = pivot × (1 + خطوة×(n−1)/2)`) ويُقارَن الاشتقاقان؛ واختلافُهما فوق
    `tol` ⇒ **`level_mismatch` يُستبعَد ويُعدّ** بدل أن يُبنى على أرضيةٍ خاطئة.

    🔴 **ومستوى الكسر يُحسب بدالّة الإنتاج `_ignition_break_level` نفسها** على شكلٍ
    مطابقٍ لسجلّ القائمة: **الرقم الحرج** إن وُجد وإلا الأرضية ×1.05.
    ⚠️ **ولولا ذلك لقِيس زنادٌ آخر:** المِجَسّ الأول (بلا رقمٍ حرج) **أشعل 90% من
    الجلسات** — لأن الأرضية ×1.05 حاجزٌ يتجاوزه السهم ويبقى فوقه. فالرقم الحرج ليس
    تحسينًا تجميليًّا بل **شرطُ صلاحيةٍ للقياس كلّه**."""
    try:
        entry, stop, t1 = float(t["entry"]), float(t["stop"]), float(t["t1"])
    except (TypeError, ValueError, KeyError):
        return None
    if entry <= 0 or entry - stop <= 0 or t1 <= entry:
        return None
    s_hi = float(S.CONFIG["STOP_BELOW_LOW_PCT"][1])
    piv = stop / (1.0 - s_hi / 100.0)
    n = max(1, int(S.CONFIG["ENTRY_TRANCHES"]))
    step = float(S.CONFIG["ENTRY_STEP_PCT"]) / 100.0
    piv_chk = entry / (1.0 + step * (n - 1) / 2.0)
    if piv <= 0 or abs(piv_chk / piv - 1.0) > tol:
        return None                    # اشتقاقان متعارضان ⇒ لا نبني على الظنّ
    brk = S._ignition_break_level(
        {"pivot": t.get("pivot") or piv,
         "interp": {"critical_number": ({"price": t["crit"]} if t.get("crit")
                                        else None)}})
    if not brk:
        return None
    return {"pivot": piv, "break": float(brk), "stop": stop, "t1": t1,
            "from_crit": bool(t.get("crit"))}


def daily_break_level(trade, last_price, fallback):
    """🔴 **تجديد الرقم الحرج يوميًّا — كما يفعل الإنتاج بالضبط.**

    `update_watchlist_status` يعيد بناء `interp` كلَّ يوم بـ`last_price` المحدَّث بينما
    `key_levels`/`h4_levels`/الأهداف تبقى كما خُزِّنت ⇒ **الحاجز يتحرّك صاعدًا مع
    السهم**. وتجميدُه على يوم الإشارة كان يُشعل ‏56% من الجلسات (مقيس) لأن السهم
    يتجاوزه مرّةً ويبقى فوقه.

    `last_price` = **إغلاق الجلسة السابقة** لا الحالية — فالتحديث اليوميّ في الإنتاج
    يجري قبل الافتتاح. `fallback` = مستوى يوم الإشارة (لأوّل جلسة). فاشلة-آمنة."""
    ii = (trade or {}).get("interp_in")
    if not ii or not last_price:
        return fallback
    try:
        interp = S.build_interpretation(dict(ii, price=float(last_price))) or {}
        lvl = S._ignition_break_level({"pivot": ii.get("pivot"), "interp": interp})
        return float(lvl) if lvl else fallback
    except Exception:
        return fallback


def session_levels(days, sess, trade, base):
    """مستوى الكسر **لكل جلسة** بعد التجديد اليوميّ. دالّة **نقيّة** (بلا شبكة)
    عمدًا: خاصّية «بإغلاق الجلسة **السابقة**» تعتمد على **ترتيب** سطرين، وفحصُ
    النصّ لا يرى الترتيب — **ونجت طفرةُ إعادة الترتيب فعلًا** حتى استُخرجت هنا
    فصارت تُختبَر سلوكيًّا. أوّل جلسةٍ تأخذ `base` (لا سابقةَ لها)."""
    out, prev = {}, None
    for day in days:
        out[day] = daily_break_level(trade, prev, base)
        sb = sess.get(day) or []
        if sb:
            prev = float(sb[-1]["c"])
    return out


def _resolve_from(bars, i0, entry_ask, stop, t1):
    """الحسم **بمحرّك الإنتاج نفسه** (`_resolve_arm`) على شموع الدقيقة بعد الدخول:
    نملك من الشمعة التالية (`entry_intrabar=False`, `filled=0`) · الوقف أوّلًا عند
    التعادل · `spread=0` هنا **عمدًا** لأن تكلفة الدخول مدفوعةٌ واقعًا عند `ask`،
    وتكلفة الخروج تُطبَّق في `net_r` (فلا تُحتسب مرّتين)."""
    seg = bars[i0:]
    if len(seg) < 2:
        return None
    hi = [float(b["h"]) for b in seg]
    lo = [float(b["l"]) for b in seg]
    cl = [float(b["c"]) for b in seg]
    op = [float(b["o"]) for b in seg]
    out, ret, _, _ = S._resolve_arm(hi, lo, cl, op, entry_ask, stop, t1, 0,
                                    entry_intrabar=False, spread=0.0)
    return (out, ret)


def _one_event(sym, day, sess_bars, i, sig, lv, tag, pair_key):
    """ينفّذ حدثًا واحدًا بقواعد §④ المسجَّلة: `ask` عمره ≤5ث · لا بديلَ مريحًا."""
    bar = sess_bars[i]
    end_ms = int(bar["t"]) + 60_000            # §2c: `t` = **بداية** الشمعة
    row = {"arm": tag, "symbol": sym, "day": day, "pair_key": pair_key,
           "mod": bar.get("mod"), "trigger_price": sig.get("price"),
           "usd": sig.get("usd"), "executable": False, "net_r": None,
           "outcome": None, "reason": None}
    q = EX.hist_quotes(sym, end_ms, end_ms + EX.MAX_QUOTE_AGE_MS + 1000)
    ent = EX.pick_entry_quote(q, end_ms)
    if not ent:
        row["reason"] = "non_executable"       # يبقى **في المقام** كما سُجِّل
        return row
    spr = EX.spread_frac(ent)
    if spr is None:
        row["reason"] = "no_spread"
        return row
    row.update(executable=True, entry=ent["ask"], spread_pct=round(spr * 100, 3),
               quote_age_ms=ent["age_ms"])
    res = _resolve_from(sess_bars, i + 1, ent["ask"], lv["stop"], lv["t1"])
    if res is None:
        row["reason"] = "no_runway"
        return row
    out, raw = res
    row["outcome"] = out
    row["net_r"] = EX.net_r(raw, ent["ask"], lv["stop"], spr)
    row["remaining_gain"] = round(raw, 2)
    return row


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n⚡ T-EVENT-EXEC · السنة {year}\n{'=' * 72}")
    have = [t for t in trades if t.get("exit_date")]
    if not have:
        print("⛔ `BT_REPLAY10` خامل ⇒ لا كون ARMED — لا تُفسَّر نتيجة.")
        return 2
    armed, rep = _armed(have)
    if MAX_SYMBOLS:
        armed = armed[:MAX_SYMBOLS]
    print(f"كون ARMED (ما كان على القائمة فعلًا): {len(armed)} نافذة "
          f"· من {len(have)} إشارة · مرفوض بالسعة={rep['rejected_cap']}")
    if not EX.has_key():
        print("⛔ لا `POLYGON_API_KEY` ⇒ لا قياس. (فاشل-آمن: لا نتيجة مفبركة.)")
        return 2

    real, pseudo, cross, oper = [], [], [], []
    cov = {"windows": 0, "no_bars": 0, "sessions": 0, "scale_bad": 0,
           "trig": 0, "quiet": 0, "no_levels": 0, "crit": 0, "lifted": 0}
    for a in armed:
        lv = plan_levels(a["trade"])
        if not lv:
            cov["no_levels"] += 1
            continue
        cov["windows"] += 1
        cov["crit"] += 1 if lv.get("from_crit") else 0
        bars = EX.hist_minute_bars(a["symbol"], a["start"], a["end"])
        if not bars:
            cov["no_bars"] += 1
            continue
        sess = EX.group_sessions(bars)
        # §⑩-1 حارس المقياس: مرّةً واحدة على **أوّل جلسة مسلَّحة** (يوم الإشارة) —
        # لا كلَّ يوم، وإلّا أقصينا الرابح لأنه ارتفع (وارتفاعُه هو المطلوب).
        _days = sorted(sess)
        if _days and EX.scale_mismatch(sess[_days[0]], a["trade"].get("entry"),
                                       SCALE_TOL):
            cov["scale_bad"] += 1
            continue
        fired, quiet = [], []
        # 🔴 الحاجز **يتجدّد يوميًّا بإغلاق الجلسة السابقة** — مطابقةً للتحديث اليوميّ
        #    في الإنتاج (يجري قبل الافتتاح فلا يقرأ إغلاق اليوم نفسه).
        lvl_of = session_levels(_days, sess, a["trade"], lv["break"])
        for day in _days:
            sb = sess[day]
            cov["sessions"] += 1
            brk = lvl_of[day]
            if brk > lv["break"]:
                cov["lifted"] += 1
            hit = EX.replay_trigger(sb, brk, S._ignition_signal,
                                    vol_mult=S.CONFIG["IGNITION_VOL_MULT"])
            if hit:
                fired.append((day, sb, hit))
            else:
                quiet.append(day)
                xc = EX.cross_trigger(sb, brk)
                if xc:
                    cross.append(_one_event(a["symbol"], day, sb, xc[0], xc[1],
                                            lv, "E-CROSS", f"{day}|x"))
        cov["trig"] += len(fired)
        cov["quiet"] += len(quiet)
        for day, sb, (i, sig) in fired:
            pk = f"{day}|{sb[i].get('mod')}"
            r = _one_event(a["symbol"], day, sb, i, sig, lv, "E-REAL", pk)
            real.append(r)
            # ذراع E-CROSS على يوم الزناد أيضًا (نفس المستوى، بلا شرط الحجم)
            xc = EX.cross_trigger(sb, lvl_of.get(day, lv["break"]))
            if xc:
                cross.append(_one_event(a["symbol"], day, sb, xc[0], xc[1], lv,
                                        "E-CROSS", f"{day}|x"))
            # 🔴 ثانويّة: بوّابة المضارب (عتبتها شاركت في توليد الفرضية)
            end_ms = int(sb[i]["t"]) + 60_000
            tr = EX.hist_trades(a["symbol"], end_ms - 15 * 60_000, end_ms)
            ob = S._operator_blocks([(t["p"], t["s"]) for t in (tr or [])],
                                    S.CONFIG["OPERATOR_MIN_SHARES"]) if tr else None
            if ob and ob.get("has_operator"):
                oper.append(dict(r, arm="E-OPERATOR"))
            # ذراع الحدث الزائف المُطابَق داخل الرمز
            pd = EX.match_pseudo(day, quiet)
            if pd:
                pb = sess.get(pd) or []
                j = next((k for k, b in enumerate(pb)
                          if b.get("mod") == sb[i].get("mod")), None)
                if j is not None:
                    pseudo.append(_one_event(a["symbol"], pd, pb, j,
                                             {"price": pb[j].get("c")}, lv,
                                             "E-PSEUDO", pk))

    # ✅ «أثبت أن التجربة اشتغلت»: كم نافذةً استعملت **الرقم الحرج** فعلًا؟ صفرٌ هنا
    #    يعني أن المقيس زنادٌ آخر (المرجع الاحتياطيّ) — فلا تُقرأ النتيجة.
    print(f"🎯 مستوى الكسر: {cov['crit']}/{cov['windows']} نافذة بالرقم الحرج "
          f"· ارتفع الحاجز بالتجديد اليوميّ في {cov['lifted']} جلسة"
          + ("" if cov["crit"] else "  ⛔ **صفر** ⇒ الزناد ليس زنادَ الإنتاج — لا تُقرأ أذرع"))
    print(f"🩺 التغطية: نوافذ={cov['windows']} · بلا شموع={cov['no_bars']} "
          f"· جلسات={cov['sessions']} · مقياس مختلف={cov['scale_bad']} "
          f"· جلسات مشتعلة={cov['trig']} · هادئة={cov['quiet']} "
          f"· بلا مستويات={cov['no_levels']} · نداءات={EX.call_stats()}")
    if PROBE_ONLY:
        print("🔎 وضع المِجَسّ فقط — لا تُقرأ أذرع.")
        return 0

    def concen(rows, k):
        return EX.concentration(rows, k)

    def _med(xs):
        xs = sorted(v for v in xs if v is not None)
        return xs[len(xs) // 2] if xs else "—"

    def _report(name, rows, primary=False):
        if not rows:
            print(f"  {name}: صفر حدث.")
            return None
        ex = [r for r in rows if r.get("executable")]
        dec = [r for r in ex if r.get("net_r") is not None]
        ratio = len(ex) / len(rows) * 100.0
        cb = EX.cluster_bootstrap_mean(dec)
        print(f"  {name}: خام={len(rows)} · قابل للتنفيذ={len(ex)} ({ratio:.0f}%) "
              f"· محسومة={len(dec)} · متوسط صافي R={cb['mean']:+.3f} "
              f"· cluster 95%=[{cb['lo']:+.3f}, {cb['hi']:+.3f}] ({cb['k']} رمزًا)")
        if primary and dec:
            print(f"      تركيز الربح: أكبر رمز={concen(dec,'symbol'):.0%} "
                  f"· أكبر جلسة={concen(dec,'day'):.0%} "
                  f"· وسيط عمر الاقتباس={_med([r.get('quote_age_ms') for r in ex])}ms")
        return {"rows": rows, "ex": ex, "dec": dec, "ratio": ratio, "cb": cb}

    print("\n📊 الأذرع:")
    R = _report("E-REAL     (اشتعال حقيقيّ)", real, primary=True)
    P = _report("E-PSEUDO   (زائف مُطابَق)  ", pseudo)
    C = _report("E-CROSS    (عبور بلا حجم) ", cross)
    O = _report("E-OPERATOR (ثانويّة)      ", oper)

    if R and P:
        pd_ = EX.paired_diff(R["dec"], P["dec"])
        print(f"\n📐 الفرق المزدوج داخل الرمز (‏E-REAL − E-PSEUDO): "
              f"متوسط={pd_['mean']:+.3f}R · 95%=[{pd_['lo']:+.3f}, {pd_['hi']:+.3f}] "
              f"· أزواج={pd_['n']} ({pd_['k']} رمزًا)")

    print("\n🧭 بوّابة القرار الخماسية (‏§⑧ — الخمسة معًا، وتُقرأ عبر السنوات الثلاث):")
    if R:
        n = len(R["dec"])
        # ⚠️ تشغيلةُ سنةٍ واحدة **لا تعرف** الإجمالَ عبر السنوات، فلا تدّعي اجتيازه:
        #    يُحكَم هنا على الشقّ السنويّ فقط ويُصرَّح بأن الإجمال يُجمَع خارجًا.
        print(f"  ① العيّنة السنوية: {n} محسومة (يلزم ≥30) "
              f"⇒ {'✅' if n >= 30 else '🔴'} · "
              f"**والشقّ الإجماليّ (≥150) يُجمَع عبر السنوات الثلاث — لا تحكم عليه هنا**")
        print(f"  ② الحدّ السفليّ 95% = {R['cb']['lo']:+.3f} "
              f"⇒ {'✅ فوق الصفر' if R['cb']['lo'] > 0 else '🔴 دون الصفر'}")
        print(f"  ③ متوسط السنة = {R['cb']['mean']:+.3f} "
              f"⇒ {'✅ موجب' if R['cb']['mean'] > 0 else '🔴 سالب'}")
        print(f"  ④ نسبة التنفيذ = {R['ratio']:.0f}% (يلزم ≥80%) "
              f"⇒ {'✅' if R['ratio'] >= 80 else '🔴'}")
        cs, cd = concen(R["dec"], "symbol"), concen(R["dec"], "day")
        print(f"  ⑤ التركيز: رمز={cs:.0%} · جلسة={cd:.0%} (يلزم كلاهما ≤20%) "
              f"⇒ {'✅' if max(cs, cd) <= 0.20 else '🔴'}")
    else:
        print("  ⛔ صفر حدث ⇒ لا بوّابة تُقيَّم.")
    # 🔴 كان هنا سطرٌ يقول «الرقم الحرج غير مخزَّن فالمستوى = الأرضية×1.05» — وقد صار
    #    **كذبًا** بعد إصلاح المِجَسّ (الرقم الحرج يُخزَّن ويتجدّد يوميًّا). سطرُ صدقٍ
    #    بائتٌ أسوأ من غيابه، وهو درسُ «سطر عرضٍ بلا حقلٍ = كذبة» بعينه.
    print("\n⚠️ حدود الصدق كما سُجِّلت: NBBO قمّةُ دفترٍ لا عمقه (‏«قابل للتنفيذ» = "
          "وُجد ask معلَن، **لا** أن الحجم كان متاحًا عنده) · انحياز بقاء · تشويه "
          "تقسيمات · خطّ الترند حيٌّ فقط فيغيب من مرشّحي الحاجز ⇒ الحاجز أعلى أو "
          "مساوٍ للحيّ (أحداثٌ أقلّ لا أكثر) · الحسم بلمسة الذيل (محافظ) · ولا وقفَ "
          "متحرّكًا ولا خروجًا جزئيًّا (‏T-MANAGE-25).")
    return 0


if __name__ == "__main__":
    sys.exit(run())
