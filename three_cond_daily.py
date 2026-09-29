# -*- coding: utf-8 -*-
"""🔎📬 «شروطُك الثلاثة» — رسالةٌ يوميّة **واحدة** بقسمين (💵 فوق الدولار · 🪙 سنتات) بالأسهم التي تطابق: RSI أقلّ من 33 ·
فلوت أقلّ من 4 ملايين · «الشورت» (المتاح) أقلّ من 20 ألفًا · **وثبات 5 جلسات فوق أدنى قاع · ولم تنفجر خلال آخر أسبوع** —
على كون البوت كلِّه **وتحت المتابعة ضمنًا**. **ولا يُذكر في الرسالة إلّا المطابقُ الكامل** — وما سواه عدّادٌ في التذييل واسمُه في السجلّ.

أمرُ المالك (2026-09-26): «أرسلها كل يوم و حتى الأسهم اللي تحت المتابعة يشملها الاداة» — بعد مسكته «rsi 51 ل mgn» ثمّ
«افحص البوت»: فحصُ الكون كلِّه (`36244720433`) وجد تاريخَ ياهو **غيرَ متّسقٍ مع التقسيمات في 39 من 3,390 رمزًا** (MGN منها)
⇒ **RSI من Polygon adjusted** (مصدرُ التقرير السابق نفسُه) **وياهو للتحقّق**.
🧭 **ثمّ أمرُه الثاني (2026-09-26 مساءً · بصورتَي SMX):** «عدل الاداة … تجيب أسهم السنتات و فوق الدولار في رسالة وحده لكن … لازم
لازم لازم توافق الشروط 3 و ثبات 5 جلسات» · «الفريم اليومي يستخدم للحساب عدد الجلسات الثبات و فريم 4 ساعات عشان نعرف بالضبط قيمة
ادنى قاع (SMX: ‏7.62 · جلسةٌ واحدة فقط فوقه)» · و«FGL نوع منفجر قبل اقل من اسبوع ومع ذلك حاسبه مع أسهم الارتكاز و هذا غلط».
🧭 **وأمرُه الثالث (2026-09-26 ليلًا):** «عدّل rsi بدال ما يكون تحت 30 يكون تحت 33 نفس شرط فيصل بالضبط … للصنفين» ⇒ حدُّ RSI
للأداة = **حدُّ فيصل في البوت بالاسم** `S.CONFIG["RSI_OVERSOLD"]` (‏`rsi_max` · النافذ 33 = وسيطُ **قاع** RSI في كاتالوج أسهمه ·
`FAISAL_ONLY`) للقسمين · و`OPL.RSI_OWNER` (‏30 · عقدُ `T-OPLINK`) **لا يُقرأ هنا ولا يُمَسّ** — 🔄 وتقريرا الأسبوع والفترة
على الحدّ نفسِه منذ 2026-09-29 (أمرُ المالك «وحد 33 في التقريرين» · `WW.rsi_max` · المصدرُ `S.CONFIG` نفسُه).
📺 **وأمرُه الرابع (2026-09-29 ليلًا · بعد انتهاء اشتراك Polygon):** «اشتراكي مخلص ولا راح اجدده حتى لو يتوقف التحديث اللحظي
المهم الاشعارات حقت الأدوات تكون مستمرة … و المهم تكون النتايج دقيقة يعني البيانات تاخذها من ترندق فيو مب ياهو» ⇒ **المصدرُ
الافتراضيّ `TC_SOURCE=tv`** (`tv_data.py`): الشموعُ اليوميّة (نظاميّةٌ مسوّاةٌ بالتقسيم `adjustment=splits` = Polygon
`adjusted=true`) وشموعُ الساعة الممتدّة من **مِقبس TradingView** بالتعريفات نفسِها ③ ⑨ ⑩ ⑫ · **والفلوتُ من ماسحه وحدَه**
(`float_shares_outstanding` — لا ياهو ولا ذاكرةُ البوت: المخزَّنُ يُطبع في السجلّ ولا يدخل الحكم) · **وتحقّقُ ياهو ⑦ يُستبدل**
بتحقّقٍ داخليّ: RSI الماسح **لجلسة الشموع نفسِها** (إغلاقُه = إغلاقُ الجلسة) مقابل RSI الشموع بـ`WW.RSI_TOL` — **قناةٌ ثانيةٌ من
المصدر نفسِه لا تحقّقٌ مستقلّ** (مِجَسّ `36646071838`: ‏`S.rsi` على شموعه = RSI ماسحه بفرقٍ أقصاه 0.006 · وMGN عند ياهو 25.0
وعنده 48.2) · وبلا 🩹 (لا مصدرَ ثانٍ يُصحَّح) · والمتاحُ ⑤ من ChartExchange كما هو · **و`TC_SOURCE=polygon` = المسارُ السابق
بت-بت** (يلزمه `POLYGON_API_KEY`). ⚠️ **حدُّ صدق:** TradingView **بلا واجهةٍ رسميّة** وأتمتتُه خلافُ شروط استخدامه ⇒ قد يُحجَب
أو تتغيّر واجهتُه بلا إنذار ⇒ قاطعُ دائرةٍ (`TVBreaker`) وحارسا تغطيةٍ (الماسح والشموع) ⟵ **سطرُ عطلٍ لا صمتٌ ولا «لا يوجد» كاذب**.

**التعريفات (مثبَّتةٌ قبل أيّ رقم — تعريفاتُ `watch_week_probe` بالاسم):**
① **الكون** = `S.get_universe()` ∪ القائمةُ والارتدادُ (`weekly_watchlist.json`) ∪ **تحت المتابعة** (`near_watch.json`).
② **الجلسة** = آخرُ جلسةٍ منتهية (`WW.last_closed_day`) · **والمجدولُ لا يُرسل إلّا إن كانت الجلسةُ اليومَ أو أمسَ بتوقيت نيويورك**
   (عطلةٌ ⇒ صمتٌ بسببٍ مطبوع لا تكرارُ رسالةٍ قديمة) · واليدويُّ بـ`force` يُرسل.
③ **RSI14** = `WW.rsi_at` (‏`S.rsi` على إغلاقات Polygon `adjusted=true` حتى إغلاق الجلسة · ‏21 فأكثر وإلّا مجهول) · **والسعر**
   = إغلاقُ الجلسة نفسِها (`WW.close_at` · آخرُ شمعة adjusted هي الخامّ بالبناء) · ورمزٌ بلا شمعةٍ في الجلسة ⇒ «بائت» ⇒ مجهول.
   **والفئة من السعر:** 🪙 سنتات = أقلّ من `PX.PX_MIN` (دولار) · 💵 فوق الدولار = دولارٌ فأكثر — **قسمان في رسالةٍ واحدة لا شرط**.
④ **الفلوت** = `S._yahoo_float(strict=True)` (‏`floatShares` وحدَه) ثمّ فلوتُ البوت المخزَّن بوسمه: القائمة ⟵ مخزنُ «تحت المتابعة»
   (مدخلُ `near_watch.json` · يومي منذ 2026-09-26 · أمرُ «احفظ فلوت تحت المتابعة») ⟵ `company_cache.json`.
⑤ **«الشورت»** = المتاح (`shares_available` · ChartExchange): صفُّ حصّاد اليوم (`S._harvested_borrow`) أوّلًا ثمّ
   `S.ce_borrow_info` **موزَّعًا على رنرات** (`need[shard::shards]` · حصّةُ الموقع ‏≈50 صفحة لكلّ رنر · #461) · والتعذّرُ
   يُطبع بسببه ولا يُعدّ «لا».
⑥ **الحكم** = `WW.conj` على `flags3` (RSI أقلّ من `rsi_max()` · والفلوتُ والمتاحُ من `WW.flags(...)` بالاسم — والسعرُ فئةٌ لا
   شرط): «نعم» الثلاثةُ معلومةٌ وعابرة · «لا» سقط شرطٌ معلوم · «مجهول» غيرُ ذلك.
⑦ **تحقّقُ ياهو** لكلّ مرشّح: `S.rsi` على `S.download_history` — فرقٌ **فوق نقطتين** (`WW.RSI_TOL`) ⇒ «⚠️ مشكوك» **لا يُذكر**
   (عدّادٌ في التذييل · والرقمان في السجلّ) · ومدى نسبة الإغلاقين فوق `SPLIT_RATIO` يُوسَم «تقسيمٌ غيرُ متّسق».
⑧ **حالتُه عند البوت** لكلّ سطر: القائمة (حالةُ المتابعة) · الارتداد · 👀 تحت المتابعة (أسبابُها من الملفّ) · أو ليس عند البوت.
⑨ **حارسُ التغطية:** شموعُ Polygon في الجلسة لأقلّ من `MIN_COVER` من الكون ⇒ **لا قائمة** بل سطرُ عطلٍ صريح (لا «لا يوجد» كاذب).
⑩ **الثبات** = `exact_low_stability`: **أدنى قاعٍ دقيق** في آخر `PIVOT_LOOKBACK` جلسة (بالاسم) = أدنى سعرٍ في الجلسة الممتدّة
   (‏`WW.EXT_FROM` ⟶ `WW.EXT_TO` نيويورك · البري والأفتر ضمنًا) من **شموع الساعة** مع أدنى شمعةٍ يوميّة — وهو أدنى ذيلٍ على فريم
   4 ساعات نفسُه (الصفقاتُ نفسُها · والساعةُ تحاذي نيويورك صيفًا وشتاءً بينما شموعُ Polygon بأربع ساعات تنزاح شتاءً إلى 03:00) ·
   ويومُه **أوّلُ** يومٍ بلغه («ما كسر القاع» لا «ما لمسه» — نصُّ فيصل `X_85_YMT`) · **والعدُّ جلساتٌ يوميّة بعد يوم القاع** ·
   «ثابت» = الإغلاقُ فوق القاع **و**مضت `STABILITY_REQ` (‏5 — أمرُ المالك) جلساتٍ فأكثر **بلا سقف** · وشموعُ الساعة المتعذّرة ⇒
   «تعذّر القاع الدقيق» لا تخمين. 🔒 **و`S.CONFIG["STABILITY_MIN"]` (‏3) للبوت لا يُقرأ هنا ولا يُمَسّ.**
⑪ **🩹 مصدرُ البوت:** رمزٌ استبدل `S.download_history` شموعَه بـPolygon (`S.SPLIT_REPAIR_LAST` · ياهو مختلُّ التقسيم) يُوسَم
   🩹 في سطره — فتحقّقُه بشموع البوت **ليس مستقلًّا** ويُقال ذلك ولا يُخفى.
⑫ **💥 «انفجر خلال آخر أسبوع»** = `recent_explosion`: في آخر `EXPLODE_WIN` جلسات (أسبوعُ تداول) بلغ سعرٌ (البري والنظاميّ
   والأفتر) **`EXPLOSION_PCT` بالمئة فأكثر** (‏50 — عتبةُ الانفجار بقرار المالك · بالاسم) فوق **أدنى إغلاقٍ قبله** بدءًا من إغلاق
   الجلسة التي تسبق الأسبوع — والأفترُ يُقاس على إغلاق يومه نفسِه · فيلتقط القفزةَ في يومٍ والصعودَ المتدرّجَ معًا ⇒ **لا يُذكر**.
⑬ **التتبّع** (`TC_TRACE` = رموزٌ بفاصلة): لكلّ رمزٍ مسمّى في السجلّ — RSI · السعر · الفئة · القاعُ الدقيق ويومُه ومصدرُه · عددُ
   جلسات الثبات · أقصى صعودٍ في الأسبوع — **وصفٌ لا يدخل عددًا**.

المراحل (`TC_STAGE`): `scan` (الشموعُ اليوميّة والساعة · الفلوت · التحقّق — من TradingView افتراضًا · أو Polygon وياهو بـ
`TC_SOURCE=polygon` ⟵ `tc_scan.json`) ⟶ `borrow` (المتاح لجزء الرنر ⟵ `tc_borrow_<n>.json`) ⟶ `send` (الحكم والرسالة) · و`all`
الثلاثُ في عمليّةٍ واحدة.
الخروج: 0 أُرسلت/طُبعت أو صمتُ عطلةٍ بسببه · 2 بلا مفتاح Polygon (مصدرُ `polygon` وحدَه) · 3 تغطيةٌ ناقصة (سطرُ العطل أُرسل) ·
4 لا جلسةَ في التقويم.
"""
import concurrent.futures as cf
import datetime as dt
import glob
import json
import os
import sys
import threading
import time

