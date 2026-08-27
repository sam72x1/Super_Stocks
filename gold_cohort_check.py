#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🥇🔎 تحقّقُ الكوهورت — «هل تُطابق آلةُ الدخول المنفجرين الذين نبّه عليهم
البوت؟» (‏§⑥ من `OPUS_GOLD_ENTRY_PACKAGE.md` · تنبّؤُ المالك: **‏90% فأكثر**).

🔴 **المقياسان يُطبَعان معًا أو لا رقمَ إطلاقًا:** الالتقاطُ وحدَه **غشٌّ
للمعيار** (درسُ `T-CLIFF`: أيُّ وصفةٍ فضفاضةٍ تلتقط 100% إن التقطت كلَّ
شيء) ⇒ **لوحةُ شاهدٍ إلزامية**: نفسُ الاختبار على مُنبَّهٍ عليهم **بلا سجلّ
انفجار**.

⚖️ **إعلانُ الدائرية (يُطبَع مع النتيجة حرفيًّا):** الكوهورتُ **مُختارٌ على
النتيجة** ⇒ هذا **تصديقٌ رجعيٌّ وتوصيفٌ لا معدَّلُ إصابة**، ولا يُشتقّ منه
«لو دخلنا لربحنا». الحاكمُ تجربةُ `gold_entry_prereg.md` والحصادُ الأماميّ.

🔴 **وتلوّثُ الشاهد مُعلَنٌ سلفًا:** سجلُّ الانفجارات أعمى عن حركاتٍ خارج
مسحه (‏8 من الأسماء الـ18 الموثَّقة بلا صفٍّ رغم حركاتٍ موثَّقة: WFF ‏+614%
· HCWB · CRE · LGHL · HODO · MIMI · WNW · MSS) ⇒ في الشاهد منفجرون
حقيقيّون، **واتّجاهُ الأثر معلوم: يجعل الآلةَ تبدو أقلَّ تمييزًا ممّا هي**
(تحفّظٌ ضدّنا لا معنا).

