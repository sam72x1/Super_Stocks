#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🎚️📉 `T-TRAIL` — **الوقفُ المتحرّك بدل سقفِ الربح** · مجتمعُ `E-BT` الحاكم.

**العقد:** `trail_prereg.md` (مدفوعٌ ومدموجٌ قبل هذا الملفّ ولم يُمَسّ). أمرُ
المالك «سجّل الوقف المتحرّك» ثمّ «ابن الاداة» (‏2026-09-17).

**السؤال (§①):** هل استبدالُ سقفِ الربح بوقفٍ يترقّى مع القمّة يُحسّن التوقّعَ
على **نفس الصفقات** — بنفس الدخول ونفس الوقف الابتدائيّ — **وهل الترقّي هو ما
يُحسّن أم مجرّدُ إلغاء السقف؟** (‏الشاهدُ الحاكم `C-CAP` هو الذي يفصلهما.)

🔒 **المجتمعُ عينُ مجتمع `T-EXITMGMT` لا مثيلٌ له:** لقطاتُ PIT الثلاث نفسُها ·
وفلترُ الطول `MIN_BARS + 60` المجمَّدُ على `T-TRANCHE` · والمِرساةُ والسلّمُ
والخطّةُ **مستورَدةٌ بالاسم** (`exitmgmt_arms.anchor_at`/`ladder` ·
`tranche_arms.plan_at`) · والتكميمُ خانةٌ واحدة — **و`V-T1` يُثبت أن `Y0` يُعيد
الأرقامَ المنشورة بت-بت أو يخرج 5 قبل أيّ رقم.**

🔒 **صفرُ منطقِ حسمٍ مكرَّر:** `exitmgmt_arms.resolve_exit`/`anchor_at`/`ladder`/
`boot_ci`/`pool_clusters` · `tranche_arms.plan_at`/`r_fixed` ·
`optrade_arms.selfcheck_readonly`/`no_config_assign` — **كلُّها بالاسم**.
⚠️ **و`ophold_arms.trail_trade` قاعدةٌ أخرى لا هذي:** مسافتُها **‏1R** ومرجعُها
**أعلى إغلاقِ دقيقة**، وهذي مسافتُها **`d%`** ومرجعُها **أعلى قمّة** ⇒ لا
تُوحَّدان (مقفولٌ سلوكيًّا بفِكستشرٍ يفرّقهما).

🔒 **ولا رقمَ يُكتَب بيدي:** مسافاتُ الترقّي من `CONFIG["SPLIT_SWEEP_*_PCT"]`
بالاسم · وأرقامُ `V-T1` **تُستخرَج نصًّا** من `exitmgmt_result.md`.

🔒 **قراءةٌ فقط:** صفرُ إرسالٍ · صفرُ كتابةِ ملفٍّ إطلاقًا (الصفوفُ تُطبَع
`⟦TSV⟧`) · صفرُ إسنادٍ إلى `CONFIG` · والإنتاجُ لا يستورد هذا الملفّ.