import pandas as pd

import Super_stock as S
import opentry_link_probe as OPL                                     # حدودُ المالك بالاسم
import prelink_probe as P                                            # ticker_daily_adj بالاسم
import prelink_px as PX                                              # PX_MIN بالاسم
import tv_data as TV                                                 # 📺 TradingView: الماسح والمِقبس (أمرُ المالك 2026-09-29)
import watch_week_probe as WW                                        # flags · conj · rsi_at · close_at بالاسم
from kasih_scan import NY

STAGE = (os.environ.get("TC_STAGE") or "all").strip()
SOURCE = (os.environ.get("TC_SOURCE") or "tv").strip().lower()      # 📺 «tv» افتراضًا · «polygon» حرفيًّا = المسارُ السابق بت-بت
DRY = (os.environ.get("TC_DRY") or "0").strip() == "1"
FORCE = (os.environ.get("TC_FORCE") or "0").strip() == "1"
SHARD = int(os.environ.get("TC_SHARD") or 0)
SHARDS = max(1, int(os.environ.get("TC_SHARDS") or 1))
STATE_FILE = os.environ.get("TC_STATE") or "tc_scan.json"
PARTS_GLOB = os.environ.get("TC_PARTS") or "tc_borrow_*.json"
MIN_COVER = 0.85                 # engineering — كحارس تغطية الصيّادين (‏85%)
CE_CAP = 45                      # engineering — تحت حصّة الموقع ‏≈50 صفحة/رنر (مقيس #461)
CE_PAUSE = 0.6                   # engineering — كحصّاد الاقتراض
WITNESS = "AAPL"                 # شاهدُ الحصّة: صفحتُه تعود دائمًا
SPLIT_RATIO = 1.5                # «تقسيمٌ غيرُ متّسق» — عتبةُ فحص البوت `36244720433`
WORKERS = 8
BREAKER_MIN = 32                 # engineering — رموزٌ مكتملةٌ قبل الحكم على المزوّد (قاطعُ الدائرة · 2026-09-29)
BREAKER_FAIL_RATIO = 0.9         # engineering — نسبةُ إخفاق `P._get` (بعد محاولاتها الأربع) التي تفتح القاطع
BREAKER_LAST = {}                # {"daily"|"hours": ملخّصُ آخر قاطع} — يُصفَّر في `stage_scan` قبل الجلب
NEAR_SHOW = 10                   # سقفُ سجلّ «سقطت بشرطٍ معلوم» — والقصُّ يُعلَن بعدده
STABILITY_REQ = 5                # 🧭 أمرُ المالك 2026-09-26: «لازم لازم لازم توافق الشروط 3 و ثبات 5 جلسات» (للأداة وحدَها ·
#                                  ويسنده نصُّ فيصل `X_85_YMT` «إذا ما كسر القاع أكثرَ من 5 جلسات» · و`STABILITY_MIN`=3 للبوت لا يُمَسّ)
EXPLODE_WIN = 5                  # 🧭 أمرُ المالك 2026-09-26: «FGL نوع منفجر قبل اقل من اسبوع … هذا غلط» — أسبوعُ تداول = 5 جلسات
HOURS_DAYS = 45                  # engineering — أيّامٌ تقويميّة لشموع الساعة: تغطّي `PIVOT_LOOKBACK` (‏25 جلسة) بعطلاتها
TRACE = tuple(x.strip().upper() for x in (os.environ.get("TC_TRACE") or "").split(",") if x.strip())
BOT_LABEL = {"stocks": "🎯 في قائمة البوت", "pullback": "🔁 في قائمة الارتداد"}
GATE_TXT = {"wait": "ينتظر الثبات", "boom": "انفجر خلال أسبوع", "nohour": "تعذّر القاع الدقيق"}
SRC_NAME = {"tv": "TradingView", "polygon": "Polygon"}
TV_COLS = ["name", "close", "RSI", "RSI[1]", "float_shares_outstanding"]   # حقولُ الماسح (مقروءةٌ حيًّا: مِجَسّ `36646071838`)
TV_WORKERS = 8                   # engineering — مِقابسُ متوازية: المِجَسُّ قاس 6 و12 مقبسًا ‏≈0.03ث/رمز · 100 من 100 بعد إعادةٍ واحدة
TV_DAILY_N = 400                 # engineering — شموعٌ يوميّة تغطّي `WW.HIST_DAYS` (‏400 يومٍ تقويميّ ‏≈276 جلسة) بهامش ثمّ تُقصّ عليه
TV_HOURS_N = 1000                # engineering — شموعُ ساعةٍ ممتدّة تغطّي `HOURS_DAYS` (‏1000 ÷ 16 ساعة ‏≈62 جلسة لأنشط سهم)
TV_SCAN_TRIES = 2                # engineering — محاولتا الماسح (طلبٌ واحد ‏≈1ث) قبل سطر العطل
PX_TOL = 1e-6                    # engineering — تطابقُ إغلاق الماسح وإغلاق الجلسة (نسبيّ) شرطُ مقارنة RSI الماسح


def log(msg=""):
    print(msg, flush=True)


# ─────────────────────────── نقيّة ───────────────────────────
def session_gate(cal, now_ny, force=False):
    """(الجلسة, يُرسَل؟, السبب) — الجلسةُ آخرُ جلسةٍ منتهية · والمجدولُ يُرسل إن كانت **اليومَ أو أمسَ** بتوقيت نيويورك
    (فتشغيلٌ بعد عطلةٍ لا يُعيد رسالةَ جلسةٍ قديمة) · و`force` يُرسل دائمًا."""
    sess = WW.last_closed_day(cal, now_ny)
    today = now_ny.date().isoformat()
    yday = (now_ny.date() - dt.timedelta(days=1)).isoformat()
    if sess is None:
        return None, False, "لا جلسةَ منتهية في التقويم"
    if force:
        return sess, True, "يدويّ (force)"
    if sess in (today, yday):
        return sess, True, "جلسةٌ جديدة"
    return sess, False, f"آخرُ جلسةٍ {sess} ليست اليومَ ولا أمسَ بتوقيت نيويورك (عطلة) — لا تكرار"


def source_of(x):
    """📺 «polygon» حرفيًّا (بلا حالةٍ ولا مسافات) ⟵ المسارُ السابق (Polygon اليوميّ والساعة · فلوتُ ياهو · تحقّقُ ياهو) بت-بت ·
    وأيُّ قيمةٍ غيرها ⟵ «tv» (الافتراضيّ بأمر المالك 2026-09-29)."""
    return "polygon" if str(x or "").strip().lower() == "polygon" else "tv"


