#!/usr/bin/env python3
"""🔒 `T-DATE-CANDLES` مُغلَقٌ إغلاقًا مُنفَّذًا (أمرُ المالك «ثم اقفل T-DATE-CANDLES» 2026-11-04 · `T_DATE_CANDLES_ADDENDUM_5.md §⑤`).

كلُّ أداةٍ في `fm_forensics/date_candles/` تنادي `gate()` أوّلَ `main` ⟵ تخرج 8 قبل أيّ عمليّة ما لم يكن الوضعُ إعادةً بايتًا
(`--check` · `table-check` · `levels-check`) أو `DATE_CANDLES_REOPEN=1` (يُقرأ «1» حرفيًّا · إقرارٌ بشروط الفتح الثلاثة لا التفاف).
"""
from __future__ import annotations

import os
import sys

REOPEN_ENV = "DATE_CANDLES_REOPEN"
CLOSED_RC = 8                      # غيرُ 0 (نجاح) · 1 (عدمُ تطابق) · 3 (F0 «لا قياس») · 9 (العقد)
OPEN_MODES = ("--check", "table-check", "levels-check")
TEXT = (
    "🔒 T-DATE-CANDLES مُغلَقٌ إغلاقًا مُنفَّذًا (2026-11-04 · أمرُ المالك «ثم اقفل T-DATE-CANDLES»).",
    "   ⚖️ الحكم: قنواتُ التأريخ الرجعيّ الأربع (مرساةُ السعر · بصمةُ المؤشّر · الشموع · الطابع) لا تحرّك العدَّ ④",
    "      («قبل الحركة» 4 · T-FSWEEP 0) — والقيدُ الحاكم الإرسالُ الأماميّ (الملحق 4 §⑦ · الملحق 5).",
    "   🔓 شروطُ الفتح ثلاثةٌ معًا: مصدرُ تأريخٍ جديدٌ لم يُقَس · تسجيلٌ مسبقٌ جديد · وإذنُ المالك.",
    "   ⚖️ والمفتاحُ DATE_CANDLES_REOPEN=1 إقرارٌ بالثلاثة لا التفافٌ عليها — ويُقرأ «1» حرفيًّا.",
    "   ✅ مفتوحٌ دائمًا: --check · table-check · levels-check (إعادةٌ بايتًا بلا كتابة).",
)


def gate(tool: str, argv=None):
    """None ⟵ امضِ · وإلّا رمزُ الخروج 8 بعد طباعة نصّ الإغلاق."""
    args = list(sys.argv if argv is None else argv)[1:]
    if any(a in OPEN_MODES for a in args):
        return None
    if os.environ.get(REOPEN_ENV) == "1":
        return None
    print(f"⛔ {tool}: " + "\n".join(TEXT))
    return CLOSED_RC
