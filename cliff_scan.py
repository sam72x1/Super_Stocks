#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""⛰️ T-CLIFF — أذرع مُرشّح الكليف: **مصدر الأذرع الوحيد** + قياس الكلفة على السوق الكامل.

العقد: `cliff_prereg.md` (مدفوع **قبل** أي رقم) · الدافع: `hunter_six_result.md` §③-①
(«مُرشّح الكليف هو الحاجب الأول في الصيّاد — وهو بوّابة تكلفة لا شرطًا فيصليًّا»).

**هذا الملف يحمل شيئين لا ثالث لهما:**

  ① **تعريف الأذرع الخمس** (‏§1) — ويستوردها `hunter_six_check.py` منه، فلا تتفرّق
     نسختان بتعريفين (لو تفرّقتا صارت «الكلفة» و«الاسترجاع» عن ذراعين مختلفتين وهي
     أسوأ أنواع البطلان: تجربةٌ تبدو متّسقة وليست كذلك). **وميكانيكا الذراع في مكانٍ
     واحد: `arm_context`** — يستعمله مسح السوق عبر `run_arm`، وتستعمله أداة المشي
     مباشرةً (لأن نداءها `S.scan_split_hunter(...)` يجب أن يبقى مقروءًا في موضعه،
     وقفلٌ في السويّة يحرس ذلك). و`--selftest` يُثبت تطابق المدخلين لكل ذراع.
  ② **المقياس الثاني الإلزاميّ** (‏`cliff_prereg.md` §③-2): كم مطابقًا كاملًا في اليوم
     على السوق الكامل، وكم رمزًا يدخل مرحلة `probe` (كلفة الشبكة التي وُضع الكليف لأجلها).

**🔒 القيد الحاسم (‏§② من التسجيل): الذراع تغيّر مُرشّح الدخول وحده.** الشروط الستة
(①-⑥) تبقى من دوال الإنتاج حرفيًّا، **والحكم النهائي يبقى من `scan_split_hunter` نفسها**
— هذا الملف **لا يحكم على أي سهم أبدًا**؛ يبني القاموس ويضبط عتبة الدخول ويقرأ ما تُرجعه
دالّة الإنتاج. وميكانيكا كل ذراع مصرَّحٌ بها في `ARM_SPEC[...]["mech"]` وتُطبع في السجلّ.

**ميكانيكا الأذرع (مصرَّحة — لا خفاء):**
  • `c0/c1/c2` → **ضبط `CONFIG["SPLIT_CLIFF_PCT"]` مؤقّتًا** داخل `try/finally` وتمرير
    القاموس كاملًا ⇒ **الإنتاج نفسه** يطبّق مُرشّح الكليف. (‏c0 = القيمة الإنتاجية بلا
    تغيير أصلًا.)
  • `c3/c4` → معيارهما **ليس** «هبوط يوم واحد ≥X%» فلا تعبّر عنه العتبة؛ فتُعطَّل عتبة
    الإنتاج تعطيلًا **تامًّا** (‏`CLIFF_DISABLED` ⇒ الشرط `cliff <= +1e7` صادقٌ لكل قيمة
    ممكنة لأن `cliff ≥ -1` دائمًا) ثم:
        – `c4`: بلا تقييد ⇒ **بلا مُرشّح كليف إطلاقًا** (حدّ الالتقاط الأعلى).
        – `c3`: يُقيَّد القاموس بمجموعة الرموز المستوفية للمعيار التراكميّ.
    **وفي الحالتين يبقى الحكم — وكلُّ الشروط الستة وفلتر السعر وسقف `probe` — داخل
    `scan_split_hunter` حرفيًّا**، والمقيَّد هو *من يدخل* لا *من يُقبَل*.
  • **قفل الميكانيكا** (‏`--selftest` و`CLIFF_EQUIV_DAYS` في المسح): تُشغَّل `c0`
    بالميكانيكتين (عتبةٌ إنتاجية مقابل تعطيلٍ + ترشيحٍ خارجيّ) ويُشترط تطابق مجموعة
    المطابقين — فلو غيّر التعطيلُ حكمًا لظهر فورًا.

**الكلفة تُقاس من الإنتاج لا من حسابي:** عدّاد `probe` = عدد نداءات `fetch_splits`
المحقونة (‏`scan_split_hunter` تناديها مرة لكل رمزٍ اجتاز المُرشّح **وبعد** السقف)، وكذلك
`fetch_float` (مرحلة ⑤) و`fetch_pump` (مرحلة ⑥). وحسابي الخارجيّ للعدد **قبل** السقف
يُقارَن بعدّاد الإنتاج كل يوم (‏`probe = min(pre_raw, cap)`) وأي اختلاف يُطبع ⚠️.

🔒 بحث/قياس فقط — صفر مسّ إنتاج · لا تلغرام · لا حفظ حالة · لا بوّابة · لا وزن ·
   لا `LOGIC_VERSION` · لا تغيير عتبةٍ دائم (كل ضبطٍ داخل `try/finally` ومُتحقَّق منه).

التشغيل:
  BT_FROZEN_PATH=frozen_backtest.pkl.gz python cliff_scan.py
  python cliff_scan.py --selftest          # تحقّق بلا شبكة (اصطناعيّ) — لا يلزمه لقطة
متغيّرات:
  CLIFF_ARMS        أذرع مفصولة بفاصلة (افتراضي: c0,c1,c2,c3,c4)
  CLIFF_DAYS        عدد أيام العيّنة (0/فارغ = كل أيام اللقطة) — أي تخفيف **يُعلَن**
  CLIFF_WARMUP      أقلّ عدد شموع مطلوب ليُمشى اليوم (افتراضي 20 = حدّ الإنتاج نفسه)
  CLIFF_FLOAT_MODE  cache | yahoo (افتراضي yahoo: الذاكرة ثم `_yahoo_float` مصدر الإنتاج)
  CLIFF_FLOAT_BUDGET سقف نداءات ياهو الفريدة (افتراضي 1500) — النفاد **يُعلَن بصوت عالٍ**
  CLIFF_EQUIV_DAYS  أيام قفل تكافؤ الميكانيكا (افتراضي 5 · 0 = تعطيل مع إعلانه)
  CLIFF_PROBE_CAP   تجاوزٌ **بحثيّ مُعلَن** لسقف `SPLIT_RADAR_PROBE_CAP` أثناء القياس
                    (فارغ = سقف الإنتاج). سببه: بلا مُرشّح كليف (‏c4) يصير **السقف
                    نفسه** هو المُرشّح المُلزِم، فلا يقيس «حدّ الالتقاط الأعلى» بل
                    «أعمق 80 هابطًا». يُطبع في الترويسة والخلاصة وكل صفّ CSV.
  CLIFF_CSV         مسار CSV أرشيفيّ (الحكم من السجلّ — تنزيل الـartifacts محجوب)
