#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""📒🗜️ **حاصِدُ قناة الضغط** — يجعل `press_radar_ledger.jsonl` **مقروءًا دليلًا**.

🔴 **لماذا وُلد (2026-08-29، أمرُ المالك «سجل حصاد الضغط»):** الرادارُ يكتب صفًّا لكلّ
كرتٍ **سُلّم فعلًا** منذ 2026-08-14، وبلغ **452 صفًّا** — **ولا قارئَ له في المستودع
كلِّه**: لا حقلَ نتيجةٍ فيه ولا دالّةَ حسم. و`T-PRESS-BT-2` نصَّت أن «أيَّ تنقيحٍ
بعدها **من سجلّ الحصاد الأماميّ حصرًا**» ⇒ **المصدرُ المعتمَدُ للتنقيح لم يكن قابلًا
للقراءة أصلًا**، فالوعدُ كان بلا آلةٍ خلفه.

⚖️ **وهو قارئٌ لا حَكَم — وهذا مقصودٌ لا نقص:** يحسم الصفوفَ ويطبع الشرائح، **ولا
يُصدر حكمًا على القناة**. أيُّ دعوى «الضغطُ يربح/لا يربح» تلزمها **تسجيلٌ مسبقٌ
جديد** بمقياسٍ وحدٍّ وأرضيةِ عيّنةٍ مثبَّتةٍ قبل الأرقام — وإلّا كان اختيارَ المقياس
بعد رؤية النتيجة. الأداةُ تطبع «لا حكم» دائمًا.

🔒 **مقياسٌ واحدٌ لا اثنان:** الخطّةُ `rebound_arms.mirror_plan` والحسمُ
`rebound_arms.resolve_episode` — **بالاسم**، وهما نفسُهما اللذان أنتجا الرقمَ المنشور
`HOLD3` ‏+0.174R في `press_prereg §⑬`. فلو كتبتُ حسمًا ثانيًا لصار على القناة رقمان.

🔒 **وبلا نظرٍ مستقبليّ بالبناء:** المِرساةُ `press_low` **مقروءةٌ من الصفّ المسجَّل
ليلتَها** لا محسوبةً اليوم، و`resolve_episode` تبدأ التعبئةَ من **الجلسة التالية**
(`i + 1`) — والكرتُ يصل بعد إغلاق افتر جلسةِ الصفّ ⇒ **يستحيل الدخولُ في جلسته**.

🛑🔴 **وذراعا الوقف — حدُّ صدقٍ يعلو الجدول:** `mirror_plan` تضع الوقفَ **‏7% تحت
القاع** وهو **وقفُ القياس** الذي أنتج `HOLD3` ‏+0.174R، **والمالكُ اعتمد 2026-08-27
وقفَ القاع نفسِه لقناة الضغط** (الكرتُ يطبعه). فلو حسمنا بواحدٍ فقط لكان الجدولُ إمّا
غيرَ قابلٍ للمقارنة بالمنشور أو غيرَ واصفٍ لِما يستعمله المالك. ⇒ **يُطبَع الاثنان
جنبًا إلى جنب**: `B0` وقفُ القياس (‏7% تحت) · **`B1` وقفُ القاع المعتمَد** — والدفعاتُ
**واحدةٌ في الذراعين** فالفارقُ **الوقفُ وحدَه**، ولا حكمَ على أيّهما.

🩺 **وحارسُ المقياس إلزاميّ:** السجلُّ يحمل أسعارًا **خامّة** ليلةَ التسجيل، والجلبُ
اليوم يعيد سلسلةً **معدَّلةً بالتقسيمات** ⇒ مقسَّمٌ عكسيًّا بعد التسجيل تصير مِرساتُه
بلا معنًى. فيُقارَن `close` المسجَّل بإغلاق يوم الجلسة المجلوب، والمتفرّقُ **يُستبعَد
بسببٍ مُسمًّى ويُعَدّ** (سابقة `scale_mismatch` في `T-SLIP`) — لا يُصحَّح ولا يُدفَن.