def tv_float(sn):
    """فلوتُ TradingView من صفّ الماسح (`float_shares_outstanding`) ⟵ عددٌ موجب أو None (مجهولٌ لا صفر)."""
    try:
        f = float((sn or {}).get("float_shares_outstanding"))
    except (TypeError, ValueError):
        return None
    return f if f > 0 else None


def tv_ref_rsi(sn, px, tol=PX_TOL):
    """RSI الماسح **لجلسة الشموع نفسِها** ⟵ حقلُ "RSI" حين يطابق إغلاقُ الماسح إغلاقَ الجلسة `px` (نسبيًّا ضمن `tol`) · وإلّا
    None: الماسحُ على شمعةٍ أخرى (جلسةٌ جديدة فُتحت أو بياناتٌ متأخّرة) ⟵ **لا مقارنة ولا شكّ** (المجهولُ لا يصنع شكًّا ⑦).
    قناةٌ ثانيةٌ من TradingView نفسِه (الماسح مقابل المِقبس) — تُمسك خللَ البيانات أو الحساب **لا خطأَ المصدر كلِّه**."""
    try:
        c, r, p = float((sn or {}).get("close")), (sn or {}).get("RSI"), float(px)
    except (TypeError, ValueError):
        return None
    if r is None or p <= 0 or abs(c - p) > tol * p:
        return None
    try:
        return float(r)
    except (TypeError, ValueError):
        return None


def ratio_range(ya, pa):
    """مدى نسبة إغلاقات ياهو إلى Polygon على الأيّام المشتركة (الأكبرُ ÷ الأصغر) ⟵ None إن قلّت عن 20 يومًا ·
    و`ya`/`pa` = {تاريخ: إغلاق}. تقسيمٌ طبّقه مصدرٌ دون الآخر يرفعه فوق `SPLIT_RATIO` (الأرباحُ الموزّعة لا تصنع هذا)."""
    rs = [ya[d] / pa[d] for d in sorted(set(ya) & set(pa)) if ya[d] and pa[d] and ya[d] > 0 and pa[d] > 0]
    if len(rs) < 20:
        return None
    return max(rs) / min(rs)


def shard_of(need, shard, shards):
    """جزءُ الرنر من قائمة المتاح المطلوبة — `need[shard::shards]` (تقسيمٌ تامٌّ منفصل · كحصّاد الاقتراض)."""
    shards = max(1, int(shards))
    return list(need)[int(shard) % shards::shards]


def bot_label(sym, wl, nw):
    """حالةُ السهم عند البوت (عرضٌ فقط): القائمة (حالةُ المتابعة `WW.cont_label`) · الارتداد · تحت المتابعة (أسبابُها)."""
    out = []
    for sec in ("stocks", "pullback"):
        for e in (wl or {}).get(sec) or []:
            if e.get("symbol") == sym and (sec == "pullback" or e.get("status", "active") == "active"):
                tag = WW.cont_label(e) if sec == "stocks" else str(e.get("status") or "")
                out.append(f"{BOT_LABEL[sec]} ({tag})" if tag else BOT_LABEL[sec])
    n = (nw or {}).get(sym) if isinstance(nw, dict) else None
    if n:
        why = [str(x) for x in (n.get("outside") or [])][:2]
        out.append("👀 تحت المتابعة" + (": " + " · ".join(why) if why else ""))
    return " · ".join(out) or "ليس عند البوت"


def rsi_max():
    """حدُّ RSI للأداة ⟵ `S.CONFIG["RSI_OVERSOLD"]` **وقتَ النداء** (بالاسم لا رقمٌ مكتوب · النافذ 33 = وسيطُ قاع RSI في كاتالوج
    فيصل) — أمرُ المالك 2026-09-26 «تحت 33 نفس شرط فيصل بالضبط … للصنفين» · والمقارنةُ «أقلّ من» حصرًا («تحت 33»)."""
    return float(S.CONFIG["RSI_OVERSOLD"])


def flags3(r):
    """(RSI · الفلوت · المتاح) لصفٍّ فيه rsi · px · fl · av — RSI أقلّ من `rsi_max()` (حدُّ فيصل للأداة) · والفلوتُ والمتاحُ من
    `WW.flags(...)` بالاسم (`OPL.FLOAT_OWNER` · `OPL.AVAIL_OWNER`) · والمجهولُ None لا «لا». و`WW.flags` الأوّلُ **لا يُقرأ
    هنا** (حدُّ التقريرين `WW.rsi_max()` — والمصدرُ `S.CONFIG["RSI_OVERSOLD"]` نفسُه منذ 2026-09-29)."""
    rsi = r.get("rsi")
    f = WW.flags(rsi, r.get("px"), r.get("fl"), r.get("av"))
    return (None if rsi is None else float(rsi) < rsi_max(), f[1], f[2])


def verdict(r, tol=None):
    """(الحكم, مشكوك؟) لصفٍّ فيه rsi · px · fl · av · ry — `WW.conj` على `flags3` (RSI بحدّ فيصل `rsi_max()` · والفلوتُ والمتاحُ من
    `WW.flags` بالاسم — والسعرُ فئةٌ لا شرط: أمرُ المالك «تجيب أسهم السنتات و فوق الدولار في رسالة وحده») · والشكُّ = فرقُ RSI
    ياهو عن Polygon فوق `tol` نقطة (`WW.RSI_TOL`) · وياهو المجهولُ لا يصنع شكًّا (لا دليلَ نقيض)."""
    tol = WW.RSI_TOL if tol is None else tol
    v = WW.conj(flags3(r))
    ry, rp = r.get("ry"), r.get("rsi")
    doubt = ry is not None and rp is not None and abs(float(ry) - float(rp)) > tol
    return v, doubt


def px_class(px):
    """🪙 «سنتات» تحت `PX.PX_MIN` (دولار) · 💵 «دولار» دولارٌ فأكثر — من إغلاق الجلسة (الخامّ بالبناء) · None بلا سعر."""
    if px is None:
        return None
    return "penny" if float(px) < PX.PX_MIN else "dollar"


def ext_rows(hours, days=None):
    """شموعُ الساعة **داخل الجلسة الممتدّة** (`WW.EXT_FROM` ⟶ `WW.EXT_TO` نيويورك) ⟵ [(يومُ نيويورك, ms, high, low)] مرتّبةً
    زمنيًّا · و`days` (مجموعةُ أيّام) يقصرها عليها · والشمعةُ التالفة تُتخطّى لا تُخمَّن. و`hours` = [(ms, high, low)]."""
    lo_h = WW.EXT_FROM[0] + WW.EXT_FROM[1] / 60.0
    hi_h = WW.EXT_TO[0] + WW.EXT_TO[1] / 60.0
    out = []
    for b in hours or []:
        try:
            ms, h, lo = int(b[0]), float(b[1]), float(b[2])
        except (TypeError, ValueError, IndexError):
            continue
        t = dt.datetime.fromtimestamp(ms / 1000.0, tz=NY)
        hh = t.hour + t.minute / 60.0
        d = t.date().isoformat()
        if lo_h <= hh < hi_h and (days is None or d in days) and lo > 0 and h > 0:
            out.append((d, ms, h, lo))
    return sorted(out, key=lambda x: x[1])


def exact_low_stability(daily, hours, sess, need=None, look=None):
    """🔻 **أدنى قاعٍ دقيق وثباتُه** (أمرُ المالك: «الفريم اليومي يستخدم للحساب عدد الجلسات الثبات و فريم 4 ساعات عشان نعرف
    بالضبط قيمة ادنى قاع») ⟵ {pivot · pivot_date · bars_after · held · need · stable · ext · daily_low} أو None.

    القاعُ = أدنى سعرٍ في آخر `look` جلسة (`PIVOT_LOOKBACK` بالاسم) من **شموع الساعة الممتدّة** (البري والأفتر) **ومن الشمعة
    اليوميّة** معًا (الساعةُ تحوي النظاميّة بالبناء · واليوميّةُ أرضيّةٌ لو نقصت ساعة) · ويومُه **أوّلُ** يومٍ بلغه (لمسُه ثانيةً
    ليس كسرًا — «ما كسر القاع» `X_85_YMT`) · و`bars_after` = الجلساتُ اليوميّة المكتملة **بعد** يوم القاع حتى `sess` ·
    و«ثابت» = إغلاقُ `sess` فوق القاع **و**`bars_after` من `need` (‏`STABILITY_REQ`) فأكثر بلا سقف · و`ext` = القاعُ من خارج
    الجلسة النظاميّة (أدنى من كلّ شمعةٍ يوميّة). **بلا شمعة ساعةٍ واحدةٍ في النافذة ⟵ None** (القاعُ الدقيق لم يُقَس فلا يُخمَّن)."""
    try:
        need = STABILITY_REQ if need is None else int(need)
        look = int(S.CONFIG["PIVOT_LOOKBACK"]) if look is None else int(look)
        cut = [r for r in (daily or []) if r[0] <= sess]
        if len(cut) < 2:
            return None
        win = cut[-look:]
        days = [r[0] for r in win]
        ext = ext_rows(hours, set(days))
        if not ext:
            return None
        cands = [(r[0], float(r[3])) for r in win if float(r[3]) > 0] + [(d, lo) for d, _ms, _h, lo in ext]
        low = min(x for _d, x in cands)
        day = min(d for d, x in cands if x <= low)
        d_low = min(float(r[3]) for r in win if float(r[3]) > 0)
        after = sum(1 for d in days if d > day)
        held = float(cut[-1][4]) > low
        return {"pivot": low, "pivot_date": day, "bars_after": after, "held": held, "need": need,
                "stable": held and after >= need, "ext": low < d_low, "daily_low": d_low}
    except Exception:                                                # noqa: BLE001
        return None


