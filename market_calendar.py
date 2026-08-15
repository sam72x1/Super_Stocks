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
    # ---- 2027 (أُضيفت 2026-08-15، خطة 014 — قبل نفاد المدى بأربعة أشهر) ----
    # ⚠️ **تُتحقَّق من جدول NYSE/Nasdaq الرسميّ قبل الاعتماد** (مصدرُها اشتقاقٌ
    # من قاعدة العطل الأمريكية: ما وقع سبتًا يُلاحَظ الجمعةَ قبله، وما وقع أحدًا
    # يُلاحَظ الاثنينَ بعده). وحارسُ التقادم أدناه يجعل أيَّ نقصٍ **مسموعًا**.
    "2027-01-01",  # New Year's Day (جمعة)
    "2027-01-18",  # MLK Day
    "2027-02-15",  # Presidents' Day
    "2027-03-26",  # Good Friday (عيد الفصح 2027-03-28)
    "2027-05-31",  # Memorial Day
    "2027-06-18",  # Juneteenth مُلاحَظ (19 يونيو سبت)
    "2027-07-05",  # Independence Day مُلاحَظ (4 يوليو أحد)
    "2027-09-06",  # Labor Day
    "2027-11-25",  # Thanksgiving
    "2027-12-24",  # Christmas مُلاحَظ (25 ديسمبر سبت)
}

# الإغلاق المبكر (1:00pm نيويورك بدل 4:00pm) — ISO date → دقيقة الإغلاق بتوقيت نيويورك.
EARLY_CLOSES = {
    "2026-11-27": 13 * 60,   # اليوم التالي للثانكسجيفينغ
    "2026-12-24": 13 * 60,   # ليلة الميلاد
    "2027-11-26": 13 * 60,   # اليوم التالي للثانكسجيفينغ 2027
    # (لا إغلاقَ مبكرًا لليلة الميلاد 2027: 24 ديسمبر **عطلةٌ كاملة** لأن
    #  الميلاد وقع سبتًا · ولا لـ3 يوليو لأنه وقع سبتًا أيضًا.)
}

REGULAR_OPEN_NY_MIN = 9 * 60 + 30      # 09:30
REGULAR_CLOSE_NY_MIN = 16 * 60         # 16:00

# 🗓️ **مدى التغطية** (خطة 014 · 2026-08-15) — أقدمُ وأحدثُ سنةٍ يعرفها هذا
# التقويم. `session_info` كانت تُرجع «regular» لأيّ تاريخٍ مجهول ⇒ من أوّل يومٍ
# بعد المدى **تُقرأ كلُّ عطلةٍ يومَ تداولٍ صامتًا** (رادارُ الانطلاق يمشي على
# سوقٍ مغلق ويقرأ شمعةً بائتة). الآن: خارج المدى يُوسَم `beyond_calendar=True`
# **ويُعلَن**، فالتقادمُ يصير مسموعًا لا صامتًا.
CALENDAR_FIRST_YEAR = 2026
CALENDAR_LAST_YEAR = 2027
STALE_WARN_DAYS = 60      # قبل نفاد المدى بهذي المدّة يبدأ التحذير


def _year_of(date_iso):
    try:
        return int(str(date_iso)[:4])
    except (TypeError, ValueError):
        return None


def beyond_calendar(date_iso) -> bool:
    """هل التاريخ خارج مدى التقويم المعروف؟ (تاريخٌ تالفٌ = خارج المدى — لا نخمّن)"""
    y = _year_of(date_iso)
    return y is None or y < CALENDAR_FIRST_YEAR or y > CALENDAR_LAST_YEAR


def calendar_staleness(today_iso):
    """🩺 نقيّة: هل التقويم على وشك النفاد أو نفد؟ ترجّع dict فيه `stale` (نفد
    فعلًا) و`warn` (اقترب) و`message` عربيّة جاهزة للسجلّ/التنبيه، أو `None`
    داخل المدى بأمان. تُنادى من الرنرات فيصير التقادمُ **مسموعًا**."""
    y = _year_of(today_iso)
    if y is None:
        return {"stale": True, "warn": True, "days_left": None,
                "message": f"⚠️ تاريخٌ غيرُ صالح ({today_iso!r}) — تقويمُ السوق "
                           f"لا يستطيع الحكم؛ عُومل خارجَ المدى."}
    if y > CALENDAR_LAST_YEAR:
        return {"stale": True, "warn": True, "days_left": 0,
                "message": f"⚠️ تقويمُ السوق نفد: {today_iso} خارج المدى "
                           f"{CALENDAR_FIRST_YEAR}-{CALENDAR_LAST_YEAR} "
                           f"(نسخة {CALENDAR_VERSION}) ⇒ العطلاتُ تُقرأ أيامَ "
                           f"تداولٍ. حدِّث HOLIDAYS/EARLY_CLOSES."}
    if y == CALENDAR_LAST_YEAR:
        try:
            import datetime as _dt                              # noqa: PLC0415
            d = _dt.date.fromisoformat(str(today_iso)[:10])
            left = (_dt.date(CALENDAR_LAST_YEAR, 12, 31) - d).days
        except (TypeError, ValueError):
            left = None
        if left is not None and left <= STALE_WARN_DAYS:
            return {"stale": False, "warn": True, "days_left": left,
                    "message": f"⚠️ تقويمُ السوق ينفد بعد {left} يومًا "
                               f"(آخرُ سنةٍ مغطّاة {CALENDAR_LAST_YEAR}) — "
                               f"أضِف سنةَ {CALENDAR_LAST_YEAR + 1} قبل انقضائها."}
    return None


def session_info(date_iso):
    """يرجّع dict: `session_type (regular|early_close|holiday) · open_ny_min · close_ny_min ·
    calendar_version · beyond_calendar`. نقيّة/قابلة للاختبار.
    **العطلة: open/close = None** (لا جلسة).
    ⚠️ `beyond_calendar=True` ⇒ النوعُ «regular» **افتراضٌ لا معرفة** (خارج المدى)."""
    _far = beyond_calendar(date_iso)
    if date_iso in HOLIDAYS:
        return {"session_type": "holiday", "open_ny_min": None, "close_ny_min": None,
                "calendar_version": CALENDAR_VERSION, "beyond_calendar": _far}
    if date_iso in EARLY_CLOSES:
        return {"session_type": "early_close", "open_ny_min": REGULAR_OPEN_NY_MIN,
                "close_ny_min": EARLY_CLOSES[date_iso],
                "calendar_version": CALENDAR_VERSION, "beyond_calendar": _far}
    return {"session_type": "regular", "open_ny_min": REGULAR_OPEN_NY_MIN,
            "close_ny_min": REGULAR_CLOSE_NY_MIN,
            "calendar_version": CALENDAR_VERSION, "beyond_calendar": _far}


def is_trading_day(date_iso):
    """يوم تداول = ليس عطلة (لا يفحص عطلة نهاية الأسبوع — الكرون أيام العمل فقط)."""
    return date_iso not in HOLIDAYS
