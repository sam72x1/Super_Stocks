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
    """كون ARMED = **ما كان على القائمة فعلًا** (الذراع `R0`)، لا ما رشّحه الفارز.

    🔴🔴 **بداية النافذة = `eligible_at` حصرًا** (إصلاح العيب الزمنيّ — مراجعة Codex
    الثانية): `trade["date"]` هو **يوم الإشارة** الذي **إغلاقُه بنى الخطّة**، فمسحُه
    نظرٌ مستقبليّ. و`eligible_at` = أوّل جلسةٍ يجوز فيها التنفيذ، يكتبها المحرّك من
    `fut.index[0]`.
    🔒 **ولا ارتداد إلى `date` عند غيابه** — الارتداد يُعيد التسريب **صامتًا**، وهو
    أسوأ من التوقّف. الغياب يعني أن العلم كان خاملًا ⇒ يُسقَط الصفّ ويُعدّ، مطابقةً
    لقاعدة «أثبت أن التجربة اشتغلت قبل تفسير نتيجتها». يرجّع `(نافذات، res، مُسقَط)`."""
    cands, idx, outcome_of = RP.candidates_from_trades(trades)
    res = RP.replay(cands, outcome_of=outcome_of, ranker=RP.rank_actual,
                    sessions=range(0, len(idx)))
    inv = {v: k for k, v in idx.items()}
    out, dropped = [], 0
    for c in res["taken"]:
        _, held = outcome_of(c)
        elig = c.payload.get("eligible_at")
        if not elig:
            dropped += 1
            continue
        out.append({"symbol": c.symbol, "trade": c.payload,
                    "start": elig,
                    "end": inv.get(c.session + max(int(held), 0),
                                   c.payload["exit_date"])})
    return out, res, dropped


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
            # 🎚️ `t3` من الخطة المخزَّنة — لا هدفٌ مُخترَع (`manage25_prereg.md` §②)
            "t3": (t.get("interp_in") or {}).get("t3"),
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


def _one_event(sym, day, sess_bars, i, sig, lv, tag, pair_key, fwd=None):
    """ينفّذ حدثًا واحدًا بقواعد §④ المسجَّلة: `ask` عمره ≤5ث · لا بديلَ مريحًا.

    🔴 **`fwd` = مسار الدقيقة من الدخول حتى نهاية نافذة ARMED** — لا جلسة الزناد
    وحدها. كان الحسم يجري داخل الجلسة الواحدة **خلافًا للتسجيل** («من يوم الزناد»)
    فسُحبت أرقامُ التشغيلة الأولى وأُصلح الأفق (`manage25_prereg.md` ⓪).

    🎚️ **وعليه تُحسب السياسة ب أيضًا** (‏T-MANAGE-25) على **نفس** الصفقة — فالمجتمع
    واحدٌ **بالبناء** لا بالتوفيق."""
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
    path = fwd if fwd is not None else sess_bars[i + 1:]
    res = _resolve_from(path, 0, ent["ask"], lv["stop"], lv["t1"])
    if res is None:
        row["reason"] = "no_runway"
        return row
    out, raw = res
    row["outcome"] = out
    row["net_r"] = EX.net_r(raw, ent["ask"], lv["stop"], spr)
    row["remaining_gain"] = round(raw, 2)
    # 🎚️ T-MANAGE-25: السياسة ب على **نفس** الصفقة. غيرُ الرابحة ⇒ ب = أ حرفيًّا.
    risk = (ent["ask"] - lv["stop"]) / ent["ask"] * 100.0
    if out != "win" or risk <= 0:
        row["net_r_b"] = row["net_r"]
        row["b_reason"] = "same_as_a"
    else:
        k = next((j for j, b in enumerate(path)
                  if float(b["h"]) >= lv["t1"]), None)
        rex = EX.runner_exit(path[k + 1:], lv["t1"], lv.get("t3")) if k is not None else None
        if rex is None:
            row["net_r_b"] = row["net_r"]
            row["b_reason"] = "no_runner_path"
        else:
            t1_ret = (lv["t1"] / ent["ask"] - 1.0) * 100.0
            run_ret = (rex[1] / ent["ask"] - 1.0) * 100.0
            row["net_r_b"] = EX.manage_b_r(raw, t1_ret, run_ret, spr) / risk
            row["b_reason"] = rex[0]
    return row


