#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🔬 T-METHOD — أداة «النهج العلمي» (`method_prereg.md` · `FAISAL_SCIENTIFIC_METHOD.md`).

🔒 **بحث/قياس — خارج الإنتاج تمامًا:** لا تُستورَد في `Super_stock.py` (مقفول)، ولا
تكتب حالة، ولا تمسّ بوّابةً ولا عتبة. تُعيد استعمال **دوالّ الإنتاج نفسها**
(`trigger_state` · `spike_info` · `group_pump_scar` · `_resolve_arm`) فيستحيل أن
ينحرف المقيس عن المُشغَّل.

**البنية الأربع الإلزامية** (‏مراجعة خصومية 2026-08-01، `method_prereg.md` §⑧-مكرّر):
  ① **استبعاد التقسيمات** — البيانات المعدَّلة **تُصنّع الحدث المؤسِّس نفسه**
     («وصل 17 قبل شهر ثم 3.10» = بصمة التقسيم العكسيّ حرفيًّا) ⇒ `split_in_window`
     تُقصي وتَعُدّ، والصفر يُعلَن `no-op`.
  ② **فهرس SEC مؤرَّخ** — `dated_offerings` تقرأ **كلّ** `filings.recent` بلا قصٍّ
     زمنيّ (‏`sec_recent_filings` يقصّ عند `today−N` ⇒ يُرجع `None` دائمًا في المشي
     فيُقرأ الشرط **مستوفًى** والاختبارات خضراء = بصمة الـ`no-op` بعينها).
  ③ **اختبار السببية** — `walk` تمرّر `df.iloc[:i]` حصرًا، فناتجُ أيّ لحظة **لا
     يتغيّر** بإلحاق شموعٍ لاحقة («**آخر** اختبار» لا يُعرَف إلا بأثرٍ رجعيّ).
  ④ **استبعاد رموز المصدر** — `SOURCE_SYMBOLS` (UPC وما ورد في الصور) خارج عيّنة
     الحكم، وتُستعمل **شاهد توصيلٍ فقط** (سابقة استبعاد GEOS في E2).