def recent_explosion(daily, hours, sess, win=None, pct=None):
    """💥 **انفجر خلال آخر أسبوع؟** (أمرُ المالك: «FGL نوع منفجر قبل اقل من اسبوع … هذا غلط») ⟵ {pct · day · ref · peak ·
    boom} أو None. في آخر `win` جلسات (`EXPLODE_WIN`) أقصى ارتفاعٍ لسعرٍ (البري والنظاميّ من شموع الساعة ومن أعلى الشمعة
    اليوميّة · والأفتر) فوق **أدنى إغلاقٍ نظاميٍّ قبله** بدءًا من إغلاق الجلسة التي تسبق الأسبوع — والأفترُ يُقاس على إغلاق يومه
    نفسِه (`WW.close_utc` يعرف الإغلاقَ المبكّر) · و«انفجر» = `pct` من `EXPLOSION_PCT` (بالاسم · قرارُ المالك «قفزة ≥50% =
    انفجار») فأكثر. يلتقط قفزةَ اليوم الواحد والصعودَ المتدرّجَ معًا (مرجعُه أدنى إغلاقٍ لا إغلاقُ الأمس وحدَه)."""
    try:
        win = EXPLODE_WIN if win is None else int(win)
        thr = float(S.CONFIG["EXPLOSION_PCT"]) if pct is None else float(pct)
        cut = [r for r in (daily or []) if r[0] <= sess]
        if len(cut) < win + 1:
            return None
        ref = float(cut[-win - 1][4])
        if ref <= 0:
            return None
        wk = cut[-win:]
        ext = ext_rows(hours, {r[0] for r in wk})
        best = (-1e9, None, None, None)
        for r in wk:
            d, close_d = r[0], float(r[4])
            cms = WW.close_utc(d).timestamp() * 1000.0
            pre = [h for dd, ms, h, _lo in ext if dd == d and ms < cms] + [float(r[2])]
            aft = [h for dd, ms, h, _lo in ext if dd == d and ms >= cms]
            for peak, base in ((max(pre), ref), (max(aft) if aft else None, min(ref, close_d))):
                if peak is None or base <= 0:
                    continue
                rise = (peak / base - 1.0) * 100.0
                if rise > best[0]:
                    best = (rise, d, base, peak)
            ref = min(ref, close_d)
        if best[1] is None:
            return None
        return {"pct": best[0], "day": best[1], "ref": best[2], "peak": best[3], "boom": best[0] >= thr}
    except Exception:                                                # noqa: BLE001
        return None


def gate_of(stab, boom):
    """بوّابةُ الثبات والانفجار ⟵ "ok" · "nohour" (القاعُ الدقيق لم يُقَس) · "boom" (انفجر خلال أسبوع) · "wait" (لم يثبت
    `STABILITY_REQ` جلسات) — **بهذا الترتيب** فيُعدّ السهمُ مرّةً واحدة في التذييل."""
    if not stab:
        return "nohour"
    if boom and boom.get("boom"):
        return "boom"
    if not stab.get("stable"):
        return "wait"
    return "ok"


def stab_text(r):
    """نصُّ الثبات في سطر السهم (عرضٌ فقط) — القاعُ بدقّة السعر (`S._px_txt`) ويومُه و«بري/أفتر» إن كان من خارج الجلسة."""
    t = r.get("stab")
    if not t:
        return "القاعُ الدقيق لم يُقَس"
    low = f"{S._px_txt(t['pivot'])} ({t['pivot_date']}{' · بري/أفتر' if t.get('ext') else ''})"
    if t["stable"]:
        return f"ثابتٌ {t['bars_after']} جلسات فوق أدنى قاع {low}"
    if t["bars_after"] >= t["need"]:
        return f"الإغلاقُ عند أدنى قاع {low} — لم يثبت فوقه"
    return f"أدنى قاع {low} · مضى {t['bars_after']} من {t['need']} جلسات"


def near_misses(rows):
    """🔸 (سجلٌّ فقط) أسهمُ البوت (القائمة · الارتداد · تحت المتابعة) التي عبرت الثبات وسقطت **بشرطٍ واحدٍ والباقيان معلومان
    وعابران** ⟵ [(رمز, السبب)] — تجيب «ليه ما ذكرت سهمي؟» في السجلّ **لا في الرسالة** (أمرُ المالك «لازم لازم لازم توافق»)."""
    out = []
    names = ("RSI", "الفلوت", "المتاح")
    for s in sorted(rows, key=lambda x: rows[x].get("rsi") if rows[x].get("rsi") is not None else 99):
        r = rows[s]
        if r.get("gate") != "ok" or r.get("v") is not False or r.get("bot") in (None, "ليس عند البوت"):
            continue
        f = flags3(r)
        bad = [i for i, x in enumerate(f) if x is False]
        if len(bad) != 1 or any(x is None for x in f):
            continue
        val = {1: _num_txt(r.get("fl")), 2: f"{(r.get('av') or 0):,.0f}"}.get(bad[0], "")
        out.append((s, f"{names[bad[0]]} {val}".strip()))
    return out


def _num_txt(x):
    """عددٌ بالعربيّة المختصرة للفلوت (مليون/ألف) — عرضٌ فقط."""
    if x is None:
        return "—"
    x = float(x)
    if x >= 1e6:
        return f"{x / 1e6:.2f} مليون"
    if x >= 1e3:
        return f"{x:,.0f}"
    return f"{x:,.0f}"


def listed(rows):
    """المطابقُ الكامل وحدَه ⟵ (فوق الدولار, سنتات) مرتّبين بـRSI: عبر الثبات والانفجار (`gate` = ok) **و**الحكمُ «نعم» **و**لا
    شكّ — وما سواه لا يُذكر في الرسالة (أمرُ المالك «لازم لازم لازم توافق الشروط 3 و ثبات 5 جلسات»)."""
    ok = [s for s, r in rows.items() if r.get("gate") == "ok" and r.get("v") is True and not r.get("doubt")]
    key = (lambda s: rows[s]["rsi"])
    return (sorted((s for s in ok if px_class(rows[s]["px"]) == "dollar"), key=key),
            sorted((s for s in ok if px_class(rows[s]["px"]) == "penny"), key=key))


def excluded_counts(rows):
    """عدّاداتُ «لا تُذكر» لمن عبر RSI: بوّاباتُ الثبات والانفجار ثمّ ما بعد الفلوت والمتاح — كلُّ سهمٍ مرّةً واحدة."""
    c = {"wait": 0, "boom": 0, "nohour": 0, "float": 0, "avail": 0, "doubt": 0, "unk": 0}
    for r in rows.values():
        g = r.get("gate")
        if g in ("wait", "boom", "nohour"):
            c[g] += 1
            continue
        if g != "ok":
            continue
        if r.get("v") is True and r.get("doubt"):
            c["doubt"] += 1
        elif r.get("v") is None:
            c["unk"] += 1
        elif r.get("v") is False:
            f = flags3(r)
            c["float" if f[1] is False else "avail"] += 1
    return c


def build_message(st, rows):
    """نصُّ الرسالة (HTML تلغرام) — **رسالةٌ واحدة بقسمين** (💵 فوق الدولار · 🪙 سنتات) **بالمطابق الكامل وحدَه** · وما سواه
    عدّادٌ في التذييل (والقصُّ يُعلَن بعدده) · **بلا علامات مقارنة.** ومصدرُ البيانات من `st["source"]` (وغيابُه = Polygon)."""
    sess = st.get("sess")
    src = source_of(st.get("source") or "polygon")
    need = STABILITY_REQ
    dol, pen = listed(rows)
    lines = [f"🔎 <b>شروطك الثلاثة</b> — إغلاق {sess}",
             f"RSI أقلّ من {rsi_max():g} · فلوت أقلّ من {OPL.FLOAT_OWNER / 1e6:g} ملايين · شورت (المتاح) أقلّ من "
             f"{OPL.AVAIL_OWNER:,}",
             f"وثبات {need} جلسات فوق أدنى قاع (القاعُ الدقيق بالبري والأفتر كفريم 4 ساعات · والعدُّ جلساتٌ يوميّة) · "
             f"ولم ينفجر خلال آخر {EXPLODE_WIN} جلسات ({float(S.CONFIG['EXPLOSION_PCT']):g}% فأكثر)",
             ("(البياناتُ من TradingView: الشموعُ وRSI والفلوت · والمتاحُ من ChartExchange)" if src == "tv"
              else "(RSI من Polygon · وياهو للتحقّق)"), ""]
    if any(rows[s].get("repaired") for s in dol + pen):
        lines.insert(4, "🩹 = شموعُ البوت لهذا الرمز صارت من Polygon (ياهو مختلُّ التقسيم) ⇒ تحقّقُه ليس مستقلًّا")
    lines.append(f"💵 <b>فوق الدولار — يطابق: {len(dol)}</b>")
    for i, s in enumerate(dol, 1):
        lines += _yes_lines(i, s, rows[s])
    if not dol:
        lines.append("لا سهمَ فوق الدولار يطابق في هذه الجلسة.")
    lines += ["", f"🪙 <b>سنتات (أقلّ من دولار) — يطابق: {len(pen)}</b>"]
    for i, s in enumerate(pen, 1):
        lines += _yes_lines(i, s, rows[s])
    if not pen:
        lines.append("لا سهمَ سنتات يطابق في هذه الجلسة.")
    x = excluded_counts(rows)
    lines += ["", f"🧾 لا تُذكر (عبرت RSI): ينتظر الثبات {x['wait']} · انفجر خلال أسبوع {x['boom']} · تعذّر القاعُ الدقيق "
                  f"{x['nohour']} · الفلوت فوق الحدّ {x['float']} · المتاح فوق الحدّ {x['avail']} · مشكوك {x['doubt']} · مجهول "
                  f"{x['unk']} (الأسماءُ في السجلّ)"]
    c = st.get("counts") or {}
    lines.append(f"🧾 الكون {c.get('universe', 0):,} · بشمعة الجلسة من {SRC_NAME[src]} {c.get('fresh', 0):,} · RSI أقلّ من "
                 f"{rsi_max():g}: {c.get('c2', 0)} (فوق الدولار {c.get('c2_dollar', 0)} · سنتات {c.get('c2_penny', 0)}) · "
                 f"ثابتٌ وغيرُ منفجر {c.get('c3', 0)} · منه فلوتٌ أقلّ من الحدّ أو مجهول {c.get('c4', 0)} · المتاح: حصاد "
                 f"{c.get('av_harvest', 0)} · الموقع {c.get('av_ce', 0)} · تعذّر {c.get('av_fail', 0)}"
                 + (f" · 🩹 صُحِّح مصدرُ البوت {c['repaired']}" if c.get("repaired") else ""))
    return S._rtl_join(lines)


