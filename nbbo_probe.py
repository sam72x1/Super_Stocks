"""🔎 مِجَسّ مؤقّت — **هل لدينا تاريخ NBBO؟** (`/v3/quotes`)

**السبب (البند 3 من `COMMON_LINK_REPORT_FOR_OPUS.md` §⑥-مكرر):** الاعتقاد الموثّق في
`CLAUDE.md` أن «تدفق الأوامر **بلا تاريخ** فلا باكتيست» — والقاضي الخصومي كشف أنه
يخصّ **عمق الدفتر L2** حصرًا، أمّا **تاريخ NBBO** (أفضل طلب/عرض) فـ**لم يُفحص قطّ**.
والفرق قاطع: لو كان تاريخ NBBO متاحًا وعميقًا انفتح باب تجربة مسجَّلة (T-BOOK) تقيس
«جدار الطلب/العرض» تاريخيًّا — وهو أقرب ما نملك لقراءة فيصل «يفرّغ العروض».

**المِجَسّ يجيب أربعة أسئلة بالأرقام لا بالظنّ:**
① هل المنفذ مسموح لاشتراكنا أصلًا (‏200 مقابل 401/403)؟
② **كم يعود التاريخ**؟ يُفحص سلّم تواريخ (‏30 · 180 · 400 · 800 · 1200 يومًا) —
   وهذا هو الحاسم: تجاربنا تشترط **ثلاث سنوات** (‏≈1100 يوم) فما دون سنتين لا يكفي.
③ ما **شكل السجلّ** فعلًا (الحقول الموجودة) حتى تُبنى أي تجربة على العقد الحقيقي لا
   على تخمين — درسٌ مسجَّل: «المحلّل يُكتب من الشكل الحقيقي».
④ ما **كثافة** السجلّات في دقيقة واحدة (هل الحجم عمليّ لباكتيست سنوات؟).

⚠️ **مِجَسّ للقراءة ثم الحذف** (نفس نمط مِجَسّي SEC وChartExchange الموثّقين):
لا يكتب حالة · لا يمسّ الفرز · **لا يطبع المفتاح** · فاشل-آمن. يُحذف بعد قراءة حكمه.
"""
import datetime as dt
import json
import os
import sys

import requests

BASE = "https://api.polygon.io"
# سلّم التواريخ: الأعمق أولًا لا يهمّ — نفحص كلًّا ونطبع أول عمق نجح وآخر عمق فشل،
# فالحكم يصير «التاريخ يعود إلى ≥N يومًا» بدليل لا باستنتاج.
LADDER = [30, 180, 400, 800, 1200]
# رمزان مختلفان قصدًا: كبير سائل (شكل السجلّ وكثافته) + مغمور من نوع أسهمنا (هل
# التغطية تشمل الصغائر أصلًا — سؤال منفصل عن الصلاحية).
SYMS = ["AAPL", "APVO"]


def _probe(sym, days, key):
    """يفحص يومًا واحدًا (جلسة تداول مرجّحة) ويرجّع (حالة، عدد، أول سجلّ)."""
    day = dt.date.today() - dt.timedelta(days=days)
    while day.weekday() >= 5:                 # أقرب يوم عمل قبله (لا نضمن أنه ليس عطلة)
        day -= dt.timedelta(days=1)
    nxt = day + dt.timedelta(days=1)
    url = (f"{BASE}/v3/quotes/{sym}"
           f"?timestamp.gte={day.isoformat()}&timestamp.lt={nxt.isoformat()}"
           f"&limit=50&order=asc")
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=15)
    except Exception as e:                    # شبكة — ليس حكمًا على الصلاحية
        return ("net_error", type(e).__name__, None, day)
    if r.status_code != 200:
        # الرسالة قد تحمل سبب المنع («not entitled» مقابل «plan») — نطبعها مقتضبة.
        msg = ""
        try:
            msg = (r.json() or {}).get("message", "")[:140]
        except Exception:
            msg = r.text[:140]
        return (f"http_{r.status_code}", msg, None, day)
    j = r.json() or {}
    res = j.get("results") or []
    return ("ok", len(res), (res[0] if res else None), day)