**رموزُ الخروج:** 0 صدر حكمٌ (الفرعان 1 و2) · 2 مدخلاتٌ ناقصة · **3 عطبُ أداة**
(‏`V-T4`/`V-T6`/تعذّرُ قراءةِ المنشور) · **5 حارسُ هُويّةٍ ساقط (`V-T1`)** ·
**9 «لا حكم» (الفرعُ 3)**.
"""
from __future__ import annotations

import os

os.environ.setdefault("SCREENER_MODE", "BACKTEST")   # قبل أيّ استيرادٍ للإنتاج

import json                                                      # noqa: E402
import re                                                        # noqa: E402
import sys                                                       # noqa: E402

from exitmgmt_arms import (anchor_at, boot_ci, ladder,            # noqa: E402
                           pool_clusters, resolve_exit)
from tranche_arms import plan_at, r_fixed                         # noqa: E402

EX_RESULT = "exitmgmt_result.md"     # `V-T1` — المنشورُ يُقرأ لا يُكتَب بيدي
RESULT_MD = "trail_result.md"
FLOOR_PAIR = 150                     # §⑤ `TR4`
MATERIAL = 0.05                      # §⑤ `TR3` — وسمٌ `engineering`
LEN_PAD = 60                         # 🧊 فلترُ الطول المجمَّدُ على `T-TRANCHE`
RET_ND = 1                           # 🧊 التكميمُ المجمَّد (خانةٌ واحدة)

# §④ — قائمةٌ **مُغلَقة**: (الاسم · السقفُ قائم؟ · مفتاحُ مسافةِ الترقّي)
ARMS = (("Y0",    True,  None),
        ("Y1",    False, "MID"),
        ("C-CAP", False, None),
        ("Y4",    True,  "MID"),
        ("Y1@7",  False, "MIN"),
        ("Y1@13", False, "MAX"))
BASE, GOV, CTRL = "Y0", "Y1", "C-CAP"
DESC = ("Y4", "Y1@7", "Y1@13")       # §④ — وصفيّةٌ لا تحكم

RC_OK, RC_INPUT, RC_TOOL, RC_POP, RC_NOVERDICT = 0, 2, 3, 5, 9

# 🔒🔴 **الإغلاقُ المُنفَّذ (شرطُ العقد §⑤ المكتوبُ قبل النتيجة):** سقط `TR2`
#    (‏`Y1 − C-CAP` موجبٌ في الثلاث وفاصلُه يلمس الصفر) ⇒ **محورُ «إدارةُ
#    الخروج بعد الدخول» مُغلَق** — إغلاقًا يُنفَّذ لا يُكتَب.
AXIS_CLOSED = True
REOPEN_ENV = "TRAIL_REOPEN"
CLOSED_RC = 8            # مميَّزٌ عمدًا عن 0/2/3/5/**9 «لا حكم»**


def _closed_now() -> bool:
    """أمُغلَقٌ الآن؟ — المفتاحُ يُقرأ **وقت النداء** لا وقت الاستيراد."""
    return AXIS_CLOSED and not (os.environ.get(REOPEN_ENV) or "").strip()


def closure_notice() -> list:
    """نصُّ الإغلاق — **دالّةٌ نقيّة** ليُقفَل مضمونُها لا شكلُها."""
    return [
        "🔒🔴 **محورُ «إدارةُ الخروج بعد الدخول» مُغلَق** — بشرط العقد §⑤.",
        "",
        "⚖️ **السبب — بالأرقام لا بالرأي** (`trail_result.md` · التشغيلة "
        "‏35314901325 · ثلاثُ سنوات · 4,817 زوجًا):",
        "   • `TR1` `Y1−Y0` = ‏+0.0136 · **−0.0111** · +0.0315 ⇒ مجمَّع "
        "**‏+0.0114R [−0.0564, +0.0858]** 🔴 (سنةٌ سالبةٌ وفاصلٌ يلمس الصفر)",
        "   • `TR2` `Y1−C-CAP` = ‏+0.0301 · +0.1481 · +0.0538 ⇒ **موجبٌ في "
        "الثلاث** لكنّ المجمَّع ‏+0.0770R **[−0.0503, +0.1987]** 🔴",
        "   • `TR3` الماديّة ‏≥+0.05R: ‏+0.0114R 🔴 · و`TR4` الأرضيّة ✅ "
        "**لكنّها تعبر بالبناء** (الأزواجُ = كلُّ صفوف السنة) فلا تحمل معلومة.",
        "   • **والبنيةُ تفسّر الاتّساع:** الوقفُ المترقّي يتحرّك فعليًّا في "
        "**‏21-24%** من المُعبَّأة فقط ⇒ `Y1 ≡ C-CAP` بت-بت في الباقي.",
        "   • **وهي سادسةُ تجربةٍ تسقط في هذا المحور** (‏`T-EXIT` · "
        "`T-EXITMGMT` · `T-T1MOVE` · `T-MANAGE-25` · `T-OPHOLD-2`).",
        "",
        "🔓 **ولا يُعاد فتحُه إلّا بثلاثةٍ معًا (نصُّ §⑤):**",
        "   ① **مصدرٌ جديدٌ للدعوى** — وأرقامُ `E-OP` الوصفيّة **ليست مصدرًا** "
        "(من التجربة نفسِها ومُلوَّثةٌ بنصّ §⓪-أ) · والطريقُ الملموس **حصادٌ "
        "أماميٌّ غيرُ مُلوَّثٍ** على مراسٍ بعد 2026-09-15.",
        "   ② **تسجيلٌ مسبقٌ جديد** — والعقدُ الحاليُّ مدموجٌ لا يُعدَّل. ويلزمه "
        "**دقّةٌ تُخرج الفرقَ من نطاق `±0.08R`** و**ضبطٌ يعزل «الترقّي» عن "
        "«طول الأفق»**.",
        "   ③ **إذنُ المالك.**",
        "",
        f"⚙️ وللتشغيل بعد استيفائها: `{REOPEN_ENV}=1` — **إقرارٌ لا التفاف**: "
        "مَن يضبطه يُعلن أنه استوفى الثلاثة.",
    ]
DRY = os.environ.get("TRAIL_DRY", "").strip() == "1"
# 🔴 **عيبٌ مقيسٌ في قناة المُخرَج (2026-09-18):** جدولُ الصفوف ‏≈4,818 سطرًا
#    يُطبَع في **ذيل** سجلّ الـCI، وسجلُّ الجوب هو **القناةُ الوحيدةُ المقروءة**
#    (تنزيلُ السجلّ الكامل والـartifacts محجوبان ببوّابة الشبكة) ⇒ الحكمُ يصير
#    فوق أربعة آلاف سطرٍ **فلا يُقرأ**. فصار الجدولُ **مطفأً افتراضًا** والحكمُ
#    آخرَ ما يُطبَع · والقصُّ **يُعلَن بعدّاده** (قاعدةُ `faisal-gates §⑥`).
TSV_ON = os.environ.get("TRAIL_TSV", "").strip() == "1"


def _log(msg: str = "") -> None:
    print(msg, flush=True)


def _f(v, nd=4):
    return "—" if v is None else f"{v:+.{nd}f}"


# ═══════════ ⓪ المنشورُ يُستخرَج نصًّا — `V-T1` (صفرُ رقمٍ مكتوبٍ بيدي) ═══════
def _cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _num(cell: str):
    """رقمٌ من خليّةِ جدولٍ عربيّة — بعد تسوية السالبِ الرياضيّ وعلامةِ الاتّجاه."""
    t = cell.replace("−", "-").replace("‏", "").replace("‎", "")
    m = re.search(r"-?\d+(?:\.\d+)?", t)
    return None if m is None else float(m.group(0))


def read_published(path: str = EX_RESULT) -> dict:
    """`V-T1` — `{سنة: {r, fill, rows}}` من جدول `exitmgmt_result.md` المنشور.

    الصفوفُ الثلاثةُ المقروءة: `V1` أساسُ `T-TRANCHE` · `V3` التعبئة · «الصفوف».
    وتعذّرُ القراءة **عطبُ أداةٍ لا نتيجة** (خروج 3) — فلا يُقاس بلا مرجع."""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "why": f"تعذّر فتحُ {path}: {type(e).__name__}"}
    lines = [ln for ln in txt.splitlines() if ln.lstrip().startswith("|")]

    def _row(key):
        return next((ln for ln in lines if key in ln), None)
    hdr, rv1, rv3, rrw = (_row("البوّابة"), _row("أساسُ `T-TRANCHE`"),
                          _row("التعبئةُ متطابقة"), _row("| الصفوف"))
    if not all((hdr, rv1, rv3, rrw)):
        return {"ok": False, "why": "صفٌّ منشورٌ غيرُ موجود"}
    yrs = [c for c in _cells(hdr)[1:] if c.isdigit()]
    if len(yrs) != 3:
        return {"ok": False, "why": f"سنواتٌ غيرُ ثلاث: {yrs}"}
    out = {"ok": True, "years": yrs}
    for i, y in enumerate(yrs):
        r = _num(_cells(rv1)[1 + i])
        fl = _num(_cells(rv3)[1 + i])
        rw = _num(_cells(rrw)[1 + i])
        if r is None or fl is None or rw is None:
            return {"ok": False, "why": f"قيمةٌ ناقصةٌ لسنة {y}"}
        out[y] = {"r": r, "fill": int(fl), "rows": int(rw)}
    return out


def read_arm(path: str, arm: str) -> dict:
    """`(n, R)` لذراعٍ من جدولِ نتيجةٍ منشورة — **بلا فهرسِ عمودٍ مغروس**:
    في صفِّ الذراع، أوّلُ خليّةٍ **عددٌ صحيح** = عددُ الصفوف، وأوّلُ خليّةٍ
    **كسريّةٍ بعدها** = مستوى `R`. (تختلف أعمدةُ `optrade_result.md` عن
    `ophold2_result.md` فلا يُغرَس رقمُ عمودٍ يتعفّن.)"""
    try:
        txt = open(path, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return {"ok": False, "why": f"تعذّر فتحُ {path}: {type(e).__name__}"}
    for ln in txt.splitlines():
        if not ln.lstrip().startswith("|"):
            continue
        c = _cells(ln)
        if not c or f"`{arm}`" not in c[0]:
            continue
        n = r = None
        for cell in c[1:]:
            v = _num(cell)
            if v is None:
                continue
            if n is None and float(v).is_integer() and v >= 1:
                n = int(v)
            elif n is not None and not float(v).is_integer():
                r = v
                break
        if n is not None and r is not None:
            return {"ok": True, "n": n, "r": r}
    return {"ok": False, "why": f"صفُّ `{arm}` غيرُ موجودٍ أو بلا رقمين"}


def dmap(S) -> dict:
    """§③ — مسافاتُ الترقّي **من `CONFIG` بالاسم**: ‏7/10/13 (نقلُ إطارٍ مُعلَنٌ
    في §⑦-4 — نظامُ الرقم عندَ فيصل «عمقُ سحبِ سيولة» لا «مسافةُ وقف»)."""
    return {"MIN": float(S.CONFIG["SPLIT_SWEEP_MIN_PCT"]),
            "MID": float(S.CONFIG["SPLIT_SWEEP_MID_PCT"]),
            "MAX": float(S.CONFIG["SPLIT_SWEEP_MAX_PCT"])}


# ═══════════ ① المُصيِّرُ — سقفٌ اختياريٌّ ووقفٌ يترقّى (§③ بحرفه) ═══════════
def ratchet_exit(hi, lo, cl, op, entry, stop0, t1, filled, d=None, cap=True,
                 spread=0.0):
    """يُرجع `(outcome, ret_pct, info)`.

    **الترقّي:** `stop_t = max(stop_0, peak_t × (1 − d/100))` — **يشدّ ولا يُرخي
    أبدًا** وبلا عتبةِ تسليح. **والترتيبُ المحافظ:** الوقفُ يُفحَص أوّلًا ثمّ
    الهدف، **ثمّ** تُحدَّث القمّة ⇒ الوقفُ المترقّي **يسري من الشمعة التالية**
    (قاعدةُ `T-EXITMGMT §②` بحرفها، صفرُ اصطلاحٍ جديد).

    **وحارسُ `F-L1` يسري على القمّة كما يسري على الهدف:** شمعةُ التعبئة لا تحسم
    هدفًا **ولا تُغذّي القمّة** — ترتيبُ الشمعة مجهولٌ فلا يُعلَم هل سبقت
    قمّتُها تعبئتَنا (اصطلاحٌ متماثلٌ: لا شيءَ من شمعة التعبئة يحسم شيئًا).

    🔒 **وبلا ترقٍّ وبسقفٍ قائم (`d=None` و`cap=True`) يُعيد
    `exitmgmt_arms.resolve_exit` بلا إدارةٍ بت-بت** — و`V-T4` يُثبته على
    مدخلاتٍ عشوائيّةٍ ببذرةٍ ثابتة، فلا يصير على المجتمع مقياسان."""
    if filled is None or entry <= 0:
        return "no_fill", None, {}
    from_bar = filled + 1                            # `F-L1`
    s0 = float(stop0)
    peak, lvl = None, s0
    out, exit_last = "open", float(cl[-1])
    for k in range(filled, len(cl)):
        if lo[k] <= lvl:
            out, exit_last = "loss", min(lvl, float(op[k]))
            break
        if cap and k >= from_bar and hi[k] >= float(t1):
            out, exit_last = "win", float(t1)
            break
        if d is not None and k >= from_bar:
            h = float(hi[k])
            peak = h if peak is None else max(peak, h)
            lvl = max(s0, peak * (1.0 - float(d) / 100.0))
    buy = float(entry) * (1.0 + spread / 2.0)
    ret = (exit_last * (1.0 - spread / 2.0) / buy - 1.0) * 100.0
    return out, ret, {"peak": (None if peak is None else round(peak, 6)),
                      "lvl": round(lvl, 6), "moved": lvl > s0}


def selfcheck_v4(n: int = 4000, seed: int = 20260917) -> int:
    """`V-T4` — **بوّابةُ المِقياس الواحد**: `ratchet_exit(d=None, cap=True)`
    تُعيد `resolve_exit` بلا إدارةٍ **بت-بت** (النتيجةُ والعائد) على مدخلاتٍ
    عشوائيّةٍ ببذرةٍ ثابتة. تفرّقٌ واحد ⇒ **عطبُ أداةٍ لا نتيجة**."""
    import random                                                # noqa: PLC0415
    rng = random.Random(seed)
    bad = 0
    for _ in range(n):
        m = rng.randint(2, 40)
        base = rng.uniform(0.4, 10.0)
        op = [round(base * rng.uniform(0.7, 1.3), 4) for _ in range(m)]
        cl = [round(o * rng.uniform(0.85, 1.15), 4) for o in op]
        hi = [round(max(a, b) * rng.uniform(1.0, 1.12), 4)
              for a, b in zip(op, cl)]
        lo = [round(min(a, b) * rng.uniform(0.88, 1.0), 4)
              for a, b in zip(op, cl)]
        entry = round(base * rng.uniform(0.9, 1.1), 4)
        stop = round(entry * rng.uniform(0.90, 0.995), 4)
        # 🔴 **حدُّ «قاعٌ يساوي الوقفَ بالضبط» مصنوعٌ عمدًا في نصف
        #    الحالات** — وإلّا صار الفرقُ بين `<=` و`<` غيرَ قابلِ الوصول
        #    (نفسُ الطفرة الناجية 2026-09-17). والاصطلاحُ هنا **غيرُ
        #    صارم** (`lo[k] <= stop`) كـ`resolve_exit` بحرفه.
        if rng.random() < 0.5:
            _cand = [v for v in lo if v < entry]
            if _cand:
                stop = _cand[rng.randrange(len(_cand))]
        t1 = round(entry * rng.uniform(1.02, 1.60), 4)
        filled = rng.choice([None] + list(range(m)))
        spread = rng.choice([0.0, 0.0, 0.05])
        oa, ra, _ = resolve_exit(hi, lo, cl, op, entry, stop, t1, filled,
                                 spread=spread)
        ob, rb, _ = ratchet_exit(hi, lo, cl, op, entry, stop, t1, filled,
                                 d=None, cap=True, spread=spread)
        if oa != ob or (ra is None) != (rb is None):
            bad += 1
        elif ra is not None and ra != rb:
            bad += 1
    return bad


def guards_ok() -> tuple:
    """`V-T6` — قراءةٌ فقط وصفرُ إسنادٍ إلى `CONFIG`، **بحارسَي `T-OPTRADE`
    بالاسم** (الأشدّان عندنا: ما لا يُثبَت أنه قراءةٌ يُعَدّ كتابة)."""
    from optrade_arms import (no_config_assign,                  # noqa: PLC0415
                              selfcheck_readonly)
    try:
        src = open(__file__, encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّر قراءةُ المصدر: {type(e).__name__}"
    ro, na = selfcheck_readonly(src), no_config_assign(src)
    return (ro and na), f"قراءةٌ فقط={ro} · صفرُ إسناد={na}"


# ═══════════ ② الأذرعُ على الصفّ — نفسُ الصفقة ونفسُ الدخول والوقف ═══════════
def arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct, ds):
    """يحسم الأذرعَ الستّ على **نفس الشموع ونفس الدخول ونفس الوقف الابتدائيّ** —
    المتغيّرُ **سقفُ الربح وترقّي الوقف وحدَهما** (§④).

    منقولُ البنية من `exitmgmt_arms.arms_for` حرفيًّا (المِرساةُ والسلّمُ
    والخطّةُ والحرّاسُ والتكميم) فيبقى `Y0` مطابقًا للمنشور بت-بت."""
    try:
        import pandas as pd                                      # noqa: PLC0415
        pos = df.index.get_loc(pd.Timestamp(tr["date"]))
    except Exception:                                            # noqa: BLE001
        return None, "تاريخٌ غيرُ موجود"
    i = int(pos) + 1
    pl = plan_at(S, sym, df, i)                                  # بالاسم
    if pl is None:
        return None, "تعذّرت إعادةُ الخطّة"
    anchor = anchor_at(S, df.iloc[:i], pl)                       # بالاسم
    if anchor is None:
        return None, "بلا مِرساة"
    stop, t1 = pl["stop"], pl["t1"]
    fut = df.iloc[i:i + fwd]
    if not len(fut):
        return None, "نافذةٌ فارغة"
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    op = fut["Open"].values.astype(float)

    trs = ladder(anchor, n_tr, step_pct)                         # بالاسم
    entry = sum(trs) / len(trs)
    if entry - stop <= 0:
        return None, "مقامُ المخاطرة غيرُ موجب"
    if t1 <= entry:
        return None, "هدفٌ دون الدخول"
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
    row = {"symbol": sym, "date": tr["date"], "stop": round(stop, 4),
           "t1": round(t1, 4), "anchor": round(anchor, 6),
           "e": round(entry, 4), "tr0": trs,
           "k": round((t1 - entry) / (entry - stop), 6)}
    for name, cap, dk in ARMS:
        d = None if dk is None else ds[dk]
        o, rt, info = ratchet_exit(hi, lo, cl, op, entry, stop, t1, filled,
                                   d=d, cap=cap, spread=spread)
        row[f"o_{name}"] = o
        # 🧊 خانةٌ واحدة — **مُجمَّدةٌ على `T-TRANCHE`** وإلّا استحال `V-T1`
        #    (‏`exitmgmt_arms:238`). والتكميمُ **واحدٌ للأذرع الستّ** فالفرقُ
        #    المقترن على أرضيّةٍ واحدة. ⚠️ وثمنُه مُعلَن: 0.1 نقطةٍ مئويّة
        #    تقع متماسكةً على خسائر `Y0`/`C-CAP` (تتكدّس عند سعر الوقف)
        #    ومبعثرةً على المترقّي.
        row[f"ret_{name}"] = (round(rt, RET_ND) if rt is not None else None)
        row[f"mv_{name}"] = bool(info.get("moved"))
    return row, None


def r_row(r, name):
    """`R₀` لذراعٍ على صفّ — و`no_fill` = **صفرُ عائدٍ يدخل المقام** (اصطلاحُ
    `T-EXITMGMT` المنشور · §⑦-8) · والمقامُ `entry − stop_0` **واحدٌ للستّ**."""
    o = r.get(f"o_{name}")
    if o is None:
        return None
    if o == "no_fill":
        return 0.0
    return r_fixed(r.get(f"ret_{name}"), r["e"], r["e"], r["stop"])  # بالاسم


def pair_clusters(rows, a: str, b: str) -> dict:
    """عناقيدُ فرقِ `a − b` **مقترنًا** (نفسُ الصفقة) — العنقودُ **الرمز**."""
    g = {}
    for r in rows:
        va, vb = r_row(r, a), r_row(r, b)
        if va is None or vb is None:
            continue
        n, s = g.get(r["symbol"], (0, 0.0))
        g[r["symbol"]] = (n + 1, s + (va - vb))
    return g


def agg(rows, name: str) -> dict:
    """`no_fill` = صفرٌ **ويدخل المقام** ⇒ المقامُ واحدٌ للأذرع الستّ."""
    fx, n_fill, wins, losses, opens, moved = [], 0, 0, 0, 0, 0
    for r in rows:
        o = r.get(f"o_{name}")
        if o is None:
            continue
        if o == "no_fill":
            fx.append(0.0)
            continue
        n_fill += 1
        wins += (o == "win")
        losses += (o == "loss")
        opens += (o == "open")
        moved += bool(r.get(f"mv_{name}"))
        v = r_row(r, name)
        fx.append(v if v is not None else 0.0)
    n = len(fx)
    return {"n": n, "n_fill": n_fill, "win": wins, "loss": losses,
            "open": opens, "moved": moved,
            "fill_pct": (n_fill / n * 100.0) if n else 0.0,
            "win_pct": (wins / n_fill * 100.0) if n_fill else 0.0,
            "loss_pct": (losses / n_fill * 100.0) if n_fill else 0.0,
            "open_pct": (opens / n_fill * 100.0) if n_fill else 0.0,
            "mv_pct": (moved / n_fill * 100.0) if n_fill else 0.0,
            "r": (sum(fx) / n) if n else 0.0}


# ═══════════ ③ الحكمُ — دالّةٌ نقيّةٌ تطبّق §⑤ بحرفه ═══════════════════════════
def read_verdict(tr1: dict, tr2: dict, tr3: dict, tr4: dict) -> tuple:
    """يطبّق §⑤ **بحرفه** — والفروعُ الثلاثةُ كلٌّ في سطرها.

    `TR4` **أرضيّةٌ تمنع الفرعَ 1** ⇒ سقوطُها «لا حكم» (خروج 9) · **وسقوطُ سنةٍ
    واحدةٍ في `TR1`/`TR2` ليس «لا حكم» بل الفرعُ 2** (درسُ `T-PMGATE`
    و`T-RSI-RANK`) — لأن المعيارَين معرَّفان «موجبٌ في السنوات الثلاث»."""
    if not bool(tr4.get("pass")):
        return 3, ("لا حكم", "سقطت الأرضيّةُ `TR4` ⇒ يُنشَر العددُ المقيس "
                             "ولا تُرفَع العيّنةُ ولا يُشحَن")
    if bool(tr1.get("pass")) and bool(tr2.get("pass")) and bool(tr3.get("pass")):
        return 1, ("تُوصى", "المعاييرُ الأربعةُ عبرت ⇒ اقتراحٌ للمالك بلا شحن (§⑧)")
    return 2, ("لا تُوصى", "أرضيّةٌ قائمةٌ وسقط معيارٌ حاكم ⇒ لا شحنَ "
                           "ولا رفعَ عيّنة، ويُنشَر الرقم")


def crit(per_year: list, pooled, bar: float = 0.0) -> dict:
    """موجبٌ في **كلّ** سنةٍ ‏+ فاصلُ المجمَّع لا يلمس الصفر (و`bar` للماديّة)."""
    ok_y = bool(per_year) and all(d > 0 for _y, d, _n in per_year)
    off0 = bool(pooled) and (pooled["lo"] > 0 or pooled["hi"] < 0)
    mat = bool(pooled) and pooled["mean"] >= bar
    return {"per_year": per_year, "pooled": pooled, "years_ok": ok_y,
            "off_zero": off0, "material": mat,
            "pass": (ok_y and off0 and (mat if bar else True))}


# ═══════════ ④ القياس — سنةٌ على لقطتها ═══════════════════════════════════════
def _measure(S, year: str, frozen: str, ds: dict):
    """يقيس سنةً واحدةً على لقطتها ويُرجع `(rc, rows, issues, attempted)`.
    🔒 **مصدرٌ واحد** — ولا `R` ولا فاصلَ هنا إطلاقًا (فوضعُ الجدوى لا يمسّهما)."""
    hist, splits_map, asof = S.load_frozen_dataset(frozen)
    if not hist:
        _log("⛔ تعذّر تحميل اللقطة")
        return RC_INPUT, [], {}, 0
    # §⑧ — الوقفُ والدخولُ المشحونان **لا يُمَسّان** (عزلُ أثر الخروج شرطُ صلاحية)
    if not S.CONFIG.get("PIVOT_STOP_AT_LOW"):
        _log("⛔ `Y0` يشترط وقفَ القاع المشحون (`PIVOT_STOP_AT_LOW`) — مُطفأ")
        return RC_TOOL, [], {}, 0
    n_tr = max(1, int(S.CONFIG["ENTRY_TRANCHES"]))
    step_pct = float(S.CONFIG["ENTRY_STEP_PCT"])
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    spread = S.CONFIG.get("BT_SPREAD_PCT", 0.0) or 0.0
    if str(asof or "")[:4] != str(year):
        _log(f"⛔ اللقطة as-of {asof} لا تطابق سنةَ القياس {year} — "
             "مجتمعٌ مختلف، لا تُقاس")
        return RC_INPUT, [], {}, 0
    lo_d, hi_d = f"{year}-01-01", f"{year}-12-31"
    syms = sorted(hist)
    _log(f"📦 اللقطة as-of {asof} · رموز {len(syms)} · دفعات "
         f"{n_tr}×{step_pct}% · الترقّي d = {ds['MID']:.0f}% "
         f"(والحسّاسيّة {ds['MIN']:.0f}% و{ds['MAX']:.0f}% — من `CONFIG`)")
    rows, issues, missing = [], {}, []
    for k, sym in enumerate(syms):
        df = hist.get(sym)
        # 🧊 مجمَّدٌ على `T-TRANCHE` (‏`MIN_BARS + 60`) — وإلّا استحال `V-T1`
        if df is None or len(df) < int(S.CONFIG["MIN_BARS"]) + LEN_PAD:
            continue
        try:
            trs = S.backtest_symbol(sym, df, date_window=(lo_d, hi_d),
                                    splits=(splits_map or {}).get(sym))
        except Exception as e:                                   # noqa: BLE001
            issues[type(e).__name__] = issues.get(type(e).__name__, 0) + 1
            continue
        for tr in trs:
            row, why = arms_for(S, sym, df, tr, fwd, spread, n_tr, step_pct, ds)
            if row is None:
                issues[why] = issues.get(why, 0) + 1
                if len(missing) < 25:
                    missing.append(f"{sym}/{tr.get('date')}:{why}")
                continue
            rows.append(row)
        if (k + 1) % 500 == 0:
            _log(f"   … {k + 1}/{len(syms)} · صفوف {len(rows)}")
    if missing:
        _log("   🔍 عيّنةٌ من المفقود بتواريخه: " + " · ".join(missing))
    return RC_OK, rows, issues, len(rows) + sum(issues.values())


def year_table(rows, year: str) -> dict:
    """جدولُ السنة — وصفيٌّ يُطبَع، والحكمُ مجمَّعًا وحدَه."""
    st = {n: agg(rows, n) for n, _c, _d in ARMS}
    base = st[BASE]
    _log(f"\n🎚️ T-TRAIL · سنة {year} · صفوف {len(rows)}")
    _log("   الذراع │ تعبئة% │ هدف% │ وقف% │ معلّق% │ ترقّى% │    R₀    │ عن Y0")
    for n, _c, _d in ARMS:
        a = st[n]
        d = "" if n == BASE else f"{a['r'] - base['r']:+.4f}"
        _log(f"   {n:>6} │ {a['fill_pct']:6.2f} │ {a['win_pct']:5.2f} │"
             f" {a['loss_pct']:5.2f} │ {a['open_pct']:6.2f} │"
             f" {a['mv_pct']:6.2f} │ {a['r']:+9.4f} │ {d}")
    return st


# ═══════════ ⑤ التجميع والتقرير ═══════════════════════════════════════════════
def _pool(S, spec: str) -> int:                                  # noqa: PLR0911
    """§⑤ **مجمَّعًا**: السنواتُ في تشغيلةٍ واحدة (ميزانيةٌ واحدةٌ بالبناء) ثمّ
    تُجمع عناقيدُ البوتستراب **بالرمز عبر السنوات** (`pool_clusters` بالاسم)."""
    gok, gwhy = guards_ok()
    if not gok:
        _log(f"⛔ `V-T6` حارسُ «قراءةٌ فقط / صفرُ إسناد» ساقط ({gwhy}) — خروج 3")
        return RC_TOOL
    _log(f"✅ `V-T6` {gwhy}")
    bad = selfcheck_v4()
    if bad:
        _log(f"⛔ `V-T4` المُصيِّرُ لا يُعيد `resolve_exit` بت-بت ({bad} تفرّقًا)"
             " — عطبُ أداةٍ لا نتيجة — خروج 3")
        return RC_TOOL
    _log("✅ `V-T4` المُصيِّرُ بلا ترقٍّ وبسقفٍ قائم يُعيد `resolve_exit` بت-بت "
         "(صفرُ تفرّق)")
    pub = read_published()
    if not pub.get("ok"):
        _log(f"⛔ `V-T1` المنشورُ غيرُ مقروء: {pub.get('why')} — خروج 3")
        return RC_TOOL
    _log(f"📖 `V-T1` المنشورُ مُستخرَجٌ نصًّا من {EX_RESULT}: "
         + " · ".join(f"{y} {pub[y]['r']:+.4f}/{pub[y]['fill']}/{pub[y]['rows']}"
                      for y in pub["years"]))
    ds = dmap(S)
    parts = [p.strip() for p in spec.split(",") if p.strip() and ":" in p]
    if not parts:
        _log("⛔ مواصفةُ اللقطات فارغة — خروج 2")
        return RC_INPUT
    if not DRY and len(parts) < 3:
        _log("⛔ التجميعُ يشترط ثلاث سنوات — خروج 2")
        return RC_INPUT
    tot, per = [], {}
    for part in parts:
        year, path = (x.strip() for x in part.split(":", 1))
        if not os.path.exists(path):
            _log(f"⛔ لقطةُ {year} غيرُ موجودة: {path} — خروج 2")
            return RC_INPUT
        rc, rows, issues, attempted = _measure(S, year, path, ds)
        if rc:
            return rc
        cov = (len(rows) / attempted * 100.0) if attempted else 0.0
        n_fill = sum(1 for r in rows
                     if r.get(f"o_{BASE}") not in (None, "no_fill"))
        _log(f"🩺 {year}: صفوف {len(rows)} من {attempted} = {cov:.1f}% · "
             f"مُعبَّأة {n_fill}")
        if issues:
            _log("   ℹ️ أسبابُ عدم القياس: "
                 + " · ".join(f"{k}={v}" for k, v in sorted(issues.items())))
        per[year] = {"rows": rows, "n": len(rows), "fill": n_fill, "cov": cov}
        tot.extend(rows)
    if DRY:
        _log("\n🧪 **وضعُ الجدوى** — ثلاثةُ أعدادٍ فقط لكلّ سنة (الصفوف · "
             "المُعبَّأة · التغطية) · **صفرُ `R` وصفرُ فرقٍ وصفرُ فاصل**.")
        for y, v in per.items():
            _log(f"   {y}: {v['n']} · {v['fill']} · {v['cov']:.1f}%")
        _log("⚠️ ودرسُ `T-PMGATE`: **وضعُ الجدوى يُجيز ما يمرّ به وحدَه** فلا "
             "يُقرأ إذنًا للمسار كلِّه.")
        return RC_OK
    # ── `V-T1` — هُويّةُ `Y0` ضدّ المنشور · **قبل أيّ فرقٍ أو فاصل** ───────────
    for y in sorted(per):
        p = pub.get(y)
        if p is None:
            _log(f"⛔ `V-T1` سنةٌ بلا مرجعٍ منشور: {y} — خروج 5")
            return RC_POP
        got = round(agg(per[y]["rows"], BASE)["r"], 4)
        ok = (abs(got - p["r"]) <= 0.0001 and per[y]["n"] == p["rows"]
              and per[y]["fill"] == p["fill"])
        _log(f"   {'✅' if ok else '⛔'} `V-T1` {y}: R {got:+.4f} مقابل "
             f"{p['r']:+.4f} · صفوف {per[y]['n']}/{p['rows']} · تعبئة "
             f"{per[y]['fill']}/{p['fill']}")
        if not ok:
            _log("⛔ `V-T1` — المجتمعُ أو الأساسُ يخالف المنشور ⇒ لا يُفسَّر "
                 "رقم — خروج 5")
            return RC_POP
    for y in sorted(per):
        year_table(per[y]["rows"], y)
    return report(per, tot, pub, ds)


def pair_year(per: dict, a: str, b: str) -> list:
    out = []
    for y in sorted(per):
        g = pair_clusters(per[y]["rows"], a, b)
        n = sum(v[0] for v in g.values())
        out.append([y, (sum(v[1] for v in g.values()) / n) if n else 0.0, n])
    return out


def pair_pool(per: dict, a: str, b: str):
    return boot_ci(pool_clusters([pair_clusters(per[y]["rows"], a, b)
                                  for y in sorted(per)]))        # بالاسم


def _ci(ci) -> str:
    if not ci:
        return "—"
    return (f"{ci['mean']:+.4f}R [{ci['lo']:+.4f}, {ci['hi']:+.4f}] · "
            f"أزواج {ci['n']} · رموز {ci['k']}")


def tsv_block(rows) -> list:
    """صفوفُ المُخرَج **تُطبَع ولا تُكتَب** (الأداةُ لا تفتح ملفًّا للكتابة)."""
    cols = (["date", "sym", "e", "stop", "t1", "k"]
            + [f"{p}_{n}" for n, _c, _d in ARMS for p in ("o", "R", "mv")])
    out = ["⟦TSV⟧" + "\t".join(cols)]
    for r in rows:
        cells = [r["date"], r["symbol"], f"{r['e']:.4f}", f"{r['stop']:.4f}",
                 f"{r['t1']:.4f}", f"{r['k']:.4f}"]
        for n, _c, _d in ARMS:
            v = r_row(r, n)
            cells += [str(r.get(f"o_{n}")),
                      ("—" if v is None else f"{v:+.4f}"),
                      ("1" if r.get(f"mv_{n}") else "0")]
        out.append("⟦TSV⟧" + "\t".join(cells))
    return out


def rows_out(tot: list, on: bool) -> list:
    """سطورُ المُخرَج للصفوف: الجدولُ كاملًا عند `on`، وإلّا **سطرُ قصٍّ بعدّاده**.

    🔒 والحكمُ (`JUDGE`) يبقى **آخرَ ما يُطبَع** فيُقرأ بذيلٍ قصير — وهو عينُ
    ما عجزتُ عنه في التشغيلة الأولى."""
    if on:
        return tsv_block(tot)
    return [f"⟦ROWS⟧ جدولُ الصفوف مطفأٌ: **{len(tot)} صفًّا** لم تُطبَع "
            "(‏`TRAIL_TSV=1` يطبعها) — قصٌّ مُعلَنٌ بعدّاده، والحكمُ أعلاه آخرَ "
            "سطرٍ ذي معنًى فيُقرأ بذيلٍ قصير."]


def report(per: dict, tot: list, pub: dict, ds: dict) -> int:     # noqa: PLR0915
    """الحكمُ المجمَّع — والمعاييرُ الأربعةُ كلٌّ برقمها (§⑤)."""
    py1, pl1 = pair_year(per, GOV, BASE), pair_pool(per, GOV, BASE)
    py2, pl2 = pair_year(per, GOV, CTRL), pair_pool(per, GOV, CTRL)
    tr1 = crit(py1, pl1)
    tr2 = crit(py2, pl2)
    tr3 = crit(py1, pl1, bar=MATERIAL)
    n_min = min([n for _y, _d, n in py1] + [n for _y, _d, n in py2])
    tr4 = {"pass": n_min >= FLOOR_PAIR, "n_min": n_min}
    _log("\n" + "═" * 66)
    _log("🎚️📉 الحكمُ المجمَّع — العقد `trail_prereg.md §⑤`")
    _log(f"   🥇 `TR1` ‏`{GOV} − {BASE}` (الترقّي بلا سقفٍ مقابل الإنتاج):")
    for y, d, n in py1:
        _log(f"      {y}: {d:+.6f}R · أزواج {n}")
    _log(f"      مجمَّعًا {_ci(pl1)}")
    _log(f"   🥇 `TR2` ‏`{GOV} − {CTRL}` (**الشاهدُ الحاكم** — الترقّي وحدَه):")
    for y, d, n in py2:
        _log(f"      {y}: {d:+.6f}R · أزواج {n}")
    _log(f"      مجمَّعًا {_ci(pl2)}")
    _log(f"   ① `TR1` موجبٌ في الثلاث: {'✅' if tr1['years_ok'] else '🔴'} · "
         f"والفاصلُ لا يلمس الصفر: {'✅' if tr1['off_zero'] else '🔴'} ⇒ "
         f"{'✅' if tr1['pass'] else '🔴'}")
    _log(f"   ② `TR2` موجبٌ في الثلاث: {'✅' if tr2['years_ok'] else '🔴'} · "
         f"والفاصلُ لا يلمس الصفر: {'✅' if tr2['off_zero'] else '🔴'} ⇒ "
         f"{'✅' if tr2['pass'] else '🔴'}")
    _log(f"   ③ `TR3` الماديّة (‏≥ {MATERIAL:+.2f}R · وسمٌ `engineering`): "
         f"{'✅' if tr3['material'] else '🔴'}")
    _log(f"   ④ `TR4` الأرضيّة (‏≥{FLOOR_PAIR} زوجًا لكلّ سنةٍ وذراع): "
         f"{'✅' if tr4['pass'] else '🔴'} (الأدنى {n_min})")
    if tr4["pass"]:
        _log("      ℹ️ **حدُّ صدقٍ يُقال:** التعبئةُ واحدةٌ للأذرع الستّ "
             "و`no_fill` يدخل المقام ⇒ الأزواجُ = كلُّ صفوف السنة ⇒ `TR4` "
             "**تعبر بالبناء على `E-BT`** وتبقى ملزِمةً على `E-OP` وحدَه.")
    br, (name, why) = read_verdict(tr1, tr2, tr3, tr4)
    _log(f"\n   ⇒ **الفرعُ {br} — «{name}»**: {why}")
    # ── الوصفيّاتُ الثلاثُ ملزِمةُ النشر (§④) ───────────────────────────────
    _log("\n═══ الوصفيّاتُ (لا تحكم · ملزِمةُ النشر) ═══")
    for n in DESC:
        _log(f"   {n} − {BASE}: {_ci(pair_pool(per, n, BASE))}")
    _log(f"   {CTRL} − {BASE} (كلفةُ إلغاءِ السقف وحدَه): "
         f"{_ci(pair_pool(per, CTRL, BASE))}")
    _log(f"   {GOV} − {'Y1@7'}: {_ci(pair_pool(per, GOV, 'Y1@7'))} · "
         f"{GOV} − Y1@13: {_ci(pair_pool(per, GOV, 'Y1@13'))}")
    # ── قراءةٌ ثانيةٌ مُعلَنة: المُعبَّأةُ وحدَها (اصطلاحُ المنشور هو الحاكم) ──
    fl = [r for r in tot if r.get(f"o_{BASE}") not in (None, "no_fill")]
    _log(f"\n═══ قراءةٌ ثانيةٌ **وصفيّة** — المُعبَّأةُ وحدَها ({len(fl)} صفًّا) "
         "═══\n   (والحاكمُ اصطلاحُ المنشور: `no_fill` صفرٌ يدخل المقام)")
    _log(f"   {GOV} − {BASE}: {_ci(boot_ci(pair_clusters(fl, GOV, BASE)))}")
    _log(f"   {GOV} − {CTRL}: {_ci(boot_ci(pair_clusters(fl, GOV, CTRL)))}")
    # ── التنبّؤاتُ العمياء (§⑥) — تُنشَر مؤكَّدةً أو مكذَّبة ──────────────────
    _log("\n═══ التنبّؤاتُ العمياء (§⑥) ═══")
    m1 = pl1["mean"] if pl1 else 0.0
    m2 = pl2["mean"] if pl2 else 0.0
    ccap = pair_pool(per, CTRL, BASE)
    y4 = pair_pool(per, "Y4", BASE)
    d7 = pair_pool(per, "Y1@7", BASE)
    for tag, txt, ok in (
            ("TP1", "`Y1−Y0` موجبٌ ودون +0.05R ⇒ `TR3` هو الساقط",
             (m1 > 0) and (m1 < MATERIAL)),
            ("TP2", "`C-CAP` سالبٌ بعنفٍ على `E-BT`",
             bool(ccap) and ccap["mean"] <= -0.30),
            ("TP3", "`Y1−C-CAP` موجبٌ فوق +0.30R", m2 > 0.30),
            ("TP4", "`Y4−Y0` سالبٌ وقريبٌ من الصفر",
             bool(y4) and -0.05 <= y4["mean"] < 0),
            ("TP5", "`Y1@7` أسوأُ من `Y1@10`",
             bool(d7) and bool(pl1) and d7["mean"] < m1)):
        _log(f"   {tag}: {'✅ مؤكَّد' if ok else '🔴 مكذَّب'} — {txt}")
    _log("   TP6: على `E-OP` وحدَه (‏`trail_op_arms.py`) — ويُقرأ بتلوّث §⓪-أ")
    # ── حدودُ الصدق (§⑦) — تُطبَع في كلّ تقرير ───────────────────────────────
    _log("\n═══ حدودُ الصدق (§⑦ — تُطبَع دائمًا) ═══")
    _log("   ① `E-OP` مُلوَّثٌ (§⓪-أ) ⇒ وصفيٌّ لا حاكم · وهذا التقريرُ `E-BT`.")
    _log("   ② السابقةُ فشلٌ متكرّر · و±0.025R تعني أن أثرًا صغيرًا قد يكون "
         "غيرَ قابلٍ للكشف أصلًا.")
    _log("   ③ `X3 − X0` = ‏−0.0207 سالبٌ في الثلاث ⇒ `Y4` تعميمٌ لا محورٌ جديد.")
    _log(f"   ④ **نقلُ إطارٍ مُعلَن:** d = {ds['MID']:.0f}% (والنطاق "
         f"{ds['MIN']:.0f}-{ds['MAX']:.0f}%) رقمُ فيصل **حرفيًّا** لكنّ نظامَه "
         "«عمقُ سحبِ سيولة» لا «مسافةُ وقف» ⇒ `faisal_adopted` **نقلُ إطار** ·"
         " ولا تُشحَن `d` عتبةً بهذي التجربة.")
    _log(f"   ⑤ `{MATERIAL:+.2f}R` ماديّةٌ **`engineering`** بلا سندٍ فيصليّ.")
    _log("   ⑥ **لمسٌ لا تنفيذ:** القمّةُ لمسةٌ تُرقّي الوقفَ ولو لم تُنفَّذ ⇒ "
         "**الرقمُ سقفُ أداءٍ للذراع لا أرضية.**")
    _log("   ⑦ ترتيبُ الشمعة مجهولٌ ⇒ الاصطلاحُ المحافظ بحرف `T-EXITMGMT` · "
         "وشمعةُ التعبئة لا تحسم هدفًا ولا تُغذّي القمّة.")
    _log("   ⑧ كلُّ ذراعٍ **خروجٌ واحد** ⇒ التكلفةُ تُلغى في الفرق المقترن "
         "(‏رِجلٌ واحدةٌ لكلّ ذراعٍ بالبناء).")
    _log("   ⑨⑩ انحيازُ البقاء قائمٌ في لقطات PIT · و‏64% من الانفجارات بلا "
         "مِرساةٍ أصلًا (منقولٌ من `T-OPTRADE §⑩` ويخصّ `E-OP`).")
    _log("═" * 66)
    judge = ({"branch": br, "name": name,
         "TR1": {"mean": (round(m1, 6) if pl1 else None),
                 "per_year": [[y, round(d, 6), n] for y, d, n in py1],
                 "pass": tr1["pass"]},
         "TR2": {"mean": (round(m2, 6) if pl2 else None),
                 "per_year": [[y, round(d, 6), n] for y, d, n in py2],
                 "pass": tr2["pass"]},
         "TR3": tr3["material"], "TR4": tr4,
         "d": ds, "rows": {y: per[y]["n"] for y in sorted(per)}})
    for ln in rows_out(tot, TSV_ON):
        _log(ln)
    # 🔒 `JUDGE` **آخرَ سطر** (وبعد الصفوف لو طُلبت) فيبلغه الذيلُ دائمًا
    _log("JUDGE " + json.dumps(judge, ensure_ascii=False))
    return RC_OK if br in (1, 2) else RC_NOVERDICT


def main() -> int:
    # 🔒 الحارسُ **قبل أيّ مدخل** — ولا لقطةَ تُفتَح ولا عمليةَ تُطلَق.
    if _closed_now():
        for _ln in closure_notice():
            _log(_ln)
        return CLOSED_RC
    _log("🎚️📉 T-TRAIL — الوقفُ المتحرّك بدل سقفِ الربح (العقد trail_prereg.md)")
    _log("🔒 قراءةٌ فقط · صفرُ مسٍّ بجذر · لا LOGIC_VERSION · والحاكمُ `E-BT`.")
    import Super_stock as S                                      # noqa: PLC0415
    spec = (os.environ.get("TRAIL_POOL") or "").strip()
    if not spec:
        _log("⛔ TRAIL_POOL مطلوب (‏`2023:path,2024:path,2025:path`) — خروج 2")
        return RC_INPUT
    return _pool(S, spec)


if __name__ == "__main__":
    sys.exit(main())