def _yes_lines(i, s, r):
    """سطرا السهم المطابق: الأرقام ثمّ (الثبات · 🩹 · حالتُه عند البوت) — عرضٌ فقط · والسعرُ بدقّة `S._px_txt`."""
    rep = f" · 🩹 ×{r['repaired']:g}" if r.get("repaired") else ""
    return [f"{i}. ${s} · {S._px_txt(r['px'])} · RSI {r['rsi']:.1f} · فلوت {_num_txt(r['fl'])} · متاح {r['av']:,.0f}",
            f"   ↳ {stab_text(r)}{rep} · {r['bot']}"]


def _fmt1(x):
    return "—" if x is None else f"{x:.1f}"


def _fmt2(x):
    return "—" if x is None else f"{x:.2f}"


def trace_line(s, r, stab, boom, gate):
    """🔎 سطرُ التتبّع (`TC_TRACE` · سجلٌّ فقط) — وصفٌ لا يدخل عددًا."""
    if r is None:
        return f"🔎 تتبّع {s}: خارج «RSI أقلّ من {rsi_max():g}» أو بلا شمعة الجلسة"
    low = (f"القاع {S._px_txt(stab['pivot'])} ({stab['pivot_date']}{' · بري/أفتر' if stab.get('ext') else ''} · أدنى يوميّ "
           f"{S._px_txt(stab['daily_low'])}) · مضى {stab['bars_after']} جلسات · الإغلاقُ فوقه {stab['held']}"
           if stab else "القاعُ الدقيق لم يُقَس")
    bm = (f"أقصى صعودٍ في الأسبوع {boom['pct']:+.1f}% ({boom['day']} · من {S._px_txt(boom['ref'])} إلى "
          f"{S._px_txt(boom['peak'])})" if boom else "الانفجار لم يُقَس")
    return (f"🔎 تتبّع {s}: RSI {_fmt1(r.get('rsi'))} · {S._px_txt(r.get('px'))} ({px_class(r.get('px'))}) · {low} · {bm} · "
            f"البوّابة {gate}")


def failure_message(sess, why):
    """سطرُ عطلٍ صريح بدل القائمة (حارسُ التغطية/البيانات البائتة) — لا «لا يوجد» كاذب."""
    return S._rtl_join([f"🔎 <b>شروطك الثلاثة</b> — إغلاق {sess}",
                        f"⚠️ تعذّر الفحص اليوم: {why}",
                        "لا تُقرأ الرسالةُ «لا يوجد» — البياناتُ ناقصة، وتُعاد غدًا."])


# ─────────────────────────── الجلب ───────────────────────────
class Breaker:
    """⛔ قاطعُ دائرةٍ لنداءات Polygon (‏2026-09-29 · عطلٌ مُثبَت بالتشغيلة `36631553164`): حين يرفض المزوّدُ الطلبات يدفع
    `P._get` كلَّ رمزٍ أربعَ محاولاتٍ بانتظارٍ ‏30ث ⇒ ‏3,584 رمزًا بثمانية خيوطٍ ‏≈3.7 ساعات ⇒ تُقصّ المرحلةُ عند مهلتها
    (‏40 د) **قبل حارس التغطية** فلا يصل سطرُ العطل المصمَّم ويُتخطّى الإرسالُ كلُّه (صمتٌ لا «تعذّر»). القاطعُ يعدّ الرموزَ
    المكتملة وإخفاقاتِ `P._get` (فرقُ `P._CALLS["fail"]` منذ إنشائه) فإذا بلغت المكتملةُ `BREAKER_MIN` وبلغ إخفاقُها
    `BREAKER_FAIL_RATIO` منها فُتح: **البقيّةُ `[]` بلا نداء** ⇒ حارسُ التغطية يُرسل سطرَ العطل في دقائق. **وسليمًا لا يُفتح**
    (الإخفاقُ نادر) ⇒ النداءاتُ والنتائجُ بت-بت · وسباقُ العدّاد بين الخيوط لا يُنقص إلّا الإخفاق (فلا يفتحه كذبًا)."""

    def __init__(self, min_done=None, ratio=None, calls=None):
        self.min_done = BREAKER_MIN if min_done is None else int(min_done)
        self.ratio = BREAKER_FAIL_RATIO if ratio is None else float(ratio)
        self.calls = P._CALLS if calls is None else calls
        self.base = self.calls["fail"]
        self.done = self.skipped = 0
        self.open = False
        self.lock = threading.Lock()

    def fails(self):
        return self.calls["fail"] - self.base

    def skip(self):
        """مفتوحٌ ⇒ يُعَدّ المتخطّى ويعود True (لا نداء)."""
        with self.lock:
            if self.open:
                self.skipped += 1
            return self.open

    def record(self):
        """رمزٌ اكتمل نداؤه (نجح أو أخفق) ⟵ يُفتح القاطعُ إن بلغ الحدّين."""
        with self.lock:
            self.done += 1
            if not self.open and self.done >= self.min_done and self.fails() >= self.ratio * self.done:
                self.open = True

    def summary(self):
        return {"open": self.open, "done": self.done, "fail": self.fails(), "skipped": self.skipped}


class TVBreaker(Breaker):
    """⛔ قاطعُ TradingView — عدّادُه **نتائجُ الرموز نفسُها** (None بعد الإعادة = إخفاق) لا عدّادٌ عامّ: `TV.fetch_many` ينادي
    `skip()` قبل كلّ رمز و`record(ok)` بعد نتيجته النهائيّة (معاملُ `gate`). حين يُحجَب الموقعُ يُفتح بعد `BREAKER_MIN` رمزًا
    ⟵ البقيّةُ بلا نداء ⟵ سطرُ العطل في دقائق لا صمتٌ حتى المهلة (درسُ Polygon 2026-09-29 · والحدّان نفسُهما)."""

    def __init__(self, min_done=None, ratio=None):
        super().__init__(min_done=min_done, ratio=ratio, calls={"fail": 0})

    def record(self, ok=True):
        if not ok:
            with self.lock:
                self.calls["fail"] += 1
        super().record()

    def summary(self):
        return dict(super().summary(), src="tv")


def breaker_note(b):
    """ذيلُ سطر العطل حين فُتح القاطع ⟵ نصٌّ عربيٌّ بلا علاماتِ مقارنة · وإلّا "" — ونصُّ TradingView لقاطعه (`src`)."""
    if not b or not b.get("open"):
        return ""
    if b.get("src") == "tv":
        return (f" — قاطعُ الدائرة: TradingView أخفق في {b['fail']:,} من {b['done']:,} رمزًا فتُخطّيت البقيّةُ "
                f"({b['skipped']:,}) · قد يكون الموقعُ حجب الوصول أو غيّر واجهته (لا واجهةَ رسميّة)")
    return (f" — قاطعُ الدائرة: Polygon أخفق في {b['fail']:,} من {b['done']:,} رمزًا فتُخطّيت البقيّةُ "
            f"({b['skipped']:,}) · تحقّق من اشتراك Polygon")


def _guarded(brk, fn, s):
    """نداءٌ واحدٌ تحت القاطع ⟵ (s, صفوف) · والمتخطّى والمُستثنى ⟵ []."""
    if brk.skip():
        return s, []
    try:
        return s, fn(s) or []
    except Exception:                                                # noqa: BLE001
        return s, []
    finally:
        brk.record()


