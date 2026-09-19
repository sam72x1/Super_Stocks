# -*- coding: utf-8 -*-
"""🧱🔬 `T-SUPDEF` — مِجَسُّ **تعريف الدعم** (العقد `support_def_prereg.md` ‏+ الملحق `§⑩`).

**قراءةٌ فقط:** لا كتابةَ حالةٍ · لا إرسالَ تلغرام · لا سرَّ · لا مسَّ إنتاج.
**ولا يُشحَن منه شيءٌ مهما كانت النتيجة** (‏المحورُ يمسّ جذرًا — `§⓪`).

الحاكمُ `A0` = `pivot_stability` **الإنتاجيّة** كما هي · والوصفيّون
(`A1`/`A2`/`A-FAR`/`A-MID`/`A-HIGHLOW`) **يُنشَرون ولا يُرشَّحون** · وشاهدُ الضبط
الحاكم **`A-RAND`** (‏`§⑩-ⓕ`) سقوطُه شرطُ صحّة.

المجتمعُ (`§⑪-ⓒ`) = ثلاثيّاتُ `§⑨-ⓒ` ‏+ الأربعُ المؤرَّخةُ **بمرساة السعر**
(`§⑩-ⓑ`) ‏+ الأربعُ المؤرَّخةُ **ببصمة المؤشّر** (`§⑪-ⓒ`) ⇒ **‏10 ثلاثيّاتٍ من
‏10 رموز**. وكلُّها **تُعاد اشتقاقًا** من الأداتَين بالاسم لا تُكتَب بيدٍ
(‏`V-S6` للسعر · `V-S11` للمؤشّر) — والوسمُ يوثّق الأصل ولا يفرز.

ومعه معيارٌ ثانٍ نظيف **`SD1-NEW`** (‏`§⑪-ⓔ`) على الأربعة الجديدة وحدَها،
**ويُقرأ الحكمُ بالأضعف** فلا يُنتقى الأمرَحُ بعد رؤية الرقمين.

رموزُ الخروج: 0 = الفرعُ 1 · 2 = الفرعُ 2 · 3 = الفرعُ 3 «لا قياس» · 5 = حارس ·
‏6 = هُويّةُ المجتمع (‏`V-S6`/`V-S11`) · 7 = شاهدُ الضبط لا يفارق (‏`V-S7`) ·
‏8 = المحورُ مُغلَق (يُرفَع بإقرار `SUPDEF_REOPEN=1`).
"""
import csv
import datetime as dt
import os
import random
import sys

import Super_stock as bot
import faisal_indicator_anchor as ia
import faisal_price_anchor as pa

TOL = 2.0                 # `FAISAL_LEVEL_TOL_PCT` — يُقرأ من CONFIG أدناه
FAR_LOOKBACK = 120        # `A-FAR` — وصفيٌّ بنصّ `§⑩-ⓖ` بعد تقاعده شاهدًا
SD0_MIN_ROWS, SD0_MIN_SYMS = 5, 3
SD1_SHARE, SD1_P = 80.0, 0.10
SD2_MEDIAN = 10.0

# ── `§⑩-ⓕ` شاهدُ الضبط الحاكم `A-RAND` ────────────────────────────────────────
ARAND_DRAWS = 999
ARAND_SEED_TAG = "T-SUPDEF-ARAND"
V_S7_MIN_GAP = 1.0        # نقطةٌ مئويّة — `engineering` مُعلَن (بوّابةُ فِكستشرٍ لا معيار)

# ── `§⑩-ⓔ` وسمُ مؤشّر السعر يُستبعَد ─────────────────────────────────────────
MARKER_TOL = 0.25         # % — `engineering` مُعلَنٌ في الملحق

LEVELS_TSV = "faisal_levels_table.tsv"

# ── `§⑩-ⓑ` هُويّةُ المجتمع الموسَّع: رمزٌ ⟶ تاريخُ الشارت (حارسُ `V-S6`) ────────
#    **لا يُوثَق بي**: الأداةُ تُعيد اشتقاقَها من `faisal_price_anchor` وتُقارن.
ANCHOR_EXPECT = {"TRUG": "2026-03-27", "TURB": "2026-04-02",
                 "GRI": "2026-04-13", "VEEE": "2026-05-14"}

# ── `§⑪-ⓒ` هُويّةُ الأربعة المؤرَّخة **ببصمة المؤشّر** (حارسُ `V-S11`) ──────────
#    **لا يُوثَق بي** كذلك: تُعاد اشتقاقًا من `faisal_indicator_anchor` وتُقارَن،
#    وأيُّ انزياحٍ يُوقف القياسَ ولا يُغيّره صامتًا.
IND_EXPECT = {"NEXR": "2026-04-01", "ALMU": "2026-04-10",
              "NXTT": "2026-01-22", "PRFX": "2026-05-29"}

# ── جدولُ `§⑨-ⓒ`: (رمز · تاريخ · فريم · مستويات · سطرُ الكاتالوج) ──────────────
#    **لا يُوثَق بي**: قفلُ `SDT1` يقرأ الكاتالوج ويشترط ظهورَ كلّ رقمٍ في سطره.
CASES = [
    ("PPBT", "2026-09-05", "daily",  [1.980, 1.682], 1211),
    ("DCOY", "2026-09-05", "ambig",  [2.851],        1218),
    ("ELPW", "2026-09-18", "daily",  [2.500],        1461),
    ("NUWE", "2026-09-18", "h4",     [0.7119],       1464),
    ("DAIC", "2026-09-18", "h4",     [1.986],        1466),
    ("SXTC", "2026-09-18", "daily",  [2.064],        1474),
]


def log(m: str) -> None:
    print(m, flush=True)


def selfcheck_readonly() -> list:
    import ast
    bad = []
    src = open(__file__, encoding="utf-8").read()
    for n in ast.walk(ast.parse(src)):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
            if nm in ("send_telegram", "git_save", "save_watchlist"):
                bad.append(f"نداءٌ محرَّم: {nm}")
            if nm == "open":
                mode = getattr(n.args[1], "value", None) if len(n.args) > 1 else None
                for k in n.keywords:
                    if k.arg == "mode":
                        mode = getattr(k.value, "value", "؟")
                if mode is not None and "r" not in str(mode):
                    bad.append(f"فتحٌ بوضعٍ غيرِ قراءة: {mode}")
    if src.count("TELEGRAM_BOT" + "_TOKEN") > 1:
        bad.append("ذكرُ سرّ")
    return bad


def cut_asof(df, asof: str):
    try:
        d = dt.date.fromisoformat(asof)
        keep = [(x.date() if hasattr(x, "date") else x) <= d for x in df.index]
        out = df[keep]
        return out if len(out) >= 40 else None
    except Exception:                                          # noqa: BLE001
        return None


def a0(df):
    """`A0` الحاكم — دالّةُ الإنتاج نفسُها بلا مسٍّ لـ`CONFIG`."""
    try:
        ps = bot.pivot_stability(df["Low"].values.astype(float),
                                 df["Close"].values.astype(float))
        return None if not ps else round(float(ps["pivot"]), 4)
    except Exception:                                          # noqa: BLE001
        return None


def a1(df, look=None):
    """`A1` وصفيّ — أدنى **إغلاقٍ** في النافذة نفسِها."""
    try:
        n = int(look or bot.CONFIG["PIVOT_LOOKBACK"])
        return round(float(df["Close"].astype(float).tail(n).min()), 4)
    except Exception:                                          # noqa: BLE001
        return None