def run() -> int:
    trades = S.run_backtest() or []
    year = (os.environ.get("BACKTEST_YEAR", "") or "?").strip()
    print(f"\n{'=' * 72}\n⚡ T-EVENT-EXEC · السنة {year}\n{'=' * 72}")
    have = [t for t in trades if t.get("exit_date")]
    if not have:
        print("⛔ `BT_REPLAY10` خامل ⇒ لا كون ARMED — لا تُفسَّر نتيجة.")
        return 2
    armed, rep, dropped = _armed(have)
    if dropped:
        # 🔴 غيابُ `eligible_at` = علمٌ خامل/بناءٌ قديم. لا نرتدّ ليوم الإشارة (تسريب)
        #    ولا نصمت: يُعلَن ويُوقَف لو كان الغياب شاملًا.
        print(f"⚠️ أُسقِطت {dropped} نافذة بلا `eligible_at` (لا ارتداد ليوم الإشارة).")
    if not armed:
        print("⛔ صفر نافذةٍ بمرجعٍ زمنيّ صالح ⇒ لا قياس (لا نتيجة مفبركة).")
        return 2
    if MAX_SYMBOLS:
        armed = armed[:MAX_SYMBOLS]
    print(f"كون ARMED (ما كان على القائمة فعلًا): {len(armed)} نافذة "
          f"· من {len(have)} إشارة · مرفوض بالسعة={rep['rejected_cap']}")
    if not EX.has_key():
        print("⛔ لا `POLYGON_API_KEY` ⇒ لا قياس. (فاشل-آمن: لا نتيجة مفبركة.)")
        return 2

    real, pseudo, cross, oper = [], [], [], []
    ncross, nmiss, labels = [], [], []          # 🔬 T-NEARMISS · T-LABEL-AUDIT
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
        # §⑩-1 حارس المقياس: مرّةً واحدة على **أوّل جلسةٍ مؤهَّلة** (`eligible_at` =
        # الجلسة **التالية** ليوم الإشارة) — لا كلَّ يوم، وإلّا أقصينا الرابح لأنه
        # ارتفع (وارتفاعُه هو المطلوب).
        _days = sorted(sess)
        if _days and EX.scale_mismatch(sess[_days[0]], a["trade"].get("entry"),
                                       SCALE_TOL):
            cov["scale_bad"] += 1
            continue
        fired, quiet = [], []
        # 🔴 الحاجز **يتجدّد يوميًّا بإغلاق الجلسة السابقة** — مطابقةً للتحديث اليوميّ
        #    في الإنتاج (يجري قبل الافتتاح فلا يقرأ إغلاق اليوم نفسه).
        lvl_of = session_levels(_days, sess, a["trade"], lv["break"])
        # 🔴 مسارٌ مسطَّح لكامل نافذة ARMED — الحسم يمتدّ **من يوم الزناد** كما سُجِّل،
        #    لا داخل جلسته وحدها (الانحراف الذي سحب أرقام التشغيلة الأولى).
        flat, base = [], {}
        for day in _days:
            base[day] = len(flat)
            flat.extend(sess[day])
        # 🔬 T-LABEL-AUDIT: الوسم على الجلسة النظامية (‏`flat`) مقابل **كلّ** الدقائق
        #    (‏`bars` كما وردت من Polygon = تشمل ما قبل الافتتاح وما بعد الإغلاق).
        _lab = EX.relabel(bars, flat, a["trade"].get("entry"), lv["stop"])
        if _lab:
            labels.append(dict(_lab, symbol=a["symbol"]))
        for day in _days:
            sb = sess[day]
            cov["sessions"] += 1
            brk = lvl_of[day]
            if brk > lv["break"]:
                cov["lifted"] += 1
            # 🔬 T-NEARMISS: الذراعان لا يفترقان إلا في **جانب الخطّ** — وشرطُ الحجم
            #    يُقيَّم بدالّة الإنتاج نفسها بمستوًى مخفَّض (لا إعادةَ تطبيقٍ يدويّ).
            _bt = EX.band_triggers(sb, brk, S._ignition_signal,
                                   vol_mult=S.CONFIG["IGNITION_VOL_MULT"])
            for _arm, _bucket in (("cross", ncross), ("miss", nmiss)):
                if _arm in _bt:
                    _j, _s = _bt[_arm]
                    _bucket.append(_one_event(
                        a["symbol"], day, sb, _j, _s, lv, f"N-{_arm.upper()}",
                        f"{day}|n", fwd=flat[base[day] + _j + 1:]))
            hit = EX.replay_trigger(sb, brk, S._ignition_signal,
                                    vol_mult=S.CONFIG["IGNITION_VOL_MULT"])
            if hit:
                fired.append((day, sb, hit))
            else:
                quiet.append(day)
                xc = EX.cross_trigger(sb, brk)
                if xc:
                    cross.append(_one_event(a["symbol"], day, sb, xc[0], xc[1],
                                            lv, "E-CROSS", f"{day}|x",
                                            fwd=flat[base[day] + xc[0] + 1:]))
        cov["trig"] += len(fired)
        cov["quiet"] += len(quiet)
        for day, sb, (i, sig) in fired:
            pk = f"{day}|{sb[i].get('mod')}"
            r = _one_event(a["symbol"], day, sb, i, sig, lv, "E-REAL", pk,
                           fwd=flat[base[day] + i + 1:])
            real.append(r)
            # ذراع E-CROSS على يوم الزناد أيضًا (نفس المستوى، بلا شرط الحجم)
            xc = EX.cross_trigger(sb, lvl_of.get(day, lv["break"]))
            if xc:
                cross.append(_one_event(a["symbol"], day, sb, xc[0], xc[1], lv,
                                        "E-CROSS", f"{day}|x",
                                        fwd=flat[base[day] + xc[0] + 1:]))
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
                                             "E-PSEUDO", pk,
                                             fwd=flat[base[pd] + j + 1:]))

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

    # ══════════ 🎚️ T-MANAGE-25 — على **نفس** الصفقات المُنفَّذة (بالبناء) ══════════
    if R and R["dec"]:
        pairs = [(r, r.get("net_r_b")) for r in R["dec"] if r.get("net_r_b") is not None]
        diffs = [{"symbol": r["symbol"], "net_r": b - r["net_r"]} for r, b in pairs]
        changed = [d for d, (r, b) in zip(diffs, pairs) if abs(d["net_r"]) > 1e-12]
        cb = EX.cluster_bootstrap_mean(diffs)
        med = sorted(d["net_r"] for d in diffs)
        med = med[len(med) // 2] if med else 0.0
        a_mean = sum(r["net_r"] for r, _ in pairs) / len(pairs) if pairs else 0.0
        b_mean = sum(b for _, b in pairs) / len(pairs) if pairs else 0.0

        def _cvar(vals, q=0.05):
            xs = sorted(vals)
            k = max(1, int(len(xs) * q))
            return sum(xs[:k]) / k if xs else 0.0
        cv_a = _cvar([r["net_r"] for r, _ in pairs])
        cv_b = _cvar([b for _, b in pairs])
        print(f"\n🎚️ T-MANAGE-25 (نفس الصفقات المُنفَّذة · {len(pairs)} صفقة):")
        print(f"  السياسة أ (خروجٌ كامل) = {a_mean:+.3f}R · "
              f"السياسة ب (‏75/25) = {b_mean:+.3f}R")
        print(f"  **الفرق المزدوج ب−أ = {cb['mean']:+.3f}R** · وسيط={med:+.3f} · "
              f"cluster 95%=[{cb['lo']:+.3f}, {cb['hi']:+.3f}] ({cb['k']} رمزًا) "
              f"· اختلفت ب عن أ في {len(changed)} صفقة")
        print(f"  CVaR5%: أ={cv_a:+.3f}R · ب={cv_b:+.3f}R "
              f"(الفرق {cv_b - cv_a:+.3f} · يلزم ألّا يسوء بأكثر من 0.10)")
        _by = {}
        for d in changed:
            if d["net_r"] > 0:
                _by[d["symbol"]] = _by.get(d["symbol"], 0.0) + d["net_r"]
        _top2 = sum(sorted(_by.values(), reverse=True)[:2])
        _tot = sum(_by.values())
        print(f"  حصّة أعلى اسمَين من الربح الإضافيّ: "
              f"{(_top2 / _tot * 100 if _tot > 0 else 0):.0f}%")
        _rs = {}
        for r, _ in pairs:
            _rs[r.get("b_reason")] = _rs.get(r.get("b_reason"), 0) + 1
        print("  أسباب خروج الربع: "
              + " · ".join(f"{k}={v}" for k, v in sorted(_rs.items())))
        print(f"  🧭 المعيار الرباعيّ (‏§⑤): ①تحسّن ≥0.15R ⇒ "
              f"{'✅' if cb['mean'] >= 0.15 else '🔴'} · ②الحدّ السفليّ >0 ⇒ "
              f"{'✅' if cb['lo'] > 0 else '🔴'} · ③موجب هذي السنة ⇒ "
              f"{'✅' if cb['mean'] > 0 else '🔴'} · ④CVaR لا يسوء >0.10 ⇒ "
              f"{'✅' if (cv_b - cv_a) >= -0.10 else '🔴'}")

    # ══════════ 🔬 T-NEARMISS — هل العبور نفسه يحمل معلومة؟ ══════════
    NC = _report("N-CROSS    (عبر بشعرة)    ", ncross)
    NM = _report("N-MISS     (وقف تحته بشعرة)", nmiss)
    if NC and NM:
        d = NC["cb"]["mean"] - NM["cb"]["mean"]
        pd2 = EX.paired_diff(NC["dec"], NM["dec"])
        print(f"\n🔬 T-NEARMISS: الفرق (‏N-CROSS − N-MISS) = {d:+.3f}R "
              f"· مزدوجًا داخل الرمز = {pd2['mean']:+.3f} "
              f"[{pd2['lo']:+.3f}, {pd2['hi']:+.3f}] · أزواج={pd2['n']}")
        n_ok = min(len(NC["dec"]), len(NM["dec"])) >= 30
        print(f"  🧭 المعيار (‏§①-ج): ①يحمل معلومة (‏≥+0.15R وحدٌّ سفليّ >0) ⇒ "
              f"{'✅' if (d >= 0.15 and pd2['lo'] > 0) else '🔴'} · "
              f"②لا يحمل شيئًا (فاصل داخل ±0.10R) ⇒ "
              f"{'✅' if (pd2['lo'] >= -0.10 and pd2['hi'] <= 0.10) else '🔴'} · "
              f"③غير ذلك ⇒ غير حاسم"
              + ("" if n_ok else "  ⚠️ **العيّنة دون 30 لذراع ⇒ يُعلَن «لا حكم»**"))

    # ══════════ 🔬 T-LABEL-AUDIT — هل عمانا عن الافتر يغيّر الوسم؟ ══════════
    if labels:
        n = len(labels)
        print(f"\n🔬 T-LABEL-AUDIT (‏{n} نافذة):")
        for t in (30.0, 50.0, 100.0):
            ap = sum(1 for x in labels if x["flips"][t]["appeared"])
            va = sum(1 for x in labels if x["flips"][t]["vanished"])
            print(f"  عتبة +{t:g}%: **ظهرت بالممتدّ {ap}** · اختفت {va} "
                  f"· صافي التغيّر {(ap + va) / n * 100:.1f}% من النوافذ")
        _pr = sum(x["reg"]["pre"] for x in labels) / n
        _pe = sum(x["ext"]["pre"] for x in labels) / n
        _sr = sum(x["reg"]["post"] for x in labels) / n
        _se = sum(x["ext"]["post"] for x in labels) / n
        _st = sum(1 for x in labels if x["stop_earlier"])
        print(f"  متوسط أقصى صعودٍ قبل الوقف: نظاميّ {_pr:.1f}% · ممتدّ {_pe:.1f}%")
        print(f"  «خرجنا ثم انفجر» (بعد الوقف): نظاميّ {_sr:.1f}% · ممتدّ {_se:.1f}%")
        print(f"  الوقف يُضرَب بالممتدّ ولا يُضرَب نظاميًّا: {_st} نافذة "
              f"({_st / n * 100:.1f}%)")
        _mx = max(((ap0 + va0) / n * 100) for ap0, va0 in
                  [(sum(1 for x in labels if x["flips"][t]["appeared"]),
                    sum(1 for x in labels if x["flips"][t]["vanished"]))
                   for t in (30.0, 50.0, 100.0)])
        print(f"  🧭 المعيار (‏§②-ب): أقصى تغيّرٍ عند عتبة = {_mx:.1f}% ⇒ "
              + ("🔴 **ماديّ (≥10%)** — الوسم السابق ناقص" if _mx >= 10 else
                 ("✅ هامشيّ (<3%) — المحور يُغلَق" if _mx < 3 else
                  "🟡 بين الاثنين — قرار المالك")))
        print("  ⚠️ **الوسم ليس ربحًا**: بلوغُ عتبةٍ بالافتر لا يعني إمكان البيع عندها "
              "(سيولة الممتدّ رقيقة).")

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