def fetch_polygon(syms, d0, d1, key, workers=WORKERS, brk=None):
    """{رمز: صفوف adjusted} بـ`P.ticker_daily_adj` بالاسم — متوازيًا · والتعذّرُ ⟵ [] · **تحت قاطع الدائرة** (`Breaker`)."""
    brk = brk or Breaker()
    out = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for i, (s, rows) in enumerate(ex.map(lambda x: _guarded(brk, lambda y: P.ticker_daily_adj(y, d0, d1, key), x),
                                             syms), 1):
            out[s] = rows
            if i % 500 == 0:
                log(f"   … Polygon {i}/{len(syms)}")
    BREAKER_LAST["daily"] = brk.summary()
    if brk.open:
        log(f"⛔ قاطعُ الدائرة (اليوميّ){breaker_note(BREAKER_LAST['daily'])}")
    return out



def _hours_one(s, d0, d1, key):
    """شموعُ الساعة `adjusted=true` لرمزٍ بين يومين ⟵ [(ms, high, low)] — بـ`P._get` بالاسم (إعادةُ المحاولة) · والشمعةُ التالفة
    تُتخطّى · والتعذّرُ ⟵ [] (فيصير القاعُ الدقيق «لم يُقَس» لا تخمينًا)."""
    js = P._get(f"{P.API}/v2/aggs/ticker/{s}/range/1/hour/{d0}/{d1}",
                {"adjusted": "true", "sort": "asc", "limit": "50000"}, key)
    out = []
    for b in (js or {}).get("results") or []:
        try:
            out.append((int(b["t"]), float(b["h"]), float(b["l"])))
        except (KeyError, TypeError, ValueError):
            continue
    return out


def fetch_hours(syms, d0, d1, key, workers=WORKERS, brk=None):
    """{رمز: شموعُ الساعة} متوازيًا — للقاع الدقيق (⑩) والانفجار (⑫) · والتعذّرُ ⟵ [] · **تحت قاطعٍ مستقلّ** عن اليوميّ."""
    brk = brk or Breaker()
    out = {}
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        for s, rows in ex.map(lambda x: _guarded(brk, lambda y: _hours_one(y, d0, d1, key), x), syms):
            out[s] = rows
    BREAKER_LAST["hours"] = brk.summary()
    if brk.open:
        log(f"⛔ قاطعُ الدائرة (الساعة){breaker_note(BREAKER_LAST['hours'])}")
    return out

def _tv_full(s, tmap):
    """رمزٌ مجرّد ⟵ «EXCH:SYM» من خريطة الماسح (`TV.ticker_map`) · وغيابُه ⟵ «NASDAQ:SYM» (كونُ البوت ناسداك)."""
    return (tmap or {}).get(s) or f"NASDAQ:{s}"


def _tv_progress(k, n):
    if k % 1000 == 0:
        log(f"   … TradingView {k}/{n}")


def fetch_tv(syms, d0, d1, key=None, tmap=None, workers=TV_WORKERS, brk=None, chart_factory=None):
    """📺 {رمز: صفوفٌ يوميّة (يومُ نيويورك, o, h, l, c, v)} من مِقبس TradingView (`TV.fetch_many` · الجلسةُ النظاميّة ·
    `adjustment=splits`) **مقصوصةً على [d0, d1]** — فشكلُ الصفّ وحدودُه كـ`P.ticker_daily_adj` (آخرُ صفٍّ = الجلسةُ أو قبلها) ·
    والتعذّرُ ⟵ [] · **تحت قاطع الدائرة** (`TVBreaker`) · و`key` مُهمَل (توقيعُ `fetch_polygon` نفسُه للحقن)."""
    brk = brk or TVBreaker()
    full = {s: _tv_full(s, tmap) for s in syms}
    got = TV.fetch_many(sorted(set(full.values())), interval="1D", n=TV_DAILY_N, workers=workers,
                        chart_factory=chart_factory, progress=_tv_progress, gate=brk)
    out = {}
    for s, f in full.items():
        rows = []
        for b in got.get(f) or []:
            d = TV.ny_day(b[0])
            if d0 <= d <= d1:
                rows.append((d, float(b[1]), float(b[2]), float(b[3]), float(b[4]), float(b[5])))
        out[s] = rows
    BREAKER_LAST["daily"] = brk.summary()
    if brk.open:
        log(f"⛔ قاطعُ الدائرة (اليوميّ){breaker_note(BREAKER_LAST['daily'])}")
    return out


def fetch_tv_hours(syms, d0, d1, key=None, tmap=None, workers=TV_WORKERS, brk=None, chart_factory=None):
    """📺 {رمز: [(ms, high, low)]} — شموعُ ساعةٍ **ممتدّة** (البري والأفتر) من مِقبس TradingView بين يومَي نيويورك d0 وd1 ضمنًا
    (شكلُ `_hours_one` نفسُه) · والتعذّرُ ⟵ [] (فالقاعُ الدقيق «لم يُقَس» لا تخمين) · **تحت قاطعٍ مستقلّ** عن اليوميّ."""
    brk = brk or TVBreaker()
    full = {s: _tv_full(s, tmap) for s in syms}
    got = TV.fetch_many(sorted(set(full.values())), interval="60", n=TV_HOURS_N, extended=True, workers=workers,
                        chart_factory=chart_factory, gate=brk)
    out = {}
    for s, f in full.items():
        out[s] = [(int(b[0]) * 1000, float(b[2]), float(b[3])) for b in (got.get(f) or []) if d0 <= TV.ny_day(b[0]) <= d1]
    BREAKER_LAST["hours"] = brk.summary()
    if brk.open:
        log(f"⛔ قاطعُ الدائرة (الساعة){breaker_note(BREAKER_LAST['hours'])}")
    return out


def tv_snapshot(tries=TV_SCAN_TRIES, scan=None, pause=5.0):
    """📺 لقطةُ الماسح (`TV_COLS` لأسهم الأسواق الثلاثة) ⟵ {«EXCH:SYM»: {عمود: قيمة}} أو None بعد `tries` محاولات — و`TV.scan`
    لا يُرجع نصفَ قائمة (صفحةٌ تتعذّر ⟵ None للكلّ)."""
    scan = scan or TV.scan
    for i in range(max(1, int(tries))):
        sn = scan(TV_COLS)
        if sn:
            return sn
        if i + 1 < tries and pause:
            time.sleep(pause)
    return None


def _stored_float(s, wl_fl, nw, cache):
    """فلوتُ البوت المخزَّن لرمز (القائمة ⟵ مخزنُ «تحت المتابعة» ⟵ ذاكرةُ الشركات) ⟵ عددٌ أو None — **للاطّلاع في السجلّ وحدَه**
    في مصدر TradingView (أصلُه ياهو) · وترتيبُه ترتيبُ مسار Polygon نفسُه."""
    if wl_fl.get(s):
        return float(wl_fl[s])
    if isinstance(nw, dict) and isinstance(nw.get(s), dict) and nw[s].get("float"):
        return float(nw[s]["float"])
    if isinstance(cache, dict) and isinstance(cache.get(s), dict) and cache[s].get("float"):
        return float(cache[s]["float"])
    return None


def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:                                                # noqa: BLE001
        return default


def _dump(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False)


