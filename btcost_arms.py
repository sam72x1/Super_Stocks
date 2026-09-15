#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""🩸📡 `T-BTCOST` — تكلفةُ التنفيذ مقيسةً على **مجتمع المحرّك نفسِه** (العقد
`btcost_prereg.md` مدفوعٌ **ومدموجٌ في `main` قبل هذا الملفّ** وقبل أيّ رقم).

**السؤال (§①):** على صفقات محرّك الباكتيست نفسِها، ما **السبريدُ المقيس** `c`
الذي يُسعّره المحرّكُ نصفَين، وما **الانزلاقُ المتبقّي** `s` على ساق الخسارة
**بعد** خصمِ نصف السبريد؟ — **رقمٌ لهذا المجتمع، لا حكمٌ على زوجٍ ولا سياسة.**

🔑 **والمادّةُ تُستورَد ولا يُعاد بناؤها (‏§② · `V-B6`):** فهرسُ التعبئة بتعبير
`backtest_symbol` حرفيًّا · فهرسُ الخروج بـ`_arm_a_exit_bar` (‏**مقفولةٌ بتطابقٍ
خاصّيّ مع `_resolve_arm`** — بُنيت لـ`T-REPLAY10`) · ودقيقةُ اللمس والاقتباسُ
السائد وحارسُ التقسيم من `slip_nbbo_arms` بالاسم.

⚠️ **وقراءتان مُعلَنتان لغموضٍ في العقد — قبل أيّ رقم:**
1. **السيقانُ تُقاس على الصفقات المحسومة وحدَها** بنصّ §② («لكلّ صفقةٍ محسومة»)
   ⇒ ساقان لكلّ صفقة: التعبئةُ والخروج. وفرعُ `open` **منفَّذٌ في إعادة
   الاشتقاق** (فلو أعادت المشيةُ `open` على صفقةٍ مخزَّنةٍ محسومة عُدَّت
   `walk_mismatch`) — ولا يُقاس له ساق.
2. **أسبابُ الإسقاط تبقى الخمسةَ المسمّاةَ في §⑥ حصرًا** ومجموعُها يساوي الفرقَ
   بالضبط (‏`V-B7`)، **والحالاتُ الأدقُّ تُطبَع عدّاداتٍ فرعيّةً للتشخيص لا
   بوصفها بندًا سادسًا**: «لا شمعةَ يوم» و«لا جلسة» و«لا دقيقةَ لمس» و«لا صفقةَ
   عند المستوى» كلُّها **`no_minutes`** (الدقائقُ لا تُثبت اللمسة) · وفشلُ
   مطابقةِ الإغلاق اليوميّ مع فشلِ `raw_factor` كلاهما **`raw_scale_unverified`**.

