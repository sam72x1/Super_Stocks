#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬📐 **أين يقع سهمٌ من كتالوج فيصل؟** — مِجَسٌّ تشخيصيّ لا تجربةَ حكم.

**سؤالُ المالك (2026-08-16):** «لو تقاون شموعه وشرحه للمقطع بأسهم الكتالوج
فالمفروض تشوف فيه نقطة تشابه — لأنه الآن داخلٌ فيه ووقفه 1.6».

**الآلية — صفرُ منطقٍ مكرّر:** يقيس المعاييرَ الخمسةَ عشرَ بـ`measure_session`
**نفسِها** التي عايرت الظرف (‏`analyze_ticker` بكلّ البوّابات مُرخاة)، ثم يقارن
كلَّ معيارٍ بـ**وسيط الكاتالوج** و**حافّة الظرف** من `envelope_p100.json`.

⚖️ **ما يقوله وما لا يقوله:**
  · ✅ يقول: **أين يقع السهمُ من توزيع أسهم فيصل** معيارًا معيارًا.
  · ⛔ ولا يقول إنه سيربح — الكاتالوج **مختارٌ بعد الحدث**، والمقارنةُ **سهمٌ
    واحدٌ مقابل وسيط** لا اختبارَ دلالة.
  · ⛔ ولا يغيّر قرارًا: **عرض/تشخيص فقط** — خارج الفرز والجذور تمامًا.

التشغيل: `CMP_SYMS=RUBI,DRCT python3 catalog_compare.py`
"""
import json
import os
import sys

import catalog_envelope as CE
import Super_stock as S

ENV_FILE = os.environ.get("CMP_ENV_FILE", "envelope_p100.json")
SYMS = [s.strip().upper() for s in
        (os.environ.get("CMP_SYMS") or "RUBI").split(",") if s.strip()]

# 🎯 زنادُ دخول فيصل من تغريدة `DRCT` (‏`faisal_verbatim` — صورةُ المالك):
#    «اختبرها **وثبت مع شورت اقل من 10K** ‏+ rsi اقل من 30».
#    ⚖️ **يُعرَض ولا يُنفَّذ** — شرطُ الـRSI ألغاه المالك بوّابةً (‏«الغ شرط rsi»)
#    وهذا **عرضٌ تشخيصيّ** لا بوّابة. والمصدرُ نظامُه «زنادُ دخولٍ لمتابَع».
FAISAL_RSI_ENTRY_MAX = 30.0


def _fmt(v):
    if v is None:
        return "—"
    if isinstance(v, (int, float)):
        return f"{v:,.2f}" if abs(v) < 1e6 else f"{v:,.0f}"
    return str(v)


def compare_one(vals: dict, edges: dict, median: dict) -> list:
    """يقارن قيمَ سهمٍ بالظرف والوسيط — **دالّةٌ نقيّة**.

    يرجّع صفوفًا `(اسم, قيمة, وسيطُ الكاتالوج, داخلَ الظرف؟, وصفٌ)`.
    🔒 **والمفقودُ يمرّ بفائدة الشك** (نفسُ قاعدة الفارز: مجهولٌ ≠ رفض)."""
    out = []
    for key, direction, label, _cfg in CE.CRITERIA:
        v = vals.get(key)
        med = median.get(key)
        edge = edges.get(key)
        if v is None:
            out.append((label, None, med, None, "لم يُقَس"))
            continue
        inside, why = True, ""
        if edge is not None:
            if direction == "lo" and v < edge:
                inside, why = False, f"تحت حدّ الظرف {_fmt(edge)}"
            elif direction == "hi" and v > edge:
                inside, why = False, f"فوق حدّ الظرف {_fmt(edge)}"
            elif direction == "both" and isinstance(edge, (list, tuple)):
                lo, hi = float(edge[0]), float(edge[1])
                if v < lo:
                    inside, why = False, f"تحت أرضية الظرف {_fmt(lo)}"
                elif v > hi:
                    inside, why = False, f"فوق سقف الظرف {_fmt(hi)}"
        if inside and med is not None:
            m = med[0] if isinstance(med, (list, tuple)) else med
            try:
                why = ("مطابقٌ للوسيط" if abs(v - float(m)) <= abs(float(m)) * 0.15
                       else ("فوق الوسيط" if v > float(m) else "تحت الوسيط"))
            except (TypeError, ValueError):
                why = ""
        out.append((label, v, med, inside, why))
    return out


def main() -> int:
    env = json.load(open(ENV_FILE, encoding="utf-8"))
    edges, median = env.get("edges", {}), env.get("soft_median", {})
    print(f"📐 الظرف: {ENV_FILE} · {env.get('n_symbols')} رمزًا من الكاتالوج "
          f"· as-of {env.get('asof')}")
    print(f"🎯 المقارنة: {', '.join(SYMS)}\n")

    data = S.download_history(SYMS)
    for sym in SYMS:
        df = (data or {}).get(sym)
        print("─" * 74)
        if df is None or len(df) < 60:
            print(f"⛔ {sym}: بياناتٌ غير كافية — لا يُقارَن")
            continue
        vals = CE.measure_session(S, sym, df)
        if not vals:
            print(f"⛔ {sym}: `measure_session` لم تُرجع قيمًا")
            continue
        rows = compare_one(vals, edges, median)
        n_in = sum(1 for _, _, _, ok, _ in rows if ok is True)
        n_out = sum(1 for _, _, _, ok, _ in rows if ok is False)
        print(f"🔬 {sym} — داخلَ الظرف {n_in} · خارجَه {n_out} "
              f"· لم يُقَس {len(rows) - n_in - n_out}")
        for label, v, med, ok, why in rows:
            mark = "✅" if ok is True else ("❌" if ok is False else "ℹ️")
            m = med[0] if isinstance(med, (list, tuple)) else med
            print(f"   {mark} {label:22} = {_fmt(v):>14}  "
                  f"· وسيطُ فيصل {_fmt(m):>12}  {why}")
        # 🎯 زنادُ فيصل — **عرضٌ لا حكم**
        rn = vals.get("rsi_now")
        try:
            bor = (S.ce_borrow_info(sym) or {}).get("shares_available")
        except Exception:                                        # noqa: BLE001
            bor = None
        print(f"   🎯 زنادُ فيصل (عرضٌ لا بوّابة): RSI الآن {_fmt(rn)} "
              + ("✅ تحت 30" if rn is not None and rn < FAISAL_RSI_ENTRY_MAX
                 else "❌ ليس تحت 30" if rn is not None else "—")
              + f" · المتاح {_fmt(bor)} "
              + ("✅ تحت 10 آلاف" if bor is not None and bor < 10_000
                 else "❌ فوق 10 آلاف" if bor is not None
                 else "— (تعذّر الجلب · تعذّرٌ ليس صفرًا)"))
    print("─" * 74)
    print("⚠️ **حدودٌ تُقرأ مع الأرقام:** الكاتالوج **مختارٌ بعد الحدث** · "
          "والمقارنةُ **سهمٌ واحدٌ مقابل وسيط** لا اختبارَ دلالة · "
          "والتعريفاتُ تعريفاتُنا · ولا يُدَّعى منها عائد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
