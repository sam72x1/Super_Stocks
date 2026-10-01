# -*- coding: utf-8 -*-
"""🛡️ سلامةُ البيانات قبل كلّ مخرَج — الطزاجةُ والإجراءاتُ المؤسسيّة وحالةُ الصلاحيّة (أمرُ المالك 2026-10-01 «CRITICAL MISSION»).

العلّةُ المقيسة (`data_integrity_result.md` · مِجَسّ `36863655877`): البوتُ يقرأ شموعًا **مسوّاةً بالتقسيم** (TradingView/ياهو) ولا يعرف
**متى** وقع التقسيم ولا **أيّ جلسةٍ** تمثّلها آخرُ شمعة — فأخرج DLXY بعد تقسيمٍ عكسيّ 1:5 يوم 09-28 بقمّةٍ مسوّاةٍ $22.25 لم تُتداوَل
(فعليًّا $4.45 قبل التقسيم) وهبوطٍ 90% هو هبوطُ ما قبل التقسيم · وقرأ 66 إطارًا آخرُ شمعتها أقدمُ من الجلسة «اليوم» (وصل منها 4 مخرجًا) ·
**وياهو وحدَه لا يكفي مصدرًا للتقسيم**: لم يُدرج تقسيمَ DLXY أصلًا (و19 غيرَه) وأدرجه تقويمُ ناسداك الرسميّ.

هذي الوحدةُ **نقيّةٌ وقابلةٌ للحقن** (لا شبكةَ إلّا عبر جالبٍ يُمرَّر): تُقيّم كلَّ رمزٍ بحالةٍ صريحة ثمّ تطبّق **سياسةً قابلةً للضبط**:

  الحالة                     | المعنى                                                                         | الافتراض
  ---------------------------|---------------------------------------------------------------------------------|-----------
  VALID                      | آخرُ شمعةٍ = الجلسةُ المتوقَّعة · لا إجراءَ مؤسسيًّا حديث                         | allow
  STALE                      | آخرُ شمعةٍ أقدمُ من آخر جلسةٍ مكتملة · أو شمعةُ ياهو محشوّة بحجم صفر (بلا صفقة)    | block
  INCOMPLETE                 | الإطارُ فارغ · أو إغلاقُ آخر شمعةٍ مفقود                                           | block
  SPLIT_UNADJUSTED           | قفزةٌ في السلسلة تساوي نسبةَ تقسيمٍ مُدرَج (المزوّدُ لم يسوِّه)                    | block
  CORPORATE_ACTION_PENDING   | تقسيمٌ عكسيّ حديث **لم تكتمل بعده وصفةُ فيصل** · أو مرجعُ القراءة قبل التقسيم       | quarantine
  CORPORATE_ACTION_ANNOUNCED | تقسيمٌ مُعلَن **لم يُنفَّذ بعد** (المستوياتُ ستتغيّر بالتقسيم)                       | warn
  RECENT_SPLIT               | تقسيمٌ داخل نافذة «حديث» اكتملت بعده الوصفة (أو أماميّ)                            | warn
  SOURCE_CONFLICT            | المصدران يختلفان على **نسبة** التقسيم أو على إغلاق الجلسة نفسِها                   | block
  SYMBOL_CHANGED             | الرمزُ خارج كون ناسداك اليوم (مشطوب/أُعيدت تسميتُه؟)                              | block
  MARKET_CLOSED              | لا جلسةَ مكتملة معروفة في التقويم                                                 | warn
  UNVERIFIED                 | مصدرا التقسيمات تعذّرا معًا — لا يُدّعى «لا تقسيم»                                 | warn

⚖️ **لا مدّةَ احتجازٍ مختلَقة:** «حديث» = نافذةُ البوت القائمة `SPLIT_LOOKBACK_DAYS` (120 يومًا · رادارُ التقسيم والصيّاد) · و«اكتمال
الوصفة» = نصُّ فيصل للمقسّم عكسيًّا **«ضرب قاع الـ÷2 وحافظ عليه 3ج»** (`IMG_0150`/`IMG_0151`) بمرجع الصيّاد نفسِه **قمّةِ ما بعد التقسيم**
(`_post_split_high` · «الهبوط يُقاس من قمة ما بعد آخر تقسيم عكسي لا قمة 52أ المنفوخة» `IMG_0143`/`IMG_0144`) ونطاقِه نفسِه
(`SPLIT_RADAR_BAND_LOW` · وتسامحِ `_split_setup_probe`) — تُقرأ **بالاسم** والصيّادُ **لا يُمَسّ**. وقبل اكتمالها السهمُ في طور «ما بعد
التقسيم» الذي يعرفه الصيّادُ وحدَه · و«مرجعُ القراءة قبل التقسيم» = القاعدةُ نفسُها: هبوطٌ يُقاس من قمّةٍ سابقةٍ للتقسيم ليس هبوطَ فيصل.

🔁 **مفتاحٌ يرجع بت-بت:** `DQ_GATE=0` (بيئة) ⟵ `enabled()` False ⟵ كلُّ بوّابةٍ تمرّر كلَّ شيءٍ كما كان. والسياسةُ تُضبط بـ`DQ_POLICY`
(«STALE=warn,CORPORATE_ACTION_PENDING=allow,…») · والأفعال: allow · warn (يمرّ بوسم) · quarantine (يُحجَز حتى تكتمل الوصفة · يُعلَن) ·
block (يُستبعَد · يُعلَن). **ولا صمت:** كلُّ محجوزٍ/مستبعَدٍ يُسجَّل بسببه.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os

VALID = "VALID"
STALE = "STALE"
INCOMPLETE = "INCOMPLETE"
SPLIT_UNADJUSTED = "SPLIT_UNADJUSTED"
CORPORATE_ACTION_PENDING = "CORPORATE_ACTION_PENDING"
CORPORATE_ACTION_ANNOUNCED = "CORPORATE_ACTION_ANNOUNCED"
RECENT_SPLIT = "RECENT_SPLIT"
SOURCE_CONFLICT = "SOURCE_CONFLICT"
SYMBOL_CHANGED = "SYMBOL_CHANGED"
MARKET_CLOSED = "MARKET_CLOSED"
UNVERIFIED = "UNVERIFIED"

STATES = (VALID, STALE, INCOMPLETE, SPLIT_UNADJUSTED, CORPORATE_ACTION_PENDING, CORPORATE_ACTION_ANNOUNCED, RECENT_SPLIT,
          SOURCE_CONFLICT, SYMBOL_CHANGED, MARKET_CLOSED, UNVERIFIED)
ACTIONS = ("allow", "warn", "quarantine", "block")
_SEVERITY = {"allow": 0, "warn": 1, "quarantine": 2, "block": 3}

DEFAULT_POLICY = {
    VALID: "allow",
    STALE: "block",
    INCOMPLETE: "block",
    SPLIT_UNADJUSTED: "block",
    CORPORATE_ACTION_PENDING: "quarantine",
    CORPORATE_ACTION_ANNOUNCED: "warn",
    RECENT_SPLIT: "warn",
    SOURCE_CONFLICT: "block",
    SYMBOL_CHANGED: "block",
    MARKET_CLOSED: "warn",
    UNVERIFIED: "warn",
}

LABELS_AR = {
    VALID: "صالح",
    STALE: "قديم",
    INCOMPLETE: "ناقص",
    SPLIT_UNADJUSTED: "تقسيمٌ غيرُ مسوًّى",
    CORPORATE_ACTION_PENDING: "تقسيمٌ عكسيّ حديث لم تكتمل بعده الوصفة",
    CORPORATE_ACTION_ANNOUNCED: "تقسيمٌ مُعلَن لم يُنفَّذ",
    RECENT_SPLIT: "تقسيمٌ حديث",
    SOURCE_CONFLICT: "تعارضُ المصدرين",
    SYMBOL_CHANGED: "خارج كون اليوم",
    MARKET_CLOSED: "لا جلسةَ مكتملة معروفة",
    UNVERIFIED: "التقسيماتُ غيرُ مُتحقَّقة",
}

# faisal_verbatim — «ضرب قاع الـ÷2 وحافظ عليه 3ج» (وصفةُ المقسّم · الحرفُ نفسُه في `_split_setup_probe`: `close.tail(3)`)
SPLIT_HELD_SESSIONS = 3
# engineering — نافذةُ تقويم ناسداك (أيّامٌ تقويميّة للخلف): **تغطيةُ تأخّر ياهو في إدراج التقسيمات** لا عتبةُ فرز. المقيسُ في المِجَسّ:
#   أقدمُ تقسيمٍ أدرجه ناسداك ولم يُدرجه ياهو بعدُ = 15 يومًا (FBYDP 09-16) ⇒ 45 تغطّيه ثلاثًا. وما قبلها يأتي من ياهو.
NASDAQ_DAYS = 45
NASDAQ_URL = "https://api.nasdaq.com/api/calendar/splits"
NASDAQ_HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*", "Origin": "https://www.nasdaq.com", "Referer": "https://www.nasdaq.com/"}


def _minor_tol() -> float:
    """⚖️ engineering — نسبةُ تقسيمٍ داخل [1/(1+t)، 1+t] (أرباحُ أسهمٍ 5% · انفصالٌ صغير) لا تُشوّه السلسلة فوق التسامح فلا تُعَدّ «تقسيمًا»
    هنا. القيمةُ `hunter_outcomes.SCALE_TOL` **بالاسم** (‏0.25 · مقيسةٌ في `tvs_probe`) — لا رقمَ يُكرَّر."""
    try:
        import hunter_outcomes as _HO
        return float(_HO.SCALE_TOL)
    except Exception:                                            # noqa: BLE001
        return 0.25


def enabled() -> bool:
    """المفتاحُ العامّ — يُقرأ وقتَ النداء · «0» ⟵ كلُّ بوّابةٍ تمرّر كلَّ شيءٍ (السلوكُ السابق بت-بت) · وغيابُه = مُفعَّل (الإنتاج)."""
    return os.environ.get("DQ_GATE", "1").strip() != "0"


def policy_map(env: str = None) -> dict:
    """السياسةُ النافذة = الافتراضيّة ثمّ تجاوزاتُ `DQ_POLICY` («STATE=action,…») — مدخلٌ تالف يُتجاهل (فاشلٌ-آمن)."""
    pol = dict(DEFAULT_POLICY)
    raw = os.environ.get("DQ_POLICY", "") if env is None else env
    for part in str(raw or "").replace(";", ",").split(","):
        if "=" not in part:
            continue
        k, v = (x.strip() for x in part.split("=", 1))
        k, v = k.upper(), v.lower()
        if k in pol and v in ACTIONS:
            pol[k] = v
    return pol


def _iso(x) -> str | None:
    try:
        if x is None:
            return None
        if isinstance(x, str):
            return x[:10]
        if hasattr(x, "date") and callable(getattr(x, "date")):
            return x.date().isoformat()
        if hasattr(x, "isoformat"):
            return x.isoformat()[:10]
        return str(x)[:10]
    except Exception:                                            # noqa: BLE001
        return None


def last_bar(df) -> str | None:
    """تاريخُ آخر شمعة (ISO) أو None. نقيّة · فاشلةٌ-آمنة."""
    try:
        if df is None or len(df) == 0:
            return None
        return _iso(df.index[-1])
    except Exception:                                            # noqa: BLE001
        return None


def bars_src(df) -> str:
    try:
        return (getattr(df, "attrs", None) or {}).get("bars_src") or "yahoo"
    except Exception:                                            # noqa: BLE001
        return "yahoo"


def freshness(df, expected: str | None) -> tuple:
    """(حالة، تفصيل) لطزاجة الإطار مقابل آخر جلسةٍ مكتملة `expected`.

    • بلا إطار/إغلاقٍ صالح ⟵ INCOMPLETE · • `expected` مجهول ⟵ MARKET_CLOSED (لا يُدّعى «طازج»)
    • آخرُ شمعةٍ أقدمُ من `expected` ⟵ STALE (TradingView بلا حشو: لا صفقةَ في الجلسة أو المزوّدُ لم يُعطها)
    • شمعةُ ياهو على `expected` بحجم صفر ⟵ STALE (ياهو **يحشو** يومًا بلا صفقة بإغلاق الأمس — ليست بياناتِ جلسة)
    • غيرُ ذلك ⟵ VALID (وآخرُ شمعةٍ **أحدثُ** من `expected` = شمعةُ جلسةٍ جارية: `live` صريح ولا تُرفض)."""
    lb = last_bar(df)
    if lb is None:
        return INCOMPLETE, {"last_bar": None, "why": "إطارٌ فارغ"}
    try:
        c = float(df["Close"].iloc[-1])
        if not (c > 0) or math.isnan(c):
            return INCOMPLETE, {"last_bar": lb, "why": "إغلاقٌ مفقود"}
    except Exception:                                            # noqa: BLE001
        return INCOMPLETE, {"last_bar": lb, "why": "إغلاقٌ مفقود"}
    if not expected:
        return MARKET_CLOSED, {"last_bar": lb, "why": "لا جلسةَ مكتملة معروفة"}
    if lb < expected:
        return STALE, {"last_bar": lb, "expected": expected, "why": f"آخرُ شمعة {lb} أقدمُ من جلسة {expected}"}
    if lb == expected and bars_src(df) != "tradingview":
        try:
            if float(df["Volume"].iloc[-1]) == 0.0:
                return STALE, {"last_bar": lb, "expected": expected, "why": "شمعةُ ياهو محشوّة (حجم صفر · بلا صفقة)"}
        except Exception:                                        # noqa: BLE001
            pass
    return VALID, {"last_bar": lb, "expected": expected, "live": lb > expected}


def split_events(splits, since_iso: str | None = None) -> list:
    """[(يوم ISO، نسبة)] مرتّبةً من Series ياهو أو أزواج — نسبةٌ موجبة فقط · وبعد `since_iso` (ضمنًا) إن مُرِّر. فاشلةٌ-آمنة ⟵ []."""
    out = []
    try:
        if splits is None:
            return out
        items = splits.items() if hasattr(splits, "items") else splits
        for d, v in items:
            try:
                ds, fv = _iso(d), float(v)
            except Exception:                                    # noqa: BLE001
                continue
            if ds and fv > 0 and (since_iso is None or ds >= since_iso):
                out.append((ds, fv))
    except Exception:                                            # noqa: BLE001
        return []
    return sorted(out)


def is_minor(ratio: float, tol: float = None) -> bool:
    t = _minor_tol() if tol is None else float(tol)
    try:
        return abs(math.log(float(ratio))) <= math.log(1.0 + t)
    except Exception:                                            # noqa: BLE001
        return False


def cross_check(primary: list | None, secondary: list | None, tol_days: int = 1) -> tuple:
    """تحقّقٌ متقاطع لأحداث التقسيم بين مصدرين مستقلّين ⟵ (الاتّحاد أو None، التعارضات، الملاحظات).

    • **التعارض** (يحكم: SOURCE_CONFLICT) = حدثٌ في المصدرين داخل `tol_days` يومًا **بنسبتين مختلفتين** (أكثر من 5%) — لا يُختار أحدُهما
      عشوائيًّا.
    • **الملاحظة** (تُسجَّل ولا تحكم) = حدثٌ في مصدرٍ بلا نظيرٍ في الآخر: يدخل **الاتّحادَ** (الأحوطُ أن يُفترَض التقسيمُ وقع · ياهو
      يتأخّر في الإدراج — مقيس: DLXY) فيُعامَل السهمُ كمقسَّم.
    • مصدرٌ تعذّر (None) ⟵ الاتّحادُ = الآخر بلا تعارض · وكلاهما تعذّر ⟵ الاتّحادُ None (UNVERIFIED — لا يُدّعى «لا تقسيم»)."""
    if primary is None and secondary is None:
        return None, [], []
    if primary is None or secondary is None:
        return sorted(list(primary if primary is not None else secondary)), [], []
    conflicts, notes, union = [], [], list(primary)

    def _near(a, b):
        try:
            return abs((dt.date.fromisoformat(a) - dt.date.fromisoformat(b)).days) <= tol_days
        except Exception:                                        # noqa: BLE001
            return False
    for d, r in primary:
        m = [x for x in secondary if _near(d, x[0])]
        if not m:
            notes.append(("only_primary", d, r))
        elif m[0][1] and r and abs(math.log(m[0][1] / r)) > math.log(1.05):
            conflicts.append(("ratio", d, r, m[0][1]))
    for d, r in secondary:
        if not any(_near(d, x[0]) for x in primary):
            notes.append(("only_secondary", d, r))
            union.append((d, r))
    return sorted(union), conflicts, notes


def unadjusted(df, events) -> bool:
    """هل لم يُسوِّ الإطارُ تقسيمًا مُدرَجًا؟ — `hunter_outcomes.unadjusted_jump` **بالاسم** (مقيسةٌ على WOK في `tvs_probe` ·
    واتّجاهُها محكوم §⑧-ب/ج). فاشلةٌ-آمنة ⟵ False."""
    try:
        import hunter_outcomes as _HO
        return bool(_HO.unadjusted_jump(df, events))
    except Exception:                                            # noqa: BLE001
        return False


def sessions_since(df, day_iso: str) -> int | None:
    """عددُ شموع الإطار في يوم الحدث أو بعده (جلساتٌ متداولة منذه). فاشلةٌ-آمنة ⟵ None."""
    try:
        return int(sum(1 for x in df.index if _iso(x) >= str(day_iso)[:10]))
    except Exception:                                            # noqa: BLE001
        return None


def _recipe_params() -> tuple:
    """(حدُّ النطاق الأدنى، التسامح الأعلى) **بالاسم من الصيّاد** — `CONFIG["SPLIT_RADAR_BAND_LOW"]` وافتراضُ `tol` في توقيع
    `_split_setup_probe` (لا رقمَ يُكرَّر هنا) · وتعذّرُ القراءة ⟵ القيمُ المقروءةُ يومَ الكتابة (0.70 · 0.25)."""
    try:
        import inspect
        import Super_stock as _S
        return (float(_S.CONFIG["SPLIT_RADAR_BAND_LOW"]),
                float(inspect.signature(_S._split_setup_probe).parameters["tol"].default))
    except Exception:                                            # noqa: BLE001
        return 0.70, 0.25


def split_settled(df, split_date: str, band_low: float = None, tol: float = None, held: int = None) -> dict:
    """هل **اكتملت** وصفةُ فيصل للمقسّم عكسيًّا بعد التقسيم؟ — «ضرب قاع الـ÷2 وحافظ عليه 3ج» حرفيًّا · نقيّة · فاشلةٌ-آمنة.

    في كلّ يومٍ t منذ يوم التقسيم: المرجعُ = أعلى High منذ التقسيم حتى t (= `_post_split_high` مقصوصًا على t) · النصفُ = المرجع÷2 ·
    والنطاقُ [النصف×حدّه الأدنى، النصف×(1+التسامح)] (نطاقُ الصيّاد نفسُه). **«ضرب»** = أوّلُ يومٍ يبلغ فيه Low أعلى النطاق · **«حافظ»** =
    إغلاقُ `held` جلساتٍ **بعده** داخل النطاق متتاليةً · وانكسارُ إغلاقٍ تحت النطاق يُعيد العدّ من الضربة التالية.
    ⚖️ **تاريخيّةٌ لا لحظيّة:** مرّةً تكتمل تبقى مكتملة (الصعودُ بعدها انطلاقٌ لا عودةٌ للتعليق).
    ⟵ {"settled", "half" (نصفُ آخر يوم), "post_high", "hit" (يومُ الضربة الجارية), "held" (جلساتُ الحفاظ بعدها), "day" (يومُ الاكتمال)}."""
    bl, tl = _recipe_params()
    bl = bl if band_low is None else float(band_low)
    tl = tl if tol is None else float(tol)
    h = SPLIT_HELD_SESSIONS if held is None else int(held)
    out = {"settled": False, "half": None, "post_high": None, "hit": None, "held": 0, "day": None}
    try:
        days = [_iso(x) for x in df.index]
        hi = [float(x) for x in df["High"].values]
        lo = [float(x) for x in df["Low"].values]
        cl = [float(x) for x in df["Close"].values]
        j0 = next((k for k, d in enumerate(days) if d >= str(split_date)[:10]), None)
        if j0 is None:
            return out
        run_hi, hit, cnt = 0.0, None, 0
        for t in range(j0, len(days)):
            run_hi = max(run_hi, hi[t])
            half = run_hi / 2.0
            top, bottom = half * (1.0 + tl), half * bl
            out["half"], out["post_high"] = round(half, 4), round(run_hi, 4)
            if out["settled"]:
                continue
            if hit is None:
                if lo[t] <= top:
                    hit, cnt = t, 0
                continue
            if bottom <= cl[t] <= top:
                cnt += 1
                if cnt >= h:
                    out["settled"], out["day"] = True, days[t]
            elif cl[t] < bottom:
                hit, cnt = (t if lo[t] <= top else None), 0     # انكسر تحت النطاق ⟵ ضربةٌ جديدة من هنا
            else:
                cnt = 0                                          # أغلق فوق النطاق ⟵ لم يحافظ (يعود العدّ)
        out["hit"] = days[hit] if hit is not None else None
        out["held"] = cnt
        return out
    except Exception:                                            # noqa: BLE001
        return out


def assess(sym: str, df, expected: str | None, *, events=None, splits=None, today: dt.date = None,
           universe=None, lookback_days: int = None, xcheck: dict = None, ref_date: str = None) -> dict:
    """تقييمُ رمزٍ واحد ⟵ {symbol, state, states, action, reasons, last_bar, expected, src, split, label}.

    • `events`: أحداثُ التقسيم المدموجة من المصدرين (أو `splits` خامًّا) — **None = المصدران تعذّرا** ⟵ UNVERIFIED.
    • `lookback_days`: نافذةُ «حديث» — افتراضًا `CONFIG["SPLIT_LOOKBACK_DAYS"]` **بالاسم** (نافذةُ الرادار والصيّاد القائمة).
    • `xcheck`: {"conflicts": [...]} — تعارضٌ في النسبة أو في إغلاق الجلسة ⟵ SOURCE_CONFLICT.
    • `universe`: كونُ اليوم — الرمزُ خارجه ⟵ SYMBOL_CHANGED.
    • `ref_date`: يومُ **مرجع القراءة** (قمّةُ نافذة الرادار مثلًا) — قبل تقسيمٍ عكسيٍّ حديثٍ داخل الإطار ⟵ CORPORATE_ACTION_PENDING
      («الهبوطُ يُقاس من قمّة ما بعد التقسيم» — `IMG_0143`/`IMG_0144`).
    والحالةُ الحاكمة = الأشدُّ سياسةً بين كلّ الحالات المنطبقة · والتفصيلُ كلُّه في `reasons` (لا صندوقَ أسود)."""
    today = today or dt.date.today()
    pol = policy_map()
    states, reasons = [], []
    st, info = freshness(df, expected)
    if st != VALID:
        states.append(st)
        reasons.append(info.get("why") or LABELS_AR[st])
    if universe is not None and str(sym).upper() not in universe:
        states.append(SYMBOL_CHANGED)
        reasons.append("الرمزُ خارج كون ناسداك اليوم")
    if lookback_days is None:
        try:
            import Super_stock as _S
            lookback_days = int(_S.CONFIG["SPLIT_LOOKBACK_DAYS"])
        except Exception:                                        # noqa: BLE001
            lookback_days = 120
    since = (today - dt.timedelta(days=int(lookback_days))).isoformat()
    ev = None
    if events is not None:
        ev = [(d, r) for d, r in events if d >= since]
    elif splits is not None:
        ev = split_events(splits, since)
    split = None
    lb = info.get("last_bar") or last_bar(df) or today.isoformat()
    if ev is None:
        states.append(UNVERIFIED)
        reasons.append("مصدرا التقسيمات تعذّرا — لا يُدّعى «لا تقسيم»")
    else:
        unk = [d for d, r in ev if not r and d <= (info.get("last_bar") or today.isoformat())]
        if unk:                                                  # حدثٌ مؤكَّدٌ بنسبةٍ مجهولة (ناسداك أحيانًا) — لا يُطوى
            states.append(RECENT_SPLIT)
            reasons.append(f"تقسيمٌ يوم {max(unk)} بنسبةٍ مجهولة")
            split = {"date": max(unk), "ratio": None, "kind": "unknown"}
        sig = [(d, r) for d, r in ev if r and not is_minor(r)]
        past = [(d, r) for d, r in sig if d <= lb]
        future = [(d, r) for d, r in sig if d > lb]
        if future:
            d, r = min(future)
            states.append(CORPORATE_ACTION_ANNOUNCED)
            reasons.append(f"تقسيمٌ {_ratio_txt(r)} مُعلَن ينفَّذ يوم {d} — المستوياتُ ستتغيّر بالتقسيم")
            split = {"date": d, "ratio": r, "kind": "announced"}
        if past and df is not None:
            d, r = max(past)
            split = {"date": d, "ratio": r, "kind": "reverse" if r < 1.0 else "forward",
                     "sessions_since": sessions_since(df, d)}
            if unadjusted(df, past):
                states.append(SPLIT_UNADJUSTED)
                reasons.append(f"قفزةٌ غيرُ مسوّاة عند تقسيم {d}")
                split["unadjusted"] = True
            if r < 1.0:
                s8 = split_settled(df, d)
                split.update({"half": s8["half"], "post_high": s8["post_high"], "settled": s8["settled"],
                              "settled_day": s8["day"], "hit": s8["hit"], "held": s8["held"]})
                if ref_date and str(ref_date)[:10] < d:
                    states.append(CORPORATE_ACTION_PENDING)
                    reasons.append(f"مرجعُ القراءة يوم {str(ref_date)[:10]} قبل التقسيم العكسيّ {d} — والهبوطُ يُقاس من قمّة ما بعد"
                                   " التقسيم (فيصل IMG_0143/0144) لا من قمّةٍ مسوّاةٍ لم تُتداوَل")
                if s8["settled"]:
                    states.append(RECENT_SPLIT)
                    reasons.append(f"تقسيمٌ عكسيّ {_ratio_txt(r)} يوم {d} — ضرب ÷2 وحافظ {SPLIT_HELD_SESSIONS} جلسات"
                                   f" (اكتملت الوصفة يوم {s8['day']})")
                else:
                    states.append(CORPORATE_ACTION_PENDING)
                    _hx = (f" — ÷2 = ${s8['half']:.2f} من قمّة ما بعده ${s8['post_high']:.2f}" if s8.get("half") else "")
                    _st = (f"ضرب ÷2 يوم {s8['hit']} وحافظ {s8['held']} من {SPLIT_HELD_SESSIONS}" if s8.get("hit")
                           else "لم يضرب ÷2 بعد")
                    reasons.append(f"تقسيمٌ عكسيّ {_ratio_txt(r)} يوم {d} (جلساتُ ما بعده {split['sessions_since']}) · {_st}{_hx}"
                                   " — وصفةُ فيصل للمقسّم لم تكتمل (مكانُه صيّادُ المقسّم)")
            else:
                states.append(RECENT_SPLIT)
                reasons.append(f"تقسيمٌ أماميّ {_ratio_txt(r)} يوم {d}")
    if xcheck and xcheck.get("conflicts"):
        states.append(SOURCE_CONFLICT)
        reasons.append("المصدران يختلفان: " + "، ".join(str(c) for c in xcheck["conflicts"][:3]))
    if not states:
        states = [VALID]
    states = list(dict.fromkeys(states))                         # حالةٌ واحدة لكلّ اسم (السببان يبقيان في `reasons`)
    action = max((pol.get(s, "allow") for s in states), key=lambda a: _SEVERITY[a])
    gov = max(states, key=lambda s: _SEVERITY[pol.get(s, "allow")])
    return {"symbol": str(sym).upper(), "state": gov, "states": states, "action": action, "reasons": reasons,
            "last_bar": info.get("last_bar"), "expected": expected, "src": bars_src(df) if df is not None else None,
            "split": split, "label": label_ar(gov, split)}


def _ratio_txt(r) -> str:
    try:
        r = float(r)
        return f"1:{round(1 / r):d}" if r < 1 else f"{r:g}:1"
    except Exception:                                            # noqa: BLE001
        return "؟"


def label_ar(state: str, split: dict | None = None) -> str:
    """وسمٌ عربيٌّ قصير **ثابتٌ عبر الأيّام** (بلا عدّادٍ يتقادم) للمخرَج المسموح بوسم — بلا علامات مقارنة."""
    if state == RECENT_SPLIT and split:
        r = split.get("ratio") or 0
        return (f"✂️ {'مقسَّم عكسيًّا' if r and r < 1 else 'مقسَّم'} {_ratio_txt(r)} يوم {split.get('date')}"
                " — أسعارُ ما قبله مسوّاةٌ لم تُتداوَل بقيمها")
    if state == CORPORATE_ACTION_ANNOUNCED and split:
        return f"✂️ تقسيمٌ {_ratio_txt(split.get('ratio'))} مُعلَن ينفَّذ يوم {split.get('date')} — المستوياتُ ستتغيّر بالتقسيم"
    if state == UNVERIFIED:
        return "⚠️ التقسيماتُ غيرُ مُتحقَّقة (المصدران تعذّرا)"
    if state == MARKET_CLOSED:
        return "⚠️ لا جلسةَ مكتملة معروفة في التقويم"
    return ""


def gate(items, assess_fn, sym_of=None) -> tuple:
    """يطبّق التقييم على مرشّحي مخرَجٍ ⟵ (المارّون، المحجوزون/المستبعَدون، ملخّص).

    `assess_fn(sym, item)` ⟵ نتيجةُ `assess` · `sym_of(item)` ⟵ الرمز (افتراضًا `item["symbol"]` أو item نفسُه نصًّا).
    المفتاحُ مطفأ ⟵ (الكلّ، []، ملخّصٌ فارغ) **بت-بت**. وتقييمٌ يرمي ⟵ UNVERIFIED بسياسته (لا انهيار ولا تمريرٌ صامت).
    والمارُّ الموسومُ (warn) يحمل وسمَه في `warnings` (يُعرَض في الكرت واليوميّ بالمسار القائم) و`dq` بحالته."""
    items = list(items or [])
    if not enabled():
        return items, [], {"enabled": False, "n": len(items)}
    sym_of = sym_of or (lambda it: it.get("symbol") if isinstance(it, dict) else str(it))
    pol = policy_map()
    kept, dropped = [], []
    summ = {"enabled": True, "n": len(items), "kept": 0, "by_state": {}, "by_action": {}}
    for it in items:
        s = sym_of(it)
        try:
            a = assess_fn(s, it)
        except Exception as e:                                   # noqa: BLE001
            a = {"symbol": s, "state": UNVERIFIED, "states": [UNVERIFIED], "action": pol[UNVERIFIED],
                 "reasons": [f"تعذّر التقييم: {type(e).__name__}"], "label": label_ar(UNVERIFIED)}
        summ["by_state"][a["state"]] = summ["by_state"].get(a["state"], 0) + 1
        summ["by_action"][a["action"]] = summ["by_action"].get(a["action"], 0) + 1
        if a["action"] in ("block", "quarantine"):
            dropped.append((it, a))
            continue
        if isinstance(it, dict):
            it["dq"] = {k: a.get(k) for k in ("state", "action", "label", "last_bar", "expected", "split")}
            if a["action"] == "warn" and a.get("label"):
                w = it.setdefault("warnings", [])
                if a["label"] not in w:
                    w.append(a["label"])
        kept.append(it)
    summ["kept"] = len(kept)
    return kept, dropped, summ


def summary_line(summ: dict, scope: str = "") -> str:
    """سطرُ سجلٍّ واحد — العددُ لكلّ حالةٍ وفعل (لا قصَّ صامتًا)."""
    if not summ or not summ.get("enabled"):
        return f"🛡️ سلامةُ البيانات{(' · ' + scope) if scope else ''}: المفتاحُ مطفأ (DQ_GATE=0) — بلا تحقّق"
    bs = " · ".join(f"{LABELS_AR.get(k, k)} {v}" for k, v in sorted(summ.get("by_state", {}).items()) if k != VALID)
    return (f"🛡️ سلامةُ البيانات{(' · ' + scope) if scope else ''}: فُحص {summ.get('n', 0)} · مرّ {summ.get('kept', 0)}"
            + (f" · {bs}" if bs else " · كلُّه صالح"))


def dropped_lines(dropped, cap: int = 40) -> list:
    """أسطرُ السجلّ للمحجوزين/المستبعَدين بأسبابهم — والقصُّ يُعلَن بعدده."""
    out = []
    for _it, a in list(dropped or [])[:cap]:
        out.append(f"   ⛔ {a.get('symbol')} [{a.get('state')} ⟵ {a.get('action')}]: " + " · ".join(a.get("reasons") or []))
    if len(dropped or []) > cap:
        out.append(f"   …و{len(dropped) - cap} غيرهم (لا قصَّ صامتًا)")
    return out


# ──────────────────────── تقويمُ ناسداك للتقسيمات (المصدرُ المستقلّ الثاني) ────────────────────────

def parse_ratio(txt) -> float | None:
    """«1 : 5» ⟵ 0.2 (صيغةُ ياهو: جديدٌ ÷ قديم) · «3 : 1» ⟵ 3.0 · وإلّا None. نقيّة."""
    try:
        t = str(txt).replace("-", ":").replace("for", ":").replace("/", ":")
        a, b = [float(x.strip()) for x in t.split(":")[:2]]
        if a > 0 and b > 0:
            return a / b
    except Exception:                                            # noqa: BLE001
        return None
    return None


def parse_exec_date(txt) -> str | None:
    """«9/28/2026» أو «09/28/2026» أو ISO ⟵ «2026-09-28» · وإلّا None. نقيّة."""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d"):
        try:
            return dt.datetime.strptime(str(txt).strip(), fmt).date().isoformat()
        except Exception:                                        # noqa: BLE001
            continue
    return None


def parse_nasdaq_rows(payload) -> list:
    """صفوفُ ردّ ناسداك ⟵ [(رمز، يوم، نسبة)] — الشكلُ المقيسُ حيًّا (`data.rows` ⟵ symbol · ratio · executionDate) ·
    صفٌّ تالفٌ يُتخطّى · ونسبةٌ لا تُقرأ ⟵ None (يبقى حدثًا: «وقع تقسيمٌ» معلومةٌ ولو جُهلت نسبتُه). نقيّة."""
    out = []
    try:
        if isinstance(payload, (str, bytes)):
            payload = json.loads(payload)
        data = (payload or {}).get("data") or {}
        rows = data.get("rows") or (data.get("calendar") or {}).get("rows") or []
        for row in rows:
            try:
                sym = str(row.get("symbol") or "").upper().strip()
                d = parse_exec_date(row.get("executionDate") or row.get("payableDate") or "")
                if sym and d:
                    out.append((sym, d, parse_ratio(row.get("ratio"))))
            except Exception:                                    # noqa: BLE001
                continue
    except Exception:                                            # noqa: BLE001
        return []
    return out


def nasdaq_calendar(days: int = None, today: dt.date = None, get=None, workers: int = 6) -> tuple:
    """تقويمُ ناسداك ⟵ ({رمز: [(يوم، نسبة)]}، إحصاء) أو (None، إحصاء) إن تعذّر **كلُّه**.

    يُطلب يومٌ تجاريٌّ واحد لكلّ طلب من `today` للخلف `days` يومًا تقويميًّا ‏+ الطلبُ بلا تاريخ (الأسبوعُ الجاري والمُعلَن القادم) —
    بالتوازي (`workers`) · ومهلةُ كلِّ طلبٍ 15ث. `get(url)` ⟵ (رمزُ الحالة، json) محقونٌ للاختبار. **الجزئيُّ يُقبل ويُعلَن** (تعذّرُ
    بعض الأيّام لا يُسقط الكلّ) · والكلُّ تعذّر ⟵ None (فيبقى ياهو وحدَه مصدرًا)."""
    import concurrent.futures as _cf
    days = NASDAQ_DAYS if days is None else int(days)
    today = today or dt.date.today()
    urls = [NASDAQ_URL] + [f"{NASDAQ_URL}?date={(today - dt.timedelta(days=k)).isoformat()}"
                           for k in range(days + 1) if (today - dt.timedelta(days=k)).weekday() < 5]

    def _get(u):
        if get is not None:
            return get(u)
        import requests as _rq
        r = _rq.get(u, headers=NASDAQ_HEADERS, timeout=15)
        return r.status_code, (r.json() if r.status_code == 200 else None)
    ok = fail = 0
    seen, out = set(), {}
    with _cf.ThreadPoolExecutor(max_workers=max(1, int(workers))) as ex:
        futs = {ex.submit(_get, u): u for u in urls}
        for f in _cf.as_completed(futs):
            try:
                code, payload = f.result()
            except Exception:                                    # noqa: BLE001
                code, payload = None, None
            if code != 200 or payload is None:
                fail += 1
                continue
            ok += 1
            for sym, d, r in parse_nasdaq_rows(payload):
                k = (sym, d, r)
                if k in seen:
                    continue
                seen.add(k)
                out.setdefault(sym, []).append((d, r))
    stats = {"asked": len(urls), "ok": ok, "fail": fail, "symbols": len(out), "events": len(seen)}
    if ok == 0:
        return None, stats
    for s in out:
        out[s].sort()
    return out, stats