def a2(df, look=None, tol=None):
    """`A2` وصفيّ — أرضيةُ التماسك: أدنى قاعٍ **لُمس أكثرَ من مرّة** ضمن التسامح."""
    try:
        n = int(look or bot.CONFIG["PIVOT_LOOKBACK"])
        t = float(tol if tol is not None else TOL)
        lows = sorted(float(x) for x in df["Low"].astype(float).tail(n).values)
        for i, v in enumerate(lows):
            if v <= 0:
                continue
            hits = sum(1 for w in lows if abs(w - v) / max(w, v) * 100.0 <= t)
            if hits >= 2:
                return round(v, 4)
        return round(lows[0], 4) if lows else None
    except Exception:                                          # noqa: BLE001
        return None


def a_far(df):
    """`A-FAR` — **تقاعد شاهدًا** بـ`§⑩-ⓕ` ويبقى مطبوعًا وصفيًّا (`§⑩-ⓖ`)."""
    try:
        return round(float(df["Low"].astype(float).tail(FAR_LOOKBACK).min()), 4)
    except Exception:                                          # noqa: BLE001
        return None


def _window(df, look=None):
    """نافذةُ `A0` نفسُها — `PIVOT_LOOKBACK` **تُقرأ** من `CONFIG` ولا تُضبَط."""
    n = int(look or bot.CONFIG["PIVOT_LOOKBACK"])
    lo = float(df["Low"].astype(float).tail(n).min())
    hi = float(df["High"].astype(float).tail(n).max())
    return lo, hi


def a_mid(df):
    """`A-MID` وصفيّ (`§⑩-ⓖ`) — منتصفُ مدى النافذة."""
    try:
        lo, hi = _window(df)
        return round((lo + hi) / 2.0, 4)
    except Exception:                                          # noqa: BLE001
        return None


def a_highlow(df, look=None):
    """`A-HIGHLOW` وصفيّ (`§⑩-ⓖ`) — **أعلى** قاعٍ في النافذة."""
    try:
        n = int(look or bot.CONFIG["PIVOT_LOOKBACK"])
        return round(float(df["Low"].astype(float).tail(n).max()), 4)
    except Exception:                                          # noqa: BLE001
        return None


