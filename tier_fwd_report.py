#!/usr/bin/env python3
"""📏➡️ تقريرُ الحصاد الأماميّ للتصنيف — تنفيذُ `tier_fwd_prereg.md` حرفيًّا.

أمرُ المالك 2026-08-22: «قِس التصنيف أماميًّا».

🥇 **أوّلُ قياسٍ غيرِ دائريٍّ للتصنيف:** الصفوفُ سُجِّلت **قبل** أن تُعرَف
نتيجتُها (‏`record_tier_fwd` في مسار الإرسال الحيّ)، فالدائريّةُ **منتفيةٌ
بالبناء** — بخلاف كلّ رقمٍ تاريخيٍّ عن الفئات.

🔒 **مقياسٌ واحدٌ لا اثنان:** الحسمُ بـ`kasih_scan.resolve` **بالاسم**
(الخروجُ البنيويّ = إغلاقٌ دون قاع شمعة المِرساة · و`KASIH_PCT`=30) ·
والفواصلُ بـ`wilson` منها. **صفرُ رقمٍ مغروسٍ وصفرُ منطقٍ مكرّر.**

⚖️ **وطبقةُ الجلب ليست طبقةَ القياس:** الشموعُ من `/v2/aggs` **بـ
`adjusted=false` إلزامًا** — لأن `e5` المخزَّن في السجلّ **خام**، وتقسيمًا
عكسيًّا لاحقًا يُعيد Polygon تسعيرَ اليوم الماضي فيخالط مقياسان (درسُ
`T-GATE §⑨`).

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ وصفرُ كتابةِ حالة · بلا كرون · والإنتاجُ لا
يستوردها.

**رموزُ الخروج:** 0 التقريرُ صدر · 2 مدخلاتٌ ناقصة (سجلٌّ أو مفتاح).
"""

import json
import os
import sys
import time

import requests

from kasih_scan import KASIH_PCT, resolve, wilson       # المقياسُ الواحد
# 🔒 حدُّ «قوي» **من الإنتاج بالاسم** لا نسخةً — فلا يتفرّق تعريفان
#    (أمرُ المالك «نزّل الحد لـ2» 2026-08-22 مساءً).
from Super_stock import LIQ_TIER_STRONG_MIN as _STRONG_MIN

LEDGER = os.environ.get("TIER_FWD_LEDGER", "tier_fwd_ledger.jsonl")
TIERS = ("قوي", "متوسط", "ضعيف")
AR = {"قوي": "🥇 قوي", "متوسط": "🥈 متوسط", "ضعيف": "🥉 ضعيف",
      "غير مصنَّف": "◻️ غير مصنَّف"}

# 📏 أرضيةُ العقد §③ — رقمٌ **مُعادٌ** من `T-EXIT-STOP §V3` (‏40/فئة) لا مخترَع
MIN_PER_TIER = 40
SEP_MULT = 2.0            # «قوي ضِعفُ ضعيفٍ فأكثر» (العقد §③-2)


