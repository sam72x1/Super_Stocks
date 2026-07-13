# -*- coding: utf-8 -*-
"""🔬 E2 (مراجعة Codex 4 · P1-6) — تقويم سوق **مثبَّت الإصدار** للعطلات والإغلاق المبكر.

`market_session_now` يشتق 09:30–16:00 نيويورك لكنه **لا يعرف العطلات ولا الإغلاق المبكر**، فقد
تُوصَف جلسة عطلة/مقصوصة بالمكتملة زورًا. هذا التقويم **مثبَّت الإصدار** (`CALENDAR_VERSION`) —
يُوثَّق مصدره ويُتحقَّق منه قبل الـconfirmatory. يرجّع `session_type = regular|early_close|holiday`.

⚠️ **البيانات لعام 2026 (تُتحقَّق قبل الـconfirmatory).** الإغلاق المبكر = 13:00 نيويورك (1pm).
🔒 قياس/سياق فقط — لا يمسّ الفرز/التنبيه/الاختيار · لا LOGIC_VERSION.
"""

CALENDAR_VERSION = "2026.1-us-nasdaq"
CALENDAR_SOURCE = "NYSE/Nasdaq holiday schedule 2026 (version-pinned; verify before confirmatory)"

# عطلات السوق الأمريكي 2026 (مغلق كليًّا) — ISO date.
HOLIDAYS = {
    "2026-01-01",  # New Year's Day (خميس)
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents' Day
    "2026-04-03",  # Good Friday
    "2026-05-25",  # Memorial Day
    "2026-06-19",  # Juneteenth
    "2026-07-03",  # Independence Day (مُلاحَظ — 4 يوليو سبت)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-12-25",  # Christmas
}

# الإغلاق المبكر (1:00pm نيويورك بدل 4:00pm) — ISO date → دقيقة الإغلاق بتوقيت نيويورك.
EARLY_CLOSES = {
    "2026-11-27": 13 * 60,   # اليوم التالي للثانكسجيفينغ
    "2026-12-24": 13 * 60,   # ليلة الميلاد
}

REGULAR_OPEN_NY_MIN = 9 * 60 + 30      # 09:30
REGULAR_CLOSE_NY_MIN = 16 * 60         # 16:00


def session_info(date_iso):
    """يرجّع dict: `session_type (regular|early_close|holiday) · open_ny_min · close_ny_min ·
    calendar_version`. نقيّة/قابلة للاختبار. **العطلة: open/close = None** (لا جلسة)."""
    if date_iso in HOLIDAYS:
        return {"session_type": "holiday", "open_ny_min": None, "close_ny_min": None,
                "calendar_version": CALENDAR_VERSION}
    if date_iso in EARLY_CLOSES:
        return {"session_type": "early_close", "open_ny_min": REGULAR_OPEN_NY_MIN,
                "close_ny_min": EARLY_CLOSES[date_iso], "calendar_version": CALENDAR_VERSION}
    return {"session_type": "regular", "open_ny_min": REGULAR_OPEN_NY_MIN,
            "close_ny_min": REGULAR_CLOSE_NY_MIN, "calendar_version": CALENDAR_VERSION}


def is_trading_day(date_iso):
    """يوم تداول = ليس عطلة (لا يفحص عطلة نهاية الأسبوع — الكرون أيام العمل فقط)."""
    return date_iso not in HOLIDAYS