# ─────────────────────────── المراحل ───────────────────────────
def stage_scan(now=None, key=None, fetch=None, universe=None, yahoo=None, yfloat=None, harvested=None,
               wl=None, nw=None, cache=None, repaired=None, hours=None, source=None, snap=None):
    """① ⟶ ④ + ⑦ + ⑩ + ⑫: الكون · الشموعُ اليوميّة · RSI والسعر (بلا حدّ سعرٍ — السنتاتُ قسمٌ) · شموعُ الساعة ⟵ القاعُ الدقيق
    وثباتُه والانفجار · الفلوت (لمن عبر الثبات وحدَه) · التحقّق · وقائمةُ المتاح المطلوبة ⟵ الحالة (dict).
    📺 `source` (وغيابُه ⟵ `SOURCE`): «tv» = TradingView (لقطةُ الماسح `snap` المحقونة أو `tv_snapshot()` ⟵ خريطةُ الرموز والفلوتُ
    وRSI المرجع · والمِقبسُ للشموع) · «polygon» = Polygon وياهو (المسارُ السابق بت-بت · و`yahoo`/`yfloat`/`repaired` له وحدَه)."""
    now = now or dt.datetime.now(tz=NY)
    src = source_of(SOURCE if source is None else source)
    nm = SRC_NAME[src]
    cal = WW.calendar(now.year)
    sess, send, why = session_gate(cal, now, FORCE)
    st = {"sess": sess, "send": send, "why": why, "now": now.isoformat(), "rows": {}, "need": [], "counts": {},
          "fail": None, "source": src}
    log(f"🔎 الجلسة {sess} · يُرسَل: {send} ({why})" + (f" · المصدر {nm}" if src == "tv" else ""))
    if not sess or not send:
        return st                            # عطلةٌ/لا جلسة ⇒ صفرُ جلب (لا Polygon ولا ياهو ولا موقع)
    wl = load_json(WW.WL_FILE, {}) if wl is None else wl
    nw = load_json(S.NEAR_WATCH_FILE, {}) if nw is None else nw
    extra = sorted({e.get("symbol") for sec in ("stocks", "pullback") for e in (wl.get(sec) or []) if e.get("symbol")}
                   | set(nw if isinstance(nw, dict) else {}))
    uni = sorted(set(universe() if universe else S.get_universe()) | set(extra))
    d0 = (dt.date.fromisoformat(sess) - dt.timedelta(days=WW.HIST_DAYS)).isoformat()
    BREAKER_LAST.clear()                     # ⛔ لا يُقرأ قاطعُ تشغيلةٍ سابقة (والجالبُ المحقون لا يكتبه)
    sn, tmap = {}, {}
    if src == "tv":
        #    📺 الماسحُ أوّلًا: خريطةُ «EXCH:SYM» للمِقبس · والفلوت · وRSI المرجع — وتعذّرُه أو قصورُه ⟵ سطرُ عطلٍ قبل أيّ شمعة
        sn = tv_snapshot() if snap is None else snap
        if not sn:
            st["fail"] = "ماسحُ TradingView تعذّر (الفلوت وتحقّقُ RSI) — قد يكون الموقعُ حجب الوصول أو غيّر واجهته"
            log(f"⛔ {st['fail']}")
            return st
        tmap = TV.ticker_map(sn)
        hit = sum(1 for s in uni if s in tmap)
        st["counts"]["tv_scan"] = hit
        log(f"📺 ماسحُ TradingView: {len(sn):,} صفًّا · منها في الكون {hit} من {len(uni)} = "
            f"{hit / max(1, len(uni)) * 100:.1f}% (الحدّ {MIN_COVER * 100:.0f}%)")
        if not uni or hit / len(uni) < MIN_COVER:
            st["fail"] = f"ماسحُ TradingView غطّى {hit} من {len(uni)} رمزًا فقط"
            return st
        fetch = fetch or (lambda xs, a, b, k: fetch_tv(xs, a, b, k, tmap=tmap))
        hours = hours or (lambda xs, a, b, k: fetch_tv_hours(xs, a, b, k, tmap=tmap))
    else:
        fetch = fetch or fetch_polygon
        hours = hours or fetch_hours
    log(f"👥 الكون {len(uni)} (منه القائمة والارتداد وتحت المتابعة {len(extra)}) · {nm} {d0} ⟶ {sess} …")
    pg = fetch(uni, d0, sess, key)
    fresh = [s for s in uni if (pg.get(s) or []) and pg[s][-1][0] == sess]
    cover = len(fresh) / len(uni) if uni else 0.0
    st["counts"].update({"universe": len(uni), src: sum(1 for s in uni if pg.get(s)), "fresh": len(fresh)})
    log(f"🩺 شمعةُ الجلسة من {nm}: {len(fresh)} من {len(uni)} = {cover * 100:.1f}% (الحدّ {MIN_COVER * 100:.0f}%)")
    if cover < MIN_COVER:
        st["fail"] = (f"شموعُ {nm} لجلسة {sess} لم تكتمل ({len(fresh)} من {len(uni)})"
                      + breaker_note(BREAKER_LAST.get("daily")))
        return st
    rows = {}
    lim = rsi_max()                         # حدُّ فيصل بالاسم (أمرُ المالك «تحت 33 … للصنفين») — لا `OPL.RSI_OWNER`
    for s in fresh:
        rsi = WW.rsi_at(pg[s], sess)
        px = WW.close_at(pg[s], sess)
        if rsi is not None and px is not None and px > 0 and rsi < lim:
            rows[s] = {"rsi": rsi, "px": px, "fl": None, "fl_src": "", "av": None, "av_src": "", "ry": None,
                       "ratio": None, "bot": bot_label(s, wl, nw), "stab": None, "boom": None, "gate": None,
                       "repaired": None}
    st["counts"]["c2"] = len(rows)
    st["counts"]["c2_dollar"] = sum(1 for s in rows if px_class(rows[s]["px"]) == "dollar")
    st["counts"]["c2_penny"] = len(rows) - st["counts"]["c2_dollar"]
    log(f"② RSI أقلّ من {lim:g} ({nm} · حدُّ فيصل `RSI_OVERSOLD`): {len(rows)} — فوق الدولار "
        f"{st['counts']['c2_dollar']} · سنتات {st['counts']['c2_penny']}")
    h0 = (dt.date.fromisoformat(sess) - dt.timedelta(days=HOURS_DAYS)).isoformat()
    want = sorted(set(rows) | {t for t in TRACE if t in pg})
    hr = hours(want, h0, sess, key) if want else {}
    if (BREAKER_LAST.get("hours") or {}).get("open"):
        #    ⛔ قاطعُ الساعة فُتح ⇒ القاعُ الدقيق لم يُقَس لأغلب العابرين ⇒ **سطرُ عطلٍ لا «لا يوجد» كاذب**
        st["fail"] = f"شموعُ الساعة من {nm} لجلسة {sess} تعذّرت" + breaker_note(BREAKER_LAST["hours"])
        return st
    for s in sorted(rows):
        stab = exact_low_stability(pg[s], hr.get(s) or [], sess)
        boom = recent_explosion(pg[s], hr.get(s) or [], sess)
        rows[s].update({"stab": stab, "boom": boom, "gate": gate_of(stab, boom)})
    for t in TRACE:
        if t in rows:
            log(trace_line(t, rows[t], rows[t]["stab"], rows[t]["boom"], rows[t]["gate"]))
        elif t in pg:
            _st = exact_low_stability(pg[t], hr.get(t) or [], sess)
            _bm = recent_explosion(pg[t], hr.get(t) or [], sess)
            log(trace_line(t, {"rsi": WW.rsi_at(pg[t], sess), "px": WW.close_at(pg[t], sess)}, _st, _bm, "خارج RSI"))
        else:
            log(trace_line(t, None, None, None, None))
    by = {g: sorted((s for s in rows if rows[s]["gate"] == g), key=lambda x: rows[x]["rsi"]) for g in GATE_TXT}
    for g, xs in by.items():
        st["counts"][g] = len(xs)
    c3 = sorted(s for s in rows if rows[s]["gate"] == "ok")
    st["counts"]["c3"] = len(c3)
    log(f"⑩⑫ ثابتٌ {STABILITY_REQ} جلسات فوق القاع الدقيق وغيرُ منفجر خلال {EXPLODE_WIN}: {len(c3)} · "
        + " · ".join(f"{GATE_TXT[g]} {len(xs)}" for g, xs in by.items()))
    for s in by["wait"]:
        log(f"   ⏳ {s} · {S._px_txt(rows[s]['px'])} · {stab_text(rows[s])}")
    for s in by["boom"]:
        b = rows[s]["boom"]
        log(f"   💥 {s} · {S._px_txt(rows[s]['px'])} · {b['pct']:+.1f}% يوم {b['day']} (من {S._px_txt(b['ref'])} إلى "
            f"{S._px_txt(b['peak'])}) · {stab_text(rows[s])}")
    if by["nohour"]:
        log(f"   ⛔ تعذّر القاعُ الدقيق (شموعُ الساعة) {len(by['nohour'])}: " + " · ".join(by["nohour"]))
    cache = load_json(S.COMPANY_FILE, {}) if cache is None else cache
    wl_fl = {e.get("symbol"): e.get("float") for sec in ("stocks", "pullback") for e in (wl.get(sec) or [])}
    if src == "tv":
        #    📺 الفلوتُ من ماسح TradingView **وحدَه** (أمرُ المالك «من ترندق فيو مب ياهو») — والمخزَّنُ عند البوت (أصلُه ياهو)
        #    يُطبع للغائب ولا يدخل الحكم ⇒ الغائبُ «مجهولٌ» لا «نعم»
        for s in c3:
            fl = tv_float(sn.get(tmap.get(s)))
            if fl:
                rows[s]["fl"], rows[s]["fl_src"] = fl, "TradingView"
        unk_tv = [s for s in c3 if rows[s]["fl"] is None]
        if unk_tv:
            log(f"   ❔ فلوتُ TradingView غائب {len(unk_tv)} (مجهولٌ في الحكم · والمخزَّنُ عند البوت للاطّلاع وحدَه): "
                + " · ".join(f"{s} ({_num_txt(_stored_float(s, wl_fl, nw, cache))})" for s in unk_tv))
    else:
        for s in c3:
            fl = (yfloat or (lambda x: S._yahoo_float(x, strict=True)))(s)
            if fl:
                rows[s]["fl"], rows[s]["fl_src"] = float(fl), "ياهو"
            elif wl_fl.get(s):
                rows[s]["fl"], rows[s]["fl_src"] = float(wl_fl[s]), "قائمة البوت"
            elif isinstance(nw, dict) and isinstance(nw.get(s), dict) and nw[s].get("float"):
                #    👀🏢 مخزنُ فلوت «تحت المتابعة» (ياهو `floatShares` · يُحدَّث يوميًّا منذ 2026-09-26)
                rows[s]["fl"], rows[s]["fl_src"] = float(nw[s]["float"]), "مخزن تحت المتابعة"
            elif isinstance(cache.get(s), dict) and cache[s].get("float"):
                rows[s]["fl"], rows[s]["fl_src"] = float(cache[s]["float"]), "ذاكرة البوت"
            if yfloat is None:
                time.sleep(0.3)
    c4 = [s for s in c3 if rows[s]["fl"] is None or rows[s]["fl"] < OPL.FLOAT_OWNER]
    st["counts"]["c4"] = len(c4)
    log(f"④ فلوتٌ أقلّ من {OPL.FLOAT_OWNER:,} أو مجهول: {len(c4)} (مجهول {sum(1 for s in c4 if rows[s]['fl'] is None)})")
    if src == "tv":
        for s in c4:
            rows[s]["ry"] = tv_ref_rsi(sn.get(tmap.get(s)), rows[s]["px"])
        st["counts"]["tv_ref"] = sum(1 for s in c4 if rows[s]["ry"] is not None)
        log(f"⑦ تحقّقُ RSI بماسح TradingView (قناةٌ ثانيةٌ من المصدر نفسِه لا تحقّقٌ مستقلّ): قُورن {st['counts']['tv_ref']} من "
            f"{len(c4)} · والباقي إغلاقُ الماسح ليس إغلاقَ الجلسة ⟵ لا مقارنة ولا شكّ")
    else:
        S.SPLIT_REPAIR_LAST.clear()
        yh = (yahoo or S.download_history)(sorted(c4)) if c4 else {}
        fixed = dict(S.SPLIT_REPAIR_LAST.get("replaced") or []) if repaired is None else dict(repaired)
        for s in c4:
            if s in fixed:
                rows[s]["repaired"] = float(fixed[s])
            ydf = yh.get(s)
            if ydf is None or not len(ydf):
                continue
            ya = {i.date().isoformat(): float(c) for i, c in ydf["Close"].items()}
            cut = [ya[d] for d in sorted(ya) if d <= sess]
            if len(cut) >= WW.MIN_RSI_BARS:
                rows[s]["ry"] = float(S.rsi(pd.Series(cut)).iloc[-1])
            rows[s]["ratio"] = ratio_range(ya, {r[0]: r[4] for r in pg[s][-260:]})
    hv = (harvested or S._harvested_borrow)(dt.datetime.now(dt.timezone.utc).date().isoformat())
    need = []
    for s in sorted(c4, key=lambda x: (rows[x]["fl"] is None, rows[x]["rsi"])):
        h = hv.get(s)
        if h and h.get("shares_available") is not None:
            rows[s]["av"], rows[s]["av_src"] = float(h["shares_available"]), "حصاد اليوم"
        else:
            need.append(s)
    st["rows"], st["need"] = rows, need
    st["counts"]["repaired"] = sum(1 for s in c4 if rows[s].get("repaired"))
    if st["counts"]["repaired"]:
        log(f"🩹 مصدرُ البوت صُحِّح لـ{st['counts']['repaired']}: "
            + " · ".join(f"{s} ×{rows[s]['repaired']:g}" for s in sorted(c4) if rows[s].get("repaired")))
    st["counts"]["av_harvest"] = sum(1 for s in c4 if rows[s]["av_src"] == "حصاد اليوم")
    log(f"⑤ المتاح: من حصاد اليوم {st['counts']['av_harvest']} · مطلوبٌ من الموقع {len(need)} {need[:40]}")
    return st