def _minute_density(sym, key):
    """④ كثافة السجلّات: دقيقة واحدة من جلسة حديثة — يقيس الحجم العمليّ."""
    day = dt.date.today() - dt.timedelta(days=7)
    while day.weekday() >= 5:
        day -= dt.timedelta(days=1)
    # 15:00 UTC ≈ منتصف الجلسة الصيفية (بعد ساعة ونصف من الافتتاح) — نافذة دقيقة واحدة.
    a = f"{day.isoformat()}T15:00:00Z"
    b = f"{day.isoformat()}T15:01:00Z"
    url = (f"{BASE}/v3/quotes/{sym}?timestamp.gte={a}&timestamp.lt={b}"
           f"&limit=50000&order=asc")
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"}, timeout=20)
        if r.status_code != 200:
            return f"تعذّر ({r.status_code})"
        j = r.json() or {}
        n = len(j.get("results") or [])
        more = " (وفيه صفحة تالية ⇒ الرقم أرضية)" if j.get("next_url") else ""
        return f"{n} سجلًّا في دقيقة واحدة{more}"
    except Exception as e:
        return f"تعذّر ({type(e).__name__})"


def main():
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        print("⛔ لا مفتاح Polygon — المِجَسّ لا يستنتج شيئًا. (لا حكم)")
        return 2
    print("🔎 مِجَسّ تاريخ NBBO (`/v3/quotes`) — البند 3 من تقرير الرابط المشترك\n")
    verdict = {}
    for sym in SYMS:
        print(f"═══ {sym} ═══")
        deepest_ok, first_fail = None, None
        for days in LADDER:
            st, info, row, day = _probe(sym, days, key)
            if st == "ok":
                mark = "✅" if info else "⚪️ (صفر سجلّ — يوم عطلة أو بلا تغطية)"
                print(f"  ‏{days:>5}ي ({day}) → {mark} عدد={info}")
                if info:
                    deepest_ok = max(deepest_ok or 0, days)
                if row is not None and "shape" not in verdict:
                    verdict["shape"] = sorted(row.keys())
                    print(f"     ③ شكل السجلّ: {json.dumps(row, ensure_ascii=False)[:400]}")
            else:
                print(f"  ‏{days:>5}ي ({day}) → ❌ {st} · {info}")
                first_fail = first_fail or (days, st, info)
        verdict[sym] = {"deepest_ok_days": deepest_ok, "first_fail": first_fail}
        print(f"  ④ الكثافة: {_minute_density(sym, key)}\n")

    print("═══════════ الحكم ═══════════")
    for sym in SYMS:
        d = verdict[sym]["deepest_ok_days"]
        f = verdict[sym]["first_fail"]
        if d is None:
            print(f"  ‏{sym}: ❌ لا سجلّ NBBO تاريخيّ في أي عمق مفحوص"
                  + (f" (أول فشل: {f[1]} · {f[2]})" if f else ""))
        else:
            yrs = d / 365.0
            enough = "✅ يكفي للثلاث سنوات" if d >= 1100 else \
                     ("⚠️ سنتان أو أقل — تحت حدّنا الأدنى (ثلاث سنوات)" if d >= 700
                      else "⛔ أقصر من أن يُبنى عليه باكتيست")
            print(f"  ‏{sym}: أعمق نجاح **{d} يومًا** (≈{yrs:.1f} سنة) ⇒ {enough}")
    if verdict.get("shape"):
        print(f"  ③ الحقول المتاحة: {', '.join(verdict['shape'])}")
    print("\n⚠️ حدّ صدق: «صفر سجلّ» ≠ «ممنوع» — قد يكون اليوم عطلة أو الرمز بلا تغطية "
          "وقتها. الحكم يُبنى على **حالة HTTP** أولًا وعلى عدد السجلّات ثانيًا.")
    print("🧭 وهذا مِجَسّ **يُحذف بعد القراءة** — ولا يُبنى عليه كود إنتاج قبل تسجيل "
          "مسبق وموافقة المالك.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