def _med(vals):
    """وسيطٌ **علويّ** — نفسُ تعبير النتيجة الأولى (`absl[len//2]`) بلا تغيير."""
    v = sorted(vals)
    return v[len(v) // 2] if v else 0.0


def a_rand_err(df, ref, sym, asof, draws=None):
    """`A-RAND` الحاكم (`§⑩-ⓕ`) — **وسيطُ \\|الخطأ\\| على السحبات** لا خطأُ وسيطِها.

    المدى = نافذةُ `A0` نفسُها · البذرةُ حتميّةٌ `"{رمز}|{asof}|T-SUPDEF-ARAND"`.
    """
    try:
        lo, hi = _window(df)
        if not (hi > lo > 0) or not ref or float(ref) <= 0:
            return None
        rnd = random.Random(f"{sym}|{asof}|{ARAND_SEED_TAG}")
        n = int(draws or ARAND_DRAWS)
        errs = [abs(rnd.uniform(lo, hi) - float(ref)) / float(ref) * 100.0
                for _ in range(n)]
        return round(_med(errs), 2)
    except Exception:                                          # noqa: BLE001
        return None


def drop_marker(levels, ref_price, tol=None):
    """`§⑩-ⓔ` — الخطُّ المنطبقُ على السعر **مؤشّرُ سعرٍ لا دعم**.

    يُعيد `(المتبقّي، المستبعَد)` — ويُطبَع عددُ المستبعَدات دائمًا.
    """
    t = float(tol if tol is not None else MARKER_TOL)
    kept, dropped = [], []
    for v in levels:
        try:
            near = abs(float(v) - float(ref_price)) / float(ref_price) * 100.0 <= t
        except (TypeError, ValueError, ZeroDivisionError):
            near = False
        (dropped if near else kept).append(v)
    return kept, dropped


def pick_level(levels, close):
    """`§②` قاعدةُ القراءة: الأقربُ **تحتَ** إغلاقِ يوم الصورة · وإلّا None."""
    try:
        below = [float(v) for v in levels if float(v) < float(close)]
        return max(below) if below else None
    except (TypeError, ValueError):
        return None


def err_pct(got, ref):
    try:
        return round((float(got) - float(ref)) / float(ref) * 100.0, 2)
    except (TypeError, ValueError, ZeroDivisionError):
        return None


def sign_test_p(n_below: int, n: int) -> float:
    """اختبارُ إشارةٍ ثنائيُّ الذيل عند p=0.5 — **يُحسَب** بلا مكتبةٍ خارجيّة."""
    from math import comb
    if n <= 0:
        return 1.0
    k = max(n_below, n - n_below)
    tail = sum(comb(n, i) for i in range(k, n + 1)) / (2 ** n)
    return round(min(1.0, 2 * tail), 4)


def sd1_new_of(gov):
    """`§⑪-ⓔ` — اختبارُ الإشارة نفسُه **على الأربعة الجديدة وحدَها** (`indicator`).

    يُعيد `(below, n, share, p, عبرت؟, p_best)` حيث `p_best` = `p` عند **الإجماع**
    لهذا الحجم. **نظيفٌ تمامًا**: لم يُقَس قطّ ولم أرَ له رقمًا قبل التسجيل.

    🔴🔴 **وعيبٌ في عقدي أنا يُعلَن هنا لا يُصلَح صامتًا (‏`§⑫`):** نصُّ `§⑪-ⓔ`
    كتب لـ`n = 4` الأرقامَ ‏0.0625 و0.3125 وهي **أحاديّةُ الذيل**، بينما
    `sign_test_p` المدموجة — وهي «اختبارُ الإشارة **نفسُه**» الذي يستعمله `SD1`
    ومعناه الحرفيُّ ما تعنيه الجملة — **ثنائيّةُ الذيل** فتُعطي ‏0.125 و0.625.
    ⇒ عند `n = 4` **لا تعبر `SD1-NEW` بأيّ نتيجة** (‏أفضلُ مُتاحٍ ‏0.125 فوق
    الحدّ ‏0.10). **والحدُّ لا يُخفَّض ولا يُبدَّل الاختبارُ بعد رؤية ذلك**
    (‏`§⑪-ⓖ①`)، فتُقاس بحرفها ويُطبَع `p_best` **مقيسًا لا مُدَّعًى**.
    """
    nw = [r for r in gov if r.get("origin") == "indicator"]
    n = len(nw)
    if not n:
        return 0, 0, 0.0, 1.0, False, 1.0
    below = sum(1 for r in nw if r["a0"] is not None and r["a0"] < r["ref"])
    share = below / n * 100.0
    p = sign_test_p(below, n)
    return (below, n, share, p, (share >= SD1_SHARE and p <= SD1_P),
            sign_test_p(n, n))


def read_verdict(n_rows, n_syms, share, p, med_abs, far_worse, sd1_new=None):
    """فروعُ `§④` بحرفها — ولا فرعَ رابع.

    و`sd1_new` (‏`§⑪-ⓔ`): **يُقرأ الحكمُ بالأضعف** — فلا يُرقّى الفرعُ بعبور
    أحدِهما وسقوطِ الآخر، ولا يُنتقى الأمرَحُ بعد رؤية الرقمين. و`None` =
    المعيارُ غيرُ مُقاسٍ (قبل `§⑪`) ⇒ السلوكُ السابق بت-بت."""
    if n_rows < SD0_MIN_ROWS or n_syms < SD0_MIN_SYMS or not far_worse:
        return 3, ("الفرعُ 3 — **«لا قياس»**: الأرضيّةُ أو صحّةُ المقياس لم تُبلَغ "
                   "· يُعلَن بعدَده ولا يُفسَّر · ولا يُرفَع العدُّ بتأريخٍ مُستنتَج")
    sd1 = share >= SD1_SHARE and p <= SD1_P
    if sd1_new is not None:
        sd1 = sd1 and bool(sd1_new)          # 🔒 الأضعفُ يحكم (`§⑪-ⓔ`)
    sd2 = med_abs >= SD2_MEDIAN
    if sd1 and sd2:
        return 0, ("الفرعُ 1 — الانحيازُ **مقيسٌ ومادّيّ** ⇒ يُنشَر رقمًا ويُقترَح "
                   "تسجيلٌ لاحق · **ولا يُمَسّ `pivot_stability`**")
    if sd1 and not sd2:
        return 2, ("الفرعُ 2 — الانحيازُ **موجودٌ وغيرُ مادّيّ** ⇒ **يُغلَق المحورُ** "
                   "بشرطِ فتحٍ مؤرَّخ")
    return 3, ("الفرعُ 3 — **«لا قياس»**: "
               + ("`SD1`/`SD1-NEW` (بالأضعف) لم تُستوفَ" if sd1_new is not None
                  else "`SD1` لم تُستوفَ")
               + " · يُعلَن ولا يُفسَّر")


def branch3_reason(n_rows, n_syms, med_a0, med_ctrl, sd1=None, sd1_new=None):
    """`V-S8` — سببُ الفرع 3 **مفصولًا** فلا تُطوى الحالةُ الثالثة بلا بيان.

    و`sd1`/`sd1_new` يُسمّيان **أيَّهما** سقط (‏`§⑪-ⓔ`) فلا يُقرأ «‏`SD1` لم
    تُستوفَ» على حالةٍ سقطت فيها النظيفةُ وحدَها أو العكس."""
    if n_rows < SD0_MIN_ROWS or n_syms < SD0_MIN_SYMS:
        return (f"**الأرضيّة**: {n_rows} ثلاثيّة من {n_syms} رمزًا "
                f"(المطلوب {SD0_MIN_ROWS}/{SD0_MIN_SYMS})")
    if med_ctrl is None:
        return "**الشاهدُ لا يُقاس**: تعذّر حسابُ `A-RAND` على الصفوف الحاكمة"
    if abs(float(med_ctrl) - float(med_a0)) < 1e-9:
        return (f"**الشاهدُ لا يفرّق**: وسيطُ خطأ `A-RAND` = وسيطُ \\|خطأ `A0`\\| "
                f"= {med_a0:.2f}%")
    if float(med_ctrl) < float(med_a0):
        return (f"**الشاهدُ تفوّق على `A0`**: `A-RAND` {med_ctrl:.2f}% دون "
                f"`A0` {med_a0:.2f}% ⇒ **حكمٌ لا عطب** (`§⑩-ⓕ`)")
    if sd1 is None and sd1_new is None:
        return "**`SD1` لم تُستوفَ** (الشاهدُ عبر)"
    if sd1 and not sd1_new:
        return ("**`SD1` عبرت و`SD1-NEW` سقطت** ⇒ يُقرأ **بالأضعف** بنصّ "
                "`§⑪-ⓔ` المسجَّل قبل الرقمين (الشاهدُ عبر)")
    if sd1_new and not sd1:
        return ("**`SD1-NEW` عبرت و`SD1` سقطت** ⇒ يُقرأ **بالأضعف** بنصّ "
                "`§⑪-ⓔ` المسجَّل قبل الرقمين (الشاهدُ عبر)")
    return "**`SD1` و`SD1-NEW` كلتاهما لم تُستوفَ** (الشاهدُ عبر)"


# ═══════════ `§⑩-ⓑ` المجتمعُ الموسَّع — يُشتقُّ ولا يُكتَب ═════════════════════
def _levels_of(sym: str, line: int) -> list:
    """كلُّ مستوياتِ السطر **الحمراءِ اليوميّة** (`§⑨-ⓑ`) — من جدول المستويات."""
    out = []
    for r in csv.DictReader(open(LEVELS_TSV, encoding="utf-8"), delimiter="\t"):
        if (r["symbol"] == sym and r["line"] == str(line) and r["role"] == "support"
                and r["frame"] == "daily" and r["auto_chart"] == "0"):
            try:
                out.append(round(float(r["level"]), 4))
            except (TypeError, ValueError):
                continue
    return sorted(set(out), reverse=True)


def anchor_scan(hist):
    """يُعيد `(الحالاتُ الداخلة، الوصفيُّ الضيّق، التشخيص)` بنداء
    `faisal_price_anchor` **بالاسم** وبثوابتِه نفسِها — `§⑩-ⓐ`/`§⑩-ⓑ`."""
    cases, tight_only, diag = [], [], []
    # 🔑 «دمج مرساة السعر» (2026-09-19): الأربعةُ صارت مؤرَّخةً في الجدول فتسقط
    #    من `pending` ⇒ المصدرُ `recheck` = **ما أرّخَته هذي الأداةُ بنفسها**.
    #    تشديدٌ لا إرخاء، و`V-S6` يبقى الحاكمَ على الهُويّة.
    for t in pa.targets("recheck"):
        a = t.get("anchor")
        if not a or a.get("pct") is None:          # `ⓐ`: الرخوةُ خارجَ المجتمع
            continue
        sym, ln = t["symbol"], t["line"]
        df = (hist or {}).get(sym)
        if df is None or len(df) <= 5:
            diag.append((sym, ln, "no_data")); continue
        try:
            splits = bot._fetch_splits(sym)
        except Exception:                                      # noqa: BLE001
            splits = None
        bars = pa._bars_of(df)
        cands = pa.match_days(bars, a, splits)
        tc = pa.match_days(bars, a, splits, tol=pa.TOL_TIGHT)
        if len(cands) == 1:
            c = cands[0]
            cases.append({"sym": sym, "line": ln, "kind": a["kind"], "px": a["px"],
                          "pct": a["pct"], "date": c["date"],
                          "match_date": c["match_date"],
                          "levels": _levels_of(sym, ln),
                          # 🔎 **تشخيصٌ يُطبَع ولا يُستعمَل**: مقياسُ التقسيم بعد
                          #    تاريخ الشارت. غيرُ الواحد ⇒ مستوياتُ فيصل والسعرُ
                          #    المسجَّل بمقياس الشاشة و`A0` بمقياس المزوّد المعدَّل
                          #    ⇒ **الصفُّ غيرُ قابلٍ للمقارنة** — حدُّ صدقٍ لا إصلاحٌ
                          #    صامت (`§⑩-ⓚ`: لا تُبدَّل قاعدةٌ بعد رؤية النتيجة).
                          "sf": bot._split_scale_factor(splits, c["match_date"])})
            diag.append((sym, ln, "unique ⟶ " + c["date"]))
        else:
            diag.append((sym, ln, "ambiguous" if cands else "none"))
            if len(tc) == 1:                       # `ⓖ`: وصفيٌّ — خارجَ كلّ معيار
                tight_only.append((sym, ln, tc[0]["date"]))
    return cases, tight_only, diag


def indicator_scan(hist):
    """`§⑪-ⓒ` — الأربعةُ المؤرَّخةُ **ببصمة المؤشّر**، بنداء
    `faisal_indicator_anchor` **بالاسم** وبثوابتِه نفسِها (‏`candidates_at` هي
    دالّةُ الحسم نفسُها التي يستعملها مسارُه الحيّ ⇒ صفرُ منطقٍ مكرَّر).

    يُعيد `(الحالاتُ الداخلة، التشخيص)`. والنطاقُ `recheck` = **عكسُ الفلتر** =
    «ما أرّخَته هذي الأداةُ بنفسها» — وبدونه يستحيل إعادةُ الاشتقاق بعد الدمج.
    """
    cases, diag = [], []
    for t in ia.collect("recheck"):
        sym, ln = t["symbol"], t["line"]
        if not t["fps"]:
            diag.append((sym, ln, "no_fp")); continue
        df = (hist or {}).get(sym)
        if df is None or len(df) <= ia.MIN_BARS:
            diag.append((sym, ln, "no_data")); continue
        try:
            splits = bot._fetch_splits(sym)
        except Exception:                                      # noqa: BLE001
            splits = None
        pers = {int(f["params"][0]) for f in t["fps"] if f["kind"] == "rsi"}
        ser = ia.build_series(df, sorted(pers) or (ia.RSI_PERIOD,))
        cands, _best = ia.candidates_at(t["fps"], ser, splits)
        if len(cands) != 1:
            diag.append((sym, ln, "ambiguous" if cands else "none")); continue
        d = cands[0]
        lv = _levels_of(sym, ln)
        # 🔑 تاريخُ بصمة المؤشّر **هو** آخرُ جلسةٍ مكتملةٍ على الشاشة — وهي القاعدةُ
        #    المدموجةُ في `witness_of` (‏`§⑩-ⓒ`) لا اجتهادٌ هنا ⇒ القصُّ عليه مباشرةً.
        cases.append({"sym": sym, "line": ln, "date": d, "match_date": d,
                      "levels": lv, "sf": bot._split_scale_factor(splits, d)})
        diag.append((sym, ln, "unique ⟶ " + d + ("" if lv else "  (بلا مستوًى حاكم)")))
    return cases, diag


# ═══════════ ⚖️ `T-SPLITNORM` — تسويةُ التقسيم (العقد `splitnorm_prereg.md`) ══
# 🔒 **خلف علمٍ مطفأٍ افتراضًا** ⇒ المسارُ المنشورُ بت-بت (`V-N7`)، والحارسُ
#    `SUPDEF_REOPEN` يبقى فوقه — التسويةُ **لا ترفعه**.
NORM_ENV = "SUPDEF_NORM"
NORM_RC = {1: 10, 2: 11, 3: 12}   # مميَّزةٌ عن 0/2/3 حكمًا و5/6/7 حرّاسًا و8 إغلاقًا
NORM_GUARD_RC = 13                # `V-N1`/`V-N4` سقط ⇒ يُوقَف قبل أيّ حكم

# ‏`V-N1` — المنشورُ في `support_def_result.md` للتشغيلة `35455722208`
RAW_PUBLISHED = {"below": 6, "n": 9, "p": 0.5078, "med": 31.03, "rand": 50.83}
# ‏`V-N4` — اشتقاقُ `§③` بيدي: مستوى فيصل ÷ العامل (يُقارَن بالمحسوب)
DERIV_EXPECT = {"NEXR": 18.832, "NXTT": 583.0}
DERIV_TOL_PCT = 1.0

_SF_CACHE = {}


def norm_on() -> bool:
    """هل التسويةُ مُشعَلة؟ **مطفأةٌ افتراضًا** (`§⑧`-`V-N7`)."""
    return str(os.environ.get(NORM_ENV, "")).strip() == "1"


def norm_level(level, sf):
    """⚖️ `§②` — تسويةُ مستوى فيصل إلى مقياس بيانات المزوّد: **قسمةٌ لا ضرب**.

    الاتّجاهُ ليس اختياري: دوكسترنغُ `_split_scale_factor` ينصّ أن **القسمةَ عليه
    تحوّل المستوى المخزّن لمقياس البيانات الحالية**. و`sf = 1` هُويّةٌ بالبناء.
    فاشلةٌ-آمنة ⟶ المستوى كما هو (أسوأُ حالةٍ = سلوكُ اليوم)."""
    try:
        v, f = float(level), float(sf)
        return v if f <= 0 else v / f
    except (TypeError, ValueError, ZeroDivisionError):
        return level


def split_factor_of(sym, asof):
    """عاملُ التقسيم عند `asof` الصفِّ نفسِه — بدالّتَي الإنتاج **بالاسم**
    (`_fetch_splits` ‏+ `_split_scale_factor`) · مكاشٌ فلا يتكرّر النداء."""
    key = (str(sym), str(asof))
    if key in _SF_CACHE:
        return _SF_CACHE[key]
    try:
        sf = float(bot._split_scale_factor(bot._fetch_splits(sym), asof))
    except Exception:                                          # noqa: BLE001
        sf = 1.0
    _SF_CACHE[key] = sf
    return sf


# ═══════════ بناءُ الصفوف — والحساسيّاتُ الثلاثُ تُعيد استعمالَه ═══════════════
def build_rows(hist_old, hist_new, acases, asof_mode="match", ref_mode="chart",
               marker=True, icases=(), hist_ind=None, norm=None):
    """`asof_mode` ∈ {match, date} (`ⓒ`) · `ref_mode` ∈ {chart, close} (`ⓓ`) ·
    `marker` (`ⓔ`). الافتراضاتُ **هي القاعدةُ المسجَّلة** والباقي حساسيّاتٌ وصفيّة.

    و`origin` ∈ {cat, price, **indicator**} — وسمُ الأصل الذي يعزل `SD1-NEW`
    (‏`§⑪-ⓔ`)، **ولا يفرز المجتمعَ**: كلُّ مؤرَّخٍ يدخل مهما كان مصدرُه."""
    plan = []
    for sym, asof, frame, levels, src in CASES:
        plan.append({"sym": sym, "asof": asof, "frame": frame, "levels": list(levels),
                     "src": src, "kind": "close", "px": None, "hist": hist_old,
                     "origin": "cat"})
    for c in acases:
        asof = c["match_date"] if asof_mode == "match" else c["date"]
        plan.append({"sym": c["sym"], "asof": asof, "frame": "daily",
                     "levels": list(c["levels"]), "src": c["line"],
                     "kind": c["kind"], "px": c["px"], "hist": hist_new,
                     "origin": "price"})
    for c in icases:
        # ‏`match_date == date` لبصمة المؤشّر ⇒ الحساسيّةُ `ⓒ` لا تحرّكها (مُعلَن).
        plan.append({"sym": c["sym"], "asof": c["match_date"] if asof_mode == "match"
                     else c["date"], "frame": "daily",
                     "levels": list(c["levels"]), "src": c["line"],
                     "kind": "close", "px": None, "hist": hist_ind,
                     "origin": "indicator"})
    rows, skipped, n_drop = [], [], 0
    for q in plan:
        df0 = (q["hist"] or {}).get(q["sym"])
        if df0 is None or len(df0) < 60:
            skipped.append((q["sym"], q["asof"], "تعذّر الجلب")); continue
        df = cut_asof(df0, q["asof"])
        if df is None:
            skipped.append((q["sym"], q["asof"], "القصُّ لا يترك بياناتٍ كافية"))
            continue
        close = float(df["Close"].iloc[-1])
        refpx = q["px"] if (ref_mode == "chart" and q["kind"] == "spot"
                            and q["px"]) else close
        lv = list(q["levels"])
        # ⚖️ `T-SPLITNORM §②`-3: التسويةُ **قبل** `drop_marker`/`pick_level`
        sf_row = 1.0
        if (norm_on() if norm is None else bool(norm)):
            sf_row = split_factor_of(q["sym"], q["asof"])
            lv = [norm_level(x, sf_row) for x in lv]
        if marker:
            lv, dropped = drop_marker(lv, refpx)
            n_drop += len(dropped)
        ref = pick_level(lv, refpx)
        if ref is None:
            skipped.append((q["sym"], q["asof"],
                            f"كلُّ المستويات فوق سعرِ المرجع {refpx:.3f}"))
            continue
        r = {"sym": q["sym"], "asof": q["asof"], "frame": q["frame"], "ref": ref,
             "close": close, "refpx": refpx, "kind": q["kind"],
             "a0": a0(df), "a1": a1(df), "a2": a2(df), "far": a_far(df),
             "mid": a_mid(df), "hl": a_highlow(df), "src": q["src"], "bars": len(df),
             "origin": q["origin"], "sf": sf_row}
        r["e0"] = err_pct(r["a0"], ref)
        r["e1"] = err_pct(r["a1"], ref)
        r["e2"] = err_pct(r["a2"], ref)
        r["ef"] = err_pct(r["far"], ref)
        r["er"] = a_rand_err(df, ref, q["sym"], q["asof"])
        rows.append(r)
    return rows, skipped, n_drop


def stats_of(rows):
    """إحصاءُ الصفوف **الحاكمة** (اليوميّة وحدَها — `§⑨-ⓐ`)."""
    gov = [r for r in rows if r["frame"] == "daily"]
    n, nsym = len(gov), len({r["sym"] for r in gov})
    if not gov:
        return gov, n, nsym, 0.0, 1.0, 0.0, None, False
    below = sum(1 for r in gov if r["a0"] is not None and r["a0"] < r["ref"])
    share = below / n * 100.0
    p = sign_test_p(below, n)
    med = _med([abs(r["e0"]) for r in gov if r["e0"] is not None])
    rv = [r["er"] for r in gov if r["er"] is not None]
    med_r = _med(rv) if rv else None
    ok = med_r is not None and med_r > med
    return gov, n, nsym, share, p, med, med_r, ok


# ═══════════ `V-S7` — شاهدُ الضبط يفارق **قبل أيّ جلب** ═══════════════════════
def _fixture_bottom_late():
    """فِكستشرُ `§⑩-ⓕ`: القاعُ في **آخر خمس شمعات** — الحالةُ التي أخمدت `A-FAR`."""
    import pandas as pd
    n = 60
    lows = [10.0 - 0.1 * i for i in range(n)]
    for j in range(n - 5, n):                       # القاعُ الحقيقيُّ في الذيل
        lows[j] = 3.0 - 0.05 * (j - (n - 5))
    idx = [dt.date(2026, 1, 1) + dt.timedelta(days=i) for i in range(n)]
    return pd.DataFrame({"Low": lows,
                         "High": [v * 1.15 for v in lows],
                         "Close": [v * 1.05 for v in lows]}, index=idx)


def gate_control_differs():
    """يُعيد `(مرّ؟، سطرُ البيان)` — وإلّا **خروج 7 قبل أيّ جلب**."""
    df = _fixture_bottom_late()
    v0, vf = a0(df), a_far(df)
    if v0 is None or vf is None:
        return False, "🔴 تعذّر حسابُ `A0`/`A-FAR` على الفِكستشر"
    dormant = abs(vf - v0) < 1e-9
    e0 = abs(err_pct(v0, v0) or 0.0)
    er = a_rand_err(df, v0, "FIX", "2026-03-01")
    if er is None:
        return False, "🔴 تعذّر حسابُ `A-RAND` على الفِكستشر"
    gap = abs(er - e0)
    ok = dormant and gap > V_S7_MIN_GAP
    return ok, (f"`A-FAR`={vf} و`A0`={v0} ⇒ خامدٌ؟ "
                f"**{'نعم' if dormant else 'لا'}** · خطأ `A-RAND` {er:.2f}% مقابل "
                f"`A0` {e0:.2f}% ⇒ فارقٌ {gap:.2f} نقطة (الحدّ {V_S7_MIN_GAP})")


# ═══════════ 🔒 إغلاقُ المحور — «اقفل الدعم» (‏2026-09-19، أمرُ المالك) ═════════
#   الحكمُ صدر مرّتين بالفرع 3، والثانيةُ بعد أن بلغ المجتمعُ أرضيّتَه: ثلاثةُ
#   معاييرَ من أربعةٍ تعبر و`SD1` تسقط على **قوّةِ اختبارِ الإشارة عند `n = 6`**
#   (‏5/6 ⟶ `p = 0.2188`) — وهو ما حسبه `§⑩-ⓘ-1` **قبل** التشغيل. ⇒ الباقي
#   دقّةٌ لا اتّجاه، ورفعُ العيّنة يلزمه **مصدرُ تأريخٍ لا وجودَ له اليوم**.
CLOSED_RC = 8          # مميَّزٌ عمدًا عن رموز القياس: 0/2/3 حكم · 5/6/7 حرّاس
CLOSED_ENV = "SUPDEF_REOPEN"
CLOSED_TXT = (
    "🔒 محورُ **تعريف الدعم** مُغلَقٌ بأمر المالك «اقفل الدعم» (‏2026-09-19).\n"
    "   الحكمُ الثاني: الفرعُ 3 — `SD0`/`SD2`/`SD3` تعبر و`SD1` تسقط على "
    "`p = 0.2188` عند `n = 6`.\n"
    "   ⛔ ولا يُخفَّض حدُّ `p` بعد رؤيته (`§⑩-ⓚ`).\n"
    "   🔓 والفتحُ يلزمه **ثلاثةٌ معًا**:\n"
    "   ‏1) **مصدرُ تأريخٍ جديد** — وتخفيفُ `§⑩-ⓐ` أو التسامحُ الضيّق ليس مصدرًا.\n"
    "   ‏2) **معيارٌ مسجَّلٌ في ملحقٍ مؤرَّخٍ جديد** يناسب العيّنةَ الصغيرة، "
    "**ولا يكون تخفيضًا لحدٍّ رأيتُ قيمتَه**.\n"
    "   ‏3) **إذنُ المالك.**\n"
    "   ⚙️ والإقرارُ `SUPDEF_REOPEN=1` — إقرارٌ بالثلاثة لا التفافٌ عليها.\n"
    "   📎 وحالةُ الشروط مسجَّلةٌ في **ملحق `§⑪`** (‏2026-09-19): الثلاثةُ\n"
    "   مستوفاةٌ بالتسجيل — **والناقصُ أمرُ تشغيلٍ صريحٌ من المالك وحدَه**."
)


def closed_guard():
    """يُوقف **قبل** أيّ قراءةِ مدخلٍ أو فتحِ لقطةٍ أو جلبةٍ أو حساب.

    يُعيد رمزَ الإغلاق، أو `None` حين يرفعه الإقرارُ صراحةً.
    """
    if str(os.environ.get(CLOSED_ENV, "")).strip() == "1":
        return None
    log(CLOSED_TXT)
    return CLOSED_RC


def norm_verdict(guards_ok, neutral_ok, outliers_ok, n_rows, n_syms):
    """فروعُ `splitnorm_prereg.md §⑤` بحرفها — **ولا فرعَ رابع**.

    🔴 **وثغرةٌ في عقدي تُعلَن ولا تُسَدّ بفرعٍ مخترَع:** الحالةُ «`SN1` ✅
    والشواذُّ باقية» لا يصفها `§⑤` بنصّه (الفرعُ 2 عنوانُه «ليست حياديّة»)
    ⇒ تُحمَل على **الفرعِ 2 محافظةً** (لا اعتماد) **ويُطبَع سببُها الحقيقيّ**
    لأن البديلَ اختراعُ فرعٍ رابعٍ بعد رؤية الحالة."""
    if not guards_ok or n_rows < SD0_MIN_ROWS or n_syms < SD0_MIN_SYMS:
        return NORM_RC[3], ("الفرعُ 3 — **لا قياس** (حارسٌ سقط أو الأرضيّةُ لم "
                            "تُبلَغ) · يُعلَن بعدَده ولا يُفسَّر")
    if not neutral_ok:
        return NORM_RC[2], ("الفرعُ 2 — **التسويةُ ليست حياديّة** (`SN1` 🔴) ⇒ "
                            "تُرفَض ولا يُعتمَد شيء")
    if not outliers_ok:
        return NORM_RC[2], ("الفرعُ 2 — **لا تُعتمَد**: `SN1` ✅ لكنّ شاذًّا بقي "
                            "خارجَ مدى صفوف العامل 1 ⇒ ثغرةُ `§⑤` تُحمَل محافظةً")
    return NORM_RC[1], ("الفرعُ 1 — **التسويةُ تُعتمَد مقياسًا لهذا المحور وحدَه** "
                        "· **ولا يُشحَن في الإنتاج شيء**")


def main() -> int:
    global TOL
    _closed = closed_guard()                 # 🔒 قبل أيّ عمليّة — لا بعدها
    if _closed is not None:
        return _closed
    TOL = float(bot.CONFIG.get("FAISAL_LEVEL_TOL_PCT", 2.0))
    log("🧱🔬 T-SUPDEF — مِجَسُّ تعريف الدعم ‏+ الملحق §⑩ "
        "(قراءةٌ فقط · لا شحنَ مهما كانت النتيجة)")
    bad = selfcheck_readonly()
    log(f"   V-S1 قراءةٌ فقط: {'✅' if not bad else '🔴 ' + str(bad)}")
    if bad:
        return 5
    if int(bot.CONFIG["PIVOT_LOOKBACK"]) != 25:
        log("   V-S2 🔴 PIVOT_LOOKBACK تحرّك — يُوقَف")
        return 5
    log(f"   V-S2 ✅ PIVOT_LOOKBACK=25 · التسامح {TOL}% · A-FAR={FAR_LOOKBACK} "
        f"(وصفيّ) · A-RAND={ARAND_DRAWS} سحبة")

    ok7, txt7 = gate_control_differs()                # `V-S7` **قبل أيّ جلب**
    log(f"   V-S7 شاهدُ الضبط يفارق: {'✅' if ok7 else '🔴'} — {txt7}")
    if not ok7:
        log("JUDGE rc=7 · شاهدُ الضبط لا يفارق على فِكستشر `§⑩-ⓕ` ⇒ يُوقَف قبل الجلب")
        return 7

    hist_old = bot.download_history(sorted({c[0] for c in CASES}))
    asyms = sorted({t["symbol"] for t in pa.targets("recheck")
                    if t.get("anchor") and t["anchor"].get("pct") is not None})
    hist_new = bot.download_history(asyms, start_override=pa.W0) if asyms else {}
    acases, tight_only, diag = anchor_scan(hist_new)

    got = {c["sym"]: c["date"] for c in acases}
    log("")
    log("═══ V-S6 هُويّةُ المجتمع الموسَّع (§⑩-ⓑ) ═══")
    for sym, ln, st in diag:
        log(f"   {sym:6s} سطر {ln:<5} {st}")
    if got != ANCHOR_EXPECT:
        log(f"   🔴 المُشتقّ {got} ≠ المسجَّل {ANCHOR_EXPECT} ⇒ يُوقَف بلا تغييرٍ صامت")
        log("JUDGE rc=6 · هُويّةُ المجتمع لم تُطابق `§⑩-ⓑ`")
        return 6
    log(f"   ✅ الأربعةُ أُعيد اشتقاقُها بتواريخها بالضبط: {ANCHOR_EXPECT}")

    # ── `§⑪-ⓒ` القناةُ الثانية: بصمةُ المؤشّر ─────────────────────────────────
    isyms = sorted({t["symbol"] for t in ia.collect("recheck") if t["fps"]})
    hist_ind = (bot.download_history(isyms, start_override=ia.WARMUP)
                if isyms else {})
    icases, idiag = indicator_scan(hist_ind)

    igot = {c["sym"]: c["date"] for c in icases}
    log("")
    log("═══ V-S11 هُويّةُ القناة الثانية — بصمةُ المؤشّر (§⑪-ⓒ) ═══")
    for sym, ln, st in idiag:
        log(f"   {sym:6s} سطر {ln:<5} {st}")
    if igot != IND_EXPECT:
        log(f"   🔴 المُشتقّ {igot} ≠ المسجَّل {IND_EXPECT} ⇒ يُوقَف بلا تغييرٍ صامت")
        log("JUDGE rc=6 · هُويّةُ القناة الثانية لم تُطابق `§⑪-ⓒ`")
        return 6
    log(f"   ✅ الأربعةُ أُعيد اشتقاقُها بتواريخها بالضبط: {IND_EXPECT}")
    log("   (والصفُّ بلا مستوًى حاكمٍ يسقط في التغطية `V-S5` — لا يُطوى بصمت)")

    # 🔴 **`norm=False` صراحةً — لا بقراءةِ العلم:** المسارُ المنشورُ خامٌّ
    #   **بالتعريف**، وقراءةُ العلم هنا كانت تُسوّيه فتمحو مرجعَ `V-N1`.
    #   (‏أمسكه `V-N1` في أوّل تشغيلةٍ حيّة قبل أيّ حكم — والعيبُ عيبي.)
    rows, skipped, n_drop = build_rows(hist_old, hist_new, acases,
                                       icases=icases, hist_ind=hist_ind,
                                       norm=False)

    log("")
    log("═══ V-S3 الجدول (‏صفًّا صفًّا) ═══")
    log("   الرمز  التاريخ     الفريم  مرجع    فيصل    A0      A1      A2      "
        "A-FAR   A-MID   A-HL    خطأ%A0  خطأ%RAND")
    for r in rows:
        tag = {"daily": "يوميّ", "h4": "4س*", "ambig": "ملتبس*"}[r["frame"]]
        log(f"   {r['sym']:6s} {r['asof']}  {tag:6s} {r['refpx']:<7.3f} "
            f"{r['ref']:<7.3f} {str(r['a0']):<7s} {str(r['a1']):<7s} "
            f"{str(r['a2']):<7s} {str(r['far']):<7s} {str(r['mid']):<7s} "
            f"{str(r['hl']):<7s} {str(r['e0']):<7s} {r['er']}")
    log("   (* وصفيٌّ بنصّ §⑨-ⓐ — خارج كلّ معيار · وA1/A2/A-FAR/A-MID/A-HL "
        "وصفيّون بنصّ §⑩-ⓖ)")
    log(f"   §⑩-ⓔ مستوياتٌ استُبعدت بوسم مؤشّر السعر (‏{MARKER_TOL}%): **{n_drop}**")
    log(f"   V-S5 تغطية: طُلبت {len(CASES) + len(acases) + len(icases)} · "
        f"نجحت {len(rows)} · استُبعدت {len(skipped)}")
    for s in skipped:
        log(f"        ⟶ {s[0]} {s[1]}: {s[2]}")

    gov, n, nsym, share, p, med, med_r, ctrl_ok = stats_of(rows)
    log("")
    log("═══ الحاكم (الصفوفُ اليوميّة وحدَها) ═══")
    log(f"   ثلاثيّاتٌ حاكمة: **{n}** من **{nsym}** رمزًا (الأرضيّة {SD0_MIN_ROWS}"
        f"/{SD0_MIN_SYMS})")
    if gov:
        below = sum(1 for r in gov if r["a0"] is not None and r["a0"] < r["ref"])
        log(f"   `SD1` A0 أدنى في **{below}/{n}** = {share:.1f}% · p={p} "
            f"(الحدّ {SD1_SHARE}% و{SD1_P})")
        log(f"   `SD2` وسيطُ |خطأ A0| = **{med:.2f}%** (الحدّ {SD2_MEDIAN}%)")
        log(f"   `SD3` وسيطُ خطأ A-RAND = "
            f"{('%.2f%%' % med_r) if med_r is not None else '—'} ⇒ أسوأُ من A0؟ "
            f"**{'نعم' if ctrl_ok else 'لا'}**")
        absf = [abs(r["ef"]) for r in gov if r["ef"] is not None]
        log(f"   (وصفيّ) وسيطُ |خطأ A-FAR| = {_med(absf):.2f}% — "
            f"**متقاعدٌ شاهدًا** (`§⑩-ⓕ`)")

    nb, nn, nshare, np_, nok, npbest = sd1_new_of(gov)
    log("")
    log("═══ §⑪-ⓔ `SD1-NEW` — الأربعةُ الجديدةُ وحدَها (نظيفٌ: لم يُقَس قطّ) ═══")
    if nn:
        log(f"   A0 أدنى في **{nb}/{nn}** = {nshare:.1f}% · p={np_} "
            f"(الحدّ {SD1_SHARE}% و{SD1_P}) ⇒ **{'تعبر' if nok else 'تسقط'}**")
        log(f"   الرموز: {sorted(r['sym'] for r in gov if r.get('origin') == 'indicator')}")
        _feas = ("🔴 **غيرُ قابلٍ للعبور بأيّ نتيجة** — عيبُ عقدي يُعلَن (`§⑫`)"
                 if npbest > SD1_P else "✅ العبورُ ممكنٌ بنيويًّا")
        log(f"   🔎 أفضلُ `p` مُتاحٍ عند الإجماع ({nn}/{nn}) = **{npbest}** "
            f"مقابل الحدّ {SD1_P} ⇒ {_feas}")
    else:
        log("   🔴 صفرُ صفٍّ جديدٍ حاكم — `SD1-NEW` بلا مجتمعٍ فتسقط بالبناء")
    log("   🔒 وقاعدةُ القراءة مسجَّلةٌ قبل الرقمين: **يُنشَران معًا ويُقرأ بالأضعف**")

    rc, txt = read_verdict(n, nsym, share, p, med, ctrl_ok, sd1_new=nok)

    log("")
    log("═══ V-S9 الحساسيّاتُ الثلاث (وصفيّةٌ — لا تدخل أيَّ معيار) ═══")
    for nm, kw in (("ⓒ القصُّ عند `date` لصفوف `spot`", {"asof_mode": "date"}),
                   ("ⓓ سعرُ المرجع = إغلاقُ `match_date` في الثلاثة",
                    {"ref_mode": "close"}),
                   ("ⓔ بلا قاعدةِ وسمِ مؤشّر السعر", {"marker": False})):
        try:
            r2, _s2, _d2 = build_rows(hist_old, hist_new, acases,
                                      icases=icases, hist_ind=hist_ind,
                                      norm=False, **kw)
            g2, n2, ns2, sh2, p2, md2, mr2, ok2 = stats_of(r2)
            _nb2, _nn2, nsh2, np2, nok2, _pb2 = sd1_new_of(g2)
            log(f"   {nm}: حاكمة {n2}/{ns2} · SD1 {sh2:.1f}% p={p2} · "
                f"SD1-NEW {nsh2:.1f}% p={np2} · "
                f"SD2 {md2:.2f}% · SD3 "
                f"{('%.2f%%' % mr2) if mr2 is not None else '—'} ⇒ "
                f"{'تعبر' if ok2 else 'تسقط'} · "
                f"الفرعُ {read_verdict(n2, ns2, sh2, p2, md2, ok2, sd1_new=nok2)[0]}")
        except Exception as e:                                 # noqa: BLE001
            log(f"   {nm}: ⛔ رمى {type(e).__name__}")

    log("")
    log("═══ 🔎 تشخيصٌ: مقياسُ التقسيم عند تاريخ الشارت (يُطبَع ولا يُستعمَل) ═══")
    for c in list(acases) + list(icases):
        log(f"   {c['sym']:6s} {c['match_date']}  عامل={c['sf']:.6g}  "
            f"{'✅ قابلٌ للمقارنة' if abs(c['sf'] - 1.0) < 1e-9 else '🔴 مقياسان مختلفان — الصفُّ غيرُ قابلٍ للمقارنة'}")
    log("   (غيرُ الواحد = مستوياتُ الشاشة و`A0` بمقياسين ⇒ حدُّ صدقٍ يُعلَن ولا يُصلَح صامتًا)")

    log("")
    log("═══ ⓖ وصفيٌّ — خارجَ كلّ معيار ═══")
    log(f"   صفوفُ 4س/الملتبس: "
        f"{[r['sym'] + ' ' + r['frame'] for r in rows if r['frame'] != 'daily'] or '—'}")
    log(f"   المؤرَّخُ بالتسامح الضيّق {pa.TOL_TIGHT}% وحدَه (لا يُؤرِّخ حاكمًا): "
        f"{[f'{s}:{d}' for s, _l, d in tight_only] or '—'}")

    log("")
    log("═══ §⑪-ⓕ تنبّؤاتي — تُنشَر مكذَّبةً أو مؤكَّدة ═══")
    _sd1 = share >= SD1_SHARE and p <= SD1_P
    _spread = [r["e0"] for r in gov if r["e0"] is not None]
    _rng = (max(_spread) - min(_spread)) if _spread else 0.0
    log(f"   P⑪-1 `SD1` لا يعبر ⟶ {'✅ مؤكَّد' if not _sd1 else '🔴 مكذَّب'}")
    log(f"   P⑪-2 `SD1-NEW` لا يعبر ⟶ {'✅ مؤكَّد' if not nok else '🔴 مكذَّب'}")
    log(f"   P⑪-3 الفجوةُ طيفٌ واسع ⟶ مدى الخطأ {_rng:.2f} نقطة "
        f"({min(_spread) if _spread else 0:.2f}% ⟶ {max(_spread) if _spread else 0:.2f}%)")
    log(f"   P⑪-4 مخالفٌ واحدٌ على الأقلّ بين الأربعة الجديدة ⟶ "
        f"{'✅ مؤكَّد' if nn and nb < nn else '🔴 مكذَّب' if nn else '—'} "
        f"({nn - nb if nn else 0} مخالفًا)")

    # ══════════ ⚖️ `T-SPLITNORM` — يعمل فقط بالعلم (`V-N7`) ══════════════════
    if norm_on():
        log("")
        log("═════════ ⚖️ `T-SPLITNORM` — تسويةُ التقسيم (العقد `splitnorm_prereg.md`) ═════════")
        guards, bad_g = True, []

        # `V-N1` — الخامُّ يُعيد المنشورَ بت-بت قبل أيّ تسوية
        _got = {"below": below if gov else 0, "n": n, "p": p,
                "med": round(med, 2), "rand": round(med_r, 2) if med_r else None}
        _ok1 = all(_got[k] == RAW_PUBLISHED[k] for k in RAW_PUBLISHED)
        log(f"   `V-N1` الخامُّ ≡ المنشور (`35455722208`): "
            f"{'✅' if _ok1 else '🔴'} — المُشتقّ {_got} · المنشور {RAW_PUBLISHED}")
        if not _ok1:
            guards, _ = False, bad_g.append("V-N1")

        # `V-N3` — الدالّةُ قسمةٌ لا ضرب (هُويّةٌ عند 1 · وقسمةٌ عند غيره)
        _id = norm_level(12.345, 1.0) == 12.345
        _dv = abs(norm_level(1.712, 0.0909091) - 18.832) < 0.01
        _nm = abs(norm_level(1.712, 0.0909091) - 1.712 * 0.0909091) > 1.0
        log(f"   `V-N3` قسمةٌ لا ضرب: هُويّةٌ عند 1={_id} · القسمةُ صحيحة={_dv} · "
            f"ليست ضربًا={_nm} ⇒ {'✅' if (_id and _dv and _nm) else '🔴'}")
        if not (_id and _dv and _nm):
            guards, _ = False, bad_g.append("V-N3")

        nrows, nskip, nn_drop = build_rows(hist_old, hist_new, acases,
                                           icases=icases, hist_ind=hist_ind,
                                           norm=True)
        ngov, nn2, nsym2, nshare2, np2, nmed2, nmedr2, nok2 = stats_of(nrows)

        # `V-N4` — اشتقاقُ `§③` بيدي يُقارَن بالمحسوب · التعارضُ يوقف.
        # 🔑 **المقارنةُ على المستوى الخامِّ مُسوًّى** (`norm_level(ref_خام, sf)`)
        #   لا على الصفّ الناجي: نصُّ `§③` اشتقاقٌ للمستوى نفسِه، **وبقاءُ الصفّ
        #   بعد `drop_marker` مسألةٌ أخرى يرصدها `SN2`** — فلا يُخلَط الأمران.
        _by = {r["sym"]: r for r in ngov}
        _raw_by = {r["sym"]: r for r in gov}
        log("   `V-N4` اشتقاقُ `§③` مقابل المحسوب (على المستوى الخامِّ مُسوًّى):")
        for sym, want in sorted(DERIV_EXPECT.items()):
            r0 = _raw_by.get(sym)
            if r0 is None:
                log(f"        {sym:6s} 🔴 غائبٌ عن **الخام** ⇒ تعارضٌ حقيقيّ")
                guards, _ = False, bad_g.append(f"V-N4:{sym}")
                continue
            _sfx = split_factor_of(sym, r0["asof"])
            _calc = norm_level(r0["ref"], _sfx)
            _alive = "✅ باقٍ" if sym in _by else "⚠️ خرج بعد `drop_marker` (يرصده `SN2`)"
            r = {"ref": _calc}
            d = abs(r["ref"] - want) / want * 100.0
            _o = d <= DERIV_TOL_PCT
            log(f"        {sym:6s} خامٌّ={r0['ref']:.4f} ÷ {_sfx:.6g} = "
                f"{r['ref']:.4f} · اشتقاقي={want} · فرق={d:.3f}% ⇒ "
                f"{'✅' if _o else '🔴 تعارضٌ — الخطأُ خطئي ويُنشَر'} · {_alive}")
            if not _o:
                guards, _ = False, bad_g.append(f"V-N4:{sym}")

        # `SN1` الحياد — كلُّ صفٍّ عاملُه 1 يطابق نظيرَه الخام بت-بت
        _raw = {(r["sym"], r["asof"]): r for r in gov}
        neutral, diffs = True, []
        for r in ngov:
            if abs(r["sf"] - 1.0) > 1e-9:
                continue
            o = _raw.get((r["sym"], r["asof"]))
            if o is None or o["ref"] != r["ref"] or o["a0"] != r["a0"] \
                    or o["e0"] != r["e0"]:
                neutral = False
                diffs.append(f"{r['sym']} {r['asof']}")
        log("")
        log(f"   `SN1` الحياد (صفوفُ العامل 1 ≡ الخام): "
            f"{'✅ تعبر' if neutral else '🔴 تسقط'} — "
            f"المختلف: {diffs or 'لا شيء'}")

        # `SN2` توسُّعُ المجتمع — **أعمى**: صفوفٌ استُبعدت خامًا ودخلت مُسوّاةً
        _rk = {(x[0], x[1]) for x in skipped}
        _nk = {(x[0], x[1]) for x in nskip}
        _new_in = sorted(_rk - _nk)
        _new_out = sorted(_nk - _rk)
        log(f"   `SN2` توسُّعُ المجتمع: خامًا استُبعد {len(skipped)} · مُسوًّى "
            f"{len(nskip)} ⇒ **دخل {len(_new_in)}** · خرج {len(_new_out)}")
        log(f"        الداخلُ: {_new_in or '—'} · الخارجُ: {_new_out or '—'}")

        # `SN3` صفوفُ الكاتالوج — **أعمى**: هل لأيٍّ منها عاملٌ ≠ 1؟
        _cat = [r for r in ngov if r.get("origin") == "cat"]
        _cat_sp = [r for r in _cat if abs(r["sf"] - 1.0) > 1e-9]
        log(f"   `SN3` صفوفُ الكاتالوج: {len(_cat)} · منها بعاملٍ ≠ 1: "
            f"**{len(_cat_sp)}** {[(r['sym'], round(r['sf'], 6)) for r in _cat_sp] or ''}")
        if _cat_sp:
            log("        🔴🔴 ⇒ **الحكمُ السابق (`SD1` ‏6/9) كان هو نفسُه ملوَّثًا "
                "بأثر مقياس** — اكتشافٌ عن الحكم لا عن التعريف")

        # الشواذُّ: هل بقي صفُّ عاملٍ ≠ 1 خارجَ مدى صفوف العامل 1؟
        _one = [abs(r["e0"]) for r in ngov
                if abs(r["sf"] - 1.0) <= 1e-9 and r["e0"] is not None]
        _sp = [r for r in ngov if abs(r["sf"] - 1.0) > 1e-9 and r["e0"] is not None]
        _cap = max(_one) if _one else 0.0
        _out = [(r["sym"], r["e0"]) for r in _sp if abs(r["e0"]) > _cap]
        outliers_ok = bool(_sp) and not _out
        log(f"   الشواذُّ بعد التسوية: سقفُ صفوف العامل 1 = {_cap:.2f}% · "
            f"الباقي خارجَه: {_out or 'لا شيء'} ⇒ "
            f"{'✅' if outliers_ok else '🔴' if _sp else '⚪ لا صفَّ عاملٍ ≠ 1'}")

        log("")
        log("═══ الوصفيُّ المُسوّى — **موسومٌ بحالة العمى** (`§④`-4) ═══")
        log("   الرمز  التاريخ     أصل     عامل        فيصل-خام  فيصل-مُسوًّى  A0      خطأ%")
        for r in sorted(ngov, key=lambda x: (x["origin"], x["sym"])):
            o = _raw.get((r["sym"], r["asof"]))
            log(f"   {r['sym']:6s} {r['asof']}  {r['origin']:9s} {r['sf']:<11.6g} "
                f"{(o['ref'] if o else 0):<9.3f} {r['ref']:<11.3f} "
                f"{str(r['a0']):<7s} {str(r['e0'])}")
        _nb3, _nn3, nsh3, npv3, nok3, _pb3 = sd1_new_of(ngov)
        log(f"   `SD1` مُسوًّى: A0 أدنى في **{sum(1 for r in ngov if r['a0'] is not None and r['a0'] < r['ref'])}/{nn2}** "
            f"= {nshare2:.1f}% · p={np2} ⇒ 🔴 **مشتقٌّ سلفًا في `§③` — لا يُحسَب تنبّؤًا**")
        log(f"   `SD2` مُسوًّى = {nmed2:.2f}% · `SD3` = "
            f"{('%.2f%%' % nmedr2) if nmedr2 is not None else '—'} ⇒ "
            f"أسوأُ من A0؟ **{'نعم' if nok2 else 'لا'}** (‏`SD1-NEW` {nsh3:.1f}% p={npv3})")

        nrc, ntxt = norm_verdict(guards, neutral, outliers_ok, nn2, nsym2)
        log("")
        log("═══ حكمُ `T-SPLITNORM` ═══")
        if not guards:
            log(f"   🔴 حارسٌ سقط: {bad_g} ⇒ يُوقَف قبل أيّ حكم")
            log(f"JUDGE rc={NORM_GUARD_RC} · حارسُ التسوية سقط — لا حكم ولا اعتماد")
            return NORM_GUARD_RC
        log(f"   حاكمةٌ مُسوّاة: {nn2} من {nsym2} رمزًا · وسمُ المؤشّر أسقط {nn_drop}")
        log(f"JUDGE rc={nrc} · {ntxt}")
        return nrc

    log("")
    log("═══ الحكم ═══")
    if rc == 3:
        log(f"   V-S8 سببُ الفرع 3: "
            f"{branch3_reason(n, nsym, med, med_r, sd1=_sd1, sd1_new=nok)}")
    log(f"JUDGE rc={rc} · {txt}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