def load_ledger(path=None):
    """يقرأ السجلَّ ويُبقي **أوّلَ صفٍّ لكلّ (تاريخ، رمز)** (العقد §②).

    المسارُ يُحسَم **وقت النداء** لا وقت التعريف (درسُ `load_edges`)."""
    fp = LEDGER if path is None else path
    out, seen = [], set()
    try:
        with open(fp, encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    r = json.loads(line)
                except ValueError:
                    continue          # سطرٌ تالفٌ يُتخطّى ويُعَدّ أدناه
                k = (r.get("date"), r.get("symbol"))
                if k in seen or not all(k):
                    continue
                seen.add(k)
                out.append(r)
    except FileNotFoundError:
        return []
    return out


def fetch_day(sym: str, day: str, key: str, get=None):
    """شموعُ دقيقةِ يومٍ كاملٍ بترتيبٍ تصاعديّ — `adjusted=false` إلزامًا.

    ترجّع قائمةَ `(t, o, h, l, c, v)` أو `None` عند أيّ إخفاق (فاشلٌ-آمن:
    الصفُّ يُعَدّ **معلَّقًا** ولا يُنسَب لفئةٍ بالخطأ)."""
    g = requests.get if get is None else get
    try:
        url = (f"https://api.polygon.io/v2/aggs/ticker/{sym.upper()}"
               f"/range/1/minute/{day}/{day}"
               "?adjusted=false&sort=asc&limit=50000")
        r = g(url, headers={"Authorization": f"Bearer {key}"}, timeout=30)
        if getattr(r, "status_code", 0) != 200:
            return None
        res = (r.json() or {}).get("results") or []
        rows = [(int(b["t"]), float(b["o"]), float(b["h"]), float(b["l"]),
                 float(b["c"]), float(b.get("v") or 0.0))
                for b in res if b.get("t") is not None and b.get("c")
                is not None and b.get("l") is not None]
        return rows or None
    except Exception:                                            # noqa: BLE001
        return None


def outcome(row: dict, bars):
    """حسمُ صفٍّ واحد — بتعريفات العقد §② حرفيًّا.

    ترجّع `(الحالة، mg5، تشخيص)`:
    - **`kasih`** بلغ ‏+30% فوق `e5` قبل الخروج البنيويّ.
    - **`lost`** لم يبلغ · **`pending`** تعذّر الجلب أو غابت المِرساة.
    🔴 **وحالةٌ مُعلَنةٌ في العقد:** كُسر قاعُ المِرساة **قبل اكتمال الخمس**
    ⇒ `resolve` لا تُنتج `kasih30_from5` ⇒ **تُعَدّ `lost`** لأن المركزَ خرج
    بنيويًّا قبل أن يُبلَغ سعرُ الكرت — لا «معلَّقة».
    """
    if not bars:
        return ("pending", None, "تعذّر الجلب")
    try:
        a_ms = int(row["anchor_ms"])
        e5 = float(row["e5"])
        ap = float(row["anchor_price"])
    except (KeyError, TypeError, ValueError):
        return ("pending", None, "حقلٌ ناقص")
    res = resolve(bars, a_ms, ap)
    if res is None:
        return ("pending", None, "المِرساةُ غائبةٌ عن الشموع")
    # الحاكم: من **سعر الكرت المخزَّن** — أقصى قمّةٍ بعد اكتمال الخمس وقبل الخروج
    mx5, frozen, broke = None, False, False
    for t, _o, h, _l, c, _v in bars:
        if t <= a_ms:
            continue
        if not frozen and t < a_ms + 5 * 60_000:
            pass
        elif not frozen:
            frozen, mx5 = True, e5
        if mx5 is not None:
            mx5 = max(mx5, h)
        if c < res["anchor_low"]:
            broke = True
            break
    if mx5 is None:
        return ("lost", None,
                "كُسر قاعُ المِرساة قبل اكتمال الخمس" if broke else "نافذةٌ قصيرة")
    mg5 = (mx5 / e5 - 1.0) * 100.0 if e5 > 0 else None
    return (("kasih" if (mg5 is not None and mg5 >= KASIH_PCT) else "lost"),
            mg5, res.get("exit"))


def tier_of(row):
    """🔁 **الفئةُ تُعاد اشتقاقُها من المكوّنات المخزَّنة لا من الوسم المكتوب.**

    أمرُ المالك 2026-08-22 «اعتمد S2» بدّل تعريفَ «قوي» ⇒ صفوفٌ كُتبت قبله
    تحمل وسمًا بتعريفٍ آخر. **ولو جُمّعت بالوسم المكتوب لخلط السجلُّ
    تعريفَين** — وهو ما وعدتُ بمنعه حين قلتُ إن السجلَّ يخزّن المكوّناتِ
    الخام فيُعاد تسجيلُه **بأثرٍ رجعيّ**.

    ⇒ **محورٌ واحد** (عدّادُ المواصلة) مطابقٌ لـ`liq_tier` النافذة — مقفولٌ
    **سلوكيًّا** في السويّة على القيم صفر إلى أربع."""
    g = row.get("green")
    if g is None:
        return "غير مصنَّف"
    try:
        g = int(g)
    except (TypeError, ValueError):
        return "غير مصنَّف"
    return ("قوي" if g >= _STRONG_MIN
            else ("ضعيف" if g <= _STRONG_MIN - 2 else "متوسط"))


def _rate(k, n):
    return (k / n * 100.0) if n else 0.0


def _fmt(k, n):
    lo, hi = wilson(k, n)
    return f"{_rate(k, n):.1f}% ({k}/{n}) [{lo:.0f}·{hi:.0f}]"


def main() -> int:
    rows = load_ledger()
    if not rows:
        print(f"⛔ لا سجلَّ `{LEDGER}` أو هو فارغ — لا شيء يُحصَد بعد.")
        print("   ⏳ يمتلئ تلقائيًّا: صفٌّ لكلّ كرت `M5` يصل المالكَ.")
        return 2
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        print("⛔ لا `POLYGON_API_KEY` — الحسمُ يلزمه شموعُ الدقيقة.")
        return 2

    days = sorted({r["date"] for r in rows})
    print(f"📦 السجلّ: **{len(rows)} صفًّا** فريدًا (تاريخ، رمز) · "
          f"{len(days)} جلسة: {days[0]} ⟶ {days[-1]}")
    print(f"🔎 الحاكم: كاسح{KASIH_PCT:.0f} **من سعر كرت M5** · الخروجُ "
          "البنيويّ إغلاقٌ دون قاع المِرساة (‏`resolve` بالاسم)")
    print(f"⚖️ العقد §③: الأرضيةُ **{MIN_PER_TIER} محسومةً لكلّ فئة** · "
          f"والفصلُ **{SEP_MULT:.0f}×** مع فاصلَي ويلسون منفصلَين")

    tally = {t: {"k": 0, "n": 0, "pend": 0} for t in list(TIERS)
             + ["غير مصنَّف"]}
    notes, restamped = {}, 0
    for i, r in enumerate(rows, 1):
        bars = fetch_day(r["symbol"], r["date"], key)
        st, mg5, why = outcome(r, bars)
        t = tier_of(r)
        if r.get("tier") and r.get("tier") != t:
            restamped += 1
        if st == "pending":
            tally[t]["pend"] += 1
            notes[why] = notes.get(why, 0) + 1
        else:
            tally[t]["n"] += 1
            tally[t]["k"] += 1 if st == "kasih" else 0
        if i % 20 == 0:
            time.sleep(0.2)           # مجاملةُ معدّلٍ لا أكثر

    print(f"\n{'=' * 78}\n📊 الحصيلةُ حسب الفئة\n{'=' * 78}")
    for t in list(TIERS) + ["غير مصنَّف"]:
        d = tally[t]
        print(f"  {AR[t]}: {_fmt(d['k'], d['n'])}"
              + (f" · معلَّق {d['pend']}" if d["pend"] else ""))
    tot_n = sum(tally[t]["n"] for t in tally)
    tot_p = sum(tally[t]["pend"] for t in tally)
    print(f"  ➕ المجموع: محسوم {tot_n} · معلَّق {tot_p} "
          f"({_rate(tot_p, tot_n + tot_p):.1f}%)")
    for why, c in sorted(notes.items(), key=lambda x: -x[1]):
        print(f"     ↳ سببُ التعليق «{why}»: {c}")
    if restamped:
        print(f"  🔁 **أُعيد اشتقاقُ الفئة لـ{restamped} صفًّا** كُتب بتعريفٍ "
              "سابق (أمرُ «اعتمد S2») — فالسجلُّ لا يخلط تعريفَين.")

    print(f"\n{'=' * 78}\n⚖️ المعيارُ الثلاثيّ (العقد §③ — لا يُحرَّك)\n{'=' * 78}")
    short = [t for t in TIERS if tally[t]["n"] < MIN_PER_TIER]
    if short:
        need = " · ".join(f"{AR[t]} {tally[t]['n']}/{MIN_PER_TIER}"
                          for t in TIERS)
        print(f"  📏 الأرضيةُ لم تُبلَغ: {need}")
        print("  ⏳ **«لا حكم»** — يُطبَع العدّادُ وحدَه بنصّ العقد، ولا تُخفَّض "
              "الأرضيةُ ولا تُدمَج فئتان لتُبلَغ.")
        print("  🔒 والحكمُ يُكتب **مرّةً واحدة** عند بلوغها أوّلَ مرّة.")
        return 0

    r_q = _rate(tally["قوي"]["k"], tally["قوي"]["n"])
    r_m = _rate(tally["متوسط"]["k"], tally["متوسط"]["n"])
    r_w = _rate(tally["ضعيف"]["k"], tally["ضعيف"]["n"])
    c1 = r_q >= r_m >= r_w
    lo_q, _hi_q = wilson(tally["قوي"]["k"], tally["قوي"]["n"])
    _lo_w, hi_w = wilson(tally["ضعيف"]["k"], tally["ضعيف"]["n"])
    c2 = (r_q >= SEP_MULT * r_w) and (lo_q > hi_w)
    print(f"  ① الترتيب (قوي ≥ متوسط ≥ ضعيف): {r_q:.1f} · {r_m:.1f} · "
          f"{r_w:.1f} ⇒ {'✅' if c1 else '🔴'}")
    print(f"  ② الفصل: قوي {r_q:.1f}% مقابل ضعيف {r_w:.1f}% "
          f"(المطلوب {SEP_MULT:.0f}×) · ويلسون [{lo_q:.0f}·] مقابل "
          f"[·{hi_w:.0f}] ⇒ {'✅' if c2 else '🔴'}")
    print(f"  ③ الأرضية: {MIN_PER_TIER} لكلّ فئة ⇒ ✅")
    ok = c1 and c2
    print(f"\n  ⚖️ **الحكم: {'✅ يعبر — ويُقترَح سطرُ عرضٍ للمالك' if ok else '🔴 لا يعبر'}**")
    print("  🔒 سقفُ النجاح (§④): **سطرُ عرضٍ واقتراحٌ فقط** — ولا تحويلَ "
          "التصنيف إلى فلترٍ أو كتم، ولا إعادةَ تعريفٍ بعد الأرقام.")
    print("\n⚠️ حدودُ صدق (§⑥): لا دائريّة ✅ · «كاسح» لمسٌ لا تنفيذ · "
          "المقامُ ما سُلِّم بعد الفلتر · نظامٌ سوقيٌّ واحد.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