"""
from __future__ import annotations

import datetime as dt
import json

import numpy as np

# ④ رموز الصور الستّ — **خارج عيّنة الحكم** (‏`in-sample`: الصور وصلت بعد +99.76%).
SOURCE_SYMBOLS = frozenset({"UPC"})

# نافذة الانتظار الحرفية من `IMG_0489`: «20 < 30 يوم».
DECLINE_MIN_BARS = 20
DECLINE_MAX_BARS = 30

_OFF_CACHE_PATH = "sec_offering_index.json"


# ═══════════════════ ① استبعاد التقسيمات ═══════════════════
def split_in_window(splits, start, end) -> bool:
    """① هل وقع تقسيمٌ داخل `[start, end]`؟ — **الحارس الأخطر**.

    بصمةُ الوصفة («صعودٌ عالٍ قبل شهر ثم سعرٌ منخفض») هي **حرفيًّا** بصمة التقسيم
    العكسيّ في السلسلة **المعدَّلة** — فبلا هذا الحارس تنتقي الذراعُ مقسّمين
    عكسيًّا وتُسمّيهم «صاعدين». يقبل `pandas.Series` أو قائمة أزواج.
    🔒 **فاشلة-آمنة نحو الإقصاء**: تالفٌ/غير مقروء ⇒ `True` (يُقصى ويُعَدّ) —
    لأن الشكّ هنا يُفسد الحدث المؤسِّس نفسه لا حقلًا عرضيًّا."""
    if splits is None:
        return False                     # لا سياق تقسيمات = لا إقصاء (يُعلَن)
    try:
        items = (list(zip(splits.index, splits.values))
                 if hasattr(splits, "iloc") else list(splits))
    except Exception:                                            # noqa: BLE001
        return True
    try:
        s = start.date() if hasattr(start, "date") else start
        e = end.date() if hasattr(end, "date") else end
    except Exception:                                            # noqa: BLE001
        return True
    # ⚠️ التفكيك نفسه داخل الحارس: عنصرٌ تالف (‏نصٌّ مفرد) كان **يرمي** بدل أن
    #    يُقصي — والعقد «فاشلة-آمنة نحو الإقصاء». كشفه أوّل فحصٍ دخانيّ.
    for it in items:
        try:
            d, ratio = it
            dd = d.date() if hasattr(d, "date") else d
            if float(ratio) <= 0:
                continue
        except Exception:                                        # noqa: BLE001
            return True
        if s <= dd <= e:
            return True
    return False


# ═══════════════════ ② فهرس SEC مؤرَّخ ═══════════════════
def parse_dated_offerings(recent: dict, forms=None) -> list:
    """② يستخرج **كلّ** النشرات النهائية بتواريخها من `filings.recent` — **بلا قصٍّ
    زمنيّ**، وهو الفرق الحاسم عن `sec_recent_filings`.

    النماذج الافتراضية = **النشرات النهائية فقط** (`424B1/424B4/424B5`) مطابقةً
    لـ`_FOUNDING_OFFERING_FORMS` الإنتاجية؛ و`S-1/S-3/F-3/EFFECT/424B3` **روتينية
    تُستبعَد عمدًا** (قرارٌ مدوَّن). دالّة **نقيّة**."""
    forms = tuple(forms or ("424B1", "424B4", "424B5"))
    out = []
    try:
        fl = list(recent.get("form") or [])
        dl = list(recent.get("filingDate") or [])
    except Exception:                                            # noqa: BLE001
        return out
    for f, d in zip(fl, dl):
        if str(f).strip().upper() in forms and d:
            out.append(str(d)[:10])
    return sorted(set(out))


def offering_before(dates, when, lookback_days=120) -> bool:
    """هل هناك نشرةٌ نهائية في `[when−lookback, when]`؟ — **بلا نظرٍ مستقبليّ**
    (لا تُقرأ نشرةٌ بعد `when`). دالّة **نقيّة**."""
    if not dates or when is None:
        return False
    try:
        w = when.date() if hasattr(when, "date") else when
        lo = w - dt.timedelta(days=int(lookback_days))
    except Exception:                                            # noqa: BLE001
        return False
    for d in dates:
        try:
            dd = dt.date.fromisoformat(str(d)[:10])
        except Exception:                                        # noqa: BLE001
            continue
        if lo <= dd <= w:
            return True
    return False


def load_offering_index(path=None) -> dict:
    """فهرسٌ على القرص `{رمز: [تواريخ]}` — يُبنى مرّةً ويُعاد استعماله."""
    try:
        with open(path or _OFF_CACHE_PATH, encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:                                            # noqa: BLE001
        return {}


# ═══════════════════ الحدث المؤسِّس (البند الناقص الوحيد) ═══════════════════
def peak_and_decline(high, close=None):
    """📈 **قمّةٌ حديثة ثم هبوط** — البند الوحيد غير المبنيّ عندنا.

    🔴 **ولا تُستعمل `behavior_rise_profile.recency_bars` مكانها**: تُحسب على
    `c[:n-BASE_WINDOW]` ⇒ **مُزاحةٌ 15 جلسة**، واستعمالها لقياس «20 < 30 يوم»
    يقلب الحكم على الشرط نفسه (اعتراض ⑧ في المراجعة الخصومية).

    يُرجع `{peak_idx, bars_since_peak, peak, rise_pct}` أو `None`.
    `rise_pct` = صعودُ القمّة عن **أدنى قاعٍ سبقها** (‏«سهم صاعد نسبه عاليه»).
    دالّة **نقيّة** · تقرأ المُمرَّر وحده ⇒ **سببيّةٌ بنيويًّا**."""
    try:
        h = np.asarray(high, dtype=float)
    except Exception:                                            # noqa: BLE001
        return None
    if h.size < 5 or not np.isfinite(h).any():
        return None
    pk = int(np.nanargmax(h))
    if pk <= 0:
        return None
    pre = h[:pk]
    base = float(np.nanmin(pre)) if pre.size else None
    if not base or base <= 0:
        return None
    return {"peak_idx": pk, "bars_since_peak": int(h.size - 1 - pk),
            "peak": float(h[pk]), "rise_pct": (float(h[pk]) / base - 1.0) * 100.0}


def founding_context(df, rise_min, win_bars,
                     dmin=DECLINE_MIN_BARS, dmax=DECLINE_MAX_BARS):
    """🏛️ **تعريف المجتمع** (`IMG_0486`/`IMG_0489`): صعودٌ حديث عالٍ **ثم** هبوطٌ
    20-30 يومًا. يُرجع dict أو `None`. نقيّة.

    `rise_min` و`win_bars` **يُمرَّران** من ثوابت الإنتاج (`EXPLOSION_PCT` ·
    `PRIOR_SPIKE_WINDOW`) — **لا رقمَ مُبتكَر**، و`dmin/dmax` **حرفيّان من الصورة**."""
    try:
        tail = df.tail(int(win_bars) + int(dmax) + 5)
        pd_ = peak_and_decline(tail["High"].astype(float).values)
    except Exception:                                            # noqa: BLE001
        return None
    if not pd_:
        return None
    if pd_["rise_pct"] < float(rise_min):
        return None
    if not (int(dmin) <= pd_["bars_since_peak"] <= int(dmax)):
        return None
    return pd_


# ═══════════════════ ③ المشي السببيّ + الحسم ═══════════════════
def method_signal(S, df, splits=None, off_dates=None, pump=None):
    """🔬 إشارةُ «النهج العلمي» على إطارٍ **مبتور عند لحظة القرار**.

    الترتيب مقصود — الأرخص أوّلًا (بوّابة تكلفة كالصيّاد):
      ① الحدث المؤسِّس (‏OHLCV نقيّ) · ② `trigger_state` الإنتاجية · ③ حارس
      التقسيم · ④ القروب · ⑤ الطرح.
    🔒 **سببيّةٌ بنيويًّا:** كلُّ ما تقرأه هو `df` المُمرَّر — فإلحاق شمعةٍ لاحقة
    **لا يغيّر مخرَجًا واحدًا في الماضي** (‏«**آخر** اختبار» لا يُعرَف إلا بأثرٍ
    رجعيّ، وهو التسريب المركزيّ الذي طعنت به المراجعة).
    يُرجع dict أو `None`، وسببُ الإقصاء في `skip`."""
    if df is None or len(df) < 40:
        return None
    fc = founding_context(df, S.CONFIG["EXPLOSION_PCT"],
                          S.CONFIG["PRIOR_SPIKE_WINDOW"])
    if not fc:
        return None
    ts = S.trigger_state(df)          # عتباتٌ إنتاجية — صفر ضبط (§⑧-مكرّر ④)
    if not (ts and ts.get("ok")):
        return None
    when = df.index[-1]
    # ① حارس التقسيم: النافذة = من القمّة حتى لحظة القرار
    try:
        w0 = df.index[max(0, len(df) - 1 - fc["bars_since_peak"]
                          - int(S.CONFIG["PRIOR_SPIKE_WINDOW"]))]
    except Exception:                                            # noqa: BLE001
        w0 = df.index[0]
    if split_in_window(splits, w0, when):
        return {"skip": "split_in_window"}
    # ④ القروب — يُمرَّر محسوبًا من المُنادي (قفل: لا اسمَ لها داخل جذرٍ مقفول)
    if pump:
        return {"skip": "group_pump"}
    # ⑤ الطرح — الفهرس المؤرَّخ؛ وغيابُه **يُعلَن غير مُختبَر** لا مستوفًى
    if off_dates is not None and offering_before(off_dates, when):
        return {"skip": "offering"}
    return {"ok": True, "when": str(getattr(when, "date", lambda: when)()),
            "bottom": ts.get("bottom"), "rsi": ts.get("rsi"),
            "swept_pct": ts.get("swept_pct"), "rise_pct": fc["rise_pct"],
            "bars_since_peak": fc["bars_since_peak"], "peak": fc["peak"],
            "offer_tested": off_dates is not None}


def walk(S, sym, df, splits=None, off_dates=None, pump=None,
         step=1, fwd=60, cov=None):
    """③ **مشيٌ سببيّ**: لكل جلسة `i` تُنادى `method_signal` على `df.iloc[:i]`
    حصرًا ⇒ **يستحيل** أن تُقرأ شمعةٌ لاحقة. ثم يُحسم بـ`_resolve_arm` **وحده**
    (‏`F-L1`: الهدف من `filled+1` والوقف من `filled` — مصدرُ حسمٍ واحد لا ثانٍ).

    الدخول/الوقف **حرفيّان من `IMG_0486`** («الدخول عند أقل سعر 3.20 مع وقف 3»
    حول مستوى 3.10) ⇒ نسبةً: الدخول `+3.2%` فوق القاع والوقف `−3.2%` تحته.
    والهدف `t1` = **القمّة** (رأسُ ما قبل الانهيار) — بنيويّ لا نسبةٌ مجرّدة."""
    out, last = [], -10 ** 9
    c = cov if cov is not None else {}
    for i in range(60, len(df), max(1, int(step))):
        if i - last < 5:                     # لا إشارتان متلاصقتان لنفس الحدث
            continue
        sig = method_signal(S, df.iloc[:i], splits=splits,
                            off_dates=off_dates, pump=pump)
        if not sig:
            continue
        if sig.get("skip"):
            c[sig["skip"]] = c.get(sig["skip"], 0) + 1
            continue
        last = i
        bot = float(sig["bottom"] or 0)
        if bot <= 0:
            c["no_bottom"] = c.get("no_bottom", 0) + 1
            continue
        entry, stop = bot * 1.032, bot * 0.968
        # 🎯 **الهدف الأوّل حرفيًّا من `IMG_0486`: «راس شمعة الفجوه الهابطه 8»** —
        #    لا القمّة (17.96). استعمالُ القمّة جعل `t1` بعيدًا بعدًا يستحيل بلوغُه
        #    ⇒ نسبةُ نجاحٍ صفر بالبناء (كشفته التشغيلة الأولى لا القراءة).
        #    🔒 وتُنادى على **الإطار المبتور** حصرًا (اعتراض ③: الإطار الكامل =
        #    هدفٌ من المستقبل، والاختبارات تبقى خضراء).
        t1 = None
        try:
            _g = S.falling_gap_candle(df.iloc[:i], price=entry)
            t1 = float((_g or {}).get("head") or 0) or None
        except Exception:                                        # noqa: BLE001
            t1 = None
        if t1 is None or t1 <= entry:
            c["no_gap_target"] = c.get("no_gap_target", 0) + 1
            continue
        fut = df.iloc[i:i + int(fwd)]
        if len(fut) < 5:
            c["short_fwd"] = c.get("short_fwd", 0) + 1
            continue
        hi = fut["High"].values.astype(float)
        lo = fut["Low"].values.astype(float)
        cl = fut["Close"].values.astype(float)
        op = fut["Open"].values.astype(float)
        filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
        if filled is None:
            c["no_fill"] = c.get("no_fill", 0) + 1
            continue
        oc, ret, _, _ = S._resolve_arm(hi, lo, cl, op, entry, stop, t1, filled)
        mg = (float(max(hi[filled + 1:])) / entry - 1.0) * 100.0 \
            if filled + 1 < len(hi) else 0.0
        out.append({"symbol": sym, "date": sig["when"], "outcome": oc,
                    "ret": ret, "entry": round(entry, 4), "stop": round(stop, 4),
                    "t1": round(t1, 4), "mg_pre_stop": round(mg, 1),
                    "rise_pct": round(sig["rise_pct"], 1),
                    "bars_since_peak": sig["bars_since_peak"],
                    "rsi": sig["rsi"], "offer_tested": sig["offer_tested"]})
    return out
