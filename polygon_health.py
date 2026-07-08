# -*- coding: utf-8 -*-
"""
==========================================================
🩺 فحص صحة اشتراك Polygon (Polygon Health) — أداة مستقلة
==========================================================
تجيب سؤال المستخدم «اشتراكي شغّال؟» بالدليل: تفحص المنافذ الثلاثة التي يعتمدها
البوت وترسل الحكم لتلغرام + سجل الأكشن:
  1) الصفقات التاريخية  /v3/trades          (رادار التجميع + T-ACC)
  2) شموع الدقيقة        /v2/aggs .. minute  (رادار الانطلاق + كنسة الدقيقة + بريماركت)
  3) NBBO اللحظي         /v2/last/nbbo       (تدفق الأوامر الحي)

**عرض/تشخيص فقط — لا تلمس الفرز ولا الحالة. لا تطبع المفتاح أبدًا.**
التشغيل: python polygon_health.py   (workflow: polygon_health.yml يدوي)
"""
import datetime as dt
import os
import time

import requests

try:
    import Super_stock as bot
except ImportError:
    import super_stock as bot

_SYM = "AAPL"                       # سهم سائل دائم التداول (فحص فقط)


def _check(name, url, key):
    """يفحص منفذًا واحدًا: (الاسم، ✓/❌/⚠️، وصف). لا يطبع المفتاح."""
    try:
        t0 = time.time()
        r = requests.get(url, headers={"Authorization": f"Bearer {key}"},
                         timeout=12)
        ms = int((time.time() - t0) * 1000)
        if r.status_code == 200:
            n = len(((r.json() or {}).get("results") or [])) \
                if isinstance((r.json() or {}).get("results"), list) else 1
            return name, "✅", f"يشتغل ({ms}م.ث · {n} نتيجة)"
        if r.status_code in (401, 403):
            return name, "❌", (f"رفض ({r.status_code}) — مفتاح غير صالح أو "
                                "الاشتراك لا يشمل هذا المنفذ")
        if r.status_code == 429:
            return name, "⚠️", "حدّ الطلبات (429) — المفتاح حي لكن مزدحم"
        return name, "⚠️", f"ردّ غير متوقّع ({r.status_code})"
    except Exception as e:
        return name, "⚠️", f"شبكة: {type(e).__name__}"


def main():
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    if not key:
        msg = ("🩺 <b>فحص اشتراك Polygon</b>\n❌ لا مفتاح POLYGON_API_KEY في "
               "الأسرار — أضِفه ثم أعد الفحص.")
        bot.log(msg)
        bot.send_telegram(msg + "\n\n" + bot.FOOTER)
        return
    today = dt.date.today().isoformat()
    week_ago = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    base = "https://api.polygon.io"
    checks = [
        _check("الصفقات التاريخية (تجميع/T-ACC)",
               f"{base}/v3/trades/{_SYM}?timestamp.gte={week_ago}&limit=5", key),
        _check("شموع الدقيقة (رادار الانطلاق/الكنسة/البريماركت)",
               f"{base}/v2/aggs/ticker/{_SYM}/range/1/minute/{today}/{today}"
               "?adjusted=true&sort=desc&limit=5", key),
        _check("NBBO اللحظي (تدفق الأوامر الحي)",
               f"{base}/v2/last/nbbo/{_SYM}", key),
    ]
    ok = sum(1 for _, s, _ in checks if s == "✅")
    verdict = ("✅ <b>الاشتراك شغّال بالكامل</b>" if ok == len(checks) else
               ("⚠️ <b>يشتغل جزئيًّا</b> — انظر التفاصيل" if ok else
                "❌ <b>الاشتراك لا يستجيب</b> — تحقّق من المفتاح/التجديد"))
    lines = [f"🩺 <b>فحص اشتراك Polygon</b> · {today}", verdict, ""]
    for name, st, detail in checks:
        lines.append(f"{st} {name}: {detail}")
    lines.append("")
    lines.append("ℹ️ البوت فاشل-آمن: أي منفذ متعطّل يُعرض «—» ولا يعيق الفرز.")
    msg = "\n".join(lines)
    bot.log(msg)
    bot.send_telegram(msg + "\n\n" + bot.FOOTER)


if __name__ == "__main__":
    main()
