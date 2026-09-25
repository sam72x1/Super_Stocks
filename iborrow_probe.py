#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🩺💧 مِجَسٌّ مؤقّت — هل لـiBorrowDesk **تاريخٌ يوميّ مؤرَّخ** للمتاح للاقتراض؟ (يُحذف بعد القراءة)

**السؤال وحدَه:** فرضيّةُ المالك «متاح <20k» على مراسي «هنا الدخول» حُكمت «لا قياس» في `T-OPLINK`
(‏39 مؤرَّخًا من 711) لأن المتاح «بلا تاريخ» (`short_thread_prereg.md §2` — والتدقيقُ هناك شمل
ChartExchange ولم يُسمِّ iBorrowDesk). و`Super_stock._parse_iborrow` يقرأ مفتاحَي `real_time`/`daily`
من ردّه ⇒ **هل `daily` سلسلةٌ مؤرَّخةٌ تغطّي 2026-08-17⟶اليوم لرموزنا؟** — شكلُ الردّ يُطبَع كما هو
(مفاتيح · أطوال · أوّلُ وآخرُ صفّ) **ولا يُحسب رقمُ فرضيّة ولا يُكتب شيء**.

🔒 قراءةٌ فقط · بلا سرّ · بلا تلغرام · لا يستورده الإنتاج · يُحذف بعد قراءة سجلّه (سابقةُ مِجَسّ ClinicalTrials).
"""
import json
import sys
import time

import requests

UA = {"User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                     "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"), "Accept": "application/json"}
# رموزٌ من مراسي T-OPLINK (قديمةٌ وحديثة) + حالاتُ المالك المسمّاة — سقفٌ مُعلَن 16 نداءً
SYMS = ["SXTC", "ONCO", "DSY", "WHLR", "GIPR", "ANPA", "BLOG", "NNNN", "SKYQ", "BTCS", "ONMD", "RDAC",
        "WXM", "MSS", "BAOS", "AAPL"]


def shape(js):
    out = {"keys": sorted(js.keys()) if isinstance(js, dict) else type(js).__name__}
    if isinstance(js, dict):
        for k in ("daily", "real_time"):
            v = js.get(k)
            if isinstance(v, list):
                out[k] = {"n": len(v), "first": v[0] if v else None, "last": v[-1] if v else None,
                          "fields": sorted(v[0].keys()) if v and isinstance(v[0], dict) else None}
            else:
                out[k] = type(v).__name__
    return out


def main() -> int:
    ok = cover = 0
    for sym in SYMS:
        try:
            r = requests.get(f"https://iborrowdesk.com/api/ticker/{sym}", headers=UA, timeout=15)
            st = r.status_code
            js = r.json() if st == 200 else None
        except Exception as e:                                       # noqa: BLE001
            print(f"{sym}: ⛔ {type(e).__name__}")
            continue
        if js is None:
            print(f"{sym}: HTTP {st} · {len(getattr(r, 'text', '') or '')} محرفًا")
            continue
        ok += 1
        s = shape(js)
        dates = []
        for row in (js.get("daily") or []):
            if isinstance(row, dict):
                dates.append(str(row.get("time") or row.get("date") or row.get("timestamp") or ""))
        span = (min(dates), max(dates)) if dates else None
        if span and span[0][:10] <= "2026-08-17" and span[1][:10] >= "2026-09-20":
            cover += 1
        print(f"{sym}: HTTP 200 · {json.dumps(s, ensure_ascii=False, default=str)[:900]} · مدى daily {span}")
        time.sleep(1.0)
    print(f"\n🏁 وصل {ok}/{len(SYMS)} · يغطّي daily ‏2026-08-17⟶2026-09-20: {cover} — "
          "شكلٌ لا حكم (أيُّ قياسٍ بعده عقدٌ مسجَّلٌ مسبقًا)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
