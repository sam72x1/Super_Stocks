#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🕵️ T-M13 — **سائقٌ ناقلٌ فقط** (`m13_prereg.md`): يشغّل أداة T-SHORT
المسجَّلة القائمة (`_bt_short_enrich` + `backtest_short_thread` داخل
`run_backtest`) على بِركة الإنتاج الجديدة — **صفر كود تحليلٍ جديد**.

وُلد لأن مدخل `bt_short` أُزيل من `backtest.yml` بسقف الـ25 مدخلًا؛ الضبط هنا
**قبل الاستيراد** وإلّا خرج العلمُ خاملًا (بصمة الـno-op الموثّقة).
🔒 بحث/قياس — صفر مسّ إنتاج."""
from __future__ import annotations

import os
import sys

os.environ["SCREENER_MODE"] = "BACKTEST"
os.environ["BT_SHORT"] = "1"         # 🕵️ الأداة المسجَّلة — تطبع وتُبرق بنفسها
os.environ["BT_POTENTIAL"] = "1"     # `exploded` يقرأ الحركة قبل الوقف

import Super_stock as S                                        # noqa: E402


def run() -> int:
    trades = S.run_backtest() or []
    known = [t for t in trades if t.get("short_at_signal") is not None]
    print(f"\n🕵️ T-M13: صفقات = {len(trades)} · بشورت مؤرَّخ = {len(known)} "
          f"· مجهول = {len(trades) - len(known)}")
    if trades and not known:
        print("⚠️ الشورت المؤرَّخ غائب عن الكلّ — تُقرأ رسالة الأداة أعلاه "
              "(«لا حكم») ولا تُفسَّر شرائح.")
    return 0


if __name__ == "__main__":
    sys.exit(run())