def stage_borrow(st, shard=SHARD, shards=SHARDS, ce=None, pause=CE_PAUSE):
    """⑤ المتاحُ لجزء الرنر `need[shard::shards]` من ChartExchange — شاهدٌ أوّلًا وآخرًا · وتعذّرٌ بسببه ⟵ {رمز: {av, why}}."""
    ce = ce or S.ce_borrow_info
    mine = shard_of(st.get("need") or [], shard, shards)[:CE_CAP]
    out = {}
    w0 = ce(WITNESS)
    for s in mine:
        d = {}
        if pause:
            time.sleep(pause)
        info = ce(s, diag=d)
        av = (info or {}).get("shares_available")
        out[s] = {"av": None if av is None else float(av), "why": None if av is not None else str(d.get("reason") or "؟")}
    w1 = ce(WITNESS)
    log(f"🩺 جزء {int(shard) % max(1, int(shards)) + 1} من {max(1, int(shards))}: {len(mine)} رمزًا · شاهدٌ أوّلًا "
        f"{'✓' if (w0 or {}).get('shares_available') is not None else '✗'} · آخرًا "
        f"{'✓' if (w1 or {}).get('shares_available') is not None else '✗'} · تعذّر "
        f"{sum(1 for v in out.values() if v['av'] is None)}")
    return out


def stage_send(st, parts, send=None):
    """⑥ ⟶ ⑨: دمجُ المتاح · الحكم · الرسالة · والإرسالُ (إلّا في `DRY`) ⟵ رمزُ الخروج."""
    send = send or S.send_telegram
    if not st.get("sess"):
        log("⛔ لا جلسة")
        return 4
    if not st.get("send"):
        log(f"🔕 لا إرسال: {st.get('why')}")
        return 0
    if st.get("fail"):
        msg = failure_message(st["sess"], st["fail"])
        log(msg)
        if not DRY:
            send(msg + "\n\n" + S.FOOTER)
        return 3
    rows = st.get("rows") or {}
    merged = {}
    for p in parts:
        merged.update(p or {})
    ok_ce = fail_ce = 0
    for s, v in merged.items():
        if s not in rows:
            continue
        if v.get("av") is not None:
            rows[s]["av"], rows[s]["av_src"] = float(v["av"]), "الموقع"
            ok_ce += 1
        else:
            rows[s]["av_src"] = "تعذّر: " + str(v.get("why") or "؟")
            fail_ce += 1
    for s in st.get("need") or []:
        if s in rows and s not in merged:
            rows[s]["av_src"] = "لم يُسأل (حصّة الموقع)"
            fail_ce += 1
    st.setdefault("counts", {}).update({"av_ce": ok_ce, "av_fail": fail_ce})
    for s, r in rows.items():
        r["v"], r["doubt"] = verdict(r) if r.get("gate") == "ok" else (None, False)
    # 🗒️ ما لا يُذكر في الرسالة يُطبع هنا بأسمائه (أمرُ المالك «لازم لازم لازم توافق» ⇒ الرسالةُ للمطابق وحدَه)
    ok = [s for s in sorted(rows) if rows[s].get("gate") == "ok"]
    for s in ok:
        r = rows[s]
        if r["v"] is True and r["doubt"] and source_of(st.get("source") or "polygon") == "tv":
            log(f"   ⚠️ مشكوك {s} · RSI الشموع {r['rsi']:.1f} · الماسح {r['ry']:.1f} (TradingView) · {S._px_txt(r['px'])}")
        elif r["v"] is True and r["doubt"]:
            why = " · تقسيمٌ غيرُ متّسق بين المصدرين" if (r.get("ratio") or 0) > SPLIT_RATIO else ""
            log(f"   ⚠️ مشكوك {s} · RSI Polygon {r['rsi']:.1f} · ياهو {r['ry']:.1f}{why} · {S._px_txt(r['px'])}")
        elif r["v"] is None:
            miss = [n for n, x in (("الفلوت", r.get("fl")), ("المتاح", r.get("av"))) if x is None]
            log(f"   ❔ مجهول {s} · الناقص: {' · '.join(miss) or '—'} ({r.get('av_src') or '—'}) · {r['bot']}")
    # ✖️ وما سقط بالفلوت أو المتاح يُطبع **كلُّه بقيمته** — التذييلُ يَعِد «الأسماءُ في السجلّ» (أمسكه dry `36259380803`: الفلوت
    #    29 والمتاح 20 كانوا عدًّا بلا أسماء) · والتصنيفُ نفسُه في `excluded_counts`
    fl_x, av_x = [], []
    for s in ok:
        r = rows[s]
        if r["v"] is False:
            f = flags3(r)
            (fl_x if f[1] is False else av_x).append(s)
    if fl_x:
        log(f"   ✖️ الفلوت فوق الحدّ {len(fl_x)}: " + " · ".join(f"{s} ({_num_txt(rows[s].get('fl'))})" for s in fl_x))
    if av_x:
        log(f"   ✖️ المتاح فوق الحدّ {len(av_x)}: "
            + " · ".join(f"{s} ({(rows[s].get('av') or 0):,.0f})" for s in av_x))
    near = near_misses(rows)
    if near:
        log(f"   🔸 من أسهم البوت سقطت بشرطٍ واحد (والثبات عابر): {len(near)} — "
            + " · ".join(f"{s} ({why})" for s, why in near[:NEAR_SHOW])
            + (f" … و{len(near) - NEAR_SHOW} غيرُها" if len(near) > NEAR_SHOW else ""))
    for t in TRACE:
        r = rows.get(t)
        if r is not None:
            log(f"🔎 تتبّع {t}: البوّابة {r.get('gate')} · الحكم {r.get('v')} · مشكوك {r.get('doubt')} · فلوت "
                f"{_num_txt(r.get('fl'))} ({r.get('fl_src') or '—'}) · متاح {r.get('av')} ({r.get('av_src') or '—'})")
    msg = build_message(st, rows)
    log(msg)
    if DRY:
        log("🧪 TC_DRY=1 — طُبعت ولم تُرسل")
        return 0
    send(msg + "\n\n" + S.FOOTER)
    return 0


def main() -> int:
    key = (os.environ.get("POLYGON_API_KEY") or "").strip()
    if STAGE in ("scan", "all") and source_of(SOURCE) == "polygon" and not key:     # 📺 TradingView بلا مفتاح
        log("⛔ بلا POLYGON_API_KEY")
        return 2
    if STAGE == "scan":
        _dump(STATE_FILE, stage_scan(key=key))
        return 0
    if STAGE == "borrow":
        st = load_json(STATE_FILE, {})
        _dump(os.environ.get("TC_PART") or f"tc_borrow_{SHARD}.json", stage_borrow(st))
        return 0
    if STAGE == "send":
        st = load_json(STATE_FILE, {})
        parts = [load_json(p, {}) for p in sorted(glob.glob(PARTS_GLOB, recursive=True))]
        log(f"📦 أجزاءُ المتاح: {len(parts)}")
        return stage_send(st, parts)
    st = stage_scan(key=key)
    return stage_send(st, [stage_borrow(st, 0, 1)])


if __name__ == "__main__":
    sys.exit(main())