قراءةٌ فقط · خارج الفرز · لا `LOGIC_VERSION` · الإنتاجُ لا يستوردها.
"""
from __future__ import annotations

import json
import os
import sys

WINDOW = int(os.environ.get("GC_WINDOW") or 40)   # نافذةُ الفحص قبل المرجع
#            (‏افتراضُها 40 = `RB.WAIT` — والمدخلُ موصولٌ فليس ميتًا)
HOLD_MIN = 3         # ① «مراقبه لمدة 3 جلسات» (‏`press_radar.READY_HOLD`)


def _log(m):
    print(m, flush=True)


def _idx_before(df, date_str):
    """نقيّة: فهرسُ آخر بارٍ **قبل** التاريخ المرجعيّ (صارمًا) — لا نظر
    مستقبليّ: كلُّ ما بعده لا يُقرأ إطلاقًا. لا شيء ⇒ None."""
    try:
        want = str(date_str)[:10]
        out = None
        for k, d in enumerate(df.index):
            if str(d)[:10] < want:
                out = k
            else:
                break
        return out
    except Exception:                                            # noqa: BLE001
        return None


def machine_reads(df, ref_idx, window=WINDOW, hold_min=HOLD_MIN):
    """هل رأت الآلةُ «قاعًا جاهزًا» في النافذة قبل المرجع؟

    ترجع قاموسًا: `read` (‏أطلقت `press_read` أصلًا) · `ready` (‏+ حفظُ
    ثلاث جلسات = المرحلة ①) · `filled` (‏+ تعبئةُ سلّم فيصل **قبل** المرجع =
    المرحلة ②) · `group_free` (‏بوّابة ⑥) · وفهرسَ أوّل قراءةٍ جاهزة.
    🔒 تُنادى `press_read` و`faisal_ladder` و`fill_index` **بالاسم** من
    أدوات التجربة نفسِها — صفرُ منطقٍ مكرَّر."""
    import gold_entry_arms as GE                                 # noqa: PLC0415
    import press_radar as PR                                     # noqa: PLC0415
    # 🔴 **الشروطُ تُقيَّم على القراءة الواحدة لا مجموعةً:** جمعُها بـOR عبر
    #    قراءاتٍ مختلفةٍ يخلط «قراءةٌ خاليةٌ من قروب» بـ«قراءةٌ أخرى تعبّأت»
    #    فيَعِد بمطابقةٍ لم تقع في أيّ لحظة. `match` = اجتماعُها في قراءةٍ واحدة.
    out = {"read": False, "ready": False, "filled": False,
           "group_free": False, "match": False, "i": None, "hold": None}
    try:
        lo = df["Low"].values.astype(float)
        hi = df["High"].values.astype(float)
        cl = df["Close"].values.astype(float)
        op = df["Open"].values.astype(float)
    except Exception:                                            # noqa: BLE001
        return out
    start = max(int(ref_idx) - int(window) + 1, GE.PRESS_W + 1)
    for i in range(start, int(ref_idx) + 1):
        r = PR.press_read(df.iloc[:i + 1], w=GE.PRESS_W)
        if not r:
            continue
        out["read"] = True
        hold = int(r.get("hold_sessions") or 0)
        if hold < hold_min:
            continue
        out["ready"] = True
        if out["i"] is None:
            out["i"], out["hold"] = i, hold
        pl = float(r["press_low"])
        j_low = max(i - hold, 0)
        a_sit = min(j_low + 1, i)
        gf = bool(GE.osc_pct(hi, lo, a_sit, i) <= GE.GROUP_OSC_MAX
                  and not GE.group_candle(op, hi, lo, cl, a_sit, i))
        out["group_free"] = out["group_free"] or gf
        trF, _stF = GE.faisal_ladder(pl)
        # 🔒 التعبئةُ **قبل تاريخ المرجع** — `n = ref_idx + 1` فيُسمح ببارِ
        #    `ref_idx` نفسِه (وهو آخرُ بارٍ **قبل** الانفجار) ولا يُقرأ ما بعده.
        fj = GE.fill_index(lo, i, max(trF), WINDOW, int(ref_idx) + 1)
        filled = fj is not None
        out["filled"] = out["filled"] or filled
        if filled and gf:
            out["match"] = True          # اجتمعت في **قراءةٍ واحدة**
    return out


def _rows(path="gold_cohort.json"):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    coh = [(r["symbol"], r["expl_date"]) for r in d["gold_rows"]]
    coh += [(r["symbol"], r["expl_date"])
            for r in d["alert_after_explosion_rows"]]
    ctl = list(d["liq_anchored_no_explosion_record"])
    return coh, ctl, d


def main() -> int:
    import Super_stock as S                                      # noqa: PLC0415
    _log("=" * 78)
    _log("🥇🔎 تحقّقُ الكوهورت — الالتقاط مقابل الشاهد (‏§⑥)")
    _log("=" * 78)
    coh, ctl, d = _rows()
    _log(f"📦 الكوهورت {len(coh)} رمزًا (‏تقاطعُ المُنبَّه عليهم بالمنفجرين) ·"
         f" الشاهد {len(ctl)} (‏مرساةُ LIQ بلا سجلّ انفجار)")
    # مرجعُ الشاهد = أوّلُ تنبيهٍ له (لحظةٌ مقابلةٌ للحدث) — تُقرأ من الجدول
    # 🔒 مرجعُ الشاهد **حتميٌّ من توزيع الكوهورت نفسِه** (نمطُ `control_panel`
    #    المعتمَد): `sha256(الرمز)` يختار تاريخَ انفجارٍ من قائمة الكوهورت ⇒
    #    تعرّضٌ تقويميٌّ متكافئ، وقابليةُ إعادةِ إنتاجٍ بت-بت، وبلا انتقاء.
    import hashlib                                              # noqa: PLC0415
    _dates = sorted({r["expl_date"] for r in d["gold_rows"]
                     + d["alert_after_explosion_rows"]})

    def _ctl_ref(sym):
        h = int(hashlib.sha256(str(sym).encode()).hexdigest(), 16)
        return _dates[h % len(_dates)]
    syms = sorted({s for s, _ in coh} | set(ctl))
    _log(f"⬇️ تحميلُ التاريخ اليوميّ لـ{len(syms)} رمزًا …")
    hist = S.download_history(syms)
    _log(f"📊 وصل {len(hist)} إطارًا من {len(syms)}")
    res = {"coh": [], "ctl": []}
    miss = {"coh": [], "ctl": []}
    for grp, items in (("coh", coh),
                       ("ctl", [(s, _ctl_ref(s)) for s in ctl])):
        for sym, ref in items:
            df = hist.get(sym)
            if df is None or len(df) < 80:
                miss[grp].append(sym)
                continue
            ri = _idx_before(df, ref)
            if ri is None or ri < 45:
                miss[grp].append(sym)
                continue
            m = machine_reads(df, ri)
            res[grp].append((sym, ref, m))
    for grp, name in (("coh", "الكوهورت (منفجرون مُنبَّهٌ عليهم)"),
                      ("ctl", "الشاهد (مُنبَّهٌ عليهم بلا انفجار)")):
        r = res[grp]
        n = len(r)
        if not n:
            _log(f"\n⛔ {name}: صفرُ رموزٍ قابلةٍ للقياس — لا رقم.")
            continue
        rd = sum(1 for _, _, m in r if m["read"])
        rr = sum(1 for _, _, m in r if m["ready"])
        ff = sum(1 for _, _, m in r if m["filled"])
        gf = sum(1 for _, _, m in r if m["ready"] and m["group_free"])
        mt = sum(1 for _, _, m in r if m["match"])
        _log(f"\n📈 {name} — ن={n} (تعذّر {len(miss[grp])})")
        _log(f"   ① قراءةُ ضغطٍ في النافذة      : {rd:>4} = {100.0*rd/n:5.1f}%")
        _log(f"   ② + حفظُ ثلاث جلسات (المرحلة ①): {rr:>4} = {100.0*rr/n:5.1f}%")
        _log(f"   ③ + تعبئةُ سلّم فيصل قبل المرجع: {ff:>4} = {100.0*ff/n:5.1f}%")
        _log(f"   ④ + خلوٌّ من القروبات (بند ⑥)  : {gf:>4} = {100.0*gf/n:5.1f}%")
        _log(f"   ⑤ **مطابقةٌ كاملةٌ في قراءةٍ واحدة**: {mt:>4} = "
             f"{100.0*mt/n:5.1f}%   ← الرقمُ الحاكم للسؤال")
    if res["coh"] and res["ctl"]:
        for key, lbl in (("ready", "المرحلة ①"), ("filled", "المرحلة ②"),
                         ("match", "المطابقةُ الكاملة")):
            a = sum(1 for _, _, m in res["coh"] if m[key]) / len(res["coh"])
            b = sum(1 for _, _, m in res["ctl"] if m[key]) / len(res["ctl"])
            _log(f"\n🎯 {lbl}: الكوهورت {100*a:.1f}% مقابل الشاهد {100*b:.1f}%"
                 f" ⇒ الفارق {100*(a-b):+.1f} نقطة"
                 f" · الإثراء ×{(a/b if b > 0 else float('inf')):.2f}")
    _log("\n⚠️ الدائريّةُ مُعلَنة: الكوهورتُ مُختارٌ على النتيجة ⇒ **تصديقٌ"
         " رجعيّ لا معدَّلُ إصابة**. وتلوّثُ الشاهد مُعلَن (‏8 من 18 اسمًا"
         " موثَّقًا بلا صفِّ انفجارٍ رغم حركاتٍ موثَّقة) ⇒ الفارقُ **أرضيّة**.")
    _log("⚠️ ومرجعُ الشاهد مسحوبٌ حتميًّا (‏sha256) من **توزيع تواريخ**"
         " انفجارات الكوهورت — تعرّضٌ تقويميٌّ متكافئ، لا مرجعَ حدثٍ خاصّ به"
         " (لأنه بلا حدث): فرقُ طبيعةِ المرجع مُعلَنٌ لا يُطوى.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