🔒 قراءةٌ/بحثٌ فقط · بلا كرون · ولا `CONFIG` تُسنَد هنا (الأعلامُ عبر بيئة
الطفل حصرًا) · ولا تتحرّك `BT_SPREAD_PCT` الافتراضية · ولا إرسال.
"""
from __future__ import annotations

import ast
import hashlib
import json
import os
import random
import statistics
import subprocess
import sys
import time

# ══════════ ثوابتُ العقد — تُطبَع في كلّ تقرير ولا تتحرّك ══════════
GOV_YEARS = ("2023", "2024", "2025")      # §② الكونُ مطابقٌ لـ`T-FCOST`
# §⑥ `V-B1` — أعدادُ `T-FCOST` المنشورة (‏`fcost_result.md §⑥`)
FC_SIGNALS = {"2023": 1620, "2024": 1591, "2025": 1607}
FC_RESOLVED = {"2023": 1381, "2024": 1364, "2025": 1354}
AGREE_MIN = 0.99                          # §⑥ `V-B2`
COV_MIN = 0.60                            # §④ `BC1`
LEGS_YEAR, LEGS_TOTAL = 300, 1200         # §④ `BC2`
CI_MAX_PP = 0.50                          # §④ `BC3` (نقطةٌ مئويّة)
BOOT_N = 2000                             # إعاداتُ البوتستراب
BOOT_SEED = 20260913                      # بذرةٌ ثابتة ⇒ حتميّة
# 🕒 حارسُ التقادم: `prevailing` تُرجع آخرَ اقتباسٍ قائمٍ عند اللمسة، ونافذةُ
#    الرجوع خمسُ دقائق (‏`LOOKBACK_MS`) فما تجاوز دقيقتين يُوسَم ويُعَدّ.
#    عتبةٌ **هندسيّةُ قياسٍ** (لا بوّابةَ فرزٍ ولا رقمَ فيصل) — ولهذا يُطبَع
#    وسيطُ `c` **بلا الحارس** سطرًا وصفيًّا فلا يُسيّرَ الرقمَ في الخفاء.
STALE_MS = 120_000
OUT_LEGS = "btcost_legs.jsonl"
TRADES_TMPL = "btcost_trades_{}.json"
_IDX_CACHE = {}          # فهرسُ التواريخ لكلّ إطار (مسارٌ احتياطيّ)
LEGS_TMPL = "btcost_childlegs_{}.json"

# ⚙️ الأعلامُ المُلحِقة — **أعلامُ `T-FCOST` نفسُها** (‏§② «والأعلامُ نفسُها»)
FLAGS = {"BT_ENVVALS": "1", "BT_POTENTIAL": "1", "BT_SWEEP_ENTRY": "1"}

# 🔒 §⑥ `V-B3` — الجذورُ الاثنا عشر ‏+ محرّكُ الحسم ‏+ مُمكِّنُ هذي التجربة
ROOTS = ("rank_key", "select_top", "classify_tier", "analyze_ticker",
         "apply_short_gate", "apply_float_gate", "scan_market",
         "backtest_symbol", "scan_ignition", "scan_split_hunter",
         "entry_status", "build_interpretation",
         "_resolve_arm", "_arm_a_exit_bar")

# 🔢 رموزُ الخروج — **متمايزةٌ عمدًا** فلا يُقرأ حارسٌ خللًا في السجلّ.
#    ‏2 مدخلٌ · 3 فحصٌ ذاتيٌّ/جذور · 4 طفلٌ/لقطة · 5 `V-B1` · 6 `V-B2` ·
#    7 `V-B7`/`V-B9` · **8 محجوزٌ للإغلاق (‏§⑪ — ولم يقع)** · 9 «لا حكم»
RC_INPUT, RC_SELF, RC_CHILD = 2, 3, 4
RC_VB1, RC_VB2, RC_VGUARD, RC_NOVERDICT = 5, 6, 7, 9

# §⑥ `V-B7` — الأسبابُ الخمسةُ المسمّاة **حصرًا**
REASONS = ("no_minutes", "raw_scale_unverified", "no_quotes", "stale_quote",
           "walk_mismatch")


def _log(msg: str) -> None:
    print(msg, flush=True)


def _num(v, nd: int = 4) -> str:
    """عرضٌ فاشلٌ-آمن: الغائبُ «—» ولا ينهار التنسيق (‏الصنفُ ① في الأداة)."""
    return "—" if v is None else f"{v:.{nd}f}"


# ══════════════════ ① دوالٌّ نقيّةٌ مقفولة ══════════════════
def touch_index(sess: list, level: float, side: str):
    """فهرسُ **أوّلِ دقيقةٍ تلمس المستوى** داخل الجلسة.

    `down` ⟶ يُفوَّض إلى `slip_arms.trigger_index` **بالاسم** (‏`low ≤ level`) ·
    `up` ⟶ أوّلُ `high ≥ level`. 🔑 **والاتّجاهُ الصاعدُ غيرُ مبنيٍّ هناك أصلًا**
    (أدواتُ الوقف كلُّها هابطة) — فهذا إضافةٌ لا إعادةُ بناء."""
    import slip_arms as SL                                       # noqa: PLC0415
    if side == "down":
        return SL.trigger_index(sess, level)
    try:
        lv = float(level)
    except (TypeError, ValueError):
        return None
    for k, b in enumerate(sess or []):
        try:
            if float(b["h"]) >= lv:
                return k
        except (TypeError, ValueError, KeyError):
            continue
    return None


def touch_ms(trades: list, level_raw: float, side: str):
    """طابعُ **أوّلِ صفقةٍ تعبر المستوى الخامّ**.

    `down` ⟶ **يُفوَّض إلى `slip_nbbo_arms.trigger_ms` بالاسم** (‏فالمستوردُ على
    المسار الحيّ فعلًا لا في تعليق) · `up` ⟶ مرآتُه بنفس هامش `PX_EPS`."""
    import slip_nbbo_arms as NB                                  # noqa: PLC0415
    if side == "down":
        return NB.trigger_ms(trades, level_raw)
    try:
        lv = float(level_raw)
    except (TypeError, ValueError):
        return None
    for x in trades or []:
        try:
            p, t = float(x["p"]), int(x["t"])
        except (TypeError, ValueError, KeyError):
            continue
        if p >= lv * (1.0 - NB.PX_EPS):
            return t
    return None


def spread_pct(q) -> float:
    """`c` بالنقاط المئويّة: `(ask − bid) ÷ mid × 100` — خالٍ من المقياس فلا
    يحتاج تحويلَ الخامّ. غيابُ طرفٍ أو قيمةٌ غيرُ موجبة ⇒ `None`."""
    try:
        b, a = float((q or {}).get("bid")), float((q or {}).get("ask"))
    except (TypeError, ValueError):
        return None
    if b <= 0 or a <= 0 or a < b:
        return None
    mid = (a + b) / 2.0
    if mid <= 0:
        return None
    return (a - b) / mid * 100.0


def slip_of(exit_model: float, c_pct: float, p_real: float):
    """`s = 1 − P_real ÷ (exit_model × (1 − c/2))` — **بلا قصٍّ ولا حدّ**
    (‏`V-B8`): التنفيذُ الأفضلُ من النموذج يُعطي قيمةً **سالبة** تُعَدّ وتُنشَر،
    فقصُّها يصنع رقمًا متشائمًا كذبًا. يُرجَع بالنقاط المئويّة."""
    try:
        em, c, pr = float(exit_model), float(c_pct), float(p_real)
    except (TypeError, ValueError):
        return None
    model = em * (1.0 - (c / 100.0) / 2.0)
    if model <= 0:
        return None
    return (1.0 - pr / model) * 100.0


def pctile(xs_sorted: list, p: float):
    """رتبةٌ أقرب — حتميّةٌ بلا استيفاء (‏`V-B9`)."""
    if not xs_sorted:
        return None
    k = int(round((p / 100.0) * (len(xs_sorted) - 1)))
    return xs_sorted[max(0, min(len(xs_sorted) - 1, k))]


def boot_ci_median(groups: dict, n: int = BOOT_N, seed: int = BOOT_SEED):
    """فاصلُ بوتستراب ‏95% لوسيط `c` — **عنقوديٌّ بالرمز** (‏سيقانُ الرمز
    الواحد ليست مستقلّة) وببذرةٍ ثابتة ⇒ حتميّ."""
    keys = sorted(groups)
    if not keys:
        return None, None
    rnd = random.Random(seed)
    meds = []
    for _ in range(int(n)):
        pool = []
        for _ in range(len(keys)):
            pool.extend(groups[keys[rnd.randrange(len(keys))]])
        if pool:
            meds.append(statistics.median(pool))
    if not meds:
        return None, None
    meds.sort()
    return pctile(meds, 2.5), pctile(meds, 97.5)


# ══════════════════ ② الحكم — يطبّق §⑤ بحرفه ══════════════════
def read_verdict(crit: dict) -> tuple:
    """الفروعُ الثلاثةُ بنصّ §⑤ — **والأرضيةُ (`BC1`/`BC2`) تُفحَص أوّلًا**.

    `crit` = {"BC1": bool, "BC2": bool, "BC3": bool}."""
    lines = []
    if not (crit.get("BC1") and crit.get("BC2")):
        bad = [k for k in ("BC1", "BC2") if not crit.get(k)]
        lines.append("⚖️ الفرعُ 3 — «لا حكم»: سقطت "
                     + " و".join("`" + b + "`" for b in bad))
        lines.append("   ويُكتب في ملفّ النتيجة **تاريخُ إعادة قراءةٍ صريح** "
                     "لا وعدٌ بلا موعد.")
        return 3, lines
    if not crit.get("BC3"):
        lines.append("⚖️ الفرعُ 2 — `BC3` وحدَها ساقطة: يُنشَر الرقمُ **مدًى لا "
                     "نقطةً**")
        lines.append("   **ولا يُعَدّ «مصدرًا»** بنصّ `fcost_prereg.md §⑨` — "
                     "قياسٌ غيرُ دقيقٍ لا يُغني عن المستعار.")
        return 2, lines
    lines.append("⚖️ الفرعُ 1 — `C-MED` و`S-MED` **هما تكلفةُ هذا المجتمع**")
    lines.append("   ⇒ المصدرُ الذي سمّاه `fcost_prereg.md §⑨` صار موجودًا.")
    return 1, lines


# ══════════════════ ③ حرّاسُ الصلاحية ══════════════════
def selfcheck_readonly() -> bool:
    """`V-B4`-ب — قراءةٌ فقط بالـAST: صفرُ إرسالٍ وصفرُ كتابةِ حالة، ولا يُفتَح
    للكتابة إلّا مُخرَجُ هذي الأداة."""
    banned = {"send_telegram", "send_telegram_document", "git_save",
              "save_watchlist", "save_op_entry_state", "record_new_alerts",
              "save_near_watch", "save_hunter_watch"}
    allowed = {"OUT_LEGS", "_tp", "_lp"}
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        fn = getattr(n.func, "id", None) or getattr(n.func, "attr", None)
        if fn in banned:
            return False
        if fn == "open":
            mode = ""
            if len(n.args) > 1 and isinstance(n.args[1], ast.Constant):
                mode = str(n.args[1].value)
            for kw in n.keywords or []:
                if kw.arg == "mode" and isinstance(kw.value, ast.Constant):
                    mode = str(kw.value.value)
            if any(ch in mode for ch in ("w", "a", "x", "+")):
                if not (n.args and isinstance(n.args[0], ast.Name)
                        and n.args[0].id in allowed):
                    return False
    return True


def no_config_assign() -> bool:
    """`V-B5` — **أشدُّ من قائمةٍ بيضاء**: صفرُ إسنادٍ إلى `CONFIG` إطلاقًا.
    الأعلامُ تمرّ عبر **بيئة الطفل** فيقرؤها `_apply_backtest_overrides` في وضع
    `BACKTEST` حصرًا (‏وهو بعينه ما كان يفعله `T-RSI40` بضبطٍ في الذاكرة)."""
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
    except Exception:                                            # noqa: BLE001
        return False
    for n in ast.walk(tree):
        tgts = []
        if isinstance(n, ast.Assign):
            tgts = list(n.targets)
        elif isinstance(n, (ast.AugAssign, ast.AnnAssign)):
            tgts = [n.target]
        for t in tgts:
            if isinstance(t, ast.Subscript):
                base = t.value
                nm = getattr(base, "id", None) or getattr(base, "attr", None)
                if nm == "CONFIG":
                    return False
        if isinstance(n, ast.Call):
            f = n.func
            if (isinstance(f, ast.Attribute) and f.attr in ("update", "setdefault")
                    and (getattr(f.value, "id", None)
                         or getattr(f.value, "attr", None)) == "CONFIG"):
                return False
    return True


def reuse_by_name() -> tuple:
    """`V-B6` — المُمكِّناتُ الخمسُ **تُنادى فعلًا** في هذا الملفّ (‏AST): لا
    ذكرٌ في تعليقٍ ولا استيرادٌ خامل. (‏الصنفُ ② المدوَّن: قفلٌ نصّيٌّ يُرضيه شرح.)"""
    want = {"_arm_a_exit_bar", "trigger_ms", "trigger_index", "fetch_quotes",
            "prevailing", "raw_factor"}
    try:
        tree = ast.parse(open(__file__, encoding="utf-8").read())
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّرت القراءة: {type(e).__name__}"
    got = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Call):
            nm = getattr(n.func, "attr", None) or getattr(n.func, "id", None)
            if nm in want:
                got.add(nm)
    miss = sorted(want - got)
    return (not miss), ("كلُّها منادَاة" if not miss else "غيرُ منادَاة: "
                        + ", ".join(miss))


def roots_identical() -> tuple:
    """`V-B3` — بصمةُ AST للجذور ‏+ `_resolve_arm` ‏+ `_arm_a_exit_bar` مقابل
    `origin/main`، **و`slip_nbbo_arms.py` لا يُمَسّ بحرف**.

    ⚠️ **وتُقرأ على الرنر من `main` فالشجرةُ نظيفة** — ولا يُبنى عليها قفلُ سويّةٍ
    سلوكيّ (درسُ `RSK3`: حارسٌ يفترض شجرةً نظيفةً يُحمّر البوّابةَ على كلّ تعديل)."""
    try:
        p = subprocess.run(["git", "show", "origin/main:Super_stock.py"],
                           capture_output=True, text=True)
        base = p.stdout or ""
        cur = open("Super_stock.py", encoding="utf-8").read()
        q = subprocess.run(["git", "show", "origin/main:slip_nbbo_arms.py"],
                           capture_output=True, text=True)
        nb_base = q.stdout or ""
        nb_cur = open("slip_nbbo_arms.py", encoding="utf-8").read()
    except Exception as e:                                       # noqa: BLE001
        return False, f"تعذّرت القراءة: {type(e).__name__}"
    if not base or not nb_base:
        return False, "تعذّر جلبُ origin/main"
    if nb_base != nb_cur:
        return False, "`slip_nbbo_arms.py` مُعدَّل"

    def fp(src):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return {}
        return {n.name: hashlib.sha256(ast.dump(n).encode()).hexdigest()[:12]
                for n in ast.walk(tree)
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and n.name in ROOTS}

    a, b = fp(base), fp(cur)
    diff = [r for r in ROOTS if a.get(r) != b.get(r)]
    return (not diff), ("لا شيء" if not diff else "مختلفة: " + ", ".join(diff))


# ══════════════════ ④ الطفل — المشيُ واسترجاعُ اللحظتين ══════════════════
def child_env(frozen: str, extra=None) -> dict:
    """بيئةُ الطفل: وضعُ الباكتيست ‏+ الأعلامُ نفسُها ‏+ اللقطةُ المجمَّدة.

    🔒🔴 **وتُجرَّد مفاتيحُ تلغرام بنيويًّا:** الطفلُ ينادي `run_backtest` وفيها
    إرسالٌ ووثائقُ CSV **بلا حارس** ⇒ لا يُتَّكل على غيابِ سرٍّ في workflow واحد."""
    env = {**dict(os.environ), **FLAGS, "BT_FROZEN_PATH": frozen}
    env.update(extra or {})
    for k in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "TELEGRAM_BOT_TOKEN_2",
              "TG_BOT_TOKEN", "TG_CHAT_ID"):
        env.pop(k, None)
    env["SCREENER_MODE"] = "BACKTEST"
    return env


def derive_legs(df, t: dict, fwd: int):
    """يُعيد اشتقاقَ **فهرسِ التعبئة وشمعةِ الخروج** بتعبير المحرّك نفسِه.

    ‏`filled` = تعبيرُ `backtest_symbol` حرفيًّا · و`(outcome, k)` من
    `_arm_a_exit_bar` المستوردة. ويُرجَع `agree` = هل تطابق `outcome` المعادةُ
    المخزَّنةَ (‏`V-B2`) — والقيمُ المخزَّنةُ مقرَّبةٌ لخانتين فالتفرّقُ ممكنٌ
    **ويُعَدّ باسمه** لا يُخفى."""
    import pandas as pd                                          # noqa: PLC0415
    import Super_stock as S                                      # noqa: PLC0415
    if df is None or not len(df):
        return None
    want = str(t.get("date"))
    try:
        pos = int(df.index.get_loc(pd.Timestamp(want)))
    except Exception:                                            # noqa: BLE001
        # 🔑 المسارُ الاحتياطيُّ **لازمٌ لا زينة**: الفهرسُ اليوميُّ قد يكون
        #    واعيًا بالمنطقة (المستودعُ يُسقط المنطقةَ في مواضعَ عدّة) فيسقط
        #    `get_loc` بطابعٍ ساذج ⇒ **كلُّ صفٍّ يصير `walk_mismatch` وتسقط
        #    `V-B2` على المشية كلِّها**. والبحثُ بالتاريخ وحدَه محصَّنٌ منها،
        #    ومُكاشٌ بالفهرس نفسِه فلا يُعاد المسحُ لكلّ صفقة.
        _ck = (str(t.get("symbol")), len(df), str(df.index[0]),
               str(df.index[-1]))
        _mp = _IDX_CACHE.get(_ck)
        if _mp is None:
            _mp = _IDX_CACHE[_ck] = {str(ts.date()): k
                                     for k, ts in enumerate(df.index)}
        pos = _mp.get(want)
    if pos is None:
        return None
    i = int(pos) + 1
    fut = df.iloc[i:i + int(fwd)]
    if not len(fut):
        return None
    try:
        entry = float(t["entry"]); stop = float(t["stop"]); t1 = float(t["t1"])
    except (TypeError, ValueError, KeyError):
        return None
    hi = fut["High"].values.astype(float)
    lo = fut["Low"].values.astype(float)
    cl = fut["Close"].values.astype(float)
    filled = next((k for k in range(len(fut)) if lo[k] <= entry), None)
    out, k = S._arm_a_exit_bar(hi, lo, cl, entry, stop, t1, filled)
    if filled is None:
        return {"agree": False, "why": "no_fill"}
    day = lambda j: str(fut.index[j].date())                     # noqa: E731
    return {"agree": bool(out == t.get("outcome")), "why": out,
            "fill_day": day(filled), "dclose_fill": float(cl[filled]),
            "exit_day": day(k), "dclose_exit": float(cl[k]),
            "exit_kind": out}


def run_child(tag: str) -> int:
    """يُشغّل الباكتيست ثمّ يسترجع لحظتَي كلّ صفقةٍ محسومة — **بلا أيّ جلب**."""
    import Super_stock as S                                      # noqa: PLC0415
    fz = (os.environ.get("BT_FROZEN_PATH") or "").strip()
    hist, snap = {}, {"asof": None, "n": None}
    if fz:
        try:
            hist, _sp, asof = S.load_frozen_dataset(fz)
            snap = {"asof": (str(asof) if asof else None),
                    "n": (len(hist) if hist else 0)}
        except Exception as e:                                   # noqa: BLE001
            _log(f"⛔ لقطةٌ غيرُ مقروءة: {type(e).__name__}")
            return RC_CHILD
    _log(f"SNAP {tag} as-of={snap['asof']} n_symbols={snap['n']}")
    trades = S.run_backtest() or []
    _tp = TRADES_TMPL.format(tag)
    with open(_tp, "w", encoding="utf-8") as fh:
        json.dump(trades, fh, ensure_ascii=False, default=str)
    fwd = int(S.CONFIG["BACKTEST_FORWARD_DAYS"])
    legs, n_res, n_agree = [], 0, 0
    for t in trades:
        o, r = (t or {}).get("outcome"), (t or {}).get("ret_a")
        if o not in ("win", "loss") or r is None:
            continue
        n_res += 1
        d = derive_legs((hist or {}).get(t.get("symbol")), t, fwd)
        if not d or not d.get("agree"):
            legs.append({"sym": t.get("symbol"), "date": t.get("date"),
                         "agree": False, "why": (d or {}).get("why", "no_walk")})
            continue
        n_agree += 1
        legs.append({"sym": t.get("symbol"), "date": t.get("date"),
                     "agree": True, "outcome": o,
                     "entry": float(t["entry"]), "stop": float(t["stop"]),
                     "t1": float(t["t1"]),
                     "fill_day": d["fill_day"], "dclose_fill": d["dclose_fill"],
                     "exit_day": d["exit_day"], "dclose_exit": d["dclose_exit"],
                     "exit_kind": d["exit_kind"]})
    _lp = LEGS_TMPL.format(tag)
    with open(_lp, "w", encoding="utf-8") as fh:
        json.dump(legs, fh, ensure_ascii=False)
    meta = {"tag": tag, "snap": snap, "n_signals": len(trades),
            "n_resolved": n_res, "n_agree": n_agree, "path": _lp,
            # 🔒 برهانٌ لا زينة: قيمةُ السبريد النافذةُ داخل الطفل تُطبَع.
            "spread": float(S.CONFIG.get("BT_SPREAD_PCT") or 0.0)}
    print("BTCOST_CHILD:" + json.dumps(meta, ensure_ascii=False))
    return 0


def _run_child(tag: str, frozen: str, extra: dict) -> dict:
    env = child_env(frozen, extra)
    p = subprocess.run([sys.executable, os.path.abspath(__file__), "--child",
                        tag], capture_output=True, text=True, env=env)
    blob = (p.stdout or "") + "\n" + (p.stderr or "")
    for ln in blob.splitlines():
        if not ln.startswith("BTCOST_CHILD:"):
            _log(f"  [{tag}] {ln}")
    rows = [x for x in blob.splitlines() if x.startswith("BTCOST_CHILD:")]
    if p.returncode != 0 or not rows:
        return {}
    return json.loads(rows[-1].split("BTCOST_CHILD:", 1)[1])


# ══════════════════ ⑤ القياس — ساقًا ساقًا ══════════════════
def legs_of(rec: dict, year: str) -> list:
    """ساقا الصفقة المحسومة: **التعبئةُ** (هابطة عند `entry`) و**الخروجُ**
    (‏`loss` هابطٌ عند الوقف · `win` صاعدٌ عند الهدف)."""
    return [
        {"sym": rec["sym"], "year": year, "kind": "entry", "side": "down",
         "day": rec["fill_day"], "level": rec["entry"],
         "dclose": rec["dclose_fill"], "model": None},
        {"sym": rec["sym"], "year": year, "kind": rec["exit_kind"],
         "side": ("down" if rec["exit_kind"] == "loss" else "up"),
         "day": rec["exit_day"],
         "level": (rec["stop"] if rec["exit_kind"] == "loss" else rec["t1"]),
         "dclose": rec["dclose_exit"],
         "model": (rec["stop"] if rec["exit_kind"] == "loss" else None)},
    ]


def window_of(key: tuple) -> dict:
    """نافذةُ اللمسة: اقتباساتٌ بنافذة رجوعٍ ‏+ صفقاتُ الدقيقة — **بندائَي
    `fetch_quotes` و`fetch_trades` بالاسم** (‏§② الجدول · `V-B6`)."""
    import slip_nbbo_arms as NB                                  # noqa: PLC0415
    _sym, _day, t0 = key
    q, _qt = NB.fetch_quotes(_sym, t0 - NB.LOOKBACK_MS, t0 + 60_000)
    tr, _tt = NB.fetch_trades(_sym, t0, t0 + 60_000)
    return {"q": q, "t": tr}


def stage_bar(leg: dict, bars) -> tuple:
    """من شموع اليوم إلى **دقيقةِ اللمس** — أو سببٌ مسمًّى من الخمسة."""
    import slip_arms as SL                                       # noqa: PLC0415
    sess = SL.session_slice(bars) if bars else []
    if not sess:
        return ("no_minutes", "day" if not bars else "sess"), None
    if not SL.scale_ok(sess[-1]["c"], leg.get("dclose")):
        return ("raw_scale_unverified", "dclose"), None
    k = touch_index(sess, leg["level"], leg["side"])
    if k is None:
        return ("no_minutes", "touch"), None
    return ("ok", ""), sess[k]


def stage_quote(leg: dict, bar: dict, win: dict) -> tuple:
    """من النافذة إلى **الاقتباس السائد** — أو سببٌ مسمًّى.

    يُرجَع `(سبب، تفصيل)` و`payload` فيه ما يلزم `c`/`s` **بلا حسابهما هنا**
    (فوضعُ الجدوى يعدّ الأسباب ولا يحسب رقمًا)."""
    import slip_nbbo_arms as NB                                  # noqa: PLC0415
    if win is None:
        return ("no_quotes", "window_failed"), None
    quotes, trades = win.get("q"), win.get("t")
    if trades is None:
        return ("no_quotes", "trades_failed"), None
    if not trades:
        return ("no_minutes", "no_trades"), None
    f, ok = NB.raw_factor(bar, trades)
    if not ok or not f:
        return ("raw_scale_unverified", "factor"), None
    tms = touch_ms(trades, float(leg["level"]) * f, leg["side"])
    if tms is None:
        return ("no_minutes", "no_trade_at_level"), None
    if not quotes:
        return ("no_quotes", "empty"), None
    q = NB.prevailing(quotes, tms)
    if q is None:
        return ("no_quotes", "none_before"), None
    if q.get("ask") is None or q.get("bid") is None:
        return ("no_quotes", "half"), None
    age = int(tms) - int(q["t"])
    if age > STALE_MS:
        # 🔑 تُرجَع الحمولةُ **مع** السبب: الساقُ **مُسقَطةٌ من كلّ معيار**
        #    (‏`BC1`-`BC3`) لكنّها تُغذّي السطرَ الوصفيَّ «بلا حارس التقادم»
        #    فلا تُسيّر عتبةُ `STALE_MS` الرقمَ في الخفاء.
        return ("stale_quote", ""), {"bid": float(q["bid"]),
                                     "ask": float(q["ask"]),
                                     "factor": float(f), "t_ms": int(tms),
                                     "age_ms": age}
    return ("ok", ""), {"bid": float(q["bid"]), "ask": float(q["ask"]),
                        "factor": float(f), "t_ms": int(tms), "age_ms": age}


def measure(leg: dict, pay: dict) -> dict:
    """`c` لكلّ ساق · و`s` **على ساق الخسارة وحدَها** (‏§②)."""
    c = spread_pct(pay)
    if c is None:
        return None
    out = {"sym": leg["sym"], "year": leg["year"], "kind": leg["kind"],
           "day": leg["day"], "c": c, "age_ms": pay["age_ms"], "s": None}
    if leg["kind"] == "loss" and leg.get("model"):
        out["s"] = slip_of(float(leg["model"]), c, pay["bid"] / pay["factor"])
    return out


# ══════════════════ ⑥ المسار الرئيس ══════════════════
def main() -> int:                                               # noqa: PLR0911,PLR0912,PLR0915
    import concurrent.futures as _cf                             # noqa: PLC0415
    import slip_arms as SL                                       # noqa: PLC0415
    import slip_nbbo_arms as NB                                  # noqa: PLC0415

    years = [x.strip() for x in
             str(os.environ.get("BTCOST_YEARS", "")).split(",") if x.strip()]
    frozen = [x.strip() for x in
              str(os.environ.get("BTCOST_FROZEN", "")).split(",") if x.strip()]
    dry = str(os.environ.get("BTCOST_DRY", "")).strip() == "1"
    workers = int(os.environ.get("BTCOST_WORKERS") or NB.WORKERS)
    if not years or len(years) != len(frozen):
        _log("⛔ يلزم BTCOST_YEARS و BTCOST_FROZEN بالعدد نفسِه وبالترتيب نفسِه")
        return RC_INPUT
    if any(y not in GOV_YEARS for y in years):
        _log(f"⛔ سنةٌ غيرُ مسموحة — الكونُ هو كونُ `T-FCOST` {GOV_YEARS}")
        return RC_INPUT
    if not dry and sorted(years) != sorted(GOV_YEARS):
        _log(f"⛔ الحكمُ يشترط السنواتِ الثلاث {GOV_YEARS} بنصّ §④")
        return RC_INPUT

    _log("🩸📡 T-BTCOST — تكلفةُ التنفيذ على مجتمع المحرّك نفسِه")
    _log(f"   `BC1` تغطية ≥ {COV_MIN:.0%}/سنة · `BC2` ≥ {LEGS_YEAR} ساقًا/سنة "
         f"و≥ {LEGS_TOTAL} مجمَّعًا · `BC3` فاصلٌ أضيقُ من {CI_MAX_PP} نقطة")
    _log(f"   حارسُ التقادم {STALE_MS // 1000}ث · نافذةُ الرجوع "
         f"{NB.LOOKBACK_MS // 1000}ث · بوتستراب {BOOT_N} ببذرة {BOOT_SEED}")
    if dry:
        _log("🧪 وضعُ الجدوى: **صفرُ `c` وصفرُ `s` وصفرُ فاصلٍ وصفرُ حكم** — "
             "سؤالُه الوحيد: هل تعبر `BC1` و`BC2`؟")
        _log("   ⚠️ ودرسُ `T-PMGATE`: وضعُ الجدوى يُجيز ما يمرّ به وحدَه.")

    if not selfcheck_readonly():
        _log("⛔ `V-B4`-ب: الأداةُ ليست قراءةً فقط")
        return RC_SELF
    if not no_config_assign():
        _log("⛔ `V-B5`: إسنادٌ إلى CONFIG داخل الأداة")
        return RC_SELF
    ok6, why6 = reuse_by_name()
    _log(f"🔒 `V-B6` إعادةُ الاستعمال بالاسم: {why6}")
    if not ok6:
        return RC_SELF
    ok3, why3 = roots_identical()
    _log(f"🔒 `V-B3` الجذور و`slip_nbbo_arms`: {why3}")
    if not ok3:
        return RC_SELF

    # ── المشيُ: طفلٌ لكلّ سنة ──
    recs, meta_all = {}, {}
    for y, fz in zip(years, frozen):
        _log(f"▶️ مشيُ {y} …")
        meta = _run_child(y, fz, {"BACKTEST_YEAR": y})
        if not meta:
            _log(f"⛔ سقط طفلُ {y}")
            return RC_CHILD
        try:
            rows = json.load(open(meta["path"], encoding="utf-8"))
        except Exception:                                        # noqa: BLE001
            rows = []
        if not rows:
            _log(f"⛔ صفرُ صفقاتٍ محسومةٍ في {y}")
            return RC_CHILD
        recs[y], meta_all[y] = rows, meta
        _log(f"   {y}: إشارات={meta['n_signals']} · محسومة={meta['n_resolved']}"
             f" · مُعادةٌ مطابِقة={meta['n_agree']} · سبريدُ الطفل={meta['spread']}")

    # ── `V-B1`: أعدادُ `T-FCOST` بت-بت ──
    bad1 = []
    for y in years:
        m = meta_all[y]
        if m["n_signals"] != FC_SIGNALS[y] or m["n_resolved"] != FC_RESOLVED[y]:
            bad1.append(f"{y}: {m['n_signals']}/{m['n_resolved']} ≠ "
                        f"{FC_SIGNALS[y]}/{FC_RESOLVED[y]}")
    _log(f"🔗 `V-B1` تكاملٌ مع `T-FCOST`: "
         f"{'مطابقٌ بت-بت ✅' if not bad1 else '🔴 ' + ' · '.join(bad1)}")
    if bad1:
        _log("⛔ **عطبُ أداةٍ لا نتيجة** ⇒ لا يُقرأ رقم.")
        return RC_VB1

    # ── `V-B2`: تطابقُ إعادة الاشتقاق ──
    agree_bad = []
    for y in years:
        m = meta_all[y]
        rate = m["n_agree"] / float(m["n_resolved"] or 1)
        _log(f"🔒 `V-B2` {y}: تطابقٌ {rate:.4f} "
             f"({m['n_agree']}/{m['n_resolved']})")
        if rate < AGREE_MIN:
            agree_bad.append(f"{y}={rate:.4f}")
    if agree_bad:
        _log(f"⛔ `V-B2` دون {AGREE_MIN} ⇒ خروجٌ ولا رقم ({' · '.join(agree_bad)})")
        return RC_VB2

    # ── بناءُ السيقان ──
    legs, why = [], {r: 0 for r in REASONS}
    sub = {}
    for y in years:
        for rec in recs[y]:
            if not rec.get("agree"):
                why["walk_mismatch"] += 2          # ساقاها معًا
                sub["mismatch:" + str(rec.get("why"))] = \
                    sub.get("mismatch:" + str(rec.get("why")), 0) + 1
                continue
            legs.extend(legs_of(rec, y))
    need = len(legs) + why["walk_mismatch"]
    _log(f"🦵 السيقانُ المطلوبة {need} · مرشَّحةٌ للقياس {len(legs)}"
         f" · `walk_mismatch` {why['walk_mismatch']}")

    # ── شموعُ الدقيقة (‏`slip_arms.fetch_day` بالاسم) ──
    days = {}
    for lg in legs:
        days.setdefault((lg["sym"], lg["day"]), None)
    _log(f"⬇️ أيّامٌ فريدة: {len(days)} — جلبٌ بـ{workers} عاملًا …")
    t0 = time.time()
    with _cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(SL.fetch_day, k[0], k[1]): k for k in days}
        for i, f in enumerate(_cf.as_completed(futs), 1):
            try:
                days[futs[f]] = f.result()
            except Exception:                                    # noqa: BLE001
                days[futs[f]] = None
            if i % 500 == 0:
                _log(f"  … شموع {i}/{len(days)} ({time.time() - t0:.0f}ث)")
    _log(f"⬇️ الشموع: {len(days)} يومًا في {time.time() - t0:.0f}ث")

    # ── دقيقةُ اللمس ثمّ نوافذُ الاقتباس ──
    by_key, n_staged = {}, 0
    for lg in legs:
        (why_k, det), bar = stage_bar(lg, days.get((lg["sym"], lg["day"])))
        if why_k != "ok":
            why[why_k] += 1
            sub[f"{why_k}:{det}"] = sub.get(f"{why_k}:{det}", 0) + 1
            continue
        key = (lg["sym"], lg["day"], int(bar["t"]))
        by_key.setdefault(key, []).append((lg, bar))
        n_staged += 1
    _log(f"🪟 نوافذُ الاقتباس الفريدة: {len(by_key)} "
         f"(لسيقانٍ مؤهَّلة {n_staged})")

    # 🔑 **تُستهلَك النافذةُ عند وصولها ثمّ تُحرَّر**: تخزينُ آلاف النوافذ
    #    (كلٌّ بآلاف الاقتباسات) يُسقط الرنرَ بالذاكرة. والنتائجُ تُرتَّب بعدُ
    #    فلا يتسرّب ترتيبُ الوصول إلى رقمٍ منشور (‏`V-B9`).
    ready, stale_pool = [], []
    t0 = time.time()
    with _cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(window_of, k): k for k in by_key}
        for i, f in enumerate(_cf.as_completed(futs), 1):
            try:
                win = f.result()
            except Exception:                                    # noqa: BLE001
                win = None
            for lg, bar in by_key.get(futs[f], []):
                (why_k, det), pay = stage_quote(lg, bar, win)
                if why_k != "ok":
                    why[why_k] += 1
                    sub[f"{why_k}:{det}"] = sub.get(f"{why_k}:{det}", 0) + 1
                    if why_k == "stale_quote" and pay:
                        stale_pool.append((lg, pay))   # وصفيٌّ فقط
                    continue
                ready.append((lg, pay))
            win = None
            if i % 500 == 0:
                _log(f"  … نوافذ {i}/{len(by_key)} ({time.time() - t0:.0f}ث)")
    _log(f"⬇️ النوافذ: {len(by_key)} في {time.time() - t0:.0f}ث")
    ready.sort(key=lambda z: (z[0]["sym"], z[0]["day"], z[0]["kind"]))
    stale_pool.sort(key=lambda z: (z[0]["sym"], z[0]["day"], z[0]["kind"]))

    got = len(ready)
    drop = sum(why.values())
    _log("📉 أسبابُ الإسقاط المسمّاة: "
         + " · ".join(f"{r}={why[r]}" for r in REASONS))
    if sub:
        _log("   (تشخيصٌ فرعيٌّ لا بندَ سادس): "
             + " · ".join(f"{k}={v}" for k, v in sorted(sub.items())))
    ok7 = (got + drop == need)
    _log(f"🔒 `V-B7` مقيسة {got} ‏+ مُسقَطة {drop} = مطلوبة {need}: "
         f"{'✅' if ok7 else '🔴 لا تتساوى'}")
    if not ok7:
        _log("⛔ إسقاطٌ صامتٌ ⇒ خروج.")
        return RC_VGUARD

    cov = {}
    for y in years:
        n_need = 2 * meta_all[y]["n_resolved"]
        n_got = sum(1 for lg, _ in ready if lg["year"] == y)
        cov[y] = (n_got / float(n_need)) if n_need else 0.0
        _log(f"📊 {y}: مقيسة {n_got} من {n_need} ⇒ `COV` = {cov[y]:.3f}")
    bc1 = all(cov[y] >= COV_MIN for y in years)
    per_year = {y: sum(1 for lg, _ in ready if lg["year"] == y) for y in years}
    bc2 = all(per_year[y] >= LEGS_YEAR for y in years) and got >= LEGS_TOTAL
    _log(f"🎯 `BC1` {'✅' if bc1 else '🔴'} · `BC2` {'✅' if bc2 else '🔴'} "
         f"(مجمَّع {got})")

    if dry:
        _log("🧪 انتهى وضعُ الجدوى — لا `c` ولا `s` ولا فاصلَ ولا حكم.")
        return 0

    rows = [measure(lg, pay) for lg, pay in ready]
    rows = [r for r in rows if r]
    if len(rows) != got:
        _log(f"⛔ `V-B7`: {got - len(rows)} ساقًا سقطت بعد الاقتباس بلا سبب")
        return RC_VGUARD
    with open(OUT_LEGS, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")

    cs = sorted(r["c"] for r in rows)
    ent = sorted(r["c"] for r in rows if r["kind"] == "entry")
    exi = sorted(r["c"] for r in rows if r["kind"] != "entry")
    ss = sorted(r["s"] for r in rows if r["s"] is not None)
    grp = {}
    for r in rows:
        grp.setdefault(r["sym"], []).append(r["c"])
    lo, hi = boot_ci_median(grp)
    width = (hi - lo) if (lo is not None and hi is not None) else None
    bc3 = bool(width is not None and width < CI_MAX_PP)

    _log("── المُخرَجاتُ المقيسة (‏§③) ──")
    _log(f"  `C-MED` = {_num(statistics.median(cs))}% · "
         f"`C-P25` = {_num(pctile(cs, 25))}% · `C-P75` = {_num(pctile(cs, 75))}%")
    _log(f"  `C-ENT` = {_num(statistics.median(ent)) if ent else '—'}% "
         f"({len(ent)}) · `C-EXI` = "
         f"{_num(statistics.median(exi)) if exi else '—'}% ({len(exi)})")
    if ss:
        neg = sum(1 for x in ss if x < 0) / float(len(ss))
        _log(f"  `S-MED` = {_num(statistics.median(ss))}% · "
             f"`S-P25` = {_num(pctile(ss, 25))}% · "
             f"`S-P75` = {_num(pctile(ss, 75))}% · "
             f"سالبةٌ {neg:.3f} من {len(ss)} ساقَ خسارة (‏`V-B8` بلا قصّ)")
    else:
        _log("  `S-MED` — لا ساقَ خسارةٍ مقيسة")
    for y in years:
        yc = sorted(r["c"] for r in rows if r["year"] == y)
        _log(f"  {y}: `C-MED` = {_num(statistics.median(yc)) if yc else '—'}% "
             f"({len(yc)} ساقًا)")
    _log(f"  فاصلُ البوتستراب لوسيط `c`: [{_num(lo)}, {_num(hi)}] ⇒ عرضٌ "
         f"{_num(width)} نقطة · `BC3` {'✅' if bc3 else '🔴'}")
    ages = sorted(r["age_ms"] for r in rows)
    _log(f"  🕒 عمرُ الاقتباس: وسيط {pctile(ages, 50)}مِلّي · "
         f"‏P75 {pctile(ages, 75)} · P95 {pctile(ages, 95)}")
    # ℹ️ حساسيّةُ عتبةٍ **من عندنا**: لو رُفع حارسُ التقادم كلَّه، أيُّ وسيطٍ
    #    يُقرأ؟ — يُطبَع دائمًا فلا تُسيّر العتبةُ الرقمَ في الخفاء (‏وصفيٌّ
    #    لا حاكم: هذي السيقانُ خارج `BC1`-`BC3` بنصّ §④).
    _st_c = [x for x in (spread_pct(p) for _l, p in stale_pool) if x is not None]
    if _st_c:
        _both = sorted(cs + _st_c)
        _log(f"  ℹ️ **وصفيٌّ لا حاكم** — `C-MED` بلا حارس التقادم = "
             f"{_num(statistics.median(_both))}% على {len(_both)} ساقًا "
             f"(‏{len(_st_c)} متقادمة أُضيفت) · مقابل "
             f"{_num(statistics.median(cs))}% بالحارس")
    else:
        _log("  ℹ️ لا ساقَ متقادمةً بحمولةٍ ⇒ الحارسُ لم يقصّ شيئًا يُقاس")

    # ── `V-B9`: الحتميّةُ على شريحةٍ مُعادةٍ من الكاش نفسِه ──
    # 🔑 لا تُعاد النداءةُ نفسُها (لكانت تطابقًا تافهًا — الصنفُ ③): تُعاد
    #    الشريحةُ **معكوسةَ الترتيب** ويُعاد الفاصلُ على قاموسٍ **معكوسِ
    #    الإدراج** ⇒ يسقط أيُّ اعتمادٍ على ترتيب الورود أو ترتيب القاموس.
    _key9 = lambda z: (z[0]["sym"], z[0]["day"], z[0]["kind"])   # noqa: E731
    slice_in = sorted(ready, key=_key9)[:200]
    fwd_rows = [measure(lg, pay) for lg, pay in slice_in]
    rev_rows = [measure(lg, pay) for lg, pay in reversed(slice_in)]
    _dump = lambda z: json.dumps(                                # noqa: E731
        sorted([x for x in z if x], key=lambda r: (r["sym"], r["day"],
                                                  r["kind"], r["c"])),
        ensure_ascii=False, sort_keys=True)
    ok9 = _dump(fwd_rows) == _dump(rev_rows)
    grp_rev = {}
    for r in reversed(rows):
        grp_rev.setdefault(r["sym"], []).insert(0, r["c"])
    lo2, hi2 = boot_ci_median(grp_rev)
    ok9 = ok9 and (lo2, hi2) == (lo, hi)
    _log(f"🔒 `V-B9` الحتميّة (شريحةٌ {len(slice_in)} ‏+ الفاصل): "
         f"{'✅ بت-بت' if ok9 else '🔴 تفرّقت'}")
    if not ok9:
        return RC_VGUARD

    branch, lines = read_verdict({"BC1": bc1, "BC2": bc2, "BC3": bc3})
    for ln in lines:
        _log(ln)
    _log(f"📄 الصفوف: {OUT_LEGS}")
    return RC_NOVERDICT if branch == 3 else 0


if __name__ == "__main__":
    if len(sys.argv) > 2 and sys.argv[1] == "--child":
        sys.exit(run_child(sys.argv[2]))
    sys.exit(main())
