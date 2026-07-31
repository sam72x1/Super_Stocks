#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🩺 مِجَسّ **الكون التاريخيّ الشامل للمشطوبة** (اقتراح المراجِع `§11.6`).

**السؤال:** هل نستطيع بناء كونٍ `point-in-time` **يشمل الرموز المشطوبة**؟
لأن **انحياز البقاء** هو أعرض حدود الصدق عندنا: كلُّ نتائجنا السالبة قد تكون أثرَ
قياسٍ على **الناجين وحدهم** — والمشطوبة هي بالضبط مَن انهار، فغيابُها يُحسِّن
الماضي بلا وجه حقّ.

**مِجَسّ جدوى لا فرضية** — لا تسجيل مسبق له ولا حكم: يسأل «هل البيانات موجودة؟»
ويطبع الجواب. فاشل-آمن · لا يكتب حالة · ولا يمسّ الإنتاج.
"""
from __future__ import annotations

import os
import sys
import time

import requests

API = "https://api.polygon.io/v3/reference/tickers"
DATES = ("2023-06-01", "2024-06-03", "2025-06-02")


def _page(params, key, cap=6):
    """يعدّ الرموز عبر الصفحات بسقفٍ (المِجَسّ يقيس الجدوى لا يبني الكون)."""
    n, url, seen = 0, API, []
    for _ in range(cap):
        try:
            r = requests.get(url, params=params, timeout=25,
                             headers={"Authorization": f"Bearer {key}"})
        except Exception as e:
            return None, f"شبكة: {type(e).__name__}", seen
        if r.status_code != 200:
            return None, f"HTTP {r.status_code}", seen
        j = r.json() or {}
        res = j.get("results") or []
        n += len(res)
        seen += [t.get("ticker") for t in res[:3]]
        url = j.get("next_url")
        if not url:
            break
        params = {}
        time.sleep(0.08)
    return n, None, seen[:6]


def run() -> int:
    key = os.environ.get("POLYGON_API_KEY", "").strip()
    print("🩺 مِجَسّ الكون التاريخيّ (هل يشمل المشطوبة؟)")
    if not key:
        print("⛔ لا مفتاح Polygon ⇒ لا قياس (فاشل-آمن، لا جواب مفبرك).")
        return 2
    ok = True
    for d in DATES:
        base = {"market": "stocks", "date": d, "limit": 1000,
                "type": "CS", "exchange": "XNAS"}
        n_act, e1, s1 = _page(dict(base, active="true"), key)
        n_ina, e2, s2 = _page(dict(base, active="false"), key)
        print(f"\n📅 {d}")
        print(f"   نشط  : {n_act if n_act is not None else '⛔ ' + str(e1)}"
              + (f"  (عيّنة: {', '.join(x for x in s1 if x)})" if s1 else ""))
        print(f"   مشطوب: {n_ina if n_ina is not None else '⛔ ' + str(e2)}"
              + (f"  (عيّنة: {', '.join(x for x in s2 if x)})" if s2 else ""))
        if n_ina is None or not n_ina:
            ok = False
    print("\n🧭 القراءة: وجودُ عددٍ موجب في «مشطوب» ⇒ **الكون الشامل قابل للبناء** "
          "⇒ يمكن إعادة الأساس بلا انحياز بقاء.\n"
          "   وغيابُه ⇒ الحدّ يبقى معلنًا ولا يُخفَّف بالتمنّي.")
    print("⚠️ المِجَسّ **مسقوف بالصفحات** فأرقامُه حدٌّ أدنى لا إحصاءً كاملًا.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