"""
import csv
import datetime as dt
import json
import os
import statistics
import sys
from collections import deque

# ═══════════════════════════════════════════════════════════════════════════════
# §1 — الأذرع (مصدر الحقيقة الوحيد؛ يستوردها `hunter_six_check.py`)
# ═══════════════════════════════════════════════════════════════════════════════

# ثوابت الذراع c3 — **من التسجيل المسبق `cliff_prereg.md` §② حرفيًّا**، وليست
# قابلة للضبط بالبيئة عمدًا: ذراعٌ متحرّكة الحدّ = p-hacking بعد رؤية الأرقام.
CLIFF_CUM_PCT = 40.0        # هبوط تراكميّ ≥40%
CLIFF_CUM_DAYS = 20         # خلال ≤20 جلسة

# قيمة تعطيل عتبة الإنتاج تعطيلًا تامًّا: الشرط في `scan_split_hunter` هو
# `cliff <= -SPLIT_CLIFF_PCT/100`. بـ`-1e9` يصير الحدّ `+1e7`، و`cliff` عائدٌ يوميّ
# ‏= c[t]/c[t-1]-1 بمقام موجب ⇒ **‏≥ -1 دائمًا** ⇒ الشرط صادقٌ لكل مدخل ممكن.
# (مُقفَل في `--selftest`: سهمٌ مسطّح cliff=0 يمرّ في c4 ويسقط في c0.)
CLIFF_DISABLED = -1.0e9

ARMS = ("c0", "c1", "c2", "c3", "c4")

ARM_SPEC = {
    "c0": {"kind": "day", "pct": None, "mech": "عتبة الإنتاج كما هي (بلا تغيير)",
           "desc": "الأساس: هبوط **يومٍ واحد** ≥SPLIT_CLIFF_PCT% داخل نافذة الحدث"},
    "c1": {"kind": "day", "pct": 25.0, "mech": "ضبط CONFIG مؤقّتًا (try/finally)",
           "desc": "هبوط **يومٍ واحد** ≥25%"},
    "c2": {"kind": "day", "pct": 20.0, "mech": "ضبط CONFIG مؤقّتًا (try/finally)",
           "desc": "هبوط **يومٍ واحد** ≥20%"},
    "c3": {"kind": "cum", "pct": CLIFF_CUM_PCT,
           "mech": "تعطيل عتبة الإنتاج + **تقييد القاموس** بالمستوفين للمعيار التراكميّ",
           "desc": f"**تراكميّ**: هبوط ≥{CLIFF_CUM_PCT:g}% خلال ≤{CLIFF_CUM_DAYS} جلسة "
                   "(بلا شرط يومٍ واحد)"},
    "c4": {"kind": "none", "pct": None, "mech": "تعطيل عتبة الإنتاج بلا أي تقييد",
           "desc": "**بلا مُرشّح كليف إطلاقًا** (حدّ الالتقاط الأعلى)"},
}


def arm_valid(arm):
    return isinstance(arm, str) and arm.strip().lower() in ARM_SPEC


def arm_needs_prefilter(arm):
    """هل تحتاج الذراع **ترشيحًا خارجيًّا** لمجموعة الرموز الداخلة؟ (‏c3 وحدها)."""
    return ARM_SPEC[arm]["kind"] == "cum"


def arm_cfg_value(arm, prod_pct):
    """القيمة التي تُضبَط عليها `CONFIG["SPLIT_CLIFF_PCT"]` أثناء نداء الإنتاج."""
    spec = ARM_SPEC[arm]
    if spec["kind"] == "day":
        return float(prod_pct) if spec["pct"] is None else float(spec["pct"])
    return CLIFF_DISABLED


def arm_label(arm, prod_pct):
    spec = ARM_SPEC[arm]
    if spec["kind"] == "day":
        thr = float(prod_pct) if spec["pct"] is None else float(spec["pct"])
        return f"{arm}: {spec['desc']} ⇒ عتبة فعليّة {thr:g}%"
    if spec["kind"] == "cum":
        return f"{arm}: {spec['desc']}"
    return f"{arm}: {spec['desc']}"


# ── المقاييس (نقيّة · بلا نظر مستقبليّ · مرجعيّة) ──────────────────────────────
def day_cliff_metric(c, look):
    """أعمق **عائد يوميّ** داخل النافذة — **نسخة حرفيّة من تعبير الإنتاج**
    (‏`scan_split_hunter` سطر ~5437): `min(c[-k]/c[-k-1]-1 for k in 1..look if c[-k-1]>0)`.
    يرجّع None لو لا نسبة صالحة (الإنتاج في هذي الحالة يرمي `ValueError` من `min()`
    فيتخطّى الرمز — والنتيجة نفسها: لا يدخل)."""
    n = len(c)
    if n < 2:
        return None
    look = min(int(look), n - 1)
    vals = [c[-k] / c[-k - 1] - 1.0 for k in range(1, look + 1) if c[-k - 1] > 0]
    return min(vals) if vals else None


def cum_drop_metric(c, look, win=CLIFF_CUM_DAYS):
    """أعمق **هبوط تراكميّ** خلال ≤`win` جلسة، داخل نفس نافذة `look` التي يستعملها
    الإنتاج. التعريف: لكل جلسة j في النافذة، الهبوط = `c[j] / max(c[j-win .. j]) - 1`
    (‏= الهبوط من قمّةٍ تسبقه بـ`win` جلسة على الأكثر)، والمقياس = أدناها.
    ⚠️ **حدّ مُعلَن:** القمّة قد تقع حتى `win` جلسة **قبل** بداية نافذة `look` — مقصود
    (وإلا لتعذّر قياس هبوطٍ يبدأ عند حافة النافذة)، ومُصرَّحٌ به لا مخفيّ."""
    n = len(c)
    if n < 2:
        return None
    look = max(1, min(int(look), n - 1))
    start = max(1, n - look)
    best = None
    for j in range(start, n):
        seg = c[max(0, j - win):j + 1]
        pk = max(seg)
        if pk <= 0:
            continue
        d = c[j] / pk - 1.0
        best = d if best is None else min(best, d)
    return best


def arm_gate(arm, c, look, prod_pct):
    """بوّابة الدخول للذراع على سلسلة إغلاقاتٍ واحدة. تُرجّع dict وصفيًّا:
    {ok, metric, thr, unit} — و`metric=None` تعني «تعذّر القياس» **لا صفرًا**."""
    spec = ARM_SPEC[arm]
    if spec["kind"] == "none":
        m = day_cliff_metric(c, look)          # يُعرَض للسياق ولا يحكم
        return {"ok": True, "metric": m, "thr": None, "unit": "يوميّ (لا يحكم)"}
    if spec["kind"] == "cum":
        m = cum_drop_metric(c, look)
        thr = -float(spec["pct"]) / 100.0
        return {"ok": (m is not None and m <= thr), "metric": m, "thr": thr,
                "unit": f"تراكميّ≤{CLIFF_CUM_DAYS}ج"}
    thr = -float(arm_cfg_value(arm, prod_pct)) / 100.0
    m = day_cliff_metric(c, look)
    return {"ok": (m is not None and m <= thr), "metric": m, "thr": thr,
            "unit": "يوميّ"}


# ── مسارات سريعة (للسوق الكامل) — **مُقفَلة بالمطابقة مع المرجع** في --selftest ──
def sliding_min(a, win):
    """`out[i] = min(a[max(0,i-win+1) : i+1])` بطابور رتيب — O(n)."""
    out = [0.0] * len(a)
    dq = deque()
    for i, x in enumerate(a):
        while dq and a[dq[-1]] >= x:
            dq.pop()
        dq.append(i)
        while dq[0] <= i - win:
            dq.popleft()
        out[i] = a[dq[0]]
    return out


def daily_return_series(c):
    """`ret[j] = c[j]/c[j-1]-1` (و`+inf` حيث لا نسبة صالحة = ما يستبعده الإنتاج)."""
    inf = float("inf")
    out = [inf] * len(c)
    for j in range(1, len(c)):
        if c[j - 1] > 0:
            out[j] = c[j] / c[j - 1] - 1.0
    return out


def cum_drop_series(c, win=CLIFF_CUM_DAYS):
    """`out[j] = c[j]/max(c[j-win..j]) - 1` بطابور رتيب — O(n) · بلا نظر مستقبليّ."""
    out = [0.0] * len(c)
    dq = deque()
    for j, x in enumerate(c):
        while dq and c[dq[-1]] <= x:
            dq.pop()
        dq.append(j)
        while dq[0] <= j - (win + 1):
            dq.popleft()
        pk = c[dq[0]]
        out[j] = (x / pk - 1.0) if pk > 0 else 0.0
    return out


# ── ضبط CONFIG المؤقّت (‏try/finally + تحقّق) ──────────────────────────────────
class CfgRestoreError(RuntimeError):
    """تلوّث CONFIG: لم تُستعَد القيمة الأصلية — يُرفع بصوتٍ عالٍ لا يُبتلع."""


class cfg_override:
    """مدير سياق يضبط مفتاح `CONFIG` مؤقّتًا **ويعيده في `finally` ويتحقّق**.
    (‏فخّ تلوّث CONFIG موثّقٌ في المستودع: عتبةٌ تبقى مضبوطة بعد التجربة ⇒ كل ما بعدها
    يُقاس بذراعٍ خاطئة صامتًا.) يعيد الحالة **الأصلية بدقّة** — بما فيها «المفتاح لم
    يكن موجودًا» (فلا نخترع مفتاحًا)."""

    _MISSING = object()

    def __init__(self, cfg, key, value):
        self.cfg, self.key, self.value = cfg, key, value
        self.old = self._MISSING

    def __enter__(self):
        self.old = self.cfg[self.key] if self.key in self.cfg else self._MISSING
        self.cfg[self.key] = self.value
        return self

    def __exit__(self, *exc):
        if self.old is self._MISSING:
            self.cfg.pop(self.key, None)
            ok = self.key not in self.cfg
        else:
            self.cfg[self.key] = self.old
            ok = self.cfg.get(self.key) == self.old
        if not ok:
            raise CfgRestoreError(f"تعذّرت استعادة CONFIG[{self.key!r}]")
        return False        # لا يبتلع أي استثناء


class Counters(dict):
    """عدّادات مراحل الإنتاج — تُملأ من **داخل** `scan_split_hunter` عبر الجالبات
    المحقونة (‏`fetch_splits` = مرحلة probe · `fetch_float` = ⑤ · `fetch_pump` = ⑥)،
    فالكلفة مقروءةٌ من الإنتاج لا محسوبةٌ عندي."""

    def reset(self):
        for k in ("probe", "float", "pump", "offering"):
            self[k] = 0
        return self


def make_fetchers(splits_of, float_of, counters, pump_fn):
    """يبني الجالبات الخمسة المحقونة + العدّادات. `fetch_borrow`/`fetch_offering`
    مُعطَّلان عمدًا (‏صفر شبكة · سياقٌ لا يدخل الحكم · قناة SEC معطَّلة = حدّ مُعلَن في
    `cliff_prereg.md` §⑥-3)."""
    def _fs(sym):
        counters["probe"] = counters.get("probe", 0) + 1
        return splits_of(sym)

    def _ff(sym):
        counters["float"] = counters.get("float", 0) + 1
        return float_of(sym)

    def _fp(df):
        counters["pump"] = counters.get("pump", 0) + 1
        return pump_fn(df)

    def _fo(sym, today=None):
        counters["offering"] = counters.get("offering", 0) + 1
        return None

    return {"fetch_splits": _fs, "fetch_float": _ff, "fetch_borrow": lambda s: None,
            "fetch_pump": _fp, "fetch_offering": _fo}


# ── 🚦 ميكانيكا الذراع — **مكانٌ واحد** تستعمله الأداتان (بلا تفرّق نسختين) ──
class arm_context:
    """مدير سياق الذراع: يتحقّق من الحرّاس · يقيّد القاموس لأذرع الترشيح الخارجيّ ·
    يضبط عتبة الإنتاج ويعيدها في `finally`. **يُنتِج القاموس الذي يُمرَّر لدالّة
    الإنتاج، والنداء يبقى صريحًا في يد الأداة** (‏`S.scan_split_hunter(...)`) فيُقرأ
    من موضعه ولا يُخبَّأ خلف طبقة — قاعدة «الميزة موصولة تُثبَت من نقطة النداء».

    `prefilter`: مجموعة الرموز المسموح دخولها (لأذرع الترشيح الخارجيّ **فقط**).
    🔒 قفلان يمنعان انزلاق الذراع صامتًا:
      • ذراعٌ تحتاج ترشيحًا و`prefilter is None` ⇒ **يُرفع استثناء** (وإلا لصارت c3
        هي c4 بلا أن يلاحظ أحد).
      • ذراعٌ لا تحتاجه ومُرِّر لها ⇒ **يُرفع استثناء** (وإلا لتلوّث خطُّ الأساس).
    """

    def __init__(self, S, arm, day_hist, prod_pct, prefilter=None):
        arm = (arm or "").strip().lower()
        if arm not in ARM_SPEC:
            raise ValueError(f"ذراع غير معروفة: {arm!r} (المتاح: {', '.join(ARMS)})")
        need = arm_needs_prefilter(arm)
        if need and prefilter is None:
            raise ValueError(
                f"الذراع {arm} تحتاج `prefilter` — تمريره None يحوّلها إلى c4 صامتًا")
        if (not need) and prefilter is not None:
            raise ValueError(
                f"الذراع {arm} لا تأخذ `prefilter` — تمريره يلوّث خطّ الأساس")
        self.arm, self.S = arm, S
        self.hist = (day_hist if not need
                     else {s: d for s, d in day_hist.items() if s in prefilter})
        self._cfg = cfg_override(S.CONFIG, "SPLIT_CLIFF_PCT",
                                 arm_cfg_value(arm, prod_pct))

    def __enter__(self):
        self._cfg.__enter__()
        return self.hist

    def __exit__(self, *exc):
        self._cfg.__exit__(*exc)
        return False        # لا يبتلع أي استثناء


def run_arm(S, arm, day_hist, today, fetchers, prod_pct, prefilter=None):
    """غلافٌ رقيق فوق `arm_context` **بنداء `scan_split_hunter` نفسها** (يستعمله
    مسح السوق الكامل؛ والأداة الأخرى تستعمل `arm_context` مباشرةً لأن نداءها يجب
    أن يبقى مقروءًا في موضعه)."""
    with arm_context(S, arm, day_hist, prod_pct, prefilter) as h:
        return S.scan_split_hunter(h, today=today, **fetchers) or []


# ═══════════════════════════════════════════════════════════════════════════════
# §2 — المسح على السوق الكامل (المقياس الثاني الإلزاميّ)
# ═══════════════════════════════════════════════════════════════════════════════
SIX = ("AZI", "DSY", "EHGO", "ZCMD", "JZ", "SPRC")
CONTROLS = ("JEM", "NUWE")


def _stats(vals):
    if not vals:
        return {"n": 0, "mean": None, "median": None, "max": None, "sum": 0}
    return {"n": len(vals), "mean": sum(vals) / len(vals),
            "median": statistics.median(vals), "max": max(vals), "sum": sum(vals)}


def _fmt(x, nd=2):
    return "—" if x is None else f"{x:.{nd}f}"


def _ratio(a, b):
    """نسبة a إلى b مع تصريحٍ صادق عن القسمة على صفر (لا «∞» صامتة)."""
    if b is None or a is None:
        return "—"
    if b == 0:
        return "—(الأساس صفر)" if a == 0 else "∞(الأساس صفر)"
    return f"×{a / b:.2f}"


class FloatSource:
    """الفلوت **بمصدر الإنتاج حرفيًّا** (`_yahoo_float` المتساهل — هو ما يناديه
    `scan_split_hunter` افتراضيًّا)، مع ذاكرةٍ لكل رمز (يُجلَب مرّة ويُعاد استعماله
    عبر كل الأيام والأذرع). ⚠️ **حدّ مُعلَن** (‏`cliff_prereg.md` §⑥-2): الفلوت **ليس
    point-in-time**. وعند نفاد الميزانية يُرجَع None (= «مجهول») **ويُعلَن بصوتٍ عالٍ**
    لأن الإنتاج يُقصي المجهول ⇒ عدد المطابقين يصير **أرضية لا سقفًا**."""

    def __init__(self, S, mode="yahoo", budget=1500, cache=None):
        self.S, self.mode, self.budget = S, mode, int(budget)
        self.cache = cache or {}
        self.memo = {}
        self.src = {}          # الرمز → مصدر قيمته (provenance يُطبع، لا يُفترَض)
        self.n_yahoo = 0
        self.exhausted = False

    def __call__(self, sym):
        if sym in self.memo:
            return self.memo[sym]
        val, src = None, "مجهول"
        c = (self.cache or {}).get(sym) or {}
        if isinstance(c, dict) and c.get("float") is not None:
            try:
                val, src = int(c["float"]), "company_cache"
            except Exception:
                val, src = None, "مجهول"
        if val is None and self.mode == "yahoo":
            if self.n_yahoo >= self.budget:
                self.exhausted = True
                src = "مجهول (نفدت الميزانية)"
            elif getattr(self.S, "yf", None) is not None:
                self.n_yahoo += 1
                try:
                    val = self.S._yahoo_float(sym)      # مصدر الإنتاج (المتساهل)
                    src = "ياهو" if val is not None else "مجهول (ياهو أعاد None)"
                except Exception:
                    val, src = None, "مجهول (استثناء ياهو)"
            else:
                src = "مجهول (yfinance غير متاح)"
        self.memo[sym], self.src[sym] = val, src
        return val

    def report(self):
        by = {}
        for s in self.src.values():
            by[s] = by.get(s, 0) + 1
        unk = sum(n for s, n in by.items() if s.startswith("مجهول"))
        return (f"الفلوت: وضع={self.mode} · رموز فريدة={len(self.memo)} · "
                f"نداءات ياهو={self.n_yahoo}/{self.budget} · مجهول={unk} · "
                "المصادر: " + (" · ".join(f"{k}={v}" for k, v in
                                          sorted(by.items(), key=lambda x: -x[1])) or "—")
                + ("\n   🔴 **نفدت ميزانية ياهو** ⇒ رموزٌ صارت «مجهولة» بلا فحص، "
                   "والإنتاج يُقصي المجهول ⇒ **أعداد المطابقين أرضية لا سقف**"
                   if self.exhausted else ""))


def run():
    import Super_stock as S
    C = S.CONFIG
    path = os.environ.get("BT_FROZEN_PATH", "").strip()
    if not path:
        print("⚠️ لا BT_FROZEN_PATH — هذي الأداة تعمل على **لقطة مجمّدة** حصرًا "
              "(دستور ⑦: لقطة إلزامية لكل ما يمسّ التقسيمات).")
        return 2
    arms = [a.strip().lower() for a in
            (os.environ.get("CLIFF_ARMS", "") or "").split(",") if a.strip()] or list(ARMS)
    bad = [a for a in arms if a not in ARM_SPEC]
    if bad:
        print(f"⛔ أذرع غير معروفة: {bad} — المتاح: {', '.join(ARMS)}. "
              "**لا سقوط صامت لذراعٍ افتراضية** (التجربة تُبطَل بذراعٍ خاطئة).")
        return 2
    # c0 إلزاميّ: التسجيل §③ «خط الأساس يُقاس ولا يُفترَض»
    if "c0" not in arms:
        arms = ["c0"] + arms
        print("ℹ️ أُضيفت c0 إلزاميًّا — التسجيل §③: «خط الأساس يُقاس ولا يُفترَض».")
    arms = [a for a in ARMS if a in arms]        # ترتيب ثابت

    bad_env = []

    def _int_env(name, default):
        """قراءة عددٍ من البيئة — **المشوّه يُعلَن ويُوقِف** لا يُبتلع بقيمةٍ افتراضية
        (قيمةٌ صامتة هنا تعني قياسًا بعيّنةٍ غير التي طُلبت)."""
        raw = (os.environ.get(name) or "").strip()
        if not raw:
            return default
        try:
            return int(raw)
        except ValueError:
            bad_env.append(f"{name}={raw!r}")
            return default

    n_days_req = _int_env("CLIFF_DAYS", 0)
    warmup = _int_env("CLIFF_WARMUP", 20)
    equiv_days = _int_env("CLIFF_EQUIV_DAYS", 5)
    fbudget = _int_env("CLIFF_FLOAT_BUDGET", 1500)
    cap_override = _int_env("CLIFF_PROBE_CAP", None)
    fmode = (os.environ.get("CLIFF_FLOAT_MODE") or "yahoo").strip().lower()
    if fmode not in ("cache", "yahoo"):
        print(f"⛔ CLIFF_FLOAT_MODE غير معروف: {fmode!r} (cache|yahoo)")
        return 2
    if bad_env:
        print(f"⛔ متغيّرات بيئة غير رقمية: {', '.join(bad_env)} — "
              "لا تُبتلع بقيمةٍ افتراضية (القياس يصير عن عيّنةٍ غير المطلوبة).")
        return 2
    if cap_override is not None and cap_override < 1:
        print("⛔ CLIFF_PROBE_CAP يجب أن يكون ≥1")
        return 2
    if n_days_req < 0 or warmup < 0 or equiv_days < 0 or fbudget < 0:
        print("⛔ CLIFF_DAYS/CLIFF_WARMUP/CLIFF_EQUIV_DAYS/CLIFF_FLOAT_BUDGET ≥0")
        return 2

    hist, splits_map, asof = S.load_frozen_dataset(path)
    if not hist:
        print(f"⚠️ تعذّر تحميل اللقطة {path}")
        return 2
    splits_map = splits_map or {}
    try:
        with open("company_cache.json", encoding="utf-8") as fh:
            cache = json.load(fh)
    except Exception:
        cache = {}

    prod_pct = float(C["SPLIT_CLIFF_PCT"])       # 🔒 القيمة الإنتاجية **قبل** أي ضبط
    print("⛰️ T-CLIFF — كلفة أذرع مُرشّح الكليف على السوق الكامل "
          "(قياس فقط · صفر مسّ إنتاج)")
    print(f"لقطة: {path} · as-of {asof} · {len(hist)} رمز · "
          f"{sum(1 for v in splits_map.values() if v is not None and len(v))} منها بتقسيمات")
    print("العقد: cliff_prereg.md (مدفوع قبل أي رقم) · الحكم من `scan_split_hunter` نفسها.")
    print(f"العتبات الإنتاجية (تُقرأ · وتُعاد بعد كل ذراع): كليف={prod_pct:g}% · "
          f"سعر [{C['SPLIT_RADAR_PRICE_MIN']:g}, {C['SPLIT_RADAR_PRICE_MAX']:g}] · "
          f"نافذة {C['SPLIT_LOOKBACK_DAYS']}ي · نطاق [×{C['SPLIT_RADAR_BAND_LOW']:g}, ×1.25] "
          f"· صعود ≤{C['SPLIT_ROSE_MAX_PCT']:g}% · فلوت <{C['SPLIT_RADAR_FLOAT_MAX']:,} · "
          f"سقف probe={C['SPLIT_RADAR_PROBE_CAP']}")
    print("الأذرع المشمولة:")
    for a in arms:
        print(f"   • {arm_label(a, prod_pct)}\n     ↳ ميكانيكا: {ARM_SPEC[a]['mech']}")
    print("ℹ️ `fetch_borrow`/`fetch_offering` معطَّلان (صفر شبكة · سياقٌ لا يدخل الحكم · "
          "قناة SEC حدٌّ مُعلَن §⑥-3).")

    # ── تقويم الجلسات + تجهيز المصفوفات (مرّة واحدة) ───────────────────────────
    syms = sorted(hist.keys())
    ords, closes, cliff_fast, cum_fast = {}, {}, {}, {}
    all_days = set()
    need_cum = any(arm_needs_prefilter(a) for a in arms)
    skipped = {"تالف": [], "أقصر من شمعتين": []}
    for s in syms:
        df = hist[s]
        try:
            ds = [S.pd.Timestamp(t).date() for t in df.index]
            c = [float(x) for x in df["Close"].values]
        except Exception:
            skipped["تالف"].append(s)
            continue
        if len(c) < 2:
            skipped["أقصر من شمعتين"].append(s)
            continue
        ords[s] = [d.toordinal() for d in ds]
        closes[s] = c
        all_days.update(ds)
        cliff_fast[s] = sliding_min(daily_return_series(c),
                                    int(C["SPLIT_LOOKBACK_DAYS"]))
        if need_cum:
            cum_fast[s] = sliding_min(cum_drop_series(c), int(C["SPLIT_LOOKBACK_DAYS"]))
    n_skip = sum(len(v) for v in skipped.values())
    print(f"🧮 جُهِّز {len(ords)} رمزًا من {len(syms)}"
          + (" · **مُستبعَدون مُعلَنون** (لا إسقاط صامت): "
             + " · ".join(f"{k}={len(v)}" for k, v in skipped.items() if v)
             + (f" — أمثلة: {', '.join(sorted(sum(skipped.values(), []))[:8])}"
                if n_skip else "")
             if n_skip else " · صفر مُستبعَد"))
    days = sorted(all_days)
    if not days:
        print("⚠️ اللقطة بلا أيام صالحة.")
        return 2
    # 🔎 «القابلة للمشي» = من اليوم الذي يبلغ فيه **رمزٌ واحد على الأقل** حدَّ الشموع.
    # (‏الأيام الأولى من اللقطة لا يمشيها الإنتاج أصلًا — تُستبعَد **قبل** أخذ العيّنة
    # فلا تُهدَر منها حصص، ويُطبع العددان معًا بدل عددٍ واحدٍ يوهم.)
    min_bars = max(20, warmup)
    firsts = [o[min_bars - 1] for o in ords.values() if len(o) >= min_bars]
    raw_days = len(days)
    if firsts:
        first_ok = min(firsts)
        days = [d for d in days if d.toordinal() >= first_ok]
    if not days:
        print(f"⚠️ لا يومَ قابلًا للمشي (لا رمز يبلغ {min_bars} شمعة).")
        return 2
    print(f"🔍 أيام اللقطة: {raw_days} · **القابلة للمشي** (‏≥{min_bars} شمعة لرمزٍ "
          f"واحد على الأقل): {len(days)}")
    total_days = len(days)
    if n_days_req and n_days_req < total_days:
        step = total_days / float(n_days_req)
        idxs = sorted({min(total_days - 1, int(round(i * step))) for i in range(n_days_req)})
        if idxs[-1] != total_days - 1:
            idxs.append(total_days - 1)          # آخر يومٍ دائمًا داخل العيّنة
        days = [days[i] for i in idxs]
        print(f"🔍 **تخفيف مُعلَن**: قِيس على {len(days)} يومًا من {total_days} "
              f"قابلًا للمشي (عيّنة منتظمة تشمل آخر يوم) — لا يُخفى ولا يُقرأ «كل الأيام».")
    else:
        print(f"🔍 قِيس على **كل** الأيام القابلة للمشي: {len(days)} يومًا "
              f"({days[0]} → {days[-1]}).")
    print(f"🔍 حدّ الإحماء: يُتخطّى الرمزُ في اليوم إن كان عنده أقلّ من {min_bars} شمعة "
          f"(حدّ الإنتاج نفسه = 20؛ ما فوقه تشديدٌ مُعلَن).")
    print("⚠️ **حدّ بنيويّ مُعلَن**: نافذة الكليف = min(نافذة الحدث، عدد الشموع−1) ⇒ "
          "الأيام الأولى نافذتها أقصر فالالتقاط فيها أقلّ — **لكل الأذرع سواء** "
          "فالنِّسَب تبقى ذات معنى.")

    fsrc = FloatSource(S, fmode, fbudget, cache)
    counters = Counters().reset()

    def _splits_of(sym):
        """تقسيمات الرمز **مقصوصة عند يوم المشي** (`_splits_of.day` يُضبَط كل يوم)
        = ما كان الجالب الحيّ يراه ذلك اليوم. بلا القصّ يتسرّب تقسيمٌ **لاحق** إلى
        `freq` (‏`_split_frequency` بلا حدّ أعلى للتاريخ) — تسريبٌ عرضيّ لكنه تسريب.
        🔴 **الفخّ الموثّق:** `hasattr(x, "index")` **صحيحٌ للقوائم أيضًا**
        (`list.index` دالّة!) ⇒ الفحص على `iloc` وحدها (خاصّة بـpandas)، وللقائمة
        مسارٌ صريح بدل أن تسقط في `except` فتُرجَع **بلا قصّ** صامتةً."""
        sp = splits_map.get(sym)
        d = _splits_of.day
        if sp is None or d is None:
            return sp
        try:
            if hasattr(sp, "iloc") and hasattr(sp, "index"):
                keep = [i for i in range(len(sp))
                        if S.pd.Timestamp(sp.index[i]).date() <= d]
                return sp.iloc[keep] if keep else sp.iloc[0:0]
            return [(ds, r) for ds, r in (sp or []) if ds <= d]
        except Exception:
            return sp
    _splits_of.day = None

    fetchers = make_fetchers(_splits_of, fsrc, counters, S.group_pump_scar)

    # ── جمع النتائج ────────────────────────────────────────────────────────────
    per_arm = {a: {"matchers": [], "probe": [], "flt": [], "pump": [],
                   "pre_raw": [], "trunc": 0, "syms": {}, "mismatch": 0}
               for a in arms}
    rows_csv = []
    log_msgs = {}
    _orig_log = S.log
    S.log = lambda m, _b=log_msgs: _b.__setitem__(str(m), _b.get(str(m), 0) + 1)
    equiv = {"checked": 0, "mismatch": 0, "detail": []}
    eq_days = set()
    if equiv_days > 0 and days:
        k = min(equiv_days, len(days))
        eq_days = {days[min(len(days) - 1, int(round(i * (len(days) - 1) / max(1, k - 1)))) ]
                   for i in range(k)} if k > 1 else {days[-1]}
    t0 = dt.datetime.now()
    # سقف probe: سقف الإنتاج افتراضيًّا، أو تجاوزٌ **بحثيّ مُعلَن** عبر `cfg_override`
    # (يُستعاد في `finally`، ويُتحقَّق من استعادته في الخلاصة).
    prod_cap = int(C["SPLIT_RADAR_PROBE_CAP"])
    cap_ctx = (cfg_override(C, "SPLIT_RADAR_PROBE_CAP", cap_override)
               if cap_override is not None else None)
    if cap_ctx is not None:
        cap_ctx.__enter__()
        print(f"🔬 **تجاوزٌ بحثيّ مُعلَن**: سقف probe {prod_cap} → {cap_override} "
              "طوال القياس (يُستعاد بعده). سببه: بلا مُرشّح كليف يصير السقفُ نفسه هو "
              "المُرشّح المُلزِم ⇒ c4 تقيس «أعمق N هابطًا» لا «حدّ الالتقاط الأعلى».")
    try:
        for D in days:
            _splits_of.day = D
            do = D.toordinal()
            day_hist, day_close, day_k = {}, {}, {}
            for s in syms:
                o = ords.get(s)
                if not o:
                    continue
                # عدد الشموع ≤ D (بحثٌ ثنائيّ يدويّ — بلا اعتماد numpy)
                lo, hi = 0, len(o)
                while lo < hi:
                    mid = (lo + hi) // 2
                    if o[mid] <= do:
                        lo = mid + 1
                    else:
                        hi = mid
                k = lo
                if k < min_bars:
                    continue
                day_hist[s] = hist[s].iloc[:k]
                day_close[s] = closes[s]
                day_k[s] = k
            if not day_hist:
                continue
            for a in arms:
                # (أ) الحساب الخارجيّ **للإبلاغ والمقارنة فقط** (لا يحكم على سهم)
                pre_raw, pf = 0, set()
                for s, k in day_k.items():
                    c = day_close[s]
                    price = c[k - 1]
                    if not (C["SPLIT_RADAR_PRICE_MIN"] <= price
                            <= C["SPLIT_RADAR_PRICE_MAX"]):
                        continue
                    spec = ARM_SPEC[a]
                    if spec["kind"] == "none":
                        ok = True
                    elif spec["kind"] == "cum":
                        ok = cum_fast[s][k - 1] <= -CLIFF_CUM_PCT / 100.0
                    else:
                        thr = -arm_cfg_value(a, prod_pct) / 100.0
                        m = cliff_fast[s][k - 1]
                        ok = (m != float("inf") and m <= thr)
                    if ok:
                        pre_raw += 1
                        pf.add(s)
                counters.reset()
                try:
                    rows = run_arm(S, a, day_hist, D, fetchers, prod_pct,
                                   prefilter=(pf if arm_needs_prefilter(a) else None))
                except Exception as e:
                    log_msgs[f"استثناء run_arm[{a}]: {type(e).__name__}: {e}"] = \
                        log_msgs.get(f"استثناء run_arm[{a}]: {type(e).__name__}: {e}", 0) + 1
                    rows = []
                got = [r["symbol"] for r in rows]
                cap = int(C["SPLIT_RADAR_PROBE_CAP"])
                expect = min(pre_raw, cap)
                st = per_arm[a]
                if counters.get("probe", 0) != expect:
                    st["mismatch"] += 1
                if pre_raw > cap:
                    st["trunc"] += 1
                st["matchers"].append(len(got))
                st["probe"].append(counters.get("probe", 0))
                st["flt"].append(counters.get("float", 0))
                st["pump"].append(counters.get("pump", 0))
                st["pre_raw"].append(pre_raw)
                for g in got:
                    st["syms"][g] = st["syms"].get(g, 0) + 1
                rows_csv.append({
                    "date": D.isoformat(), "arm": a, "universe_day": len(day_hist),
                    "pre_raw_external": pre_raw, "probe_measured": counters.get("probe", 0),
                    "probe_expected": expect, "probe_cap": cap,
                    "probe_cap_is_override": cap_override is not None,
                    "truncated": pre_raw > cap,
                    "float_calls": counters.get("float", 0),
                    "pump_calls": counters.get("pump", 0),
                    "matchers": len(got), "symbols": "|".join(sorted(got)),
                })
            # (ب) 🔒 قفل تكافؤ الميكانيكا على c0 (عتبةٌ إنتاجية مقابل تعطيل+ترشيح)
            if D in eq_days:
                pf0 = set()
                for s, k in day_k.items():
                    c = day_close[s]
                    price = c[k - 1]
                    if not (C["SPLIT_RADAR_PRICE_MIN"] <= price
                            <= C["SPLIT_RADAR_PRICE_MAX"]):
                        continue
                    m = cliff_fast[s][k - 1]
                    if m != float("inf") and m <= -prod_pct / 100.0:
                        pf0.add(s)
                counters.reset()
                a1 = {r["symbol"] for r in run_arm(S, "c0", day_hist, D, fetchers,
                                                   prod_pct)}
                counters.reset()
                with cfg_override(C, "SPLIT_CLIFF_PCT", CLIFF_DISABLED):
                    a2 = {r["symbol"] for r in S.scan_split_hunter(
                        {s: d for s, d in day_hist.items() if s in pf0},
                        today=D, **fetchers)}
                equiv["checked"] += 1
                if a1 != a2:
                    equiv["mismatch"] += 1
                    equiv["detail"].append((D, sorted(a1 ^ a2)))
    finally:
        S.log = _orig_log
        if cap_ctx is not None:
            cap_ctx.__exit__(None, None, None)
    dur = (dt.datetime.now() - t0).total_seconds()
    eff_cap = cap_override if cap_override is not None else prod_cap

    # ── الطباعة ────────────────────────────────────────────────────────────────
    print(f"\n⏱️ زمن المسح: {dur:.1f}ث · {fsrc.report()}")
    print("\n" + "═" * 110)
    print("📊 الكلفة لكل ذراع (المقياس الثاني الإلزاميّ — `cliff_prereg.md` §③-2)")
    base = _stats(per_arm[arms[0]]["matchers"]) if arms else {}
    base_m = _stats(per_arm["c0"]["matchers"]) if "c0" in per_arm else base
    base_p = _stats(per_arm["c0"]["probe"]) if "c0" in per_arm else base
    print(f"{'ذراع':<5} {'أيام':>5} {'مطابق/يوم: متوسط':>18} {'وسيط':>6} {'أقصى':>5} "
          f"{'مجموع':>7} {'×C0':>8} | {'probe: متوسط':>13} {'وسيط':>6} {'أقصى':>5} "
          f"{'×C0':>8} {'قُصّ':>5}")
    for a in arms:
        st = per_arm[a]
        m, p = _stats(st["matchers"]), _stats(st["probe"])
        print(f"{a:<5} {len(st['matchers']):>5} {_fmt(m['mean']):>18} "
              f"{_fmt(m['median'], 1):>6} {(m['max'] if m['max'] is not None else '—'):>5} "
              f"{m['sum']:>7} {_ratio(m['mean'], base_m.get('mean')):>8} | "
              f"{_fmt(p['mean'], 1):>13} {_fmt(p['median'], 1):>6} "
              f"{(p['max'] if p['max'] is not None else '—'):>5} "
              f"{_ratio(p['mean'], base_p.get('mean')):>8} {st['trunc']:>5}")
    print(f"«قُصّ» = عدد الأيام التي تجاوز فيها المُرشّح سقف probe ({eff_cap}"
          + (f" — **تجاوزٌ بحثيّ مُعلَن**، سقف الإنتاج {prod_cap}"
             if cap_override is not None else " = سقف الإنتاج")
          + ") ⇒ **أعداد ذلك اليوم أرضية لا سقف**.")
    _tr = [a for a in arms if per_arm[a]["trunc"]]
    if _tr:
        print(f"   ⚠️ الأذرع المقصوصة: {', '.join(_tr)} — لا تُقرأ أرقامها «حدًّا "
              "أعلى للالتقاط»؛ أعِد القياس بـCLIFF_PROBE_CAP أكبر لتعرف السقف الحقيقيّ.")

    print("\n🔒 قفل «الكلفة من الإنتاج»: مطابقة عدّاد probe المقروء من داخل "
          "`scan_split_hunter` مع `min(المحسوب خارجيًّا، السقف)`:")
    tot_mm = 0
    for a in arms:
        mm = per_arm[a]["mismatch"]
        tot_mm += mm
        print(f"   • {a}: اختلاف في {mm} من {len(per_arm[a]['probe'])} يومًا"
              + ("  ✅" if mm == 0 else "  ⚠️ **راجع** — حسابي لا يطابق الإنتاج"))
    print("\n🔒 قفل تكافؤ الميكانيكا (c0 بعتبة الإنتاج ⟷ c0 بتعطيلٍ + ترشيحٍ خارجيّ): "
          + (f"فُحِص {equiv['checked']} يومًا · اختلاف {equiv['mismatch']}"
             + ("  ✅ ⇒ ميكانيكا c3/c4 لا تغيّر الحكم" if equiv["mismatch"] == 0
                else "  ⚠️ **التعطيل غيّر الحكم — النتائج مشكوكة**")
             if equiv["checked"] else "⛔ **مُعطَّل** (CLIFF_EQUIV_DAYS=0) — مُعلَن."))
    for d, diff in equiv["detail"][:5]:
        print(f"      ⚠️ {d}: فرق {diff}")

    print("\n📛 المطابقون (رمز=عدد الأيام) — الستة والشاهدان مُبرَزان:")
    for a in arms:
        st = per_arm[a]["syms"]
        if not st:
            print(f"   • {a}: لا مطابق كامل في أي يوم من العيّنة.")
            continue
        items = sorted(st.items(), key=lambda x: (-x[1], x[0]))
        mark = lambda s: ("🎯" if s in SIX else ("🧪" if s in CONTROLS else ""))  # noqa: E731
        print(f"   • {a} ({len(items)} رمزًا فريدًا): "
              + " · ".join(f"{mark(s)}{s}={n}" for s, n in items[:40])
              + (" …" if len(items) > 40 else ""))
        hit6 = [s for s, _ in items if s in SIX]
        if hit6:
            print(f"     🎯 **من الستة**: {', '.join(hit6)}")

    if "c0" in per_arm and "c3" in per_arm:
        print("\n🔀 ملاحظة بنيويّة: c3 **ليست فوقيّة على c0** (هبوطُ يومٍ ‏−32% قد لا "
              "يبلغ ‏−40% تراكميًّا) — لذلك تُقرأ ذراعًا مستقلّة لا توسيعًا.")

    print("\n" + "═" * 110)
    print("⚖️ معيار التسجيل المسبق §④-(ب) — «كلفةٌ محتمَلة: معدّل المطابقين ≤3× معدّل C0»:")
    for a in arms:
        m = _stats(per_arm[a]["matchers"])
        b = base_m.get("mean")
        if b is None or m["mean"] is None:
            print(f"   • {a}: — (لا عيّنة)")
        elif b == 0:
            print(f"   • {a}: متوسط {m['mean']:.2f} · **الأساس صفر ⇒ النسبة غير معرّفة** "
                  "⇒ «لا حكم» على شرط (ب) (التسجيل §④: العيّنة غير الكافية ليست فشلًا).")
        else:
            r = m["mean"] / b
            print(f"   • {a}: ×{r:.2f} من C0 ⇒ "
                  + ("✅ داخل السقف" if r <= 3.0 else "❌ يتجاوز 3×"))
    print("⚠️ وهذا **شرط (ب) وحده**؛ الحكم لا يصدر إلا باستيفاء (أ) الاسترجاع معه — "
          "ويُقاس بأداة `hunter_six_check.py` بنفس الذراع (‏HUNTER_SIX_CLIFF).")
    print("🔴 **واستثناءٌ مسجَّل (‏`cliff2_prereg.md` §③):** أذرعُ **الترتيب/السقف** "
          "(`SPLIT_RADAR_ORDER` · `SPLIT_RADAR_PROBE_CAP`) **لا تُقاس بتلك الأداة** — "
          "مشيُها رمزًا واحدًا لا يُقيَّد بالسقف ولا يعمل فيه ترتيبٌ أصلًا ⇒ استرجاعُها "
          "يُؤخذ من **قائمة رموز المطابقين أعلاه** في هذي التشغيلة نفسِها.")

    if log_msgs:
        print("\n📝 رسائل الإنتاج أثناء المسح (فريدة + تكرارها — لا حذف صامت):")
        for m, n in sorted(log_msgs.items(), key=lambda x: -x[1])[:25]:
            print(f"   ×{n}  {m}")
        if len(log_msgs) > 25:
            print(f"   … و{len(log_msgs) - 25} رسالة أخرى")

    out = os.environ.get("CLIFF_CSV", "").strip()
    if out and rows_csv:
        try:
            with open(out, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(rows_csv[0].keys()))
                w.writeheader()
                w.writerows(rows_csv)
            print(f"\n💾 CSV: {out} ({len(rows_csv)} صف)")
        except Exception as e:
            print(f"\n⚠️ تعذّر كتابة CSV: {e}")

    # 🔒 لا تلوّث: العتبة الإنتاجية كما كانت
    still = float(C["SPLIT_CLIFF_PCT"])
    still_cap = int(C["SPLIT_RADAR_PROBE_CAP"])
    clean = (still == prod_pct and still_cap == prod_cap)
    print(f"\n🔒 CONFIG بعد كل الأذرع: SPLIT_CLIFF_PCT={still:g} · "
          f"SPLIT_RADAR_PROBE_CAP={still_cap} "
          + ("(= الإنتاجية ✅ لا تلوّث)" if clean else
             f"⚠️ **تلوّث!** المتوقّع {prod_pct:g}/{prod_cap}"))
    print("\nℹ️ حدود الصدق (‏`cliff_prereg.md` §⑥): اللقطة موسمٌ واحد لا حكم دهر · "
          "الفلوت ليس point-in-time · قناة الطرح (SEC) معطَّلة · الشمعة اليومية لا "
          "تشمل الافتر · **الكلفة «مطابقون/يوم» لا «إنذارات كاذبة»** (لا تُسمَّ دقّة). "
          "قياس/تشخيص — صفر مسّ حالة، صفر تنبيه.")
    return 0 if (tot_mm == 0 and equiv["mismatch"] == 0 and clean) else 1


# ═══════════════════════════════════════════════════════════════════════════════
# §3 — التحقّق بلا شبكة (اصطناعيّ) — إلزاميّ قبل أي تشغيل حقيقيّ
# ═══════════════════════════════════════════════════════════════════════════════
def _mk_df(pd, dates, closes, opens=None, highs=None, lows=None, vols=None):
    o = opens or closes
    h = highs or [max(a, b) * 1.001 for a, b in zip(o, closes)]
    lo = lows or [min(a, b) * 0.999 for a, b in zip(o, closes)]
    v = vols or [100_000.0] * len(closes)
    return pd.DataFrame({"Open": o, "High": h, "Low": lo, "Close": closes,
                         "Volume": v}, index=pd.to_datetime(dates))


def _sessions(pd, n, end):
    """n جلسة عمل تنتهي عند `end` (تقويم مبسّط: أيام الأسبوع فقط)."""
    out, d = [], end
    while len(out) < n:
        if d.weekday() < 5:
            out.append(d)
        d -= dt.timedelta(days=1)
    return list(reversed(out))


def selftest():
    """تحقّق بلا شبكة (‏④ من المهمّة): سهمٌ بكليف حادّ + سهمٌ بهبوطٍ سلّميّ متدرّج
    (نمط EHGO) → تُشغَّل الأذرع الخمس **فعليًّا** على دالّة الإنتاج، ويُثبَت أن c0
    تُسقط المتدرّج وc3 تلتقطه. + أقفال: استعادة CONFIG (حتى عند الاستثناء) · تطابق
    المسار السريع مع المرجع · التعطيل التامّ · حراسة `prefilter`."""
    import Super_stock as S
    pd = S.pd
    C = S.CONFIG
    fails = []

    def chk(cond, msg):
        print(("   ✅ " if cond else "   ❌ ") + msg)
        if not cond:
            fails.append(msg)

    print("⛰️ T-CLIFF — تحقّق اصطناعيّ بلا شبكة")
    print("=" * 100)

    # ── ① الأقفال النقيّة ────────────────────────────────────────────────────
    print("\n① أقفال الدوال النقيّة")
    import random
    random.seed(11)
    ok_fast, worst = True, None
    for _ in range(30):
        n = random.randint(25, 200)
        c = [10.0]
        for _i in range(n - 1):
            c.append(max(0.05, c[-1] * (1.0 + random.uniform(-0.35, 0.30))))
        cf = sliding_min(daily_return_series(c), 120)
        cu = sliding_min(cum_drop_series(c), 120)
        for t in range(20, n):
            look = min(120, t)
            ref_d = day_cliff_metric(c[:t + 1], look)
            ref_c = cum_drop_metric(c[:t + 1], look)
            if ref_d is not None and abs(cf[t] - ref_d) > 1e-12:
                ok_fast, worst = False, ("يوميّ", t, cf[t], ref_d)
            if ref_c is not None and abs(cu[t] - ref_c) > 1e-12:
                ok_fast, worst = False, ("تراكميّ", t, cu[t], ref_c)
    chk(ok_fast, f"المسار السريع = المرجع في كل نقطة (30 سلسلة عشوائية) {worst or ''}")

    flat = [5.0] * 60
    chk(day_cliff_metric(flat, 50) == 0.0, "سهم مسطّح: أعمق عائد يوميّ = 0")
    chk(arm_gate("c0", flat, 50, 30.0)["ok"] is False, "c0 ترفض المسطّح")
    chk(arm_gate("c4", flat, 50, 30.0)["ok"] is True, "c4 تقبل المسطّح (تعطيل تامّ)")
    chk(-CLIFF_DISABLED / 100.0 > 1.0,
        f"سنتينل التعطيل يعطي حدًّا {-CLIFF_DISABLED/100.0:g} > 1 ⇒ يمرّ كل cliff∈[-1,∞)")
    # c3 ليست فوقيّة على c0: يومٌ ‏−32% ثم تعافٍ ⇒ يمرّ c0/c1/c2 ويسقط c3
    mid = [10.0] * 25 + [6.8] + [8.2] * 24
    chk(arm_gate("c0", mid, 40, 30.0)["ok"] is True, "c0 تلتقط يوم −32%")
    chk(arm_gate("c3", mid, 40, 30.0)["ok"] is False,
        "c3 **لا** تلتقطه (تراكميّ −32% > −40%) ⇒ c3 ليست فوقيّة على c0")

    # ── ② حراسة الميكانيكا ───────────────────────────────────────────────────
    print("\n② حراسة الميكانيكا (انزلاق ذراعٍ صامتًا) — على **المدخلين معًا**")
    for nm, fn in (("run_arm",
                    lambda a, pf: run_arm(S, a, {}, dt.date(2026, 1, 5), {}, 30.0,
                                          prefilter=pf)),
                   ("arm_context",
                    lambda a, pf: arm_context(S, a, {}, 30.0, prefilter=pf))):
        for label, a, pf in (("c3 بلا prefilter ⇒ لا تنزلق إلى c4 صامتًا", "c3", None),
                             ("c0 مع prefilter ⇒ لا يتلوّث خطّ الأساس", "c0", set()),
                             ("ذراع مجهولة ⇒ لا سقوط صامت لذراعٍ افتراضية", "cX", None)):
            try:
                fn(a, pf)
                chk(False, f"[{nm}] {label} — لم يُرفع استثناء!")
            except ValueError:
                chk(True, f"[{nm}] {label}")

    # ── ③ استعادة CONFIG (بما فيها عند الاستثناء) ────────────────────────────
    print("\n③ استعادة CONFIG (فخّ التلوّث)")
    before = C["SPLIT_CLIFF_PCT"]
    with cfg_override(C, "SPLIT_CLIFF_PCT", 7.0):
        inside = C["SPLIT_CLIFF_PCT"]
    chk(inside == 7.0 and C["SPLIT_CLIFF_PCT"] == before,
        f"ضبط ثم استعادة ({before:g} → 7 → {C['SPLIT_CLIFF_PCT']:g})")
    try:
        with cfg_override(C, "SPLIT_CLIFF_PCT", 9.0):
            raise RuntimeError("انفجار اصطناعيّ داخل الذراع")
    except RuntimeError:
        pass
    chk(C["SPLIT_CLIFF_PCT"] == before,
        "الاستعادة تعمل **حتى عند الاستثناء** (finally لا زخرفة)")
    _tmp = {}
    with cfg_override(_tmp, "K", 1):
        pass
    chk("K" not in _tmp, "مفتاحٌ لم يكن موجودًا لا يُخترَع بعد الاستعادة")

    # ── ④ نهاية-إلى-نهاية على دالّة الإنتاج ──────────────────────────────────
    # 🔴 **العيّنة مصمَّمة ليكون لكل ذراعٍ جوابٌ مختلف عن الأربع الأخرى** — وإلا لمرّت
    #    طفراتٌ حقيقية بلا كشف (نسخةٌ أولى من هذي العيّنة أعطت c1=c2 وc3=c4، فكانت
    #    طفرة «تجاهل prefilter» و«خلط 25/20» غير مكشوفتين. الفرق بين اختبارٍ يمرّ
    #    واختبارٍ يحرس هو هذا بالضبط).
    print("\n④ الأذرع الخمس على `scan_split_hunter` نفسها (اصطناعيّ · صفر شبكة)")
    end = dt.date(2026, 7, 30)
    N, POST = 160, 62
    ds = _sessions(pd, N, end)
    split_i = N - POST                    # التقسيم قبل 62 جلسة (داخل نافذة 120 يومًا)
    split_day = ds[split_i]
    BAND = (2.00 * C["SPLIT_RADAR_BAND_LOW"], 2.00 * 1.25)

    def _geo(a, b, n):
        """`n` خطوة هندسية من `a` إلى `b` (لا تشمل `a`)."""
        r = (b / a) ** (1.0 / n)
        out, cur = [], a
        for _ in range(n):
            cur *= r
            out.append(cur)
        return out

    def _jit(v, n):
        return [v + 0.02 * ((i % 5) - 2) for i in range(n)]

    def _pad(seq):
        """يكمل المسار إلى POST بالتذبذب حول 2.00 (داخل النطاق، ثابتٌ 3 جلسات)."""
        return (seq + _jit(2.00, POST - len(seq)))[:POST]

    # قمة ما بعد التقسيم = 4.00 للجميع ⇒ ÷2 = 2.00 · النطاق [1.40، 2.50]
    paths = {
        # كليف يومٍ واحد ‏−46% ⇒ يمرّ الأربعة (c0-c4)
        "SHARP":   _pad([4.00, 3.90, 3.80, 2.05]),
        # يومٌ واحد ‏−27% ثم ثباتٌ طويل يُخرج القمّة من نافذة 20 ⇒ c1/c2/c4 فقط
        "MID27":   _pad([4.00, 2.92] + [2.92] * 25 + _geo(2.92, 2.02, 31)),
        # يومٌ واحد ‏−22% بنفس البنية ⇒ c2/c4 فقط
        "MID22":   _pad([4.00, 3.12] + [3.12] * 25 + _geo(3.12, 2.02, 31)),
        # نمط EHGO: سلّميّ سريع (‏18 جلسة) بلا يومِ ‏−20% ⇒ c3/c4 فقط
        "GRAD":    _pad([4.00, 3.95, 3.90] + _geo(3.90, 2.05, 18)),
        # سلّميّ **بطيء** (‏40 جلسة) ⇒ لا يوميّ ولا تراكميّ ⇒ c4 وحدها
        "NOCLIFF": _pad([4.00, 3.95] + _geo(3.95, 2.00, 40)),
    }
    EXPECT = {"c0": ["SHARP"], "c1": ["MID27", "SHARP"],
              "c2": ["MID22", "MID27", "SHARP"], "c3": ["GRAD", "SHARP"],
              "c4": ["GRAD", "MID22", "MID27", "NOCLIFF", "SHARP"]}

    hist, splits = {}, {}
    sp = pd.Series([0.2], index=pd.to_datetime([split_day]))   # تقسيم عكسي 1:5
    for name, post in paths.items():
        cl = [3.0] * split_i + list(post)
        op = list(cl)
        op[split_i] = 3.95    # افتتاح يوم الحدث ⇒ الصعود للقمة 4.00 = +1.3% ≤20% ✅
        # `High` = `Close` بالضبط ⇒ قمة ما بعد التقسيم = 4.00 حرفيًّا (بلا فتيلٍ يزيحها)
        hist[name] = _mk_df(pd, ds, cl, opens=op, highs=list(cl))
        splits[name] = sp
    prod = float(C["SPLIT_CLIFF_PCT"])

    print(f"   بيانات: {N} جلسة · تقسيم عكسي {split_day} (قبل {POST} جلسة) · "
          f"قمة ما بعد التقسيم 4.00 ⇒ ÷2 = 2.00 · نطاق [{BAND[0]:.2f}، {BAND[1]:.2f}]")
    for s in paths:
        c = [float(x) for x in hist[s]["Close"].values]
        look = min(int(C["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
        print(f"   {s:<8s} سعر أخير {c[-1]:.2f} · أعمق يوم "
              f"{day_cliff_metric(c, look)*100:+6.1f}% · أعمق تراكميّ ≤{CLIFF_CUM_DAYS}ج "
              f"{cum_drop_metric(c, look)*100:+6.1f}%")

    cnt = Counters().reset()
    fx = make_fetchers(lambda s: splits.get(s), lambda s: 500_000, cnt,
                       S.group_pump_scar)
    got = {}
    logs = {}
    _ol = S.log
    S.log = lambda m, _b=logs: _b.__setitem__(str(m), _b.get(str(m), 0) + 1)
    try:
        for a in ARMS:
            pf = None
            if arm_needs_prefilter(a):
                pf = set()
                for s, df in hist.items():
                    c = [float(x) for x in df["Close"].values]
                    look = min(int(C["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
                    if arm_gate(a, c, look, prod)["ok"]:
                        pf.add(s)
            cnt.reset()
            rows = run_arm(S, a, hist, end, fx, prod, prefilter=pf)
            got[a] = sorted(r["symbol"] for r in rows)
            print(f"   {a}: probe={cnt['probe']} · float={cnt['float']} · "
                  f"pump={cnt['pump']} ⇒ مطابق كامل: {got[a] or '—'}")
            chk(C["SPLIT_CLIFF_PCT"] == prod,
                f"CONFIG مُستعادة بعد الذراع {a} ({C['SPLIT_CLIFF_PCT']:g})")
            # 🔒 المدخلان ميكانيكا واحدة: `arm_context` (تستعمله أداة المشي، نداؤها
            #    صريحٌ في موضعه) ⟷ `run_arm` (يستعمله مسح السوق). أي تفرّقٍ = ذراعان.
            cnt.reset()
            with arm_context(S, a, hist, prod, prefilter=pf) as _h:
                alt2 = sorted(r["symbol"] for r in
                              (S.scan_split_hunter(_h, today=end, **fx) or []))
            chk(alt2 == got[a],
                f"{a}: `arm_context` = `run_arm` ({alt2}) — مدخلان بميكانيكا واحدة")
    finally:
        S.log = _ol

    for a in ARMS:
        chk(got.get(a) == EXPECT[a],
            f"{a}: المطابقون = {EXPECT[a]} (المقروء {got.get(a)})")
    chk(len({tuple(EXPECT[a]) for a in ARMS}) == len(ARMS),
        "العيّنة تفرّق الأذرع الخمس كلها (خمسة أجوبةٍ مختلفة) — فأي خلطٍ يُكشَف")

    # 🔒 قفل تكافؤ الميكانيكا: c0 بالعتبة ⟷ c0 بتعطيلٍ + ترشيحٍ خارجيّ
    pf0 = set()
    for s, df in hist.items():
        c = [float(x) for x in df["Close"].values]
        look = min(int(C["SPLIT_LOOKBACK_DAYS"]), len(c) - 1)
        if arm_gate("c0", c, look, prod)["ok"]:
            pf0.add(s)
    _ol = S.log
    S.log = lambda m: None
    try:
        cnt.reset()
        with cfg_override(C, "SPLIT_CLIFF_PCT", CLIFF_DISABLED):
            alt = sorted(r["symbol"] for r in S.scan_split_hunter(
                {s: d for s, d in hist.items() if s in pf0}, today=end, **fx))
    finally:
        S.log = _ol
    chk(alt == got.get("c0"),
        f"تكافؤ الميكانيكا: c0 بالعتبة {got.get('c0')} = c0 بالتعطيل+الترشيح {alt}")

    # ── ⑤ درع أداة المقسّم (⓿-أ) ─────────────────────────────────────────────
    # 🔒 **تمييزٌ مقصود ومُعلَن**: الثمانية أدناه على **مسار حكم T-CLIFF** (تناديها
    # أدواتي مباشرةً أو تناديها `scan_split_hunter` داخلها) ⇒ تغيّرها يُبطل القياس
    # ⇒ **سقوطٌ صلب**. أمّا `build_split_hunter_alert` فهي **باني نصّ التنبيه** ولا
    # تُنادى في أيٍّ من أدواتي ولا من مسار الحكم ⇒ تغيّرها **يُبلَّغ ولا يُبتلَع**
    # لكنه لا يُسقط قياسًا لا يمرّ بها (وهي موضع حقنٍ مُعلَنٍ لمهامّ أخرى في الحزمة).
    print("\n⑤ درع أداة المقسّم — البصمات كما سُلّمت")
    import hashlib
    import inspect
    VERDICT_PATH = {
        "_split_setup_probe": "4a37c171615d79e1", "_post_split_high": "b63231ab887c4f9d",
        "_split_day_value": "3ac4102924950c71", "faisal_split_plan": "ed7e5bf7e22184e9",
        "_yahoo_float": "0d6301165a68fa38",
        # 🔴 **إقرارٌ بتغييرٍ متعمَّد لا إصلاحُ فشل (2026-08-06):** أُضيف إلى
        #    `scan_split_radar` **خطّافُ ترتيبٍ مطفأ** (`SPLIT_RADAR_ORDER`، افتراضُه
        #    `"cliff"` = السلوكُ السابق **حرفيًّا**) لتجربة `cliff2_prereg.md`.
        #    والقياسُ يبقى صالحًا لأن الافتراض بت-بت، **وهو مقفولٌ في السويّة**
        #    (‏`CONFIG["SPLIT_RADAR_ORDER"] == "cliff"` + استعادةٌ بعد الضبط).
        "scan_split_radar": "4c8a21f4838c37ba",
        "split_radar_ready": "7002dda81b304609", "scan_split_hunter": "e54959a04f43124e"}
    # 🔴 وإقرارٌ ثانٍ: `build_split_hunter_alert` تغيّرت بإضافة `faisal_rule_lines`
    #    (قواعدُ فيصل عرضًا على الكرت) — **خارج مسار الحكم** فلا تمسّ قياسًا.
    OFF_PATH = {"build_split_hunter_alert": "e6c49e84351ed888"}

    def _sha(n):
        return hashlib.sha256(inspect.getsource(getattr(S, n)).encode()).hexdigest()[:16]

    bads = [f"{n}: {_sha(n)} ≠ {h}" for n, h in VERDICT_PATH.items() if _sha(n) != h]
    chk(not bads, f"الثماني التي على مسار الحكم مطابقة {bads or ''}")
    for n, h in OFF_PATH.items():
        g = _sha(n)
        print(("   ✅ " if g == h else "   ⚠️ ")
              + f"{n} (خارج مسار الحكم — لا تُنادى في أدوات T-CLIFF): {g}"
              + ("" if g == h else f" ≠ {h} — **تغيّرت**: يجب أن تكون موضع حقنٍ "
                                   "مُعلَنًا لمهمّةٍ أخرى · تُبلَّغ ولا تُسقط القياس"))

    print("\n" + "=" * 100)
    if fails:
        print(f"❌ سقط {len(fails)} فحصًا:")
        for f in fails:
            print("   • " + f)
        return 1
    print("✅ كل الفحوص نجحت — الأذرع الخمس تعمل على دالّة الإنتاج، وCONFIG نظيفة.")
    return 0


if __name__ == "__main__":
    if "--selftest" in sys.argv or os.environ.get("CLIFF_SELFTEST", "") == "1":
        raise SystemExit(selftest())
    raise SystemExit(run())
