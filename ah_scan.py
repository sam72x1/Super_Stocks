#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🌙 `T-AH` — قياسُ «عمى الافتر» من شموع الدقيقة المجمَّعة (‏Flat Files · S3).

**العقد:** `ah_prereg.md` (مدفوعٌ **قبل أيّ رقم** · حرّاسُ الصلاحية `V1`-`V6`).

**السؤال:** الفرزُ يقرأ الشمعةَ اليومية **ولا تشمل الجلسةَ الممتدّة** — فانفجر `NUWE`
‏+100% في الافتر وأعاد الصيّادُ ترشيحَه صباحَ الغد. وحارسُنا `ah_guard` بعتبة 20%
**لم تُقَس قطّ**. والملفّاتُ تعطي ما لا يعطيه أيُّ مصدرٍ آخر: **تاريخَ الجلسة الممتدّة**.

🔒 **بحث/قياس فقط:** لا يُستورَد في أيّ مسار إنتاج · لا يكتب حالة · لا تلغرام · ولا
يمسّ عتبةً. **وإعادةُ استعمالٍ لا بناء:** الوصولُ إلى S3 من `flatfiles_probe`
بأسمائه · وحدُّ الجلسة من `market_calendar.session_info` (فيومُ الإغلاق المبكّر
‏13:00 يجعل ما بعده **ممتدًّا**) · والاتّفاقُ مع `event_exec.ny_session_key`
الإنتاجية **مُثبَتٌ بحارس** فلا يصير عندنا تعريفان للجلسة.
"""
from __future__ import annotations

import csv
import datetime as dt
import gzip
import os
import sys
import time
from zoneinfo import ZoneInfo

import flatfiles_probe as FP
import market_calendar as MC

NY = ZoneInfo("America/New_York")

DAYS = [d.strip() for d in os.environ.get("AH_DAYS", "2026-08-07").split(",")
        if d.strip()]
WITNESS = os.environ.get("AH_WITNESS", "AAPL")
PRICE_MAX = float(os.environ.get("AH_PRICE_MAX", "10"))
CAP_MB = float(os.environ.get("AH_CAP_MB", "2048"))
# 🎯 عتباتُ `Q1` **مثبَّتةٌ قبل الأرقام** — و20% هي عتبةُ `ah_guard` الحيّة.
THRESH = (10.0, 20.0, 50.0, 100.0)
GUARD_T = 20.0
# 🕯️ نافذةُ ما قبل السوق عند المزوّد تبدأ 04:00 نيويورك.
PRE_OPEN_NY_MIN = 4 * 60
MIN_PATH = "us_stocks_sip/minute_aggs_v1"
# ‏V1: شاهدُ الضبط — حجمٌ ممتدٌّ **موجبٌ وصغير**. الصفرُ عطبٌ حتى يُنفى، والنصفُ عطبٌ أيضًا.
CTRL_MIN_PCT, CTRL_MAX_PCT = 0.0, 20.0

# ── `T-AH-YEAR` (العقد: `ah_year_prereg.md` — مدفوعٌ قبل أيّ رقم) ─────────────
# مدى المعايرة: `AH_FROM`/`AH_TO` (ISO). فارغان ⇒ وضعُ `AH_DAYS` كما هو (توافقٌ
# خلفيٌّ يجعل أرقامَ `ah_result.md` قابلةً لإعادة الإنتاج حرفيًّا).
FROM_DAY = (os.environ.get("AH_FROM") or "").strip()
TO_DAY = (os.environ.get("AH_TO") or "").strip()
# 🎯 منحنى الكلفة — **مثبَّتٌ قبل الأرقام** (`Y1`)، و20 هي العتبةُ الحيّة لا خيارٌ بعديّ.
CURVE = (10.0, 15.0, 20.0, 25.0, 30.0, 50.0, 100.0)
# 🎯 شرائحُ السعر (`Y4`) — مثبَّتةٌ سلفًا: أمثلةُ فيصل للمقسّم تتمركز ‏≈$3 (مدوَّن).
PRICE_BANDS = ((0.0, 2.0), (2.0, 5.0), (5.0, 10.0))
# ‏VY6: تغطيةٌ دون هذي النسبة ⇒ الأرقامُ **أرضيّةٌ مُعلَنة** وخروجٌ 6.
COVER_MIN_PCT = 90.0
# ‏VY6: شهرٌ دون هذا العدد **لا يدخل حكمَ `Y3`** (يُعلَن ولا يُطوى).
MONTH_MIN_DAYS = 15
# ‏VY7: فوق هذا العدد من الأيام لا تُحفَظ الصفوفُ في الذاكرة (‏≈12 ألف صفٍّ/يوم).
KEEP_FRAMES_MAX = 8
# ميزانيةُ ساعةِ الحائط — تُوقِف **بإعلان** قبل أن يقتلَنا سقفُ الجوب.
BUDGET_MIN = float(os.environ.get("AH_BUDGET_MIN", "300"))


def log(m: str = "") -> None:
    print(m, flush=True)                       # ⚡ حيًّا: عمليةٌ طويلة بلا طباعةٍ حيّة عمياءُ عند أوّل قتل


# ── دوالُّ نقيّة (بلا شبكة · قابلة للاختبار) ──────────────────────────────────
def ny_minute(ts_ns) -> tuple:
    """‏(تاريخُ نيويورك ISO، دقيقةُ اليوم) لطابعٍ زمنيّ **بالنانو**. تعذّرٌ ⇒ `(None, None)`."""
    try:
        d = dt.datetime.fromtimestamp(int(ts_ns) / 1e9, tz=NY)
    except (TypeError, ValueError, OSError, OverflowError):
        return (None, None)
    return (d.date().isoformat(), d.hour * 60 + d.minute)


def session_bucket(day: str, mod) -> str:
    """‏`regular` / `pre` / `post` / `off` — **بحدود اليوم الفعلية** من التقويم (`V3`).

    فيومُ الإغلاق المبكّر (‏13:00) ما بعده **ممتدٌّ لا نظاميّ**، وتثبيتُ 16:00 يَسِمه
    «نظاميًّا» فيخلط مقياسين. والعطلةُ ⇒ لا جلسةَ نظامية ⇒ كلُّ شيءٍ `off`."""
    if mod is None:
        return "off"
    info = MC.session_info(day)
    op, cl = info.get("open_ny_min"), info.get("close_ny_min")
    if op is None or cl is None:
        return "off"
    if op <= mod < cl:
        return "regular"
    if PRE_OPEN_NY_MIN <= mod < op:
        return "pre"
    if cl <= mod < 20 * 60:
        return "post"
    return "off"


def _pick(header: list, *names) -> int:
    """فهرسُ عمودٍ **من الترويسة** (`V2`) — لا افتراضَ ترتيبٍ ولا اسم. غيابٌ ⇒ `-1`."""
    low = [str(h).strip().lower() for h in (header or [])]
    for n in names:
        if n in low:
            return low.index(n)
    return -1


def reduce_minutes(fh) -> dict:
    """يختزل ملفَّ شموع الدقيقة إلى سماتِ جلسةٍ لكل **(رمز، يوم)**.

    المُرجَع: `{(sym, day): {...}}` بحقول `reg_high/reg_low/reg_close/reg_vol ·
    pre_high/pre_vol · post_high/post_vol · reg_close_mod`.
    🔴 **و`reg_close` = إغلاقُ آخرِ دقيقةٍ نظامية** (بالدقيقة الأكبر) لا آخرِ صفٍّ في
    الملفّ — فترتيبُ الملفّ ليس عقدًا.

    🌙 **و`post_close` أُضيف لـ`T-AH-YEAR` (‏`VY4`) إضافةً لا تبديلًا:** الحارسُ الحيّ
    `extended_last_price` يقرأ **آخرَ** إغلاقِ دقيقةٍ ممتدّة «بأكبر طابعٍ زمنيّ لا
    بترتيب الورود» — بنفس هذي الصيغة حرفيًّا. و`post_high` **لم يُمَسّ** فتبقى أرقامُ
    `ah_result.md` قابلةً لإعادة الإنتاج."""
    rd = csv.reader(fh)
    try:
        header = next(rd)
    except StopIteration:
        return {}
    i_t = _pick(header, "ticker", "symbol")
    i_h = _pick(header, "high")
    i_l = _pick(header, "low")
    i_c = _pick(header, "close")
    i_v = _pick(header, "volume")
    i_w = _pick(header, "window_start", "t", "timestamp")
    if min(i_t, i_h, i_l, i_c, i_v, i_w) < 0:
        raise KeyError(f"ترويسةٌ ناقصة: {header}")
    out: dict = {}
    for row in rd:
        try:
            sym = row[i_t].strip().upper()
            hi, lo = float(row[i_h]), float(row[i_l])
            cl, vol = float(row[i_c]), float(row[i_v])
            day, mod = ny_minute(row[i_w])
        except (IndexError, ValueError, TypeError):
            continue
        if not sym or day is None:
            continue
        b = session_bucket(day, mod)
        if b == "off":
            continue
        k = (sym, day)
        r = out.get(k)
        if r is None:
            r = out[k] = {"reg_high": None, "reg_low": None, "reg_close": None,
                          "reg_close_mod": -1, "reg_vol": 0.0,
                          "pre_high": None, "pre_vol": 0.0,
                          "post_high": None, "post_vol": 0.0,
                          "post_close": None, "post_close_mod": -1}
        if b == "regular":
            r["reg_high"] = hi if r["reg_high"] is None else max(r["reg_high"], hi)
            r["reg_low"] = lo if r["reg_low"] is None else min(r["reg_low"], lo)
            r["reg_vol"] += vol
            if mod > r["reg_close_mod"]:
                r["reg_close_mod"], r["reg_close"] = mod, cl
        elif b == "pre":
            r["pre_high"] = hi if r["pre_high"] is None else max(r["pre_high"], hi)
            r["pre_vol"] += vol
        else:
            r["post_high"] = hi if r["post_high"] is None else max(r["post_high"], hi)
            r["post_vol"] += vol
            if mod > r["post_close_mod"]:        # ‏VY4: بأكبر دقيقة لا بآخر صفّ
                r["post_close_mod"], r["post_close"] = mod, cl
    return out


def post_move_pct(r: dict):
    """حركةُ الافتر = `post_high / reg_close − 1` بالمئة. **`None` إن تعذّر** —
    ولا يُستبدَل بصفرٍ (‏«تعذّرٌ ≠ صفر»)."""
    try:
        rc, ph = float(r.get("reg_close")), float(r.get("post_high"))
    except (TypeError, ValueError):
        return None
    if rc <= 0 or ph <= 0:
        return None
    return (ph / rc - 1.0) * 100.0


def post_last_pct(r: dict):
    """🌙 **مقياسُ الحارس نفسِه** (‏`T-AH-YEAR`/`Y1`): `post_close / reg_close − 1`.

    🔴 هذا ما يقرؤه `ah_guard` عبر `extended_last_price` (آخرُ إغلاقِ دقيقةٍ ممتدّة) —
    بخلاف `post_move_pct` الذي يقرأ **القمّة** وهو ما قاسه `T-AH` فأعطى **سقفًا أعلى**.
    **`None` إن تعذّر** ولا يُستبدَل بصفر (‏«تعذّرٌ ≠ صفر»)."""
    try:
        rc, pc = float(r.get("reg_close")), float(r.get("post_close"))
    except (TypeError, ValueError):
        return None
    if rc <= 0 or pc <= 0:
        return None
    return (pc / rc - 1.0) * 100.0


def calendar_years() -> set:
    """سنواتُ التقويم **المُتحقَّقة** — تُشتقّ من جدول العطلات لا تُكتَب يدويًّا (‏`VY-CAL`).

    فمدُّ التقويم لسنةٍ جديدة يوسّع المدى المسموح **تلقائيًّا**، ولا يبقى رقمٌ مغروسٌ
    يتعفّن (درسُ «الجدولُ المكتوب يتعفّن»)."""
    ys = set()
    for d in list(MC.HOLIDAYS) + list(MC.EARLY_CLOSES):
        try:
            ys.add(int(str(d)[:4]))
        except (TypeError, ValueError):
            continue
    return ys


def trading_days(a: str, b: str) -> list:
    """أيامُ التداول في [a, b]: أيامُ عملٍ ناقصَ عطلاتِ التقويم.

    ⚠️ **لا تُختلَق عطلة:** خارجَ سنوات التقويم المُتحقَّقة تُرجع `[]` ويتولّى النداءُ
    إعلانَ الرفض بخروج 8 (‏`VY-CAL`) — لأن سنةً بلا تقويمٍ مُتحقَّق تَسِم الإغلاقَ
    المبكّر «نظاميًّا» فتخلط ثلاثَ ساعاتٍ ممتدّةٍ بالنظاميّ."""
    try:
        d0, d1 = dt.date.fromisoformat(a), dt.date.fromisoformat(b)
    except (TypeError, ValueError):
        return []
    if d1 < d0:
        return []
    ok = calendar_years()
    if d0.year not in ok or d1.year not in ok:
        return []
    out, d = [], d0
    while d <= d1:
        iso = d.isoformat()
        if d.weekday() < 5 and MC.is_trading_day(iso):
            out.append(iso)
        d += dt.timedelta(days=1)
    return out


def pre_move_pct(r: dict, prev_close):
    """حركةُ ما قبل السوق **مقابل إغلاق اليوم السابق** — و`None` إن لم يكن السابقُ
    في العيّنة (`V5`: مقياسٌ مفبركٌ أسوأُ من غيابِ مقياس)."""
    try:
        pc, ph = float(prev_close), float(r.get("pre_high"))
    except (TypeError, ValueError):
        return None
    if pc <= 0 or ph <= 0:
        return None
    return (ph / pc - 1.0) * 100.0


def ext_vol_share(r: dict):
    """نصيبُ الحجم الممتدّ من **حجم اليوم كلِّه** بالمئة. `None` إن لا حجمَ نظاميّ."""
    reg = float(r.get("reg_vol") or 0.0)
    ext = float(r.get("pre_vol") or 0.0) + float(r.get("post_vol") or 0.0)
    tot = reg + ext
    return None if tot <= 0 else ext / tot * 100.0


def control_verdict(r) -> tuple:
    """`V1` — شاهدُ الضبط: حجمٌ ممتدٌّ **موجبٌ ودون 20%**. غيابُ الرمز ⇒ سقوط."""
    if not isinstance(r, dict):
        return False, "الشاهدُ غائبٌ عن المُخرَج — عطبُ اختزالٍ حتى يُنفى"
    sh = ext_vol_share(r)
    if sh is None:
        return False, "لا حجمَ للشاهد (صفرٌ = عطبٌ حتى يُنفى)"
    if not (CTRL_MIN_PCT < sh < CTRL_MAX_PCT):
        return False, f"نصيبُ الممتدّ {sh:.2f}% خارج [{CTRL_MIN_PCT}, {CTRL_MAX_PCT}]"
    return True, f"نصيبُ الممتدّ {sh:.2f}%"


def bucket_counts(rows: list, threshes=THRESH) -> dict:
    """عددُ الرموز-الأيام التي تتجاوز حركةُ افترها كلَّ عتبة + المقام **الصريح**."""
    vals = [post_move_pct(r) for r in rows]
    ok = [v for v in vals if v is not None]
    out = {"n": len(rows), "measurable": len(ok),
           "unmeasurable": len(vals) - len(ok)}
    for t in threshes:
        out[f"ge_{t:g}"] = sum(1 for v in ok if v >= t)
    return out


def price_band(rc) -> str:
    """شريحةُ السعر (`Y4`) من إغلاقِ الجلسة — مثبَّتةٌ سلفًا. خارجَ المدى ⇒ `""`."""
    try:
        v = float(rc)
    except (TypeError, ValueError):
        return ""
    for lo, hi in PRICE_BANDS:
        if lo < v <= hi:
            return f"${lo:g}-{hi:g}"
    return ""


class YearAcc:
    """🌙 مُراكِمٌ **انسيابيّ** (‏`VY7`): عدّاداتٌ لا صفوف — فسنةٌ ‏≈3 ملايين صفٍّ
    تُسقط الرنر، والانهيارُ يُقرأ «لم يُقَس» لا «سقط القفل».

    يُغذَّى يومًا يومًا بمُخرَج `reduce_minutes`، ويحسب:
    **`Y1`** معدَّلَ مقياس الحارس (`post_close`) وللمقارنة القمّة (`post_high`) عند
    `CURVE` · **`Y2`** فجوةَ التلاشي · **`Y3`** شهرًا شهرًا · **`Y4`** شرائحَ السعر ·
    ووسيطَ نصيبِ الحجم الممتدّ (بمصفوفةِ `float` لا بقائمةِ كائنات)."""

    GROUPS = ("all", "ours")

    def __init__(self, price_max: float = PRICE_MAX):
        from array import array
        self.price_max = float(price_max)
        self.n = dict.fromkeys(self.GROUPS, 0)
        # لكل (مجموعة، مقياس): المقام ثم عدّادُ كلّ عتبة
        self.meas = {(g, m): 0 for g in self.GROUPS for m in ("last", "high")}
        self.ge = {(g, m, t): 0 for g in self.GROUPS
                   for m in ("last", "high") for t in CURVE}
        # ‏Y2: قمّتُه ‏≥ العتبة — كم أغلق دونها؟ (على فئتنا وعلى الكون)
        self.fade_den = {(g, t): 0 for g in self.GROUPS for t in CURVE}
        self.fade_num = {(g, t): 0 for g in self.GROUPS for t in CURVE}
        # ‏Y3 شهريًّا (على فئتنا · مقياسُ الحارس) · و‏Y4 شرائحُ السعر
        self.mon_den, self.mon_ge, self.mon_days = {}, {}, {}
        self.band_den, self.band_ge = {}, {}
        self.shares = array("f")
        self.days = 0

    def ingest(self, day: str, red: dict) -> None:
        self.days += 1
        mon = str(day)[:7]
        self.mon_days[mon] = self.mon_days.get(mon, 0) + 1
        for r in red.values():
            rc = r.get("reg_close")
            try:
                rcf = float(rc)
            except (TypeError, ValueError):
                rcf = None
            is_ours = rcf is not None and 0 < rcf < self.price_max
            pl, ph = post_last_pct(r), post_move_pct(r)
            band = price_band(rcf) if is_ours else ""
            for g in ("all",) + (("ours",) if is_ours else ()):
                self.n[g] += 1
                for m, v in (("last", pl), ("high", ph)):
                    if v is None:
                        continue
                    self.meas[(g, m)] += 1
                    for t in CURVE:
                        if v >= t:
                            self.ge[(g, m, t)] += 1
                if ph is None:
                    continue
                for t in CURVE:                 # ‏Y2 فجوةُ التلاشي
                    if ph >= t:
                        self.fade_den[(g, t)] += 1
                        if pl is None or pl < t:
                            self.fade_num[(g, t)] += 1
            if not is_ours:
                continue
            if pl is not None:                  # ‏Y3 + ‏Y4 على مقياس الحارس
                self.mon_den[mon] = self.mon_den.get(mon, 0) + 1
                if pl >= GUARD_T:
                    self.mon_ge[mon] = self.mon_ge.get(mon, 0) + 1
                if band:
                    self.band_den[band] = self.band_den.get(band, 0) + 1
                    if pl >= GUARD_T:
                        self.band_ge[band] = self.band_ge.get(band, 0) + 1
            sh = ext_vol_share(r)
            if sh is not None:
                self.shares.append(sh)

    def rate(self, g: str, m: str, t: float):
        d = self.meas[(g, m)]
        return None if d <= 0 else self.ge[(g, m, t)] / d * 100.0

    def fade_pct(self, g: str, t: float):
        d = self.fade_den[(g, t)]
        return None if d <= 0 else self.fade_num[(g, t)] / d * 100.0

    def share_median(self):
        if not self.shares:
            return None
        s = sorted(self.shares)
        return s[len(s) // 2]

    def integrity(self, rows: list, group: str) -> tuple:
        """‏VY8 — فحصُ تكاملٍ ذاتيّ: المُراكِمُ يجب أن يطابق `bucket_counts` **بت-بت**
        على نفس الصفوف. فمسارُ السنة يُصادِقه رقمُ `T-AH` المنشور نفسُه، ولو تفرّق
        المسارانِ صار عندنا مقياسان — وهو أسوأُ من الخطأ لأنه يبدو متّسقًا."""
        c = bucket_counts(rows, CURVE)
        if c["measurable"] != self.meas[(group, "high")]:
            return False, (f"المقام: مُراكِم={self.meas[(group, 'high')]} "
                           f"مقابل bucket_counts={c['measurable']}")
        for t in CURVE:
            if c[f"ge_{t:g}"] != self.ge[(group, "high", t)]:
                return False, (f"‏≥{t:g}%: مُراكِم={self.ge[(group, 'high', t)]} "
                               f"مقابل {c[f'ge_{t:g}']}")
        return True, f"مطابقٌ بت-بت على {len(rows):,} صفًّا و{len(CURVE)} عتبة"


# ── الشبكة (فاشلٌ-آمن · يُعلن ولا يصمت) ───────────────────────────────────────
def day_key(day: str) -> str:
    y, m, _ = day.split("-")
    return f"{MIN_PATH}/{y}/{m}/{day}.csv.gz"


def head_size_mb(key: str):
    for ep in FP.ENDPOINTS:
        rc, out, _ = FP.aws_api("head-object", "--bucket", FP.BUCKET,
                                "--key", key, endpoint=ep)
        if rc == 0:
            try:
                import json as _j
                return float(_j.loads(out)["ContentLength"]) / (1024 * 1024), ep
            except (ValueError, KeyError, TypeError):
                continue
    return None, None


def download(key: str, dest: str, endpoint: str) -> bool:
    rc, _, err = FP.aws("cp", f"s3://{FP.BUCKET}/{key}", dest,
                        endpoint=endpoint, timeout=3600)
    if rc != 0:
        log(f"   ⛔ تعذّر التنزيل (rc={rc}): {(err or '')[:180]}")
    return rc == 0


def report_year(acc, mode: str, measured: int, missing: list,
                mb_tot: float, t_red: float, t_start: float) -> int:
    """🌙📏 تقريرُ `T-AH-YEAR` — الأسئلةُ `Y1`-`Y5` بترتيبها المسجَّل، ولا سؤالَ يُضاف.

    ⚖️ **الفرقُ الجوهريّ عن `T-AH`:** العمودُ الحاكم `post_close` (‏= ما يقرؤه
    `ah_guard` فعلًا)، و`post_high` يُعرَض **للمقارنة** لا للحكم."""
    log("=" * 78)
    log("🌙📏 T-AH-YEAR — معايرةُ `ah_guard` (العقد: `ah_year_prereg.md`)")
    log("=" * 78)

    # ── Y1 منحنى الكلفة على **مقياس الحارس** ─────────────────────────────────
    log("③ `Y1` معدَّلُ الحركة عند العتبات — العمودُ الحاكم **إغلاقُ الافتر** "
        "(`post_close` = مقياسُ `ah_guard`) والقمّةُ للمقارنة:")
    for g, name in (("ours", f"فئتُنا (<${PRICE_MAX:g})"), ("all", "الكونُ كلُّه")):
        log(f"   • {name}: ن={acc.n[g]:,} · قابلٌ للقياس بالإغلاق="
            f"{acc.meas[(g, 'last')]:,} · بالقمّة={acc.meas[(g, 'high')]:,}")
        for m, lbl in (("last", "🎯 إغلاقُ الافتر"), ("high", "   القمّة    ")):
            log(f"     {lbl}: " + " · ".join(
                f"‏≥{t:g}%: {acc.ge[(g, m, t)]:,}"
                f" ({(acc.rate(g, m, t) or 0):.2f}%)" for t in CURVE))
    log("   ⚠️ **معدَّلُ الظاهرة لا دقّةُ الحارس** — مرشّحو الصيّاد التاريخيون غيرُ "
        "محفوظين (مسجَّلٌ قبل الرقم) ⇒ لا يُقال «صائب» ولا «مبالغ».")
    log("")

    # ── Y2 فجوةُ التلاشي — الرقمُ الذي يحسم «القمّة أم الإغلاق؟» ───────────────
    log("④ `Y2` فجوةُ التلاشي: من بلغت **قمّتُه** العتبةَ، كم أغلق افترَه **دونها**؟")
    for g, name in (("ours", "فئتُنا"), ("all", "الكون")):
        parts = []
        for t in CURVE:
            f = acc.fade_pct(g, t)
            parts.append(f"‏≥{t:g}%: " + ("—" if f is None else
                         f"{acc.fade_num[(g, t)]:,}/{acc.fade_den[(g, t)]:,}"
                         f" = {f:.1f}%"))
        log(f"   • {name}: " + " · ".join(parts))
    fg = acc.fade_pct("ours", GUARD_T)
    if fg is not None:
        log(f"   🔑 وعند عتبة الحارس {GUARD_T:g}%: **{fg:.1f}%** من قفزات فئتنا "
            f"**تتلاشى** قبل إغلاق الافتر ⇒ رقمُ `T-AH` المنشور (بالقمّة) يبخس بهذي "
            f"النسبة تحديدًا.")
    log("")

    # ── Y3 الثبات شهرًا شهرًا (اختبار «هل تنقلب الإشارة؟») ────────────────────
    log(f"⑤ `Y3` الثبات: معدَّلُ فئتنا عند {GUARD_T:g}% (مقياسُ الحارس) شهرًا شهرًا — "
        f"وشهرٌ دون {MONTH_MIN_DAYS} يومًا **يُعلَن ويُستبعَد من الحكم** (‏VY6):")
    rates = []
    for mon in sorted(acc.mon_den):
        den = acc.mon_den[mon]
        rt = acc.mon_ge.get(mon, 0) / den * 100.0 if den else None
        nd = acc.mon_days.get(mon, 0)
        used = nd >= MONTH_MIN_DAYS
        if used and rt is not None:
            rates.append((rt, mon))
        log(f"   • {mon}: {nd} يومًا · ن={den:,} · "
            + ("—" if rt is None else f"{rt:.2f}%")
            + ("" if used else "  ⚠️ خارج الحكم (أيامٌ قليلة)"))
    if len(rates) >= 2:
        lo, hi = min(rates), max(rates)
        ratio = (hi[0] / lo[0]) if lo[0] > 0 else float("inf")
        log(f"   🔑 أدنى {lo[0]:.2f}% ({lo[1]}) · أقصى {hi[0]:.2f}% ({hi[1]}) ⇒ "
            f"**النسبة ×{ratio:,.2f}** — و`PY3` سجّل «‏≤2×» فهو "
            f"{'✅ صمد' if ratio <= 2.0 else '🔴 سقط ⇒ رقمٌ سنويٌّ واحد لا يصف الظاهرة'}")
    else:
        log("   ⚠️ أشهرٌ أقلُّ من اثنين تدخل الحكم ⇒ **لا حكمَ على الثبات** (يُعلَن).")
    log("")

    # ── Y4 صدقُ العيّنة: هل المعدَّل حسّاسٌ للسعر؟ ────────────────────────────
    log("⑥ `Y4` صدقُ العيّنة — المجتمعُ ليس مرشّحي الصيّاد؛ فهل المعدَّل حسّاسٌ للسعر؟")
    seen = []
    for lo, hi in PRICE_BANDS:
        b = f"${lo:g}-{hi:g}"
        den = acc.band_den.get(b, 0)
        rt = acc.band_ge.get(b, 0) / den * 100.0 if den else None
        seen.append(rt)
        log(f"   • {b}: ن={den:,} · " + ("—" if rt is None else f"{rt:.2f}%"))
    ok = [r for r in seen if r is not None]
    if len(ok) == len(PRICE_BANDS):
        mono = all(ok[i] >= ok[i + 1] for i in range(len(ok) - 1))
        log(f"   🔑 الرتابةُ التنازلية مع السعر (‏`PY2`): "
            f"{'✅ صمد' if mono else '🔴 سقط'} ({' ← '.join(f'{r:.2f}%' for r in ok)})")
    med = acc.share_median()
    log("   نصيبُ الحجم الممتدّ في فئتنا: "
        + ("—" if med is None else f"وسيط {med:.2f}% · ن={len(acc.shares):,}")
        + " ⇒ الافترُ رقيقُ السيولة ⇒ **كلُّ رقمٍ أعلاه سقفٌ متفائل**.")
    log("")

    # ── Y5 الجدوى (معامِلُ التوسيع مطبوعٌ — VY9) ─────────────────────────────
    wall = (time.time() - t_start) / 60.0
    if measured > 0:
        per_day = t_red / measured
        log(f"⑦ `Y5` الجدوى: {mb_tot:,.1f}MB · {measured} يومًا مقيسًا · اختزال "
            f"{t_red:,.1f}ث ⇒ **{per_day:,.1f}ث/يوم** · ساعةُ الحائط "
            f"**{wall:,.1f}د**")
        log(f"   • معامِلُ التوسيع لسنةٍ كاملة = **×252 يومًا** (مطبوعٌ لا مضمَر) ⇒ "
            f"اختزال ‏≈{per_day * 252 / 3600:,.2f} ساعة · "
            f"وبساعةِ الحائط ‏≈{wall / measured * 252 / 60:,.2f} ساعة")
        log(f"   • `PY5` سجّل «‏≤2 ساعة» لهذا المدى ⇒ "
            f"{'✅ صمد' if wall <= 120 else '🔴 سقط'} ({wall:,.1f}د)")
    log("")
    log("🔒 **منحنى كلفةٍ لا قرار:** لا عتبةَ تتغيّر · و`SPLIT_ROSE_MAX_PCT` (‏20% "
        "= نصُّ فيصل على مرجع `ref`) **لم تُقَس ولا تُمَسّ** · والمقيسُ مرجعُ `price` "
        "وحده. وأيُّ تغييرٍ **قرارُ مالكٍ** بعد الأرقام (‏§①).")
    if mode == "range":
        log(f"📌 والمدى **سنةٌ حتى تاريخه لا اثنا عشر شهرًا** (تقويمُنا مُتحقَّقٌ لـ"
            f"{', '.join(str(y) for y in sorted(calendar_years()))} حصرًا — ‏§②) · "
            f"ومفقودٌ {len(missing)} يومًا.")
    log("✅ وبلا انحياز بقاء: الملفّاتُ تحوي كلَّ رمزٍ تداول يومَه بمن شُطب لاحقًا.")
    return 0


def resolve_days() -> tuple:
    """‏(الأيام، الوضع، خطأ) — مدًى إن أُعطي `AH_FROM`/`AH_TO`، وإلّا `AH_DAYS` كما هو.

    ‏`VY-CAL`: مدًى خارج سنوات التقويم المُتحقَّقة ⇒ **رفضٌ بخروج 8** لا تخمينُ عطلات."""
    if FROM_DAY or TO_DAY:
        if not (FROM_DAY and TO_DAY):
            return [], "range", "يلزم `AH_FROM` و`AH_TO` معًا"
        ds = trading_days(FROM_DAY, TO_DAY)
        if not ds:
            ys = ", ".join(str(y) for y in sorted(calendar_years())) or "—"
            return [], "range", (f"مدًى غيرُ صالحٍ أو خارج تقويمنا المُتحقَّق ({ys}) — "
                                 f"وسنةٌ بلا تقويمٍ مُتحقَّق تَسِم الإغلاقَ المبكّر "
                                 f"«نظاميًّا» فتخلط مقياسين")
        return ds, "range", ""
    return list(DAYS), "days", ""


def main() -> int:
    log("=" * 78)
    log("🌙 T-AH — عمى الافتر من شموع الدقيقة المجمَّعة · **قياسُ أساسٍ لا حكم**")
    log("=" * 78)
    days, mode, err = resolve_days()
    if err:
        log(f"⛔ {err} ⇒ خروج 8 (‏VY-CAL) — لا رقمَ يُنشَر.")
        return 8
    globals()["DAYS"] = days
    log(f"🔗 البكت: {FP.BUCKET} · المسار: {MIN_PATH}")
    if mode == "range":
        log(f"   📏 المدى: {FROM_DAY} → {TO_DAY} · **أيامُ تداولٍ مستهدَفة "
            f"{len(days)}** (تقويمٌ مُتحقَّق: "
            f"{', '.join(str(y) for y in sorted(calendar_years()))})")
        log(f"   🎯 منحنى الكلفة (مثبَّتٌ قبل الأرقام): "
            f"{' · '.join(f'{t:g}%' for t in CURVE)}")
    else:
        log(f"   الأيام: {', '.join(days)}")
    log(f"   شاهدُ الضبط: {WITNESS} · فئتُنا: سعرٌ دون ${PRICE_MAX:g} · "
        f"عتبةُ الحارس: {GUARD_T:g}%")
    log("")

    sh = FP.creds_shape()
    log("⓪ شكلُ المفتاحين (لا تُطبَع قيمة): "
        f"معرِّف طول={sh['id_len']} · UUID={'✅' if sh['id_uuid_shaped'] else '❌'} · "
        f"سرّ طول={sh['sec_len']}")
    if FP.resolve_swapped_creds():
        log("   🔁 **صُحّح انقلابُ المعرِّف/السرّ لهذي التشغيلة فقط** — وما في "
            "GitHub لم يتغيّر.")
    if not FP.creds_present():
        log("⛔ المفتاحان غائبان ⇒ خروج 2 (تهيئة) — لا رقمَ يُنشَر.")
        return 2
    log("")

    frames: dict = {}
    keep_frames = len(DAYS) <= KEEP_FRAMES_MAX      # ‏VY7: سنةٌ لا تُحفَظ في الذاكرة
    acc = YearAcc(PRICE_MAX)
    t_red = 0.0
    mb_tot = 0.0
    missing, ctrl_bad = [], []
    t_start = time.time()
    for i, day in enumerate(DAYS, 1):
        if (time.time() - t_start) / 60.0 > BUDGET_MIN:
            log(f"   ⏹️ بلغت ميزانيةَ الوقت {BUDGET_MIN:g}د عند اليوم {i}/{len(DAYS)}"
                f" ⇒ **يُوقَف بإعلان** ويحكم حارسُ التغطية (‏VY6).")
            break
        info = MC.session_info(day)
        key = day_key(day)
        mb, ep = head_size_mb(key)
        if mb is None:
            # يومٌ بلا ملفّ = عطلةٌ لا يعرفها تقويمُنا أو فجوةُ مزوّد. في وضع المدى
            # **يُعَدّ ويُعلَن** ويحكم حارسُ التغطية — فإسقاطُ السنة كلِّها ليوم
            # واحد كان سيقتل القياس (ولا نُخمّن عطلةً بدل التقويم).
            if mode == "range":
                missing.append(day)
                log(f"① {day}: لا ملفّ ⇒ **يُعَدّ مفقودًا ويُعلَن** "
                    f"({len(missing)} حتى الآن)")
                continue
            log(f"⛔ {day}: لا ملفَّ على أيّ منفذ ({key}) ⇒ خروج 4.")
            return 4
        log(f"① {day} ({info['session_type']} · إغلاق "
            f"{info['close_ny_min']}د) ≈ {mb:,.1f}MB · المنفذ {ep}")
        if mb_tot + mb > CAP_MB:
            log(f"   ⛔ يتجاوز السقفَ المُعلَن {CAP_MB:g}MB ⇒ يُوقَف بإعلانٍ لا صمتًا.")
            return 4
        dest = f"/tmp/ah-{day}.csv.gz"
        if not download(key, dest, ep):
            return 4
        mb_tot += mb
        t0 = time.time()
        try:
            with gzip.open(dest, "rt", newline="") as fh:
                red = reduce_minutes(fh)
        except KeyError as e:
            log(f"⛔ {e} ⇒ خروج 5.")
            return 5
        except (OSError, EOFError, gzip.BadGzipFile) as e:
            log(f"⛔ تعذّر فكُّ الضغط: {e} ⇒ خروج 4.")
            return 4
        finally:
            try:
                os.remove(dest)                  # 🧹 المساحةُ لا تتراكم
            except OSError:
                pass
        t_red += time.time() - t0
        # ‏VY1: الشاهدُ يُفحَص في **كلّ** يومٍ مقيس لا مرّةً واحدة (يومٌ صامتٌ = عطب)
        wok, wwhy = control_verdict(red.get((WITNESS.upper(), day)))
        if not wok:
            ctrl_bad.append((day, wwhy))
        acc.ingest(day, red)
        if keep_frames:
            frames.update(red)
        log(f"   ✅ اختُزل إلى {len(red):,} (رمز، يوم) في {time.time() - t0:,.1f}ث"
            f" · أُسقط الخام" + ("" if wok else f" · ⚠️ الشاهد: {wwhy}"))
    log("")

    # ── V1/VY1 شاهدُ الضبط (إلزاميّ · قبل أيّ رقم · **في كلّ يومٍ مقيس**) ──────
    measured = acc.days
    if measured <= 0:
        log("⛔ لم يُقَس يومٌ واحد ⇒ **لا رقمَ يُنشَر** · خروج 3.")
        return 3
    bad_pct = len(ctrl_bad) / measured * 100.0
    ok = bad_pct <= 5.0
    log(f"② شاهدُ الضبط `{WITNESS}` (‏V1/VY1): {'✅' if ok else '❌'} سقط في "
        f"{len(ctrl_bad)} من {measured} يومًا مقيسًا = {bad_pct:.1f}% "
        f"(الحدّ 5%)")
    for d, why in ctrl_bad[:5]:
        log(f"   ⚠️ {d}: {why}")
    if not ok:
        log("⛔ الشاهدُ سقط ⇒ **لا رقمَ يُنشَر** (الصفرُ عطبٌ حتى يُنفى) · خروج 3.")
        return 3
    if frames:
        wrow = next((r for (sym, _), r in frames.items()
                     if sym == WITNESS.upper()), None)
        if wrow:
            log(f"   نظاميّ حجم={wrow['reg_vol']:,.0f} · قبل={wrow['pre_vol']:,.0f} · "
                f"بعد={wrow['post_vol']:,.0f} · إغلاق={wrow['reg_close']}")
    log("")

    # ── VY6 التغطية — **قبل** أيّ رقمٍ سنويّ (فجوةٌ صامتة تُقرأ تغطيةً كاملة) ──
    cover = measured / len(DAYS) * 100.0 if DAYS else 0.0
    if mode == "range":
        log(f"②-ب `VY6` التغطية: قِيس {measured} من {len(DAYS)} يومَ تداولٍ "
            f"مستهدَف = **{cover:.1f}%** · مفقودٌ {len(missing)}"
            + (f" ({', '.join(missing[:8])}{'…' if len(missing) > 8 else ''})"
               if missing else ""))
        if cover < COVER_MIN_PCT:
            log(f"⛔ التغطيةُ دون {COVER_MIN_PCT:g}% ⇒ الأرقامُ **أرضيّةٌ لا تُنشَر "
                f"حكمًا** · خروج 6.")
            return 6
        log("")

    # ── VY8 فحصُ التكامل الذاتيّ (حين تُحفَظ الصفوف) ─────────────────────────
    if frames:
        _ours = [r for r in frames.values()
                 if isinstance(r.get("reg_close"), float)
                 and 0 < r["reg_close"] < PRICE_MAX]
        iok, iwhy = acc.integrity(_ours, "ours")
        log(f"②-ج `VY8` فحصُ التكامل الذاتيّ (مُراكِمٌ مقابل `bucket_counts`): "
            f"{'✅' if iok else '❌'} {iwhy}")
        if not iok:
            log("⛔ المسارانِ اختلفا ⇒ **مقياسان لا مقياس** · خروج 7.")
            return 7
        log("")

    # ── Q1 نصيبُ الحركة خارج النظاميّ (‏`T-AH` الأصليّ — يلزمه حفظُ الصفوف) ────
    allr = list(frames.values())
    ours = [r for r in allr
            if isinstance(r.get("reg_close"), float) and 0 < r["reg_close"] < PRICE_MAX]
    if not frames:
        log(f"③ `Q1`/`Q1-ب`/`Q2`/`Q3` بصيغة `T-AH` **تُتخطّى في وضع المدى** "
            f"(‏VY7: {measured} يومًا ‏≈{acc.n['all']:,} صفًّا لا يُحفَظ في الذاكرة) "
            f"⇒ الأرقامُ أدناه من المُراكِم، **ومسارُه مُصادَقٌ بت-بت** بفحص `VY8` "
            f"على عيّنة `T-AH` المنشورة.")
        log("   📌 وما قبل السوق **ليس من أسئلة `T-AH-YEAR`** المسجَّلة — الحارسُ "
            "لا يقرؤه (‏`extended_last_price` نافذتُها ما بعد الإغلاق) ⇒ لا يُقاس هنا.")
        log("")
        return report_year(acc, mode, measured, missing, mb_tot, t_red, t_start)
    log("③ `Q1` حركةُ الافتر فوق إغلاق النظاميّ — العتباتُ مثبَّتةٌ قبل الأرقام:")
    for name, rows in (("الكونُ كلُّه", allr), (f"فئتُنا (<${PRICE_MAX:g})", ours)):
        c = bucket_counts(rows)
        m = c["measurable"] or 1
        log(f"   • {name}: ن={c['n']:,} · قابلٌ للقياس={c['measurable']:,} "
            f"· غيرُ قابل={c['unmeasurable']:,}")
        log("     " + " · ".join(
            f"‏≥{t:g}%: {c[f'ge_{t:g}']:,} ({c[f'ge_{t:g}'] / m * 100:.2f}%)"
            for t in THRESH))
    log("")

    # ── Q1-ب حركةُ ما قبل السوق — **تُقاس فقط إن كان السابقُ في العيّنة** (V5) ──
    pre_ok, pre_ge = 0, 0
    for (sym, day), r in frames.items():
        try:
            prev = (dt.date.fromisoformat(day) - dt.timedelta(days=1)).isoformat()
        except ValueError:
            continue
        pm = pre_move_pct(r, (frames.get((sym, prev)) or {}).get("reg_close"))
        if pm is None:
            continue
        pre_ok += 1
        if pm >= GUARD_T:
            pre_ge += 1
    log(f"③-ب `Q1-ب` ما قبل السوق مقابل إغلاق **اليوم السابق**: قابلٌ للقياس="
        f"{pre_ok:,}" + (f" · ‏≥{GUARD_T:g}%: {pre_ge:,}" if pre_ok else
                         " ⇒ **لا يُقاس** (اليومُ السابق خارج العيّنة — `V5`)"))
    log("")

    # ── Q2 معدَّلُ الأساس عند عتبة الحارس ────────────────────────────────────
    co = bucket_counts(ours, (GUARD_T,))
    mo = co["measurable"] or 1
    log(f"④ `Q2` معايرةُ `ah_guard` عند {GUARD_T:g}% على فئتنا: "
        f"{co[f'ge_{GUARD_T:g}']:,} من {co['measurable']:,} = "
        f"**{co[f'ge_{GUARD_T:g}'] / mo * 100:.2f}%**")
    log("   ⚠️ **يقيس معدَّلَ الظاهرة لا دقّةَ الحارس** — مرشّحو الصيّاد التاريخيون "
        "غيرُ محفوظين (مسجَّلٌ قبل الرقم).")
    log("")

    # ── Q3 نصيبُ الحجم الممتدّ (وصفيّ) ───────────────────────────────────────
    shares = [s for s in (ext_vol_share(r) for r in ours) if s is not None]
    if shares:
        shares.sort()
        med = shares[len(shares) // 2]
        log(f"⑤ `Q3` نصيبُ الحجم الممتدّ في فئتنا: وسيط {med:.2f}% · "
            f"ن={len(shares):,}")
    else:
        log("⑤ `Q3` لا حجمَ قابلًا للقياس (يُعلَن ولا يُخمَّن).")

    # ── Q4 الجدوى (معامِلُ التوسيع مطبوعٌ — V6) ──────────────────────────────
    if mb_tot > 0 and DAYS:
        per_day = t_red / len(DAYS)
        log("")
        log(f"⑥ `Q4` الجدوى: {mb_tot:,.1f}MB لـ{len(DAYS)} يوم · اختزال "
            f"{t_red:,.1f}ث ⇒ **{per_day:,.1f}ث/يوم**")
        log(f"   • معامِلُ التوسيع لسنةٍ = **×252 يومًا** (مطبوعٌ لا مضمَر) ⇒ "
            f"اختزال ‏≈{per_day * 252 / 3600:,.1f} ساعة · "
            f"وبالتوازي 8 ‏≈{per_day * 252 / 3600 / 8:,.1f} ساعة")
        log("   ⚠️ ورقمُ التنزيل غيرُ مقيسٍ هنا منفصلًا (مدموجٌ في `s3 cp`) ⇒ "
            "**أرضيّةٌ لا سقف**.")
    log("")
    log("🔒 **قياسُ أساسٍ لا حكم:** لا عتبةَ تتغيّر · ولا `ah_guard` يُمَسّ · وأيُّ "
        "معايرةٍ تلزمها سنةٌ كاملة **بتسجيلٍ جديد وإذن المالك**.")
    log(f"📌 وعيّنةُ {len(DAYS)} يومٍ **لا تحكم** — الأرقامُ وصفيّةٌ لجدوى (‏§④-4).")
    log("")
    # 🌙 وتقريرُ السنة يُطبَع هنا أيضًا — فالعيّنةُ الصغيرة **تُصادِق مسارَه**
    #    (‏VY8 أعلاه قارن العدّادات بت-بت)، وهو مسارُ قياسٍ واحدٌ لا نسختان.
    return report_year(acc, mode, measured, missing, mb_tot, t_red, t_start)


if __name__ == "__main__":
    sys.exit(main())
