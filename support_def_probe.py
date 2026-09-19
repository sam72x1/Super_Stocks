# -*- coding: utf-8 -*-
"""🧱🔬 `T-SUPDEF` — مِجَسُّ **تعريف الدعم** (العقد `support_def_prereg.md` ‏+ الملحق `§⑩`).

**قراءةٌ فقط:** لا كتابةَ حالةٍ · لا إرسالَ تلغرام · لا سرَّ · لا مسَّ إنتاج.
**ولا يُشحَن منه شيءٌ مهما كانت النتيجة** (‏المحورُ يمسّ جذرًا — `§⓪`).

الحاكمُ `A0` = `pivot_stability` **الإنتاجيّة** كما هي · والوصفيّون
(`A1`/`A2`/`A-FAR`/`A-MID`/`A-HIGHLOW`) **يُنشَرون ولا يُرشَّحون** · وشاهدُ الضبط
الحاكم **`A-RAND`** (‏`§⑩-ⓕ`) سقوطُه شرطُ صحّة.

المجتمعُ = ثلاثيّاتُ `§⑨-ⓒ` ‏+ الأربعُ المؤرَّخةُ بمرساة السعر (`§⑩-ⓑ`) —
**تُعاد اشتقاقًا** من `faisal_price_anchor` لا تُكتَب بيدٍ (‏`V-S6`).

رموزُ الخروج: 0 = الفرعُ 1 · 2 = الفرعُ 2 · 3 = الفرعُ 3 «لا قياس» · 5 = حارس ·
‏6 = هُويّةُ المجتمع (‏`V-S6`) · 7 = شاهدُ الضبط لا يفارق (‏`V-S7`).
"""
import csv
import datetime as dt
import random
import sys

import Super_stock as bot
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


def read_verdict(n_rows, n_syms, share, p, med_abs, far_worse):
    """فروعُ `§④` بحرفها — ولا فرعَ رابع."""
    if n_rows < SD0_MIN_ROWS or n_syms < SD0_MIN_SYMS or not far_worse:
        return 3, ("الفرعُ 3 — **«لا قياس»**: الأرضيّةُ أو صحّةُ المقياس لم تُبلَغ "
                   "· يُعلَن بعدَده ولا يُفسَّر · ولا يُرفَع العدُّ بتأريخٍ مُستنتَج")
    sd1 = share >= SD1_SHARE and p <= SD1_P
    sd2 = med_abs >= SD2_MEDIAN
    if sd1 and sd2:
        return 0, ("الفرعُ 1 — الانحيازُ **مقيسٌ ومادّيّ** ⇒ يُنشَر رقمًا ويُقترَح "
                   "تسجيلٌ لاحق · **ولا يُمَسّ `pivot_stability`**")
    if sd1 and not sd2:
        return 2, ("الفرعُ 2 — الانحيازُ **موجودٌ وغيرُ مادّيّ** ⇒ **يُغلَق المحورُ** "
                   "بشرطِ فتحٍ مؤرَّخ")
    return 3, ("الفرعُ 3 — **«لا قياس»**: `SD1` لم تُستوفَ · يُعلَن ولا يُفسَّر")


def branch3_reason(n_rows, n_syms, med_a0, med_ctrl):
    """`V-S8` — سببُ الفرع 3 **مفصولًا** فلا تُطوى الحالةُ الثالثة بلا بيان."""
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
    return "**`SD1` لم تُستوفَ** (الشاهدُ عبر)"


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
    for t in pa.targets():
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


# ═══════════ بناءُ الصفوف — والحساسيّاتُ الثلاثُ تُعيد استعمالَه ═══════════════
def build_rows(hist_old, hist_new, acases, asof_mode="match", ref_mode="chart",
               marker=True):
    """`asof_mode` ∈ {match, date} (`ⓒ`) · `ref_mode` ∈ {chart, close} (`ⓓ`) ·
    `marker` (`ⓔ`). الافتراضاتُ **هي القاعدةُ المسجَّلة** والباقي حساسيّاتٌ وصفيّة."""
    plan = []
    for sym, asof, frame, levels, src in CASES:
        plan.append({"sym": sym, "asof": asof, "frame": frame, "levels": list(levels),
                     "src": src, "kind": "close", "px": None, "hist": hist_old})
    for c in acases:
        asof = c["match_date"] if asof_mode == "match" else c["date"]
        plan.append({"sym": c["sym"], "asof": asof, "frame": "daily",
                     "levels": list(c["levels"]), "src": c["line"],
                     "kind": c["kind"], "px": c["px"], "hist": hist_new})
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
             "mid": a_mid(df), "hl": a_highlow(df), "src": q["src"], "bars": len(df)}
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


def main() -> int:
    global TOL
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
    asyms = sorted({t["symbol"] for t in pa.targets()
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

    rows, skipped, n_drop = build_rows(hist_old, hist_new, acases)

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
    log(f"   V-S5 تغطية: طُلبت {len(CASES) + len(acases)} · نجحت {len(rows)} "
        f"· استُبعدت {len(skipped)}")
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

    rc, txt = read_verdict(n, nsym, share, p, med, ctrl_ok)

    log("")
    log("═══ V-S9 الحساسيّاتُ الثلاث (وصفيّةٌ — لا تدخل أيَّ معيار) ═══")
    for nm, kw in (("ⓒ القصُّ عند `date` لصفوف `spot`", {"asof_mode": "date"}),
                   ("ⓓ سعرُ المرجع = إغلاقُ `match_date` في الثلاثة",
                    {"ref_mode": "close"}),
                   ("ⓔ بلا قاعدةِ وسمِ مؤشّر السعر", {"marker": False})):
        try:
            r2, _s2, _d2 = build_rows(hist_old, hist_new, acases, **kw)
            g2, n2, ns2, sh2, p2, md2, mr2, ok2 = stats_of(r2)
            log(f"   {nm}: حاكمة {n2}/{ns2} · SD1 {sh2:.1f}% p={p2} · "
                f"SD2 {md2:.2f}% · SD3 "
                f"{('%.2f%%' % mr2) if mr2 is not None else '—'} ⇒ "
                f"{'تعبر' if ok2 else 'تسقط'} · "
                f"الفرعُ {read_verdict(n2, ns2, sh2, p2, md2, ok2)[0]}")
        except Exception as e:                                 # noqa: BLE001
            log(f"   {nm}: ⛔ رمى {type(e).__name__}")

    log("")
    log("═══ 🔎 تشخيصٌ: مقياسُ التقسيم عند تاريخ الشارت (يُطبَع ولا يُستعمَل) ═══")
    for c in acases:
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
    log("═══ الحكم ═══")
    if rc == 3:
        log(f"   V-S8 سببُ الفرع 3: {branch3_reason(n, nsym, med, med_r)}")
    log(f"JUDGE rc={rc} · {txt}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