⛔ قراءةٌ فقط: لا يستورده الإنتاج · لا يكتب حالةً · لا يرسل تلغرام · لا يمسّ عتبة.
"""
import json
import os
import sys

LEDGER = os.environ.get("PRESS_LEDGER", "press_radar_ledger.jsonl")
SCALE_TOL = 0.15          # 🩺 حدُّ تفرّق المقياس — مُعادٌ من حارس `T-SLIP` لا مخترَع
READY_HOLD_DEFAULT = 3    # يُقرأ من الإنتاج؛ هذا ارتدادٌ فاشل-آمن فقط
SESSION_BACKSTEP_DAYS = 4  # 📅 مدى ردِّ ختمِ نهاية الأسبوع (عطلةٌ ممتدّة)
# 🔒 الحالاتُ القابلةُ للحسم — **مصدرٌ واحد**: ما ليس منها فهو استبعادٌ يُعَدّ
# ويُعلَن، فأيُّ سببٍ جديدٍ يُسمّى تلقائيًّا ولا يُسقَط صامتًا.
_RESOLVABLE = ("win", "loss", "no_fill", "open")


def load_ledger(path=LEDGER):
    """يقرأ الصفوف صفًّا صفًّا. السطرُ التالف **يُعَدّ ولا يُدفَن**."""
    rows, bad = [], 0
    try:
        with open(path, encoding="utf-8") as fh:
            for ln in fh:
                ln = ln.strip()
                if not ln:
                    continue
                try:
                    rows.append(json.loads(ln))
                except Exception:                                # noqa: BLE001
                    bad += 1
    except FileNotFoundError:
        return [], -1
    return rows, bad


def scale_verdict(rec_close, fetched_close, tol=SCALE_TOL):
    """🩺 هل السلسلةُ المجلوبةُ اليوم بمقياس الصفّ المسجَّل؟
    ترجع `True` متّسق · `False` متفرّق · `None` تعذّر الحكم (يُعَدّ ولا يُفترَض)."""
    try:
        a, b = float(rec_close), float(fetched_close)
        if a <= 0 or b <= 0:
            return None
        return abs(a - b) / a <= float(tol)
    except Exception:                                            # noqa: BLE001
        return None


def resolve_row(row, df, mirror=None, resolve=None):
    """يحسم صفًّا واحدًا بدوالّ الإنتاج. يرجّع dict فيه **ذراعا وقفٍ**:
    `outcome` (‏B0 = وقفُ `mirror_plan`، ‏7% تحت القاع — يقارَن بالمنشور) و
    `outcome_low` (‏B1 = **وقفُ القاع المعتمَد**). كلٌّ من `resolve_episode`:
    win | loss | no_fill | open — أو سببُ استبعادٍ مُسمًّى **يُكتَب في الذراعين
    معًا** فلا يختلف مقامُهما: `no_data` · `session_missing` · **`session_ahead`**
    (الجلسةُ بعد آخر بارٍ متاح ⇒ تُحسَم لاحقًا لا عطب) · `scale_mismatch` ·
    `scale_unknown` · `no_anchor`."""
    import rebound_arms as RB                                    # noqa: PLC0415
    mirror = mirror or RB.mirror_plan
    resolve = resolve or RB.resolve_episode
    out = {"symbol": row.get("symbol"), "session": row.get("session"),
           "hold": int(row.get("hold_sessions") or 0),
           "awake": bool(row.get("awake")), "swept": bool(row.get("swept_hold")),
           "src": row.get("src"), "outcome": None, "outcome_low": None,
           "bars_after": None, "window_full": None, "session_used": None,
           "has_wake": ("awake" in row)}
    try:
        anchor = float(row.get("press_low"))
        if anchor <= 0:
            out["outcome"] = out["outcome_low"] = "no_anchor"
            return out
    except Exception:                                            # noqa: BLE001
        out["outcome"] = out["outcome_low"] = "no_anchor"
        return out
    if df is None or len(df) == 0:
        out["outcome"] = out["outcome_low"] = "no_data"
        return out
    # 🔴📅 **ختمُ نهايةِ الأسبوع — عيبٌ كشفته التشغيلةُ الحيّة لا الاختبار:** قبل
    # إصلاح الاستدراك (2026-08-29) كان الرادارُ يختم الصفَّ بـ**تاريخ التشغيل** لا
    # بجلسة البيانات، وكرونُه 00:25/01:25 UTC ⇒ جلسةُ الجمعة تُختَم **السبت**.
    # والمقيسُ على السجلّ: **118 صفًّا من 452 (‏26%) بختمِ نهايةِ أسبوع** ⇒ كان
    # الحاصدُ يُسقط ربعَ السجلّ صامتًا تحت `session_missing`.
    # ✅ فيُردّ الختمُ إلى **آخر جلسةٍ في الفهرس عندها أو قبلها** بقيدٍ مُعلَن
    # (‏`SESSION_BACKSTEP_DAYS` أيامًا تقويميّة — يكفي عطلةَ نهاية أسبوعٍ ممتدّة)،
    # **وحارسُ المقياس يُصادق الرَّدَّ** (إغلاقُ الصفّ يجب أن يطابق إغلاقَ البار)
    # فردٌّ إلى بارٍ خاطئ يسقط `scale_mismatch` لا يمرّ. والعددُ **يُطبَع**.
    try:
        idx = [str(d)[:10] for d in df.index]
        want = str(row.get("session"))[:10]
        if want in idx:
            i = idx.index(want)
        else:
            import datetime as _dt                               # noqa: PLC0415
            # 🔎🔴 **الفحصُ قبل الرَّدِّ لا بعده — عيبٌ كشفه هذا العدّادُ نفسُه:**
            # ختمٌ **بعد** آخرِ بارٍ متاح يعني **أن الجلسةَ لم تصل بعد**، ولو
            # سُمح بالرَّدِّ لَوقع على بار **الأمس** (داخلَ مدى الاستدراك) فحُسم
            # الصفُّ على **مِرساةٍ أقدمَ بجلسةٍ كاملة** — **وحارسُ المقياس لا
            # يمسكه** (تسامحُه 15% يبتلع فرقَ يومٍ واحد). ⇒ يُعلَن ولا يُردّ،
            # ويُحسَم بإعادة التشغيل غدًا. **ومقيسٌ حيًّا:** تشغيلةُ 08-29 ردَّت
            # 55 صفًّا ختمُها 2026-08-28 إلى بارٍ أقدم بلا أن يعترضها شيء.
            if want > idx[-1]:
                out["outcome"] = out["outcome_low"] = "session_ahead"
                return out
            w = _dt.date.fromisoformat(want)
            cand = [k for k, d in enumerate(idx)
                    if 0 <= (w - _dt.date.fromisoformat(d)).days
                    <= SESSION_BACKSTEP_DAYS]
            if not cand:
                # ختمٌ **داخل** المدى بلا بارٍ قريب = عطبُ ختمٍ حقيقيّ
                out["outcome"] = out["outcome_low"] = "session_missing"
                return out
            i = max(cand)
            out["session_used"] = idx[i]
    except Exception:                                            # noqa: BLE001
        out["outcome"] = out["outcome_low"] = "session_missing"
        return out
    sv = scale_verdict(row.get("close"), df["Close"].values[i])
    if sv is not True:
        out["outcome"] = out["outcome_low"] = (
            "scale_mismatch" if sv is False else "scale_unknown")
        return out
    hi = df["High"].values.astype(float)
    lo = df["Low"].values.astype(float)
    tr, st = mirror(anchor)
    out["bars_after"] = len(df) - 1 - i
    # ⏳🔴 **«بلا تعبئة» قبل اكتمال النافذة ليست نتيجة:** `resolve_episode` تمسح
    # `min(i+1+wait, n)` فإن قصُر التاريخُ عن `wait` رجعت `no_fill` **وهي في الحقيقة
    # «لم تنتهِ نافذتُها بعد»** — والسجلُّ عمرُه جلساتٌ معدودة ⇒ كلُّ صفٍّ غيرِ مُعبَّأ
    # كان سيُطبَع «بلا تعبئة» فيُقرأ «الخطّةُ لا تُعبَّأ» وهو باطل. ⚖️ والمحرّكُ
    # **مجمَّدٌ لا يُمَسّ** (أنتج `HOLD3`) ⇒ الوسمُ هنا في القارئ لا فيه.
    out["window_full"] = out["bars_after"] >= int(getattr(RB, "WAIT", 40))
    # 🛑 ذراعان بنفس الدفعات: `B0` وقفُ القياس (‏7% تحت القاع — يُبقي المقارنةَ
    # مع `HOLD3` ‏+0.174R) · `B1` **وقفُ القاع المعتمَد** (قرارُ المالك 2026-08-27).
    out["outcome"] = resolve(hi, lo, i, tr, st)
    out["outcome_low"] = resolve(hi, lo, i, tr, anchor)
    return out


def _slice(name, res, key="outcome"):
    """سطرُ شريحة — يطبع المحسومَ والمعلَّق معًا فلا يُقرأ المعلَّقُ نجاحًا ولا فشلًا.
    `key` يختار ذراعَ الوقف: `outcome` = ‏7% تحت القاع · `outcome_low` = القاع نفسُه."""
    win = sum(1 for r in res if r.get(key) == "win")
    loss = sum(1 for r in res if r.get(key) == "loss")
    nf = sum(1 for r in res if r.get(key) == "no_fill")
    op = sum(1 for r in res if r.get(key) == "open")
    done = win + loss
    rate = f"{100.0 * win / done:.1f}%" if done else "—"
    return (f"  {name:<22} ن={len(res):<4} محسومة={done:<4} فائزة={win:<4} "
            f"خاسرة={loss:<4} بلا تعبئة={nf:<4} معلّقة={op:<4} نسبة={rate}")


def report(results, bad_lines=0):
    """يطبع التغطيةَ والشرائح — **ولا يحكم**. يرجّع القاموسَ المطبوع للأقفال."""
    try:
        import press_radar as PR                                 # noqa: PLC0415
        hold_min = int(PR.READY_HOLD)
    except Exception:                                            # noqa: BLE001
        hold_min = READY_HOLD_DEFAULT
    # 🔴 المستبعَدُ **مُكمِّلُ** الصالح لا قائمةً بيضاء — قائمةٌ بيضاءُ تنسى سببًا
    # جديدًا فتُسقط صفوفًا **صامتةً** (وقع: `session_ahead` لم يُعَدّ فبقي
    # 452−394=58 والمُعلَنُ 3). فالحسابُ يُغلق بالبناء: صالحٌ + مستبعَدٌ = الكلّ.
    usable = [r for r in results if r["outcome"] in _RESOLVABLE]
    excl = {}
    for r in results:
        if r["outcome"] not in _RESOLVABLE:
            excl[r["outcome"]] = excl.get(r["outcome"], 0) + 1
    done = [r for r in usable if r["outcome"] in ("win", "loss")]
    print("=" * 78)
    print("📒 حاصِدُ قناة الضغط — قراءةٌ لا حكم")
    print("=" * 78)
    print(f"🩺 التغطية: صفوفٌ {len(results)} · صالحةٌ للحسم {len(usable)} · "
          f"محسومةٌ {len(done)} · سطورٌ تالفة {bad_lines}")
    _nowake = [r for r in results if r.get("has_wake") is False]
    if _nowake:
        print(f"🧩 حقولُ الصحوة غائبةٌ عن {len(_nowake)} صفًّا (سُجّلت قبل شحنها) "
              "⇒ تُعَدّ «هادئ» و«لم يُكنس» **بالافتراض لا بالقياس** — "
              "فشريحتاهما تخلطان مقيسًا بغير مقيس.")
    _remap = [r for r in results if r.get("session_used")]
    if _remap:
        print(f"📅 صفوفٌ رُدَّ ختمُها إلى آخر جلسةٍ قبله: {len(_remap)} — ختمُ "
              "**تاريخِ التشغيل** قبل إصلاح الاستدراك (جلسةُ الجمعة تُختَم السبت)، "
              "وحارسُ المقياس يُصادق الرَّدّ.")
    if excl:
        print("   المستبعَدون بأسبابهم: "
              + " · ".join(f"{k}={v}" for k, v in sorted(excl.items()))
              + f" · المجموع {sum(excl.values())}"
              + f" (‏{len(usable)} + {sum(excl.values())} = {len(results)})")
    else:
        print("   المستبعَدون: صفر")
    _SL = [("الكلّ", usable),
           (f"حفظٌ {hold_min} فأكثر", [r for r in usable if r["hold"] >= hold_min]),
           (f"حفظٌ دون {hold_min}", [r for r in usable if r["hold"] < hold_min]),
           ("مستيقظ", [r for r in usable if r["awake"]]),
           ("هادئ", [r for r in usable if not r["awake"]]),
           ("كُنس بعد حفظ", [r for r in usable if r["swept"]])]
    for _key, _ttl in (("outcome", "🛑 B0 — وقفُ القياس (‏7% تحت القاع · يقارَن بـHOLD3)"),
                       ("outcome_low", "🛑 B1 — وقفُ القاع المعتمَد (قرارُ المالك 08-27)")):
        print("-" * 78)
        print(_ttl)
        for _n, _rs in _SL:
            print(_slice(_n, _rs, _key))
    print("-" * 78)
    # ⏳ المعلَّقُ بنيويٌّ لا عيب: نافذةُ التعبئة `WAIT` جلسةً ثم الحسمُ بعدها.
    import rebound_arms as RB                                    # noqa: PLC0415
    young = [r for r in usable if (r["bars_after"] or 0) < RB.WAIT]
    _prem = [r for r in usable
             if r.get("window_full") is False and r.get("outcome") == "no_fill"]
    _prem_low = [r for r in usable
                 if r.get("window_full") is False and r.get("outcome_low") == "no_fill"]
    print(f"⏳ صفوفٌ لم تكتمل نافذتُها بعد ({RB.WAIT} جلسة): {len(young)} من {len(usable)}"
          " — معلَّقةٌ بالبناء لا بعطل.")
    print(f"⏳🔴 ومنها «بلا تعبئة» ونافذتُها **لم تكتمل**: B0={len(_prem)} · "
          f"B1={len(_prem_low)} — **لا تُقرأ «الخطّةُ لا تُعبَّأ»**، فالمحرّكُ يرجّع "
          "`no_fill` حين ينفد التاريخُ قبل النافذة.")
    print("🛑 الذراعان بدفعاتٍ واحدة — الفارقُ **الوقفُ وحدَه**: `B0` يقارَن بالمنشور "
          "`HOLD3` ‏+0.174R · و`B1` يصف ما يستعمله المالك اليوم. ولا حكمَ على أيّهما.")
    print("⚖️ **لا حكم**: هذي قراءةٌ للسجلّ. أيُّ دعوى على القناة تلزمها تسجيلٌ مسبقٌ "
          "جديد بمقياسٍ وحدٍّ وأرضيةِ عيّنةٍ مثبَّتةٍ **قبل** الأرقام.")
    print("=" * 78)
    done_low = [r for r in usable if r.get("outcome_low") in ("win", "loss")]
    return {"rows": len(results), "usable": len(usable), "resolved": len(done),
            "resolved_low": len(done_low), "excluded": excl,
            "young": len(young), "premature_nofill": len(_prem),
            "remapped": len(_remap), "no_wake_fields": len(_nowake),
            "hold_min": hold_min}


def main() -> int:
    rows, bad = load_ledger()
    if bad == -1:
        print(f"⛔ لا سجلَّ حصاد على المسار {LEDGER}.")
        return 4
    if not rows:
        print("⛔ سجلُّ الحصاد فارغ — لا شيء يُقرأ (بصمةُ no-op لا نتيجة).")
        return 4
    import Super_stock as S                                      # noqa: PLC0415
    syms = sorted({str(r.get("symbol")) for r in rows if r.get("symbol")})
    print(f"📥 {len(rows)} صفًّا · {len(syms)} رمزًا فريدًا — يُجلَب التاريخ…")
    data = {}
    CH = 60
    for k in range(0, len(syms), CH):
        try:
            data.update(S.download_history(syms[k:k + CH]) or {})
        except Exception as e:                                   # noqa: BLE001
            print(f"⚠️ دفعةٌ تعذّرت ({k}): {e}")
    results = [resolve_row(r, data.get(str(r.get("symbol")))) for r in rows]
    report(results, bad_lines=bad)
    return 0


if __name__ == "__main__":
    sys.exit(main())
